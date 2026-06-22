# import streamlit as st
# import pandas as pd
# import os
# from dotenv import load_dotenv
# from extractor import extract_data
# from uploader import upload_to_s3

# # ── Load .env for AWS/S3 credentials ─────────────────────────────
# load_dotenv()

# # ── Page config ───────────────────────────────────────────────────
# st.set_page_config(
#     page_title="DB → S3 Pipeline",
#     page_icon="🛢️",
#     layout="wide",
#     initial_sidebar_state="expanded",
# )

# # ── Custom CSS ────────────────────────────────────────────────────
# st.markdown("""
# <style>
#     @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700&family=Inter:wght@300;400;500;600&display=swap');

#     /* Global */
#     html, body, [class*="css"] {
#         font-family: 'Inter', sans-serif;
#     }

#     /* Background */
#     .stApp {
#         background-color: #0d1117;
#         color: #e6edf3;
#     }

#     /* Sidebar */
#     [data-testid="stSidebar"] {
#         background-color: #161b22;
#         border-right: 1px solid #30363d;
#     }
#     [data-testid="stSidebar"] * {
#         color: #e6edf3 !important;
#     }

#     /* Title */
#     .pipeline-title {
#         font-family: 'JetBrains Mono', monospace;
#         font-size: 2rem;
#         font-weight: 700;
#         color: #58a6ff;
#         letter-spacing: -0.5px;
#         margin-bottom: 0;
#     }
#     .pipeline-subtitle {
#         font-size: 0.9rem;
#         color: #8b949e;
#         margin-top: 4px;
#         margin-bottom: 2rem;
#     }

#     /* Cards */
#     .card {
#         background: #161b22;
#         border: 1px solid #30363d;
#         border-radius: 10px;
#         padding: 1.5rem;
#         margin-bottom: 1rem;
#     }
#     .card-title {
#         font-family: 'JetBrains Mono', monospace;
#         font-size: 0.75rem;
#         font-weight: 600;
#         color: #58a6ff;
#         text-transform: uppercase;
#         letter-spacing: 1.5px;
#         margin-bottom: 1rem;
#     }

#     /* Metric cards */
#     .metric-row {
#         display: flex;
#         gap: 1rem;
#         margin-bottom: 1.5rem;
#     }
#     .metric-card {
#         flex: 1;
#         background: #161b22;
#         border: 1px solid #30363d;
#         border-radius: 8px;
#         padding: 1rem 1.25rem;
#         text-align: center;
#     }
#     .metric-value {
#         font-family: 'JetBrains Mono', monospace;
#         font-size: 1.8rem;
#         font-weight: 700;
#         color: #58a6ff;
#     }
#     .metric-label {
#         font-size: 0.75rem;
#         color: #8b949e;
#         margin-top: 2px;
#         text-transform: uppercase;
#         letter-spacing: 1px;
#     }

#     /* Status badges */
#     .badge {
#         display: inline-block;
#         padding: 2px 10px;
#         border-radius: 20px;
#         font-size: 0.75rem;
#         font-weight: 600;
#         font-family: 'JetBrains Mono', monospace;
#     }
#     .badge-success { background: #1a4731; color: #3fb950; border: 1px solid #3fb950; }
#     .badge-error   { background: #4d1a1a; color: #f85149; border: 1px solid #f85149; }
#     .badge-info    { background: #1a3a5c; color: #58a6ff; border: 1px solid #58a6ff; }

#     /* Inputs */
#     .stTextInput input, .stSelectbox select, .stTextArea textarea {
#         background-color: #0d1117 !important;
#         border: 1px solid #30363d !important;
#         color: #e6edf3 !important;
#         border-radius: 6px !important;
#         font-family: 'JetBrains Mono', monospace !important;
#         font-size: 0.85rem !important;
#     }
#     .stTextInput input:focus, .stTextArea textarea:focus {
#         border-color: #58a6ff !important;
#         box-shadow: 0 0 0 2px rgba(88,166,255,0.15) !important;
#     }

