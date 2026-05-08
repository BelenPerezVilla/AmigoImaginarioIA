# ============================================================
# database/support_db.py
# Funciones de base de datos para:
# - Vincular padre/madre con hijo
# - Generar resumen de actividad del hijo
# - Mensajes de padres al superadmin / psicólogo
# - Respuestas del superadmin
# - Contactos o lugares recomendados
# ============================================================

from __future__ import annotations

from datetime import datetime
import sqlite3
from typing import Any

from database.chat_db import get_connection


# ------------------------------------------------------------
# Fecha actual en formato texto
# ------------------------------------------------------------
def now_text() -> str:
    """
    Devuelve la fecha actual en formato ISO simple.
    """
    return datetime.utcnow().replace(microsecond=0).isoformat()


# ------------------------------------------------------------
# Convertir fila SQLite a diccionario
# ------------------------------------------------------------
def row_to_dict(row: sqlite3.Row | None) -> dict | None:
    """
    Convierte una fila SQLite en diccionario.
    """
    if row is None:
        return None

    return dict(row)


# ------------------------------------------------------------
# Convertir varias filas SQLite a lista de diccionarios
# ------------------------------------------------------------
def rows_to_list(rows: list[sqlite3.Row]) -> list[dict]:
    """
    Convierte varias filas SQLite a lista de diccionarios.
    """
    return [dict(row) for row in rows]


# ------------------------------------------------------------
# Inicializar tablas del módulo de apoyo a padres
# ------------------------------------------------------------
def initialize_support_schema() -> None:
    """
    Crea las tablas necesarias para seguimiento de padres,
    solicitudes de apoyo y contactos recomendados.
    """
    connection = get_connection()
    cursor = connection.cursor()

    # --------------------------------------------------------
    # Relación padre-hijo
    # Permite que un padre vea resumen de uno o más hijos.
    # --------------------------------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS parent_child_links (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            parent_user_id INTEGER NOT NULL,
            child_user_id INTEGER NOT NULL,
            created_by_user_id INTEGER,
            status TEXT NOT NULL DEFAULT 'active',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(parent_user_id, child_user_id),
            FOREIGN KEY (parent_user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (child_user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (created_by_user_id) REFERENCES users(id) ON DELETE SET NULL
        );
    """)

    # --------------------------------------------------------
    # Solicitudes del padre al superadmin / psicólogo
    # --------------------------------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS parent_support_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            parent_user_id INTEGER NOT NULL,
            child_user_id INTEGER,
            subject TEXT NOT NULL,
            message TEXT NOT NULL,
            priority TEXT NOT NULL DEFAULT 'normal',
            status TEXT NOT NULL DEFAULT 'open',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (parent_user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (child_user_id) REFERENCES users(id) ON DELETE SET NULL
        );
    """)

    # --------------------------------------------------------
    # Respuestas del superadmin / psicólogo a cada solicitud
    # --------------------------------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS parent_support_replies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            request_id INTEGER NOT NULL,
            author_user_id INTEGER NOT NULL,
            message TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (request_id) REFERENCES parent_support_requests(id) ON DELETE CASCADE,
            FOREIGN KEY (author_user_id) REFERENCES users(id) ON DELETE CASCADE
        );
    """)

    # --------------------------------------------------------
    # Catálogo de contactos recomendados
    # Pueden ser especialistas, centros, instituciones o lugares.
    # --------------------------------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS support_contacts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            specialty TEXT NOT NULL DEFAULT '',
            organization TEXT NOT NULL DEFAULT '',
            phone TEXT NOT NULL DEFAULT '',
            email TEXT NOT NULL DEFAULT '',
            address TEXT NOT NULL DEFAULT '',
            notes TEXT NOT NULL DEFAULT '',
            is_active INTEGER NOT NULL DEFAULT 1,
            created_by_user_id INTEGER,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (created_by_user_id) REFERENCES users(id) ON DELETE SET NULL
        );
    """)

    # --------------------------------------------------------
    # Contactos recomendados dentro de una solicitud específica
    # --------------------------------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS support_request_contact_recommendations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            request_id INTEGER NOT NULL,
            contact_id INTEGER NOT NULL,
            recommended_by_user_id INTEGER NOT NULL,
            note TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(request_id, contact_id),
            FOREIGN KEY (request_id) REFERENCES parent_support_requests(id) ON DELETE CASCADE,
            FOREIGN KEY (contact_id) REFERENCES support_contacts(id) ON DELETE CASCADE,
            FOREIGN KEY (recommended_by_user_id) REFERENCES users(id) ON DELETE CASCADE
        );
    """)

    connection.commit()
    connection.close()


# ------------------------------------------------------------
# Obtener usuario básico
# ------------------------------------------------------------
def get_user_basic(user_id: int) -> dict | None:
    """
    Obtiene datos básicos de un usuario.
    """
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
            is_active
        FROM users
        WHERE id = ?;
    """, (user_id,))

    row = cursor.fetchone()
    connection.close()

    return row_to_dict(row)


