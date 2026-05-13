# TNEA College Finder — Data Schema

> **Project**: TNEA College Finder — find colleges and branches a Tamil Nadu
> engineering aspirant is eligible for, given their TNEA cutoff mark and
> category.

Two CSV files live in `data/`:

1. **`colleges_master.csv`** — wide format, **human-editable**. One row per
   `(college, branch)`. This is the file you maintain.
2. **`cutoffs_long.csv`** — long format, **auto-generated**. One row per
   `(college, branch, category, year)`. The TNEA College Finder app reads
   this file. Do **not** edit it by hand — rerun `scripts/rebuild_long.py`
   after editing the master.

---

## `data/colleges_master.csv`

### Identity columns

| Column | Type | Required | Notes |
|---|---|---|---|
| `college_code` | int | yes | TNEA college code (e.g. `1` = Anna University CEG) |
| `college_name` | str | yes | **Canonical** name (longest variant when the source has spelling variants). One unique name per code. |
| `college_name_raw` | str | yes | Original per-row name from the source Excel, preserved for audit. May differ from `college_name` due to punctuation/abbreviation. |
| `college_short_name` | str | optional | E.g. `Anna Univ CEG`, `CIT Coimbatore`. Empty for now — fill as you go. |
| `college_type` | str | optional | One of: `Government`, `Government Aided`, `Self-Financing`, `University Department`, `Anna University Constituent`. Empty for now. |
| `district` | str | optional | District name (e.g. `Chennai`, `Coimbatore`). Empty for now. |
| `region` | str | optional | One of: `Chennai`, `Coimbatore`, `Madurai`, `Trichy`, `Tirunelveli`, `Salem`, `Vellore`, `Other`. Empty for now. |
| `nirf_rank` | int | optional | NIRF Engineering rank (if applicable). Empty for now. |

### Branch columns

| Column | Type | Notes |
|---|---|---|
| `branch_raw` | str | Original branch text from the source Excel. Kept verbatim for audit. |
| `branch_clean` | str | `branch_raw` with `(SS)` suffix removed and whitespace normalized. Preserves the source casing exactly — useful when checking against TNEA's printed lists. |
| `branch_norm` | str | **Canonical display name** — smart Title Case (with "and", "of", "the" kept lowercase), acronyms restored (AI, ML, VLSI, IoT, IT, SS), known typos fixed (e.g., `Bussiness` → `Business`), and inner paren whitespace tightened (`( foo )` → `(foo)`). This is what the app uses for the branch dropdown, grouping, and display. Multiple raw forms can collapse to one `branch_norm` (e.g., `ARTIFICIAL INTELLIGENCE AND DATA SCIENCE` and `Artificial Intelligence and Data Science` both become `Artificial Intelligence and Data Science`). |
| `branch_short` | str | Compact code: `CSE`, `ECE`, `EEE`, `IT`, `MECH`, `CIVIL`, `AI&DS`, `AI&ML`, `BME`, etc. May be empty for niche/specialization branches with no canonical short code. |
| `degree` | str | `B.E./B.Tech`, `B.Arch`, or `B.Plan`. |
| `is_self_supporting` | bool | `True` if the original branch name had the `(SS)` suffix. |
| `has_any_cutoff` | bool | `True` if any of the 35 cutoff cells for this row is populated. `False` for branches that were listed by TNEA but never had an allottee in 2021–2025 (filter these out in the TNEA College Finder UI). |

### Cutoff columns

There are **7 categories × 5 years = 35 cutoff columns**, named `{CATEGORY}_{YEAR}`.
All 7 categories are now populated from the source Excel (`Cutoff for All` sheet):

| Category code | Meaning |
|---|---|
| `OC` | Open Category |
| `BC` | Backward Class |
| `BCM` | Backward Class — Muslim |
| `MBC` | Most Backward Class & Denotified Communities |
| `SC` | Scheduled Caste |
| `SCA` | Scheduled Caste — Arunthathiyar |
| `ST` | Scheduled Tribe |

Years currently supported: `2025`, `2024`, `2023`, `2022`, `2021`.

So the full set of cutoff column names is:

