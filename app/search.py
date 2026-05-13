"""Data loaders and search logic for TNEA College Finder."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

import pandas as pd

CATEGORIES = ["OC", "BC", "BCM", "MBC", "SC", "SCA", "ST"]
YEARS = [2025, 2024, 2023, 2022, 2021]


def _data_dir() -> Path:
    return Path(__file__).resolve().parent.parent / "data"


def _bool_coerce(s: pd.Series) -> pd.Series:
    """Normalize CSV boolean column for reliable merges."""
    def _one(x) -> bool:
        if isinstance(x, bool):
            return x
        if pd.isna(x):
            return False
        return str(x).strip().lower() in ("true", "1", "yes", "t")

    return s.map(_one)


def _ensure_branch_norm(df: pd.DataFrame) -> pd.DataFrame:
    """Guarantee a non-empty `branch_norm` column.

    Older `cutoffs_long.csv` files may omit it. When `colleges_master.csv` has
    `branch_norm`, merge on (college_code, branch_clean, is_self_supporting).
    Otherwise copy `branch_clean`.
    """
    df = df.copy()
    key_cols = ["college_code", "branch_clean", "is_self_supporting"]
    master_path = _data_dir() / "colleges_master.csv"
    map_df = None
    if master_path.exists():
        master = pd.read_csv(master_path, encoding="utf-8-sig")
        if "branch_norm" in master.columns and all(c in master.columns for c in key_cols):
            if all(c in df.columns for c in key_cols):
                m = master[key_cols + ["branch_norm"]].drop_duplicates(
                    subset=key_cols
                ).copy()
                m["is_self_supporting"] = _bool_coerce(m["is_self_supporting"])
                d = df[key_cols + [c for c in df.columns if c not in key_cols]].copy()
                d["is_self_supporting"] = _bool_coerce(d["is_self_supporting"])
                map_df = m
                df = d.drop(columns=["branch_norm"], errors="ignore").merge(
                    map_df, on=key_cols, how="left"
                )

    if map_df is None:
        if "branch_norm" not in df.columns:
            df["branch_norm"] = df["branch_clean"].astype(str)
        else:
            blank = df["branch_norm"].isna() | (
                df["branch_norm"].astype(str).str.strip() == ""
            )
            df.loc[blank, "branch_norm"] = df.loc[blank, "branch_clean"].astype(str)
        return df

    if "branch_norm" not in df.columns:
        df["branch_norm"] = df["branch_clean"].astype(str)
    else:
        blank = df["branch_norm"].isna() | (
            df["branch_norm"].astype(str).str.strip() == ""
        )
        df.loc[blank, "branch_norm"] = df.loc[blank, "branch_clean"].astype(str)
    return df


def load_long() -> pd.DataFrame:
    """Load the long-format cutoffs table."""
    path = _data_dir() / "cutoffs_long.csv"
    df = pd.read_csv(path, encoding="utf-8-sig")
    df["college_code"] = pd.to_numeric(df["college_code"], errors="coerce").astype("Int64")
    df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")
    df["cutoff"] = pd.to_numeric(df["cutoff"], errors="coerce")
    df = df.dropna(subset=["college_code", "year", "cutoff"]).reset_index(drop=True)
    df = _ensure_branch_norm(df)
    return df


def load_master() -> pd.DataFrame:
    """Load the wide master (used for cross-year, cross-category trend lookups)."""
    path = _data_dir() / "colleges_master.csv"
    df = pd.read_csv(path, encoding="utf-8-sig")
    return df


def _pick_representative_short(series: pd.Series) -> str:
    """First non-null, non-empty branch_short (pandas NaN-safe)."""
    for x in series:
        if x is None or pd.isna(x):
            continue
        xs = str(x).strip()
        if xs and xs.lower() not in ("nan", "none", "<na>"):
            return xs
    return ""


def branch_options(master: pd.DataFrame) -> list[tuple[str, str]]:
    """Return (id, display_label) pairs for the branch filter.

    Prefers one option per distinct ``branch_raw`` (exact brochure / Excel
    wording) so spelling variants stay separate. Falls back to ``branch_clean``
    if ``branch_raw`` is missing. Sorted by popularity (row count in master).
    """
    m = master.copy()
    key_col = "branch_raw" if "branch_raw" in m.columns else "branch_clean"
    if key_col not in m.columns:
        return []
    pool = m[m[key_col].astype(str).str.strip() != ""].copy()
    if pool.empty:
        return []
    if "branch_norm" not in pool.columns:
        pool["branch_norm"] = pool[key_col].astype(str)
    counts = pool.groupby(key_col).size().sort_values(ascending=False)
    short_by = pool.groupby(key_col)["branch_short"].agg(_pick_representative_short)
    norm_by = pool.sort_values("branch_norm").groupby(key_col)["branch_norm"].first()
    out: list[tuple[str, str]] = []
    for val, n in counts.items():
        short = short_by.get(val, "")
        norm = norm_by.get(val, val)
        prefix = f"{short} — " if short else ""
        label_core = str(norm).strip() if pd.notna(norm) else str(val)
        out.append((str(val), f"{prefix}{label_core}  ·  {n}"))
    return out


def parse_branch_filter_param(
    raw_csv: str,
    valid: set[str],
    master: pd.DataFrame,
) -> list[str]:
    """Resolve ``branch`` query tokens to filter ids used in ``cutoffs_long``.

    Accepts ``branch_raw`` (current), or legacy ``branch_clean`` /
    ``branch_norm`` tokens from older share links.
    """
    has_raw = "branch_raw" in master.columns
    has_norm = "branch_norm" in master.columns
    has_clean = "branch_clean" in master.columns

    norm_map: dict[str, list[str]] = {}
    clean_map: dict[str, list[str]] = {}

    if has_norm and has_raw:
        for norm, grp in master.groupby("branch_norm", sort=False):
            norm_map[str(norm)] = sorted(grp["branch_raw"].astype(str).unique())
    elif has_norm and has_clean:
        # Legacy master: no branch_raw column — norms map to branch_clean ids.
        for norm, grp in master.groupby("branch_norm", sort=False):
            norm_map[str(norm)] = sorted(grp["branch_clean"].astype(str).unique())

    if has_raw and has_clean:
        for cl, grp in master.groupby("branch_clean", sort=False):
            clean_map[str(cl)] = sorted(grp["branch_raw"].astype(str).unique())

    out: list[str] = []
    seen: set[str] = set()
    for b in str(raw_csv).split(","):
        token = b.strip()
        if not token:
            continue
        if token in valid:
            if token not in seen:
                seen.add(token)
                out.append(token)
            continue
        if has_raw and token in clean_map:
            for r in clean_map[token]:
                if r in valid and r not in seen:
                    seen.add(r)
                    out.append(r)
            continue
        for c in norm_map.get(token, []):
            if c in valid and c not in seen:
                seen.add(c)
                out.append(c)
    return out


def norm_to_branch_cleans(master: pd.DataFrame) -> dict[str, list[str]]:
    """Deprecated: use ``parse_branch_filter_param``; kept for older callers."""
    if "branch_norm" not in master.columns or "branch_clean" not in master.columns:
        return {}
    m = master[["branch_norm", "branch_clean"]].dropna()
    m = m[m["branch_clean"].astype(str).str.strip() != ""]
    parts: dict[str, list[str]] = {}
    for norm, grp in m.groupby("branch_norm", sort=False):
        parts[str(norm)] = sorted(grp["branch_clean"].astype(str).unique())
    return parts


def find_colleges(
    long: pd.DataFrame,
    cutoff_min: float,
    cutoff_max: float,
    category: str,
    year: int,
    branches: Iterable[str] | None = None,
    include_ss: bool = True,
    college_name_query: str | None = None,
) -> pd.DataFrame:
    """Return college+branch rows where the cutoff falls within [min, max].

    Results are sorted highest-cutoff-first (toughest match at the top).

    Args:
        long: long-format cutoffs dataframe (from load_long()).
        cutoff_min, cutoff_max: inclusive range to search within.
        category: one of CATEGORIES (OC / BC / BCM / MBC / SC / SCA / ST).
        year: integer year (one of YEARS).
        branches: optional iterable of branch row ids: ``branch_raw`` when
            present in ``long``, otherwise ``branch_clean``.
        include_ss: if False, hide self-supporting (SS) seats.
        college_name_query: optional case-insensitive substring match on
            college_name.
    """
    lo, hi = float(min(cutoff_min, cutoff_max)), float(max(cutoff_min, cutoff_max))
    q = long[
        (long["category"] == category)
        & (long["year"] == int(year))
        & (long["cutoff"] >= lo)
        & (long["cutoff"] <= hi)
    ].copy()
    if branches:
        ids = list(branches)
        if "branch_raw" in q.columns:
            q = q[q["branch_raw"].isin(ids)]
        else:
            q = q[q["branch_clean"].isin(ids)]
    if not include_ss:
        q = q[q["is_self_supporting"] != True]  # noqa: E712
    if college_name_query:
        needle = str(college_name_query).strip()
        if needle:
            q = q[q["college_name"].astype(str).str.contains(needle, case=False, na=False)]
    q = q.sort_values(
        ["cutoff", "college_code", "branch_clean"],
        ascending=[False, True, True],
    ).reset_index(drop=True)
    return q


def trend_for(
    long: pd.DataFrame,
    college_code: int,
    branch_clean: str,
    category: str,
    is_ss: bool,
) -> pd.DataFrame:
    """5-year cutoff series for a specific (college, branch, category) row."""
    sub = long[
        (long["college_code"] == int(college_code))
        & (long["branch_clean"] == branch_clean)
        & (long["category"] == category)
        & (long["is_self_supporting"] == bool(is_ss))
    ].copy()
    sub = sub.sort_values("year")
    return sub[["year", "cutoff"]].reset_index(drop=True)


def trend_all_categories(
    long: pd.DataFrame,
    college_code: int,
    branch_clean: str,
    is_ss: bool,
) -> pd.DataFrame:
    """5-year cutoff series for all 7 categories at a specific (college, branch).

    Returns a wide-format DataFrame indexed by year, columns are categories.
    Missing values are NaN.
    """
    sub = long[
        (long["college_code"] == int(college_code))
        & (long["branch_clean"] == branch_clean)
        & (long["is_self_supporting"] == bool(is_ss))
    ].copy()
    if sub.empty:
        return pd.DataFrame(index=YEARS, columns=CATEGORIES, dtype=float)
    wide = (
        sub.pivot_table(index="year", columns="category", values="cutoff", aggfunc="first")
        .reindex(index=sorted(YEARS), columns=CATEGORIES)
    )
    return wide


def aggregate_stats() -> dict:
    """Cheap aggregate stats for the footer."""
    df = load_long()
    master = load_master()
    return {
        "n_colleges": int(master["college_code"].nunique()),
        "n_branches": int(
            master["branch_raw"].nunique()
            if "branch_raw" in master.columns
            else master["branch_clean"].nunique()
        ),
        "n_rows": int(len(df)),
        "year_min": int(df["year"].min()),
        "year_max": int(df["year"].max()),
    }
