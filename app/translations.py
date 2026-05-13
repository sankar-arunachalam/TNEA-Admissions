"""Translation strings for TNEA College Finder.

Two languages: English (en) and Tamil (ta).
Designed so non-developers can edit Tamil text directly — keys are stable.
"""

from __future__ import annotations

CATEGORY_LABELS = {
    "en": {
        "OC": "OC — Open / General",
        "BC": "BC — Backward Class",
        "BCM": "BCM — Backward Class (Muslim)",
        "MBC": "MBC — Most Backward Class",
        "SC": "SC — Scheduled Caste",
        "SCA": "SCA — SC Arunthathiyar",
        "ST": "ST — Scheduled Tribe",
    },
    "ta": {
        "OC": "OC — பொது / ஒதுக்கீடு இல்லை",
        "BC": "BC — பிற்படுத்தப்பட்ட வகுப்பினர்",
        "BCM": "BCM — பிற்படுத்தப்பட்டோர் (இஸ்லாமியர்)",
        "MBC": "MBC — மிகவும் பிற்படுத்தப்பட்ட வகுப்பினர்",
        "SC": "SC — பட்டியல் சாதியினர்",
        "SCA": "SCA — பட்டியல் சாதி அருந்ததியர்",
        "ST": "ST — பழங்குடியினர்",
    },
}


