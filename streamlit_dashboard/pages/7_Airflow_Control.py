import streamlit as st
import pandas as pd
from datetime import datetime

from airflow_client import (
    health, list_dags, trigger_dag,
    pause_dag, unpause_dag, get_dag_runs, get_task_instances,
)
from db.connection import run_query
from auth.rbac import require_permission, has_permission, log_action
from Theme import (
    inject_base_styles, render_sidebar, page_header, section_header,
    kpi_card, COLOR_ACCENT, COLOR_SUCCESS, COLOR_DANGER,
    COLOR_WARNING, COLOR_TEXT_MUTED, COLOR_BORDER,
)

st.set_page_config(page_title="Airflow Control", page_icon="", layout="wide")
inject_base_styles()

require_permission("pipeline.view")

with st.sidebar:
    render_sidebar()

page_header(
    eyebrow="Orchestration",
    title="Airflow Control",
    subtitle="Monitor DAG status, trigger runs, and inspect execution history",
)

st.markdown('<div class="udif-body" style="padding-top:0;">', unsafe_allow_html=True)


# ── helpers ───────────────────────────────────────────────────────────────────
def fmt_dt(val):
    """Format an ISO datetime string to a readable local format."""
    if not val:
        return "—"
    try:
        dt = datetime.fromisoformat(val.replace("Z", "+00:00"))
        return dt.strftime("%d %b %Y  %H:%M:%S")
    except Exception:
        return str(val)


def state_pill(state: str) -> str:
    s = (state or "").lower()
    color_map = {
        "success":  ("#15803D", "#F0FDF4", "#BBF7D0"),
        "running":  ("#1D4ED8", "#EFF6FF", "#BFDBFE"),
        "failed":   ("#DC2626", "#FEF2F2", "#FECACA"),
        "queued":   ("#D97706", "#FFFBEB", "#FDE68A"),
        "skipped":  ("#6B7280", "#F9FAFB", "#E5E7EB"),
    }
    fg, bg, border = color_map.get(s, ("#6B7280", "#F9FAFB", "#E5E7EB"))
    return (
        f'<span style="display:inline-flex;align-items:center;gap:5px;'
        f'padding:3px 10px;border-radius:999px;font-size:12px;font-weight:700;'
        f'background:{bg};color:{fg};border:1px solid {border};">'
        f'<span style="width:5px;height:5px;border-radius:50%;'
        f'background:{fg};display:inline-block;"></span>{s.upper()}</span>'
    )


def paused_badge(is_paused: bool) -> str:
    if is_paused:
        return (
            '<span style="font-size:11px;font-weight:700;color:#D97706;'
            'background:#FFFBEB;border:1px solid #FDE68A;'
            'padding:2px 8px;border-radius:999px;">PAUSED</span>'
        )
    return (
        '<span style="font-size:11px;font-weight:700;color:#15803D;'
        'background:#F0FDF4;border:1px solid #BBF7D0;'
        'padding:2px 8px;border-radius:999px;">ACTIVE</span>'
    )


# ════════════════════════════════════════════════════════════════════════════════
# AIRFLOW HEALTH
# ════════════════════════════════════════════════════════════════════════════════
section_header("Airflow Health")

try:
    h = health()
    db_status   = h.get("metadatabase", {}).get("status", "unknown")
    sch_status  = h.get("scheduler",    {}).get("status", "unknown")

    c1, c2, c3 = st.columns(3)
    with c1:
        accent = COLOR_SUCCESS if db_status == "healthy" else COLOR_DANGER
        kpi_card("Metadata DB", db_status.upper(), accent=accent)
    with c2:
        accent = COLOR_SUCCESS if sch_status == "healthy" else COLOR_DANGER
        kpi_card("Scheduler", sch_status.upper(), accent=accent)
    with c3:
        kpi_card("Airflow API", "CONNECTED", accent=COLOR_SUCCESS)

    airflow_ok = True

