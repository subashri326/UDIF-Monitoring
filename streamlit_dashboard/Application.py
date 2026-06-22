import streamlit as st
from db.connection import run_query
from auth.auth import attempt_login, logout, current_user, is_logged_in, require_login
from auth.rbac import has_permission
from Theme import (
    inject_base_styles, render_sidebar,
    hero_header, section_header, kpi_card, status_pill, health_banner,
    COLOR_ACCENT, COLOR_SUCCESS, COLOR_WARNING,
    COLOR_TEXT_MUTED, COLOR_BORDER, COLOR_TEXT_FAINT,
)

st.set_page_config(page_title="UDIF Monitoring Portal", page_icon="◆", layout="wide")
inject_base_styles()


# ════════════════════════════════════════════════════════════════════
# LOGIN GATE
# ════════════════════════════════════════════════════════════════════
def render_login():
    st.markdown(
        """
        <div style="max-width:420px;margin:8vh auto 0 auto;text-align:center;">
            <div style="font-size:13px;letter-spacing:.12em;color:%s;
                        text-transform:uppercase;margin-bottom:6px;">UDIF</div>
            <div style="font-size:28px;font-weight:700;margin-bottom:4px;">
                Pipeline Monitoring Portal
            </div>
            <div style="font-size:14px;color:%s;margin-bottom:28px;">
                Sign in to continue
            </div>
        </div>
        """ % (COLOR_ACCENT, COLOR_TEXT_MUTED),
        unsafe_allow_html=True,
    )

    _, mid, _ = st.columns([1, 1.2, 1])
    with mid:
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Sign In", use_container_width=True)

        if submitted:
            if not username or not password:
                st.error("Enter both username and password.")
            else:
                ok, msg = attempt_login(username, password)
                if ok:
                    st.rerun()
                else:
                    st.error(msg)


if not is_logged_in():
    render_login()
    st.stop()

# Forces a password change for newly-seeded/admin-created accounts.
require_login()


# ════════════════════════════════════════════════════════════════════
# DASHBOARD (logged in)
# ════════════════════════════════════════════════════════════════════
with st.sidebar:
    render_sidebar()
    user = current_user()
    st.markdown("---")
    st.markdown(f"**{user['full_name']}**")
    st.caption(f"Role: {user['role_name']}")
    if st.button("Log out", use_container_width=True):
        logout()
        st.rerun()

hero_header(
    title="UDIF Pipeline Monitoring",
    accent_word="Monitoring",
    subtitle="",
)

st.markdown('<div class="udif-body">', unsafe_allow_html=True)

if not has_permission("analytics.view"):
    st.warning("Your role does not have access to dashboard analytics. Contact an administrator.")
    st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# KPI query
kpi_query = """
SELECT
    COUNT(DISTINCT pipeline_name)                                      AS active_pipelines,
    COUNT(*)                                                           AS total_executions,
    COALESCE(SUM(records_processed), 0)                               AS total_records,
    ROUND(
        100.0 * SUM(CASE WHEN status = 'SUCCESS' THEN 1 ELSE 0 END)
        / NULLIF(COUNT(*), 0), 2
    )                                                                  AS success_rate
FROM pipeline_audit;
"""
try:
    kpi_df           = run_query(kpi_query)
    active_pipelines = kpi_df.iloc[0]["active_pipelines"]
    total_executions = kpi_df.iloc[0]["total_executions"]
    total_records    = kpi_df.iloc[0]["total_records"]
    success_rate     = kpi_df.iloc[0]["success_rate"]
except Exception as e:
    st.error(f"Database Error: {e}")
    active_pipelines = total_executions = total_records = success_rate = 0

# KPI cards
col1, col2, col3, col4 = st.columns(4, gap="small")
with col1:
    kpi_card("Active Pipelines",  f"{active_pipelines}",     accent=COLOR_ACCENT)
with col2:
    kpi_card("Total Executions",  f"{total_executions:,}",   accent=COLOR_ACCENT)
with col3:
    kpi_card("Records Processed", f"{int(total_records):,}", accent=COLOR_ACCENT)
with col4:
    rate_accent = COLOR_SUCCESS if (success_rate and success_rate >= 95) else COLOR_WARNING
    kpi_card("Success Rate", f"{success_rate}%", accent=rate_accent)

st.markdown("<div style='margin-top:14px;'></div>", unsafe_allow_html=True)
health_banner(success_rate)

# Pipeline Health Overview
section_header("Pipeline Health Overview", "Latest status per pipeline", icon="◈")

pipeline_query = """
WITH latest AS (
    SELECT DISTINCT ON (pipeline_name) pipeline_name, status
    FROM pipeline_audit ORDER BY pipeline_name, start_time DESC
)
SELECT
    p.pipeline_name,
    COUNT(*)                                                           AS total_runs,
    ROUND(
        100.0 * SUM(CASE WHEN p.status = 'SUCCESS' THEN 1 ELSE 0 END)
        / NULLIF(COUNT(*), 0), 2
    )                                                                  AS success_rate,
    l.status                                                           AS last_status
FROM pipeline_audit p
JOIN latest l ON p.pipeline_name = l.pipeline_name
GROUP BY p.pipeline_name, l.status
ORDER BY p.pipeline_name;
"""
pipeline_df = run_query(pipeline_query)
pipeline_df["last_status"] = pipeline_df["last_status"].apply(status_pill)
pipeline_df = pipeline_df.rename(columns={
    "pipeline_name": "Pipeline", "total_runs": "Total Runs",
    "success_rate": "Success Rate %", "last_status": "Last Status",
})
st.markdown(
    '<div class="udif-card-tight">'
    + pipeline_df.to_html(escape=False, index=False, classes="udif-table")
    + "</div>",
    unsafe_allow_html=True,
)

# Latest Executions
section_header("Latest Executions", "Most recent 10 runs across all pipelines", icon="◷")

recent_query = """
SELECT pipeline_name, status, records_processed, duration_seconds, start_time, end_time
FROM pipeline_audit ORDER BY start_time DESC LIMIT 10;
"""
recent_df = run_query(recent_query)
recent_df["status"] = recent_df["status"].apply(status_pill)
recent_df = recent_df.rename(columns={
    "pipeline_name": "Pipeline", "status": "Status",
    "records_processed": "Records", "duration_seconds": "Duration (s)",
    "start_time": "Start Time", "end_time": "End Time",
})
st.markdown(
    '<div class="udif-card-tight">'
    + recent_df.to_html(escape=False, index=False, classes="udif-table")
    + "</div>",
    unsafe_allow_html=True,
)

st.markdown('</div>', unsafe_allow_html=True)

# Footer
st.markdown(
    f'<div style="font-size:12px;color:{COLOR_TEXT_FAINT};'
    f'border-top:1px solid {COLOR_BORDER};padding:14px 3rem;">'
    f'UDIF Monitoring Portal &nbsp;·&nbsp; Streamlit + PostgreSQL + Airflow</div>',
    unsafe_allow_html=True,
)