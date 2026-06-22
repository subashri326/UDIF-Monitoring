"""
RBAC permission checks for the UDIF UI.

Pages call `require_permission("pipeline.create")` to hard-gate an
entire page, or `has_permission("dataset.create")` to conditionally
show/hide a button or form within an otherwise-accessible page.
"""
import streamlit as st

from auth.auth import require_login


def has_permission(permission_key: str) -> bool:
    perms = st.session_state.get("auth_permissions", set())
    return permission_key in perms


def require_permission(permission_key: str):
    """Call at the top of a page after require_login(). Stops rendering
    entirely (with a clear message) if the user lacks the permission."""
    require_login()

    if not has_permission(permission_key):
        user = st.session_state.get("auth_user", {})
        st.error(
            f"🔒 You don't have access to this page.\n\n"
            f"Required permission: `{permission_key}` · "
            f"Your role: **{user.get('role_name', 'Unknown')}**\n\n"
            f"Contact an administrator if you believe this is incorrect."
        )
        st.stop()


def log_action(action: str, target: str = "", details: str = ""):
    """Write an entry to ui_audit_log. Call after any create/update/
    delete/activate action so there's a record of who did what."""
    from db.connection import execute_query
    from db.queries import INSERT_UI_AUDIT_LOG

    user = st.session_state.get("auth_user", {})
    execute_query(
        INSERT_UI_AUDIT_LOG,
        {
            "user_id": user.get("user_id"),
            "username": user.get("username", "unknown"),
            "action": action,
            "target": target,
            "details": details,
        },
    )