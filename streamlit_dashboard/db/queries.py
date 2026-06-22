"""
Centralized SQL for the UDIF UI.

Why this file exists: queries were previously inline and, in a few
places (Pipeline Explorer), built with f-strings against user-selected
values — which is a SQL injection risk even when the value comes from a
dropdown (defense in depth: don't rely on the UI being the only entry
point). Every query here that takes a variable uses a bound parameter.

Each function returns (sql_text, params_dict) or just executes via the
provided run_query/execute_query helpers, depending on call site needs.
"""

# ── Auth ──────────────────────────────────────────────────────────────

GET_USER_BY_USERNAME = """
    SELECT u.user_id, u.username, u.password_hash, u.full_name,
           u.is_active, u.must_change_password, r.role_id, r.role_name
    FROM users u
    JOIN roles r ON u.role_id = r.role_id
    WHERE u.username = :username
"""

GET_PERMISSIONS_FOR_ROLE = """
    SELECT p.permission_key
    FROM role_permissions rp
    JOIN permissions p ON rp.permission_id = p.permission_id
    WHERE rp.role_id = :role_id
"""

UPDATE_LAST_LOGIN = """
    UPDATE users SET last_login = NOW() WHERE user_id = :user_id
"""

UPDATE_PASSWORD = """
    UPDATE users
    SET password_hash = :password_hash, must_change_password = FALSE
    WHERE user_id = :user_id
"""

# ── Users (admin management) ────────────────────────────────────────

LIST_USERS = """
    SELECT u.user_id, u.username, u.full_name, r.role_name,
           u.is_active, u.must_change_password, u.created_at, u.last_login
    FROM users u
    JOIN roles r ON u.role_id = r.role_id
    ORDER BY u.user_id
"""

LIST_ROLES = "SELECT role_id, role_name, description FROM roles ORDER BY role_id"

INSERT_USER = """
    INSERT INTO users (username, password_hash, full_name, role_id, is_active, must_change_password)
    VALUES (:username, :password_hash, :full_name, :role_id, TRUE, TRUE)
"""

SET_USER_ACTIVE = "UPDATE users SET is_active = :is_active WHERE user_id = :user_id"

SET_USER_ROLE = "UPDATE users SET role_id = :role_id WHERE user_id = :user_id"

# ── Datasets ─────────────────────────────────────────────────────────

LIST_DATASETS = """
    SELECT dataset_id, dataset_name, dataset_type, storage_type, is_active, created_at
    FROM dataset_master
    ORDER BY dataset_id DESC
"""

LIST_ACTIVE_DATASETS = """
    SELECT dataset_id, dataset_name, dataset_type, storage_type
    FROM dataset_master
    WHERE is_active = TRUE
    ORDER BY dataset_name
"""

INSERT_DATASET = """
    INSERT INTO dataset_master
        (dataset_name, dataset_type, storage_type, host, port,
         database_name, username, source_table_name,
         bucket_name, object_key, file_format, file_path, is_active)
    VALUES
        (:dataset_name, :dataset_type, :storage_type, :host, :port,
         :database_name, :username, :source_table_name,
         :bucket_name, :object_key, :file_format, :file_path, TRUE)
"""

SET_DATASET_ACTIVE = "UPDATE dataset_master SET is_active = :is_active WHERE dataset_id = :dataset_id"

# ── Pipelines ────────────────────────────────────────────────────────

LIST_PIPELINES = """
    SELECT
        pm.pipeline_id, pm.pipeline_name, pm.is_active, pm.created_at, pm.cron_expression,
        pc.pipeline_mode,
        src.dataset_name AS source_dataset, src.storage_type AS source_storage_type,
        tgt.dataset_name AS target_dataset, tgt.storage_type AS target_storage_type
    FROM pipeline_master pm
    JOIN pipeline_config pc ON pm.pipeline_id = pc.pipeline_id
    JOIN dataset_master src ON pc.source_dataset_id = src.dataset_id
    JOIN dataset_master tgt ON pc.target_dataset_id = tgt.dataset_id
    ORDER BY pm.pipeline_id DESC
"""

INSERT_PIPELINE_MASTER = """
    INSERT INTO pipeline_master (pipeline_name, is_active, created_at, cron_expression)
    VALUES (:pipeline_name, TRUE, NOW(), :cron_expression)
    RETURNING pipeline_id
"""

INSERT_PIPELINE_CONFIG = """
    INSERT INTO pipeline_config (pipeline_id, pipeline_mode, created_at, source_dataset_id, target_dataset_id)
    VALUES (:pipeline_id, :pipeline_mode, NOW(), :source_dataset_id, :target_dataset_id)
"""

SET_PIPELINE_ACTIVE = "UPDATE pipeline_master SET is_active = :is_active WHERE pipeline_id = :pipeline_id"

CHECK_PIPELINE_NAME_EXISTS = "SELECT 1 FROM pipeline_master WHERE pipeline_name = :pipeline_name"

# ── Audit ────────────────────────────────────────────────────────────

INSERT_UI_AUDIT_LOG = """
    INSERT INTO ui_audit_log (user_id, username, action, target, details)
    VALUES (:user_id, :username, :action, :target, :details)
"""

LIST_UI_AUDIT_LOG = """
    SELECT username, action, target, details, created_at
    FROM ui_audit_log
    ORDER BY created_at DESC
    LIMIT 100
"""