```
OC_2025  OC_2024  OC_2023  OC_2022  OC_2021
BC_2025  BC_2024  BC_2023  BC_2022  BC_2021
BCM_2025 BCM_2024 BCM_2023 BCM_2022 BCM_2021
MBC_2025 MBC_2024 MBC_2023 MBC_2022 MBC_2021
SC_2025  SC_2024  SC_2023  SC_2022  SC_2021
SCA_2025 SCA_2024 SCA_2023 SCA_2022 SCA_2021
ST_2025  ST_2024  ST_2023  ST_2022  ST_2021
```

Each cell is a **decimal cutoff out of 200** (e.g. `199.5`). Leave blank if
the cutoff was not published, or if the branch was not offered that year.

---

## How to add new data later

### Refresh from an updated `TNEA Colleges.xlsx`

If you replace the Excel with a newer version (more rows, corrected values),
just run:

```
python scripts/build_master.py
```

This rebuilds **both** `colleges_master.csv` and `cutoffs_long.csv` from the
`Cutoff for All` sheet. ⚠️ It overwrites any manual edits to the master CSV
(e.g. district, NIRF rank). Maintain those edits in the Excel instead, or
keep them in a separate file and merge after rebuild.

### Patch a few values by hand

1. Open `data/colleges_master.csv` in Excel or Google Sheets.
2. Find the columns for the category and year you want to fill, e.g. `SC_2025`.
3. Paste your values aligned by the composite key
   `college_code` + `college_name` + `branch_raw`. This triple is guaranteed
   unique across the 3,906 rows. Some TNEA codes cover multiple campuses
   (e.g. code `1` = Anna Univ CEG, ACT, MIT, SAP), so `college_code` alone
   is **not** unique. The recommended Excel vlookup helper column is
   `=A2 & "|" & B2 & "|" & H2` (code | name | branch_raw).
4. Save as CSV (UTF-8). Make sure the file stays at `data/colleges_master.csv`.
5. From the repo root:

   ```
   python scripts/rebuild_long.py
   ```

   This regenerates `data/cutoffs_long.csv` for the TNEA College Finder app.

### Add a new year (e.g. 2026)

1. Add 7 new columns to `colleges_master.csv`: `OC_2026`, `BC_2026`, …, `ST_2026`.
2. Edit `scripts/build_master.py` and add `2026` to the top of the `YEARS` list.
3. Run `python scripts/rebuild_long.py`.

### Add metadata (district, college type, region, NIRF)

Fill the corresponding column in `colleges_master.csv` (it already exists,
just empty). Re-run `rebuild_long.py`. Empty values are fine — they just
become empty in the long file too.

### Add a new category (e.g. EWS, if TNEA introduces it)

1. Add 5 new columns to `colleges_master.csv`: `EWS_2021` … `EWS_2025`.
2. Edit `scripts/build_master.py` and add `"EWS"` to the `CATEGORIES` list.
3. Run `python scripts/rebuild_long.py`.

---

## `data/cutoffs_long.csv` (auto-generated)

One row per `(college, branch, category, year)` where a cutoff exists.

| Column | Type | Notes |
|---|---|---|
| `college_code` | int | |
| `college_name` | str | |
| `college_short_name` | str | |
| `college_type` | str | |
| `district` | str | |
| `region` | str | |
| `nirf_rank` | int / blank | |
| `branch_clean` | str | |
| `branch_short` | str | |
| `degree` | str | |
| `is_self_supporting` | bool | |
| `category` | str | one of OC, BC, BCM, MBC, SC, SCA, ST |
| `year` | int | 2021–2025 |
| `cutoff` | float | the cutoff out of 200 |

This is the file the TNEA College Finder eligibility query reads. Typical query:

> "Given a student's cutoff X, category C, year Y → return all colleges and
> branches where `cutoff <= X AND category = C AND year = Y`, sorted by
> `cutoff` descending (best-rank college on top)."

---

## Rebuilding from scratch

If you ever want to regenerate `colleges_master.csv` from the raw Excel
(e.g. you got a new master sheet), run:

```
python scripts/build_master.py
```

⚠️ This **overwrites** `colleges_master.csv`. Any manual edits you made
(SC values, district, etc.) will be lost unless you merge them back in.
Recommended workflow: keep manual edits in `colleges_master.csv` and only
rerun `build_master.py` when you have a fresh authoritative source sheet.