#     /* Buttons */
#     .stButton > button {
#         background: #238636 !important;
#         color: #ffffff !important;
#         border: 1px solid #2ea043 !important;
#         border-radius: 6px !important;
#         font-family: 'JetBrains Mono', monospace !important;
#         font-size: 0.85rem !important;
#         font-weight: 600 !important;
#         padding: 0.5rem 1.5rem !important;
#         width: 100%;
#         transition: all 0.2s ease !important;
#     }
#     .stButton > button:hover {
#         background: #2ea043 !important;
#         border-color: #3fb950 !important;
#         transform: translateY(-1px) !important;
#     }

#     /* Dataframe */
#     .stDataFrame {
#         border: 1px solid #30363d;
#         border-radius: 8px;
#         overflow: hidden;
#     }

#     /* Log box */
#     .log-box {
#         background: #0d1117;
#         border: 1px solid #30363d;
#         border-radius: 8px;
#         padding: 1rem;
#         font-family: 'JetBrains Mono', monospace;
#         font-size: 0.8rem;
#         color: #3fb950;
#         max-height: 200px;
#         overflow-y: auto;
#     }

#     /* Divider */
#     hr { border-color: #30363d; }

#     /* Hide streamlit branding */
#     #MainMenu, footer, header { visibility: hidden; }

#     /* Force sidebar always visible */
#     [data-testid="stSidebar"] {
#         transform: none !important;
#         min-width: 320px !important;
#         max-width: 320px !important;
#         visibility: visible !important;
#         display: block !important;
#     }
#     [data-testid="stSidebarCollapsedControl"] {
#         display: none !important;
#     }

#     /* Labels */
#     label, .stSelectbox label {
#         color: #8b949e !important;
#         font-size: 0.8rem !important;
#         font-weight: 500 !important;
#         text-transform: uppercase !important;
#         letter-spacing: 0.8px !important;
#     }
# </style>
# """, unsafe_allow_html=True)


# # ── Header ────────────────────────────────────────────────────────
# st.markdown('<p class="pipeline-title">🛢️ DB → S3 Pipeline</p>', unsafe_allow_html=True)
# st.markdown('<p class="pipeline-subtitle">Extract data from any database and upload to AWS S3</p>', unsafe_allow_html=True)
# st.markdown("---")

# # ── Layout: Sidebar = config, Main = results ──────────────────────
# with st.sidebar:
#     st.markdown("### ⚙️ Configuration")
#     st.markdown("---")

#     # ── DB Credentials ────────────────────────────────────────────
#     st.markdown("**🗄️ Database**")

#     db_type = st.selectbox(
#         "Database Type",
#         options=["postgres", "mysql", "mssql"],
#         format_func=lambda x: {
#             "postgres": "🐘 PostgreSQL",
#             "mysql":    "🐬 MySQL",
#             "mssql":    "🪟 SQL Server"
#         }[x]
#     )

#     default_ports = {"postgres": "5432", "mysql": "3306", "mssql": "1433"}

#     col1, col2 = st.columns([2, 1])
#     with col1:
#         host = st.text_input("Host", value="localhost", placeholder="localhost")
#     with col2:
#         port = st.text_input("Port", value=default_ports[db_type])

#     database = st.text_input("Database Name", placeholder="e.g. company")
#     username = st.text_input("Username", placeholder="e.g. postgres")
#     password = st.text_input("Password", type="password", placeholder="••••••••")

#     st.markdown("---")

#     # ── Table + Query ──────────────────────────────────────────────
#     st.markdown("**📝 Query**")

#     # Fetch tables button
#     fetch_clicked = st.button("🔍 Fetch Tables", use_container_width=True)
#     if fetch_clicked:
#         if not all([host, port, database, username, password]):
#             st.warning("⚠️ Fill in all DB credentials first.")
#         else:
#             try:
#                 from extractor import connect_db
#                 from sqlalchemy import inspect as sa_inspect
#                 _engine = connect_db({
#                     "db_type": db_type, "host": host, "port": port,
#                     "database": database, "username": username, "password": password
#                 })
#                 _inspector = sa_inspect(_engine)
#                 tables = _inspector.get_table_names()
#                 _engine.dispose()
#                 st.session_state["tables"] = tables
#             except Exception as e:
#                 st.error(f"❌ {e}")

