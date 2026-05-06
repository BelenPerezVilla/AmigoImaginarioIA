# ============================================================
# database/chat_db.py
# SQLite para:
# - usuarios y autenticación
# - historial por usuario
# - biblioteca estructurada
# - administración de artículos
# - importación/exportación masiva de artículos
# ============================================================

import hashlib
import hmac
import os
import secrets
import sqlite3
from typing import Optional


from config import DATABASE_PATH


# ------------------------------------------------------------
# Obtener conexión a SQLite
# ------------------------------------------------------------
def get_connection() -> sqlite3.Connection:
    """
    Crea y devuelve una conexión a la base de datos SQLite.

    Retorna:
        sqlite3.Connection: conexión activa
    """
    carpeta_db = os.path.dirname(DATABASE_PATH)

    # Crear carpeta si no existe
    if carpeta_db:
        os.makedirs(carpeta_db, exist_ok=True)

    connection = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON;")

    return connection


# ------------------------------------------------------------
# Verificar si una columna existe
# ------------------------------------------------------------
def column_exists(table_name: str, column_name: str) -> bool:
    """
    Verifica si una columna existe dentro de una tabla.

    Parámetros:
        table_name (str): nombre de la tabla
        column_name (str): nombre de la columna

    Retorna:
        bool: True si existe, False si no
    """
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(f"PRAGMA table_info({table_name});")
    columnas = cursor.fetchall()

    connection.close()

    return any(columna["name"] == column_name for columna in columnas)


# ------------------------------------------------------------
# Inicializar base de datos
# ------------------------------------------------------------
def initialize_database() -> None:
    """
    Crea las tablas necesarias y aplica migraciones simples
    para mantener compatibilidad con fases anteriores.
    """
    connection = get_connection()
    cursor = connection.cursor()

    # --------------------------------------------------------
    # Tabla de usuarios
    # --------------------------------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            display_name TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            is_admin INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
    """)

# Tabla de artículos favoritos por usuario
# --------------------------------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS article_favorites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            article_id INTEGER NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, article_id),
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (article_id) REFERENCES articles(id) ON DELETE CASCADE
        );
    """)
# --------------------------------------------------------
# Tabla para el avatar del amigo imaginario
# Un perfil por usuario
# --------------------------------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS imaginary_friend_profile (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL UNIQUE,
            face_shape TEXT NOT NULL DEFAULT 'redondo',
            primary_color TEXT NOT NULL DEFAULT 'azul',
            hair_style TEXT NOT NULL DEFAULT 'corto',
            hair_color TEXT NOT NULL DEFAULT 'castano',
            eye_style TEXT NOT NULL DEFAULT 'felices',
            mouth_style TEXT NOT NULL DEFAULT 'sonrisa',
            accessory TEXT NOT NULL DEFAULT 'estrella',
            background_style TEXT NOT NULL DEFAULT 'cielo',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );
        """)

    # --------------------------------------------------------
    # Tabla de conversaciones
    # --------------------------------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            module TEXT NOT NULL,
            title TEXT NOT NULL DEFAULT 'Nueva conversación',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );
    """)

    # --------------------------------------------------------
    # Tabla de mensajes
    # --------------------------------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conversation_id INTEGER NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
        );
    """)

    # --------------------------------------------------------
    # Tabla de artículos
    # --------------------------------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            category TEXT NOT NULL,
            reader_type TEXT NOT NULL,
            short_description TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
    """)
    # --------------------------------------------------------
# Tabla de feedback por respuesta del asistente
# - rating: 1 = útil, 0 = no útil
# - un usuario puede calificar una sola vez cada mensaje
# --------------------------------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS message_feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            conversation_id INTEGER NOT NULL,
            module TEXT NOT NULL,
            rating INTEGER NOT NULL CHECK (rating IN (0, 1)),
            comment TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(message_id, user_id),
            FOREIGN KEY (message_id) REFERENCES messages(id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
        );
    """)

    connection.commit()
    

    # --------------------------------------------------------
    # Migraciones simples de columnas
    # --------------------------------------------------------
    if not column_exists("conversations", "user_id"):
        cursor.execute("""
            ALTER TABLE conversations
            ADD COLUMN user_id INTEGER;
        """)
        connection.commit()

    if not column_exists("users", "is_admin"):
        cursor.execute("""
            ALTER TABLE users
            ADD COLUMN is_admin INTEGER NOT NULL DEFAULT 0;
        """)
        connection.commit()
    if not column_exists("users", "friend_name"):
        cursor.execute("""
            ALTER TABLE users
            ADD COLUMN friend_name TEXT NOT NULL DEFAULT 'Lumi';
        """)
        connection.commit()
    # --------------------------------------------------------
# Migraciones para memoria suave del vínculo
# --------------------------------------------------------
    if not column_exists("users", "favorite_color"):
        cursor.execute("""
        ALTER TABLE users
        ADD COLUMN favorite_color TEXT NOT NULL DEFAULT '';
    """)
    connection.commit()

    if not column_exists("users", "favorite_activity"):
        cursor.execute("""
        ALTER TABLE users
        ADD COLUMN favorite_activity TEXT NOT NULL DEFAULT '';
    """)
    connection.commit()

    if not column_exists("users", "encouragement_style"):
        cursor.execute("""
        ALTER TABLE users
        ADD COLUMN encouragement_style TEXT NOT NULL DEFAULT '';
    """)
    connection.commit()

    if not column_exists("users", "preferred_comfort"):
        cursor.execute("""
        ALTER TABLE users
        ADD COLUMN preferred_comfort TEXT NOT NULL DEFAULT 'cuentos';
    """)
    connection.commit()

    # --------------------------------------------------------
# Migraciones para autenticación con Google
# --------------------------------------------------------
    if not column_exists("users", "google_sub"):
        cursor.execute("""
        ALTER TABLE users
        ADD COLUMN google_sub TEXT;
        """)
    connection.commit()

    if not column_exists("users", "auth_provider"):
        cursor.execute("""
        ALTER TABLE users
        ADD COLUMN auth_provider TEXT NOT NULL DEFAULT 'local';
        """)
    connection.commit()

# --------------------------------------------------------
# Índice único para google_sub cuando exista
# --------------------------------------------------------
    cursor.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS idx_users_google_sub
        ON users(google_sub)
        WHERE google_sub IS NOT NULL;
    """)
    connection.commit()
    # --------------------------------------------------------
    # Índices
    # --------------------------------------------------------

# Índices para favoritos de biblioteca
# --------------------------------------------------------
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_article_favorites_user
        ON article_favorites(user_id, created_at DESC);
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_article_favorites_article
        ON article_favorites(article_id);
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_users_username
        ON users(username);
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_users_admin
        ON users(is_admin);
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_conversations_user_module_updated
        ON conversations(user_id, module, updated_at DESC);
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_imaginary_friend_user
        ON imaginary_friend_profile(user_id);
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_messages_conversation
        ON messages(conversation_id, id ASC);
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_articles_category
        ON articles(category);
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_articles_reader_type
        ON articles(reader_type);
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_articles_title
        ON articles(title);
    """)
    # --------------------------------------------------------
    # Índices para feedback
    # --------------------------------------------------------
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_feedback_message_user
        ON message_feedback(message_id, user_id);
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_feedback_module
        ON message_feedback(module);
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_feedback_created
        ON message_feedback(created_at DESC);
    """)

    connection.commit()

    # --------------------------------------------------------
    # Asegurar que exista al menos un administrador
    # --------------------------------------------------------
    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM users
        WHERE is_admin = 1;
    """)
    total_admins = cursor.fetchone()["total"]

    if total_admins == 0:
        cursor.execute("""
            SELECT id
            FROM users
            ORDER BY id ASC
            LIMIT 1;
        """)
        primer_usuario = cursor.fetchone()

        if primer_usuario:
            cursor.execute("""
                UPDATE users
                SET is_admin = 1
                WHERE id = ?;
            """, (primer_usuario["id"],))
            connection.commit()

    # --------------------------------------------------------
    # Semilla inicial de artículos
    # --------------------------------------------------------
    cursor.execute("SELECT COUNT(*) AS total FROM articles;")
    total_articles = cursor.fetchone()["total"]

    if total_articles == 0:
        seed_default_articles(cursor)
        connection.commit()

    connection.close()

    # --------------------------------------------------------
    # Migración de roles, guests y tokens
    # --------------------------------------------------------
    from database.access_control import initialize_access_control_schema

    initialize_access_control_schema()


# ------------------------------------------------------------
# Sembrar artículos base
# ------------------------------------------------------------
def seed_default_articles(cursor: sqlite3.Cursor) -> None:
    """
    Inserta artículos base en la biblioteca.

    Parámetros:
        cursor (sqlite3.Cursor): cursor activo
    """
    articulos = [
        {
            "title": "¿Qué es el TDAH en lenguaje sencillo?",
            "category": "TDAH",
            "reader_type": "Usuario",
            "short_description": "Una explicación clara y simple sobre qué es el TDAH y cómo puede sentirse en el día a día.",
            "content": """