except RuntimeError as e:
    st.markdown(
        f'<div class="udif-banner bad">'
        f'Airflow unreachable — {e}'
        f'</div>',
        unsafe_allow_html=True,
    )
    airflow_ok = False

if not airflow_ok:
    st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════════════════
# LOAD DAGS + MATCH TO pipeline_master
# ════════════════════════════════════════════════════════════════════════════════
try:
    all_dags = list_dags()
    dag_map  = {d["dag_id"]: d for d in all_dags}
except RuntimeError as e:
    st.error(f"Failed to load DAGs: {e}")
    st.stop()

# Pull pipeline names from DB so we only show UDIF-managed DAGs
try:
    pipelines_df = run_query(
        "SELECT pipeline_id, pipeline_name, is_active FROM pipeline_master ORDER BY pipeline_name"
    )
except Exception as e:
    st.error(f"DB error: {e}")
    st.stop()


# ════════════════════════════════════════════════════════════════════════════════
# DAG OVERVIEW TABLE
# ════════════════════════════════════════════════════════════════════════════════
section_header(
    "Pipeline DAGs",
    "One row per UDIF pipeline — shows Airflow state alongside DB active flag",
)

can_trigger = has_permission("pipeline.activate")
can_pause   = has_permission("pipeline.deactivate")

if pipelines_df.empty:
    st.info("No pipelines registered in pipeline_master yet.")
else:
    for row in pipelines_df.itertuples():
        dag_id  = row.pipeline_name
        dag     = dag_map.get(dag_id)

        st.markdown('<div class="udif-card" style="margin-bottom:10px;">', unsafe_allow_html=True)
        cols = st.columns([2.5, 1.2, 1.2, 1.5, 1.5, 2.5])

        # ── Pipeline name
        with cols[0]:
            st.markdown(f"**{dag_id}**")
            if dag:
                next_run = fmt_dt(dag.get("next_dagrun"))
                st.caption(f"Next run: {next_run}")
            else:
                st.caption("Not found in Airflow")

        # ── DB active flag
        with cols[1]:
            st.caption("DB Schedule")
            color = COLOR_SUCCESS if row.is_active else COLOR_WARNING
            label = "Active" if row.is_active else "Inactive"
            st.markdown(
                f'<span style="color:{color};font-weight:600;font-size:13px;">'
                f'● {label}</span>',
                unsafe_allow_html=True,
            )

        # ── Airflow paused state
        with cols[2]:
            st.caption("Airflow State")
            if dag:
                st.markdown(paused_badge(dag.get("is_paused", True)), unsafe_allow_html=True)
            else:
                st.markdown(
                    '<span style="font-size:12px;color:#9CA3AF;">DAG not found</span>',
                    unsafe_allow_html=True,
                )

        # ── Last run status
        with cols[3]:
            st.caption("Last Run")
            if dag:
                try:
                    runs = get_dag_runs(dag_id, limit=1)
                    if runs:
                        st.markdown(state_pill(runs[0]["state"]), unsafe_allow_html=True)
                        st.caption(fmt_dt(runs[0].get("start_date")))
                    else:
                        st.markdown('<span style="color:#9CA3AF;font-size:13px;">No runs yet</span>', unsafe_allow_html=True)
                except Exception:
                    st.markdown('<span style="color:#9CA3AF;font-size:13px;">—</span>', unsafe_allow_html=True)
            else:
                st.markdown('<span style="color:#9CA3AF;font-size:13px;">—</span>', unsafe_allow_html=True)

        # ── Pause / Unpause
        with cols[4]:
            if dag and can_pause:
                is_paused = dag.get("is_paused", True)
                btn_label = "Unpause" if is_paused else "Pause"
                if st.button(btn_label, key=f"pause_{dag_id}"):
                    try:
                        if is_paused:
                            unpause_dag(dag_id)
                            log_action("airflow.unpause", target=f"dag_id={dag_id}")
                            st.success(f"DAG '{dag_id}' unpaused.")
                        else:
                            pause_dag(dag_id)
                            log_action("airflow.pause", target=f"dag_id={dag_id}")
                            st.success(f"DAG '{dag_id}' paused.")
                        st.rerun()
                    except RuntimeError as e:
                        st.error(str(e))

        # ── Trigger run now
        with cols[5]:
            if dag and can_trigger:
                if st.button("Run Now", key=f"trigger_{dag_id}", type="primary"):
                    try:
                        result = trigger_dag(dag_id)
                        run_id = result.get("dag_run_id", "")
                        log_action(
                            "airflow.trigger",
                            target=f"dag_id={dag_id}",
                            details=f"run_id={run_id}",
                        )
                        st.success(f"Triggered! Run ID: `{run_id}`")
                        st.rerun()
                    except RuntimeError as e:
                        st.error(str(e))

        st.markdown('</div>', unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════════════════
# RUN HISTORY DRILL-DOWN
# ════════════════════════════════════════════════════════════════════════════════
st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)
section_header("Run History", "Select a pipeline to see its last 10 Airflow DAG runs")