#     # Table dropdown (shown after fetch)
#     tables = st.session_state.get("tables", [])
#     selected_table = None
#     if tables:
#         selected_table = st.selectbox("Select Table", options=tables)

#     # Auto-generate default query from selected table, but let user edit
#     default_query = f"SELECT * FROM {selected_table}" if selected_table else "SELECT * FROM employees"
#     query = st.text_area("SQL Query", value=default_query, height=100)

#     st.markdown("---")

#     # ── Output Format ─────────────────────────────────────────────
#     st.markdown("**📦 Output Format**")
#     fmt = st.radio(
#         "Format",
#         options=["csv", "json"],
#         format_func=lambda x: "📄 CSV" if x == "csv" else "📋 JSON",
#         horizontal=True
#     )

#     st.markdown("---")

#     # ── S3 Config ─────────────────────────────────────────────────
#     st.markdown("**☁️ S3 Destination**")
#     s3_bucket = st.text_input("Bucket", value=os.getenv("S3_BUCKET", ""), placeholder="my-bucket")
#     s3_key    = st.text_input("File Key", value=os.getenv("S3_KEY", "output.csv"), placeholder="output.csv")

#     st.markdown("---")

#     # ── Run Button ────────────────────────────────────────────────
#     run = st.button("▶ Run Pipeline", use_container_width=True)


# # ── Main Panel ────────────────────────────────────────────────────
# if "result_df"    not in st.session_state: st.session_state.result_df    = None
# if "logs"         not in st.session_state: st.session_state.logs         = []
# if "upload_status" not in st.session_state: st.session_state.upload_status = None

# def add_log(msg: str, level: str = "INFO"):
#     icon = {"INFO": "ℹ️", "SUCCESS": "✅", "ERROR": "❌", "WARN": "⚠️"}.get(level, "ℹ️")
#     st.session_state.logs.append(f"{icon}  {msg}")


# if run:
#     # Reset state
#     st.session_state.result_df     = None
#     st.session_state.logs          = []
#     st.session_state.upload_status = None

#     # Validate inputs
#     if not all([host, port, database, username, password, query, s3_bucket, s3_key]):
#         st.error("❌ Please fill in all fields before running.")
#     else:
#         config = {
#             "db_type" : db_type,
#             "host"    : host,
#             "port"    : port,
#             "database": database,
#             "username": username,
#             "password": password,
#         }

#         # ── Extract ───────────────────────────────────────────────
#         with st.spinner(f"Connecting to {db_type.upper()}..."):
#             try:
#                 add_log(f"Connecting to {db_type.upper()} at {host}:{port}/{database}")
#                 df = extract_data(config, query)
#                 st.session_state.result_df = df
#                 add_log(f"Extracted {len(df)} rows × {len(df.columns)} columns", "SUCCESS")
#             except ValueError as e:
#                 add_log(f"Validation error: {e}", "ERROR")
#                 st.error(f"❌ {e}")
#                 st.stop()
#             except ConnectionError as e:
#                 add_log(f"Connection failed: {e}", "ERROR")
#                 st.error(f"❌ {e}")
#                 st.stop()
#             except Exception as e:
#                 add_log(f"Unexpected error: {e}", "ERROR")
#                 st.error(f"❌ {e}")
#                 st.stop()

#         # ── Upload ────────────────────────────────────────────────
#         with st.spinner("Uploading to S3..."):
#             try:
#                 add_log(f"Uploading to s3://{s3_bucket}/{s3_key} as {fmt.upper()}")
#                 upload_to_s3(st.session_state.result_df, s3_bucket, s3_key, fmt=fmt)
#                 add_log(f"Upload successful → s3://{s3_bucket}/{s3_key}", "SUCCESS")
#                 st.session_state.upload_status = "success"
#             except Exception as e:
#                 add_log(f"Upload failed: {e}", "ERROR")
#                 st.session_state.upload_status = "error"


