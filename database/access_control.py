# ============================================================
# database/access_control.py
# Control centralizado para:
# - roles y permisos
# - cuentas guest temporales
# - tokens / créditos de uso
# - validaciones reutilizables para FastAPI y Streamlit
# ============================================================

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import os
import sqlite3
from typing import Any

from config import DATABASE_PATH


# ------------------------------------------------------------
# Constantes de roles
# ------------------------------------------------------------
ROLE_SUPERADMIN = "superadmin"
ROLE_PARENT_ADMIN = "parent_admin"
ROLE_CHILD = "child"
ROLE_GUEST_CHILD = "guest_child"
ROLE_GUEST_PARENT = "guest_parent"

VALID_ROLES = {
    ROLE_SUPERADMIN,
    ROLE_PARENT_ADMIN,
    ROLE_CHILD,
    ROLE_GUEST_CHILD,
    ROLE_GUEST_PARENT,
}

ROLE_LABELS = {
    ROLE_SUPERADMIN: "Superadmin",
    ROLE_PARENT_ADMIN: "Admin padre",
    ROLE_CHILD: "Usuario niño",
    ROLE_GUEST_CHILD: "Guest niño",
    ROLE_GUEST_PARENT: "Guest padre",
}

ACCOUNT_TYPE_PERMANENT = "permanent"
ACCOUNT_TYPE_GUEST = "guest"

GUEST_STATUS_NONE = "none"
GUEST_STATUS_ACTIVE = "active"
GUEST_STATUS_INACTIVE = "inactive"
GUEST_STATUS_EXPIRED = "expired"

DEFAULT_TOKEN_LIMIT = 20
DEFAULT_GUEST_TOKEN_LIMIT = 10
DEFAULT_TOKEN_RESET_INTERVAL_HOURS = 24
DEFAULT_LOW_TOKEN_THRESHOLD = 5

LEGAL_NOTICE_TEXT = (
    "Aviso de uso: esta plataforma es una herramienta digital de apoyo, "
    "orientación general y acompañamiento guiado. No realiza diagnósticos, "
    "no ofrece tratamiento psicológico, médico ni terapéutico, y no sustituye "
    "la atención o seguimiento de profesionales de la salud, educación o terapia."
)

NO_TOKENS_MESSAGE = (
    "Por ahora ya no tienes tokens disponibles para enviar más mensajes. "
    "Tus tokens se reiniciarán automáticamente en {reset_text}. Mientras esperas, "
    "puedes hacer una pausa, respirar con calma, escribir en una libreta cómo te sientes, "
    "leer una actividad guardada o probar una dinámica offline tranquila."
)

LOW_TOKENS_MESSAGE = "Te quedan pocos tokens disponibles. Úsalos con calma para lo más importante."


# ------------------------------------------------------------
# Conexión local a SQLite
# ------------------------------------------------------------
def get_connection() -> sqlite3.Connection:
    """
    Crea una conexión a SQLite sin depender de chat_db.py para evitar ciclos.
    """
    carpeta_db = os.path.dirname(DATABASE_PATH)

    if carpeta_db:
        os.makedirs(carpeta_db, exist_ok=True)

    connection = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON;")
    return connection


# ------------------------------------------------------------
# Utilidades de fecha UTC
# ------------------------------------------------------------
def utc_now() -> datetime:
    """
    Devuelve la fecha actual en UTC sin microsegundos.
    """
    return datetime.now(timezone.utc).replace(microsecond=0)


def to_iso(value: datetime) -> str:
    """
    Convierte datetime a texto ISO compatible con SQLite.
    """
    return value.astimezone(timezone.utc).replace(microsecond=0).isoformat()


def parse_datetime(value: str | None) -> datetime | None:
    """
    Convierte fechas guardadas como texto a datetime UTC.
    """
    if not value:
        return None

    text = str(value).strip()

    try:
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"

        parsed = datetime.fromisoformat(text)

        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)

        return parsed.astimezone(timezone.utc)
    except Exception:
        try:
            parsed = datetime.strptime(text, "%Y-%m-%d %H:%M:%S")
            return parsed.replace(tzinfo=timezone.utc)
        except Exception:
            return None


