"""
Seed the first Admin user.

Run once, after applying migrations/001_auth_and_rbac.sql:

    python migrations/seed_admin.py

The password is bcrypt-hashed before it touches the database — never
stored or printed in plaintext anywhere except this one-time console
output, which you should rotate immediately via the UI on first login
(must_change_password is set to TRUE, so the app will force this).
"""
import os
import sys
import getpass

import bcrypt
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Reuse the same shared .env as the rest of the dashboard (lives in
# JDBC/src/.env, not streamlit_dashboard/) — same path resolution as
# db/connection.py and migrations/run_migration.py.
_DASHBOARD_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # streamlit_dashboard/
_PROJECT_ROOT = os.path.dirname(_DASHBOARD_DIR)                                # JDBC/
_SHARED_ENV_PATH = os.path.join(_PROJECT_ROOT, "src", ".env")
load_dotenv(_SHARED_ENV_PATH)

DB_HOST = os.getenv("METADATA_DB_HOST", "localhost")
DB_PORT = os.getenv("METADATA_DB_PORT", "5432")
DB_NAME = os.getenv("METADATA_DB_NAME", "metadata_db")
DB_USER = os.getenv("METADATA_DB_USER")
DB_PASSWORD = os.getenv("METADATA_DB_PASSWORD")

if not DB_USER or not DB_PASSWORD:
    print(f"ERROR: METADATA_DB_USER / METADATA_DB_PASSWORD not found.")
    print(f"  Looked for them in: {_SHARED_ENV_PATH}")
    print(f"  Check that file exists and has those variables set.")
    sys.exit(1)

DB_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(DB_URL)


def main():
    username = input("Admin username [admin]: ").strip() or "admin"
    full_name = input("Full name [System Administrator]: ").strip() or "System Administrator"

    default_password = "ChangeMe@123"
    use_default = input(
        f"Use generated default password '{default_password}'? [Y/n]: "
    ).strip().lower()

    if use_default in ("", "y", "yes"):
        password = default_password
    else:
        password = getpass.getpass("Enter password: ")
        confirm = getpass.getpass("Confirm password: ")
        if password != confirm:
            print("Passwords did not match. Aborting.")
            sys.exit(1)

    password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    with engine.begin() as conn:
        role_row = conn.execute(
            text("SELECT role_id FROM roles WHERE role_name = 'Admin'")
        ).fetchone()

        if not role_row:
            print("ERROR: 'Admin' role not found. Run migrations/001_auth_and_rbac.sql first.")
            sys.exit(1)

        admin_role_id = role_row[0]

        existing = conn.execute(
            text("SELECT user_id FROM users WHERE username = :u"),
            {"u": username},
        ).fetchone()

        if existing:
            print(f"User '{username}' already exists. Aborting (no changes made).")
            sys.exit(1)

        conn.execute(
            text("""
                INSERT INTO users
                    (username, password_hash, full_name, role_id, is_active, must_change_password)
                VALUES
                    (:username, :password_hash, :full_name, :role_id, TRUE, TRUE)
            """),
            {
                "username": username,
                "password_hash": password_hash,
                "full_name": full_name,
                "role_id": admin_role_id,
            },
        )

    print("\n✓ Admin user created.")
    print(f"  username: {username}")
    print(f"  password: {password}  (you will be forced to change this on first login)")
    print("  Store this somewhere safe and rotate it immediately after first login.\n")


if __name__ == "__main__":
    main()