# # ── Results Panel ─────────────────────────────────────────────────
# if st.session_state.result_df is not None:
#     df = st.session_state.result_df

#     # Metrics
#     st.markdown(f"""
#     <div class="metric-row">
#         <div class="metric-card">
#             <div class="metric-value">{len(df):,}</div>
#             <div class="metric-label">Rows Extracted</div>
#         </div>
#         <div class="metric-card">
#             <div class="metric-value">{len(df.columns)}</div>
#             <div class="metric-label">Columns</div>
#         </div>
#         <div class="metric-card">
#             <div class="metric-value">{fmt.upper()}</div>
#             <div class="metric-label">Output Format</div>
#         </div>
#         <div class="metric-card">
#             <div class="metric-value">{'✅' if st.session_state.upload_status == 'success' else '❌'}</div>
#             <div class="metric-label">S3 Upload</div>
#         </div>
#     </div>
#     """, unsafe_allow_html=True)

#     # Upload status
#     if st.session_state.upload_status == "success":
#         st.success(f"✅ Successfully uploaded to `s3://{s3_bucket}/{s3_key}`")
#     elif st.session_state.upload_status == "error":
#         st.error("❌ Upload to S3 failed. Check logs below.")

#     # Data preview
#     st.markdown("#### 📊 Data Preview")
#     st.dataframe(df, use_container_width=True, height=400)

#     # Download button
#     col1, col2 = st.columns(2)
#     with col1:
#         csv_data = df.to_csv(index=False).encode("utf-8")
#         st.download_button("⬇️ Download CSV", csv_data, "output.csv", "text/csv", use_container_width=True)
#     with col2:
#         json_data = df.to_json(orient="records", indent=2).encode("utf-8")
#         st.download_button("⬇️ Download JSON", json_data, "output.json", "application/json", use_container_width=True)

# else:
#     # Empty state
#     st.markdown("""
#     <div style="text-align:center; padding: 5rem 2rem; color: #8b949e;">
#         <div style="font-size: 3rem; margin-bottom: 1rem;">🛢️</div>
#         <div style="font-family: 'JetBrains Mono', monospace; font-size: 1rem; color: #58a6ff;">
#             Ready to extract
#         </div>
#         <div style="font-size: 0.85rem; margin-top: 0.5rem;">
#             Configure your database credentials in the sidebar and click <strong>Run Pipeline</strong>
#         </div>
#     </div>
#     """, unsafe_allow_html=True)

# # ── Logs ──────────────────────────────────────────────────────────
# if st.session_state.logs:
#     st.markdown("#### 🖥️ Pipeline Logs")
#     log_html = "<br>".join(st.session_state.logs)
#     st.markdown(f'<div class="log-box">{log_html}</div>', unsafe_allow_html=True)


# import streamlit as st
# import yaml
# from extractor import extract_data
# from uploader import upload_to_s3
# from retry import retry
# from logger import setup_logger

# # ── Logger ─────────────────────────────
# logger = setup_logger("app")

# # ── Load YAML ──────────────────────────
# def load_config():
#     with open("src/config.yaml") as f:
#         return yaml.safe_load(f)

# config_yaml = load_config()

# # ── Page Config ────────────────────────
# st.set_page_config(
#     page_title="DB → S3 Pipeline",
#     page_icon="🛢️",
#     layout="wide"
# )

# # ── Custom Dark Theme ──────────────────
# st.markdown("""
# <style>
# .stApp {
#     background-color: #0d1117;
#     color: #e6edf3;
# }

# [data-testid="stSidebar"] {
#     background-color: #161b22;
# }

# h1, h2, h3 {
#     color: #58a6ff;
# }
            

