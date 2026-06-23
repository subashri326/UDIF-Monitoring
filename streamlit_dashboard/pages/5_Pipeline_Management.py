import streamlit as st
from sqlalchemy import text
from db.connection import run_query, engine, execute_query, create_pipeline
from auth.rbac import require_permission, has_permission, log_action
from Theme import (
    inject_base_styles, render_sidebar, page_header, section_header,
    kpi_card, COLOR_ACCENT, COLOR_SUCCESS, COLOR_DANGER, COLOR_TEXT_MUTED,
)

st.set_page_config(page_title="Pipeline Management", page_icon="", layout="wide")
inject_base_styles()
require_permission("pipeline.view")

with st.sidebar:
    render_sidebar()

page_header(
    eyebrow="Operations",
    title="Pipeline Management",
    subtitle="Create pipelines and control their active schedule",
)

st.markdown('<div class="udif-body" style="padding-top:0;">', unsafe_allow_html=True)

# ── Session state ─────────────────────────────────────────────────────────────
if "pl_edit_id" not in st.session_state:
    st.session_state.pl_edit_id = None


def derive_mode(src_storage: str, tgt_storage: str) -> str:
    def norm(s): return "db" if (s or "").strip().lower() == "db" else "storage"
    return f"{norm(src_storage)}_to_{norm(tgt_storage)}"


def load_pipelines():
    return run_query("""
        SELECT
            pm.pipeline_id, pm.pipeline_name, pm.is_active,
            pm.cron_expression, pm.created_at,
            pc.config_id, pc.pipeline_mode,
            pc.source_dataset_id, pc.target_dataset_id,
            src.dataset_name  AS source_dataset,
            src.storage_type  AS source_storage_type,
            src.dataset_type  AS source_type,
            tgt.dataset_name  AS target_dataset,
            tgt.storage_type  AS target_storage_type,
            tgt.dataset_type  AS target_type
        FROM pipeline_master pm
        JOIN pipeline_config pc  ON pm.pipeline_id       = pc.pipeline_id
        JOIN dataset_master  src ON pc.source_dataset_id = src.dataset_id
        JOIN dataset_master  tgt ON pc.target_dataset_id = tgt.dataset_id
        ORDER BY pm.pipeline_id DESC
    """)


def load_pipeline_by_id(pipeline_id):
    df = run_query("""
        SELECT pm.*, pc.pipeline_mode, pc.pipeline_config_id,
               pc.source_dataset_id, pc.target_dataset_id
        FROM pipeline_master pm
        JOIN pipeline_config pc ON pm.pipeline_id = pc.pipeline_id
        WHERE pm.pipeline_id = :id
    """, {"id": pipeline_id})
    return df.iloc[0] if not df.empty else None


# ── KPIs ──────────────────────────────────────────────────────────────────────
try:
    pipelines_df = load_pipelines()
except Exception as e:
    st.error(f"Database error: {e}")
    pipelines_df = None

total  = len(pipelines_df) if pipelines_df is not None else 0
active = int(pipelines_df["is_active"].sum()) if pipelines_df is not None and total else 0

c1, c2, c3 = st.columns([1, 1, 3])
with c1: kpi_card("Total Pipelines",  f"{total}",  accent=COLOR_ACCENT)
with c2: kpi_card("Active Pipelines", f"{active}", accent=COLOR_SUCCESS)
with c3:
    st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)
    if st.button("View & Manage Pipelines", type="secondary"):
        st.session_state.show_pipeline_modal = True


