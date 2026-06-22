-- =====================================================================
-- UDIF — Auth & RBAC schema
-- Run this once against metadata_db (the same Postgres DB pipeline_master
-- and dataset_master already live in).
-- =====================================================================

BEGIN;

-- ---------------------------------------------------------------------
-- ROLES
-- A role is just a named bundle of permissions. Add new roles by
-- inserting a row here + rows in role_permissions — no code changes.
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS roles (
    role_id     SERIAL PRIMARY KEY,
    role_name   VARCHAR(50) UNIQUE NOT NULL,
    description VARCHAR(255),
    created_at  TIMESTAMP NOT NULL DEFAULT NOW()
);

-- ---------------------------------------------------------------------
-- PERMISSIONS
-- Fine-grained capability keys. Pages check these, not role names.
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS permissions (
    permission_id  SERIAL PRIMARY KEY,
    permission_key VARCHAR(100) UNIQUE NOT NULL,
    description    VARCHAR(255)
);

-- ---------------------------------------------------------------------
-- ROLE <-> PERMISSION (many-to-many)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS role_permissions (
    role_id       INTEGER NOT NULL REFERENCES roles(role_id) ON DELETE CASCADE,
    permission_id INTEGER NOT NULL REFERENCES permissions(permission_id) ON DELETE CASCADE,
    PRIMARY KEY (role_id, permission_id)
);

-- ---------------------------------------------------------------------
-- USERS
-- Passwords are bcrypt hashes — never plaintext. must_change_password
-- forces a reset on first login for seeded/admin-created accounts.
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    user_id              SERIAL PRIMARY KEY,
    username              VARCHAR(50) UNIQUE NOT NULL,
    password_hash         VARCHAR(255) NOT NULL,
    full_name             VARCHAR(150),
    role_id               INTEGER NOT NULL REFERENCES roles(role_id),
    is_active              BOOLEAN NOT NULL DEFAULT TRUE,
    must_change_password   BOOLEAN NOT NULL DEFAULT TRUE,
    created_at            TIMESTAMP NOT NULL DEFAULT NOW(),
    last_login            TIMESTAMP
);

-- ---------------------------------------------------------------------
-- UI AUDIT LOG
-- Tracks who-did-what in the UI itself (separate from pipeline_audit,
-- which tracks pipeline *execution* results).
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS ui_audit_log (
    log_id      SERIAL PRIMARY KEY,
    user_id     INTEGER REFERENCES users(user_id),
    username    VARCHAR(50),
    action      VARCHAR(100) NOT NULL,      -- e.g. 'dataset.create', 'pipeline.activate'
    target      VARCHAR(255),                -- e.g. 'dataset_id=12' or 'pipeline_name=foo'
    details     TEXT,
    created_at  TIMESTAMP NOT NULL DEFAULT NOW()
);

-- =====================================================================
-- SEED: baseline permissions
-- =====================================================================
INSERT INTO permissions (permission_key, description) VALUES
    ('dataset.view',         'View registered datasets'),
    ('dataset.create',       'Register a new dataset'),
    ('dataset.edit',         'Edit/deactivate an existing dataset'),
    ('pipeline.view',        'View pipelines and their config'),
    ('pipeline.create',      'Create a new pipeline'),
    ('pipeline.activate',    'Activate a pipeline (enable schedule)'),
    ('pipeline.deactivate',  'Deactivate a pipeline (disable schedule)'),
    ('analytics.view',       'View dashboard, analytics, failures, explorer'),
    ('user.manage',          'Create/edit users and assign roles'),
    ('audit.view',           'View UI audit log')
ON CONFLICT (permission_key) DO NOTHING;

-- =====================================================================
-- SEED: baseline roles
-- =====================================================================
INSERT INTO roles (role_name, description) VALUES
    ('Admin',    'Full access — manage users, datasets, pipelines'),
    ('Operator', 'Can manage datasets and activate/deactivate pipelines, no user management'),
    ('Viewer',   'Read-only access to dashboards and analytics')
ON CONFLICT (role_name) DO NOTHING;

-- Admin → every permission
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.role_id, p.permission_id
FROM roles r CROSS JOIN permissions p
WHERE r.role_name = 'Admin'
ON CONFLICT DO NOTHING;

-- Operator → everything except user.manage
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.role_id, p.permission_id
FROM roles r CROSS JOIN permissions p
WHERE r.role_name = 'Operator'
  AND p.permission_key != 'user.manage'
ON CONFLICT DO NOTHING;

-- Viewer → view-only permissions
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.role_id, p.permission_id
FROM roles r CROSS JOIN permissions p
WHERE r.role_name = 'Viewer'
  AND p.permission_key IN ('dataset.view', 'pipeline.view', 'analytics.view')
ON CONFLICT DO NOTHING;

COMMIT;

-- =====================================================================
-- NOTE: the first Admin user is NOT created here.
-- Run seed_admin.py separately — it hashes the password with bcrypt
-- properly instead of a plaintext INSERT in a SQL file.
-- =====================================================================