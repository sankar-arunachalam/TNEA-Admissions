"""TNEA College Finder - Streamlit app.

Run locally:    streamlit run streamlit_app.py
Deploy:         push the repo to GitHub, then deploy free at https://share.streamlit.io
"""

from __future__ import annotations

import html
import os
import sys
import urllib.parse
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "app"))

from search import (  # noqa: E402
    CATEGORIES,
    YEARS,
    aggregate_stats,
    branch_options,
    find_colleges,
    load_long,
    load_master,
    parse_branch_filter_param,
    trend_all_categories,
)
from translations import CATEGORY_LABELS, t  # noqa: E402

# ----------------------------------------------------------------------------
# Page config
# ----------------------------------------------------------------------------
st.set_page_config(
    page_title="TNEA College Finder",
    layout="centered",
    initial_sidebar_state="collapsed",
    menu_items={
        "About": (
            "TNEA College Finder — find Tamil Nadu engineering colleges and "
            "branches you can get into based on your TNEA mark and community. "
            "Free, no signup. Built as a public-service tool."
        )
    },
)

MAX_MARK = 200.0
MIN_MARK = 0.0
MODES = ["safe", "match", "reach", "custom"]
DEFAULT_MODE = "match"

MASTER_CSV = ROOT / "data" / "colleges_master.csv"
LONG_CSV = ROOT / "data" / "cutoffs_long.csv"


def _file_mtime_ns(path: Path) -> int:
    """Cheap cache-bust token when CSVs change (Streamlit caches ignore disk by default)."""
    try:
        return int(path.stat().st_mtime_ns)
    except OSError:
        return 0


# ----------------------------------------------------------------------------
# Cached loaders (arguments must change when files change — see _file_mtime_ns)
# ----------------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def _load_long(_mtime_ns: int) -> pd.DataFrame:
    return load_long()


@st.cache_data(show_spinner=False)
def _load_master(_mtime_ns: int) -> pd.DataFrame:
    return load_master()


@st.cache_data(show_spinner=False)
def _branch_options(_master_mtime_ns: int) -> list[tuple[str, str]]:
    return branch_options(_load_master(_master_mtime_ns))


@st.cache_data(show_spinner=False)
def _stats(_long_mtime_ns: int, _master_mtime_ns: int) -> dict:
    return aggregate_stats()


# ----------------------------------------------------------------------------
# Query-param plumbing (deep links)
# ----------------------------------------------------------------------------
def _qp_get_optional_float(key: str, lo: float, hi: float) -> float | None:
    """Parse ``key`` from query params; missing or invalid → ``None``."""
    if key not in st.query_params:
        return None
    raw = st.query_params.get(key, "")
    if raw is None or str(raw).strip() == "":
        return None
    try:
        v = float(raw)
    except (ValueError, TypeError):
        return None
    return max(lo, min(hi, v))


def _qp_get_category_init() -> str:
    raw = str(st.query_params.get("cat", "")).strip()
    return raw if raw in CATEGORIES else ""


def _qp_get_year_init() -> str:
    raw = str(st.query_params.get("year", "")).strip()
    return raw if raw in (str(y) for y in YEARS) else ""


def _fmt_num_param(x: float) -> str:
    """Compact string for URL / WhatsApp (drops trailing zeros)."""
    xf = float(x)
    if abs(xf - round(xf)) < 1e-9:
        return str(int(round(xf)))
    s = f"{xf:.6f}".rstrip("0").rstrip(".")
    return s if s else "0"


def _mark_for_display(m: float | int) -> str:
    return _fmt_num_param(float(m))


def _filters_ready(
    mode: str,
    mark: float | None,
    category: str,
    year_val: int | None,
    range_lo: float | None,
    range_hi: float | None,
) -> bool:
    if category not in CATEGORIES or year_val is None:
        return False
    if mode == "custom":
        return range_lo is not None and range_hi is not None
    return mark is not None


def _qp_get_str(key: str, default: str, allowed: list[str]) -> str:
    raw = st.query_params.get(key, default)
    return raw if raw in allowed else default


def _qp_get_bool(key: str, default: bool) -> bool:
    raw = str(st.query_params.get(key, "1" if default else "0")).strip().lower()
    if raw in ("1", "true", "yes", "on"):
        return True
    if raw in ("0", "false", "no", "off"):
        return False
    return default


def _get_app_base_url() -> str:
    env_url = os.environ.get("APP_URL", "").strip()
    if env_url:
        return env_url.rstrip("/")
    try:
        secret_url = str(st.secrets.get("APP_URL", "")).strip()  # type: ignore[attr-defined]
        if secret_url:
            return secret_url.rstrip("/")
    except Exception:
        pass
    return ""


