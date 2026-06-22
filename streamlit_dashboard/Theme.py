"""
Shared design system for the UDIF Monitoring Portal.
Corporate / AlgeniX-inspired: dark sidebar with section labels,
no emojis, SVG geometric icons, white main canvas.
"""
import streamlit as st

# ── Design tokens ──────────────────────────────────────────────────────────────
COLOR_BG            = "#FFFFFF"
COLOR_SURFACE       = "#FFFFFF"
COLOR_BORDER        = "#E8ECF4"
COLOR_BORDER_SOFT   = "#F0F3FA"

COLOR_TEXT          = "#0A0F1E"
COLOR_TEXT_MUTED    = "#5B6478"
COLOR_TEXT_FAINT    = "#99A3B8"

COLOR_ACCENT        = "#4F39F6"
COLOR_ACCENT_LIGHT  = "#7C6FF7"
COLOR_ACCENT_SOFT   = "#EEF0FF"
COLOR_ACCENT_GLOW   = "rgba(79,57,246,0.12)"

COLOR_SUCCESS        = "#15803D"
COLOR_SUCCESS_SOFT   = "#F0FDF4"
COLOR_SUCCESS_BORDER = "#BBF7D0"

COLOR_DANGER         = "#DC2626"
COLOR_DANGER_SOFT    = "#FEF2F2"
COLOR_DANGER_BORDER  = "#FECACA"

COLOR_WARNING        = "#D97706"
COLOR_WARNING_SOFT   = "#FFFBEB"
COLOR_WARNING_BORDER = "#FDE68A"

COLOR_SIDEBAR_BG     = "#111827"
COLOR_SIDEBAR_BORDER = "#1F2937"

FONT_STACK = (
    "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', "
    "Helvetica, Arial, sans-serif"
)
MONO_STACK = (
    "'JetBrains Mono', 'SF Mono', 'Roboto Mono', Menlo, Consolas, monospace"
)

# ── SVG icon set (no emojis anywhere) ─────────────────────────────────────────
# Each returns a small inline SVG string sized for sidebar use.
def _icon(path_d, size=16):
    return (
        f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" '
        f'stroke="currentColor" stroke-width="1.8" stroke-linecap="round" '
        f'stroke-linejoin="round" style="flex-shrink:0;opacity:0.75;">'
        f'<path d="{path_d}"/></svg>'
    )

ICON_OVERVIEW   = _icon("M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z M9 22V12h6v10")
ICON_EXPLORER   = _icon("M11 3a8 8 0 1 0 0 16A8 8 0 0 0 11 3z M21 21l-4.35-4.35")
ICON_FAILURES   = _icon("M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z M12 9v4 M12 17h.01")
ICON_ANALYTICS  = _icon("M18 20V10 M12 20V4 M6 20v-6")
ICON_DATASET    = _icon("M3 3h18v4H3z M3 10h18v4H3z M3 17h18v4H3z")
ICON_PIPELINE   = _icon("M22 12h-4l-3 9L9 3l-3 9H2")
ICON_AIRFLOW    = _icon("M12 2a10 10 0 1 0 0 20A10 10 0 0 0 12 2z M12 6v6l4 2")
ICON_USERS      = _icon("M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2 M23 21v-2a4 4 0 0 0-3-3.87 M16 3.13a4 4 0 0 1 0 7.75 M9 7a4 4 0 1 0 0 8A4 4 0 0 0 9 7z")

