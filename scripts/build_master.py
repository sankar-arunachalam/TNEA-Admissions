"""
TNEA College Finder - master data build pipeline.

Reads:  ../TNEA Colleges.xlsx, sheet "Cutoff for All"
        (3 header rows: category, year, blank; then 7 categories x 5 years)
Writes: ../data/colleges_master.csv  (wide format, one row per college+branch)
        ../data/cutoffs_long.csv     (long format, one row per college+branch+category+year)

Categories in source: OC, BC, BCM, MBC, SC, SCA, ST
Years in source:      2025, 2024, 2023, 2022, 2021
"""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
RAW_XLSX = ROOT / "TNEA Colleges.xlsx"
RAW_SHEET = "Cutoff for All"
MASTER_CSV = ROOT / "data" / "colleges_master.csv"
LONG_CSV = ROOT / "data" / "cutoffs_long.csv"

YEARS = [2025, 2024, 2023, 2022, 2021]
CATEGORIES = ["OC", "BC", "BCM", "MBC", "SC", "SCA", "ST"]
SOURCE_CATEGORY_ORDER = ["OC", "BC", "BCM", "MBC", "SC", "SCA", "ST"]
SOURCE_YEAR_ORDER = [2025, 2024, 2023, 2022, 2021]


def _parse_cutoff(value) -> float | None:
    """Convert a raw cell into a float cutoff, or None for missing/placeholder."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value) if pd.notna(value) else None
    s = str(value).strip()
    if not s or s in {"-", "--", "NA", "N/A", "\ufffd"}:
        return None
    s = re.sub(r"[^\d.\-]", "", s)
    if not s:
        return None
    try:
        return float(s)
    except ValueError:
        return None


_ACRONYM_FIXES = [
    (r"\bAi\b", "AI"),
    (r"\bMl\b", "ML"),
    (r"\bIot\b", "IoT"),
    (r"\bVlsi\b", "VLSI"),
    (r"\bSs\b", "SS"),
    (r"\bIt\b", "IT"),
    (r"\bBussiness\b", "Business"),
    (r"\bStrucutural\b", "Structural"),
    (r"\bStructutural\b", "Structural"),
    (r"\bM\.Tech\.", "M.Tech."),
    (r"\bB\.Plan\b", "B.Plan"),
    (r"\bB\.E\.", "B.E."),
    (r"\bB\.Tech\b", "B.Tech"),
]

# Filler / function words that should stay lowercase inside a Title Case name,
# but never at the start of the string.
_LOWERCASE_WORDS = {
    "and", "or", "of", "the", "in", "for", "with", "to", "a", "an", "on",
    "by", "at", "as", "from", "but", "into",
}


def _smart_title_case(s: str) -> str:
    """Title case using letter-run word boundaries (handles 'Word(Word' edge cases).

    Function words ('and', 'of', 'the', ...) stay lowercase unless they are
    the first letter-run in the string.
    """
    state = {"started": False}

    def fix(match: re.Match[str]) -> str:
        word = match.group(0)
        low = word.lower()
        first = not state["started"]
        state["started"] = True
        if not first and low in _LOWERCASE_WORDS:
            return low
        return low.capitalize()

    return re.sub(r"[A-Za-z]+", fix, s)


def _normalize_branch_name(name: str) -> str:
    """Canonical, case-consistent display name for a branch.

    Steps:
      1. Trim whitespace and collapse interior runs of spaces.
      2. Tighten spacing inside parentheses: '( foo )' -> '(foo)'.
      3. Smart title-case (lowercase function words like 'and', 'of').
      4. Restore well-known acronyms (AI, ML, VLSI, IoT, IT, SS).
      5. Fix common typos (e.g., 'Bussiness' -> 'Business').
    """
    if not isinstance(name, str):
        return ""
    s = re.sub(r"\s+", " ", name.strip())
    if not s:
        return ""
    s = re.sub(r"\(\s+", "(", s)
    s = re.sub(r"\s+\)", ")", s)
    s = _smart_title_case(s)
    for pattern, repl in _ACRONYM_FIXES:
        s = re.sub(pattern, repl, s, flags=re.IGNORECASE)
    s = re.sub(r"\s+", " ", s).strip()
    return s


_STOP_WORDS = frozenset({
    "AND", "OR", "OF", "THE", "IN", "FOR", "WITH", "TO", "A", "AN", "ON", "AT", "AS", "BY",
    "INCLUDING", "YEARS", "YEAR", "INTEGRATED",
})


def _initials_from_norm(norm: str, max_len: int = 8) -> str:
    """Abbreviation from significant words when no short_map entry matches."""
    if not norm or not isinstance(norm, str):
        return ""
    words = re.findall(r"[A-Za-z]+", norm)
    initials = [w[0].upper() for w in words if w.upper() not in _STOP_WORDS]
    if not initials:
        return ""
    return "".join(initials[:6])[:max_len]


def _derive_branch_fields(branch: str) -> dict:
    """Extract canonical name, degree, short code, and SS flag from the raw branch name."""
    if not isinstance(branch, str):
        return {
            "branch_clean": "", "branch_norm": "",
            "branch_short": "", "is_self_supporting": False, "degree": "",
        }

    raw = branch.strip()
    is_ss = bool(re.search(r"\(\s*SS\s*\)", raw, re.IGNORECASE))
    clean = re.sub(r"\(\s*SS\s*\)", "", raw, flags=re.IGNORECASE).strip()
    clean = re.sub(r"\s+", " ", clean)
    norm = _normalize_branch_name(clean)

    upper = clean.upper()
    if "ARCHITECT" in upper:
        degree = "B.Arch"
    elif "PLANNING" in upper:
        degree = "B.Plan"
    else:
        degree = "B.E./B.Tech"

    # Longer / more specific needles must come *before* shorter ones
    # (e.g. CSE-(AIML) before plain CSE — both match the same raw string otherwise).
    short_map = [
        # Computer-science family (specific → generic)
        (
            "COMPUTER SCIENCE AND ENGINEERING (INTERNET OF THINGS AND CYBER SECURITY",
            "CSE-IoT",
        ),
        ("COMPUTER SCIENCE AND ENGINEERING (INTERNET OF THINGS", "CSE-IoT"),
        (
            "COMPUTER SCIENCE AND ENGINEERING (ARTIFICIAL INTELLIGENCE AND MACHINE LEARNING",
            "CSE-AIML",
        ),
        ("COMPUTER SCIENCE AND ENGINEERING (AI AND MACHINE LEARNING", "CSE-AIML"),
        ("COMPUTER SCIENCE AND ENGINEERING (DATA SCIENCE", "CSE-DS"),
        ("COMPUTER SCIENCE AND ENGINEERING (CYBER SECURITY", "CSE-CY"),
        ("COMPUTER SCIENCE AND ENGINEERING (TAMIL", "CSE-TM"),
        ("COMPUTER SCIENCE AND ENGINEERING(TAMIL", "CSE-TM"),
        ("COMPUTER SCIENCE AND ENGINEERING(Artificial Intelligence", "CSE-AI"),
        ("COMPUTER SCIENCE AND ENGINEERING (ARTIFICIAL INTELLIGENCE)", "CSE-AI"),
        ("M.TECH. COMPUTER SCIENCE AND ENGINEERING", "M.TECH-CSE"),
        ("COMPUTER SCIENCE AND DESIGN", "CSD"),
        ("COMPUTER SCIENCE AND BUSINESS SYSTEM", "CSBS"),
        ("COMPUTER SCIENCE AND BUSINESS", "CSBS"),
        ("COMPUTER AND COMMUNICATION ENGINEERING", "CNC"),
        ("COMPUTER SCIENCE AND TECHNOLOGY", "CST"),
        ("COMPUTER TECHNOLOGY", "CMPT"),
        ("INFORMATION SCIENCE AND ENGINEERING", "ISE"),
        ("COMPUTER SCIENCE AND ENGINEERING", "CSE"),
        # Other branches (order only matters when one needle is a substring of another)
        ("ARTIFICIAL INTELLIGENCE AND DATA SCIENCE", "AI&DS"),
        ("ARTIFICIAL INTELLIGENCE AND MACHINE LEARNING", "AI&ML"),
        ("ELECTRONICS AND COMMUNICATION ENGINEERING", "ECE"),
        ("ELECTRONICS AND TELECOMMUNICATION ENGINEERING", "ETE"),
        ("ELECTRICAL AND ELECTRONICS ENGINEERING", "EEE"),
        ("ELECTRONICS AND INSTRUMENTATION ENGINEERING", "E&I"),
        ("INSTRUMENTATION AND CONTROL ENGINEERING", "ICE"),
        ("ELECTRONICS AND COMPUTER ENGINEERING", "ECOMP"),
        ("ELECTRICAL AND COMPUTER ENGINEERING", "ELCP"),
        ("INFORMATION TECHNOLOGY", "IT"),
        ("MECHANICAL ENGINEERING", "MECH"),
        ("CIVIL ENGINEERING", "CIVIL"),
        ("CHEMICAL ENGINEERING", "CHEM"),
        ("BIO MEDICAL ENGINEERING", "BME"),
        ("BIOMEDICAL ENGINEERING", "BME"),
        ("BIOTECHNOLOGY", "BIOTECH"),
        ("BIO TECHNOLOGY", "BIOTECH"),
        ("AEROSPACE ENGINEERING", "AERO"),
        ("AERONAUTICAL ENGINEERING", "AERO"),
        ("AUTOMOBILE ENGINEERING", "AUTO"),
        ("AGRICULTURAL ENGINEERING", "AGRI"),
        ("AGRICULTURE ENGINEERING", "AGRI"),
        ("MARINE ENGINEERING", "MARINE"),
        ("PRODUCTION ENGINEERING", "PROD"),
        ("INDUSTRIAL ENGINEERING", "IND"),
        ("MINING ENGINEERING", "MIN"),
        ("METALLURGICAL ENGINEERING", "METAL"),
        ("MATERIAL SCIENCE", "MATSCI"),
        ("VLSI", "VLSI"),
        ("ROBOTICS", "ROBO"),
        ("MECHATRONICS", "MCT"),
        ("CYBER SECURITY", "CYBER"),
        ("FOOD TECHNOLOGY", "FOOD"),
        ("PHARMACEUTICAL TECHNOLOGY", "PHARM"),
        ("PHARMACEUTICAL ENGINEERING", "PHARM"),
        ("GEO INFORMATICS", "GEOINF"),
        ("PETROLEUM ENGINEERING", "PETRO"),
        ("ARCHITECTURE", "ARCH"),
    ]
    short = ""
    for needle, code in short_map:
        if needle in upper:
            short = code
            break

    if not short:
        short = _initials_from_norm(norm)

    return {
        "branch_clean": clean,
        "branch_norm": norm,
        "branch_short": short,
        "is_self_supporting": is_ss,
        "degree": degree,
    }


def _canonical_name(group: pd.Series) -> str:
    """Pick the canonical college name from multiple variants under the same code.

    Strategy: choose the longest non-empty name (proxy for "most descriptive").
    Ties broken by lexicographic order for determinism.
    """
    candidates = sorted(
        (n for n in group.dropna().astype(str).str.strip().unique() if n),
        key=lambda s: (-len(s), s),
    )
    return candidates[0] if candidates else ""


def canonicalize_names(df: pd.DataFrame) -> pd.DataFrame:
    """Replace per-row college_name with one canonical name per college_code.
    Preserves the original under college_name_raw for audit.
    """
    df = df.copy()
    df["college_name_raw"] = df["college_name"]
    canon = df.groupby("college_code")["college_name"].agg(_canonical_name)
    df["college_name"] = df["college_code"].map(canon)
    return df


def load_raw() -> pd.DataFrame:
    raw = pd.read_excel(RAW_XLSX, sheet_name=RAW_SHEET, header=None)

    expected_cutoff_cols = len(SOURCE_CATEGORY_ORDER) * len(SOURCE_YEAR_ORDER)
    expected_total_cols = 3 + expected_cutoff_cols
    if raw.shape[1] < expected_total_cols:
        raise ValueError(
            f"Sheet '{RAW_SHEET}' has only {raw.shape[1]} columns; "
            f"expected at least {expected_total_cols} (3 id + {expected_cutoff_cols} cutoff)"
        )

    cutoff_col_names: list[str] = []
    for cat in SOURCE_CATEGORY_ORDER:
        for yr in SOURCE_YEAR_ORDER:
            cutoff_col_names.append(f"{cat}_{yr}")
    new_cols = ["college_code", "college_name", "branch_raw"] + cutoff_col_names
    raw = raw.iloc[:, : len(new_cols)].copy()
    raw.columns = new_cols

    raw = raw.iloc[3:].reset_index(drop=True)
    raw = raw.dropna(subset=["college_code", "branch_raw"], how="any")
    raw["college_code"] = pd.to_numeric(raw["college_code"], errors="coerce").astype("Int64")
    raw = raw.dropna(subset=["college_code"])

    for col in cutoff_col_names:
        raw[col] = raw[col].apply(_parse_cutoff)

    derived = raw["branch_raw"].apply(_derive_branch_fields).apply(pd.Series)
    raw = pd.concat([raw, derived], axis=1)

    raw["college_name"] = (
        raw["college_name"].astype(str).str.strip().str.replace(r"\s+", " ", regex=True)
    )

    raw = canonicalize_names(raw)

    return raw


def build_master(df: pd.DataFrame) -> pd.DataFrame:
    """Build the wide-format master with all 7 categories x 5 years."""
    meta_cols = [
        "college_code",
        "college_name",
        "college_name_raw",
        "college_short_name",
        "college_type",
        "district",
        "region",
        "nirf_rank",
        "branch_raw",
        "branch_clean",
        "branch_norm",
        "branch_short",
        "degree",
        "is_self_supporting",
        "has_any_cutoff",
    ]

    for col in ("college_short_name", "college_type", "district", "region", "nirf_rank"):
        if col not in df.columns:
            df[col] = ""
    if "college_name_raw" not in df.columns:
        df["college_name_raw"] = df["college_name"]

    cutoff_cols: list[str] = []
    for cat in CATEGORIES:
        for yr in YEARS:
            col = f"{cat}_{yr}"
            if col not in df.columns:
                df[col] = pd.NA
            cutoff_cols.append(col)

    df["has_any_cutoff"] = df[cutoff_cols].notna().any(axis=1)

    master = df[meta_cols + cutoff_cols].copy()
    master = master.sort_values(["college_code", "branch_clean"]).reset_index(drop=True)
    return master


def build_long(master: pd.DataFrame) -> pd.DataFrame:
    """Pivot the wide master into a long table for app consumption."""
    id_cols = [
        "college_code", "college_name", "college_short_name", "college_type",
        "district", "region", "nirf_rank",
        "branch_raw", "branch_clean", "branch_norm", "branch_short", "degree",
        "is_self_supporting",
    ]
    for col in id_cols:
        if col not in master.columns:
            master[col] = ""
    cutoff_cols = [f"{c}_{y}" for c in CATEGORIES for y in YEARS]

    long = master.melt(
        id_vars=id_cols,
        value_vars=cutoff_cols,
        var_name="cat_year",
        value_name="cutoff",
    )
    long[["category", "year"]] = long["cat_year"].str.split("_", expand=True)
    long["year"] = long["year"].astype(int)
    long = long.drop(columns=["cat_year"])
    long = long.dropna(subset=["cutoff"])
    long["cutoff"] = pd.to_numeric(long["cutoff"], errors="coerce")
    long = long.dropna(subset=["cutoff"])
    long = long[id_cols + ["category", "year", "cutoff"]]
    long = long.sort_values(
        ["college_code", "branch_clean", "category", "year"]
    ).reset_index(drop=True)
    return long


def main() -> None:
    df = load_raw()
    master = build_master(df)
    long = build_long(master)

    MASTER_CSV.parent.mkdir(parents=True, exist_ok=True)
    master.to_csv(MASTER_CSV, index=False, encoding="utf-8-sig")
    long.to_csv(LONG_CSV, index=False, encoding="utf-8-sig")

    print(f"Wrote {MASTER_CSV.relative_to(ROOT)}  ({len(master):,} rows)")
    print(f"Wrote {LONG_CSV.relative_to(ROOT)}    ({len(long):,} rows)")
    print(f"Colleges: {master['college_code'].nunique():,}")
    print(f"Branches (raw clean):  {master['branch_clean'].nunique():,}")
    print(f"Branches (normalized): {master['branch_norm'].nunique():,}")
    print(f"Year coverage in long table: {sorted(long['year'].unique().tolist())}")
    print(f"Category coverage in long table: {sorted(long['category'].unique().tolist())}")


if __name__ == "__main__":
    main()