## Idea principal
El TDAH es una forma distinta de procesar la atención, la energía y el impulso.

## Cómo puede sentirse
- A veces cuesta concentrarse por mucho tiempo.
- Puede ser difícil empezar una tarea o terminarla.
- Algunas personas sienten muchas ideas al mismo tiempo.
- También puede haber inquietud, olvido o frustración.

## Algo importante
No significa flojera ni falta de inteligencia. Muchas personas con TDAH son creativas, curiosas y muy capaces.

## Qué puede ayudar
- Dividir una tarea en pasos pequeños
- Usar recordatorios visuales
- Tener pausas cortas
- Trabajar con una sola cosa a la vez
            """.strip()
        },
        {
            "title": "Apoyar a un hijo con TDAH sin caer en regaños constantes",
            "category": "TDAH",
            "reader_type": "Padre/Cuidador",
            "short_description": "Estrategias prácticas para acompañar con más calma y menos confrontación.",
            "content": """
## Qué suele pasar
Muchas conductas del TDAH parecen desobediencia, pero a menudo tienen que ver con dificultad para regular atención, tiempo o impulsos.

## Qué hacer
- Da instrucciones cortas y concretas
- Pide una cosa a la vez
- Usa rutinas visibles
- Revisa avances en pequeños momentos
- Refuerza lo que sí logró, aunque sea parcial

## Qué evitar
- Dar muchas indicaciones al mismo tiempo
- Compararlo con otros
- Pensar que “si quisiera, podría hacerlo siempre”

## Frase útil
“Vamos paso por paso, te ayudo a empezar.”
            """.strip()
        },
        {
            "title": "Autismo: una explicación clara para entenderlo mejor",
            "category": "Autismo",
            "reader_type": "Usuario",
            "short_description": "Una introducción sencilla al autismo, sin tecnicismos innecesarios.",
            "content": """
## Idea principal
El autismo es una forma distinta de percibir, procesar y responder al mundo.

## Puede verse en cosas como
- Necesidad de rutina o previsibilidad
- Sensibilidad a sonidos, luces, texturas o cambios
- Maneras distintas de comunicarse
- Intereses profundos en temas específicos

## Algo importante
No todas las personas autistas son iguales. Cada una tiene necesidades, fortalezas y formas de expresarse distintas.

## Qué puede ayudar
- Avisar cambios con anticipación
- Dar instrucciones claras
- Respetar tiempos de descanso sensorial
- No forzar contacto o interacción de una sola manera
            """.strip()
        },
        {
            "title": "Autismo en el aula: apoyos razonables para docentes",
            "category": "Autismo",
            "reader_type": "Docente",
            "short_description": "Ideas concretas para hacer el aula más clara, predecible e inclusiva.",
            "content": """
## Qué suele ayudar en clase
- Rutina visible en pizarrón o cartel
- Anticipar cambios en actividades
- Instrucciones breves y por pasos
- Opciones de participación variadas

## También es útil
- Permitir pausas reguladoras
- Evitar sobrecarga de estímulos cuando sea posible
- No asumir falta de interés si la respuesta social es distinta
- Dar tiempo adicional para procesar indicaciones

## Meta principal
Crear un entorno comprensible y seguro, no exigir que todos aprendan de la misma forma.
            """.strip()
        },
        {
            "title": "Dislexia: qué es y qué no es",
            "category": "Dislexia",
            "reader_type": "Usuario",
            "short_description": "Una explicación accesible sobre la dislexia y sus efectos en lectura y escritura.",
            "content": """
## Idea principal
La dislexia es una dificultad específica relacionada con la lectura y, a veces, con la escritura.

## Puede pasar que
- Leer tome más tiempo
- Algunas palabras se confundan
- Escribir correctamente cueste más
- Haya cansancio rápido al leer mucho texto

## Lo que no significa
- No significa baja inteligencia
- No significa falta de esfuerzo
- No significa que la persona no pueda aprender

## Qué puede ayudar
- Texto con buen espaciado
- Lectura acompañada
- Apoyos visuales
- Tiempo extra en tareas de lectura
            """.strip()
        },
        {
            "title": "Ansiedad y neurodivergencia: cuando el cuerpo se siente sobrepasado",
            "category": "Ansiedad",
            "reader_type": "Usuario",
            "short_description": "Cómo reconocer la ansiedad de forma sencilla y algunas ideas básicas de apoyo.",
            "content": """
## Cómo puede sentirse
La ansiedad puede sentirse como tensión, aceleración, preocupación intensa o dificultad para relajarse.

## A veces aparece como
- Pensar demasiado en lo que puede salir mal
- Sentirse en alerta
- Querer evitar ciertas situaciones
- Cansancio después de estar en entornos exigentes

## Qué puede ayudar
- Respirar más lento
- Tomar una pausa en un lugar tranquilo
- Poner en palabras lo que está pasando
- Reducir estímulos por un momento

## Importante
Si la ansiedad interfiere mucho en la vida diaria, conviene buscar orientación profesional.
            """.strip()
        },
        {
            "title": "Cómo acompañar una crisis de frustración sin empeorarla",
            "category": "Regulación emocional",
            "reader_type": "Padre/Cuidador",
            "short_description": "Pasos concretos para acompañar con calma durante una crisis de frustración.",
            "content": """
## En el momento de la crisis
- Baja el tono de voz
- Reduce instrucciones largas
- Da espacio físico seguro
- Prioriza seguridad y regulación antes que explicación

## Qué decir
- “Estoy aquí contigo.”
- “Vamos paso por paso.”
- “Primero nos calmamos, luego hablamos.”

## Qué evitar
- Discutir en medio del pico emocional
- Hacer muchas preguntas
- Exigir razonamiento inmediato

## Después
Cuando baje la intensidad, revisen qué detonó la situación y qué podría ayudar la próxima vez.
            """.strip()
        },
        {
            "title": "Señales de sobrecarga sensorial y cómo responder en casa",
            "category": "Regulación emocional",
            "reader_type": "Padre/Cuidador",
            "short_description": "Guía breve para reconocer sobrecarga sensorial y responder con más claridad.",
            "content": """
## Posibles señales
- Irritabilidad repentina
- Cubrirse oídos
- Necesidad urgente de salir de un lugar
- Llanto o enojo por estímulos que parecen pequeños

## Qué puede ayudar
- Bajar ruido o luces
- Ofrecer un espacio tranquilo
- Hablar poco y claro
- Permitir recuperación antes de seguir con exigencias