# ------------------------------------------------------------
# Listar hijos vinculados a un padre
# ------------------------------------------------------------
def list_children_for_parent(parent_user_id: int) -> list[dict]:
    """
    Lista los hijos vinculados a un padre.
    """
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            u.id,
            u.username,
            u.display_name,
            u.role,
            pcl.created_at AS linked_at
        FROM parent_child_links pcl
        INNER JOIN users u
            ON u.id = pcl.child_user_id
        WHERE pcl.parent_user_id = ?
          AND pcl.status = 'active'
        ORDER BY u.display_name ASC;
    """, (parent_user_id,))

    rows = cursor.fetchall()
    connection.close()

    return rows_to_list(rows)


# ------------------------------------------------------------
# Listar padres vinculados a un hijo
# ------------------------------------------------------------
def list_parents_for_child(child_user_id: int) -> list[dict]:
    """
    Lista padres vinculados a un hijo.
    """
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            u.id,
            u.username,
            u.display_name,
            u.role,
            pcl.created_at AS linked_at
        FROM parent_child_links pcl
        INNER JOIN users u
            ON u.id = pcl.parent_user_id
        WHERE pcl.child_user_id = ?
          AND pcl.status = 'active'
        ORDER BY u.display_name ASC;
    """, (child_user_id,))

    rows = cursor.fetchall()
    connection.close()

    return rows_to_list(rows)


# ------------------------------------------------------------
# Vincular padre con hijo
# ------------------------------------------------------------
def link_parent_child(
    parent_user_id: int,
    child_user_id: int,
    created_by_user_id: int | None = None,
) -> None:
    """
    Vincula una cuenta de padre con una cuenta de hijo.
    """
    if parent_user_id == child_user_id:
        raise ValueError("El padre y el hijo no pueden ser el mismo usuario.")

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO parent_child_links (
            parent_user_id,
            child_user_id,
            created_by_user_id,
            status,
            created_at,
            updated_at
        )
        VALUES (?, ?, ?, 'active', ?, ?)
        ON CONFLICT(parent_user_id, child_user_id) DO UPDATE SET
            status = 'active',
            updated_at = excluded.updated_at,
            created_by_user_id = excluded.created_by_user_id;
    """, (
        parent_user_id,
        child_user_id,
        created_by_user_id,
        now_text(),
        now_text(),
    ))

    connection.commit()
    connection.close()


# ------------------------------------------------------------
# Desvincular padre e hijo
# ------------------------------------------------------------
def unlink_parent_child(parent_user_id: int, child_user_id: int) -> None:
    """
    Desactiva el vínculo entre padre e hijo.
    """
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        UPDATE parent_child_links
        SET status = 'inactive',
            updated_at = ?
        WHERE parent_user_id = ?
          AND child_user_id = ?;
    """, (
        now_text(),
        parent_user_id,
        child_user_id,
    ))

    connection.commit()
    connection.close()