# ── MODAL: View / Delete ───────────────────────────────────────────────────────
@st.dialog("Registered Pipelines", width="large")
def show_pipelines_modal():
    try:
        df = load_pipelines()
    except Exception as e:
        st.error(f"Could not load pipelines: {e}")
        return

    if df.empty:
        st.info("No pipelines configured yet.")
        return

    st.markdown(
        f"<div style='font-size:13px;color:{COLOR_TEXT_MUTED};"
        f"margin-bottom:12px;'>{len(df)} pipeline(s) on record</div>",
        unsafe_allow_html=True,
    )

    for row in df.itertuples():
        cols = st.columns([2.5, 2, 1, 0.8, 0.8, 0.8])

        with cols[0]:
            st.markdown(f"**{row.pipeline_name}**")
            st.caption(f"{row.source_dataset} → {row.target_dataset}")

        with cols[1]:
            st.caption("Mode · Cron")
            st.write(f"{row.pipeline_mode}  ·  {row.cron_expression or '—'}")

        with cols[2]:
            st.caption("Status")
            color = COLOR_SUCCESS if row.is_active else COLOR_DANGER
            label = "Active" if row.is_active else "Inactive"
            st.markdown(
                f'<span style="color:{color};font-weight:700;">{label}</span>',
                unsafe_allow_html=True,
            )

        with cols[3]:
            st.caption("ID")
            st.write(str(row.pipeline_id))

        with cols[4]:
            if st.button("Edit", key=f"modal_pl_edit_{row.pipeline_id}"):
                st.session_state.pl_edit_id = int(row.pipeline_id)
                st.rerun()

        with cols[5]:
            if has_permission("pipeline.deactivate"):
                if st.button("Delete", key=f"modal_pl_del_{row.pipeline_id}"):
                    try:
                        with engine.begin() as conn:
                            conn.execute(text(
                                "DELETE FROM pipeline_config WHERE pipeline_id = :id"
                            ), {"id": int(row.pipeline_id)})
                            conn.execute(text(
                                "DELETE FROM pipeline_master WHERE pipeline_id = :id"
                            ), {"id": int(row.pipeline_id)})
                        log_action("pipeline.delete",
                                   target=f"pipeline_id={row.pipeline_id}",
                                   details=f"name={row.pipeline_name}")
                        st.success(f"Deleted '{row.pipeline_name}'.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Delete failed: {e}")

        st.divider()


if st.session_state.get("show_pipeline_modal"):
    st.session_state.show_pipeline_modal = False
    show_pipelines_modal()


# ── Inline Edit Form ───────────────────────────────────────────────────────────
if st.session_state.pl_edit_id is not None:
    edit_row = load_pipeline_by_id(st.session_state.pl_edit_id)

    if edit_row is not None:
        section_header(
            f"Edit Pipeline — {edit_row['pipeline_name']}",
            "Update the fields below and save"
        )

        try:
            datasets_df = run_query("""
                SELECT dataset_id, dataset_name, storage_type, dataset_type
                FROM dataset_master WHERE is_active = TRUE ORDER BY dataset_name
            """)
        except Exception as e:
            st.error(f"Could not load datasets: {e}")
            datasets_df = None

        if datasets_df is not None and not datasets_df.empty:
            ds_options = {
                f"{r.dataset_name}  ·  {r.storage_type}  ·  {r.dataset_type}": r
                for r in datasets_df.itertuples()
            }
            ds_ids = {r.dataset_id: label for label, r in ds_options.items()}

            st.markdown('<div class="udif-card">', unsafe_allow_html=True)
            with st.form("edit_pipeline_form"):
                ec1, ec2 = st.columns(2)
                with ec1:
                    e_name = st.text_input("Pipeline Name *",
                                           value=edit_row["pipeline_name"] or "")
                    src_default = ds_ids.get(edit_row["source_dataset_id"],
                                             list(ds_options.keys())[0])
                    e_src = st.selectbox("Source Dataset *", list(ds_options.keys()),
                                         index=list(ds_options.keys()).index(src_default)
                                         if src_default in ds_options else 0)
                with ec2:
                    e_cron = st.text_input("Cron Expression",
                                           value=edit_row["cron_expression"] or "*/5 * * * *")
                    tgt_default = ds_ids.get(edit_row["target_dataset_id"],
                                             list(ds_options.keys())[0])
                    e_tgt = st.selectbox("Target Dataset *", list(ds_options.keys()),
                                         index=list(ds_options.keys()).index(tgt_default)
                                         if tgt_default in ds_options else 0)

                src_row = ds_options[e_src]
                tgt_row = ds_options[e_tgt]
                suggested = derive_mode(src_row.storage_type, tgt_row.storage_type)
                mode_opts = ["db_to_db", "db_to_storage", "storage_to_db", "storage_to_storage"]
                cur_mode  = edit_row["pipeline_mode"] or suggested
                e_mode = st.selectbox("Pipeline Mode",
                                      mode_opts,
                                      index=mode_opts.index(cur_mode)
                                      if cur_mode in mode_opts else 0)
                e_active = st.checkbox("Active", value=bool(edit_row["is_active"]))

                save_col, cancel_col = st.columns([1, 4])
                with save_col:
                    save = st.form_submit_button("Save Changes", type="primary")
                with cancel_col:
                    cancel = st.form_submit_button("Cancel")

            st.markdown('</div>', unsafe_allow_html=True)

            if cancel:
                st.session_state.pl_edit_id = None
                st.rerun()

            if save:
                if not e_name.strip():
                    st.error("Pipeline Name is required.")
                elif src_row.dataset_id == tgt_row.dataset_id:
                    st.error("Source and target dataset must be different.")
                else:
                    try:
                        with engine.begin() as conn:
                            conn.execute(text("""
                                UPDATE pipeline_master
                                SET pipeline_name  = :name,
                                    cron_expression = :cron,
                                    is_active       = :active
                                WHERE pipeline_id = :id
                            """), {
                                "name":   e_name.strip(),
                                "cron":   e_cron.strip(),
                                "active": e_active,
                                "id":     st.session_state.pl_edit_id,
                            })
                            conn.execute(text("""
                                UPDATE pipeline_config
                                SET pipeline_mode     = :mode,
                                    source_dataset_id = :src,
                                    target_dataset_id = :tgt
                                WHERE pipeline_id = :id
                            """), {
                                "mode": e_mode,
                                "src":  int(src_row.dataset_id),
                                "tgt":  int(tgt_row.dataset_id),
                                "id":   st.session_state.pl_edit_id,
                            })
                        log_action("pipeline.edit",
                                   target=f"pipeline_id={st.session_state.pl_edit_id}",
                                   details=f"name={e_name.strip()}, mode={e_mode}")
                        st.success("Pipeline updated successfully.")
                        st.session_state.pl_edit_id = None
                        st.rerun()
                    except Exception as e:
                        st.error(f"Update failed: {e}")


