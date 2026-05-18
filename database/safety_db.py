# ============================================================
# database/safety_db.py
# Seguridad parental para AbrazoIA:
# - Filtro de contenido sensible para usuarios niño.
# - Registro de intentos bloqueados.
# - Notificaciones para padre/tutor vinculado.
# - Términos y condiciones por rol.
# ============================================================

from __future__ import annotations

from datetime import datetime
import re
import sqlite3
import unicodedata
from typing import Any

from database.chat_db import get_connection
from database.access_control import normalize_role


# ------------------------------------------------------------
# Versión actual de términos y condiciones.
# Si cambias el texto legal, cambia también esta versión.
# ------------------------------------------------------------
TERMS_VERSION = "2026-05-18"


GENERAL_TERMS_TEXT = """
AbrazoIA es una herramienta digital de acompañamiento y orientación general. La app no realiza diagnósticos médicos, psicológicos ni terapéuticos, no sustituye a profesionales de salud, educación o terapia, y debe usarse como apoyo complementario. El usuario debe utilizar la plataforma con respeto, evitar contenido violento, sexual, de drogas, acoso, explotación, daño personal o cualquier uso que pueda poner en riesgo a niñas, niños, adolescentes o terceros. La información generada por la IA puede contener errores y debe revisarse con criterio adulto cuando corresponda.
""".strip()


PARENT_TERMS_TEXT = """
Uso y condiciones para padre, madre o tutor: AbrazoIA tiene fines de acompañamiento emocional, orientación general, seguimiento de actividad y apoyo educativo. El rol del padre/tutor permite revisar actividad básica del menor, recibir alertas parentales cuando se detecten intentos de contenido sensible, consultar el directorio profesional validado por superadmin y solicitar apoyo u orientación. La plataforma no reemplaza atención profesional. Ante señales de riesgo, crisis emocional, autolesión, violencia, abuso o emergencia, el padre/tutor debe acudir con un adulto responsable, institución correspondiente o profesional calificado. El padre/tutor acepta supervisar el uso de la app, revisar las notificaciones y respetar la privacidad y bienestar del menor.
""".strip()


CHILD_TERMS_TEXT = """
Uso seguro para niñas, niños y adolescentes: AbrazoIA es un espacio para conversar con calma, pedir orientación general y realizar actividades seguras. No se permite buscar contenido sexual, violento, de drogas, autolesión, daño a otras personas, acoso o temas que puedan ponerte en riesgo. Si escribes algo que pueda ser peligroso, la app bloqueará la respuesta y podrá avisar a tu padre, madre o tutor para que pueda acompañarte.
""".strip()


# ------------------------------------------------------------
# Palabras/frases bloqueadas por categoría.
# Puedes editar esta lista según las recomendaciones del proyecto.
# ------------------------------------------------------------
BLOCKED_KEYWORDS: dict[str, list[str]] = {
    "contenido_adulto": [
        "pornografia",
        "porno",
        "xxx",
        "sexo explicito",
        "desnudos",
        "nudes",
        "pack",
        "packs",
        "onlyfans",
        "prostitucion",
        "escort",
        "erotico",
        "masturbacion",
        "fetiche",
        "contenido sexual",
    ],
    "violencia": [
        "como matar",
        "quiero matar",
        "hacer una bomba",
        "fabricar bomba",
        "arma casera",
        "pistola",
        "apuñalar",
        "acuchillar",
        "torturar",
        "gore",
        "amenazar",
        "golpear a alguien",
    ],
    "drogas": [
        "comprar droga",
        "vender droga",
        "cocaina",
        "cocaína",
        "cristal",
        "metanfetamina",
        "lsd",
        "marihuana",
        "weed",
        "thc",
        "fentanilo",
        "pastillas para drogar",
        "como drogar",
        "dealer",
    ],
    "autolesion_crisis": [
        "me quiero morir",
        "quiero morir",
        "suicidarme",
        "suicidio",
        "quitarme la vida",
        "hacerme daño",
        "cortarme",
        "autolesion",
        "autolesión",
        "no quiero vivir",
        "desaparecer para siempre",
    ],
    "acoso_o_abuso": [
        "acosar",
        "chantajear",
        "extorsionar",
        "humillar a",
        "bullying",
        "amenazar a",
        "mandar fotos intimas",
        "mandar fotos íntimas",
        "sexting",
        "engañar a un niño",
        "engañar a una niña",
    ],
}


CATEGORY_LABELS = {
    "contenido_adulto": "contenido adulto o sexual",
    "violencia": "violencia o daño a terceros",
    "drogas": "drogas o sustancias peligrosas",
    "autolesion_crisis": "posible crisis emocional o autolesión",
    "acoso_o_abuso": "acoso, abuso o riesgo digital",
}