def _header_get(headers: object, *names: str) -> str:
    """Best-effort read of request headers (Streamlit ``st.context.headers`` API varies)."""
    if headers is None:
        return ""
    for name in names:
        try:
            v = None
            if hasattr(headers, "get"):
                v = headers.get(name)
            if v is None and hasattr(headers, "get_all"):
                try:
                    vs = headers.get_all(name)  # type: ignore[attr-defined]
                    v = vs[0] if vs else None
                except Exception:
                    v = None
            if v:
                s = str(v).strip()
                if s:
                    return s.split(",")[0].strip()
        except Exception:
            continue
    return ""


def _resolve_public_base_url() -> str:
    """Base URL for share/deep links: ``APP_URL`` / secrets, else infer from request headers."""
    configured = _get_app_base_url()
    if configured:
        return configured
    ctx = getattr(st, "context", None)
    if ctx is None:
        return ""
    headers = getattr(ctx, "headers", None)
    host = _header_get(headers, "Host", "host")
    if not host:
        return ""
    proto = _header_get(headers, "X-Forwarded-Proto", "x-forwarded-proto")
    if not proto:
        host_lc = host.split(":")[0].lower()
        if host_lc in ("localhost", "127.0.0.1", "::1") or host_lc.startswith("127."):
            proto = "http"
        else:
            proto = "https"
    proto = proto.lower()
    if proto not in ("http", "https"):
        proto = "https"
    return f"{proto}://{host}".rstrip("/")


def _build_app_url(**params) -> str:
    base = _resolve_public_base_url()
    clean = {k: v for k, v in params.items() if v not in (None, "", [])}
    if "branch" in clean and isinstance(clean["branch"], (list, tuple)):
        clean["branch"] = ",".join(clean["branch"])
    qs = urllib.parse.urlencode(clean)
    if base:
        return f"{base}/?{qs}"
    return f"?{qs}"


def _wa_share_url(text: str) -> str:
    return "https://wa.me/?text=" + urllib.parse.quote(text)


_FILTER_WIDGET_KEYS = (
    "mark",
    "category",
    "year",
    "mode",
    "range_lo_custom",
    "range_hi_custom",
    "branches",
    "college_query",
    "ss",
    "group",
)


def _reset_filters_preserve_language() -> None:
    """Clear URL + widget state so filters return to defaults (language kept)."""
    if "lang_toggle" in st.session_state:
        lang_iso = "en" if st.session_state["lang_toggle"] == "English" else "ta"
    else:
        lang_iso = _qp_get_str("lang", "en", ["en", "ta"])
    for k in _FILTER_WIDGET_KEYS:
        st.session_state.pop(k, None)
    st.session_state.pop("show_all", None)
    st.query_params.clear()
    st.query_params["lang"] = lang_iso


# ----------------------------------------------------------------------------
# Range presets
# ----------------------------------------------------------------------------
def _range_for_mode(mode: str, mark: float) -> tuple[float, float]:
    """Compute (lo, hi) cutoff range for a given Safe/Match/Reach mode."""
    m = float(mark)
    if mode == "safe":
        return (max(MIN_MARK, m - 25), max(MIN_MARK, m - 10))
    if mode == "reach":
        return (max(MIN_MARK, m - 2), min(MAX_MARK, m + 5))
    # match (default)
    return (max(MIN_MARK, m - 10), min(MAX_MARK, m))


