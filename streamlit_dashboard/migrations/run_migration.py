"""
Runs migrations/001_auth_and_rbac.sql against metadata_db without
needing the psql CLI installed.

Usage (from streamlit_dashboard/):
    python migrations/run_migration.py
"""
import os
import sys

from sqlalchemy import create_engine, text

# Reuse the same shared .env as the rest of the dashboard.
_DASHBOARD_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # streamlit_dashboard/
_PROJECT_ROOT = os.path.dirname(_DASHBOARD_DIR)                                # JDBC/
_SHARED_ENV_PATH = os.path.join(_PROJECT_ROOT, "src", ".env")

from dotenv import load_dotenv
load_dotenv(_SHARED_ENV_PATH)

DB_HOST = os.getenv("METADATA_DB_HOST")
DB_PORT = os.getenv("METADATA_DB_PORT", "5432")
DB_NAME = os.getenv("METADATA_DB_NAME")
DB_USER = os.getenv("METADATA_DB_USER")
DB_PASSWORD = os.getenv("METADATA_DB_PASSWORD")

missing = [n for n, v in [
    ("METADATA_DB_HOST", DB_HOST), ("METADATA_DB_NAME", DB_NAME),
    ("METADATA_DB_USER", DB_USER), ("METADATA_DB_PASSWORD", DB_PASSWORD),
] if not v]
if missing:
    print(f"ERROR: missing env vars in {_SHARED_ENV_PATH}: {', '.join(missing)}")
    sys.exit(1)

DB_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(DB_URL)

SQL_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "001_auth_and_rbac.sql")


def main():
    print(f"Connecting to {DB_HOST}:{DB_PORT}/{DB_NAME} as {DB_USER} ...")

    with open(SQL_FILE, "r", encoding="utf-8") as f:
        sql_script = f.read()

    # The migration file already wraps everything in BEGIN...COMMIT,
    # so run it as one executescript-style call via a raw connection
    # (SQLAlchemy's text() + execute doesn't split multi-statement
    # scripts the way psql does, so we use the underlying DBAPI cursor).
    raw_conn = engine.raw_connection()
    try:
        cur = raw_conn.cursor()
        cur.execute(sql_script)
        raw_conn.commit()
        cur.close()
        print("✓ Migration applied successfully.")
        print("  Created/verified: roles, permissions, role_permissions, users, ui_audit_log")
        print("  Seeded roles: Admin, Operator, Viewer")
    except Exception as e:
        raw_conn.rollback()
        print(f"ERROR: migration failed, rolled back. {e}")
        sys.exit(1)
    finally:
        raw_conn.close()


if __name__ == "__main__":
    main()