# ── CSS ────────────────────────────────────────────────────────────────────────
CSS_BODY = f"""
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] {{
        font-family: {FONT_STACK};
        -webkit-font-smoothing: antialiased;
        font-size: 15px;
    }}
    .stApp {{ background-color: {COLOR_BG}; }}

    .block-container {{
        padding-top: 0 !important;
        padding-bottom: 3rem;
        padding-left: 0 !important;
        padding-right: 0 !important;
        max-width: 100%;
    }}

    /* ── HIDE STREAMLIT CHROME ── */
    [data-testid="stSidebarNav"]   {{ display: none !important; }}
    [data-testid="collapsedControl"] {{ display: none !important; }}
    #MainMenu  {{ visibility: hidden; }}
    footer     {{ visibility: hidden; }}
    header[data-testid="stHeader"] {{ background: transparent; }}

    /* ── SIDEBAR ── */
    section[data-testid="stSidebar"] {{
        background-color: {COLOR_SIDEBAR_BG} !important;
        border-right: 1px solid {COLOR_SIDEBAR_BORDER} !important;
        min-width: 240px !important;
        max-width: 240px !important;
    }}
    section[data-testid="stSidebar"] > div:first-child {{
        padding: 0 !important;
    }}
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] span,
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] div {{
        color: #D1D5DB !important;
    }}

    /* ── SIDEBAR: collapse Streamlit's default block padding around page_link ── */
    section[data-testid="stSidebar"] div[data-testid="stVerticalBlock"],
    section[data-testid="stSidebar"] div[data-testid="element-container"] {{
        gap: 0 !important;
        margin: 0 !important;
        padding: 0 !important;
    }}
    section[data-testid="stSidebar"] .stPageLink {{
        margin: 0 !important;
        padding: 0 !important;
    }}

    /* ── SIDEBAR NAV LINKS (st.page_link) ── */
    section[data-testid="stSidebar"] [data-testid="stPageLink-NavLink"] {{
        display: flex !important;
        align-items: center !important;
        gap: 0 !important;
        padding: 9px 16px 9px 24px !important;
        border-radius: 0 !important;
        font-size: 13.5px !important;
        font-weight: 500 !important;
        color: #9CA3AF !important;
        text-decoration: none !important;
        margin: 0 !important;
        line-height: 1.3 !important;
        transition: color 0.12s, background 0.12s !important;
        background: transparent !important;
        border: none !important;
        border-left: 3px solid transparent !important;
    }}
    section[data-testid="stSidebar"] [data-testid="stPageLink-NavLink"]:hover {{
        background: rgba(255,255,255,0.05) !important;
        color: #FFFFFF !important;
        border-left-color: rgba(79,57,246,0.5) !important;
    }}
    section[data-testid="stSidebar"] [data-testid="stPageLink-NavLink"][aria-current="page"] {{
        background: rgba(79,57,246,0.15) !important;
        color: #FFFFFF !important;
        border-left: 3px solid {COLOR_ACCENT} !important;
        font-weight: 600 !important;
    }}
    section[data-testid="stSidebar"] [data-testid="stPageLink-NavLink"][aria-current="page"] p,
    section[data-testid="stSidebar"] [data-testid="stPageLink-NavLink"][aria-current="page"] span {{
        color: #FFFFFF !important;
    }}
    section[data-testid="stSidebar"] [data-testid="stPageLink-NavLink"] p {{
        font-size: 14px !important;
        margin: 0 !important;
        color: inherit !important;
    }}
    /* Hide the default icon Streamlit renders so only our SVG shows */
    section[data-testid="stSidebar"] [data-testid="stPageLink-NavLink"] [data-testid="stIconMaterial"],
    section[data-testid="stSidebar"] [data-testid="stPageLink-NavLink"] svg.stIcon {{
        display: none !important;
    }}

    /* ── ANIMATED WAVE HERO ── */
    @keyframes ripple {{
        0%   {{ transform: scale(0.85); opacity: 0.5; }}
        100% {{ transform: scale(2.5);  opacity: 0; }}
    }}
    .udif-hero {{
        position: relative; overflow: hidden;
        background: linear-gradient(135deg, #F8F9FF 0%, #F0F3FF 100%);
        padding: 32px 3rem 28px 3rem;
        border-bottom: 1px solid {COLOR_BORDER};
        text-align: center;
    }}
    .wave-ring {{
        position: absolute; border-radius: 50%;
        pointer-events: none; top: 50%; left: 50%;
    }}
    .wave-ring-1 {{ width:300px; height:300px; margin:-150px 0 0 -150px;
        border:1px solid rgba(79,57,246,0.18);
        animation: ripple 4s ease-out 0.2s infinite; }}
    .wave-ring-2 {{ width:500px; height:500px; margin:-250px 0 0 -250px;
        border:1px solid rgba(79,57,246,0.10);
        animation: ripple 4s ease-out 0.9s infinite; }}
    .wave-ring-3 {{ width:700px; height:700px; margin:-350px 0 0 -350px;
        border:1px solid rgba(79,57,246,0.06);
        animation: ripple 4s ease-out 1.8s infinite; }}
    .wave-ring-4 {{ width:900px; height:900px; margin:-450px 0 0 -450px;
        border:1px solid rgba(79,57,246,0.04);
        animation: ripple 4s ease-out 2.6s infinite; }}
    .udif-hero-content {{ position: relative; z-index: 10; }}
    .udif-hero-eyebrow {{
        font-size: 11px; font-weight: 700; letter-spacing: 0.14em;
        text-transform: uppercase; color: {COLOR_ACCENT}; margin-bottom: 10px;
    }}
    .udif-hero-title {{
        font-size: 2rem; font-weight: 800;
        letter-spacing: -0.03em; line-height: 1.15;
        color: {COLOR_TEXT}; margin: 0 0 12px 0;
    }}
    .udif-hero-title .accent {{ color: {COLOR_ACCENT}; }}
    .udif-hero-subtitle {{
        font-size: 14px; color: {COLOR_TEXT_MUTED};
        max-width: 520px; margin: 0 auto; line-height: 1.65;
    }}

    /* ── PAGE HEADER (inner pages) ── */
    .udif-topbar {{
        display: flex; align-items: flex-start;
        justify-content: space-between; padding-bottom: 4px;
    }}
    .udif-eyebrow {{
        font-size: 11px; font-weight: 700; letter-spacing: 0.12em;
        text-transform: uppercase; color: {COLOR_ACCENT}; margin-bottom: 6px;
    }}
    .udif-title {{
        font-size: 1.75rem; font-weight: 800; line-height: 1.15;
        letter-spacing: -0.03em; margin: 0 0 4px 0; color: {COLOR_TEXT};
    }}
    .udif-title .accent {{ color: {COLOR_ACCENT}; }}
    .udif-subtitle {{ font-size: 14px; color: {COLOR_TEXT_MUTED}; margin-top: 3px; }}
    .udif-divider {{
        border: none; border-top: 1px solid {COLOR_BORDER};
        margin: 18px 0 22px 0;
    }}

    /* ── BODY ── */
    .udif-body {{ padding: 24px 3rem; }}

    /* ── KPI CARDS ── */
    .kpi-card {{
        background: {COLOR_SURFACE}; border: 1px solid {COLOR_BORDER};
        border-radius: 12px; padding: 18px 20px; position: relative;
        box-shadow: 0 1px 3px rgba(10,15,30,0.04), 0 4px 12px rgba(10,15,30,0.03);
        transition: box-shadow 0.18s ease, border-color 0.18s ease;
    }}
    .kpi-card:hover {{
        border-color: #C7CDE8;
        box-shadow: 0 2px 8px rgba(10,15,30,0.08), 0 8px 24px rgba(10,15,30,0.05);
    }}
    .kpi-label {{
        font-size: 11px; font-weight: 700; color: {COLOR_TEXT_MUTED};
        text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 10px;
    }}
    .kpi-value {{
        font-family: {MONO_STACK}; font-size: 30px; font-weight: 700;
        color: {COLOR_TEXT}; line-height: 1; font-variant-numeric: tabular-nums;
    }}
    .kpi-accent-bar {{
        position: absolute; top: 0; left: 0; bottom: 0; width: 3px;
        border-radius: 12px 0 0 12px;
    }}

    /* ── SECTION HEADERS ── */
    .udif-section {{
        display: flex; align-items: baseline;
        justify-content: space-between; margin: 24px 0 12px 0;
    }}
    .udif-section-title {{
        font-size: 15px; font-weight: 700; color: {COLOR_TEXT};
        letter-spacing: -0.01em;
    }}
    .udif-section-sub {{ font-size: 13px; color: {COLOR_TEXT_FAINT}; }}

    /* ── STATUS PILLS ── */
    .pill {{
        display: inline-flex; align-items: center; gap: 5px;
        padding: 3px 10px; border-radius: 999px;
        font-size: 12px; font-weight: 700;
        font-family: {MONO_STACK}; line-height: 1.5; letter-spacing: 0.01em;
    }}
    .pill-success {{ background:{COLOR_SUCCESS_SOFT}; color:{COLOR_SUCCESS}; border:1px solid {COLOR_SUCCESS_BORDER}; }}
    .pill-danger  {{ background:{COLOR_DANGER_SOFT};  color:{COLOR_DANGER};  border:1px solid {COLOR_DANGER_BORDER}; }}
    .pill-warning {{ background:{COLOR_WARNING_SOFT}; color:{COLOR_WARNING}; border:1px solid {COLOR_WARNING_BORDER}; }}
    .pill-dot {{ width:5px; height:5px; border-radius:50%; display:inline-block; }}

    /* ── HEALTH BANNERS ── */
    .udif-banner {{
        border-radius: 8px; padding: 11px 16px; font-size: 13px;
        font-weight: 600; display: flex; align-items: center; gap: 9px; border: 1px solid;
    }}
    .udif-banner.ok   {{ background:{COLOR_SUCCESS_SOFT}; color:{COLOR_SUCCESS}; border-color:{COLOR_SUCCESS_BORDER}; }}
    .udif-banner.warn {{ background:{COLOR_WARNING_SOFT}; color:{COLOR_WARNING}; border-color:{COLOR_WARNING_BORDER}; }}
    .udif-banner.bad  {{ background:{COLOR_DANGER_SOFT};  color:{COLOR_DANGER};  border-color:{COLOR_DANGER_BORDER}; }}

    /* ── CARDS ── */
    .udif-card {{
        background: {COLOR_SURFACE}; border: 1px solid {COLOR_BORDER};
        border-radius: 12px; padding: 20px 20px 8px 20px;
        box-shadow: 0 1px 3px rgba(10,15,30,0.04), 0 4px 16px rgba(10,15,30,0.03);
    }}
    .udif-card-tight {{
        background: {COLOR_SURFACE}; border: 1px solid {COLOR_BORDER};
        border-radius: 12px; padding: 4px; overflow: hidden;
        box-shadow: 0 1px 3px rgba(10,15,30,0.04), 0 4px 16px rgba(10,15,30,0.03);
    }}

    /* ── TABLE ── */
    table.udif-table {{
        width:100%; border-collapse:collapse; font-size:13px; font-family:inherit;
    }}
    table.udif-table thead th {{
        text-align:left; font-size:11px; font-weight:700;
        text-transform:uppercase; letter-spacing:0.07em;
        color:{COLOR_TEXT_MUTED}; padding:11px 16px;
        border-bottom:1px solid {COLOR_BORDER}; background:#F7F8FC;
    }}
    table.udif-table tbody td {{
        padding:11px 16px; border-bottom:1px solid #F0F3F9;
        color:{COLOR_TEXT}; vertical-align:middle;
    }}
    table.udif-table tbody tr:last-child td {{ border-bottom:none; }}
    table.udif-table tbody tr:hover {{ background:#F7F8FC; }}

    /* ── WIDGET OVERRIDES ── */
    div[data-testid="stMetric"] {{
        background:{COLOR_SURFACE}; border:1px solid {COLOR_BORDER};
        border-radius:12px; padding:16px 20px;
        box-shadow:0 1px 3px rgba(10,15,30,0.04);
    }}
    .stDataFrame {{
        border:1px solid {COLOR_BORDER} !important;
        border-radius:12px !important; overflow:hidden;
    }}
    .stSelectbox > div > div {{
        border-radius:8px !important; border-color:{COLOR_BORDER} !important;
        font-family:{FONT_STACK}; background:{COLOR_SURFACE};
    }}
    .stSelectbox > div > div:focus-within {{
        border-color:{COLOR_ACCENT} !important;
        box-shadow:0 0 0 3px {COLOR_ACCENT_GLOW};
    }}
    .stTextInput > div > div > input {{
        border-radius:8px !important; border-color:{COLOR_BORDER} !important;
        font-family:{FONT_STACK};
    }}
    .stTextInput > div > div > input:focus {{
        border-color:{COLOR_ACCENT} !important;
        box-shadow:0 0 0 3px {COLOR_ACCENT_GLOW} !important;
    }}
    div[data-testid="stVerticalBlockBorderWrapper"] {{ border-radius:12px; }}

    /* ── SIDEBAR SECTION LABEL ── */
    .sidebar-section-label {{
        font-size: 10px;
        font-weight: 700;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        color: #4B5563;
        padding: 16px 20px 6px 20px;
        display: block;
    }}

    /* ── SIDEBAR NAV ROW (wraps icon + label) ── */
    .sidebar-nav-item {{
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 8px 16px 8px 20px;
        font-size: 14px;
        font-weight: 500;
        color: #9CA3AF;
    }}
"""


