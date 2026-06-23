import streamlit as st
from sqlalchemy import text
from db.connection import run_query, engine, execute_query
from auth.rbac import require_permission, has_permission, log_action
from Theme import (
    inject_base_styles, render_sidebar, page_header, section_header,
    kpi_card, COLOR_ACCENT, COLOR_SUCCESS, COLOR_DANGER, COLOR_TEXT_MUTED,
)

st.set_page_config(page_title="Dataset Management", page_icon="", layout="wide")
inject_base_styles()
require_permission("dataset.view")

with st.sidebar:
    render_sidebar()

page_header(
    eyebrow="Operations",
    title="Dataset Management",
    subtitle="Register and manage source and target datasets",
)

st.markdown('<div class="udif-body" style="padding-top:0;">', unsafe_allow_html=True)

# ── Session state init ────────────────────────────────────────────────────────
if "ds_edit_id" not in st.session_state:
    st.session_state.ds_edit_id = None


# ── Helpers ───────────────────────────────────────────────────────────────────
def load_datasets():
    return run_query("""
        SELECT dataset_id, dataset_name, dataset_type, storage_type,
               host, port, database_name, username, source_query,
               source_table_name, bucket_name, object_key,
               file_format, file_path, recursive_scan, is_active, created_at
        FROM dataset_master ORDER BY dataset_id DESC
    """)


def load_dataset_by_id(dataset_id):
    df = run_query(
        "SELECT * FROM dataset_master WHERE dataset_id = :id",
        {"id": dataset_id}
    )
    return df.iloc[0] if not df.empty else None


# ── KPIs ──────────────────────────────────────────────────────────────────────
try:
    kpi_df = run_query("""
        SELECT COUNT(*) AS total,
               SUM(CASE WHEN is_active THEN 1 ELSE 0 END) AS active
        FROM dataset_master
    """)
    total_datasets  = kpi_df.iloc[0]["total"]
    active_datasets = kpi_df.iloc[0]["active"]
except Exception as e:
    st.error(f"Database error: {e}")
    total_datasets = active_datasets = 0

c1, c2, c3 = st.columns([1, 1, 3])
with c1: kpi_card("Total Datasets",  f"{total_datasets}",  accent=COLOR_ACCENT)
with c2: kpi_card("Active Datasets", f"{active_datasets}", accent=COLOR_SUCCESS)
with c3:
    st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)
    if st.button("View & Manage Datasets", type="secondary", use_container_width=False):
        st.session_state.show_dataset_modal = True


# ── MODAL: View / Delete ───────────────────────────────────────────────────────
@st.dialog("Registered Datasets", width="large")
def show_datasets_modal():
    try:
        df = load_datasets()
    except Exception as e:
        st.error(f"Could not load datasets: {e}")
        return

    if df.empty:
        st.info("No datasets registered yet.")
        return

    st.markdown(
        f"<div style='font-size:13px;color:{COLOR_TEXT_MUTED};"
        f"margin-bottom:12px;'>{len(df)} dataset(s) on record</div>",
        unsafe_allow_html=True,
    )

    for row in df.itertuples():
        cols = st.columns([2.5, 1.2, 1.2, 0.8, 0.8, 0.8])

        with cols[0]:
            st.markdown(f"**{row.dataset_name}**")
            detail = row.host or row.bucket_name or row.file_path or "—"
            st.caption(f"{detail}")

        with cols[1]:
            st.caption("Type")
            st.write(row.dataset_type or "—")

        with cols[2]:
            st.caption("Storage")
            st.write(row.storage_type or "—")

        with cols[3]:
            st.caption("Active")
            color = COLOR_SUCCESS if row.is_active else COLOR_DANGER
            st.markdown(
                f'<span style="color:{color};font-weight:700;">'
                f'{"Yes" if row.is_active else "No"}</span>',
                unsafe_allow_html=True,
            )

        with cols[4]:
            if st.button("Edit", key=f"modal_edit_{row.dataset_id}"):
                st.session_state.ds_edit_id = int(row.dataset_id)
                st.rerun()

        with cols[5]:
            if has_permission("dataset.edit"):
                if st.button("Delete", key=f"modal_del_{row.dataset_id}"):
                    ok, msg = execute_query(
                        "DELETE FROM dataset_master WHERE dataset_id = :id",
                        {"id": int(row.dataset_id)},
                    )
                    if ok:
                        log_action("dataset.delete", target=f"dataset_id={row.dataset_id}",
                                   details=f"name={row.dataset_name}")
                        st.success(f"Deleted '{row.dataset_name}'.")
                        st.rerun()
                    else:
                        st.error(f"Delete failed: {msg}")

        st.divider()