# ------------------------------------------------------------
# Validar si un padre puede ver a un hijo
# ------------------------------------------------------------
def parent_can_view_child(parent_user_id: int, child_user_id: int) -> bool:
    """
    Verifica si el padre tiene permiso para ver resumen de ese hijo.
    """
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT id
        FROM parent_child_links
        WHERE parent_user_id = ?
          AND child_user_id = ?
          AND status = 'active';
    """, (
        parent_user_id,
        child_user_id,
    ))

    row = cursor.fetchone()
    connection.close()

    return row is not None


# ------------------------------------------------------------
# Obtener resumen de actividad del hijo
# ------------------------------------------------------------
def get_child_activity_summary(
    parent_user_id: int,
    child_user_id: int,
    allow_superadmin: bool = False,
) -> dict:
    """
    Genera un resumen básico de uso del hijo dentro del sistema.

    Importante:
        No genera diagnóstico. Solo muestra actividad registrada
        en el sistema: módulos, mensajes, tokens y fechas.
    """
    if not allow_superadmin and not parent_can_view_child(parent_user_id, child_user_id):
        raise ValueError("No tienes permiso para ver el resumen de este usuario.")

    child = get_user_basic(child_user_id)

    if not child:
        raise ValueError("Usuario hijo no encontrado.")

    connection = get_connection()
    cursor = connection.cursor()

    # --------------------------------------------------------
    # Conversaciones por módulo
    # --------------------------------------------------------
    cursor.execute("""
        SELECT
            module,
            COUNT(*) AS total_conversations,
            MAX(updated_at) AS last_activity
        FROM conversations
        WHERE user_id = ?
        GROUP BY module
        ORDER BY last_activity DESC;
    """, (child_user_id,))

    conversations_by_module = rows_to_list(cursor.fetchall())

    # --------------------------------------------------------
    # Mensajes por módulo
    # --------------------------------------------------------
    cursor.execute("""
        SELECT
            c.module,
            COUNT(m.id) AS total_messages,
            SUM(CASE WHEN m.role = 'user' THEN 1 ELSE 0 END) AS user_messages,
            SUM(CASE WHEN m.role = 'assistant' THEN 1 ELSE 0 END) AS assistant_messages
        FROM conversations c
        LEFT JOIN messages m
            ON m.conversation_id = c.id
        WHERE c.user_id = ?
        GROUP BY c.module
        ORDER BY total_messages DESC;
    """, (child_user_id,))

    messages_by_module = rows_to_list(cursor.fetchall())

    # --------------------------------------------------------
    # Actividad reciente
    # --------------------------------------------------------
    cursor.execute("""
        SELECT
            c.id,
            c.module,
            c.title,
            c.updated_at,
            COUNT(m.id) AS total_messages
        FROM conversations c
        LEFT JOIN messages m
            ON m.conversation_id = c.id
        WHERE c.user_id = ?
        GROUP BY c.id
        ORDER BY c.updated_at DESC
        LIMIT 5;
    """, (child_user_id,))

    recent_activity = rows_to_list(cursor.fetchall())

    # --------------------------------------------------------
    # Tokens
    # --------------------------------------------------------
    cursor.execute("""
        SELECT
            daily_limit,
            remaining_tokens,
            used_tokens,
            low_threshold,
            last_reset_at,
            next_reset_at
        FROM user_token_wallets
        WHERE user_id = ?;
    """, (child_user_id,))

    token_wallet = row_to_dict(cursor.fetchone()) or {}

    # --------------------------------------------------------
    # Solicitudes de apoyo relacionadas con ese hijo
    # --------------------------------------------------------
    cursor.execute("""
        SELECT
            COUNT(*) AS total_requests,
            SUM(CASE WHEN status = 'open' THEN 1 ELSE 0 END) AS open_requests,
            SUM(CASE WHEN status = 'in_review' THEN 1 ELSE 0 END) AS in_review_requests,
            SUM(CASE WHEN status = 'closed' THEN 1 ELSE 0 END) AS closed_requests
        FROM parent_support_requests
        WHERE child_user_id = ?;
    """, (child_user_id,))

    support_summary = row_to_dict(cursor.fetchone()) or {}

    connection.close()

    return {
        "child": child,
        "conversations_by_module": conversations_by_module,
        "messages_by_module": messages_by_module,
        "recent_activity": recent_activity,
        "token_wallet": token_wallet,
        "support_summary": support_summary,
        "note": (
            "Este resumen muestra actividad de uso dentro del sistema. "
            "No representa evaluación clínica, diagnóstico ni seguimiento terapéutico."
        ),
    }


# ------------------------------------------------------------
# Crear solicitud de apoyo
# ------------------------------------------------------------
def create_support_request(
    parent_user_id: int,
    child_user_id: int | None,
    subject: str,
    message: str,
    priority: str = "normal",
) -> dict:
    """
    Crea una solicitud del padre para el superadmin / psicólogo.
    """
    subject_clean = subject.strip()
    message_clean = message.strip()
    priority_clean = priority.strip() or "normal"

    if not subject_clean:
        raise ValueError("Escribe un asunto para la solicitud.")

    if not message_clean:
        raise ValueError("Escribe el mensaje de la solicitud.")

    if child_user_id is not None and not parent_can_view_child(parent_user_id, child_user_id):
        raise ValueError("No tienes permiso para enviar solicitudes sobre este usuario.")

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO parent_support_requests (
            parent_user_id,
            child_user_id,
            subject,
            message,
            priority,
            status,
            created_at,
            updated_at
        )
        VALUES (?, ?, ?, ?, ?, 'open', ?, ?);
    """, (
        parent_user_id,
        child_user_id,
        subject_clean,
        message_clean,
        priority_clean,
        now_text(),
        now_text(),
    ))

    request_id = cursor.lastrowid
    connection.commit()
    connection.close()

    return get_support_request_by_id(int(request_id)) or {}