# ----------------------------------------------------------------------------
# UI: main
# ----------------------------------------------------------------------------
def main() -> None:
    _inject_css()

    long_mtime = _file_mtime_ns(LONG_CSV)
    master_mtime = _file_mtime_ns(MASTER_CSV)

    init_lang = _qp_get_str("lang", "en", ["en", "ta"])
    lang_options = ["English", "தமிழ்"]
    if "lang_toggle" in st.session_state:
        _sel = st.session_state["lang_toggle"]
        lang = "en" if _sel == "English" else "ta"
    else:
        lang = init_lang
    idx = 0 if lang == "en" else 1

    # ------- Header: hero card (brand + attribution)
    st.markdown(
        '<div class="app-hero-card">'
        f'<p class="app-main-title">{html.escape(t(lang, "title"))}</p>'
        f'<p class="app-attribution">{html.escape(t(lang, "attribution"))}</p>'
        "</div>",
        unsafe_allow_html=True,
    )
    _rst_pad, _rst_col = st.columns([3, 2])
    with _rst_col:
        if st.button(
            t(lang, "reset_filters"),
            key="reset_filters_btn",
            type="secondary",
        ):
            _reset_filters_preserve_language()
            st.rerun()
    st.markdown(
        f'<p class="app-tagline">{html.escape(t(lang, "tagline"))}</p>',
        unsafe_allow_html=True,
    )
    widget = getattr(st, "segmented_control", None) or st.radio
    if widget is st.radio:
        st.radio(
            "lang",
            options=lang_options,
            index=idx,
            horizontal=True,
            label_visibility="collapsed",
            key="lang_toggle",
        )
    else:
        widget(
            "lang",
            options=lang_options,
            default=lang_options[idx],
            label_visibility="collapsed",
            key="lang_toggle",
        )

    with st.expander(t(lang, "hero_about"), expanded=False):
        st.markdown(
            t(lang, "tagline")
            + "\n\n"
            + t(lang, "footer_disclaimer")
        )

    # ------- Core filters: one dense row (mark | community | year)
    init_mark = _qp_get_optional_float("mark", MIN_MARK, MAX_MARK)
    init_cat = _qp_get_category_init()
    year_options = [""] + [str(y) for y in YEARS]
    init_year_s = _qp_get_year_init()
    init_mode = _qp_get_str("mode", DEFAULT_MODE, MODES)
    cat_options = [""] + CATEGORIES

    r1a, r1b, r1c = st.columns([1, 1.35, 0.85])
    with r1a:
        mark_raw = st.number_input(
            t(lang, "your_mark"),
            min_value=MIN_MARK,
            max_value=MAX_MARK,
            value=init_mark,
            step=0.1,
            format="%.2f",
            placeholder=t(lang, "mark_placeholder"),
            key="mark",
            label_visibility="visible",
        )
    mark: float | None = None if mark_raw is None else float(mark_raw)
    with r1b:
        category = st.selectbox(
            t(lang, "your_category"),
            options=cat_options,
            index=cat_options.index(init_cat),
            format_func=lambda c: (
                t(lang, "choose_category") if c == "" else CATEGORY_LABELS[lang][c]
            ),
            key="category",
        )
    with r1c:
        year_str = st.selectbox(
            t(lang, "year_label"),
            options=year_options,
            index=year_options.index(init_year_s),
            format_func=lambda y: t(lang, "choose_year") if y == "" else str(y),
            key="year",
        )
    year_val: int | None = int(year_str) if year_str else None

    # ------- Mode + range: second row (segmented pills or radio)
    mode_labels = {m: t(lang, f"mode_{m}") for m in MODES}
    mode_w = getattr(st, "segmented_control", None)
    if mode_w and mode_w is not st.radio:
        mode = mode_w(
            t(lang, "mode_label"),
            options=MODES,
            default=init_mode,
            format_func=lambda m: mode_labels[m],
            key="mode",
        )
    else:
        mode = st.radio(
            t(lang, "mode_label"),
            options=MODES,
            index=MODES.index(init_mode),
            format_func=lambda m: mode_labels[m],
            horizontal=True,
            key="mode",
        )

    range_lo: float | None
    range_hi: float | None
    if mode == "custom":
        init_lo = _qp_get_optional_float("rmin", MIN_MARK, MAX_MARK)
        init_hi = _qp_get_optional_float("rmax", MIN_MARK, MAX_MARK)
        st.caption(t(lang, "range_label"))
        _rl, _rr = st.columns(2)
        with _rl:
            v_lo = st.number_input(
                t(lang, "range_low"),
                min_value=MIN_MARK,
                max_value=MAX_MARK,
                value=init_lo,
                step=0.1,
                format="%.2f",
                placeholder=t(lang, "range_placeholder_lo"),
                key="range_lo_custom",
                label_visibility="visible",
            )
        with _rr:
            v_hi = st.number_input(
                t(lang, "range_high"),
                min_value=MIN_MARK,
                max_value=MAX_MARK,
                value=init_hi,
                step=0.1,
                format="%.2f",
                placeholder=t(lang, "range_placeholder_hi"),
                key="range_hi_custom",
                label_visibility="visible",
            )
        range_lo = None if v_lo is None else float(v_lo)
        range_hi = None if v_hi is None else float(v_hi)
        if range_lo is not None and range_hi is not None:
            if range_lo > range_hi:
                range_lo, range_hi = range_hi, range_lo
            ydisp = year_val if year_val is not None else "—"
            cdisp = category if category in CATEGORIES else "—"
            st.caption(
                t(lang, "range_help", year=ydisp, cat=cdisp)
                + f" **{_mark_for_display(range_lo)}–{_mark_for_display(range_hi)}**"
            )
        else:
            st.caption(t(lang, "range_custom_need_both"))
    else:
        if mark is not None:
            range_lo, range_hi = _range_for_mode(mode, mark)
            ydisp = year_val if year_val is not None else "—"
            cdisp = category if category in CATEGORIES else "—"
            st.caption(
                t(lang, f"mode_{mode}_help")
                + " → "
                + t(lang, "range_help", year=ydisp, cat=cdisp)
                + f" **{_mark_for_display(range_lo)}–{_mark_for_display(range_hi)}**"
            )
        else:
            range_lo, range_hi = None, None
            st.caption(
                t(lang, f"mode_{mode}_help")
                + " → "
                + t(lang, "mode_needs_mark"),
            )

    # ------- Advanced filters (compact inside)
    with st.expander(t(lang, "advanced")):
        g1, g2 = st.columns(2)
        with g1:
            master_df = _load_master(master_mtime)
            opts = _branch_options(master_mtime)
            codes = [c for c, _ in opts]
            labels = {c: l for c, l in opts}
            init_branches_raw = st.query_params.get("branch", "")
            init_branches = parse_branch_filter_param(
                str(init_branches_raw),
                set(codes),
                master_df,
            )
            selected_branches = st.multiselect(
                t(lang, "branch_filter"),
                options=codes,
                default=init_branches,
                format_func=lambda c: labels[c],
                help=t(lang, "branch_filter_help", n=len(codes)),
                key="branches",
            )
            st.caption(t(lang, "branch_filter_count", n=len(codes)))
        with g2:
            init_q = str(st.query_params.get("q", ""))
            college_query = st.text_input(
                t(lang, "search_college"),
                value=init_q,
                placeholder=t(lang, "search_college_placeholder"),
                key="college_query",
            ).strip()
        g3, g4 = st.columns(2)
        with g3:
            init_ss = _qp_get_bool("ss", True)
            include_ss = st.toggle(
                t(lang, "ss_toggle"),
                value=init_ss,
                help=t(lang, "ss_help"),
                key="ss",
            )
        with g4:
            init_group = _qp_get_bool("group", True)
            group_by_college = st.toggle(
                t(lang, "group_toggle"),
                value=init_group,
                help=t(lang, "group_help"),
                key="group",
            )

    # ------- Persist state in URL (only set fields — no surprise defaults) ---
    qp: dict[str, str] = {
        "lang": lang,
        "mode": mode,
        "ss": "1" if include_ss else "0",
        "group": "1" if group_by_college else "0",
    }
    if mark is not None:
        qp["mark"] = _fmt_num_param(mark)
    if category in CATEGORIES:
        qp["cat"] = category
    if year_val is not None:
        qp["year"] = str(year_val)
    if selected_branches:
        qp["branch"] = ",".join(selected_branches)
    if college_query:
        qp["q"] = college_query
    if (
        mode == "custom"
        and range_lo is not None
        and range_hi is not None
    ):
        qp["rmin"] = _fmt_num_param(range_lo)
        qp["rmax"] = _fmt_num_param(range_hi)
    st.query_params.clear()
    st.query_params.update(qp)

    st.markdown("---")
    if not _filters_ready(mode, mark, category, year_val, range_lo, range_hi):
        st.info(t(lang, "prompt_set_filters"))
        _render_footer(lang, long_mtime, master_mtime)
        return

    # ------- Search ------------------------------------------------------
    long = _load_long(long_mtime)
    results = find_colleges(
        long, range_lo, range_hi, category, year_val,
        branches=selected_branches or None,
        include_ss=include_ss,
        college_name_query=college_query or None,
    )

    # Safe/Match/Reach bands can sit entirely *below* real published cutoffs
    # (e.g. Safe with mark 85 → band 60–75 while OC-2025 never goes below ~77.5).
    # If so, fall back to "everything at or below your mark" when the user did not
    # narrow by branch or college name.
    if (
        len(results) == 0
        and not selected_branches
        and not college_query
        and mark is not None
    ):
        hi_fb = min(float(mark), MAX_MARK)
        alt = find_colleges(
            long, MIN_MARK, hi_fb, category, year_val,
            branches=None,
            include_ss=include_ss,
            college_name_query=None,
        )
        if len(alt) > 0:
            st.info(
                t(
                    lang, "result_fallback_band",
                    lo=_mark_for_display(range_lo),
                    hi=_mark_for_display(range_hi),
                    cat=category,
                    year=year_val,
                    mark=_mark_for_display(mark),
                )
            )
            results = alt

    n_options = len(results)
    n_colleges = int(results["college_code"].nunique()) if n_options else 0

    if n_options == 0:
        st.warning(t(lang, "result_empty"))
        _render_footer(lang, long_mtime, master_mtime)
        return

    share_mark_str = (
        _mark_for_display(mark)
        if mark is not None
        else t(
            lang,
            "share_mark_range",
            lo=_mark_for_display(range_lo),
            hi=_mark_for_display(range_hi),
        )
    )

    # ------- Single-branch context strip
    if len(selected_branches) == 1:
        only = selected_branches[0]
        only_disp = str(
            results.iloc[0].get("branch_norm")
            or results.iloc[0].get("branch_clean")
            or only,
        )
        st.info(t(lang, "single_branch_strip", branch=only_disp))

    # ------- Result header
    header_url = _build_app_url(**qp)
    if group_by_college:
        st.subheader(
            t(lang, "result_header_grouped",
              n_colleges=n_colleges, n_options=n_options,
              cat=category, year=year_val)
        )
    else:
        key = "result_header_one" if n_options == 1 else "result_header"
        st.subheader(t(lang, key, n=n_options, cat=category, year=year_val))

    # ------- Top-of-results share buttons
    share_tool = t(
        lang, "share_text_tool",
        url=_resolve_public_base_url() or t(lang, "share_tool_url_fallback"),
    )
    if mark is not None:
        share_my = t(lang, "share_text_my",
                     mark=share_mark_str, cat=category, n=n_options, url=header_url)
        sc1, sc2 = st.columns(2)
        with sc1:
            st.link_button(
                t(lang, "share_my_button"),
                _wa_share_url(share_my),
                width="stretch", type="primary",
            )
        with sc2:
            st.link_button(
                t(lang, "share_tool_button"),
                _wa_share_url(share_tool),
                width="stretch",
            )
    else:
        st.link_button(
            t(lang, "share_tool_button"),
            _wa_share_url(share_tool),
            width="stretch",
        )

    # ------- Render results ---------------------------------------------
    hide_branch_per_card = len(selected_branches) == 1
    st.caption(t(lang, "result_expand_hint"))
    if group_by_college:
        _render_grouped(
            results, lang, category, year_val, share_mark_str,
            header_url, hide_branch_per_card, long,
        )
    else:
        _render_flat(
            results, lang, category, year_val, header_url,
            hide_branch_per_card, long,
        )

    _render_footer(lang, long_mtime, master_mtime)