## Idea importante
No siempre es berrinche. A veces el entorno se volvió demasiado intenso para el sistema nervioso.
            """.strip()
        }
    ]

    for articulo in articulos:
        cursor.execute("""
            INSERT INTO articles (
                title,
                category,
                reader_type,
                short_description,
                content
            )
            VALUES (?, ?, ?, ?, ?);
        """, (
            articulo["title"],
            articulo["category"],
            articulo["reader_type"],
            articulo["short_description"],
            articulo["content"]
        ))


# ------------------------------------------------------------
# Normalizar username
# ------------------------------------------------------------
def normalize_username(username: str) -> str:
    """
    Limpia y normaliza el username.

    Parámetros:
        username (str): nombre de usuario

    Retorna:
        str: username normalizado
    """
    return username.strip().lower()


# ------------------------------------------------------------
# Normalizar texto genérico
# ------------------------------------------------------------
def normalize_text(value: str) -> str:
    """
    Limpia espacios innecesarios de un texto.

    Parámetros:
        value (str): texto a normalizar

    Retorna:
        str: texto limpio
    """
    return " ".join(str(value or "").strip().split())


# ------------------------------------------------------------
# Crear hash seguro de contraseña
# ------------------------------------------------------------
def hash_password(password: str, salt: Optional[bytes] = None) -> str:
    """
    Genera un hash seguro usando PBKDF2-HMAC.

    Parámetros:
        password (str): contraseña en texto plano
        salt (Optional[bytes]): salt opcional

    Retorna:
        str: salt y hash en hexadecimal
    """
    if salt is None:
        salt = secrets.token_bytes(16)

    derived_key = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        200_000
    )

    return f"{salt.hex()}${derived_key.hex()}"


# ------------------------------------------------------------
# Verificar contraseña
# ------------------------------------------------------------
def verify_password(password: str, stored_hash: str) -> bool:
    """
    Verifica si una contraseña coincide con el hash guardado.

    Parámetros:
        password (str): contraseña en texto plano
        stored_hash (str): hash almacenado

    Retorna:
        bool: True si coincide, False si no
    """
    try:
        salt_hex, hash_hex = stored_hash.split("$", 1)
        salt = bytes.fromhex(salt_hex)

        recalculated = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            200_000
        ).hex()

        return hmac.compare_digest(recalculated, hash_hex)
    except Exception:
        return False



# ------------------------------------------------------------
# Obtener usuario por username
# ------------------------------------------------------------
def get_user_by_username(username: str) -> Optional[dict]:
    """
    Busca un usuario por username.

    Parámetros:
        username (str): username a buscar

    Retorna:
        Optional[dict]: usuario o None
    """
    username_normalized = normalize_username(username)

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            id,
            username,
            display_name,
            is_admin,
            friend_name,
            favorite_color,
            favorite_activity,
            encouragement_style,
            preferred_comfort,
            created_at
        FROM users
        WHERE username = ?;
    """, (username_normalized,))

    row = cursor.fetchone()
    connection.close()

    if not row:
        return None

    user = {
        "id": row["id"],
        "username": row["username"],
        "display_name": row["display_name"],
        "is_admin": bool(row["is_admin"]),
        "friend_name": row["friend_name"] or "Lumi",
        "favorite_color": row["favorite_color"] or "",
        "favorite_activity": row["favorite_activity"] or "",
        "encouragement_style": row["encouragement_style"] or "",
        "preferred_comfort": row["preferred_comfort"] or "cuentos",
        "created_at": row["created_at"]
    }

    # --------------------------------------------------------
    # Validar cuenta activa / guest vigente y decorar con rol.
    # --------------------------------------------------------
    from database.access_control import (
        decorate_user_for_access,
        mark_user_login,
        validate_user_can_login,
    )

    validate_user_can_login(user["id"])
    mark_user_login(user["id"])

    return decorate_user_for_access(user)

# ------------------------------------------------------------
# Obtener usuario por id
# ------------------------------------------------------------
def get_user_by_id(user_id: int) -> Optional[dict]:
    """
    Busca un usuario por su id.

    Parámetros:
        user_id (int): id del usuario

    Retorna:
        Optional[dict]: usuario o None
    """
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            id,
            username,
            display_name,
            is_admin,
            friend_name,
            favorite_color,
            favorite_activity,
            encouragement_style,
            preferred_comfort,
            created_at
        FROM users
        WHERE id = ?;
    """, (user_id,))

    row = cursor.fetchone()
    connection.close()

    if not row:
        return None

    return {
        "id": row["id"],
        "username": row["username"],
        "display_name": row["display_name"],
        "is_admin": bool(row["is_admin"]),
        "friend_name": row["friend_name"] or "Lumi",
        "favorite_color": row["favorite_color"] or "",
        "favorite_activity": row["favorite_activity"] or "",
        "encouragement_style": row["encouragement_style"] or "",
        "preferred_comfort": row["preferred_comfort"] or "cuentos",
        "created_at": row["created_at"]
    }

# ------------------------------------------------------------
# Crear usuario
# ------------------------------------------------------------
def create_user(username: str, password: str, display_name: str = "") -> dict:
    """
    Crea un usuario nuevo.

    Parámetros:
        username (str): username único
        password (str): contraseña en texto plano
        display_name (str): nombre visible opcional

    Retorna:
        dict: usuario creado
    """
    username_normalized = normalize_username(username)
    display_name_clean = display_name.strip() or username_normalized

    if not username_normalized:
        raise ValueError("El nombre de usuario es obligatorio.")

    if len(username_normalized) < 3:
        raise ValueError("El nombre de usuario debe tener al menos 3 caracteres.")

    if len(password) < 8:
        raise ValueError("La contraseña debe tener al menos 8 caracteres.")

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT id
        FROM users
        WHERE username = ?;
    """, (username_normalized,))

    if cursor.fetchone():
        connection.close()
        raise ValueError("Ese nombre de usuario ya está en uso.")

    # --------------------------------------------------------
    # Determinar si este usuario debe ser administrador
    # --------------------------------------------------------
    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM users
        WHERE is_admin = 1;
    """)
    total_admins = cursor.fetchone()["total"]
    is_admin = 1 if total_admins == 0 else 0

    password_hash = hash_password(password)

    cursor.execute("""
        INSERT INTO users (
            username,
            display_name,
            password_hash,
            is_admin,
            friend_name,
            favorite_color,
            favorite_activity,
            encouragement_style,
            preferred_comfort
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
    """, (
        username_normalized,
        display_name_clean,
        password_hash,
        is_admin,
        "Lumi",
        "",
        "",
        "",
        "cuentos"
    ))

    user_id = cursor.lastrowid

    # --------------------------------------------------------
    # Compatibilidad con el nuevo control de roles.
    # El primer usuario sigue siendo superadmin.
    # --------------------------------------------------------
    try:
        cursor.execute("""
            UPDATE users
            SET role = ?,
                account_type = 'permanent',
                guest_status = 'none',
                is_active = 1
            WHERE id = ?;
        """, ("superadmin" if is_admin else "child", user_id))
    except sqlite3.OperationalError:
        # Si la migración aún no existe, se aplicará al iniciar la app.
        pass

    connection.commit()
    connection.close()

    usuario = get_user_by_id(user_id)

    if not usuario:
        raise ValueError("No se pudo recuperar el usuario recién creado.")

    return usuario
# ------------------------------------------------------------
# Autenticar usuario
# ------------------------------------------------------------
# ------------------------------------------------------------
# Autenticar usuario
# ------------------------------------------------------------
def authenticate_user(username: str, password: str) -> Optional[dict]:
    """
    Verifica credenciales de un usuario.

    Parámetros:
        username (str): username
        password (str): contraseña

    Retorna:
        Optional[dict]: usuario autenticado o None
    """
    username_normalized = normalize_username(username)

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            id,
            username,
            display_name,
            password_hash,
            is_admin,
            friend_name,
            favorite_color,
            favorite_activity,
            encouragement_style,
            preferred_comfort,
            created_at
        FROM users
        WHERE username = ?;
    """, (username_normalized,))

    row = cursor.fetchone()
    connection.close()

    if not row:
        return None

    if not verify_password(password, row["password_hash"]):
        return None

    return {
        "id": row["id"],
        "username": row["username"],
        "display_name": row["display_name"],
        "is_admin": bool(row["is_admin"]),
        "friend_name": row["friend_name"] or "Lumi",
        "favorite_color": row["favorite_color"] or "",
        "favorite_activity": row["favorite_activity"] or "",
        "encouragement_style": row["encouragement_style"] or "",
        "preferred_comfort": row["preferred_comfort"] or "cuentos",
        "created_at": row["created_at"]
    }