# ------------------------------------------------------------
# Obtener solicitud por ID
# ------------------------------------------------------------
def get_support_request_by_id(request_id: int) -> dict | None:
    """
    Obtiene una solicitud por ID.
    """
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            r.*,
            p.display_name AS parent_name,
            p.username AS parent_username,
            c.display_name AS child_name,
            c.username AS child_username
        FROM parent_support_requests r
        INNER JOIN users p
            ON p.id = r.parent_user_id
        LEFT JOIN users c
            ON c.id = r.child_user_id
        WHERE r.id = ?;
    """, (request_id,))

    row = cursor.fetchone()
    connection.close()

    return row_to_dict(row)


# ------------------------------------------------------------
# Listar solicitudes del padre
# ------------------------------------------------------------
def list_support_requests_for_parent(parent_user_id: int) -> list[dict]:
    """
    Lista solicitudes enviadas por un padre.
    """
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            r.*,
            c.display_name AS child_name,
            c.username AS child_username
        FROM parent_support_requests r
        LEFT JOIN users c
            ON c.id = r.child_user_id
        WHERE r.parent_user_id = ?
        ORDER BY r.updated_at DESC, r.id DESC;
    """, (parent_user_id,))

    rows = cursor.fetchall()
    connection.close()

    return rows_to_list(rows)


# ------------------------------------------------------------
# Listar solicitudes para superadmin
# ------------------------------------------------------------
def list_support_requests_for_superadmin(status_filter: str = "Todas") -> list[dict]:
    """
    Lista solicitudes recibidas para el superadmin / psicólogo.
    """
    connection = get_connection()
    cursor = connection.cursor()

    query = """
        SELECT
            r.*,
            p.display_name AS parent_name,
            p.username AS parent_username,
            c.display_name AS child_name,
            c.username AS child_username
        FROM parent_support_requests r
        INNER JOIN users p
            ON p.id = r.parent_user_id
        LEFT JOIN users c
            ON c.id = r.child_user_id
        WHERE 1 = 1
    """

    params: list[Any] = []

    if status_filter and status_filter != "Todas":
        query += " AND r.status = ?"
        params.append(status_filter)

    query += """
        ORDER BY r.updated_at DESC, r.id DESC;
    """

    cursor.execute(query, params)

    rows = cursor.fetchall()
    connection.close()

    return rows_to_list(rows)