T = {
    "en": {
        "title": "TNEA College Finder",
        "attribution": "From — ValarHub",
        "tagline": "Find Tamil Nadu engineering colleges and branches you can get into — based on your TNEA cutoff.",
        "language_label": "Language",
        "your_mark": "Your TNEA mark (out of 200)",
        "mark_placeholder": "e.g. 185.5",
        "choose_category": "— Choose community —",
        "choose_year": "— Choose year —",
        "range_placeholder_lo": "Lower bound",
        "range_placeholder_hi": "Upper bound",
        "range_custom_need_both": "Enter **both** lower and upper cutoff to search in custom mode.",
        "mode_needs_mark": "Enter your **mark** above (decimals allowed), or switch to **Custom range**.",
        "prompt_set_filters": (
            "Select your **community**, **year**, and a cutoff range: enter your **TNEA mark** "
            "(decimals like 185.25 are allowed) for Safe / Match / Reach, **or** use **Custom range** "
            "with lower and upper bounds. Results appear below once everything required is set."
        ),
        "share_mark_range": "{lo}–{hi}",
        "your_category": "Your community",
        "year_label": "Compare against year",
        "mode_label": "Show me",
        "mode_safe": "Safe",
        "mode_match": "Match",
        "mode_reach": "Reach",
        "mode_custom": "Custom range",
        "mode_safe_help": "Colleges with cutoffs well below your mark — almost certain to get in.",
        "mode_match_help": "Cutoffs close to your mark — your realistic options.",
        "mode_reach_help": "Cutoffs slightly above your mark — possible in later rounds.",
        "mode_custom_help": "Enter the lower and upper cutoff bounds you want to search.",
        "range_label": "Cutoff range",
        "range_low": "Lower cutoff",
        "range_high": "Higher cutoff",
        "range_help": "Showing colleges whose {year} {cat} cutoff falls in this range.",
        "branch_filter": "Filter by branch (optional)",
        "branch_filter_help": (
            "**{n}** distinct courses from the TNEA sheet — open the list, **scroll**, or "
            "**type** to jump to a name. Leave empty to include all branches."
        ),
        "branch_filter_count": "Showing **{n}** course rows (dropdown may only preview a few; scroll or type to see all).",
        "search_college": "Search college by name (optional)",
        "search_college_placeholder": "Type a name, area, or keyword…",
        "ss_toggle": "Include self-supporting (SS) seats",
        "ss_help": "SS seats have separate, usually slightly lower, cutoffs.",
        "group_toggle": "Group results by college",
        "group_help": "On: one card per college with eligible branches listed. Off: one card per branch.",
        "advanced": "More filters",
        "hero_about": "What is this?",
        "reset_filters": "Reset filters",
        "find_button": "Find my colleges",
        "result_header": "{n:,} options for {cat} in {year}",
        "result_header_one": "1 option for {cat} in {year}",
        "result_header_grouped": "{n_colleges:,} colleges  ·  {n_options:,} branches  ·  {cat} {year}",
        "result_empty": (
            "No matches with these filters. **Try:** switch to **Match** or **Custom** "
            "(set the cutoff range to **0–your mark**), pick another **community** or **year**, "
            "clear **branch** filters and the **college name** search, or turn **SS seats** on."
        ),
        "result_fallback_band": (
            "No college had a **{year} {cat}** closing cutoff between **{lo}** and **{hi}**. "
            "Below is the full list where the cutoff is **at or below your mark ({mark})** — "
            "use **Custom range** if you want a narrower band."
        ),
        "single_branch_strip": "Showing only: **{branch}**",
        "share_my_title": "Share your eligibility list",
        "share_my_button": "Share on WhatsApp",
        "share_tool_button": "Share this tool with a friend",
        "share_one_button": "Share",
        "trend_button": "5-year trend across all communities",
        "trend_year": "Year",
        "trend_caption": "Bold column = your community ({cat}).",
        "trend_chart_caption": "5-year cutoff trend at this college + branch",
        "code_label": "TNEA code",
        "branch_label": "Branch",
        "branches_label": "Eligible branches",
        "ss_badge": "Self-supporting",
        "showing_top": "Showing top {shown:,} of {total:,}. Use filters above to narrow down, or click below.",
        "show_all_button": "Show all {n:,}",
        "more_branches": "+{n} more",
        "result_expand_hint": "Results are **collapsed** — click a row to open branches, WhatsApp share, and 5-year trends.",
        "expander_college_suffix": "{n_br} branches · top cutoff {top}",
        "expander_flat_suffix": "{branch} · {cutoff}",
        "footer_disclaimer": (
            "**Disclaimer:** Cutoffs sourced from TNEA's published data for 2021–2025. "
            "Use this tool as guidance only — actual cutoffs may vary across rounds and years, "
            "and TNEA's official allotment is final. This tool is not affiliated with TNEA, "
            "Anna University, or the Government of Tamil Nadu."
        ),
        "footer_credit": "Built to help every Tamil Nadu engineering aspirant make an informed choice. Share freely.",
        "no_cutoff_warning": "Some branches list a very low cutoff (below 90). This usually means TNEA had no allottee for that category in early rounds, not that the seat is easy to get. Treat with caution.",
        "share_text_my": (
            "My TNEA mark is {mark} ({cat}). I have {n} eligible engineering "
            "college + branch options in Tamil Nadu. Find yours: {url}"
        ),
        "share_text_one": (
            "{college} — {branch}: TNEA {year} {cat} cutoff was {cutoff}. "
            "Find colleges for your TNEA mark: {url}"
        ),
        "share_text_college": (
            "{college}: {n} branches I'm eligible for with TNEA {mark} ({cat}) — {branches}. "
            "Find colleges for your mark: {url}"
        ),
        "share_text_tool": (
            "Tamil Nadu engineering aspirants — type your TNEA mark and see ALL "
            "eligible colleges instantly. Free, no signup. {url}"
        ),
        "share_tool_url_fallback": (
            "Open this page in your browser and copy the full address from the bar "
            "(or set APP_URL in Streamlit Cloud secrets for an automatic link)."
        ),
    },
    "ta": {
        "title": "TNEA கல்லூரி தேடல்",
        "attribution": "மூலம் — ValarHub",
        "tagline": "உங்கள் TNEA மதிப்பெண்ணுக்கு ஏற்ற தமிழ்நாடு பொறியியல் கல்லூரிகள் மற்றும் துறைகள்.",
        "language_label": "மொழி",
        "your_mark": "உங்கள் TNEA மதிப்பெண் (200-க்கு)",
        "mark_placeholder": "எ.கா. 185.5",
        "choose_category": "— சமூகத்தைத் தேர்ந்தெடுக்க —",
        "choose_year": "— ஆண்டைத் தேர்ந்தெடுக்க —",
        "range_placeholder_lo": "குறைந்த வரம்பு",
        "range_placeholder_hi": "அதிக வரம்பு",
        "range_custom_need_both": "தனிப்பயன் பயன்முறையில் தேட, **குறைந்த** மற்றும் **அதிக** கட்-ஆஃப் இரண்டையும் உள்ளிடவும்.",
        "mode_needs_mark": "மேலே **மதிப்பெண்ணை** உள்ளிடவும் (தசமம் இடலாம்), அல்லது **தனிப்பயன் வரம்பு** வேண்டும்.",
        "prompt_set_filters": (
            "**சமூகம்**, **ஆண்டு** மற்றும் கட்-ஆஃப் வரம்பை அமைக்கவும்: பாதுகாப்பு/பொருத்தம்/முயற்சிக்கு **TNEA மதிப்பெண்** "
            "(185.25 போல் தசமம் இடலாம்), அல்லது **தனிப்பயன் வரம்பு** மூலம் வரம்புகளைக் கொடுக்கவும். "
            "தேவையானவை அமைந்ததும் முடிவுகள் கீழே தோன்றும்."
        ),
        "share_mark_range": "{lo}–{hi}",
        "your_category": "உங்கள் சமூகம்",
        "year_label": "எந்த ஆண்டுடன் ஒப்பிட",
        "mode_label": "காட்டவேண்டியது",
        "mode_safe": "உறுதி",
        "mode_match": "பொருத்தம்",
        "mode_reach": "முயற்சி",
        "mode_custom": "தனிப்பயன் வரம்பு",
        "mode_safe_help": "உங்கள் மதிப்பெண்ணுக்கு கீழே — கட்டாயம் சேரக்கூடிய கல்லூரிகள்.",
        "mode_match_help": "உங்கள் மதிப்பெண்ணுக்கு அருகில் — யதார்த்த தேர்வுகள்.",
        "mode_reach_help": "உங்கள் மதிப்பெண்ணுக்கு சற்று மேல் — பின் சுற்றுகளில் வாய்ப்பு.",
        "mode_custom_help": "குறைந்த மற்றும் அதிக கட்-ஆஃப் எல்லைகளை உள்ளிடவும்.",
        "range_label": "கட்-ஆஃப் வரம்பு",
        "range_low": "குறைந்த கட்-ஆஃப்",
        "range_high": "அதிக கட்-ஆஃப்",
        "range_help": "{year} {cat} கட்-ஆஃப் இந்த வரம்பில் உள்ள கல்லூரிகள் காட்டப்படுகின்றன.",
        "branch_filter": "துறை தேர்வு (விருப்பத்தேர்வு)",
        "branch_filter_help": (
            "TNEA விவரப்பட்டியலில் **{n}** தனிப் பாடப்பிரிவுகள் — பட்டியலைத் திறந்து **உருட்டவும்**, "
            "அல்லது **தட்டச்சு** செய்து தேடவும். எல்லா துறைகளுக்கும் காலியாக விடவும்."
        ),
        "branch_filter_count": "**{n}** பாடப்பிரிவுகள் — கீழ்தோன்றலில் சில மட்டுமே தெரியலாம்; உருட்டவும் அல்லது தட்டச்சு செய்யவும்.",
        "search_college": "கல்லூரி பெயரால் தேடு (விருப்பத்தேர்வு)",
        "search_college_placeholder": "பெயர், பகுதி, அல்லது சொல் தட்டச்சு செய்யுங்கள்…",
        "ss_toggle": "சுய நிதி (SS) இடங்களையும் சேர்",
        "ss_help": "SS இடங்களுக்கு தனி கட்-ஆஃப், பெரும்பாலும் சற்று குறைவாக இருக்கும்.",
        "group_toggle": "கல்லூரி வாரியாக குழுப்படுத்து",
        "group_help": "இயக்கம்: ஒவ்வொரு கல்லூரிக்கும் ஒரு அட்டை. நிறுத்தம்: ஒவ்வொரு துறைக்கும் ஒரு அட்டை.",
        "advanced": "மேலதிக வடிகட்டிகள்",
        "hero_about": "இது என்ன?",
        "reset_filters": "வடிகட்டிகளை மீட்டமை",
        "find_button": "எனக்கான கல்லூரிகளை தேடு",
        "result_header": "{cat} ({year}) — {n:,} விருப்பங்கள்",
        "result_header_one": "{cat} ({year}) — 1 விருப்பம்",
        "result_header_grouped": "{n_colleges:,} கல்லூரிகள்  ·  {n_options:,} துறைகள்  ·  {cat} {year}",
        "result_empty": (
            "தற்போதைய வடிகட்டிகளுக்கு பொருந்தும் கல்லூரிகள் இல்லை. **முயற்சி:** "
            "**பொருத்தம் (Match)** அல்லது **தனிப்பயன் (Custom)**க்கு மாற்றுங்கள் "
            "(கட்-ஆஃப் வரம்பு **0–உங்கள் மதிப்பெண்**), வேறு **சமூகம்** அல்லது **ஆண்டு**, "
            "**துறை** வடிகட்டியையும் **கல்லூரி தேடலையும்** காலியாக்குங்கள், **SS இடங்களை** இயக்குங்கள்."
        ),
        "result_fallback_band": (
            "**{year} {cat}**-க்கு **{lo}–{hi}** வரம்பில் முடிவு கட்-ஆஃப் எதுவும் இல்லை. "
            "கீழே **உங்கள் மதிப்பெண் ({mark})க்கு வரை** எல்லா கல்லூரி வரிசைகள் காட்டப்படுகின்றன — "
            "வரம்பை இறுக்க **தனிப்பயன் வரம்பு** பயன்படுத்துங்கள்."
        ),
        "single_branch_strip": "காட்டப்படுவது: **{branch}** மட்டும்",
        "share_my_title": "உங்கள் தகுதி பட்டியலை பகிருங்கள்",
        "share_my_button": "WhatsApp இல் பகிர்",
        "share_tool_button": "நண்பருடன் இந்த கருவியை பகிர்",
        "share_one_button": "பகிர்",
        "trend_button": "5-ஆண்டு – எல்லா சமூகங்கள்",
        "trend_year": "ஆண்டு",
        "trend_caption": "தடித்த நெடுவரிசை = உங்கள் சமூகம் ({cat}).",
        "trend_chart_caption": "இந்த கல்லூரி + துறையின் 5-ஆண்டு கட்-ஆஃப் போக்கு",
        "code_label": "TNEA குறியீடு",
        "branch_label": "துறை",
        "branches_label": "தகுதி உள்ள துறைகள்",
        "ss_badge": "சுய நிதி",
        "showing_top": "மொத்தம் {total:,} இல் முதல் {shown:,} காட்டப்படுகிறது. மேலே வடிகட்டியோ கீழே பொத்தானையோ பயன்படுத்தவும்.",
        "show_all_button": "எல்லா {n:,} முடிவுகளையும் காட்டு",
        "more_branches": "+{n} மேலும்",
        "result_expand_hint": "முடிவுகள் **சுருக்கமாக** உள்ளன — துறைகள், WhatsApp பகிர்வு, 5-ஆண்டு போக்குக்கு வரிசையில் சொடுக்கவும்.",
        "expander_college_suffix": "{n_br} துறைகள் · மேல் கட்-ஆஃப் {top}",
        "expander_flat_suffix": "{branch} · {cutoff}",
        "footer_disclaimer": (
            "**குறிப்பு:** 2021–2025 ஆண்டுகளுக்கான TNEA வெளியிட்ட தரவுகளிலிருந்து. "
            "வழிகாட்டியாக மட்டுமே பயன்படுத்தவும் — உண்மையான கட்-ஆஃப் மாறுபடும், "
            "TNEA-வின் அதிகாரப்பூர்வ ஒதுக்கீடே இறுதியானது. இந்த கருவி TNEA, "
            "அண்ணா பல்கலைக்கழகம் அல்லது தமிழ்நாடு அரசுடன் தொடர்பில்லாதது."
        ),
        "footer_credit": "ஒவ்வொரு தமிழ்நாடு பொறியியல் ஆர்வலருக்கும் சரியான தேர்வு செய்ய உதவ. தாராளமாக பகிருங்கள்.",
        "no_cutoff_warning": "சில துறைகளுக்கு மிக குறைந்த கட்-ஆஃப் (90-க்கு கீழ்) காட்டப்படலாம். இது அந்த ஆண்டு அந்த வகைக்கு மாணவர் சேரவில்லை என்பதே, இடம் எளிதாக கிடைக்கும் என்பதல்ல. கவனத்துடன் பயன்படுத்தவும்.",
        "share_text_my": (
            "என் TNEA மதிப்பெண் {mark} ({cat}). நான் {n} கல்லூரி + துறை "
            "விருப்பங்களுக்கு தகுதியானவன்/ள். உங்கள் விருப்பங்களை இங்கே பாருங்கள்: {url}"
        ),
        "share_text_one": (
            "{college} — {branch}: TNEA {year} {cat} கட்-ஆஃப் {cutoff}. "
            "உங்கள் மதிப்பெண்ணுக்கான கல்லூரிகளை பாருங்கள்: {url}"
        ),
        "share_text_college": (
            "{college}: TNEA {mark} ({cat}) உடன் நான் தகுதியான {n} துறைகள் — {branches}. "
            "உங்கள் மதிப்பெண்ணுக்கான கல்லூரிகளை பாருங்கள்: {url}"
        ),
        "share_text_tool": (
            "தமிழ்நாடு பொறியியல் ஆர்வலர்களே — உங்கள் TNEA மதிப்பெண் கொடுத்து "
            "தகுதியான கல்லூரிகளை உடனே பாருங்கள். இலவசம், பதிவு தேவையில்லை. {url}"
        ),
        "share_tool_url_fallback": (
            "இந்தப் பக்கத்தை உலாவியில் திறந்து, முகவரிப்பட்டியில் உள்ள முழு இணைப்பை நகலெடுக்கவும். "
            "(அல்லது Streamlit Cloud secrets-ல் APP_URL அமைக்கவும்.)"
        ),
    },
}


def t(lang: str, key: str, **fmt) -> str:
    """Look up a translation key with optional .format() args."""
    text = T.get(lang, T["en"]).get(key) or T["en"].get(key, key)
    return text.format(**fmt) if fmt else text