# ----------------------------------------------------------------------------
# Renderers
# ----------------------------------------------------------------------------
def _truncate_label(s: str, max_chars: int = 44) -> str:
    s = str(s).strip()
    if len(s) <= max_chars:
        return s
    return s[: max_chars - 1] + "…"


def _chip_short(b: pd.Series) -> str:
    """Label for a branch chip; never 'nan' (pandas NaN is truthy and breaks `or ''`)."""
    v = b["branch_short"] if "branch_short" in b.index else None
    if v is None or pd.isna(v):
        v = ""
    else:
        v = str(v).strip()
    if not v or v.lower() in ("nan", "none", "<na>"):
        full = ""
        for key in ("branch_norm", "branch_clean"):
            if key not in b.index:
                continue
            x = b[key]
            if x is not None and not pd.isna(x):
                full = str(x).strip()
                break
        if not full or full.lower() == "nan":
            return "—"
        parts = [p for p in full.split() if p]
        return " ".join(parts[:2]) if parts else "—"
    return v


def _render_grouped(
    results: pd.DataFrame,
    lang: str,
    category: str,
    year: int,
    share_mark_str: str,
    share_url: str,
    hide_branch_per_card: bool,
    long: pd.DataFrame,
) -> None:
    """Group results by college — one compact expander per college."""
    page_size = 80
    grouped = list(results.groupby(["college_code", "college_name"], sort=False))

    if "show_all" not in st.session_state:
        st.session_state["show_all"] = False
    if not st.session_state["show_all"] and len(grouped) > page_size:
        st.caption(t(lang, "showing_top", shown=page_size, total=len(grouped)))
        view = grouped[:page_size]
    else:
        view = grouped

    for idx, ((code, name), grp) in enumerate(view):
        _render_college_card(
            code, name, grp, lang, category, year, share_mark_str, share_url,
            hide_branch_per_card, idx, long,
        )

    if not st.session_state["show_all"] and len(grouped) > page_size:
        if st.button(
            t(lang, "show_all_button", n=len(grouped)),
            width="stretch", key="show_all_btn",
        ):
            st.session_state["show_all"] = True
            st.rerun()