# ------------------------------------------------------------
# Migraciones seguras
# ------------------------------------------------------------
def column_exists(cursor: sqlite3.Cursor, table_name: str, column_name: str) -> bool:
    """
    Verifica si una columna existe en una tabla.
    """
    cursor.execute(f"PRAGMA table_info({table_name});")
    rows = cursor.fetchall()
    return any(row["name"] == column_name for row in rows)


def add_column_if_missing(
    cursor: sqlite3.Cursor,
    table_name: str,
    column_name: str,
    definition: str,
) -> None:
    """
    Agrega una columna solo si no existe.
    """
    if not column_exists(cursor, table_name, column_name):
        cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {definition};")


def initialize_access_control_schema() -> None:
    """
    Aplica la migración de roles, guests y tokens sin romper datos existentes.
    """
    connection = get_connection()
    cursor = connection.cursor()

    # --------------------------------------------------------
    # Columnas nuevas en users
    # --------------------------------------------------------
    add_column_if_missing(cursor, "users", "role", "TEXT NOT NULL DEFAULT 'child'")
    add_column_if_missing(cursor, "users", "account_type", "TEXT NOT NULL DEFAULT 'permanent'")
    add_column_if_missing(cursor, "users", "guest_type", "TEXT")
    add_column_if_missing(cursor, "users", "guest_status", "TEXT NOT NULL DEFAULT 'none'")
    add_column_if_missing(cursor, "users", "guest_created_by", "INTEGER")
    add_column_if_missing(cursor, "users", "guest_hours", "INTEGER NOT NULL DEFAULT 0")
    add_column_if_missing(cursor, "users", "guest_expires_at", "TEXT")
    add_column_if_missing(cursor, "users", "is_active", "INTEGER NOT NULL DEFAULT 1")
    add_column_if_missing(cursor, "users", "last_login_at", "TEXT")

    # --------------------------------------------------------
    # Mapear administradores antiguos a superadmin
    # --------------------------------------------------------
    cursor.execute("""
        UPDATE users
        SET role = 'superadmin', account_type = 'permanent', guest_status = 'none'
        WHERE is_admin = 1
          AND (role IS NULL OR role = '' OR role = 'child');
    """)

    cursor.execute("""
        UPDATE users
        SET role = 'child'
        WHERE role IS NULL OR role = '';
    """)

    cursor.execute("""
        UPDATE users
        SET account_type = 'permanent'
        WHERE account_type IS NULL OR account_type = '';
    """)

    cursor.execute("""
        UPDATE users
        SET guest_status = 'none'
        WHERE account_type = 'permanent'
          AND (guest_status IS NULL OR guest_status = '' OR guest_status != 'none');
    """)

    # --------------------------------------------------------
    # Wallet de tokens por usuario
    # --------------------------------------------------------
    cursor.execute("""
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
    """)

    # --------------------------------------------------------
    # Historial de consumo
    # --------------------------------------------------------
    cursor.execute("""
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
    """)

    # --------------------------------------------------------
    # Aceptación opcional del aviso legal
    # --------------------------------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS legal_notice_acceptance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL UNIQUE,
            accepted_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            notice_version TEXT NOT NULL DEFAULT '2026-05-06',
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );
    """)

    connection.commit()
    connection.close()

    # --------------------------------------------------------
    # Crear wallets para usuarios existentes y marcar expirados
    # --------------------------------------------------------
    ensure_wallets_for_all_users()
    expire_due_guest_accounts()


def ensure_wallets_for_all_users() -> None:
    """
    Crea una wallet de tokens para cada usuario existente.
    """
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("SELECT id, role FROM users;")
    rows = cursor.fetchall()
    connection.close()

    for row in rows:
        ensure_user_token_wallet(row["id"], row["role"])


# ------------------------------------------------------------
# Roles y permisos
# ------------------------------------------------------------
def normalize_role(role: str | None, is_admin: bool = False) -> str:
    """
    Normaliza roles antiguos y nuevos.
    """
    role_clean = str(role or "").strip().lower()

    if role_clean in VALID_ROLES:
        return role_clean

    return ROLE_SUPERADMIN if is_admin else ROLE_CHILD


def get_role_label(role: str) -> str:
    """
    Devuelve una etiqueta legible para el rol.
    """
    return ROLE_LABELS.get(normalize_role(role), "Usuario")


def get_permissions_for_role(role: str) -> dict[str, bool]:
    """
    Devuelve permisos simples para frontend y backend.
    """
    role = normalize_role(role)

    is_superadmin = role == ROLE_SUPERADMIN
    is_parent = role in {ROLE_PARENT_ADMIN, ROLE_GUEST_PARENT}
    is_child = role in {ROLE_CHILD, ROLE_GUEST_CHILD}

    return {
        "can_access_amigo": is_superadmin or is_child,
        "can_access_biblioteca": is_superadmin,
        "can_access_modo_padres": is_superadmin or is_parent,
        "can_access_admin": is_superadmin,
        "can_manage_users": is_superadmin,
        "can_manage_guests": is_superadmin,
        "can_manage_library": is_superadmin,
        "can_customize_child_friend": is_superadmin,
        "can_view_tokens": True,
    }


# ------------------------------------------------------------
# Módulos permitidos por rol
# ------------------------------------------------------------
def allowed_modules_for_role(role: str) -> list[str]:
    """
    Devuelve los módulos permitidos para cada rol.

    Importante:
        admin_panel se incluye solo para superadmin, pero no debe
        tratarse como chat. Es una sección administrativa.
    """
    role = normalize_role(role)

    if role == ROLE_SUPERADMIN:
        return [
            "amigo_imaginario",
            "biblioteca_inteligente",
            "modo_padres",
            "admin_panel",
        ]

    if role == ROLE_PARENT_ADMIN:
        return [
            "modo_padres",
        ]

    if role == ROLE_GUEST_PARENT:
        return [
            "modo_padres",
        ]

    if role == ROLE_CHILD:
        return [
            "amigo_imaginario",
        ]

    if role == ROLE_GUEST_CHILD:
        return [
            "amigo_imaginario",
        ]

    return []

def can_access_module(role: str, module: str) -> bool:
    """
    Indica si un rol puede entrar a un módulo.
    """
    return module in allowed_modules_for_role(role)


def assert_module_access(user: dict, module: str) -> None:
    """
    Lanza ValueError si el usuario no puede entrar al módulo.
    """
    role = normalize_role(user.get("role"), bool(user.get("is_admin")))

    if not can_access_module(role, module):
        raise ValueError("Tu cuenta no tiene permiso para acceder a este módulo.")


def assert_superadmin(user: dict) -> None:
    """
    Lanza ValueError si el usuario no es superadmin.
    """
    role = normalize_role(user.get("role"), bool(user.get("is_admin")))

    if role != ROLE_SUPERADMIN:
        raise ValueError("Esta acción solo está disponible para superadmin.")


# ------------------------------------------------------------
# Estado de usuario y guest
# ------------------------------------------------------------
def expire_due_guest_accounts() -> None:
    """
    Marca como expiradas las cuentas guest vencidas.
    """
    now_iso = to_iso(utc_now())

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        UPDATE users
        SET guest_status = 'expired', is_active = 0
        WHERE account_type = 'guest'
          AND guest_status = 'active'
          AND guest_expires_at IS NOT NULL
          AND guest_expires_at <= ?;
    """, (now_iso,))

    connection.commit()
    connection.close()