if st.session_state.get("show_dataset_modal"):
    st.session_state.show_dataset_modal = False
    show_datasets_modal()


# ── Inline Edit Form ───────────────────────────────────────────────────────────
if st.session_state.ds_edit_id is not None:
    edit_row = load_dataset_by_id(st.session_state.ds_edit_id)
    if edit_row is not None:
        section_header(f"Edit Dataset — {edit_row['dataset_name']}", "Update the fields below and save")

        st.markdown('<div class="udif-card">', unsafe_allow_html=True)
        with st.form("edit_dataset_form"):
            col1, col2 = st.columns(2)
            with col1:
                e_name = st.text_input("Dataset Name *", value=edit_row["dataset_name"] or "")
                e_type = st.selectbox(
                    "Dataset Type *",
                    ["postgres", "mysql", "mssql", "oracle", "s3", "local", "azure"],
                    index=["postgres", "mysql", "mssql", "oracle", "s3", "local", "azure"].index(
                        edit_row["dataset_type"].lower()
                    ) if edit_row["dataset_type"] and edit_row["dataset_type"].lower() in
                         ["postgres", "mysql", "mssql", "oracle", "s3", "local", "azure"] else 0,
                )
            with col2:
                e_storage = st.selectbox(
                    "Storage Type *",
                    ["db", "s3", "local", "azure"],
                    index=["db", "s3", "local", "azure"].index(
                        edit_row["storage_type"].lower()
                    ) if edit_row["storage_type"] and edit_row["storage_type"].lower() in
                         ["db", "s3", "local", "azure"] else 0,
                )
                e_active = st.checkbox("Active", value=bool(edit_row["is_active"]))

            # DB fields
            e_host = st.text_input("Host", value=edit_row["host"] or "")
            ec1, ec2 = st.columns(2)
            with ec1:
                e_port      = st.number_input("Port", min_value=1, max_value=65535,
                                               value=int(edit_row["port"]) if edit_row["port"] else 5432)
                e_db        = st.text_input("Database Name", value=edit_row["database_name"] or "")
                e_user      = st.text_input("Username", value=edit_row["username"] or "")
            with ec2:
                e_table     = st.text_input("Source Table Name", value=edit_row["source_table_name"] or "")
                e_bucket    = st.text_input("Bucket Name", value=edit_row["bucket_name"] or "")
                e_key       = st.text_input("Object Key / Prefix", value=edit_row["object_key"] or "")
            e_query         = st.text_area("Source Query", value=edit_row["source_query"] or "", height=80)
            ef1, ef2        = st.columns(2)
            with ef1:
                e_filepath  = st.text_input("File Path", value=edit_row["file_path"] or "")
                e_format    = st.text_input("File Format", value=edit_row["file_format"] or "")
            with ef2:
                e_recursive = st.checkbox("Recursive Scan", value=bool(edit_row["recursive_scan"]))

            save_col, cancel_col = st.columns([1, 4])
            with save_col:
                save = st.form_submit_button("Save Changes", type="primary")
            with cancel_col:
                cancel = st.form_submit_button("Cancel")

        st.markdown('</div>', unsafe_allow_html=True)

        if cancel:
            st.session_state.ds_edit_id = None
            st.rerun()

        if save:
            if not e_name.strip():
                st.error("Dataset Name is required.")
            else:
                try:
                    with engine.begin() as conn:
                        conn.execute(text("""
                            UPDATE dataset_master SET
                                dataset_name      = :dataset_name,
                                dataset_type      = :dataset_type,
                                storage_type      = :storage_type,
                                host              = :host,
                                port              = :port,
                                database_name     = :database_name,
                                username          = :username,
                                source_query      = :source_query,
                                source_table_name = :source_table_name,
                                bucket_name       = :bucket_name,
                                object_key        = :object_key,
                                file_format       = :file_format,
                                file_path         = :file_path,
                                recursive_scan    = :recursive_scan,
                                is_active         = :is_active
                            WHERE dataset_id = :dataset_id
                        """), {
                            "dataset_name":      e_name.strip(),
                            "dataset_type":      e_type,
                            "storage_type":      e_storage,
                            "host":              e_host or None,
                            "port":              int(e_port) if e_port else None,
                            "database_name":     e_db or None,
                            "username":          e_user or None,
                            "source_query":      e_query or None,
                            "source_table_name": e_table or None,
                            "bucket_name":       e_bucket or None,
                            "object_key":        e_key or None,
                            "file_format":       e_format or None,
                            "file_path":         e_filepath or None,
                            "recursive_scan":    e_recursive,
                            "is_active":         e_active,
                            "dataset_id":        st.session_state.ds_edit_id,
                        })
                    log_action("dataset.edit", target=f"dataset_id={st.session_state.ds_edit_id}",
                               details=f"name={e_name.strip()}")
                    st.success("Dataset updated successfully.")
                    st.session_state.ds_edit_id = None
                    st.rerun()
                except Exception as e:
                    st.error(f"Update failed: {e}")