def _render_flat(
    results: pd.DataFrame,
    lang: str,
    category: str,
    year: int,
    share_url: str,
    hide_branch_per_card: bool,
    long: pd.DataFrame,
) -> None:
    page_size = 100
    if "show_all" not in st.session_state:
        st.session_state["show_all"] = False
    if not st.session_state["show_all"] and len(results) > page_size:
        st.caption(t(lang, "showing_top", shown=page_size, total=len(results)))
        view = results.head(page_size)
    else:
        view = results

    for idx, (_, row) in enumerate(view.iterrows()):
        _render_branch_card(
            row, lang, category, share_url, hide_branch_per_card, idx, long,
        )

    if not st.session_state["show_all"] and len(results) > page_size:
        if st.button(
            t(lang, "show_all_button", n=len(results)),
            width="stretch", key="show_all_btn",
        ):
            st.session_state["show_all"] = True
            st.rerun()


def _render_college_card(
    code: int,
    name: str,
    grp: pd.DataFrame,
    lang: str,
    category: str,
    year: int,
    share_mark_str: str,
    share_url: str,
    hide_branch_per_card: bool,
    group_idx: int,
    long: pd.DataFrame,
) -> None:
    branches_sorted = grp.sort_values("cutoff", ascending=False)
    n_branches = len(branches_sorted)
    top_cut = float(branches_sorted.iloc[0]["cutoff"])
    name_t = _truncate_label(name, 42)
    suffix = t(
        lang, "expander_college_suffix", n_br=n_branches, top=f"{top_cut:.1f}",
    )
    exp_label = f"{int(code)} · {name_t} · {suffix}"

    with st.expander(exp_label, expanded=False, key=f"grp_{group_idx}"):
        st.markdown(
            f"<div class='college-detail-head'><span class='cd-code'>{int(code)}</span> "
            f"{name}</div>",
            unsafe_allow_html=True,
        )

        if not hide_branch_per_card:
            chips_html = []
            for _, b in branches_sorted.head(24).iterrows():
                cutoff_str = f"{b['cutoff']:.1f}"
                full = str(b.get("branch_norm") or b.get("branch_clean") or "")
                chip_label = _chip_short(b)
                tooltip = html.escape(
                    full + (" (SS)" if b.get("is_self_supporting") else "")
                )
                chips_html.append(
                    f'<span class="chip" title="{tooltip}">{chip_label} '
                    f'<b>{cutoff_str}</b></span>'
                )
            if n_branches > 24:
                chips_html.append(
                    f'<span class="chip more">{t(lang, "more_branches", n=n_branches - 24)}</span>'
                )
            st.markdown(
                f"<div class='chip-row chip-row-compact'>{''.join(chips_html)}</div>",
                unsafe_allow_html=True,
            )
        else:
            top = branches_sorted.iloc[0]
            st.markdown(
                f"<div class='cutoff-inline'>{top['cutoff']:.1f}</div>",
                unsafe_allow_html=True,
            )

        def _label_for(b):
            return _chip_short(b)

        chips_text = ", ".join(
            f"{_label_for(b)} {b['cutoff']:.0f}"
            for _, b in branches_sorted.head(5).iterrows()
        )
        if n_branches > 5:
            chips_text += f" +{n_branches - 5}"
        share_text = t(
            lang, "share_text_college",
            college=name[:80], n=n_branches, mark=share_mark_str, cat=category,
            branches=chips_text, url=share_url,
        )
        st.link_button(
            t(lang, "share_one_button"),
            _wa_share_url(share_text),
            width="stretch",
        )

        with st.expander(t(lang, "trend_button"), expanded=False, key=f"tr_{group_idx}"):
            target_branch = branches_sorted.iloc[0]
            _render_trend_block(
                int(code), target_branch["branch_clean"],
                bool(target_branch.get("is_self_supporting", False)),
                category, lang, long,
            )


