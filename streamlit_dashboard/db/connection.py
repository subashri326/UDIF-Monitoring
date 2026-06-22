import os

from sqlalchemy import create_engine, text
import pandas as pd
from dotenv import load_dotenv

# streamlit_dashboard shares the .env file that lives in src/, not its own.
# This resolves the path explicitly so it works no matter where Streamlit
# is launched from (streamlit run Application.py from streamlit_dashboard/,
# from JDBC/, etc.) — relying on load_dotenv()'s cwd-based discovery would
# break depending on launch directory.
_DASHBOARD_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # .../streamlit_dashboard
_PROJECT_ROOT = os.path.dirname(_DASHBOARD_DIR)                                # .../JDBC
_SHARED_ENV_PATH = os.path.join(_PROJECT_ROOT, "src", ".env")

load_dotenv(_SHARED_ENV_PATH)

DB_HOST = os.getenv("METADATA_DB_HOST")
DB_PORT = os.getenv("METADATA_DB_PORT", "5432")
DB_NAME = os.getenv("METADATA_DB_NAME")
DB_USER = os.getenv("METADATA_DB_USER")
DB_PASSWORD = os.getenv("METADATA_DB_PASSWORD")

missing = [
    name for name, val in [
        ("METADATA_DB_HOST", DB_HOST),
        ("METADATA_DB_NAME", DB_NAME),
        ("METADATA_DB_USER", DB_USER),
        ("METADATA_DB_PASSWORD", DB_PASSWORD),
    ]
    if not val
]
if missing:
    raise EnvironmentError(
        f"Missing required DB env vars: {', '.join(missing)}. "
        f"Set them in your .env file or container environment — "
        f"never hardcode credentials in source."
    )

DB_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(DB_URL, pool_pre_ping=True)


def test_connection():
    try:
        df = pd.read_sql("SELECT 1 as test", engine)
        return True, df
    except Exception as e:
        return False, str(e)


def run_query(query, params=None):
    """Read-only query. Always pass params for any user-supplied value —
    never f-string user input into `query`."""
    return pd.read_sql(text(query), engine, params=params)


def execute_query(query, params=None):
    """Write query (INSERT/UPDATE/DELETE). Always parameterized."""
    try:
        with engine.begin() as connection:
            connection.execute(text(query), params or {})
        return True, "Success"
    except Exception as e:
        return False, str(e)


def create_pipeline(pipeline_name, cron_expression, pipeline_mode, source_dataset_id, target_dataset_id):
    """
    Inserts into pipeline_master and pipeline_config in a single
    transaction so a pipeline is never left half-created (master row
    with no config, or vice versa) if something fails midway.
    Raises on failure — caller is expected to catch and show the error.
    """
    with engine.begin() as connection:
        result = connection.execute(
            text("""
                INSERT INTO pipeline_master (pipeline_name, is_active, created_at, cron_expression)
                VALUES (:pipeline_name, TRUE, NOW(), :cron_expression)
                RETURNING pipeline_id
            """),
            {"pipeline_name": pipeline_name, "cron_expression": cron_expression},
        )
        new_pipeline_id = result.scalar_one()

        connection.execute(
            text("""
                INSERT INTO pipeline_config (pipeline_id, pipeline_mode, created_at, source_dataset_id, target_dataset_id)
                VALUES (:pipeline_id, :pipeline_mode, NOW(), :source_dataset_id, :target_dataset_id)
            """),
            {
                "pipeline_id": new_pipeline_id,
                "pipeline_mode": pipeline_mode,
                "source_dataset_id": source_dataset_id,
                "target_dataset_id": target_dataset_id,
            },
        )

    return new_pipeline_id