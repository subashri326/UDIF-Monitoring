import streamlit as st

from db.connection import run_query, execute_query, create_pipeline
from db.queries import (
    LIST_PIPELINES, LIST_ACTIVE_DATASETS,
    SET_PIPELINE_ACTIVE, CHECK_PIPELINE_NAME_EXISTS,
)
from auth.rbac import require_permission, has_permission, log_action
from Theme import (
    inject_base_styles, render_sidebar, page_header, section_header,
    kpi_card, COLOR_ACCENT, COLOR_SUCCESS, COLOR_DANGER, COLOR_TEXT_MUTED,
)

st.set_page_config(page_title="Pipeline Management", page_icon="⚙", layout="wide")
inject_base_styles()

# Gate the whole page on at least view access; finer controls (create,
# activate) are checked individually below so a Viewer sees a read-only
# list while an Operator/Admin sees the management controls too.
require_permission("pipeline.view")

with st.sidebar:
    render_sidebar()

page_header(
    eyebrow="Operations",
    title="Pipeline Management",
    subtitle="Create pipelines and control their active schedule",
)

st.markdown('<div class="udif-body" style="padding-top:0;">', unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════
# DERIVE MODE FROM SOURCE/TARGET STORAGE TYPE
# ════════════════════════════════════════════════════════════════════
def derive_mode(source_storage_type: str, target_storage_type: str) -> str:
    """
    Maps dataset_master.storage_type values to the pipeline_mode
    convention already used by pipeline_config (db_to_storage,
    storage_to_db, db_to_db, storage_to_storage).
    Treats DATABASE/db as "db", everything else (FILE, OBJECT_STORAGE,
    s3, local, file) as "storage".
    """
    def normalize(storage_type):
        s = (storage_type or "").strip().lower()
        return "db" if s in ("database", "db") else "storage"

    src = normalize(source_storage_type)
    tgt = normalize(target_storage_type)
    return f"{src}_to_{tgt}"


# ════════════════════════════════════════════════════════════════════
# KPI SUMMARY
# ════════════════════════════════════════════════════════════════════
try:
    pipelines_df = run_query(LIST_PIPELINES)
except Exception as e:
    st.error(f"Database Error: {e}")
    pipelines_df = None

if pipelines_df is not None:
    total_pipelines = len(pipelines_df)
    active_count = int(pipelines_df["is_active"].sum()) if total_pipelines else 0
    c1, c2 = st.columns(2)
    with c1:
        kpi_card("Total Pipelines", f"{total_pipelines}", accent=COLOR_ACCENT)
    with c2:
        kpi_card("Active Pipelines", f"{active_count}", accent=COLOR_SUCCESS)


# ════════════════════════════════════════════════════════════════════
# CREATE PIPELINE
# ════════════════════════════════════════════════════════════════════
if has_permission("pipeline.create"):
    section_header("Create Pipeline", "Wire a source dataset to a target dataset", icon="＋")

    try:
        datasets_df = run_query(LIST_ACTIVE_DATASETS)
    except Exception as e:
        st.error(f"Could not load datasets: {e}")
        datasets_df = None

    if datasets_df is None or datasets_df.empty:
        st.info("No active datasets found. Register source and target datasets first under Dataset Management.")
    else:
        dataset_options = {
            f"{row.dataset_name}  ·  {row.storage_type}": row
            for row in datasets_df.itertuples()
        }

        st.markdown('<div class="udif-card">', unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            pipeline_name = st.text_input("Pipeline Name", placeholder="e.g. orders_db_to_s3_pipeline")
            source_label = st.selectbox("Source Dataset", list(dataset_options.keys()), key="source_ds")
        with col2:
            cron_expression = st.text_input("Cron Expression", value="*/5 * * * *",
                                             help="Standard cron syntax, e.g. */5 * * * * = every 5 minutes")
            target_label = st.selectbox("Target Dataset", list(dataset_options.keys()), key="target_ds")

        source_row = dataset_options[source_label]
        target_row = dataset_options[target_label]
        suggested_mode = derive_mode(source_row.storage_type, target_row.storage_type)

        mode_options = ["db_to_storage", "storage_to_db", "db_to_db", "storage_to_storage"]
        default_index = mode_options.index(suggested_mode) if suggested_mode in mode_options else 0
        pipeline_mode = st.selectbox(
            "Pipeline Mode (auto-detected — override if needed)",
            mode_options,
            index=default_index,
        )

        create_clicked = st.button("Create Pipeline", type="primary")
        st.markdown('</div>', unsafe_allow_html=True)

        if create_clicked:
            if not pipeline_name.strip():
                st.error("Pipeline name is required.")
            elif source_row.dataset_id == target_row.dataset_id:
                st.error("Source and target dataset must be different.")
            else:
                existing = run_query(CHECK_PIPELINE_NAME_EXISTS, {"pipeline_name": pipeline_name.strip()})
                if not existing.empty:
                    st.error(f"A pipeline named '{pipeline_name}' already exists. Choose a different name.")
                else:
                    try:
                        create_pipeline(
                            pipeline_name=pipeline_name.strip(),
                            cron_expression=cron_expression.strip(),
                            pipeline_mode=pipeline_mode,
                            source_dataset_id=int(source_row.dataset_id),
                            target_dataset_id=int(target_row.dataset_id),
                        )
                        log_action(
                            action="pipeline.create",
                            target=f"pipeline_name={pipeline_name.strip()}",
                            details=f"mode={pipeline_mode}, source={source_row.dataset_name}, target={target_row.dataset_name}",
                        )
                        st.success(f"Pipeline '{pipeline_name}' created and activated.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed to create pipeline: {e}")


# ════════════════════════════════════════════════════════════════════
# PIPELINE LIST + ACTIVATE/DEACTIVATE
# ════════════════════════════════════════════════════════════════════
section_header("Pipelines", "All configured pipelines and their current schedule status", icon="◷")

if pipelines_df is None or pipelines_df.empty:
    st.info("No pipelines configured yet.")
else:
    can_toggle = has_permission("pipeline.activate") or has_permission("pipeline.deactivate")

    for row in pipelines_df.itertuples():
        st.markdown('<div class="udif-card">', unsafe_allow_html=True)
        cols = st.columns([3, 2, 2, 2, 2])

        with cols[0]:
            st.markdown(f"**{row.pipeline_name}**")
            st.caption(f"{row.source_dataset} → {row.target_dataset}")
        with cols[1]:
            st.caption("Mode")
            st.write(row.pipeline_mode)
        with cols[2]:
            st.caption("Schedule")
            st.write(row.cron_expression or "—")
        with cols[3]:
            st.caption("Status")
            if row.is_active:
                st.markdown(f'<span style="color:{COLOR_SUCCESS};">● Active</span>', unsafe_allow_html=True)
            else:
                st.markdown(f'<span style="color:{COLOR_DANGER};">● Inactive</span>', unsafe_allow_html=True)
        with cols[4]:
            if can_toggle:
                if row.is_active:
                    if has_permission("pipeline.deactivate") and st.button(
                        "Deactivate", key=f"deactivate_{row.pipeline_id}"
                    ):
                        ok, msg = execute_query(
                            SET_PIPELINE_ACTIVE,
                            {"is_active": False, "pipeline_id": int(row.pipeline_id)},
                        )
                        if ok:
                            log_action("pipeline.deactivate", target=f"pipeline_id={row.pipeline_id}")
                            st.rerun()
                        else:
                            st.error(msg)
                else:
                    if has_permission("pipeline.activate") and st.button(
                        "Activate", key=f"activate_{row.pipeline_id}"
                    ):
                        ok, msg = execute_query(
                            SET_PIPELINE_ACTIVE,
                            {"is_active": True, "pipeline_id": int(row.pipeline_id)},
                        )
                        if ok:
                            log_action("pipeline.activate", target=f"pipeline_id={row.pipeline_id}")
                            st.rerun()
                        else:
                            st.error(msg)

        st.markdown('</div>', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

st.markdown(
    f'<div style="font-size:12px;color:{COLOR_TEXT_MUTED};border-top:1px solid #E8ECF4;padding:14px 3rem;">'
    f'UDIF Monitoring Portal · Pipeline Management</div>',
    unsafe_allow_html=True,
)