# ------------------------------------------------------------
# Mensajes que verá el niño cuando se bloquee el contenido.
# ------------------------------------------------------------
BLOCKED_CHILD_MESSAGE = (
    "No puedo continuar con ese tema porque puede no ser seguro para ti. "
    "Voy a mantener este espacio tranquilo y protegido. Si esto tiene que ver "
    "con algo que te preocupa, habla con tu mamá, papá, tutor o un adulto de confianza."
)


CRISIS_CHILD_MESSAGE = (
    "Siento mucho que estés pasando por algo así. No estás solo. "
    "No puedo seguir con instrucciones sobre daño, pero sí quiero que busques ayuda ahora: "
    "acércate a tu mamá, papá, tutor, maestro o un adulto de confianza. "
    "Si hay peligro inmediato, pide ayuda de emergencia en tu localidad."
)


def now_text() -> str:
    """
    Devuelve fecha actual en formato ISO para SQLite.
    """
    return datetime.utcnow().replace(microsecond=0).isoformat()


def row_to_dict(row: sqlite3.Row | None) -> dict | None:
    """
    Convierte una fila SQLite a diccionario.
    """
    return dict(row) if row is not None else None


def rows_to_list(rows: list[sqlite3.Row]) -> list[dict]:
    """
    Convierte varias filas SQLite a lista de diccionarios.
    """
    return [dict(row) for row in rows]


def normalize_text(value: str) -> str:
    """
    Normaliza texto:
    - minúsculas
    - sin acentos
    - espacios compactados
    """
    text = str(value or "").lower().strip()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(char for char in text if not unicodedata.combining(char))
    text = re.sub(r"\s+", " ", text)
    return text


def initialize_safety_schema() -> None:
    """
    Crea tablas de seguridad parental y aceptación de términos.
    """
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS content_safety_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            conversation_id INTEGER,
            module TEXT NOT NULL DEFAULT '',
            category TEXT NOT NULL DEFAULT '',
            matched_terms TEXT NOT NULL DEFAULT '',
            blocked_message TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE SET NULL
        );
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS parental_notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            parent_user_id INTEGER NOT NULL,
            child_user_id INTEGER NOT NULL,
            safety_event_id INTEGER,
            title TEXT NOT NULL,
            message TEXT NOT NULL,
            category TEXT NOT NULL DEFAULT '',
            is_read INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            read_at TEXT,
            FOREIGN KEY (parent_user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (child_user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (safety_event_id) REFERENCES content_safety_events(id) ON DELETE SET NULL
        );
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS terms_acceptance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            role TEXT NOT NULL DEFAULT '',
            terms_version TEXT NOT NULL,
            accepted_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, terms_version),
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );
    """)

    connection.commit()
    connection.close()


def get_terms_text_for_role(role: str | None) -> str:
    """
    Devuelve términos personalizados según rol.
    """
    normalized_role = normalize_role(role)

    if normalized_role in {"parent_admin", "guest_parent"}:
        return PARENT_TERMS_TEXT

    if normalized_role in {"child", "guest_child"}:
        return CHILD_TERMS_TEXT

    return GENERAL_TERMS_TEXT


def get_terms_for_role(role: str | None) -> dict[str, Any]:
    """
    Devuelve versión y texto de términos para un rol.
    """
    return {
        "version": TERMS_VERSION,
        "role": normalize_role(role),
        "text": get_terms_text_for_role(role),
    }


def has_accepted_terms(user_id: int, version: str = TERMS_VERSION) -> bool:
    """
    Verifica si el usuario aceptó los términos vigentes.
    """
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT id
        FROM terms_acceptance
        WHERE user_id = ?
          AND terms_version = ?;
    """, (user_id, version))

    row = cursor.fetchone()
    connection.close()
    return row is not None