# .stTextInput input, .stSelectbox select, .stTextArea textarea {
#     background-color: #0d1117 !important;
#     color: #e6edf3 !important;
#     border: 1px solid #30363d !important;
#     border-radius: 6px !important;
# }

# .stButton > button {
#     background-color: #238636 !important;
#     color: white !important;
#     border-radius: 6px !important;
#     font-weight: 600;
# }

# .stButton > button:hover {
#     background-color: #2ea043 !important;
# }
# </style>
# """, unsafe_allow_html=True)

# # ── Header ─────────────────────────────
# st.markdown("## 🛢️ DB → S3 Pipeline")
# st.caption("Extract data from any database and upload to AWS S3")

# # ── Sidebar ────────────────────────────
# with st.sidebar:
#     st.header("⚙️ Configuration")

#     # DB Type
#     db_type = st.selectbox(
#         "Database Type",
#         ["postgres", "mysql", "mssql", "oracle"]
#     )

#     db_defaults = config_yaml.get(db_type, {})

#     # DB Inputs
#     host = st.text_input("Host", db_defaults.get("host", "localhost"))
#     port = st.text_input("Port", str(db_defaults.get("port", "")))
#     database = st.text_input("Database", db_defaults.get("name", ""))
#     username = st.text_input("Username", db_defaults.get("user", ""))
#     password = st.text_input("Password", type="password")

#     # Query
#     query = st.text_area(
#         "SQL Query",
#         db_defaults.get("query", "SELECT * FROM employees"),
#         height=120
#     )

#     # S3
#     s3_defaults = config_yaml.get("s3", {})
#     bucket = st.text_input("S3 Bucket", s3_defaults.get("bucket", ""))
#     key = st.text_input("S3 Key", s3_defaults.get("key", "output.csv"))

#     # Format
#     fmt = st.radio("Format", ["csv", "json"])

#     # Run Button
#     run = st.button("▶ Run Pipeline")

# # ── Retry Wrappers ─────────────────────
# safe_extract = retry(extract_data, retries=3, delay=2)
# safe_upload = retry(upload_to_s3, retries=3, delay=2)

# # ── Main Execution ─────────────────────
# if run:
#     try:
#         config = {
#             "db_type": db_type,
#             "host": host,
#             "port": port,
#             "database": database,
#             "username": username,
#             "password": password,
#         }

#         logger.info("Starting extraction...")

#         with st.spinner("Extracting data..."):
#             df = safe_extract(config, query)

#         st.success(f"✅ Extracted {len(df)} rows")
#         st.dataframe(df, use_container_width=True)

#         logger.info("Uploading to S3...")

#         with st.spinner("Uploading to S3..."):
#             safe_upload(df, bucket, key, fmt)

#         st.success(f"✅ Uploaded to s3://{bucket}/{key}")

#     except Exception as e:
#         logger.error(f"Pipeline failed: {e}")
#         st.error(f"❌ {e}")


import streamlit as st
import yaml
from extractor import extract_data
from uploader import upload_to_s3
from retry import retry
from logger import setup_logger

# ── Logger ─────────────────────────────
logger = setup_logger("app")

# ── Load YAML ──────────────────────────
def load_config():
    with open("src/config.yaml") as f:
        return yaml.safe_load(f)

config_yaml = load_config()

# ── Page Config ────────────────────────
st.set_page_config(
    page_title="DB → S3 Pipeline",
    page_icon="🛢️",
    layout="wide"
)