def _render_branch_card(
    row: pd.Series,
    lang: str,
    category: str,
    share_url: str,
    hide: bool,
    row_idx: int,
    long: pd.DataFrame,
) -> None:
    short = _chip_short(row)
    branch_disp = str(row.get("branch_norm") or row.get("branch_clean") or "")
    br_for_label = short if short != "—" else _truncate_label(branch_disp, 18)
    col_t = _truncate_label(str(row["college_name"]), 36)
    flat_suffix = t(
        lang, "expander_flat_suffix",
        branch=br_for_label, cutoff=f"{row['cutoff']:.1f}",
    )
    exp_label = f"{int(row['college_code'])} · {col_t} · {flat_suffix}"

    with st.expander(exp_label, expanded=False, key=f"flat_{row_idx}"):
        if not hide:
            ss = " · " + t(lang, "ss_badge") if row.get("is_self_supporting") else ""
            head_short = f"{short} · " if short and short != "—" else ""
            st.markdown(
                f"<div class='college-detail-head'>{head_short}"
                f"{branch_disp}{ss}</div>",
                unsafe_allow_html=True,
            )
        st.markdown(
            f"<div class='branch-flat-college'>{row['college_name']}</div>",
            unsafe_allow_html=True,
        )
        st.caption(f"{t(lang, 'code_label')}: {int(row['college_code'])}")

        branch_share_disp = branch_disp
        one_text = t(
            lang, "share_text_one",
            college=str(row["college_name"])[:60],
            branch=branch_share_disp,
            year=int(row["year"]),
            cat=category,
            cutoff=row["cutoff"],
            url=share_url,
        )
        st.link_button(
            t(lang, "share_one_button"),
            _wa_share_url(one_text),
            width="stretch",
        )

        with st.expander(t(lang, "trend_button"), expanded=False, key=f"trf_{row_idx}"):
            _render_trend_block(
                int(row["college_code"]), row["branch_clean"],
                bool(row.get("is_self_supporting", False)),
                category, lang, long,
            )