def get_user_access_info(user_id: int) -> dict[str, Any] | None:
    """
    Devuelve los datos de acceso del usuario, incluyendo rol y guest.
    """
    expire_due_guest_accounts()

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            id,
            username,
            display_name,
            is_admin,
            role,
            account_type,
            guest_type,
            guest_status,
            guest_created_by,
            guest_hours,
            guest_expires_at,
            is_active,
            last_login_at,
            created_at
        FROM users
        WHERE id = ?;
    """, (user_id,))

    row = cursor.fetchone()
    connection.close()

    if not row:
        return None

    role = normalize_role(row["role"], bool(row["is_admin"]))
    token_status = get_token_status(user_id)

    return {
        "id": row["id"],
        "username": row["username"],
        "display_name": row["display_name"],
        "is_admin": role == ROLE_SUPERADMIN,
        "role": role,
        "role_label": get_role_label(role),
        "account_type": row["account_type"] or ACCOUNT_TYPE_PERMANENT,
        "guest_type": row["guest_type"] or "",
        "guest_status": row["guest_status"] or GUEST_STATUS_NONE,
        "guest_created_by": row["guest_created_by"],
        "guest_hours": row["guest_hours"] or 0,
        "guest_expires_at": row["guest_expires_at"] or "",
        "is_active": bool(row["is_active"]),
        "last_login_at": row["last_login_at"] or "",
        "created_at": row["created_at"],
        "permissions": get_permissions_for_role(role),
        "allowed_modules": allowed_modules_for_role(role),
        "token_status": token_status,
    }


def decorate_user_for_access(user: dict | None) -> dict | None:
    """
    Mezcla datos legacy de chat_db.py con datos nuevos de acceso.
    """
    if not user:
        return None

    access_info = get_user_access_info(int(user["id"]))

    if not access_info:
        return user

    decorated = dict(user)
    decorated.update(access_info)
    decorated["is_admin"] = access_info["role"] == ROLE_SUPERADMIN
    return decorated


def validate_user_can_login(user_id: int) -> dict:
    """
    Valida estado activo y expiración guest. Retorna usuario decorado.
    """
    user_info = get_user_access_info(user_id)

    if not user_info:
        raise ValueError("Usuario no encontrado.")

    if not user_info["is_active"]:
        if user_info["account_type"] == ACCOUNT_TYPE_GUEST and user_info["guest_status"] == GUEST_STATUS_EXPIRED:
            raise ValueError("Tu acceso temporal expiró. Solicita al administrador una extensión si necesitas continuar.")

        raise ValueError("Tu cuenta está inactiva. Contacta al administrador.")

    return user_info


def mark_user_login(user_id: int) -> None:
    """
    Guarda la fecha del último inicio de sesión.
    """
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        UPDATE users
        SET last_login_at = ?
        WHERE id = ?;
    """, (to_iso(utc_now()), user_id))

    connection.commit()
    connection.close()


