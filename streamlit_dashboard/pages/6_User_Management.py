import streamlit as st
import bcrypt

from db.connection import run_query, execute_query
from db.queries import LIST_USERS, LIST_ROLES, INSERT_USER, SET_USER_ACTIVE, SET_USER_ROLE
from auth.rbac import require_permission, log_action
from auth.auth import current_user
from Theme import (
    inject_base_styles, render_sidebar, page_header, section_header,
    kpi_card, COLOR_ACCENT, COLOR_SUCCESS, COLOR_DANGER, COLOR_TEXT_MUTED,
)

st.set_page_config(page_title="User Management", page_icon="👤", layout="wide")
inject_base_styles()

require_permission("user.manage")

with st.sidebar:
    render_sidebar()

page_header(
    eyebrow="Administration",
    title="User Management",
    subtitle="Create users and assign roles",
)

st.markdown('<div class="udif-body" style="padding-top:0;">', unsafe_allow_html=True)

try:
    users_df = run_query(LIST_USERS)
    roles_df = run_query(LIST_ROLES)
except Exception as e:
    st.error(f"Database Error: {e}")
    users_df, roles_df = None, None

if users_df is not None:
    c1, c2 = st.columns(2)
    with c1:
        kpi_card("Total Users", f"{len(users_df)}", accent=COLOR_ACCENT)
    with c2:
        active_count = int(users_df["is_active"].sum()) if len(users_df) else 0
        kpi_card("Active Users", f"{active_count}", accent=COLOR_SUCCESS)


# ════════════════════════════════════════════════════════════════════
# CREATE USER
# ════════════════════════════════════════════════════════════════════
section_header("Create User", "New accounts are forced to change their password on first login", icon="＋")

if roles_df is None or roles_df.empty:
    st.warning("No roles found. Run the auth migration (001_auth_and_rbac.sql) first.")
else:
    role_options = {row.role_name: row.role_id for row in roles_df.itertuples()}

    st.markdown('<div class="udif-card">', unsafe_allow_html=True)
    with st.form("create_user_form"):
        col1, col2 = st.columns(2)
        with col1:
            new_username = st.text_input("Username")
            new_full_name = st.text_input("Full Name")
        with col2:
            new_role = st.selectbox("Role", list(role_options.keys()))
            new_password = st.text_input(
                "Temporary Password", type="password",
                help="The user will be forced to change this on first login.",
            )
        submitted = st.form_submit_button("Create User", type="primary")
    st.markdown('</div>', unsafe_allow_html=True)

    if submitted:
        if not new_username.strip() or not new_password:
            st.error("Username and temporary password are required.")
        elif len(new_password) < 8:
            st.error("Temporary password must be at least 8 characters.")
        else:
            existing = run_query("SELECT 1 FROM users WHERE username = :u", {"u": new_username.strip()})
            if not existing.empty:
                st.error(f"Username '{new_username}' is already taken.")
            else:
                password_hash = bcrypt.hashpw(new_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
                ok, msg = execute_query(
                    INSERT_USER,
                    {
                        "username": new_username.strip(),
                        "password_hash": password_hash,
                        "full_name": new_full_name.strip(),
                        "role_id": role_options[new_role],
                    },
                )
                if ok:
                    log_action("user.create", target=f"username={new_username.strip()}", details=f"role={new_role}")
                    st.success(f"User '{new_username}' created with role '{new_role}'.")
                    st.rerun()
                else:
                    st.error(f"Failed to create user: {msg}")


# ════════════════════════════════════════════════════════════════════
# USER LIST + ROLE / ACTIVE TOGGLES
# ════════════════════════════════════════════════════════════════════
section_header("Users", "All accounts on record", icon="◷")

if users_df is None or users_df.empty:
    st.info("No users found.")
else:
    me = current_user()
    role_options = {row.role_name: row.role_id for row in roles_df.itertuples()} if roles_df is not None else {}

    for row in users_df.itertuples():
        st.markdown('<div class="udif-card">', unsafe_allow_html=True)
        cols = st.columns([2.5, 2, 2, 1.5, 2])

        with cols[0]:
            st.markdown(f"**{row.username}**")
            st.caption(row.full_name or "—")
        with cols[1]:
            st.caption("Role")
            st.write(row.role_name)
        with cols[2]:
            st.caption("Status")
            if row.is_active:
                st.markdown(f'<span style="color:{COLOR_SUCCESS};">● Active</span>', unsafe_allow_html=True)
            else:
                st.markdown(f'<span style="color:{COLOR_DANGER};">● Disabled</span>', unsafe_allow_html=True)
        with cols[3]:
            st.caption("Must Reset PW")
            st.write("Yes" if row.must_change_password else "No")
        with cols[4]:
            is_self = me is not None and me["username"] == row.username
            if is_self:
                st.caption("This is you")
            else:
                if row.is_active:
                    if st.button("Disable", key=f"disable_{row.user_id}"):
                        execute_query(SET_USER_ACTIVE, {"is_active": False, "user_id": int(row.user_id)})
                        log_action("user.disable", target=f"username={row.username}")
                        st.rerun()
                else:
                    if st.button("Enable", key=f"enable_{row.user_id}"):
                        execute_query(SET_USER_ACTIVE, {"is_active": True, "user_id": int(row.user_id)})
                        log_action("user.enable", target=f"username={row.username}")
                        st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

st.markdown(
    f'<div style="font-size:12px;color:{COLOR_TEXT_MUTED};border-top:1px solid #E8ECF4;padding:14px 3rem;">'
    f'UDIF Monitoring Portal · User Management</div>',
    unsafe_allow_html=True,
)