# ── Helpers ───────────────────────────────────────────────────────────────────

def inject_base_styles():
    """Call once per page, immediately after st.set_page_config()."""
    st.html(f"<style>{CSS_BODY}</style>")


def _nav_link(page, label):
    """Render a sidebar nav link — clean text, no broken icon overlay."""
    st.page_link(page, label=label)


def _sidebar_section(label):
    st.markdown(
        f'<span class="sidebar-section-label">{label}</span>',
        unsafe_allow_html=True,
    )


def render_sidebar():
    """
    Call inside `with st.sidebar:` on EVERY page.
    Corporate dark sidebar: wordmark, section labels, icon nav — no emojis.
    """
    # ── Wordmark ──────────────────────────────────────────────────────
    st.markdown(
        f"""
        <div style="padding:24px 20px 8px 20px;border-bottom:1px solid #1F2937;">
            <div style="display:flex;align-items:center;gap:10px;margin-bottom:4px;">
                <svg width="22" height="22" viewBox="0 0 24 24" fill="{COLOR_ACCENT}"
                     style="flex-shrink:0;">
                    <polygon points="12,2 22,19 2,19"/>
                </svg>
                <span style="font-size:16px;font-weight:800;color:#FFFFFF;
                             letter-spacing:-0.02em;font-family:{FONT_STACK};">
                    UDIF Portal
                </span>
            </div>
            <div style="font-size:11px;color:#4B5563;letter-spacing:0.04em;
                        padding-left:32px;font-family:{FONT_STACK};">
                Data Integration Framework
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── MONITORING section ─────────────────────────────────────────────
    _sidebar_section("Monitoring")
    _nav_link("Application.py", "Overview")
    _nav_link("pages/1_Pipeline_Explorer.py", "Pipeline Explorer")
    _nav_link("pages/2_Failures.py", "Failures")
    _nav_link("pages/3_Analytics.py", "Analytics")

    # ── OPERATIONS section ─────────────────────────────────────────────
    st.markdown(
        '<div style="border-top:1px solid #1F2937;margin:8px 0 0 0;"></div>',
        unsafe_allow_html=True,
    )
    _sidebar_section("Operations")
    _nav_link("pages/4_Dataset_Management.py", "Dataset Management")
    _nav_link("pages/5_Pipeline_Management.py", "Pipeline Management")
    _nav_link("pages/7_Airflow_Control.py", "Airflow Control")

    # ── ADMINISTRATION section (admin-only) ────────────────────────────
    permissions = st.session_state.get("auth_permissions", set())
    if "user.manage" in permissions:
        st.markdown(
            '<div style="border-top:1px solid #1F2937;margin:8px 0 0 0;"></div>',
            unsafe_allow_html=True,
        )
        _sidebar_section("Administration")
        _nav_link("pages/6_User_Management.py", "User Management")


def hero_header(title: str, accent_word: str, subtitle: str):
    """Full-width animated wave hero — used on the Overview (home) page."""
    if accent_word and title.endswith(accent_word):
        base = title[: -len(accent_word)].rstrip()
        title_html = f'{base} <span class="accent">{accent_word}</span>'
    else:
        title_html = title

    st.markdown(
        f"""
        <div class="udif-hero">
            <span class="wave-ring wave-ring-1"></span>
            <span class="wave-ring wave-ring-2"></span>
            <span class="wave-ring wave-ring-3"></span>
            <span class="wave-ring wave-ring-4"></span>
            <div class="udif-hero-content">
                <div class="udif-hero-eyebrow">UDIF &nbsp;·&nbsp; Monitoring Portal</div>
                <h1 class="udif-hero-title">{title_html}</h1>
                <p class="udif-hero-subtitle">{subtitle}</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def page_header(eyebrow: str, title: str, subtitle: str, accent_word: str = ""):
    """Compact header for inner pages."""
    if accent_word and title.endswith(accent_word):
        base = title[: -len(accent_word)].rstrip()
        title_html = f'{base} <span class="accent">{accent_word}</span>'
    else:
        title_html = title

    st.markdown(
        f"""
        <div class="udif-body" style="padding-bottom:0;">
            <div class="udif-topbar">
                <div>
                    <div class="udif-eyebrow">{eyebrow}</div>
                    <p class="udif-title">{title_html}</p>
                    <div class="udif-subtitle">{subtitle}</div>
                </div>
            </div>
            <hr class="udif-divider" />
        </div>
        """,
        unsafe_allow_html=True,
    )


def section_header(title: str, subtitle: str = "", icon: str = ""):
    st.markdown(
        f"""
        <div class="udif-section">
            <div class="udif-section-title">{title}</div>
            <div class="udif-section-sub">{subtitle}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def kpi_card(label, value, accent=None, delta=None, delta_dir="flat"):
    accent = accent or COLOR_ACCENT
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-accent-bar" style="background:{accent};"></div>
            <div class="kpi-label">{label}</div>
            <div class="kpi-value">{value}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def status_pill(status: str) -> str:
    s = (status or "").upper()
    if s == "SUCCESS":
        return (f'<span class="pill pill-success">'
                f'<span class="pill-dot" style="background:{COLOR_SUCCESS};"></span>SUCCESS</span>')
    if s == "FAILED":
        return (f'<span class="pill pill-danger">'
                f'<span class="pill-dot" style="background:{COLOR_DANGER};"></span>FAILED</span>')
    return f'<span class="pill pill-warning">{s}</span>'


def health_banner(success_rate: float):
    if success_rate is None:
        return
    if success_rate >= 95:
        cls, msg = "ok",   "Pipeline health is excellent"
    elif success_rate >= 80:
        cls, msg = "warn", "Pipeline health is moderate — monitor closely"
    else:
        cls, msg = "bad",  "Pipeline health requires attention"
    st.markdown(f'<div class="udif-banner {cls}">{msg}</div>', unsafe_allow_html=True)


# ── Plotly defaults ────────────────────────────────────────────────────────────
PLOTLY_LAYOUT = dict(
    plot_bgcolor="white", paper_bgcolor="white",
    font=dict(family=FONT_STACK, color=COLOR_TEXT, size=12),
    margin=dict(l=10, r=10, t=40, b=10),
    title_font=dict(size=14, color=COLOR_TEXT, family=FONT_STACK),
    xaxis=dict(gridcolor=COLOR_BORDER_SOFT, zeroline=False),
    yaxis=dict(gridcolor=COLOR_BORDER_SOFT, zeroline=False),
    legend=dict(font=dict(size=11)),
)

PLOTLY_SEQUENCE = [
    COLOR_ACCENT, "#0EA5E9", "#15803D", "#D97706", "#DC2626", "#9333EA",
]