import streamlit as st
import plotly.express as px
from db.connection import run_query
from auth.rbac import require_permission
from Theme import (
    inject_base_styles, render_sidebar, page_header, section_header,
    kpi_card, status_pill, health_banner,
    PLOTLY_LAYOUT, PLOTLY_SEQUENCE,
    COLOR_ACCENT, COLOR_SUCCESS, COLOR_WARNING, COLOR_DANGER, COLOR_TEXT_MUTED,
)

st.set_page_config(page_title="Pipeline Explorer", page_icon="◇", layout="wide")
inject_base_styles()

require_permission("analytics.view")

with st.sidebar:
    render_sidebar()

page_header(
    eyebrow="Operations",
    title="Pipeline Explorer",
    subtitle="Drill into a single pipeline's health, trend, and run history",
)

st.markdown('<div class="udif-body" style="padding-top:0;">', unsafe_allow_html=True)

def format_datetime(value):
    try:
        return value.strftime("%d-%b-%Y %H:%M")
    except Exception:
        return value

pipeline_df = run_query("SELECT DISTINCT pipeline_name FROM pipeline_audit ORDER BY pipeline_name;")
pipeline_list = pipeline_df["pipeline_name"].tolist()

if not pipeline_list:
    st.info("No pipeline executions recorded yet.")
    st.stop()

selected_pipeline = st.selectbox("Select Pipeline", pipeline_list)

# Latest run metrics — parameterized, not f-string interpolated.
latest_df = run_query(
    """
    SELECT status, start_time, duration_seconds, records_processed
    FROM pipeline_audit WHERE pipeline_name = :pipeline_name
    ORDER BY start_time DESC LIMIT 1;
    """,
    {"pipeline_name": selected_pipeline},
)

if not latest_df.empty:
    status   = latest_df.iloc[0]["status"]
    start_time = latest_df.iloc[0]["start_time"]
    duration = latest_df.iloc[0]["duration_seconds"]
    records  = latest_df.iloc[0]["records_processed"]
    status_accent = COLOR_SUCCESS if status == "SUCCESS" else COLOR_DANGER

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(
            f'<div class="kpi-card">'
            f'<div class="kpi-accent-bar" style="background:{status_accent};"></div>'
            f'<div class="kpi-label">Last Status</div>'
            f'<div style="margin-top:2px;">{status_pill(status)}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
    with c2:
        kpi_card("Last Run", format_datetime(start_time), accent=COLOR_ACCENT)
    with c3:
        kpi_card("Duration (sec)", f"{duration}", accent=COLOR_ACCENT)
    with c4:
        kpi_card("Records Processed", f"{records:,}" if records is not None else "—", accent=COLOR_ACCENT)

# Pipeline health aggregates
health_df = run_query(
    """
    SELECT
        COUNT(*) total_runs,
        SUM(CASE WHEN status='SUCCESS' THEN 1 ELSE 0 END) success_runs,
        SUM(CASE WHEN status='FAILED'  THEN 1 ELSE 0 END) failed_runs,
        ROUND(100.0 * SUM(CASE WHEN status='SUCCESS' THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0), 2) success_rate,
        ROUND(AVG(duration_seconds), 2) avg_duration
    FROM pipeline_audit WHERE pipeline_name = :pipeline_name;
    """,
    {"pipeline_name": selected_pipeline},
)
success_rate = health_df.iloc[0]["success_rate"]

section_header("Pipeline Health", f"Aggregated across all runs of {selected_pipeline}")
rate_accent = COLOR_SUCCESS if success_rate and success_rate >= 95 else (
    COLOR_WARNING if success_rate and success_rate >= 80 else COLOR_DANGER
)
m1, m2, m3, m4 = st.columns(4)
with m1: kpi_card("Success Rate",    f"{success_rate}%",                    accent=rate_accent)
with m2: kpi_card("Failed Runs",     f"{health_df.iloc[0]['failed_runs']}",  accent=COLOR_DANGER)
with m3: kpi_card("Avg Duration (s)",f"{health_df.iloc[0]['avg_duration']}",accent=COLOR_ACCENT)
with m4: kpi_card("Total Runs",      f"{health_df.iloc[0]['total_runs']}",  accent=COLOR_ACCENT)

st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)
health_banner(success_rate)

# Execution trend
trend_df = run_query(
    """
    SELECT DATE(start_time) run_date, COUNT(*) executions
    FROM pipeline_audit WHERE pipeline_name = :pipeline_name
    GROUP BY DATE(start_time) ORDER BY run_date;
    """,
    {"pipeline_name": selected_pipeline},
)
section_header("Execution Trend", "Daily run count over time")
fig = px.line(trend_df, x="run_date", y="executions", markers=True)
fig.update_traces(line_color=COLOR_ACCENT, marker=dict(size=6, color=COLOR_ACCENT))
fig.update_layout(**PLOTLY_LAYOUT, height=380, xaxis_title=None, yaxis_title="Executions")
st.markdown('<div class="udif-card">', unsafe_allow_html=True)
st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
st.markdown("</div>", unsafe_allow_html=True)

# Recent failures
section_header("Recent Failures", "Last 10 failed executions for this pipeline")
failure_df = run_query(
    """
    SELECT start_time, error_message FROM pipeline_audit
    WHERE pipeline_name = :pipeline_name AND status='FAILED'
    ORDER BY start_time DESC LIMIT 10;
    """,
    {"pipeline_name": selected_pipeline},
)
if failure_df.empty:
    st.markdown('<div class="udif-banner ok">● No failures recorded for this pipeline.</div>', unsafe_allow_html=True)
else:
    failure_df["start_time"] = failure_df["start_time"].apply(format_datetime)
    failure_df = failure_df.rename(columns={"start_time": "Start Time", "error_message": "Error Message"})
    st.dataframe(failure_df, use_container_width=True, hide_index=True)

# Execution history
section_header("Execution History", "Last 20 runs, most recent first")
history_df = run_query(
    """
    SELECT start_time, end_time, status, records_processed, duration_seconds, error_message
    FROM pipeline_audit WHERE pipeline_name = :pipeline_name
    ORDER BY start_time DESC LIMIT 20;
    """,
    {"pipeline_name": selected_pipeline},
)
history_df["start_time"] = history_df["start_time"].apply(format_datetime)
history_df["end_time"]   = history_df["end_time"].apply(format_datetime)
history_df["status"]     = history_df["status"].apply(status_pill)
history_df = history_df.rename(columns={
    "start_time": "Start Time", "end_time": "End Time", "status": "Status",
    "records_processed": "Records", "duration_seconds": "Duration (s)", "error_message": "Error Message",
})
st.markdown(
    '<div class="udif-card-tight">'
    + history_df.to_html(escape=False, index=False, classes="udif-table")
    + "</div>",
    unsafe_allow_html=True,
)

st.markdown('</div>', unsafe_allow_html=True)
st.markdown(
    f'<div style="font-size:12px;color:{COLOR_TEXT_MUTED};border-top:1px solid #E8ECF4;padding:14px 3rem;">'
    f'UDIF Monitoring Portal · Pipeline Explorer</div>',
    unsafe_allow_html=True,
)