def accept_terms(user_id: int, role: str | None, version: str = TERMS_VERSION) -> dict[str, Any]:
    """
    Guarda aceptación de términos para el usuario autenticado.
    """
    normalized_role = normalize_role(role)

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO terms_acceptance (user_id, role, terms_version, accepted_at)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(user_id, terms_version) DO UPDATE SET
            role = excluded.role,
            accepted_at = excluded.accepted_at;
    """, (user_id, normalized_role, version, now_text()))

    connection.commit()
    connection.close()

    return {
        "accepted": True,
        "version": version,
        "role": normalized_role,
    }


def analyze_content_safety(content: str) -> dict[str, Any]:
    """
    Analiza si el texto contiene palabras o frases bloqueadas.
    """
    normalized_content = normalize_text(content)

    for category, keywords in BLOCKED_KEYWORDS.items():
        normalized_terms = [normalize_text(term) for term in keywords]
        matches = [
            term
            for term in normalized_terms
            if term and term in normalized_content
        ]

        if matches:
            category_label = CATEGORY_LABELS.get(category, category)

            user_message = (
                CRISIS_CHILD_MESSAGE
                if category == "autolesion_crisis"
                else BLOCKED_CHILD_MESSAGE
            )

            parent_message = (
                "AbrazoIA bloqueó un intento de contenido sensible asociado con "
                f"{category_label}. Se recomienda revisar el contexto con calma, "
                "acompañar al menor y, si corresponde, buscar orientación profesional."
            )

            return {
                "is_blocked": True,
                "category": category,
                "category_label": category_label,
                "matched_terms": matches,
                "user_message": user_message,
                "parent_message": parent_message,
            }

    return {
        "is_blocked": False,
        "category": "",
        "category_label": "",
        "matched_terms": [],
        "user_message": "",
        "parent_message": "",
    }


def should_apply_child_safety_filter(user: dict, module: str) -> bool:
    """
    Aplica el filtro solo a usuarios niño o guest niño.
    """
    role = normalize_role(
        user.get("role"),
        bool(user.get("is_admin", False)),
    )

    return role in {"child", "guest_child"} and module in {
        "amigo_imaginario",
        "biblioteca_inteligente",
    }


def record_blocked_content_event(
    user_id: int,
    module: str,
    conversation_id: int | None,
    original_content: str,
    safety_result: dict[str, Any],
) -> int:
    """
    Guarda el evento bloqueado y genera notificación parental.
    """
    connection = get_connection()
    cursor = connection.cursor()

    matched_terms = ", ".join(safety_result.get("matched_terms", []))

    cursor.execute("""
        INSERT INTO content_safety_events (
            user_id,
            conversation_id,
            module,
            category,
            matched_terms,
            blocked_message,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?);
    """, (
        user_id,
        conversation_id,
        module,
        safety_result.get("category", ""),
        matched_terms,
        str(original_content or "")[:500],
        now_text(),
    ))

    event_id = int(cursor.lastrowid)

    connection.commit()
    connection.close()

    create_parent_notifications_for_event(
        child_user_id=user_id,
        safety_event_id=event_id,
        safety_result=safety_result,
    )

    return event_id


def create_parent_notifications_for_event(
    child_user_id: int,
    safety_event_id: int,
    safety_result: dict[str, Any],
) -> None:
    """
    Crea una alerta para cada padre/tutor vinculado al menor.
    """
    from database.support_db import list_parents_for_child

    parents = list_parents_for_child(child_user_id)

    if not parents:
        return

    connection = get_connection()
    cursor = connection.cursor()

    title = "Alerta parental de contenido bloqueado"
    message = safety_result.get(
        "parent_message",
        "Se bloqueó un contenido sensible.",
    )

    for parent in parents:
        cursor.execute("""
            INSERT INTO parental_notifications (
                parent_user_id,
                child_user_id,
                safety_event_id,
                title,
                message,
                category,
                is_read,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, 0, ?);
        """, (
            parent["id"],
            child_user_id,
            safety_event_id,
            title,
            message,
            safety_result.get("category", ""),
            now_text(),
        ))

    connection.commit()
    connection.close()


def list_parental_notifications(
    parent_user_id: int,
    limit: int = 50,
    unread_only: bool = False,
) -> list[dict]:
    """
    Lista alertas parentales del padre/tutor autenticado.
    """
    connection = get_connection()
    cursor = connection.cursor()

    where_extra = "AND pn.is_read = 0" if unread_only else ""

    cursor.execute(f"""
        SELECT
            pn.id,
            pn.parent_user_id,
            pn.child_user_id,
            pn.safety_event_id,
            pn.title,
            pn.message,
            pn.category,
            pn.is_read,
            pn.created_at,
            pn.read_at,
            child.display_name AS child_name,
            child.username AS child_username
        FROM parental_notifications pn
        INNER JOIN users child
            ON child.id = pn.child_user_id
        WHERE pn.parent_user_id = ?
        {where_extra}
        ORDER BY pn.created_at DESC
        LIMIT ?;
    """, (parent_user_id, limit))

    rows = cursor.fetchall()
    connection.close()
    return rows_to_list(rows)


def mark_parental_notification_read(
    parent_user_id: int,
    notification_id: int,
) -> dict[str, Any]:
    """
    Marca una alerta parental como leída.
    """
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        UPDATE parental_notifications
        SET is_read = 1,
            read_at = ?
        WHERE id = ?
          AND parent_user_id = ?;
    """, (now_text(), notification_id, parent_user_id))

    if cursor.rowcount == 0:
        connection.close()
        raise ValueError("Notificación no encontrada o sin permiso.")

    connection.commit()

    cursor.execute("""
        SELECT
            pn.id,
            pn.parent_user_id,
            pn.child_user_id,
            pn.safety_event_id,
            pn.title,
            pn.message,
            pn.category,
            pn.is_read,
            pn.created_at,
            pn.read_at,
            child.display_name AS child_name,
            child.username AS child_username
        FROM parental_notifications pn
        INNER JOIN users child
            ON child.id = pn.child_user_id
        WHERE pn.id = ?;
    """, (notification_id,))

    row = cursor.fetchone()
    connection.close()

    return row_to_dict(row) or {}