# ------------------------------------------------------------
# Tokens / créditos de uso
# ------------------------------------------------------------
def default_limit_for_role(role: str) -> int:
    """
    Define límite inicial por rol.
    """
    role = normalize_role(role)

    if role in {ROLE_GUEST_CHILD, ROLE_GUEST_PARENT}:
        return DEFAULT_GUEST_TOKEN_LIMIT

    return DEFAULT_TOKEN_LIMIT


def ensure_user_token_wallet(user_id: int, role: str | None = None) -> None:
    """
    Crea la wallet de tokens de un usuario si no existe.
    """
    role = normalize_role(role)
    now = utc_now()
    next_reset = now + timedelta(hours=DEFAULT_TOKEN_RESET_INTERVAL_HOURS)
    daily_limit = default_limit_for_role(role)

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT id
        FROM user_token_wallets
        WHERE user_id = ?;
    """, (user_id,))

    exists = cursor.fetchone()

    if not exists:
        cursor.execute("""
            INSERT INTO user_token_wallets (
                user_id,
                daily_limit,
                remaining_tokens,
                used_tokens,
                low_threshold,
                reset_interval_hours,
                last_reset_at,
                next_reset_at,
                updated_at
            )
            VALUES (?, ?, ?, 0, ?, ?, ?, ?, ?);
        """, (
            user_id,
            daily_limit,
            daily_limit,
            DEFAULT_LOW_TOKEN_THRESHOLD,
            DEFAULT_TOKEN_RESET_INTERVAL_HOURS,
            to_iso(now),
            to_iso(next_reset),
            to_iso(now),
        ))

    connection.commit()
    connection.close()


def refresh_user_tokens_if_needed(user_id: int) -> None:
    """
    Reinicia tokens automáticamente si ya pasó la fecha de reinicio.
    """
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT *
        FROM user_token_wallets
        WHERE user_id = ?;
    """, (user_id,))

    wallet = cursor.fetchone()

    if not wallet:
        connection.close()
        ensure_user_token_wallet(user_id)
        return

    now = utc_now()
    next_reset = parse_datetime(wallet["next_reset_at"])

    if next_reset and now >= next_reset:
        interval_hours = int(wallet["reset_interval_hours"] or DEFAULT_TOKEN_RESET_INTERVAL_HOURS)
        new_next_reset = now + timedelta(hours=interval_hours)

        cursor.execute("""
            UPDATE user_token_wallets
            SET remaining_tokens = daily_limit,
                used_tokens = 0,
                last_reset_at = ?,
                next_reset_at = ?,
                updated_at = ?
            WHERE user_id = ?;
        """, (to_iso(now), to_iso(new_next_reset), to_iso(now), user_id))

    connection.commit()
    connection.close()


