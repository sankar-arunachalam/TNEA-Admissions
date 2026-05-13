"""
TNEA College Finder - rebuild the long-format file used by the app.

Reads:  ../data/colleges_master.csv (human-edited, wide format)
Writes: ../data/cutoffs_long.csv    (one row per college+branch+category+year)

Run after editing the master CSV. Does NOT touch the master file.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from build_master import CATEGORIES, YEARS, build_long  # type: ignore

ROOT = Path(__file__).resolve().parent.parent
MASTER_CSV = ROOT / "data" / "colleges_master.csv"
LONG_CSV = ROOT / "data" / "cutoffs_long.csv"


def main() -> None:
    master = pd.read_csv(MASTER_CSV, encoding="utf-8-sig")

    for cat in CATEGORIES:
        for yr in YEARS:
            col = f"{cat}_{yr}"
            if col not in master.columns:
                master[col] = pd.NA

    long = build_long(master)
    long.to_csv(LONG_CSV, index=False, encoding="utf-8-sig")
    print(f"Rebuilt {LONG_CSV.relative_to(ROOT)} ({len(long):,} rows)")
    print(f"Category coverage: {sorted(long['category'].unique().tolist())}")
    print(f"Year coverage: {sorted(long['year'].unique().tolist())}")


if __name__ == "__main__":
    main()
