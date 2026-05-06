-- ============================================================
-- Migración: roles, cuentas guest, tokens y aviso legal
-- Proyecto: Amigo Imaginario Neurodivergente
-- Fecha: 2026-05-06
-- ============================================================

-- ------------------------------------------------------------
-- Nuevas columnas en users
-- Nota: SQLite no soporta IF NOT EXISTS en ADD COLUMN en todas
-- las versiones. Si una columna ya existe, omite esa línea.
-- ------------------------------------------------------------
ALTER TABLE users ADD COLUMN role TEXT NOT NULL DEFAULT 'child';
ALTER TABLE users ADD COLUMN account_type TEXT NOT NULL DEFAULT 'permanent';
ALTER TABLE users ADD COLUMN guest_type TEXT;
ALTER TABLE users ADD COLUMN guest_status TEXT NOT NULL DEFAULT 'none';
ALTER TABLE users ADD COLUMN guest_created_by INTEGER;
ALTER TABLE users ADD COLUMN guest_hours INTEGER NOT NULL DEFAULT 0;
ALTER TABLE users ADD COLUMN guest_expires_at TEXT;
ALTER TABLE users ADD COLUMN is_active INTEGER NOT NULL DEFAULT 1;
ALTER TABLE users ADD COLUMN last_login_at TEXT;

-- ------------------------------------------------------------
-- Mapear administradores antiguos a superadmin
-- ------------------------------------------------------------
UPDATE users
SET role = 'superadmin', account_type = 'permanent', guest_status = 'none'
WHERE is_admin = 1;

UPDATE users
SET role = 'child'
WHERE role IS NULL OR role = '';

UPDATE users
SET account_type = 'permanent'
WHERE account_type IS NULL OR account_type = '';

UPDATE users
SET guest_status = 'none'
WHERE account_type = 'permanent';

-- ------------------------------------------------------------
-- Wallet de tokens por usuario
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS user_token_wallets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL UNIQUE,
    daily_limit INTEGER NOT NULL DEFAULT 20,
    remaining_tokens INTEGER NOT NULL DEFAULT 20,
    used_tokens INTEGER NOT NULL DEFAULT 0,
    low_threshold INTEGER NOT NULL DEFAULT 5,
    reset_interval_hours INTEGER NOT NULL DEFAULT 24,
    last_reset_at TEXT NOT NULL,
    next_reset_at TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- ------------------------------------------------------------
-- Historial de consumo de tokens
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS token_usage_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    conversation_id INTEGER,
    module TEXT NOT NULL DEFAULT '',
    amount INTEGER NOT NULL DEFAULT 1,
    reason TEXT NOT NULL DEFAULT 'chat_message',
    remaining_after INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE SET NULL
);

-- ------------------------------------------------------------
-- Aceptación opcional del aviso legal
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS legal_notice_acceptance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL UNIQUE,
    accepted_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    notice_version TEXT NOT NULL DEFAULT '2026-05-06',
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