def human_reset_text(next_reset_at: str | None) -> str:
    """
    Devuelve texto amigable para indicar cuándo se reinician tokens.
    """
    next_reset = parse_datetime(next_reset_at)

    if not next_reset:
        return "el próximo reinicio programado"

    now = utc_now()
    diff = next_reset - now
    total_minutes = max(1, int(diff.total_seconds() // 60))
    hours = total_minutes // 60
    minutes = total_minutes % 60

    if hours <= 0:
        return f"aproximadamente {minutes} minuto(s)"

    if minutes == 0:
        return f"aproximadamente {hours} hora(s)"

    return f"aproximadamente {hours} hora(s) y {minutes} minuto(s)"


def get_token_status(user_id: int) -> dict[str, Any]:
    """
    Devuelve estado de tokens del usuario con reinicio lazy.
    """
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("SELECT role FROM users WHERE id = ?;", (user_id,))
    user_row = cursor.fetchone()
    connection.close()

    role = normalize_role(user_row["role"] if user_row else None)

    if role == ROLE_SUPERADMIN:
        return {
            "daily_limit": 0,
            "remaining_tokens": 999999,
            "used_tokens": 0,
            "low_threshold": DEFAULT_LOW_TOKEN_THRESHOLD,
            "reset_interval_hours": DEFAULT_TOKEN_RESET_INTERVAL_HOURS,
            "last_reset_at": "",
            "next_reset_at": "",
            "is_low": False,
            "is_empty": False,
            "is_unlimited": True,
            "message": "Uso ilimitado para superadmin.",
            "reset_text": "sin reinicio necesario",
        }

    ensure_user_token_wallet(user_id, role)
    refresh_user_tokens_if_needed(user_id)

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT *
        FROM user_token_wallets
        WHERE user_id = ?;
    """, (user_id,))

    wallet = cursor.fetchone()
    connection.close()

    if not wallet:
        raise ValueError("No se pudo obtener la wallet de tokens.")

    remaining = int(wallet["remaining_tokens"] or 0)
    low_threshold = int(wallet["low_threshold"] or DEFAULT_LOW_TOKEN_THRESHOLD)
    is_empty = remaining <= 0
    is_low = 0 < remaining <= low_threshold
    reset_text = human_reset_text(wallet["next_reset_at"])

    message = ""

    if is_empty:
        message = NO_TOKENS_MESSAGE.format(reset_text=reset_text)
    elif is_low:
        message = LOW_TOKENS_MESSAGE

    return {
        "daily_limit": int(wallet["daily_limit"] or 0),
        "remaining_tokens": remaining,
        "used_tokens": int(wallet["used_tokens"] or 0),
        "low_threshold": low_threshold,
        "reset_interval_hours": int(wallet["reset_interval_hours"] or DEFAULT_TOKEN_RESET_INTERVAL_HOURS),
        "last_reset_at": wallet["last_reset_at"],
        "next_reset_at": wallet["next_reset_at"],
        "is_low": is_low,
        "is_empty": is_empty,
        "is_unlimited": False,
        "message": message,
        "reset_text": reset_text,
    }


def can_send_message_with_tokens(user_id: int) -> tuple[bool, dict[str, Any]]:
    """
    Indica si el usuario puede enviar un mensaje según tokens.
    """
    status = get_token_status(user_id)

    if status.get("is_unlimited"):
        return True, status

    return int(status.get("remaining_tokens", 0)) > 0, status


def consume_user_token(
    user_id: int,
    conversation_id: int | None,
    module: str,
    amount: int = 1,
    reason: str = "chat_message",
) -> dict[str, Any]:
    """
    Consume tokens después de generar una respuesta válida.
    """
    status = get_token_status(user_id)

    if status.get("is_unlimited"):
        return status

    if int(status["remaining_tokens"]) < amount:
        raise ValueError("No tienes tokens suficientes para esta acción.")

    connection = get_connection()
    cursor = connection.cursor()

    remaining_after = int(status["remaining_tokens"]) - amount
    now_iso = to_iso(utc_now())

    cursor.execute("""
        UPDATE user_token_wallets
        SET remaining_tokens = remaining_tokens - ?,
            used_tokens = used_tokens + ?,
            updated_at = ?
        WHERE user_id = ?;
    """, (amount, amount, now_iso, user_id))

    cursor.execute("""
        INSERT INTO token_usage_logs (
            user_id,
            conversation_id,
            module,
            amount,
            reason,
            remaining_after,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?);
    """, (
        user_id,
        conversation_id,
        module,
        amount,
        reason,
        remaining_after,
        now_iso,
    ))

    connection.commit()
    connection.close()

    return get_token_status(user_id)


def build_no_tokens_assistant_message(user_id: int) -> str:
    """
    Construye mensaje amigable cuando no hay tokens.
    """
    status = get_token_status(user_id)
    return status.get("message") or NO_TOKENS_MESSAGE.format(reset_text=status.get("reset_text", "unas horas"))


def set_user_token_policy(
    user_id: int,
    daily_limit: int,
    reset_interval_hours: int = DEFAULT_TOKEN_RESET_INTERVAL_HOURS,
    low_threshold: int = DEFAULT_LOW_TOKEN_THRESHOLD,
) -> dict[str, Any]:
    """
    Actualiza política de tokens de un usuario.
    """
    daily_limit = max(0, int(daily_limit))
    reset_interval_hours = max(1, int(reset_interval_hours))
    low_threshold = max(0, int(low_threshold))

    ensure_user_token_wallet(user_id)

    now = utc_now()
    next_reset = now + timedelta(hours=reset_interval_hours)

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        UPDATE user_token_wallets
        SET daily_limit = ?,
            remaining_tokens = ?,
            used_tokens = 0,
            low_threshold = ?,
            reset_interval_hours = ?,
            last_reset_at = ?,
            next_reset_at = ?,
            updated_at = ?
        WHERE user_id = ?;
    """, (
        daily_limit,
        daily_limit,
        low_threshold,
        reset_interval_hours,
        to_iso(now),
        to_iso(next_reset),
        to_iso(now),
        user_id,
    ))

    connection.commit()
    connection.close()

    return get_token_status(user_id)


# ------------------------------------------------------------
# Administración de usuarios y guests
# ------------------------------------------------------------
def list_users_with_access(limit: int = 500) -> list[dict[str, Any]]:
    """
    Lista usuarios con rol, estado guest y tokens.
    """
    expire_due_guest_accounts()

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT id
        FROM users
        ORDER BY id ASC
        LIMIT ?;
    """, (limit,))

    rows = cursor.fetchall()
    connection.close()

    users: list[dict[str, Any]] = []

    for row in rows:
        user = get_user_access_info(row["id"])

        if user:
            users.append(user)

    return users


def list_guest_users(limit: int = 500) -> list[dict[str, Any]]:
    """
    Lista solo cuentas guest.
    """
    return [
        user
        for user in list_users_with_access(limit=limit)
        if user.get("account_type") == ACCOUNT_TYPE_GUEST
    ]


def update_user_role(user_id: int, role: str) -> dict[str, Any]:
    """
    Cambia rol de usuario permanente.
    """
    role = normalize_role(role)

    if role in {ROLE_GUEST_CHILD, ROLE_GUEST_PARENT}:
        raise ValueError("Para cuentas guest usa el creador de guests.")

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("SELECT id FROM users WHERE id = ?;", (user_id,))

    if not cursor.fetchone():
        connection.close()
        raise ValueError("Usuario no encontrado.")

    cursor.execute("""
        UPDATE users
        SET role = ?,
            is_admin = ?,
            account_type = 'permanent',
            guest_type = NULL,
            guest_status = 'none',
            guest_created_by = NULL,
            guest_hours = 0,
            guest_expires_at = NULL,
            is_active = 1
        WHERE id = ?;
    """, (role, 1 if role == ROLE_SUPERADMIN else 0, user_id))

    connection.commit()
    connection.close()

    ensure_user_token_wallet(user_id, role)
    return get_user_access_info(user_id) or {}


def normalize_guest_type(guest_type: str) -> tuple[str, str]:
    """
    Normaliza tipo guest y devuelve guest_type + role.
    """
    value = str(guest_type or "").strip().lower()

    if value in {"child", "guest_child", "niño", "nino", "guest niño", "guest nino"}:
        return "guest_child", ROLE_GUEST_CHILD

    if value in {"parent", "padre", "guest_parent", "guest padre"}:
        return "guest_parent", ROLE_GUEST_PARENT

    raise ValueError("Tipo de guest inválido. Usa guest_child o guest_parent.")


def create_guest_user(
    created_by_user_id: int,
    username: str,
    password: str,
    display_name: str,
    guest_type: str,
    hours: int,
    token_limit: int = DEFAULT_GUEST_TOKEN_LIMIT,
) -> dict[str, Any]:
    """
    Crea una cuenta guest temporal desde superadmin.
    """
    creator = get_user_access_info(created_by_user_id)

    if not creator:
        raise ValueError("Usuario creador no encontrado.")

    assert_superadmin(creator)

    guest_type_normalized, role = normalize_guest_type(guest_type)
    hours = max(1, int(hours))
    now = utc_now()
    expires_at = now + timedelta(hours=hours)

    # Import interno para evitar dependencia circular con chat_db.py
    from database.chat_db import create_user

    created = create_user(
        username=username,
        password=password,
        display_name=display_name,
    )

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        UPDATE users
        SET role = ?,
            is_admin = 0,
            account_type = 'guest',
            guest_type = ?,
            guest_status = 'active',
            guest_created_by = ?,
            guest_hours = ?,
            guest_expires_at = ?,
            is_active = 1
        WHERE id = ?;
    """, (
        role,
        guest_type_normalized,
        created_by_user_id,
        hours,
        to_iso(expires_at),
        created["id"],
    ))

    connection.commit()
    connection.close()

    set_user_token_policy(
        user_id=created["id"],
        daily_limit=token_limit,
        reset_interval_hours=DEFAULT_TOKEN_RESET_INTERVAL_HOURS,
        low_threshold=DEFAULT_LOW_TOKEN_THRESHOLD,
    )

    return get_user_access_info(created["id"]) or {}