# ── Custom Dark Theme ──────────────────
st.markdown("""
<style>
.stApp {
    background-color: #0d1117;
    color: #e6edf3;
}

[data-testid="stSidebar"] {
    background-color: #161b22;
}

h1, h2, h3 {
    color: #58a6ff;
}

.stTextInput input, .stSelectbox select, .stTextArea textarea {
    background-color: #0d1117 !important;
    color: #e6edf3 !important;
    border: 1px solid #30363d !important;
    border-radius: 6px !important;
}

.stButton > button {
    background-color: #238636 !important;
    color: white !important;
    border-radius: 6px !important;
    font-weight: 600;
}

.stButton > button:hover {
    background-color: #2ea043 !important;
}

/* ── Metric Cards (ADDED) ── */
.metric-row {
    display: flex; gap: 1rem; margin-bottom: 1.5rem;
}
.metric-card {
    flex: 1; background: #161b22; border: 1px solid #30363d;
    border-radius: 8px; padding: 1rem 1.25rem; text-align: center;
}
.metric-value {
    font-size: 1.8rem; font-weight: 700; color: #58a6ff;
}
.metric-label {
    font-size: 0.75rem; color: #8b949e; margin-top: 2px;
    text-transform: uppercase; letter-spacing: 1px;
}
</style>
""", unsafe_allow_html=True)

# ── Header ─────────────────────────────
st.markdown("## 🛢️ DB → S3 Pipeline")
st.caption("Extract data from any database and upload to AWS S3")

# ── Sidebar ────────────────────────────
with st.sidebar:
    st.header("⚙️ Configuration")

    # DB Type
    db_type = st.selectbox(
        "Database Type",
        ["postgres", "mysql", "mssql", "oracle"]
    )

    db_defaults = config_yaml.get(db_type, {})

    # DB Inputs
    host = st.text_input("Host", db_defaults.get("host", "localhost"))
    port = st.text_input("Port", str(db_defaults.get("port", "")))
    database = st.text_input("Database", db_defaults.get("name", ""))
    username = st.text_input("Username", db_defaults.get("user", ""))
    password = st.text_input("Password", type="password")

    # Query
    query = st.text_area(
        "SQL Query",
        db_defaults.get("query", "SELECT * FROM employees"),
        height=120
    )

    # S3
    s3_defaults = config_yaml.get("s3", {})
    bucket = st.text_input("S3 Bucket", s3_defaults.get("bucket", ""))
    key = st.text_input("S3 Key", s3_defaults.get("key", "output.csv"))

    # Format
    fmt = st.radio("Format", ["csv", "json"])

    # Run Button
    run = st.button("▶ Run Pipeline")

# ── Retry Wrappers ─────────────────────
safe_extract = retry(extract_data, retries=3, delay=2)
safe_upload = retry(upload_to_s3, retries=3, delay=2)

# ── Main Execution ─────────────────────
if run:
    try:
        config = {
            "db_type": db_type,
            "host": host,
            "port": port,
            "database": database,
            "username": username,
            "password": password,
        }

        logger.info("Starting extraction...")

        with st.spinner("Extracting data..."):
            df = safe_extract(config, query)

        logger.info("Uploading to S3...")

        with st.spinner("Uploading to S3..."):
            upload_status = "success"
            try:
                safe_upload(df, bucket, key, fmt)
            except Exception:
                upload_status = "error"
                raise

        # ── Metric Cards (ADDED) ───────────────
        st.markdown(f"""
        <div class="metric-row">
            <div class="metric-card">
                <div class="metric-value">{len(df):,}</div>
                <div class="metric-label">Rows Extracted</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{len(df.columns)}</div>
                <div class="metric-label">Columns</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{fmt.upper()}</div>
                <div class="metric-label">Output Format</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{'✅' if upload_status == 'success' else '❌'}</div>
                <div class="metric-label">S3 Upload</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.success(f"✅ Extracted {len(df)} rows")
        st.success(f"✅ Uploaded to s3://{bucket}/{key}")
        st.dataframe(df, use_container_width=True)

        # ── Download Buttons (ADDED) ───────────────
        col1, col2 = st.columns(2)
        with col1:
            st.download_button("⬇️ Download CSV",
                df.to_csv(index=False).encode("utf-8"),
                "output.csv", "text/csv", use_container_width=True)
        with col2:
            st.download_button("⬇️ Download JSON",
                df.to_json(orient="records", indent=2).encode("utf-8"),
                "output.json", "application/json", use_container_width=True)

    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        st.error(f"❌ {e}")