# ------------------------------------------------------------
# Crear conversación
# ------------------------------------------------------------
def create_conversation(user_id: int, module: str, title: str = "Nueva conversación") -> int:
    """
    Crea una conversación nueva para un usuario y módulo.

    Parámetros:
        user_id (int): id del usuario
        module (str): módulo
        title (str): título inicial

    Retorna:
        int: id de la conversación creada
    """
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO conversations (user_id, module, title)
        VALUES (?, ?, ?);
    """, (user_id, module, title))

    conversation_id = cursor.lastrowid

    connection.commit()
    connection.close()

    return conversation_id


# ------------------------------------------------------------
# Obtener conversación por id
# ------------------------------------------------------------
def get_conversation_by_id(conversation_id: int, user_id: int) -> Optional[dict]:
    """
    Obtiene una conversación asegurando que pertenezca al usuario.

    Parámetros:
        conversation_id (int): id de la conversación
        user_id (int): id del usuario

    Retorna:
        Optional[dict]: conversación o None
    """
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT id, user_id, module, title, created_at, updated_at
        FROM conversations
        WHERE id = ? AND user_id = ?;
    """, (conversation_id, user_id))

    row = cursor.fetchone()
    connection.close()

    if not row:
        return None

    return {
        "id": row["id"],
        "user_id": row["user_id"],
        "module": row["module"],
        "title": row["title"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"]
    }


# ------------------------------------------------------------
# Obtener mensajes de una conversación
# ------------------------------------------------------------
def get_messages_by_conversation(conversation_id: int, user_id: int) -> list[dict]:
    """
    Obtiene todos los mensajes de una conversación del usuario.

    Parámetros:
        conversation_id (int): id de la conversación
        user_id (int): id del usuario

    Retorna:
        list[dict]: lista de mensajes
    """
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT m.id, m.role, m.content, m.created_at
        FROM messages m
        INNER JOIN conversations c
            ON c.id = m.conversation_id
        WHERE m.conversation_id = ?
          AND c.user_id = ?
        ORDER BY m.id ASC;
    """, (conversation_id, user_id))

    rows = cursor.fetchall()
    connection.close()

    return [
        {
            "id": row["id"],
            "role": row["role"],
            "content": row["content"],
            "created_at": row["created_at"]
        }
        for row in rows
    ]


# ------------------------------------------------------------
# Obtener última conversación por módulo
# ------------------------------------------------------------
def get_latest_conversation_by_module(user_id: int, module: str) -> Optional[dict]:
    """
    Obtiene la conversación más reciente del usuario para un módulo.

    Parámetros:
        user_id (int): id del usuario
        module (str): módulo

    Retorna:
        Optional[dict]: conversación o None
    """
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT id, user_id, module, title, created_at, updated_at
        FROM conversations
        WHERE user_id = ? AND module = ?
        ORDER BY updated_at DESC, id DESC
        LIMIT 1;
    """, (user_id, module))

    row = cursor.fetchone()
    connection.close()

    if not row:
        return None

    return {
        "id": row["id"],
        "user_id": row["user_id"],
        "module": row["module"],
        "title": row["title"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"]
    }


# ------------------------------------------------------------
# Listar conversaciones por módulo
# ------------------------------------------------------------
def list_conversations_by_module(user_id: int, module: str, limit: int = 30) -> list[dict]:
    """
    Lista conversaciones de un usuario dentro de un módulo.

    Parámetros:
        user_id (int): id del usuario
        module (str): módulo
        limit (int): máximo de conversaciones

    Retorna:
        list[dict]: conversaciones
    """
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT id, user_id, module, title, created_at, updated_at
        FROM conversations
        WHERE user_id = ? AND module = ?
        ORDER BY updated_at DESC, id DESC
        LIMIT ?;
    """, (user_id, module, limit))

    rows = cursor.fetchall()
    connection.close()

    return [
        {
            "id": row["id"],
            "user_id": row["user_id"],
            "module": row["module"],
            "title": row["title"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"]
        }
        for row in rows
    ]


# ------------------------------------------------------------
# Guardar mensaje
# ------------------------------------------------------------
def add_message(conversation_id: int, role: str, content: str) -> int:
    """
    Guarda un mensaje en una conversación.

    Parámetros:
        conversation_id (int): id de la conversación
        role (str): user o assistant
        content (str): contenido

    Retorna:
        int: id del mensaje creado
    """
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO messages (conversation_id, role, content)
        VALUES (?, ?, ?);
    """, (conversation_id, role, content))

    message_id = cursor.lastrowid

    cursor.execute("""
        UPDATE conversations
        SET updated_at = CURRENT_TIMESTAMP
        WHERE id = ?;
    """, (conversation_id,))

    connection.commit()
    connection.close()

    return message_id


# ------------------------------------------------------------
# Actualizar título si sigue por defecto
# ------------------------------------------------------------
def update_title_if_default(conversation_id: int, user_id: int, user_message: str) -> None:
    """
    Si la conversación sigue con título por defecto, la renombra
    usando el primer mensaje del usuario.

    Parámetros:
        conversation_id (int): id de la conversación
        user_id (int): id del usuario
        user_message (str): mensaje del usuario
    """
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT title
        FROM conversations
        WHERE id = ? AND user_id = ?;
    """, (conversation_id, user_id))

    row = cursor.fetchone()

    if row and row["title"] == "Nueva conversación":
        title = " ".join(user_message.strip().split())

        if len(title) > 50:
            title = f"{title[:50].rstrip()}..."

        cursor.execute("""
            UPDATE conversations
            SET title = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ? AND user_id = ?;
        """, (title, conversation_id, user_id))

        connection.commit()

    connection.close()


# ------------------------------------------------------------
# Listar categorías de artículos
# ------------------------------------------------------------
def list_article_categories() -> list[str]:
    """
    Devuelve categorías disponibles en la biblioteca.

    Retorna:
        list[str]: categorías
    """
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT DISTINCT category
        FROM articles
        ORDER BY category ASC;
    """)

    rows = cursor.fetchall()
    connection.close()

    return [row["category"] for row in rows]


