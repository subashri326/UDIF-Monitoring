import streamlit as st
import plotly.express as px
from db.connection import run_query
from auth.rbac import require_permission
from Theme import (
    inject_base_styles, render_sidebar, page_header, section_header, kpi_card,
    PLOTLY_LAYOUT, COLOR_ACCENT, COLOR_SUCCESS, COLOR_TEXT_MUTED,
)

st.set_page_config(page_title="Analytics Dashboard", page_icon="◆", layout="wide")
inject_base_styles()

require_permission("analytics.view")

with st.sidebar:
    render_sidebar()

page_header(
    eyebrow="Insights",
    title="Analytics",
    subtitle="Pipeline performance, throughput, and runtime trends",
)

st.markdown('<div class="udif-body" style="padding-top:0;">', unsafe_allow_html=True)

kpi_df = run_query("""
SELECT
    ROUND(100.0 * SUM(CASE WHEN status='SUCCESS' THEN 1 ELSE 0 END) / COUNT(*), 2) AS success_rate,
    ROUND(AVG(duration_seconds), 2) AS avg_runtime,
    COALESCE(SUM(records_processed), 0) AS total_records
FROM pipeline_audit;
""")
success_rate = kpi_df.iloc[0]["success_rate"]
c1, c2, c3 = st.columns(3)
with c1: kpi_card("Success Rate",   f"{success_rate}%",                      accent=COLOR_SUCCESS)
with c2: kpi_card("Avg Runtime (s)",f"{kpi_df.iloc[0]['avg_runtime']}",      accent=COLOR_ACCENT)
with c3: kpi_card("Total Records",  f"{int(kpi_df.iloc[0]['total_records']):,}", accent=COLOR_ACCENT)

section_header("Execution Volume Trend", "Daily execution count across all pipelines")
exec_df = run_query("""
SELECT DATE(start_time) AS run_date, COUNT(*) AS executions
FROM pipeline_audit GROUP BY DATE(start_time) ORDER BY run_date;
""")
fig = px.line(exec_df, x="run_date", y="executions", markers=True)
fig.update_traces(line_color=COLOR_ACCENT, marker=dict(size=6, color=COLOR_ACCENT))
fig.update_layout(**PLOTLY_LAYOUT, height=380, xaxis_title=None, yaxis_title="Executions")
st.markdown('<div class="udif-card">', unsafe_allow_html=True)
st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
st.markdown("</div>", unsafe_allow_html=True)

section_header("Records Processed Trend", "Daily record throughput")
rec_df = run_query("""
SELECT DATE(start_time) AS run_date, SUM(records_processed) AS total_records
FROM pipeline_audit GROUP BY DATE(start_time) ORDER BY run_date;
""")
fig = px.bar(rec_df, x="run_date", y="total_records")
fig.update_traces(marker_color=COLOR_ACCENT)
fig.update_layout(**PLOTLY_LAYOUT, height=380, xaxis_title=None, yaxis_title="Records")
st.markdown('<div class="udif-card">', unsafe_allow_html=True)
st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
st.markdown("</div>", unsafe_allow_html=True)

section_header("Pipeline Performance Ranking", "Sorted by success rate")
perf_df = run_query("""
SELECT pipeline_name, COUNT(*) AS total_runs,
    ROUND(100.0 * SUM(CASE WHEN status='SUCCESS' THEN 1 ELSE 0 END) / COUNT(*), 2) AS success_rate
FROM pipeline_audit GROUP BY pipeline_name ORDER BY success_rate DESC;
""")
perf_df = perf_df.rename(columns={"pipeline_name": "Pipeline", "total_runs": "Total Runs", "success_rate": "Success Rate %"})
st.dataframe(perf_df, use_container_width=True, hide_index=True)

section_header("Average Runtime Analysis", "By pipeline")
rt_df = run_query("""
SELECT pipeline_name, ROUND(AVG(duration_seconds), 2) AS avg_runtime
FROM pipeline_audit GROUP BY pipeline_name ORDER BY avg_runtime DESC;
""")
fig = px.bar(rt_df, x="pipeline_name", y="avg_runtime")
fig.update_traces(marker_color=COLOR_ACCENT)
fig.update_layout(**PLOTLY_LAYOUT, height=380, xaxis_title=None, yaxis_title="Avg Runtime (s)")
st.markdown('<div class="udif-card">', unsafe_allow_html=True)
st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
st.markdown("</div>", unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)
st.markdown(
    f'<div style="font-size:12px;color:{COLOR_TEXT_MUTED};border-top:1px solid #E8ECF4;padding:14px 3rem;">'
    f'UDIF Monitoring Portal · Analytics</div>',
    unsafe_allow_html=True,
)