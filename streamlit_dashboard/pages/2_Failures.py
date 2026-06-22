import streamlit as st
import plotly.express as px
from db.connection import run_query
from auth.rbac import require_permission
from Theme import (
    inject_base_styles, render_sidebar, page_header, section_header, kpi_card,
    PLOTLY_LAYOUT, COLOR_DANGER, COLOR_TEXT_MUTED,
)

st.set_page_config(page_title="Failures Dashboard", page_icon="◈", layout="wide")
inject_base_styles()

require_permission("analytics.view")

with st.sidebar:
    render_sidebar()

page_header(
    eyebrow="Operations",
    title="Failure Monitoring",
    subtitle="Failure trends, impacted pipelines, and root-cause analysis",
)

st.markdown('<div class="udif-body" style="padding-top:0;">', unsafe_allow_html=True)

kpi_df = run_query("""
SELECT COUNT(*) AS total_failures, COUNT(DISTINCT pipeline_name) AS impacted_pipelines
FROM pipeline_audit WHERE status='FAILED';
""")
col1, col2 = st.columns(2)
with col1: kpi_card("Total Failures",     f"{kpi_df.iloc[0]['total_failures']}",    accent=COLOR_DANGER)
with col2: kpi_card("Impacted Pipelines", f"{kpi_df.iloc[0]['impacted_pipelines']}", accent=COLOR_DANGER)

section_header("Failure Trend", "Daily failure count")
trend_df = run_query("""
SELECT DATE(start_time) AS failure_date, COUNT(*) AS failures
FROM pipeline_audit WHERE status='FAILED'
GROUP BY DATE(start_time) ORDER BY failure_date;
""")
if not trend_df.empty:
    fig = px.line(trend_df, x="failure_date", y="failures", markers=True)
    fig.update_traces(line_color=COLOR_DANGER, marker=dict(size=6, color=COLOR_DANGER))
    fig.update_layout(**PLOTLY_LAYOUT, height=380, xaxis_title=None, yaxis_title="Failures")
    st.markdown('<div class="udif-card">', unsafe_allow_html=True)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    st.markdown("</div>", unsafe_allow_html=True)
else:
    st.markdown('<div class="udif-banner ok">● No failures recorded.</div>', unsafe_allow_html=True)

section_header("Top Failing Pipelines", "Ranked by failure count")
pf_df = run_query("""
SELECT pipeline_name, COUNT(*) AS failure_count FROM pipeline_audit
WHERE status='FAILED' GROUP BY pipeline_name ORDER BY failure_count DESC;
""")
pf_df = pf_df.rename(columns={"pipeline_name": "Pipeline", "failure_count": "Failure Count"})
st.dataframe(pf_df, use_container_width=True, hide_index=True)

section_header("Recent Failed Executions", "Last 20 failures across all pipelines")
rf_df = run_query("""
SELECT pipeline_name, start_time, error_message FROM pipeline_audit
WHERE status='FAILED' ORDER BY start_time DESC LIMIT 20;
""")
rf_df = rf_df.rename(columns={"pipeline_name": "Pipeline", "start_time": "Start Time", "error_message": "Error Message"})
st.dataframe(rf_df, use_container_width=True, hide_index=True)

section_header("Error Analysis", "Most frequent error messages")
err_df = run_query("""
SELECT error_message, COUNT(*) AS occurrence_count FROM pipeline_audit
WHERE status='FAILED' AND error_message IS NOT NULL
GROUP BY error_message ORDER BY occurrence_count DESC;
""")
err_df = err_df.rename(columns={"error_message": "Error Message", "occurrence_count": "Occurrences"})
st.dataframe(err_df, use_container_width=True, hide_index=True)

st.markdown('</div>', unsafe_allow_html=True)
st.markdown(
    f'<div style="font-size:12px;color:{COLOR_TEXT_MUTED};border-top:1px solid #E8ECF4;padding:14px 3rem;">'
    f'UDIF Monitoring Portal · Failure Analysis</div>',
    unsafe_allow_html=True,
)