# ------------------------------------------------------------
# Listar tipos de lector
# ------------------------------------------------------------
def list_reader_types() -> list[str]:
    """
    Devuelve tipos de lector disponibles.

    Retorna:
        list[str]: tipos de lector
    """
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT DISTINCT reader_type
        FROM articles
        ORDER BY reader_type ASC;
    """)

    rows = cursor.fetchall()
    connection.close()

    return [row["reader_type"] for row in rows]


# ------------------------------------------------------------
# Buscar artículos
# ------------------------------------------------------------
def search_articles(
    search_text: str = "",
    category: str = "Todas",
    reader_type: str = "Todos",
    limit: int = 50
) -> list[dict]:
    """
    Busca artículos por texto, categoría y tipo de lector.

    Parámetros:
        search_text (str): texto de búsqueda
        category (str): categoría o "Todas"
        reader_type (str): tipo de lector o "Todos"
        limit (int): máximo de resultados

    Retorna:
        list[dict]: artículos encontrados
    """
    connection = get_connection()
    cursor = connection.cursor()

    query = """
        SELECT id, title, category, reader_type, short_description, content, created_at
        FROM articles
        WHERE 1 = 1
    """
    params = []

    if search_text.strip():
        texto = f"%{search_text.strip()}%"
        query += """
            AND (
                title LIKE ?
                OR short_description LIKE ?
                OR content LIKE ?
            )
        """
        params.extend([texto, texto, texto])

    if category != "Todas":
        query += " AND category = ? "
        params.append(category)

    if reader_type != "Todos":
        query += " AND reader_type = ? "
        params.append(reader_type)

    query += """
        ORDER BY category ASC, title ASC
        LIMIT ?
    """
    params.append(limit)

    cursor.execute(query, params)
    rows = cursor.fetchall()
    connection.close()

    return [
        {
            "id": row["id"],
            "title": row["title"],
            "category": row["category"],
            "reader_type": row["reader_type"],
            "short_description": row["short_description"],
            "content": row["content"],
            "created_at": row["created_at"]
        }
        for row in rows
    ]


# ------------------------------------------------------------
# Listar todos los artículos
# ------------------------------------------------------------
def list_all_articles(limit: int = 5000) -> list[dict]:
    """
    Devuelve todos los artículos hasta un límite dado.

    Parámetros:
        limit (int): máximo de artículos

    Retorna:
        list[dict]: artículos
    """
    return search_articles(limit=limit)


# ------------------------------------------------------------
# Obtener artículo por id
# ------------------------------------------------------------
def get_article_by_id(article_id: int) -> Optional[dict]:
    """
    Obtiene un artículo por su id.

    Parámetros:
        article_id (int): id del artículo

    Retorna:
        Optional[dict]: artículo o None
    """
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT id, title, category, reader_type, short_description, content, created_at
        FROM articles
        WHERE id = ?;
    """, (article_id,))

    row = cursor.fetchone()
    connection.close()

    if not row:
        return None

    return {
        "id": row["id"],
        "title": row["title"],
        "category": row["category"],
        "reader_type": row["reader_type"],
        "short_description": row["short_description"],
        "content": row["content"],
        "created_at": row["created_at"]
    }


# ------------------------------------------------------------
# Buscar artículo por clave lógica
# ------------------------------------------------------------
def find_article_by_unique_fields(title: str, category: str, reader_type: str) -> Optional[dict]:
    """
    Busca un artículo por combinación de título, categoría y tipo
    de lector.

    Parámetros:
        title (str): título
        category (str): categoría
        reader_type (str): tipo de lector

    Retorna:
        Optional[dict]: artículo encontrado o None
    """
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT id, title, category, reader_type, short_description, content, created_at
        FROM articles
        WHERE title = ? AND category = ? AND reader_type = ?
        LIMIT 1;
    """, (
        normalize_text(title),
        normalize_text(category),
        normalize_text(reader_type)
    ))

    row = cursor.fetchone()
    connection.close()

    if not row:
        return None

    return {
        "id": row["id"],
        "title": row["title"],
        "category": row["category"],
        "reader_type": row["reader_type"],
        "short_description": row["short_description"],
        "content": row["content"],
        "created_at": row["created_at"]
    }


# ------------------------------------------------------------
# Crear artículo
# ------------------------------------------------------------
def create_article(
    title: str,
    category: str,
    reader_type: str,
    short_description: str,
    content: str
) -> int:
    """
    Crea un artículo nuevo en la biblioteca.

    Parámetros:
        title (str): título
        category (str): categoría
        reader_type (str): tipo de lector
        short_description (str): resumen breve
        content (str): contenido completo

    Retorna:
        int: id del artículo creado
    """
    validar_articulo(
        title=title,
        category=category,
        reader_type=reader_type,
        short_description=short_description,
        content=content
    )

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO articles (
            title,
            category,
            reader_type,
            short_description,
            content
        )
        VALUES (?, ?, ?, ?, ?);
    """, (
        normalize_text(title),
        normalize_text(category),
        normalize_text(reader_type),
        short_description.strip(),
        content.strip()
    ))

    article_id = cursor.lastrowid

    connection.commit()
    connection.close()

    return article_id


# ------------------------------------------------------------
# Actualizar artículo
# ------------------------------------------------------------
def update_article(
    article_id: int,
    title: str,
    category: str,
    reader_type: str,
    short_description: str,
    content: str
) -> None:
    """
    Actualiza un artículo existente.

    Parámetros:
        article_id (int): id del artículo
        title (str): título
        category (str): categoría
        reader_type (str): tipo de lector
        short_description (str): resumen breve
        content (str): contenido completo
    """
    validar_articulo(
        title=title,
        category=category,
        reader_type=reader_type,
        short_description=short_description,
        content=content
    )

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        UPDATE articles
        SET title = ?,
            category = ?,
            reader_type = ?,
            short_description = ?,
            content = ?
        WHERE id = ?;
    """, (
        normalize_text(title),
        normalize_text(category),
        normalize_text(reader_type),
        short_description.strip(),
        content.strip(),
        article_id
    ))

    connection.commit()
    connection.close()


# ------------------------------------------------------------
# Eliminar artículo
# ------------------------------------------------------------
def delete_article(article_id: int) -> None:
    """
    Elimina un artículo de la biblioteca.

    Parámetros:
        article_id (int): id del artículo
    """
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        DELETE FROM articles
        WHERE id = ?;
    """, (article_id,))

    connection.commit()
    connection.close()


# ------------------------------------------------------------
# Validar datos del artículo
# ------------------------------------------------------------
def validar_articulo(
    title: str,
    category: str,
    reader_type: str,
    short_description: str,
    content: str
) -> None:
    """
    Valida los campos mínimos de un artículo.

    Lanza:
        ValueError: si falta información importante
    """
    if not normalize_text(title):
        raise ValueError("El título es obligatorio.")

    if not normalize_text(category):
        raise ValueError("La categoría es obligatoria.")

    if not normalize_text(reader_type):
        raise ValueError("El tipo de lector es obligatorio.")

    if len(short_description.strip()) < 10:
        raise ValueError("La descripción breve debe tener al menos 10 caracteres.")

    if len(content.strip()) < 30:
        raise ValueError("El contenido del artículo es demasiado corto.")


# ------------------------------------------------------------
# Importar artículos en lote
# ------------------------------------------------------------
def import_articles(records: list[dict], duplicate_mode: str = "skip") -> dict:
    """
    Importa artículos en lote desde una lista de registros.

    Parámetros:
        records (list[dict]): registros a importar
        duplicate_mode (str): skip, replace o allow

    Retorna:
        dict: resumen de la importación
    """
    if duplicate_mode not in {"skip", "replace", "allow"}:
        raise ValueError("Modo de duplicados no válido.")

    summary = {
        "created": 0,
        "updated": 0,
        "skipped": 0,
        "errors": []
    }

    connection = get_connection()
    cursor = connection.cursor()

    for index, record in enumerate(records, start=1):
        try:
            title = normalize_text(record.get("title", ""))
            category = normalize_text(record.get("category", ""))
            reader_type = normalize_text(record.get("reader_type", ""))
            short_description = str(record.get("short_description", "")).strip()
            content = str(record.get("content", "")).strip()

            validar_articulo(
                title=title,
                category=category,
                reader_type=reader_type,
                short_description=short_description,
                content=content
            )

            cursor.execute("""
                SELECT id
                FROM articles
                WHERE title = ? AND category = ? AND reader_type = ?
                LIMIT 1;
            """, (title, category, reader_type))

            existing = cursor.fetchone()

            # Omitir duplicados
            if existing and duplicate_mode == "skip":
                summary["skipped"] += 1
                continue

            # Reemplazar duplicados
            if existing and duplicate_mode == "replace":
                cursor.execute("""
                    UPDATE articles
                    SET short_description = ?,
                        content = ?
                    WHERE id = ?;
                """, (short_description, content, existing["id"]))
                summary["updated"] += 1
                continue

            # Permitir duplicados o crear si no existe
            cursor.execute("""
                INSERT INTO articles (
                    title,
                    category,
                    reader_type,
                    short_description,
                    content
                )
                VALUES (?, ?, ?, ?, ?);
            """, (title, category, reader_type, short_description, content))

            summary["created"] += 1

        except ValueError as error:
            summary["errors"].append(f"Fila {index}: {error}")
        except Exception as error:
            summary["errors"].append(f"Fila {index}: {error}")

    connection.commit()
    connection.close()

    return summary


