"""
Authentication for the UDIF UI.

Session state holds the logged-in user's identity and permission set
for the duration of the browser session. Nothing sensitive (password,
hash) is ever put into st.session_state — only user_id, username,
full_name, role_name, and the resolved list of permission keys.
"""
import bcrypt
import streamlit as st

from db.connection import run_query, execute_query
from db.queries import (
    GET_USER_BY_USERNAME,
    GET_PERMISSIONS_FOR_ROLE,
    UPDATE_LAST_LOGIN,
    UPDATE_PASSWORD,
)


def _hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def _verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except (ValueError, TypeError):
        return False


def attempt_login(username: str, password: str):
    """Returns (success: bool, message: str)."""
    df = run_query(GET_USER_BY_USERNAME, {"username": username})

    if df.empty:
        return False, "Invalid username or password."

    row = df.iloc[0]

    if not row["is_active"]:
        return False, "This account has been deactivated. Contact an administrator."

    if not _verify_password(password, row["password_hash"]):
        return False, "Invalid username or password."

    perms_df = run_query(GET_PERMISSIONS_FOR_ROLE, {"role_id": int(row["role_id"])})
    permissions = set(perms_df["permission_key"].tolist())

    st.session_state["auth_user"] = {
        "user_id": int(row["user_id"]),
        "username": row["username"],
        "full_name": row["full_name"],
        "role_name": row["role_name"],
        "must_change_password": bool(row["must_change_password"]),
    }
    st.session_state["auth_permissions"] = permissions

    execute_query(UPDATE_LAST_LOGIN, {"user_id": int(row["user_id"])})

    return True, "Login successful."


def change_password(new_password: str):
    user = current_user()
    if not user:
        return False, "Not logged in."

    new_hash = _hash_password(new_password)
    ok, msg = execute_query(UPDATE_PASSWORD, {"password_hash": new_hash, "user_id": user["user_id"]})
    if ok:
        st.session_state["auth_user"]["must_change_password"] = False
    return ok, msg


def logout():
    st.session_state.pop("auth_user", None)
    st.session_state.pop("auth_permissions", None)


def current_user():
    return st.session_state.get("auth_user")


def is_logged_in() -> bool:
    return current_user() is not None


def require_login():
    """Call at the top of every page. Stops rendering if not logged in."""
    if not is_logged_in():
        st.switch_page("Application.py")
        st.stop()

    user = current_user()
    if user.get("must_change_password"):
        st.warning("You must change your password before continuing.")
        _render_forced_password_change()
        st.stop()


def _render_forced_password_change():
    with st.form("forced_password_change"):
        new_pw = st.text_input("New password", type="password")
        confirm_pw = st.text_input("Confirm new password", type="password")
        submitted = st.form_submit_button("Set new password")

    if submitted:
        if len(new_pw) < 8:
            st.error("Password must be at least 8 characters.")
        elif new_pw != confirm_pw:
            st.error("Passwords do not match.")
        else:
            ok, msg = change_password(new_pw)
            if ok:
                st.success("Password updated. Please continue.")
                st.rerun()
            else:
                st.error(f"Could not update password: {msg}")