import streamlit as st
from sqlalchemy import text
from db.connection import run_query, engine
from auth.rbac import require_permission, has_permission, log_action
from Theme import (
    inject_base_styles, render_sidebar, page_header, section_header,
    kpi_card, COLOR_ACCENT, COLOR_SUCCESS, COLOR_TEXT_MUTED,
)

# =====================================
# PAGE CONFIG
# =====================================
st.set_page_config(page_title="Dataset Management", page_icon="📂", layout="wide")
inject_base_styles()

require_permission("dataset.view")

with st.sidebar:
    render_sidebar()

# =====================================
# HEADER
# =====================================
page_header(
    eyebrow="Operations",
    title="Dataset Management",
    subtitle="Register and manage source datasets",
)

st.markdown('<div class="udif-body" style="padding-top:0;">', unsafe_allow_html=True)

# =====================================
# KPI SECTION
# =====================================
try:
    kpi_query = """
    SELECT
        COUNT(*) AS total_datasets,
        SUM(CASE WHEN is_active = TRUE THEN 1 ELSE 0 END) AS active_datasets
    FROM dataset_master;
    """
    kpi_df = run_query(kpi_query)
    total_datasets = kpi_df.iloc[0]["total_datasets"]
    active_datasets = kpi_df.iloc[0]["active_datasets"]
except Exception as e:
    st.error(f"Database Error: {e}")
    total_datasets = active_datasets = 0

c1, c2 = st.columns(2)
with c1:
    kpi_card("Total Datasets", f"{total_datasets}", accent=COLOR_ACCENT)
with c2:
    kpi_card("Active Datasets", f"{active_datasets}", accent=COLOR_SUCCESS)

# =====================================
# REGISTER DATASET
# =====================================
if has_permission("dataset.create"):
    section_header("Register Dataset", "Add a new source dataset", icon="＋")

    st.markdown('<div class="udif-card">', unsafe_allow_html=True)
    with st.form("dataset_form"):
        col1, col2 = st.columns(2)
        with col1:
            dataset_name = st.text_input("Dataset Name")
            dataset_type = st.selectbox(
                "Dataset Type",
                ["PostgreSQL", "MySQL", "SQL Server", "CSV", "S3"],
            )
        with col2:
            storage_type = st.selectbox(
                "Storage Type",
                ["DATABASE", "FILE", "OBJECT_STORAGE"],
            )

        # ── Default values ──
        host = ""
        port = None
        database_name = ""
        username = ""
        source_table_name = ""
        bucket_name = ""
        object_key = ""
        file_path = ""
        file_format = ""

        # ── Database config ──
        if storage_type == "DATABASE":
            st.markdown("### Database Configuration")
            db1, db2 = st.columns(2)
            with db1:
                host = st.text_input("Host")
                database_name = st.text_input("Database Name")
                source_table_name = st.text_input("Source Table Name")
            with db2:
                port = st.number_input("Port", value=5432)
                username = st.text_input("Username")

        # ── File config ──
        elif storage_type == "FILE":
            st.markdown("### File Configuration")
            file_path = st.text_input("File Path")
            file_format = st.selectbox("File Format", ["CSV", "PARQUET", "JSON"])

        # ── Object storage config ──
        elif storage_type == "OBJECT_STORAGE":
            st.markdown("### Object Storage Configuration")
            bucket_name = st.text_input("Bucket Name")
            object_key = st.text_input("Object Key")

        submitted = st.form_submit_button("Register Dataset")
    st.markdown('</div>', unsafe_allow_html=True)

    # =====================================
    # SAVE DATASET (parameterized — no string interpolation into SQL)
    # =====================================
    if submitted:
        if not dataset_name.strip():
            st.error("Dataset Name is required.")
        else:
            try:
                insert_stmt = text("""
                    INSERT INTO dataset_master
                    (
                        dataset_name, dataset_type, storage_type, host, port,
                        database_name, username, source_table_name,
                        bucket_name, object_key, file_format, file_path, is_active
                    )
                    VALUES
                    (
                        :dataset_name, :dataset_type, :storage_type, :host, :port,
                        :database_name, :username, :source_table_name,
                        :bucket_name, :object_key, :file_format, :file_path, TRUE
                    );
                """)
                params = {
                    "dataset_name": dataset_name,
                    "dataset_type": dataset_type,
                    "storage_type": storage_type,
                    "host": host,
                    "port": int(port) if port else None,
                    "database_name": database_name,
                    "username": username,
                    "source_table_name": source_table_name,
                    "bucket_name": bucket_name,
                    "object_key": object_key,
                    "file_format": file_format,
                    "file_path": file_path,
                }
                with engine.begin() as connection:
                    connection.execute(insert_stmt, params)

                log_action(
                    action="dataset.create",
                    target=f"dataset_name={dataset_name}",
                    details=f"type={dataset_type}, storage={storage_type}",
                )
                st.success("Dataset Registered Successfully")
                st.rerun()
            except Exception as e:
                st.error(f"Registration Failed: {e}")

# =====================================
# DATASET LIST
# =====================================
section_header("Registered Datasets", "All datasets currently on record", icon="◷")

try:
    dataset_query = """
    SELECT dataset_id, dataset_name, dataset_type, storage_type, is_active, created_at
    FROM dataset_master
    ORDER BY dataset_id DESC;
    """
    dataset_df = run_query(dataset_query)
    dataset_df = dataset_df.rename(columns={
        "dataset_id": "Dataset ID", "dataset_name": "Dataset Name",
        "dataset_type": "Dataset Type", "storage_type": "Storage Type",
        "is_active": "Active", "created_at": "Created At",
    })
    st.markdown(
        '<div class="udif-card-tight">'
        + dataset_df.to_html(escape=False, index=False, classes="udif-table")
        + "</div>",
        unsafe_allow_html=True,
    )
except Exception as e:
    st.error(f"Unable to load datasets: {e}")

st.markdown('</div>', unsafe_allow_html=True)

# =====================================
# FOOTER
# =====================================
st.markdown(
    f'<div style="font-size:12px;color:{COLOR_TEXT_MUTED};border-top:1px solid #E8ECF4;padding:14px 3rem;">'
    f'UDIF Monitoring Portal · Dataset Management</div>',
    unsafe_allow_html=True,
)