# ------------------------------------------------------------
# Listar todos los usuarios
# ------------------------------------------------------------
def list_users(limit: int = 100) -> list[dict]:
    """
    Lista usuarios del sistema.

    Parámetros:
        limit (int): máximo de resultados

    Retorna:
        list[dict]: usuarios
    """
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT id, username, display_name, is_admin, created_at
        FROM users
        ORDER BY id ASC
        LIMIT ?;
    """, (limit,))

    rows = cursor.fetchall()
    connection.close()

    return [
        {
            "id": row["id"],
            "username": row["username"],
            "display_name": row["display_name"],
            "is_admin": bool(row["is_admin"]),
            "created_at": row["created_at"]
        }
        for row in rows
    ]


# ------------------------------------------------------------
# Cambiar rol de administrador
# ------------------------------------------------------------
def set_user_admin_status(user_id: int, is_admin: bool) -> None:
    """
    Cambia el estado de administrador de un usuario.

    Parámetros:
        user_id (int): id del usuario
        is_admin (bool): nuevo estado
    """
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        UPDATE users
        SET is_admin = ?
        WHERE id = ?;
    """, (1 if is_admin else 0, user_id))

    connection.commit()
    connection.close()

# ============================================================
# Funciones de feedback y métricas
# ============================================================

def save_message_feedback(
    message_id: int,
    user_id: int,
    conversation_id: int,
    module: str,
    rating: int,
    comment: str = ""
) -> None:
    """
    Guarda o actualiza el feedback de un usuario sobre una
    respuesta del asistente.

    Parámetros:
        message_id (int): id del mensaje del asistente
        user_id (int): id del usuario que califica
        conversation_id (int): conversación asociada
        module (str): módulo donde ocurrió la respuesta
        rating (int): 1 útil, 0 no útil
        comment (str): comentario opcional
    """
    if rating not in (0, 1):
        raise ValueError("El rating debe ser 0 o 1.")

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO message_feedback (
            message_id,
            user_id,
            conversation_id,
            module,
            rating,
            comment
        )
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(message_id, user_id)
        DO UPDATE SET
            rating = excluded.rating,
            comment = excluded.comment,
            updated_at = CURRENT_TIMESTAMP;
    """, (
        message_id,
        user_id,
        conversation_id,
        module,
        rating,
        comment.strip()
    ))

    connection.commit()
    connection.close()


def get_feedback_for_message(message_id: int, user_id: int) -> Optional[dict]:
    """
    Obtiene el feedback guardado por un usuario para un mensaje.

    Parámetros:
        message_id (int): id del mensaje
        user_id (int): id del usuario

    Retorna:
        Optional[dict]: feedback o None
    """
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT id, message_id, user_id, conversation_id, module, rating, comment, created_at, updated_at
        FROM message_feedback
        WHERE message_id = ? AND user_id = ?;
    """, (message_id, user_id))

    row = cursor.fetchone()
    connection.close()

    if not row:
        return None

    return {
        "id": row["id"],
        "message_id": row["message_id"],
        "user_id": row["user_id"],
        "conversation_id": row["conversation_id"],
        "module": row["module"],
        "rating": row["rating"],
        "comment": row["comment"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def get_feedback_summary(module: str | None = None) -> dict:
    """
    Devuelve un resumen global o por módulo de las calificaciones.

    Parámetros:
        module (str | None): módulo opcional

    Retorna:
        dict: resumen de métricas
    """
    connection = get_connection()
    cursor = connection.cursor()

    query = """
        SELECT
            COUNT(*) AS total,
            SUM(CASE WHEN rating = 1 THEN 1 ELSE 0 END) AS positivos,
            SUM(CASE WHEN rating = 0 THEN 1 ELSE 0 END) AS negativos
        FROM message_feedback
    """
    params = []

    if module:
        query += " WHERE module = ? "
        params.append(module)

    cursor.execute(query, params)
    row = cursor.fetchone()
    connection.close()

    total = int(row["total"] or 0)
    positivos = int(row["positivos"] or 0)
    negativos = int(row["negativos"] or 0)
    porcentaje_util = round((positivos / total) * 100, 1) if total > 0 else 0.0

    return {
        "total": total,
        "positivos": positivos,
        "negativos": negativos,
        "porcentaje_util": porcentaje_util,
    }


def list_feedback_summary_by_module() -> list[dict]:
    """
    Devuelve métricas agrupadas por módulo.

    Retorna:
        list[dict]: resumen por módulo
    """
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            module,
            COUNT(*) AS total,
            SUM(CASE WHEN rating = 1 THEN 1 ELSE 0 END) AS positivos,
            SUM(CASE WHEN rating = 0 THEN 1 ELSE 0 END) AS negativos
        FROM message_feedback
        GROUP BY module
        ORDER BY module ASC;
    """)

    rows = cursor.fetchall()
    connection.close()

    resultados = []

    for row in rows:
        total = int(row["total"] or 0)
        positivos = int(row["positivos"] or 0)
        negativos = int(row["negativos"] or 0)
        porcentaje_util = round((positivos / total) * 100, 1) if total > 0 else 0.0

        resultados.append({
            "module": row["module"],
            "total": total,
            "positivos": positivos,
            "negativos": negativos,
            "porcentaje_util": porcentaje_util,
        })

    return resultados


def list_recent_feedback(limit: int = 50) -> list[dict]:
    """
    Lista feedback reciente para revisión administrativa.

    Parámetros:
        limit (int): máximo de registros

    Retorna:
        list[dict]: feedback reciente
    """
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            mf.id,
            mf.module,
            mf.rating,
            mf.comment,
            mf.created_at,
            u.username,
            c.title AS conversation_title,
            m.content AS message_content
        FROM message_feedback mf
        INNER JOIN users u
            ON u.id = mf.user_id
        INNER JOIN conversations c
            ON c.id = mf.conversation_id
        INNER JOIN messages m
            ON m.id = mf.message_id
        ORDER BY mf.updated_at DESC, mf.id DESC
        LIMIT ?;
    """, (limit,))

    rows = cursor.fetchall()
    connection.close()

    resultados = []

    for row in rows:
        contenido = str(row["message_content"] or "").strip()
        preview = contenido[:160] + "..." if len(contenido) > 160 else contenido

        resultados.append({
            "id": row["id"],
            "module": row["module"],
            "rating": "Útil" if row["rating"] == 1 else "No útil",
            "comment": row["comment"],
            "username": row["username"],
            "conversation_title": row["conversation_title"],
            "message_preview": preview,
            "created_at": row["created_at"],
        })

    return resultados
# ============================================================
# Funciones para el nombre del amigo imaginario
# ============================================================

# ------------------------------------------------------------
# Obtener nombre del amigo imaginario
# ------------------------------------------------------------
def get_friend_name(user_id: int) -> str:
    """
    Obtiene el nombre guardado del amigo imaginario.

    Parámetros:
        user_id (int): id del usuario

    Retorna:
        str: nombre del amigo imaginario
    """
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT friend_name
        FROM users
        WHERE id = ?;
    """, (user_id,))

    row = cursor.fetchone()
    connection.close()

    if not row:
        return "Lumi"

    return (row["friend_name"] or "Lumi").strip()


# ------------------------------------------------------------
# Actualizar nombre del amigo imaginario
# ------------------------------------------------------------
def update_friend_name(user_id: int, friend_name: str) -> None:
    """
    Guarda el nombre del amigo imaginario para un usuario.

    Parámetros:
        user_id (int): id del usuario
        friend_name (str): nombre nuevo del amigo
    """
    friend_name_clean = " ".join(str(friend_name or "").strip().split())

    if not friend_name_clean:
        raise ValueError("El nombre del amigo imaginario es obligatorio.")

    if len(friend_name_clean) < 2:
        raise ValueError("El nombre debe tener al menos 2 caracteres.")

    if len(friend_name_clean) > 30:
        raise ValueError("El nombre no debe pasar de 30 caracteres.")

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        UPDATE users
        SET friend_name = ?
        WHERE id = ?;
    """, (friend_name_clean, user_id))

    connection.commit()
    connection.close()