known_dag_ids = [
    row.pipeline_name for row in pipelines_df.itertuples()
    if row.pipeline_name in dag_map
]

if not known_dag_ids:
    st.info("No pipeline DAGs found in Airflow matching pipeline_master names.")
else:
    selected_dag = st.selectbox("Pipeline", known_dag_ids, key="history_dag_select")

    try:
        runs = get_dag_runs(selected_dag, limit=10)
    except RuntimeError as e:
        st.error(str(e))
        runs = []

    if not runs:
        st.markdown(
            '<div class="udif-banner ok">No runs recorded for this DAG yet.</div>',
            unsafe_allow_html=True,
        )
    else:
        rows = []
        for r in runs:
            rows.append({
                "Run ID":         r.get("dag_run_id", ""),
                "State":          r.get("state", ""),
                "Execution Date": fmt_dt(r.get("execution_date")),
                "Start":          fmt_dt(r.get("start_date")),
                "End":            fmt_dt(r.get("end_date")),
                "Run Type":       r.get("run_type", ""),
            })
        runs_df = pd.DataFrame(rows)
        runs_df["State"] = runs_df["State"].apply(state_pill)

        st.markdown(
            '<div class="udif-card-tight">'
            + runs_df.to_html(escape=False, index=False, classes="udif-table")
            + "</div>",
            unsafe_allow_html=True,
        )

        # ── Task instance detail for most recent run
        latest_run_id = runs[0].get("dag_run_id") if runs else None
        if latest_run_id:
            st.markdown("<div style='height:6px;'></div>", unsafe_allow_html=True)
            section_header(
                "Task Instances",
                f"Tasks from most recent run: {latest_run_id}",
            )
            try:
                tasks = get_task_instances(selected_dag, latest_run_id)
                if tasks:
                    task_rows = []
                    for t in tasks:
                        duration = t.get("duration")
                        dur_str = f"{duration:.2f}s" if duration else "—"
                        task_rows.append({
                            "Task ID":  t.get("task_id", ""),
                            "State":    t.get("state", ""),
                            "Start":    fmt_dt(t.get("start_date")),
                            "End":      fmt_dt(t.get("end_date")),
                            "Duration": dur_str,
                            "Try #":    t.get("try_number", 1),
                        })
                    tasks_df = pd.DataFrame(task_rows)
                    tasks_df["State"] = tasks_df["State"].apply(state_pill)
                    st.markdown(
                        '<div class="udif-card-tight">'
                        + tasks_df.to_html(escape=False, index=False, classes="udif-table")
                        + "</div>",
                        unsafe_allow_html=True,
                    )
                else:
                    st.info("No task instances found for this run.")
            except RuntimeError as e:
                st.error(f"Could not load task instances: {e}")

st.markdown('</div>', unsafe_allow_html=True)

st.markdown(
    f'<div style="font-size:12px;color:{COLOR_TEXT_MUTED};'
    f'border-top:1px solid {COLOR_BORDER};padding:14px 3rem;">'
    f'UDIF Monitoring Portal · Airflow Control</div>',
    unsafe_allow_html=True,
)