# ── Create Pipeline ────────────────────────────────────────────────────────────
if has_permission("pipeline.create") and st.session_state.pl_edit_id is None:
    section_header("Create Pipeline", "Wire a source dataset to a target dataset")

    try:
        datasets_df = run_query("""
            SELECT dataset_id, dataset_name, storage_type, dataset_type
            FROM dataset_master WHERE is_active = TRUE ORDER BY dataset_name
        """)
    except Exception as e:
        st.error(f"Could not load datasets: {e}")
        datasets_df = None

    if datasets_df is None or datasets_df.empty:
        st.info("No active datasets found. Register datasets first.")
    else:
        options = {
            f"{r.dataset_name}  ·  {r.storage_type}  ·  {r.dataset_type}": r
            for r in datasets_df.itertuples()
        }

        st.markdown('<div class="udif-card">', unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            pipeline_name   = st.text_input("Pipeline Name *",
                                             placeholder="e.g. mysql_to_postgres")
            source_label    = st.selectbox("Source Dataset *", list(options.keys()), key="new_src")
        with col2:
            cron_expression = st.text_input("Cron Expression", value="*/5 * * * *")
            target_label    = st.selectbox("Target Dataset *", list(options.keys()), key="new_tgt")

        src_row = options[source_label]
        tgt_row = options[target_label]
        suggested   = derive_mode(src_row.storage_type, tgt_row.storage_type)
        mode_opts   = ["db_to_db", "db_to_storage", "storage_to_db", "storage_to_storage"]
        pipeline_mode = st.selectbox("Pipeline Mode (auto-detected — override if needed)",
                                     mode_opts,
                                     index=mode_opts.index(suggested)
                                     if suggested in mode_opts else 0)

        create_clicked = st.button("Create Pipeline", type="primary")
        st.markdown('</div>', unsafe_allow_html=True)

        if create_clicked:
            if not pipeline_name.strip():
                st.error("Pipeline Name is required.")
            elif src_row.dataset_id == tgt_row.dataset_id:
                st.error("Source and target dataset must be different.")
            else:
                existing = run_query(
                    "SELECT 1 FROM pipeline_master WHERE pipeline_name = :n",
                    {"n": pipeline_name.strip()}
                )
                if not existing.empty:
                    st.error(f"A pipeline named '{pipeline_name}' already exists.")
                else:
                    try:
                        create_pipeline(
                            pipeline_name=pipeline_name.strip(),
                            cron_expression=cron_expression.strip(),
                            pipeline_mode=pipeline_mode,
                            source_dataset_id=int(src_row.dataset_id),
                            target_dataset_id=int(tgt_row.dataset_id),
                        )
                        log_action("pipeline.create",
                                   target=f"pipeline_name={pipeline_name.strip()}",
                                   details=(f"mode={pipeline_mode}, "
                                            f"source={src_row.dataset_name}, "
                                            f"target={tgt_row.dataset_name}"))
                        st.success(f"Pipeline '{pipeline_name}' created successfully.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed to create pipeline: {e}")

st.markdown('</div>', unsafe_allow_html=True)
st.markdown(
    f'<div style="font-size:12px;color:{COLOR_TEXT_MUTED};'
    f'border-top:1px solid #E8ECF4;padding:14px 3rem;">'
    f'UDIF Monitoring Portal · Pipeline Management</div>',
    unsafe_allow_html=True,
)