def extend_guest_user(user_id: int, extra_hours: int) -> dict[str, Any]:
    """
    Extiende el vencimiento de una cuenta guest.
    """
    extra_hours = max(1, int(extra_hours))
    user = get_user_access_info(user_id)

    if not user or user.get("account_type") != ACCOUNT_TYPE_GUEST:
        raise ValueError("La cuenta indicada no es guest.")

    base = parse_datetime(user.get("guest_expires_at")) or utc_now()

    if base < utc_now():
        base = utc_now()

    new_expiration = base + timedelta(hours=extra_hours)
    new_total_hours = int(user.get("guest_hours") or 0) + extra_hours

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        UPDATE users
        SET guest_expires_at = ?,
            guest_hours = ?,
            guest_status = 'active',
            is_active = 1
        WHERE id = ?;
    """, (to_iso(new_expiration), new_total_hours, user_id))

    connection.commit()
    connection.close()

    return get_user_access_info(user_id) or {}


def deactivate_guest_user(user_id: int) -> dict[str, Any]:
    """
    Desactiva manualmente una cuenta guest.
    """
    user = get_user_access_info(user_id)

    if not user or user.get("account_type") != ACCOUNT_TYPE_GUEST:
        raise ValueError("La cuenta indicada no es guest.")

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        UPDATE users
        SET guest_status = 'inactive',
            is_active = 0
        WHERE id = ?;
    """, (user_id,))

    connection.commit()
    connection.close()

    return get_user_access_info(user_id) or {}


def get_remaining_guest_text(guest_expires_at: str | None) -> str:
    """
    Texto amigable de tiempo restante para guest.
    """
    expires_at = parse_datetime(guest_expires_at)

    if not expires_at:
        return "Sin vencimiento definido"

    diff = expires_at - utc_now()

    if diff.total_seconds() <= 0:
        return "Expirado"

    total_minutes = int(diff.total_seconds() // 60)
    hours = total_minutes // 60
    minutes = total_minutes % 60

    if hours <= 0:
        return f"{minutes} minuto(s)"

    return f"{hours} hora(s) y {minutes} minuto(s)"