# ============================================================
# Funciones para memoria suave del amigo imaginario
# ============================================================

# ------------------------------------------------------------
# Obtener perfil suave del amigo imaginario
# ------------------------------------------------------------
def get_friend_profile(user_id: int) -> dict:
    """
    Obtiene el perfil de memoria suave del usuario.

    Parámetros:
        user_id (int): id del usuario

    Retorna:
        dict: preferencias del vínculo
    """
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            friend_name,
            favorite_color,
            favorite_activity,
            encouragement_style,
            preferred_comfort
        FROM users
        WHERE id = ?;
    """, (user_id,))

    row = cursor.fetchone()
    connection.close()

    if not row:
        return {
            "friend_name": "Lumi",
            "favorite_color": "",
            "favorite_activity": "",
            "encouragement_style": "",
            "preferred_comfort": "cuentos"
        }

    return {
        "friend_name": row["friend_name"] or "Lumi",
        "favorite_color": row["favorite_color"] or "",
        "favorite_activity": row["favorite_activity"] or "",
        "encouragement_style": row["encouragement_style"] or "",
        "preferred_comfort": row["preferred_comfort"] or "cuentos"
    }


# ------------------------------------------------------------
# Actualizar memoria suave del amigo imaginario
# ------------------------------------------------------------
def update_friend_profile(
    user_id: int,
    favorite_color: str,
    favorite_activity: str,
    encouragement_style: str,
    preferred_comfort: str
) -> None:
    """
    Guarda la memoria suave del vínculo para un usuario.

    Parámetros:
        user_id (int): id del usuario
        favorite_color (str): color favorito
        favorite_activity (str): actividad favorita
        encouragement_style (str): cómo le gusta que lo animen
        preferred_comfort (str): cuentos, juegos o respiraciones
    """
    favorite_color_clean = " ".join(str(favorite_color or "").strip().split())
    favorite_activity_clean = " ".join(str(favorite_activity or "").strip().split())
    encouragement_style_clean = " ".join(str(encouragement_style or "").strip().split())
    preferred_comfort_clean = str(preferred_comfort or "").strip().lower()

    # --------------------------------------------------------
    # Validar opción principal de consuelo
    # --------------------------------------------------------
    opciones_validas = {"cuentos", "juegos", "respiraciones"}

    if preferred_comfort_clean not in opciones_validas:
        raise ValueError("La preferencia de apoyo debe ser cuentos, juegos o respiraciones.")

    if len(favorite_color_clean) > 30:
        raise ValueError("El color favorito no debe pasar de 30 caracteres.")

    if len(favorite_activity_clean) > 50:
        raise ValueError("La actividad favorita no debe pasar de 50 caracteres.")

    if len(encouragement_style_clean) > 80:
        raise ValueError("La forma de animarlo no debe pasar de 80 caracteres.")

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        UPDATE users
        SET
            favorite_color = ?,
            favorite_activity = ?,
            encouragement_style = ?,
            preferred_comfort = ?
        WHERE id = ?;
    """, (
        favorite_color_clean,
        favorite_activity_clean,
        encouragement_style_clean,
        preferred_comfort_clean,
        user_id
    ))

    connection.commit()
    connection.close()
# ============================================================
# Funciones para el avatar del amigo imaginario
# ============================================================

# ------------------------------------------------------------
# Perfil visual por defecto del avatar
# ------------------------------------------------------------
DEFAULT_IMAGINARY_FRIEND_AVATAR = {
    "face_shape": "redondo",
    "primary_color": "azul",
    "hair_style": "corto",
    "hair_color": "castano",
    "eye_style": "felices",
    "mouth_style": "sonrisa",
    "accessory": "estrella",
    "background_style": "cielo",
}


# ------------------------------------------------------------
# Crear perfil visual por defecto si no existe
# ------------------------------------------------------------
def ensure_imaginary_friend_profile(user_id: int) -> None:
    """
    Crea el perfil visual por defecto del amigo imaginario si
    el usuario todavía no tiene uno.

    Parámetros:
        user_id (int): id del usuario
    """
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT id
        FROM imaginary_friend_profile
        WHERE user_id = ?;
    """, (user_id,))

    exists = cursor.fetchone()

    if not exists:
        cursor.execute("""
            INSERT INTO imaginary_friend_profile (
                user_id,
                face_shape,
                primary_color,
                hair_style,
                hair_color,
                eye_style,
                mouth_style,
                accessory,
                background_style
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, (
            user_id,
            DEFAULT_IMAGINARY_FRIEND_AVATAR["face_shape"],
            DEFAULT_IMAGINARY_FRIEND_AVATAR["primary_color"],
            DEFAULT_IMAGINARY_FRIEND_AVATAR["hair_style"],
            DEFAULT_IMAGINARY_FRIEND_AVATAR["hair_color"],
            DEFAULT_IMAGINARY_FRIEND_AVATAR["eye_style"],
            DEFAULT_IMAGINARY_FRIEND_AVATAR["mouth_style"],
            DEFAULT_IMAGINARY_FRIEND_AVATAR["accessory"],
            DEFAULT_IMAGINARY_FRIEND_AVATAR["background_style"],
        ))

        connection.commit()

    connection.close()


# ------------------------------------------------------------
# Obtener perfil visual del amigo imaginario
# ------------------------------------------------------------
def get_imaginary_friend_profile(user_id: int) -> dict:
    """
    Obtiene el perfil visual del amigo imaginario.

    Parámetros:
        user_id (int): id del usuario

    Retorna:
        dict: configuración visual del avatar
    """
    ensure_imaginary_friend_profile(user_id)

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            face_shape,
            primary_color,
            hair_style,
            hair_color,
            eye_style,
            mouth_style,
            accessory,
            background_style
        FROM imaginary_friend_profile
        WHERE user_id = ?;
    """, (user_id,))

    row = cursor.fetchone()
    connection.close()

    if not row:
        return dict(DEFAULT_IMAGINARY_FRIEND_AVATAR)

    return {
        "face_shape": row["face_shape"] or "redondo",
        "primary_color": row["primary_color"] or "azul",
        "hair_style": row["hair_style"] or "corto",
        "hair_color": row["hair_color"] or "castano",
        "eye_style": row["eye_style"] or "felices",
        "mouth_style": row["mouth_style"] or "sonrisa",
        "accessory": row["accessory"] or "estrella",
        "background_style": row["background_style"] or "cielo",
    }


# ------------------------------------------------------------
# Actualizar perfil visual del amigo imaginario
# ------------------------------------------------------------
def update_imaginary_friend_profile(
    user_id: int,
    face_shape: str,
    primary_color: str,
    hair_style: str,
    hair_color: str,
    eye_style: str,
    mouth_style: str,
    accessory: str,
    background_style: str
) -> None:
    """
    Guarda la configuración visual del avatar del amigo imaginario.

    Parámetros:
        user_id (int): id del usuario
        face_shape (str): forma de rostro
        primary_color (str): color principal
        hair_style (str): estilo de cabello
        hair_color (str): color de cabello
        eye_style (str): estilo de ojos
        mouth_style (str): estilo de boca
        accessory (str): accesorio
        background_style (str): fondo
    """
    ensure_imaginary_friend_profile(user_id)

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        UPDATE imaginary_friend_profile
        SET
            face_shape = ?,
            primary_color = ?,
            hair_style = ?,
            hair_color = ?,
            eye_style = ?,
            mouth_style = ?,
            accessory = ?,
            background_style = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE user_id = ?;
    """, (
        str(face_shape).strip(),
        str(primary_color).strip(),
        str(hair_style).strip(),
        str(hair_color).strip(),
        str(eye_style).strip(),
        str(mouth_style).strip(),
        str(accessory).strip(),
        str(background_style).strip(),
        user_id
    ))

    connection.commit()
    connection.close()
