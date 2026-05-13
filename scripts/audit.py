"""
TNEA College Finder - sanity audit on data/colleges_master.csv and data/cutoffs_long.csv.

Checks:
  1. Row counts, key uniqueness, value ranges
  2. Cutoff ordering by category (OC should be the toughest in most rows)
  3. Year-over-year volatility per (college, branch, category)
  4. Duplicate college codes <-> names (same code, different names)
  5. Branch name consistency (likely typos / near-duplicates per college)
  6. Outliers (very low / very high cutoffs)
  7. Missing-data patterns (rows with NO cutoffs at all)
  8. Self-supporting vs regular pairs (SS should usually be lower or equal)
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
MASTER = ROOT / "data" / "colleges_master.csv"
LONG = ROOT / "data" / "cutoffs_long.csv"

CATEGORIES = ["OC", "BC", "BCM", "MBC", "SC", "SCA", "ST"]
YEARS = [2025, 2024, 2023, 2022, 2021]


def section(title: str) -> None:
    print()
    print("=" * 72)
    print(f" {title}")
    print("=" * 72)


def main() -> None:
    m = pd.read_csv(MASTER, encoding="utf-8-sig")
    l = pd.read_csv(LONG, encoding="utf-8-sig")

    # 1. Basic shape & keys
    section("1. Basic shape & key uniqueness")
    print(f"Master rows: {len(m):,}")
    print(f"Long rows:   {len(l):,}")
    print(f"Unique college codes:  {m['college_code'].nunique():,}")
    print(f"Unique college names:  {m['college_name'].nunique():,}")
    print(f"Unique (code,name):    {m.groupby(['college_code','college_name']).ngroups:,}")
    print(f"Unique branches:       {m['branch_clean'].nunique():,}")
    dup = m.duplicated(subset=["college_code", "college_name", "branch_raw"], keep=False).sum()
    print(f"Duplicate (code,name,branch_raw) rows: {dup}  (expected 0)")

    # Codes mapping to multiple names
    dupe_codes = (
        m.groupby("college_code")["college_name"].nunique().pipe(lambda s: s[s > 1])
    )
    print(f"\nCollege codes mapping to >1 college_name: {len(dupe_codes)}")
    if len(dupe_codes):
        print("  (top 10)")
        for code, n in dupe_codes.head(10).items():
            names = m[m["college_code"] == code]["college_name"].unique()
            print(f"  code {code} ({n} names):")
            for nm in names[:3]:
                print(f"     - {nm[:90]}")
            if len(names) > 3:
                print(f"     ... and {len(names)-3} more")

    # Names mapping to multiple codes
    dupe_names = (
        m.groupby("college_name")["college_code"].nunique().pipe(lambda s: s[s > 1])
    )
    print(f"\nCollege names mapping to >1 college_code: {len(dupe_names)}")
    if len(dupe_names):
        for name, n in dupe_names.head(5).items():
            codes = m[m["college_name"] == name]["college_code"].unique()
            print(f"  '{name[:80]}' -> codes {list(codes)}")

    # 2. Cutoff ordering
    section("2. Cutoff ordering (OC >= BC >= MBC >= BCM >= SC >= SCA >= ST?)")
    print("This is a general expectation, not a hard rule. Counting violations only.")
    expected = ["OC", "BC", "MBC", "BCM", "SC", "SCA", "ST"]
    for yr in YEARS:
        cols = [f"{c}_{yr}" for c in expected]
        sub = m[cols].dropna(how="all")
        violations = 0
        big_violations = 0
        for i in range(len(expected) - 1):
            a = sub[cols[i]]
            b = sub[cols[i + 1]]
            mask = a.notna() & b.notna() & (a < b)
            violations += int(mask.sum())
            big_violations += int((a.notna() & b.notna() & (b - a > 5)).sum())
        non_null_pairs = sum(
            (sub[cols[i]].notna() & sub[cols[i + 1]].notna()).sum()
            for i in range(len(expected) - 1)
        )
        print(
            f"  {yr}: {violations:>5,} order violations / "
            f"{non_null_pairs:>6,} comparable pairs "
            f"({violations / max(non_null_pairs,1) * 100:5.1f}%)"
            f"   |   big (>5 mark gap): {big_violations}"
        )

    # 3. Year-over-year volatility per (college, branch, category)
    section("3. Year-over-year volatility (large jumps suggest data errors)")
    long = l.copy()
    long = long.sort_values(["college_code", "branch_clean", "category", "year"])
    long["prev_cutoff"] = long.groupby(
        ["college_code", "branch_clean", "category"]
    )["cutoff"].shift(1)
    long["delta"] = (long["cutoff"] - long["prev_cutoff"]).abs()
    big = long[long["delta"] > 30].copy()
    print(f"Year-over-year cutoff changes > 30 marks: {len(big)} rows")
    if len(big):
        print("  Sample of largest jumps:")
        top = big.nlargest(10, "delta")[
            ["college_code", "college_name", "branch_short", "category", "year", "prev_cutoff", "cutoff", "delta"]
        ]
        for _, r in top.iterrows():
            print(
                f"  code {int(r['college_code']):>4}  {r['branch_short']:<8}  "
                f"{r['category']:>3} {int(r['year'])}: "
                f"{r['prev_cutoff']:.1f} -> {r['cutoff']:.1f}  (delta={r['delta']:.1f})  "
                f"{str(r['college_name'])[:50]}"
            )

    # 4. Branch name consistency per college
    section("4. Branch-name fuzzy duplicates within the same college")
    suspicious = []
    for code, grp in m.groupby("college_code"):
        branches = grp["branch_clean"].unique().tolist()
        for i, b1 in enumerate(branches):
            for b2 in branches[i + 1:]:
                if b1 == b2:
                    continue
                # Normalize spaces/punct/case for comparison
                n1 = "".join(c.lower() for c in b1 if c.isalnum())
                n2 = "".join(c.lower() for c in b2 if c.isalnum())
                if n1 and n1 == n2:
                    suspicious.append((code, b1, b2))
    print(f"Pairs differing only in whitespace/punctuation: {len(suspicious)}")
    for code, b1, b2 in suspicious[:10]:
        print(f"  code {code}: '{b1}'  VS  '{b2}'")

    # 5. Outliers
    section("5. Outlier cutoffs")
    very_low = l[l["cutoff"] < 80]
    very_high = l[l["cutoff"] > 199.5]
    print(f"Cutoffs < 80:    {len(very_low)} rows")
    print(f"Cutoffs > 199.5: {len(very_high)} rows  (perfect / near-perfect scorers)")
    print("\nDistribution of very-low cutoffs by category:")
    print(very_low["category"].value_counts().to_string())
    print("\nSample of rows < 80:")
    for _, r in very_low.head(10).iterrows():
        print(
            f"  code {int(r['college_code']):>4}  {r['branch_short']:<7}  "
            f"{r['category']:>3} {int(r['year'])}: {r['cutoff']:.1f}  "
            f"{str(r['college_name'])[:55]}"
        )

    # 6. Rows with no cutoffs at all (would be dead weight in finder)
    section("6. Rows in master with ZERO cutoffs (any category, any year)")
    cutoff_cols = [f"{c}_{y}" for c in CATEGORIES for y in YEARS]
    empty_rows = m[m[cutoff_cols].isna().all(axis=1)]
    print(f"Rows with no cutoff data at all: {len(empty_rows)}")
    if len(empty_rows):
        print("  Sample:")
        for _, r in empty_rows.head(10).iterrows():
            print(f"  code {r['college_code']}  {r['branch_clean']}  ({r['college_name'][:50]})")

    # 7. SS vs non-SS pairs
    section("7. Self-supporting vs regular pairs (SS usually lower or equal)")
    paired = (
        m.groupby(["college_code", "branch_clean", "is_self_supporting"])
        .size()
        .reset_index(name="n")
    )
    pivot = paired.pivot_table(
        index=["college_code", "branch_clean"],
        columns="is_self_supporting",
        values="n",
        fill_value=0,
    ).reset_index()
    pivot.columns = ["college_code", "branch_clean", "regular", "ss"]
    both = pivot[(pivot["regular"] > 0) & (pivot["ss"] > 0)]
    print(f"(college, branch_clean) pairs with BOTH regular and SS rows: {len(both)}")
    # Compare 2025 OC for these where possible
    mismatches = 0
    examples = []
    for _, r in both.iterrows():
        code = r["college_code"]
        br = r["branch_clean"]
        reg = m[(m["college_code"] == code) & (m["branch_clean"] == br) & (~m["is_self_supporting"])]
        ss = m[(m["college_code"] == code) & (m["branch_clean"] == br) & (m["is_self_supporting"])]
        if reg.empty or ss.empty:
            continue
        rv = reg["OC_2025"].iloc[0]
        sv = ss["OC_2025"].iloc[0]
        if pd.notna(rv) and pd.notna(sv) and sv > rv:
            mismatches += 1
            if len(examples) < 5:
                examples.append((code, br, rv, sv))
    print(f"Cases where SS 2025 OC > regular 2025 OC: {mismatches}")
    for code, br, rv, sv in examples:
        print(f"  code {code}  {br}: regular={rv}  SS={sv}")

    # 8. Per-category coverage table
    section("8. Coverage matrix (filled cells in master)")
    total = len(m)
    print(f"{'Cat':<5} {'2025':>8} {'2024':>8} {'2023':>8} {'2022':>8} {'2021':>8}   total")
    for cat in CATEGORIES:
        counts = [m[f"{cat}_{y}"].notna().sum() for y in YEARS]
        print(f"{cat:<5}", " ".join(f"{c:>8,}" for c in counts), f"  {sum(counts):>7,}")
    print(f"\nTotal possible cells: {total * 7 * 5:,}")
    print(f"Total filled cells:   {sum(m[f'{c}_{y}'].notna().sum() for c in CATEGORIES for y in YEARS):,}")


if __name__ == "__main__":
    main()