# ── Register Dataset ───────────────────────────────────────────────────────────
if has_permission("dataset.create") and st.session_state.ds_edit_id is None:
    section_header("Register Dataset", "Add a new dataset to the registry")

    st.markdown('<div class="udif-card">', unsafe_allow_html=True)
    with st.form("dataset_form"):
        col1, col2 = st.columns(2)
        with col1:
            dataset_name = st.text_input("Dataset Name *")
            dataset_type = st.selectbox("Dataset Type *",
                ["postgres", "mysql", "mssql", "oracle", "s3", "local", "azure"])
        with col2:
            storage_type = st.selectbox("Storage Type *", ["db", "s3", "local", "azure"],
                help="db = relational database · s3 = AWS S3 · local = local filesystem")
            is_active = st.checkbox("Active", value=True)

        host = port = database_name = username = None
        source_query = source_table_name = None
        bucket_name = object_key = file_format = file_path = None
        recursive_scan = False

        if storage_type == "db":
            st.markdown("#### Database Configuration")
            db1, db2 = st.columns(2)
            with db1:
                host          = st.text_input("Host")
                database_name = st.text_input("Database Name")
                username      = st.text_input("Username")
            with db2:
                port              = st.number_input("Port", min_value=1, max_value=65535, value=5432)
                source_table_name = st.text_input("Source Table Name")
                source_query      = st.text_area("Source Query (optional)", height=80,
                                                  placeholder="SELECT * FROM table_name")
        elif storage_type == "s3":
            st.markdown("#### S3 Configuration")
            s1, s2 = st.columns(2)
            with s1:
                bucket_name = st.text_input("Bucket Name")
                object_key  = st.text_input("Object Key / Prefix")
            with s2:
                file_format    = st.selectbox("File Format", ["csv", "json", "parquet", "txt", "xml"])
                recursive_scan = st.checkbox("Recursive Scan")
        elif storage_type == "local":
            st.markdown("#### Local Filesystem Configuration")
            l1, l2 = st.columns(2)
            with l1:
                file_path = st.text_input("File Path", placeholder="/opt/airflow/udif-input")
            with l2:
                file_format    = st.selectbox("File Format", ["csv", "json", "parquet", "txt", "xml"])
                recursive_scan = st.checkbox("Recursive Scan")

        submitted = st.form_submit_button("Register Dataset", type="primary")
    st.markdown('</div>', unsafe_allow_html=True)

    if submitted:
        if not dataset_name.strip():
            st.error("Dataset Name is required.")
        else:
            try:
                with engine.begin() as conn:
                    conn.execute(text("""
                        INSERT INTO dataset_master (
                            dataset_name, dataset_type, storage_type,
                            host, port, database_name, username,
                            source_query, source_table_name,
                            bucket_name, object_key, recursive_scan,
                            file_format, file_path, is_active
                        ) VALUES (
                            :dataset_name, :dataset_type, :storage_type,
                            :host, :port, :database_name, :username,
                            :source_query, :source_table_name,
                            :bucket_name, :object_key, :recursive_scan,
                            :file_format, :file_path, :is_active
                        )
                    """), {
                        "dataset_name":      dataset_name.strip(),
                        "dataset_type":      dataset_type,
                        "storage_type":      storage_type,
                        "host":              host or None,
                        "port":              int(port) if port else None,
                        "database_name":     database_name or None,
                        "username":          username or None,
                        "source_query":      source_query or None,
                        "source_table_name": source_table_name or None,
                        "bucket_name":       bucket_name or None,
                        "object_key":        object_key or None,
                        "recursive_scan":    recursive_scan,
                        "file_format":       file_format or None,
                        "file_path":         file_path or None,
                        "is_active":         is_active,
                    })
                log_action("dataset.create", target=f"dataset_name={dataset_name.strip()}",
                           details=f"type={dataset_type}, storage={storage_type}")
                st.success(f"Dataset '{dataset_name}' registered successfully.")
                st.rerun()
            except Exception as e:
                st.error(f"Failed to register dataset: {e}")

st.markdown('</div>', unsafe_allow_html=True)
st.markdown(
    f'<div style="font-size:12px;color:{COLOR_TEXT_MUTED};'
    f'border-top:1px solid #E8ECF4;padding:14px 3rem;">'
    f'UDIF Monitoring Portal · Dataset Management</div>',
    unsafe_allow_html=True,
)