# ============================================================
# Funciones para login con Google / OIDC
# ============================================================

# ------------------------------------------------------------
# Obtener usuario por google_sub
# ------------------------------------------------------------
def get_user_by_google_sub(google_sub: str) -> Optional[dict]:
    """
    Busca un usuario por el identificador único de Google.

    Parámetros:
        google_sub (str): identificador único devuelto por Google

    Retorna:
        Optional[dict]: usuario encontrado o None
    """
    google_sub_clean = str(google_sub or "").strip()

    if not google_sub_clean:
        return None

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            id,
            username,
            display_name,
            is_admin,
            friend_name,
            favorite_color,
            favorite_activity,
            encouragement_style,
            preferred_comfort,
            created_at
        FROM users
        WHERE google_sub = ?;
    """, (google_sub_clean,))

    row = cursor.fetchone()
    connection.close()

    if not row:
        return None

    return {
        "id": row["id"],
        "username": row["username"],
        "display_name": row["display_name"],
        "is_admin": bool(row["is_admin"]),
        "friend_name": row["friend_name"] or "Lumi",
        "favorite_color": row["favorite_color"] or "",
        "favorite_activity": row["favorite_activity"] or "",
        "encouragement_style": row["encouragement_style"] or "",
        "preferred_comfort": row["preferred_comfort"] or "cuentos",
        "created_at": row["created_at"]
    }


# ------------------------------------------------------------
# Verificar si existe un username
# ------------------------------------------------------------
def username_exists(username: str) -> bool:
    """
    Revisa si un username ya existe en la tabla users.

    Parámetros:
        username (str): nombre de usuario a validar

    Retorna:
        bool: True si ya existe
    """
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT 1
        FROM users
        WHERE username = ?;
    """, (username,))

    exists = cursor.fetchone() is not None
    connection.close()
    return exists


# ------------------------------------------------------------
# Generar username único a partir del email
# ------------------------------------------------------------
def generate_unique_username_from_email(email: str) -> str:
    """
    Genera un username único usando el email de Google.

    Parámetros:
        email (str): correo electrónico del usuario

    Retorna:
        str: username disponible
    """
    email_clean = str(email or "").strip().lower()
    base_username = email_clean or "google_user"

    if not username_exists(base_username):
        return base_username

    counter = 1
    while True:
        candidate = f"{base_username}_{counter}"
        if not username_exists(candidate):
            return candidate
        counter += 1


# ------------------------------------------------------------
# Crear usuario local desde Google
# ------------------------------------------------------------
def create_google_user(google_sub: str, email: str, display_name: str = "") -> dict:
    """
    Crea un usuario local a partir de identidad OIDC de Google.

    Parámetros:
        google_sub (str): identificador único de Google
        email (str): correo del usuario
        display_name (str): nombre visible

    Retorna:
        dict: usuario creado
    """
    google_sub_clean = str(google_sub or "").strip()
    email_clean = str(email or "").strip().lower()
    display_name_clean = str(display_name or "").strip() or email_clean or "Usuario Google"

    if not google_sub_clean:
        raise ValueError("google_sub es obligatorio para crear un usuario Google.")

    if not email_clean:
        raise ValueError("El email es obligatorio para crear un usuario Google.")

    existing = get_user_by_google_sub(google_sub_clean)
    if existing:
        return existing

    username_final = generate_unique_username_from_email(email_clean)

    connection = get_connection()
    cursor = connection.cursor()

    # --------------------------------------------------------
    # Determinar si este usuario debe ser administrador
    # --------------------------------------------------------
    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM users
        WHERE is_admin = 1;
    """)
    total_admins = cursor.fetchone()["total"]
    is_admin = 1 if total_admins == 0 else 0

    cursor.execute("""
        INSERT INTO users (
            username,
            display_name,
            password_hash,
            is_admin,
            friend_name,
            favorite_color,
            favorite_activity,
            encouragement_style,
            preferred_comfort,
            google_sub,
            auth_provider
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
    """, (
        username_final,
        display_name_clean,
        "",
        is_admin,
        "Lumi",
        "",
        "",
        "",
        "cuentos",
        google_sub_clean,
        "google"
    ))

    user_id = cursor.lastrowid
    connection.commit()
    connection.close()

    usuario = get_user_by_id(user_id)

    if not usuario:
        raise ValueError("No se pudo recuperar el usuario Google recién creado.")

    return usuario

# ============================================================
# Favoritos de Biblioteca
# ============================================================

# ------------------------------------------------------------
# Agregar artículo a favoritos
# ------------------------------------------------------------
def add_article_to_favorites(user_id: int, article_id: int) -> None:
    """
    Guarda un artículo como favorito para un usuario.

    Parámetros:
        user_id (int): id del usuario
        article_id (int): id del artículo
    """
    article = get_article_by_id(article_id)

    if not article:
        raise ValueError("El artículo no existe.")

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        INSERT OR IGNORE INTO article_favorites (user_id, article_id)
        VALUES (?, ?);
    """, (user_id, article_id))

    connection.commit()
    connection.close()


# ------------------------------------------------------------
# Quitar artículo de favoritos
# ------------------------------------------------------------
def remove_article_from_favorites(user_id: int, article_id: int) -> None:
    """
    Elimina un artículo de favoritos para un usuario.

    Parámetros:
        user_id (int): id del usuario
        article_id (int): id del artículo
    """
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        DELETE FROM article_favorites
        WHERE user_id = ? AND article_id = ?;
    """, (user_id, article_id))

    connection.commit()
    connection.close()


# ------------------------------------------------------------
# Listar artículos favoritos de un usuario
# ------------------------------------------------------------
def list_favorite_articles(user_id: int) -> list[dict]:
    """
    Devuelve los artículos favoritos de un usuario.

    Parámetros:
        user_id (int): id del usuario

    Retorna:
        list[dict]: artículos favoritos
    """
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            a.id,
            a.title,
            a.category,
            a.reader_type,
            a.short_description,
            a.content,
            a.created_at
        FROM article_favorites af
        INNER JOIN articles a
            ON a.id = af.article_id
        WHERE af.user_id = ?
        ORDER BY af.created_at DESC, a.title ASC;
    """, (user_id,))

    rows = cursor.fetchall()
    connection.close()

    return [
        {
            "id": row["id"],
            "title": row["title"],
            "category": row["category"],
            "reader_type": row["reader_type"],
            "short_description": row["short_description"],
            "content": row["content"],
            "created_at": row["created_at"],
        }
        for row in rows
    ]


# ------------------------------------------------------------
# Verificar si un artículo está en favoritos
# ------------------------------------------------------------
def is_article_favorite(user_id: int, article_id: int) -> bool:
    """
    Revisa si un artículo ya está guardado como favorito.

    Parámetros:
        user_id (int): id del usuario
        article_id (int): id del artículo

    Retorna:
        bool: True si está en favoritos
    """
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT 1
        FROM article_favorites
        WHERE user_id = ? AND article_id = ?;
    """, (user_id, article_id))

    exists = cursor.fetchone() is not None
    connection.close()

    return exists