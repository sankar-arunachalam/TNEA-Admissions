# TNEA College Finder

Find Tamil Nadu engineering colleges and branches a student is eligible for,
based on their TNEA cutoff mark and category.

- **3,906** college + branch combinations
- **467** unique colleges
- **97** unique engineering branches
- **7** TNEA reservation categories: OC, BC, BCM, MBC, SC, SCA, ST
- **5 years** of cutoffs: 2021–2025
- Bilingual UI: English + தமிழ்
- **Safe / Match / Reach / Custom** eligibility modes (counselling-style buckets)
- **Cutoff range slider** — see exactly the band that fits your mark
- **Grouped by college** — one card per college with branch chips; toggle for flat list
- **College name search** — type "Anna", "Sairam", "Chennai" etc.
- **All 7 communities' 5-year trends** in every result card
- One-tap WhatsApp sharing — your list, a single college, or the tool itself
- Fully **deep-linkable URLs** — share a filter state, recipient sees the same view
- Free to deploy and run — no domain, no hosting fees

## Project layout

```
TNEA Admissions/
├── streamlit_app.py            <- Streamlit entry point (root, deploy ready)
├── app/
│   ├── search.py               <- data loaders + eligibility query logic
│   └── translations.py         <- English + Tamil UI strings
├── data/
│   ├── colleges_master.csv     <- wide-format master (human-editable)
│   └── cutoffs_long.csv        <- long-format, auto-built (app reads this)
├── schema/
│   └── SCHEMA.md               <- full data schema docs
├── scripts/
│   ├── build_master.py         <- builds master + long from the Excel
│   ├── rebuild_long.py         <- rebuilds long after manual edits to master
│   └── audit.py                <- data sanity audit (run anytime)
├── TNEA Colleges.xlsx          <- source data (cutoffs sheet "Cutoff for All")
├── requirements.txt
└── .streamlit/config.toml      <- theme + privacy
```

## Run locally

```powershell
pip install -r requirements.txt
python scripts/build_master.py        # only needed once or when Excel changes
streamlit run streamlit_app.py
```

Open the URL Streamlit prints (usually `http://localhost:8501`).

## Deploy free on Streamlit Community Cloud

This gets you a public URL like `tnea-college-finder.streamlit.app` at zero cost.

1. Create a free [GitHub](https://github.com) account if you don't have one.
2. Push this folder to a new public GitHub repo (e.g. `tnea-college-finder`).
3. Go to [share.streamlit.io](https://share.streamlit.io) and sign in with GitHub.
4. Click **New app** → choose your repo → set **Main file path** to
   `streamlit_app.py`. Leave Python version on default. Click **Deploy**.
5. In ~2 minutes you'll have a live URL. Share it on WhatsApp.

### Custom subdomain

In the Streamlit app settings, you can pick any unused subdomain
(`tnea-finder.streamlit.app`, `tn-colleges.streamlit.app`, etc.) — no
purchase required.

### One-time setup: make WhatsApp share links absolute

The WhatsApp share buttons embed the app's URL. By default they use a
relative URL (`?cutoff=180...`) which doesn't render as a clickable link
inside WhatsApp messages. To fix that once your subdomain is chosen:

1. In Streamlit Cloud, open your app → **Settings → Secrets**.
2. Add this single line, replacing the URL with your actual app URL:

   ```toml
   APP_URL = "https://tnea-college-finder.streamlit.app"
   ```

3. Save. The app picks it up automatically on next reload. WhatsApp messages
   will now contain a fully-qualified link.

## Sharing the app on WhatsApp

The app includes **three kinds of WhatsApp share buttons** on every results page:

1. **Share my eligibility list** — pre-fills a message with the user's
   TNEA mark, community, result count, and a deep link.
2. **Share this tool with a friend** — generic message, no personal data.
3. **Share** (per college) — when grouped, pre-fills with that college's name
   and the branches the student is eligible for. When in flat list mode,
   pre-fills with a single college + branch + cutoff.

All three use the universal `https://wa.me/?text=...` pattern — works on every
phone with WhatsApp installed, no Meta Cloud API setup needed.

### Shareable URL state

Every filter and toggle is encoded in the URL. A link like

```
https://tnea-college-finder.streamlit.app/?mark=155&cat=BC&year=2025&mode=safe&lang=ta&branch=CSE,IT
```

opens with the user's exact filter state pre-populated. Great for sharing
"my eligible colleges" with a friend in the same situation.

## Updating the data

When TNEA publishes the next year's cutoffs:

1. Add columns `OC_2026 .. ST_2026` to `TNEA Colleges.xlsx` (sheet
   `Cutoff for All`) **or** to `data/colleges_master.csv` directly.
2. If you edited the master CSV: `python scripts/rebuild_long.py`
3. If you edited the Excel: `python scripts/build_master.py`
4. Commit the updated CSVs to GitHub. Streamlit Cloud auto-redeploys.

See `schema/SCHEMA.md` for the full data dictionary.

## License + disclaimer

Cutoff data is from TNEA's published cutoffs for 2021–2025. This tool is
**not affiliated** with TNEA, Anna University, or the Government of Tamil Nadu.
Cutoffs are provided as guidance only — actual cutoffs may vary across rounds
and years, and TNEA's official allotment is final.