# ------------------------------------------------------------
# Responder solicitud
# ------------------------------------------------------------
def add_support_reply(
    request_id: int,
    author_user_id: int,
    message: str,
    new_status: str = "in_review",
) -> dict:
    """
    Agrega una respuesta a una solicitud de apoyo.
    """
    message_clean = message.strip()

    if not message_clean:
        raise ValueError("Escribe una respuesta.")

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO parent_support_replies (
            request_id,
            author_user_id,
            message,
            created_at
        )
        VALUES (?, ?, ?, ?);
    """, (
        request_id,
        author_user_id,
        message_clean,
        now_text(),
    ))

    cursor.execute("""
        UPDATE parent_support_requests
        SET status = ?,
            updated_at = ?
        WHERE id = ?;
    """, (
        new_status,
        now_text(),
        request_id,
    ))

    reply_id = cursor.lastrowid

    connection.commit()
    connection.close()

    return get_support_reply_by_id(int(reply_id)) or {}


# ------------------------------------------------------------
# Obtener respuesta por ID
# ------------------------------------------------------------
def get_support_reply_by_id(reply_id: int) -> dict | None:
    """
    Obtiene una respuesta por ID.
    """
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            pr.*,
            u.display_name AS author_name,
            u.username AS author_username
        FROM parent_support_replies pr
        INNER JOIN users u
            ON u.id = pr.author_user_id
        WHERE pr.id = ?;
    """, (reply_id,))

    row = cursor.fetchone()
    connection.close()

    return row_to_dict(row)


# ------------------------------------------------------------
# Listar respuestas de solicitud
# ------------------------------------------------------------
def list_support_replies(request_id: int) -> list[dict]:
    """
    Lista respuestas de una solicitud.
    """
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            pr.*,
            u.display_name AS author_name,
            u.username AS author_username
        FROM parent_support_replies pr
        INNER JOIN users u
            ON u.id = pr.author_user_id
        WHERE pr.request_id = ?
        ORDER BY pr.created_at ASC, pr.id ASC;
    """, (request_id,))

    rows = cursor.fetchall()
    connection.close()

    return rows_to_list(rows)


# ------------------------------------------------------------
# Actualizar estado de solicitud
# ------------------------------------------------------------
def update_support_request_status(request_id: int, status: str) -> None:
    """
    Actualiza estado de una solicitud.
    """
    valid_statuses = {"open", "in_review", "closed"}

    if status not in valid_statuses:
        raise ValueError("Estado inválido.")

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        UPDATE parent_support_requests
        SET status = ?,
            updated_at = ?
        WHERE id = ?;
    """, (
        status,
        now_text(),
        request_id,
    ))

    connection.commit()
    connection.close()


# ------------------------------------------------------------
# Crear contacto recomendado
# ------------------------------------------------------------
def create_support_contact(
    name: str,
    specialty: str,
    organization: str = "",
    phone: str = "",
    email: str = "",
    address: str = "",
    notes: str = "",
    created_by_user_id: int | None = None,
) -> dict:
    """
    Crea un contacto o lugar recomendado.
    """
    name_clean = name.strip()
    specialty_clean = specialty.strip()

    if not name_clean:
        raise ValueError("Escribe el nombre del contacto o lugar.")

    if not specialty_clean:
        raise ValueError("Escribe la especialidad o tipo de apoyo.")

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO support_contacts (
            name,
            specialty,
            organization,
            phone,
            email,
            address,
            notes,
            is_active,
            created_by_user_id,
            created_at,
            updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?, ?, ?);
    """, (
        name_clean,
        specialty_clean,
        organization.strip(),
        phone.strip(),
        email.strip(),
        address.strip(),
        notes.strip(),
        created_by_user_id,
        now_text(),
        now_text(),
    ))

    contact_id = cursor.lastrowid
    connection.commit()
    connection.close()

    return get_support_contact_by_id(int(contact_id)) or {}


# ------------------------------------------------------------
# Obtener contacto por ID
# ------------------------------------------------------------
def get_support_contact_by_id(contact_id: int) -> dict | None:
    """
    Obtiene un contacto recomendado por ID.
    """
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT *
        FROM support_contacts
        WHERE id = ?;
    """, (contact_id,))

    row = cursor.fetchone()
    connection.close()

    return row_to_dict(row)


# ------------------------------------------------------------
# Listar contactos activos
# ------------------------------------------------------------
def list_support_contacts(active_only: bool = True) -> list[dict]:
    """
    Lista contactos recomendados.
    """
    connection = get_connection()
    cursor = connection.cursor()

    if active_only:
        cursor.execute("""
            SELECT *
            FROM support_contacts
            WHERE is_active = 1
            ORDER BY specialty ASC, name ASC;
        """)
    else:
        cursor.execute("""
            SELECT *
            FROM support_contacts
            ORDER BY specialty ASC, name ASC;
        """)

    rows = cursor.fetchall()
    connection.close()

    return rows_to_list(rows)