def _render_trend_block(
    college_code: int,
    branch_clean: str,
    is_ss: bool,
    category: str,
    lang: str,
    long: pd.DataFrame,
) -> None:
    wide = trend_all_categories(long, college_code, branch_clean, is_ss)
    if wide.dropna(how="all").empty:
        st.caption("—")
        return

    # Reorder columns: highlight user's category first
    cols_order = [category] + [c for c in CATEGORIES if c != category]
    show = wide[cols_order].copy()
    show.index.name = t(lang, "trend_year")
    show = show.reset_index()

    # Render as native dataframe with the user's category column bolded via header
    show_display = show.rename(columns={category: f"{category} ★"})
    st.dataframe(
        show_display,
        hide_index=True,
        width="stretch",
    )
    st.caption(t(lang, "trend_caption", cat=category))

    # Chart for user's category (most relevant view)
    chart_df = wide[[category]].dropna()
    if len(chart_df) >= 2:
        st.line_chart(chart_df, height=110)
        st.caption(t(lang, "trend_chart_caption"))


# ----------------------------------------------------------------------------
# Styling
# ----------------------------------------------------------------------------
def _inject_css() -> None:
    st.markdown(
        """
        <style>
          :root {
            --app-accent: #2563eb;
            --app-accent-soft: #eff6ff;
            --app-border: #e2e8f0;
            --app-text: #1e293b;
            --app-muted: #64748b;
            --app-card-shadow: 0 1px 2px rgba(15, 23, 42, 0.06), 0 4px 12px rgba(15, 23, 42, 0.04);
          }
          /* Room under Streamlit chrome + notches */
          .block-container {
            padding-top: max(1.5rem, calc(env(safe-area-inset-top, 0px) + 0.75rem)) !important;
            padding-bottom: 1.25rem !important;
            max-width: 44rem;
          }
          @media (max-width: 768px) {
            .block-container {
              padding-top: max(2rem, calc(env(safe-area-inset-top, 0px) + 1.1rem)) !important;
            }
          }
          section.main > div { max-width: 44rem; }
          .stApp {
            font-size: 0.8125rem;
            color: var(--app-text);
          }
          /* Hero */
          .app-hero-card {
            background: linear-gradient(145deg, #ffffff 0%, #f0f6ff 48%, #eef2ff 100%);
            border: 1px solid var(--app-border);
            border-radius: 14px;
            padding: 1rem 1.15rem 0.85rem 1.15rem;
            margin: 0 0 0.5rem 0;
            box-shadow: var(--app-card-shadow);
          }
          p.app-main-title {
            font-size: 1.35rem !important;
            font-weight: 700 !important;
            line-height: 1.25 !important;
            letter-spacing: -0.03em;
            color: var(--app-text) !important;
            margin: 0 0 0.15rem 0 !important;
            padding: 0 !important;
          }
          p.app-attribution {
            font-size: 0.78rem !important;
            font-weight: 500 !important;
            color: var(--app-muted) !important;
            margin: 0 !important;
            line-height: 1.35 !important;
            padding: 0 !important;
          }
          p.app-tagline {
            font-size: 0.8rem !important;
            line-height: 1.45 !important;
            color: var(--app-muted) !important;
            margin: 0.35rem 0 0.5rem 0 !important;
            padding: 0 !important;
            max-width: 40rem;
          }
          [data-testid="stMarkdownContainer"] p.app-main-title,
          [data-testid="stMarkdownContainer"] p.app-attribution,
          [data-testid="stMarkdownContainer"] p.app-tagline {
            font-family: inherit !important;
          }
          h1, h2, h3 { color: var(--app-text) !important; }
          /* Result section headings — subtle accent bar */
          h2 {
            font-size: 1.05rem !important;
            line-height: 1.35 !important;
            font-weight: 600 !important;
            border-left: 3px solid var(--app-accent);
            padding-left: 0.5rem !important;
            margin: 0.5rem 0 0.35rem 0 !important;
          }
          /* Smaller value text: number input + selectboxes */
          [data-testid="stNumberInput"] input {
            font-size: 0.9rem !important;
            font-weight: 500 !important;
            padding: 0.3rem 0.45rem !important;
          }
          [data-testid="stNumberInput"] button {
            padding: 0.2rem 0.45rem !important;
          }
          [data-testid="stSelectbox"] [data-baseweb="select"] span,
          [data-testid="stSelectbox"] [data-baseweb="select"] div[class*="singleValue"] {
            font-size: 0.88rem !important;
            font-weight: 500 !important;
          }
          [data-testid="stSelectbox"] div[data-baseweb="select"] > div {
            min-height: 2.15rem !important;
            padding-top: 0.15rem !important;
            padding-bottom: 0.15rem !important;
          }
          label[data-testid="stWidgetLabel"] p {
            font-size: 0.74rem !important;
            line-height: 1.25 !important;
          }
          label[data-testid="stWidgetLabel"] {
            margin-bottom: 0.08rem !important;
          }
          [data-testid="stNumberInput"] label p,
          [data-testid="stSlider"] label p,
          [data-testid="stSelectbox"] label p {
            font-size: 0.74rem !important;
          }
          [data-testid="stRadio"] div[role="radiogroup"] {
            gap: 0.35rem 0.5rem;
            flex-wrap: wrap;
          }
          [data-baseweb="segmented-control"] {
            min-height: 1.85rem;
            max-width: 100% !important;
            flex-wrap: wrap !important;
            box-sizing: border-box !important;
          }
          [data-testid="stHorizontalBlock"] {
            gap: 0.28rem !important;
          }
          h1 {
            font-size: 1.12rem !important;
            line-height: 1.3 !important;
            font-weight: 700 !important;
            margin: 0.35rem 0 0.15rem 0 !important;
          }
          h3 { font-size: 0.92rem !important; line-height: 1.3 !important; }
          [data-testid="stCaption"] { color: var(--app-muted) !important; }
          [data-testid="stHeading"] { color: var(--app-text) !important; }
          /* Inputs: rounded, light border */
          [data-testid="stNumberInput"] input,
          [data-testid="stNumberInput"] button {
            border-radius: 8px !important;
          }
          [data-testid="stSelectbox"] [data-baseweb="select"] > div,
          div[data-baseweb="select"] > div {
            border-radius: 8px !important;
            border-color: var(--app-border) !important;
          }
          [data-testid="stTextInput"] input {
            border-radius: 8px !important;
          }
          /* Expanders — card-like */
          [data-testid="stExpander"] details {
            border: 1px solid var(--app-border) !important;
            border-radius: 10px !important;
            background: #ffffff !important;
            box-shadow: 0 1px 2px rgba(15, 23, 42, 0.05);
          }
          [data-testid="stExpander"] details summary {
            font-size: 0.74rem !important;
            font-weight: 600 !important;
            padding: 0.35rem 0.5rem !important;
            min-block-size: 1.75rem;
            background: linear-gradient(180deg, #fafbfe 0%, #ffffff 100%);
          }
          [data-testid="stExpander"] details summary p,
          [data-testid="stExpander"] details summary span {
            font-size: 0.76rem !important;
          }
          [data-testid="stExpander"] .streamlit-expanderContent {
            padding: 0.35rem 0.5rem 0.55rem 0.5rem !important;
          }
          [data-testid="stVerticalBlock"] > div {
            gap: 0.12rem;
          }
          .college-detail-head {
            font-size: 0.8rem;
            font-weight: 600;
            color: var(--app-text);
            line-height: 1.35;
            margin-bottom: 0.3rem;
          }
          .cd-code { color: var(--app-muted); font-weight: 600; margin-right: 0.35rem; }
          .branch-flat-college {
            color: #475569;
            font-size: 0.78rem;
            line-height: 1.35;
            margin-bottom: 0.25rem;
          }
          .cutoff-inline {
            font-size: 1.05rem;
            font-weight: 600;
            color: var(--app-accent);
            margin: 0.15rem 0 0.45rem 0;
          }
          .chip-row-compact { line-height: 1.55; }
          .chip-row-compact .chip,
          .chip-row .chip {
            background: var(--app-accent-soft);
            color: var(--app-accent);
            font-size: 0.7rem;
            padding: 2px 8px;
            border-radius: 999px;
            margin: 0 4px 4px 0;
            display: inline-block;
            white-space: nowrap;
            border: 1px solid rgba(37, 99, 235, 0.12);
          }
          .chip.more { background: #f1f5f9; color: #64748b; border-color: #e2e8f0; }
          [data-testid="stCaptionContainer"] { font-size: 0.72rem !important; color: var(--app-muted) !important; }
          [data-testid="stMarkdownContainer"] p {
            font-size: 0.8125rem;
            color: #334155;
          }
          hr {
            margin: 1rem 0 !important;
            border: none;
            border-top: 1px solid var(--app-border);
          }
          /* Primary actions */
          .stButton > button[kind="primary"] {
            border-radius: 8px !important;
            font-weight: 600 !important;
          }
          [data-testid="stLinkButton"] {
            border-radius: 8px !important;
          }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _render_footer(lang: str, long_mtime: int, master_mtime: int) -> None:
    st.markdown("---")
    stats = _stats(long_mtime, master_mtime)
    st.caption(
        f"{stats['n_colleges']:,} colleges  ·  "
        f"{stats['n_branches']:,} branches  ·  "
        f"{stats['year_min']}–{stats['year_max']}  ·  "
        f"{stats['n_rows']:,} cutoff data points"
    )
    st.markdown(t(lang, "footer_disclaimer"))
    st.caption(t(lang, "footer_credit"))


if __name__ == "__main__":
    main()