# ------------------------------------------------------------
# Desactivar contacto
# ------------------------------------------------------------
def deactivate_support_contact(contact_id: int) -> None:
    """
    Desactiva un contacto recomendado.
    """
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        UPDATE support_contacts
        SET is_active = 0,
            updated_at = ?
        WHERE id = ?;
    """, (
        now_text(),
        contact_id,
    ))

    connection.commit()
    connection.close()


# ------------------------------------------------------------
# Recomendar contacto dentro de una solicitud
# ------------------------------------------------------------
def recommend_contact_for_request(
    request_id: int,
    contact_id: int,
    recommended_by_user_id: int,
    note: str = "",
) -> None:
    """
    Vincula un contacto recomendado a una solicitud de apoyo.
    """
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO support_request_contact_recommendations (
            request_id,
            contact_id,
            recommended_by_user_id,
            note,
            created_at
        )
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(request_id, contact_id) DO UPDATE SET
            note = excluded.note,
            recommended_by_user_id = excluded.recommended_by_user_id,
            created_at = excluded.created_at;
    """, (
        request_id,
        contact_id,
        recommended_by_user_id,
        note.strip(),
        now_text(),
    ))

    connection.commit()
    connection.close()


# ------------------------------------------------------------
# Listar contactos recomendados en una solicitud
# ------------------------------------------------------------
def list_recommended_contacts_for_request(request_id: int) -> list[dict]:
    """
    Lista contactos recomendados para una solicitud específica.
    """
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            sc.*,
            r.note AS recommendation_note,
            r.created_at AS recommended_at,
            u.display_name AS recommended_by_name
        FROM support_request_contact_recommendations r
        INNER JOIN support_contacts sc
            ON sc.id = r.contact_id
        INNER JOIN users u
            ON u.id = r.recommended_by_user_id
        WHERE r.request_id = ?
        ORDER BY r.created_at DESC;
    """, (request_id,))

    rows = cursor.fetchall()
    connection.close()

    return rows_to_list(rows)

# ------------------------------------------------------------
# Buscar contactos recomendados por texto
# ------------------------------------------------------------
def search_support_contacts_by_text(
    text: str,
    limit: int = 5,
) -> list[dict]:
    """
    Busca contactos activos usando palabras dentro de:
    - nombre
    - especialidad
    - organización
    - notas
    """
    text_clean = str(text or "").strip().lower()

    connection = get_connection()
    cursor = connection.cursor()

    if not text_clean:
        cursor.execute("""
            SELECT *
            FROM support_contacts
            WHERE is_active = 1
            ORDER BY specialty ASC, name ASC
            LIMIT ?;
        """, (limit,))

        rows = cursor.fetchall()
        connection.close()

        return rows_to_list(rows)

    words = [
        word.strip()
        for word in text_clean.replace(",", " ").replace(".", " ").split()
        if len(word.strip()) >= 4
    ]

    if not words:
        cursor.execute("""
            SELECT *
            FROM support_contacts
            WHERE is_active = 1
            ORDER BY specialty ASC, name ASC
            LIMIT ?;
        """, (limit,))

        rows = cursor.fetchall()
        connection.close()

        return rows_to_list(rows)

    conditions = []
    params = []

    for word in words[:8]:
        like_value = f"%{word}%"

        conditions.append("""
            (
                LOWER(name) LIKE ?
                OR LOWER(specialty) LIKE ?
                OR LOWER(organization) LIKE ?
                OR LOWER(notes) LIKE ?
            )
        """)

        params.extend([
            like_value,
            like_value,
            like_value,
            like_value,
        ])

    query = f"""
        SELECT DISTINCT *
        FROM support_contacts
        WHERE is_active = 1
          AND (
            {' OR '.join(conditions)}
          )
        ORDER BY specialty ASC, name ASC
        LIMIT ?;
    """

    params.append(limit)

    cursor.execute(query, params)

    rows = cursor.fetchall()
    connection.close()

    return rows_to_list(rows)