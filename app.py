# ============================================================
# app.py
# Aplicación principal Streamlit del proyecto.
# Incluye:
# - autenticación web compartida vía FastAPI
# - soporte de acceso con Google OIDC
# - historial por usuario
# - biblioteca estructurada
# - panel admin
# - importación / exportación de artículos
# - generación de artículos desde documentos
# - RAG simple para Biblioteca Inteligente
# - feedback y métricas
# - Amigo Imaginario con nombre, memoria suave e iniciativas
# - sesión de creación con avatar SVG personalizable
# - acompañante animado al lado del chat
# ============================================================

# ------------------------------------------------------------
# Importaciones estándar
# ------------------------------------------------------------
from datetime import datetime
from urllib.parse import quote
import csv
import io
import json

# ------------------------------------------------------------
# Importaciones de terceros
# ------------------------------------------------------------
import streamlit as st

# ------------------------------------------------------------
# Configuración general del proyecto
# ------------------------------------------------------------
from config import validar_configuracion
from database.access_control import (
    LEGAL_NOTICE_TEXT,
    allowed_modules_for_role,
    get_role_label,
    get_token_status,
    normalize_role,
    can_send_message_with_tokens,
    build_no_tokens_assistant_message,
    consume_user_token,
)

# ------------------------------------------------------------
# Cliente de autenticación compartida web / móvil
# ------------------------------------------------------------
from services.web_auth import (
    login_web_user,
    register_web_user,
    get_current_web_user,
)

# ------------------------------------------------------------
# Servicios web para biblioteca compartida
# ------------------------------------------------------------
from services.web_access import (
    admin_create_guest,
    admin_deactivate_guest,
    admin_extend_guest,
    admin_list_guests,
    admin_list_users,
    admin_update_token_policy,
    admin_update_user_role,
    get_my_token_status,
)
from services.web_library import (
    get_library_article,
    get_library_filter_options,
    list_library_articles,
)

# ------------------------------------------------------------
# Servicios web para conversaciones compartidas
# ------------------------------------------------------------
from services.web_chats import (
    create_web_conversation,
    get_web_conversation_messages,
    list_web_conversations_by_module,
    send_web_chat_message,
)

# ------------------------------------------------------------
# Funciones de base de datos
# ------------------------------------------------------------
from database.chat_db import (
    add_message,
    create_article,
    create_conversation,
    create_google_user,
    delete_article,
    get_article_by_id,
    get_conversation_by_id,
    get_feedback_for_message,
    get_feedback_summary,
    get_imaginary_friend_profile,
    get_latest_conversation_by_module,
    get_messages_by_conversation,
    get_user_by_google_sub,
    import_articles,
    initialize_database,
    list_all_articles,
    list_article_categories,
    list_conversations_by_module,
    list_feedback_summary_by_module,
    list_reader_types,
    list_recent_feedback,
    list_users,
    save_message_feedback,
    search_articles,
    set_user_admin_status,
    update_article,
    update_friend_name,
    update_friend_profile,
    update_imaginary_friend_profile,
    update_title_if_default,
)

# ------------------------------------------------------------
# Configuración visual, prompts y ayudas del amigo imaginario
# ------------------------------------------------------------
from prompts import (
    MODULE_INFO,
    MODULE_LABELS,
    build_friend_initiatives,
)

# ------------------------------------------------------------
# Registrar Administración como módulo visible en la web.
# No es un chat; es un panel administrativo.
# ------------------------------------------------------------
MODULE_LABELS["admin_panel"] = "Administración"

MODULE_INFO["admin_panel"] = {
    "bienvenida": "Panel de administración del sistema.",
    "descripcion": (
        "Gestiona usuarios, cuentas guest, roles, tokens y configuraciones "
        "generales del sistema."
    ),
    "placeholder": "Selecciona una opción del panel de administración.",
    "ejemplos": [
        "Crear una cuenta guest",
        "Revisar usuarios registrados",
        "Configurar tokens de un usuario",
    ],
}


# ------------------------------------------------------------
# Módulos que sí usan conversaciones tipo chat.
# Administración queda fuera para evitar errores de permisos.
# ------------------------------------------------------------
CHAT_MODULES = {
    "amigo_imaginario",
    "biblioteca_inteligente",
    "modo_padres",
}
# ------------------------------------------------------------
# Servicios Gemini
# ------------------------------------------------------------
from services.gemini_service import (
    generar_articulo_desde_documento,
    generar_respuesta,
    generar_respuesta_biblioteca_rag,
)

# ------------------------------------------------------------
# Utilidades para leer documentos subidos
# ------------------------------------------------------------
from utils.document_ingestion import extract_text_from_uploaded_file

# ------------------------------------------------------------
# Utilidades visuales para el avatar del amigo imaginario
# ------------------------------------------------------------
from utils.avatar_svg import (
    AVATAR_FORM_OPTIONS,
    DEFAULT_FRIEND_AVATAR,
    build_friend_avatar_svg,
)



# ------------------------------------------------------------
# Configuración general de la página
# ------------------------------------------------------------
st.set_page_config(
    page_title="Amigo Imaginario Neurodivergente",
    page_icon="💙",
    layout="wide"
)
# ============================================================
# Reinicio seguro de sesión
# Permite limpiar el estado viejo de Streamlit entrando con:
# http://localhost:8501/?reset=1
# ============================================================

if st.query_params.get("reset") == "1":
    # Borra todas las variables guardadas en la sesión actual
    for key in list(st.session_state.keys()):
        del st.session_state[key]

    # Limpia el parámetro de la URL
    st.query_params.clear()

    # Recarga la app desde cero
    st.rerun()


# ------------------------------------------------------------
# Render HTML seguro con fallback
# ------------------------------------------------------------
def render_html_block(html: str) -> None:
    """
    Renderiza HTML usando st.html si existe, y si no,
    usa st.markdown con unsafe_allow_html.

    Parámetros:
        html (str): bloque HTML a renderizar
    """
    if hasattr(st, "html"):
        st.html(html)
    else:
        st.markdown(html, unsafe_allow_html=True)


# ------------------------------------------------------------
# Convertir SVG a data URI para mostrarlo en HTML
# ------------------------------------------------------------
def svg_to_data_uri(svg: str) -> str:
    """
    Convierte un SVG en un data URI seguro para usar dentro
    de una etiqueta <img>.

    Parámetros:
        svg (str): contenido SVG

    Retorna:
        str: data URI
    """
    return f"data:image/svg+xml;utf8,{quote(svg)}"


# ------------------------------------------------------------
# Inicializar estado de sesión
# ------------------------------------------------------------
def inicializar_estado() -> None:
    """
    Inicializa variables necesarias en session_state.
    """
    # --------------------------------------------------------
    # Sesión local clásica de la app
    # --------------------------------------------------------
    if "user_id" not in st.session_state:
        st.session_state.user_id = None

    if "username" not in st.session_state:
        st.session_state.username = None

    if "display_name" not in st.session_state:
        st.session_state.display_name = None

    if "is_admin" not in st.session_state:
        st.session_state.is_admin = False

    if "role" not in st.session_state:
        st.session_state.role = "child"

    if "role_label" not in st.session_state:
        st.session_state.role_label = "Usuario niño"

    if "allowed_modules" not in st.session_state:
        st.session_state.allowed_modules = ["amigo_imaginario"]

    if "token_status" not in st.session_state:
        st.session_state.token_status = None

    # --------------------------------------------------------
    # Sesión compartida basada en FastAPI
    # --------------------------------------------------------
    if "auth_token" not in st.session_state:
        st.session_state.auth_token = None

    if "current_user" not in st.session_state:
        st.session_state.current_user = None

    # --------------------------------------------------------
    # Estado general de la app
    # --------------------------------------------------------
    if "modulo_actual" not in st.session_state:
        st.session_state.modulo_actual = "amigo_imaginario"

    if "ultimo_modulo" not in st.session_state:
        st.session_state.ultimo_modulo = "amigo_imaginario"

    if "conversation_id" not in st.session_state:
        st.session_state.conversation_id = None

    if "mensajes" not in st.session_state:
        st.session_state.mensajes = []

    if "ui_font_size" not in st.session_state:
        st.session_state.ui_font_size = "Normal"

    if "ui_high_contrast" not in st.session_state:
        st.session_state.ui_high_contrast = False

    if "ui_focus_mode" not in st.session_state:
        st.session_state.ui_focus_mode = False

    if "article_search_text" not in st.session_state:
        st.session_state.article_search_text = ""

    if "article_category_filter" not in st.session_state:
        st.session_state.article_category_filter = "Todas"

    if "article_reader_filter" not in st.session_state:
        st.session_state.article_reader_filter = "Todos"

    if "selected_article_id" not in st.session_state:
        st.session_state.selected_article_id = None

    if "pending_message" not in st.session_state:
        st.session_state.pending_message = None

    if "admin_edit_article_id" not in st.session_state:
        st.session_state.admin_edit_article_id = None

    # --------------------------------------------------------
    # Estado del amigo imaginario
    # --------------------------------------------------------
    if "friend_name" not in st.session_state:
        st.session_state.friend_name = "Lumi"

    if "friend_profile" not in st.session_state:
        st.session_state.friend_profile = {
            "favorite_color": "",
            "favorite_activity": "",
            "encouragement_style": "",
            "preferred_comfort": "cuentos",
        }

    if "friend_avatar" not in st.session_state:
        st.session_state.friend_avatar = dict(DEFAULT_FRIEND_AVATAR)

    if "friend_companion_state" not in st.session_state:
        st.session_state.friend_companion_state = "calma"

    if "friend_companion_message" not in st.session_state:
        st.session_state.friend_companion_message = "Estoy aquí contigo."


# ------------------------------------------------------------
# Aplicar estilos visuales
# ------------------------------------------------------------
def aplicar_estilos() -> None:
    """
    Aplica estilos CSS según las preferencias activas de la sesión.
    """
    font_size_map = {
        "Normal": "16px",
        "Grande": "18px",
        "Muy grande": "20px",
    }

    base_font_size = font_size_map.get(st.session_state.ui_font_size, "16px")

    if st.session_state.ui_high_contrast:
        bg_card = "rgba(255, 255, 255, 0.08)"
        border_card = "rgba(255, 255, 255, 0.24)"
        text_muted = "#DCE2EA"
        accent_bg = "rgba(0, 122, 255, 0.24)"
    else:
        bg_card = "rgba(49, 100, 185, 0.12)"
        border_card = "rgba(49, 100, 185, 0.20)"
        text_muted = "#B9C0CC"
        accent_bg = "rgba(49, 100, 185, 0.12)"

    st.markdown(
        f"""
        <style>
            html, body, [class*="css"] {{
                font-size: {base_font_size};
            }}

            .main-title {{
                font-size: 2.5rem;
                font-weight: 800;
                line-height: 1.1;
                margin-bottom: 0.20rem;
            }}

            .main-subtitle {{
                color: {text_muted};
                font-size: 1rem;
                margin-bottom: 1.1rem;
            }}

            .hero-card {{
                background: linear-gradient(135deg, rgba(49,100,185,0.18), rgba(112,76,182,0.15));
                border: 1px solid {border_card};
                border-radius: 18px;
                padding: 20px 22px;
                margin-bottom: 18px;
            }}

            .hero-title {{
                font-size: 1.15rem;
                font-weight: 700;
                margin-bottom: 0.35rem;
            }}

            .hero-text {{
                color: {text_muted};
                line-height: 1.55;
            }}

            .info-card {{
                background-color: {bg_card};
                border: 1px solid {border_card};
                border-radius: 16px;
                padding: 14px 16px;
                margin-bottom: 14px;
            }}

            .info-title {{
                font-weight: 700;
                margin-bottom: 0.25rem;
            }}

            .info-text {{
                color: {text_muted};
                line-height: 1.5;
            }}

            .mini-card {{
                background-color: {accent_bg};
                border: 1px solid {border_card};
                border-radius: 14px;
                padding: 12px 14px;
                margin-bottom: 12px;
                min-height: 94px;
            }}

            .mini-card-title {{
                font-size: 0.95rem;
                font-weight: 700;
                margin-bottom: 0.25rem;
            }}

            .mini-card-value {{
                font-size: 1.20rem;
                font-weight: 800;
                margin-bottom: 0.15rem;
            }}

            .mini-card-caption {{
                color: {text_muted};
                font-size: 0.92rem;
            }}

            .auth-shell {{
                max-width: 980px;
                margin: 0 auto;
                padding-top: 6px;
            }}

            .sidebar-note {{
                font-size: 0.92rem;
                color: {text_muted};
                line-height: 1.45;
            }}

            .chip {{
                display: inline-block;
                padding: 6px 10px;
                border-radius: 999px;
                font-size: 0.86rem;
                font-weight: 600;
                background-color: {accent_bg};
                border: 1px solid {border_card};
                margin-right: 8px;
                margin-bottom: 8px;
            }}

            .ethics-box {{
                font-size: 0.95rem;
                color: {text_muted};
                padding-top: 8px;
                line-height: 1.55;
            }}

            .article-card {{
                background-color: {bg_card};
                border: 1px solid {border_card};
                border-radius: 14px;
                padding: 14px 14px;
                margin-bottom: 12px;
            }}

            .article-title {{
                font-weight: 700;
                margin-bottom: 0.35rem;
            }}

            .article-meta {{
                color: {text_muted};
                font-size: 0.92rem;
                margin-bottom: 0.35rem;
            }}

            .article-desc {{
                color: {text_muted};
                line-height: 1.45;
                margin-bottom: 0.65rem;
            }}

            .friend-companion-shell {{
                display: flex;
                flex-direction: column;
                align-items: center;
                gap: 12px;
                padding: 16px;
                border-radius: 20px;
                background: rgba(49, 100, 185, 0.10);
                border: 1px solid rgba(49, 100, 185, 0.20);
            }}

            .friend-companion-avatar {{
                animation: friendFloat 3.2s ease-in-out infinite;
                transform-origin: center;
            }}

            .friend-companion-avatar img {{
                display: block;
                width: 220px;
                height: auto;
            }}

            .friend-companion-bubble {{
                width: 100%;
                padding: 12px 14px;
                border-radius: 16px;
                background: rgba(255,255,255,0.06);
                border: 1px solid rgba(255,255,255,0.08);
                line-height: 1.45;
                font-size: 0.96rem;
                box-sizing: border-box;
            }}

            .friend-companion-badge {{
                display: inline-block;
                padding: 6px 10px;
                border-radius: 999px;
                font-size: 0.85rem;
                font-weight: 700;
                background: rgba(90,169,255,0.16);
                border: 1px solid rgba(90,169,255,0.26);
            }}

            @keyframes friendFloat {{
                0%   {{ transform: translateY(0px) scale(1); }}
                50%  {{ transform: translateY(-8px) scale(1.01); }}
                100% {{ transform: translateY(0px) scale(1); }}
            }}

            .friend-companion-shell.mood-feliz .friend-companion-badge {{
                background: rgba(102,204,153,0.18);
                border-color: rgba(102,204,153,0.28);
            }}

            .friend-companion-shell.mood-cuento .friend-companion-badge {{
                background: rgba(167,123,255,0.18);
                border-color: rgba(167,123,255,0.28);
            }}

            .friend-companion-shell.mood-juego .friend-companion-badge {{
                background: rgba(255,215,102,0.18);
                border-color: rgba(255,215,102,0.28);
            }}

            .friend-companion-shell.mood-animo .friend-companion-badge {{
                background: rgba(255,139,194,0.18);
                border-color: rgba(255,139,194,0.28);
            }}

            .friend-companion-shell.mood-calma .friend-companion-badge {{
                background: rgba(90,169,255,0.16);
                border-color: rgba(90,169,255,0.26);
            }}
        </style>
        """,
        unsafe_allow_html=True
    )


# ------------------------------------------------------------
# Formatear fecha
# ------------------------------------------------------------
def formatear_fecha(texto_fecha: str) -> str:
    """
    Convierte una fecha SQLite a formato corto.
    """
    try:
        fecha = datetime.strptime(texto_fecha, "%Y-%m-%d %H:%M:%S")
        return fecha.strftime("%d/%m %H:%M")
    except Exception:
        return texto_fecha


# ------------------------------------------------------------
# Obtener bienvenida del módulo
# ------------------------------------------------------------
def obtener_bienvenida_modulo(modulo: str) -> str:
    """
    Devuelve el mensaje de bienvenida del módulo actual.
    """
    return MODULE_INFO[modulo]["bienvenida"]


# ------------------------------------------------------------
# Verificar si la sesión actual usa FastAPI compartido
# ------------------------------------------------------------
def has_shared_api_session() -> bool:
    """
    Indica si la sesión actual tiene token API.
    """
    return bool(st.session_state.get("auth_token"))

# ------------------------------------------------------------
# Asegurar módulos permitidos según rol
# Agrega el módulo admin_panel cuando el usuario es superadmin.
# ------------------------------------------------------------
def asegurar_modulos_por_rol(role: str, allowed_modules: list[str] | None) -> list[str]:
    """
    Devuelve los módulos permitidos y agrega Administración
    cuando el usuario tiene rol superadmin.

    Parámetros:
        role (str): rol actual del usuario.
        allowed_modules (list[str] | None): módulos actuales del usuario.

    Retorna:
        list[str]: módulos finales disponibles para la navegación.
    """
    modules = list(allowed_modules or [])

    if role == "superadmin" and "admin_panel" not in modules:
        modules.append("admin_panel")

    return modules
# ------------------------------------------------------------
# Verificar si un módulo funciona como chat
# ------------------------------------------------------------
def es_modulo_chat(modulo: str) -> bool:
    """
    Indica si el módulo usa conversaciones.

    Administración no debe crear conversaciones.
    """
    return modulo in CHAT_MODULES


# ------------------------------------------------------------
# Asegurar módulos permitidos según rol
# ------------------------------------------------------------
def asegurar_modulos_por_rol(role: str, allowed_modules: list[str] | None) -> list[str]:
    """
    Devuelve módulos permitidos finales para navegación.

    Parámetros:
        role (str): rol normalizado del usuario.
        allowed_modules (list[str] | None): módulos recibidos desde backend.

    Retorna:
        list[str]: módulos disponibles en la interfaz.
    """
    modules = list(allowed_modules or allowed_modules_for_role(role))

    # --------------------------------------------------------
    # Superadmin siempre debe ver Administración
    # --------------------------------------------------------
    if role == "superadmin" and "admin_panel" not in modules:
        modules.append("admin_panel")

    # --------------------------------------------------------
    # Evitar módulos que no existan en labels/info
    # --------------------------------------------------------
    modules = [
        module
        for module in modules
        if module in MODULE_LABELS and module in MODULE_INFO
    ]

    return modules


# ------------------------------------------------------------
# Obtener módulos visibles desde la sesión
# ------------------------------------------------------------
def obtener_modulos_visibles_sesion() -> list[str]:
    """
    Obtiene los módulos permitidos para el usuario actual.
    """
    role = st.session_state.get("user_role", "child")
    allowed_modules = st.session_state.get("allowed_modules", [])

    modules = asegurar_modulos_por_rol(
        role=role,
        allowed_modules=allowed_modules,
    )

    if not modules:
        modules = ["amigo_imaginario"]

    return modules


# ------------------------------------------------------------
# Renderizar aviso legal
# ------------------------------------------------------------
def render_aviso_legal() -> None:
    """
    Muestra el aviso legal del sistema.
    """
    st.markdown(
        f"""
        <div class="ethics-box">
            <strong>Aviso de uso:</strong> {LEGAL_NOTICE_TEXT}
        </div>
        """,
        unsafe_allow_html=True
    )


# ------------------------------------------------------------
# Refrescar tokens desde API si hay sesión compartida
# ------------------------------------------------------------
def refrescar_tokens_sesion() -> dict:
    """
    Actualiza el estado de tokens del usuario.

    Si hay token de FastAPI, consulta /api/tokens/me.
    Si no hay API, usa la base local.
    """
    user_id = st.session_state.get("user_id")
    token = st.session_state.get("auth_token")

    if not user_id:
        return {}

    try:
        if token:
            token_status = get_my_token_status(token)
        else:
            token_status = get_token_status(user_id)

        st.session_state.token_status = token_status

        if st.session_state.get("current_user"):
            st.session_state.current_user["token_status"] = token_status

        return token_status

    except Exception:
        return st.session_state.get("token_status", {}) or {}


# ------------------------------------------------------------
# Tarjeta visual de tokens
# ------------------------------------------------------------
def render_token_status_card() -> None:
    """
    Muestra tokens disponibles con advertencias amigables.
    """
    token_status = refrescar_tokens_sesion()

    if not token_status:
        return

    if token_status.get("is_unlimited"):
        st.markdown(
            """
            <div class="info-card">
                <div class="info-title">Tokens</div>
                <div class="info-text">Uso ilimitado para superadmin.</div>
            </div>
            """,
            unsafe_allow_html=True
        )
        return

    remaining = token_status.get("remaining_tokens", 0)
    daily_limit = token_status.get("daily_limit", 0)
    used_tokens = token_status.get("used_tokens", 0)
    reset_text = token_status.get("reset_text", "próximo reinicio")

    st.markdown(
        f"""
        <div class="info-card">
            <div class="info-title">Tokens disponibles</div>
            <div class="info-text">
                Te quedan <strong>{remaining}</strong> de <strong>{daily_limit}</strong> tokens.<br>
                Tokens usados en este periodo: {used_tokens}.<br>
                Próximo reinicio: {reset_text}.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    if token_status.get("is_empty"):
        st.error(
            token_status.get(
                "message",
                "Por ahora ya no tienes tokens disponibles. Intenta de nuevo más tarde."
            )
        )
    elif token_status.get("is_low"):
        st.warning(
            token_status.get(
                "message",
                "Te quedan pocos tokens disponibles. Úsalos con calma para lo más importante."
            )
        )

# ------------------------------------------------------------
# Sincronizar usuario actual a current_user
# ------------------------------------------------------------
def sync_current_user_session(usuario: dict) -> None:
    """
    Guarda una representación completa del usuario autenticado
    para reutilizarla en la sesión compartida web / móvil.
    """
    role = normalize_role(
        usuario.get("role"),
        bool(usuario.get("is_admin", False))
    )

    allowed_modules = asegurar_modulos_por_rol(
        role=role,
        allowed_modules=usuario.get("allowed_modules") or allowed_modules_for_role(role),
    )

    st.session_state.current_user = {
        "id": usuario["id"],
        "username": usuario["username"],
        "display_name": usuario["display_name"],
        "is_admin": role == "superadmin",
        "role": role,
        "role_label": usuario.get("role_label", role),
        "account_type": usuario.get("account_type", "permanent"),
        "guest_type": usuario.get("guest_type", ""),
        "guest_status": usuario.get("guest_status", "none"),
        "guest_expires_at": usuario.get("guest_expires_at", ""),
        "is_active": bool(usuario.get("is_active", True)),
        "allowed_modules": allowed_modules,
        "permissions": usuario.get("permissions") or {},
        "token_status": usuario.get("token_status") or {},
        "friend_name": usuario.get("friend_name", "Lumi"),
        "favorite_color": usuario.get("favorite_color", ""),
        "favorite_activity": usuario.get("favorite_activity", ""),
        "encouragement_style": usuario.get("encouragement_style", ""),
        "preferred_comfort": usuario.get("preferred_comfort", "cuentos"),
    }

    # --------------------------------------------------------
    # Guardar datos clave también directo en session_state
    # para que la navegación los use sin depender del dict.
    # --------------------------------------------------------
    st.session_state.user_role = role
    st.session_state.role_label = usuario.get("role_label", role)
    st.session_state.allowed_modules = allowed_modules
    st.session_state.permissions = usuario.get("permissions") or {}
    st.session_state.token_status = usuario.get("token_status") or {}

# ------------------------------------------------------------
# Iniciar sesión
# ------------------------------------------------------------
def iniciar_sesion(
    usuario: dict,
    auth_token: str | None = None,
    reset_chat_state: bool = True
) -> None:
    """
    Guarda al usuario autenticado en session_state.

    Parámetros:
        usuario (dict): usuario autenticado.
        auth_token (str | None): token JWT opcional de FastAPI.
        reset_chat_state (bool): si True reinicia módulo/chat actual.
    """
    role = normalize_role(
        usuario.get("role"),
        bool(usuario.get("is_admin", False))
    )

    allowed_modules = asegurar_modulos_por_rol(
        role=role,
        allowed_modules=usuario.get("allowed_modules") or allowed_modules_for_role(role),
    )

    st.session_state.user_id = usuario["id"]
    st.session_state.username = usuario["username"]
    st.session_state.display_name = usuario["display_name"]
    st.session_state.is_admin = role == "superadmin"

    st.session_state.user_role = role
    st.session_state.role_label = usuario.get("role_label", role)
    st.session_state.allowed_modules = allowed_modules
    st.session_state.permissions = usuario.get("permissions") or {}
    st.session_state.token_status = usuario.get("token_status") or {}

    st.session_state.friend_name = usuario.get("friend_name", "Lumi")
    st.session_state.friend_profile = {
        "favorite_color": usuario.get("favorite_color", ""),
        "favorite_activity": usuario.get("favorite_activity", ""),
        "encouragement_style": usuario.get("encouragement_style", ""),
        "preferred_comfort": usuario.get("preferred_comfort", "cuentos"),
    }

    # --------------------------------------------------------
    # Guardar token si viene de autenticación FastAPI
    # --------------------------------------------------------
    st.session_state.auth_token = auth_token
    sync_current_user_session(usuario)

    # --------------------------------------------------------
    # Cargar avatar guardado del amigo imaginario
    # --------------------------------------------------------
    st.session_state.friend_avatar = get_imaginary_friend_profile(usuario["id"])

    # --------------------------------------------------------
    # Estado visual del acompañante
    # --------------------------------------------------------
    st.session_state.friend_companion_state = "calma"
    st.session_state.friend_companion_message = "Estoy aquí contigo."

    # --------------------------------------------------------
    # Al iniciar, mandar al primer módulo permitido.
    # Para superadmin puede iniciar en Amigo, pero ya tendrá Admin visible.
    # --------------------------------------------------------
    if reset_chat_state:
        modulo_inicial = allowed_modules[0] if allowed_modules else "amigo_imaginario"

        st.session_state.modulo_actual = modulo_inicial
        st.session_state.ultimo_modulo = modulo_inicial
        st.session_state.conversation_id = None
        st.session_state.mensajes = []
        st.session_state.pending_message = None

# ------------------------------------------------------------
# Cerrar sesión
# ------------------------------------------------------------
def cerrar_sesion() -> None:
    """
    Limpia el estado de autenticación, permisos y conversación.
    """
    st.session_state.user_id = None
    st.session_state.username = None
    st.session_state.display_name = None
    st.session_state.is_admin = False

    st.session_state.user_role = "child"
    st.session_state.role_label = "Usuario"
    st.session_state.allowed_modules = []
    st.session_state.permissions = {}
    st.session_state.token_status = {}

    st.session_state.auth_token = None
    st.session_state.current_user = None

    st.session_state.friend_name = "Lumi"
    st.session_state.friend_profile = {
        "favorite_color": "",
        "favorite_activity": "",
        "encouragement_style": "",
        "preferred_comfort": "cuentos",
    }

    st.session_state.friend_avatar = dict(DEFAULT_FRIEND_AVATAR)
    st.session_state.friend_companion_state = "calma"
    st.session_state.friend_companion_message = "Estoy aquí contigo."

    st.session_state.modulo_actual = "amigo_imaginario"
    st.session_state.ultimo_modulo = "amigo_imaginario"
    st.session_state.conversation_id = None
    st.session_state.mensajes = []
    st.session_state.pending_message = None
    st.session_state.selected_article_id = None
    st.session_state.admin_edit_article_id = None

# ------------------------------------------------------------
# Restaurar sesión desde token FastAPI
# ------------------------------------------------------------
def restore_api_session() -> None:
    """
    Si existe un token JWT guardado en session_state,
    intenta recuperar al usuario actual desde FastAPI
    para mantener sincronizada la sesión web con la móvil.

    Importante:
        Esta restauración NO debe reiniciar el módulo actual
        ni la conversación activa en cada rerun de Streamlit.
    """
    token = st.session_state.get("auth_token")

    if not token:
        return

    # --------------------------------------------------------
    # Si ya existe sesión local cargada, no volver a pedir
    # /api/auth/me en cada rerun para no resetear la UI.
    # --------------------------------------------------------
    if (
        st.session_state.get("user_id") is not None
        and st.session_state.get("current_user") is not None
    ):
        return

    try:
        usuario = get_current_web_user(token)

        # ----------------------------------------------------
        # Restaurar usuario SIN reiniciar módulo/chat actual.
        # ----------------------------------------------------
        iniciar_sesion(
            usuario=usuario,
            auth_token=token,
            reset_chat_state=False
        )

    except Exception:
        st.session_state.auth_token = None
        st.session_state.current_user = None

        if not getattr(st.user, "is_logged_in", False):
            cerrar_sesion()


# ------------------------------------------------------------
# Cargar conversación
# ------------------------------------------------------------
def cargar_conversacion(conversation_id: int, user_id: int) -> None:
    """
    Carga una conversación usando API compartida si existe token;
    si no, usa fallback local para sesiones Google OIDC.
    """
    if has_shared_api_session():
        token = st.session_state.get("auth_token")

        try:
            mensajes = get_web_conversation_messages(
                token=token,
                conversation_id=conversation_id
            )

            st.session_state.conversation_id = conversation_id
            st.session_state.mensajes = [
                {
                    "id": mensaje.get("id"),
                    "role": mensaje.get("role", "assistant"),
                    "content": mensaje.get("content", "")
                }
                for mensaje in mensajes
            ]
        except Exception as error:
            st.error(f"No se pudo cargar la conversación: {error}")

        return

    # --------------------------------------------------------
    # Fallback local
    # --------------------------------------------------------
    conversacion = get_conversation_by_id(conversation_id, user_id)

    if not conversacion:
        return

    mensajes = get_messages_by_conversation(conversation_id, user_id)

    st.session_state.modulo_actual = conversacion["module"]
    st.session_state.ultimo_modulo = conversacion["module"]
    st.session_state.conversation_id = conversation_id
    st.session_state.mensajes = [
        {
            "id": mensaje["id"],
            "role": mensaje["role"],
            "content": mensaje["content"]
        }
        for mensaje in mensajes
    ]


# ------------------------------------------------------------
# Crear y cargar nueva conversación
# ------------------------------------------------------------
def crear_y_cargar_nueva_conversacion(modulo: str, user_id: int) -> None:
    """
    Crea una conversación usando API compartida si existe token;
    si no, usa fallback local.

    Nota:
        admin_panel no debe crear conversaciones.
    """
    if not es_modulo_chat(modulo):
        st.session_state.conversation_id = None
        st.session_state.mensajes = []
        return

    if has_shared_api_session():
        token = st.session_state.get("auth_token")

        try:
            conversacion = create_web_conversation(
                token=token,
                module=modulo
            )

            st.session_state.conversation_id = conversacion["id"]
            st.session_state.modulo_actual = modulo
            st.session_state.ultimo_modulo = modulo
            cargar_conversacion(conversacion["id"], user_id)

        except Exception as error:
            st.error(f"No se pudo crear la conversación: {error}")

        return

    # --------------------------------------------------------
    # Fallback local
    # --------------------------------------------------------
    conversation_id = create_conversation(
        user_id=user_id,
        module=modulo
    )

    bienvenida = obtener_bienvenida_modulo(modulo)

    assistant_message_id = add_message(
        conversation_id=conversation_id,
        role="assistant",
        content=bienvenida
    )

    cargar_conversacion(conversation_id, user_id)

    if not st.session_state.mensajes:
        st.session_state.mensajes = [
            {
                "id": assistant_message_id,
                "role": "assistant",
                "content": bienvenida
            }
        ]

# ------------------------------------------------------------
# Asegurar conversación activa
# ------------------------------------------------------------
def asegurar_conversacion_activa(modulo: str, user_id: int) -> None:
    """
    Garantiza que exista una conversación activa para módulos de chat.

    Administración no crea ni carga conversaciones.
    """
    if not es_modulo_chat(modulo):
        st.session_state.conversation_id = None
        st.session_state.mensajes = []
        return

    conversation_id = st.session_state.get("conversation_id")

    # --------------------------------------------------------
    # Si ya hay una conversación con mensajes cargados,
    # la dejamos activa.
    # --------------------------------------------------------
    if conversation_id and st.session_state.mensajes:
        return

    if has_shared_api_session():
        token = st.session_state.get("auth_token")

        try:
            conversaciones = list_web_conversations_by_module(
                token=token,
                module=modulo
            )

            if conversaciones:
                cargar_conversacion(conversaciones[0]["id"], user_id)
            else:
                crear_y_cargar_nueva_conversacion(modulo, user_id)

        except Exception as error:
            st.error(f"No se pudo asegurar la conversación activa: {error}")

        return

    # --------------------------------------------------------
    # Fallback local
    # --------------------------------------------------------
    if conversation_id:
        conversacion = get_conversation_by_id(conversation_id, user_id)

        if conversacion and conversacion["module"] == modulo:
            if not st.session_state.mensajes:
                cargar_conversacion(conversation_id, user_id)
            return

    ultima = get_latest_conversation_by_module(user_id, modulo)

    if ultima:
        cargar_conversacion(ultima["id"], user_id)
    else:
        crear_y_cargar_nueva_conversacion(modulo, user_id)

# ------------------------------------------------------------
# Obtener conversaciones del módulo
# ------------------------------------------------------------
def obtener_conversaciones_modulo(modulo: str, user_id: int) -> list[dict]:
    """
    Recupera conversaciones del módulo actual.

    Administración no usa historial de conversaciones.
    """
    if not es_modulo_chat(modulo):
        return []

    if has_shared_api_session():
        token = st.session_state.get("auth_token")

        try:
            return list_web_conversations_by_module(
                token=token,
                module=modulo
            )
        except Exception as error:
            st.error(f"No se pudieron cargar las conversaciones del módulo: {error}")
            return []

    return list_conversations_by_module(
        user_id=user_id,
        module=modulo,
        limit=30
    )

# ------------------------------------------------------------
# Tarjeta estadística
# ------------------------------------------------------------
def render_stat_card(title: str, value: str, caption: str) -> None:
    """
    Muestra una tarjeta estadística simple.
    """
    st.markdown(
        f"""
        <div class="mini-card">
            <div class="mini-card-title">{title}</div>
            <div class="mini-card-value">{value}</div>
            <div class="mini-card-caption">{caption}</div>
        </div>
        """,
        unsafe_allow_html=True
    )


# ------------------------------------------------------------
# Construir plantilla CSV
# ------------------------------------------------------------
def build_template_csv() -> bytes:
    """
    Crea una plantilla CSV para importar artículos.
    """
    output = io.StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=["title", "category", "reader_type", "short_description", "content"]
    )
    writer.writeheader()
    writer.writerow({
        "title": "Ejemplo de artículo",
        "category": "TDAH",
        "reader_type": "Usuario",
        "short_description": "Descripción breve del artículo.",
        "content": "Contenido completo del artículo con al menos varios párrafos."
    })

    return output.getvalue().encode("utf-8")


# ------------------------------------------------------------
# Construir plantilla JSON
# ------------------------------------------------------------
def build_template_json() -> bytes:
    """
    Crea una plantilla JSON para importar artículos.
    """
    data = [
        {
            "title": "Ejemplo de artículo",
            "category": "TDAH",
            "reader_type": "Usuario",
            "short_description": "Descripción breve del artículo.",
            "content": "Contenido completo del artículo con al menos varios párrafos."
        }
    ]

    return json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")


# ------------------------------------------------------------
# Construir exportación CSV
# ------------------------------------------------------------
def build_export_csv(articles: list[dict]) -> bytes:
    """
    Convierte una lista de artículos a CSV.
    """
    output = io.StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=[
            "id",
            "title",
            "category",
            "reader_type",
            "short_description",
            "content",
            "created_at"
        ]
    )
    writer.writeheader()

    for article in articles:
        writer.writerow(article)

    return output.getvalue().encode("utf-8")


# ------------------------------------------------------------
# Construir exportación JSON
# ------------------------------------------------------------
def build_export_json(articles: list[dict]) -> bytes:
    """
    Convierte una lista de artículos a JSON.
    """
    return json.dumps(articles, ensure_ascii=False, indent=2).encode("utf-8")


# ------------------------------------------------------------
# Parsear archivo subido
# ------------------------------------------------------------
def parse_uploaded_articles(uploaded_file) -> list[dict]:
    """
    Lee un archivo CSV o JSON y lo convierte a lista de dicts.
    """
    filename = uploaded_file.name.lower()
    raw = uploaded_file.getvalue()

    if filename.endswith(".csv"):
        text = raw.decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(text))
        return [dict(row) for row in reader]

    if filename.endswith(".json"):
        text = raw.decode("utf-8-sig")
        data = json.loads(text)

        if isinstance(data, dict) and "articles" in data:
            data = data["articles"]

        if not isinstance(data, list):
            raise ValueError("El JSON debe ser una lista de artículos o un objeto con la clave 'articles'.")

        return [dict(item) for item in data]

    raise ValueError("Formato no soportado. Usa CSV o JSON.")


# ------------------------------------------------------------
# Historial con feedback
# ------------------------------------------------------------
def render_chat_history_with_feedback(user_id: int, modulo_actual: str) -> None:
    """
    Muestra el historial del chat y agrega feedback a las
    respuestas del asistente.
    """
    for index, mensaje in enumerate(st.session_state.mensajes):
        with st.chat_message(mensaje["role"]):
            st.markdown(mensaje["content"])

            es_respuesta_calificable = (
                mensaje["role"] == "assistant"
                and mensaje.get("id") is not None
                and index > 0
                and st.session_state.mensajes[index - 1]["role"] == "user"
            )

            if es_respuesta_calificable:
                message_id = mensaje["id"]

                feedback_guardado = get_feedback_for_message(
                    message_id=message_id,
                    user_id=user_id
                )

                default_value = feedback_guardado["rating"] if feedback_guardado else None

                st.caption("¿Te fue útil esta respuesta?")

                nuevo_valor = st.feedback(
                    "thumbs",
                    key=f"feedback_msg_{message_id}",
                    default=default_value,
                    width="content"
                )

                if nuevo_valor is not None:
                    valor_guardado = feedback_guardado["rating"] if feedback_guardado else None

                    if valor_guardado != nuevo_valor:
                        save_message_feedback(
                            message_id=message_id,
                            user_id=user_id,
                            conversation_id=st.session_state.conversation_id,
                            module=modulo_actual,
                            rating=int(nuevo_valor),
                            comment=""
                        )
                        st.rerun()


# ------------------------------------------------------------
# Panel de métricas
# ------------------------------------------------------------
def render_feedback_metrics_panel() -> None:
    """
    Muestra métricas básicas del feedback recibido.
    """
    resumen_global = get_feedback_summary()
    resumen_por_modulo = list_feedback_summary_by_module()
    feedback_reciente = list_recent_feedback(limit=50)

    st.markdown(
        """
        <div class="info-card">
            <div class="info-title">Métricas de utilidad</div>
            <div class="info-text">
                Aquí puedes ver cuántas respuestas fueron marcadas como útiles o no útiles
                y revisar retroalimentación reciente.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    col_1, col_2, col_3, col_4 = st.columns(4)

    with col_1:
        st.metric("Respuestas calificadas", resumen_global["total"])

    with col_2:
        st.metric("Útiles", resumen_global["positivos"])

    with col_3:
        st.metric("No útiles", resumen_global["negativos"])

    with col_4:
        st.metric("% útil", f"{resumen_global['porcentaje_util']}%")

    st.markdown("### Resumen por módulo")

    if not resumen_por_modulo:
        st.info("Todavía no hay feedback registrado.")
    else:
        st.dataframe(
            resumen_por_modulo,
            width="stretch",
            hide_index=True
        )

    st.markdown("### Feedback reciente")

    if not feedback_reciente:
        st.info("Todavía no hay feedback reciente para mostrar.")
    else:
        st.dataframe(
            feedback_reciente,
            width="stretch",
            hide_index=True
        )


# ------------------------------------------------------------
# Actualizar mood del acompañante
# ------------------------------------------------------------
def update_friend_companion_state(trigger: str = "") -> None:
    """
    Ajusta el estado visual del acompañante según el disparador.
    """
    trigger_clean = str(trigger or "").strip().lower()

    if "cuento" in trigger_clean:
        st.session_state.friend_companion_state = "cuento"
        st.session_state.friend_companion_message = "Tengo un cuentito listo para ti."
        return

    if "juego" in trigger_clean:
        st.session_state.friend_companion_state = "juego"
        st.session_state.friend_companion_message = "Podemos jugar algo suave y bonito."
        return

    if "respira" in trigger_clean or "respiración" in trigger_clean or "respiracion" in trigger_clean:
        st.session_state.friend_companion_state = "calma"
        st.session_state.friend_companion_message = "Vamos despacito. Estoy contigo."
        return

    if "ánimo" in trigger_clean or "animo" in trigger_clean:
        st.session_state.friend_companion_state = "animo"
        st.session_state.friend_companion_message = "Quiero darte palabras bonitas."
        return

    st.session_state.friend_companion_state = "feliz"
    st.session_state.friend_companion_message = "Estoy aquí contigo y te acompaño."


# ------------------------------------------------------------
# Vista previa del avatar del amigo imaginario
# ------------------------------------------------------------
def render_friend_avatar_preview() -> None:
    """
    Renderiza el avatar actual del amigo imaginario usando SVG.
    """
    avatar_svg = build_friend_avatar_svg(
        friend_name=st.session_state.friend_name,
        avatar_profile=st.session_state.friend_avatar,
        size=260
    )

    col_1, col_2, col_3 = st.columns([1, 2, 1])

    with col_2:
        st.image(avatar_svg, width=260)


# ------------------------------------------------------------
# Panel del acompañante al lado del chat
# ------------------------------------------------------------
def render_friend_companion_panel() -> None:
    """
    Muestra el avatar y una burbuja de acompañamiento
    al costado del chat.
    """
    avatar_svg = build_friend_avatar_svg(
        friend_name=st.session_state.friend_name,
        avatar_profile=st.session_state.friend_avatar,
        size=220
    )

    avatar_src = svg_to_data_uri(avatar_svg)
    mood = st.session_state.friend_companion_state
    bubble_text = st.session_state.friend_companion_message

    companion_html = f"""
    <div class="friend-companion-shell mood-{mood}">
        <div class="friend-companion-badge">
            {st.session_state.friend_name} te acompaña
        </div>

        <div class="friend-companion-avatar">
            <img src="{avatar_src}" alt="{st.session_state.friend_name}" />
        </div>

        <div class="friend-companion-bubble">
            {bubble_text}
        </div>
    </div>
    """

    render_html_block(companion_html)


# ------------------------------------------------------------
# Panel de memoria suave
# ------------------------------------------------------------
def render_friend_memory_panel(user_id: int) -> None:
    """
    Permite guardar gustos y preferencias suaves del vínculo.
    """
    st.markdown(
        """
        <div class="info-card">
            <div class="info-title">Memoria suave del vínculo</div>
            <div class="info-text">
                Aquí puedes guardar pequeños gustos y formas de apoyo para que el amigo imaginario
                responda de una forma más cercana y personal.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    with st.form("friend_memory_form"):
        favorite_color = st.text_input(
            "Color favorito",
            value=st.session_state.friend_profile.get("favorite_color", ""),
            placeholder="Ejemplo: azul, amarillo, morado"
        )

        favorite_activity = st.text_input(
            "Actividad favorita",
            value=st.session_state.friend_profile.get("favorite_activity", ""),
            placeholder="Ejemplo: dibujar, bailar, construir, cantar"
        )

        encouragement_style = st.text_input(
            "Cómo le gusta que lo animen",
            value=st.session_state.friend_profile.get("encouragement_style", ""),
            placeholder="Ejemplo: con palabras suaves, con abrazos imaginarios, con humor tierno"
        )

        preferred_comfort = st.selectbox(
            "Qué prefiere cuando necesita apoyo",
            options=["cuentos", "juegos", "respiraciones"],
            index=["cuentos", "juegos", "respiraciones"].index(
                st.session_state.friend_profile.get("preferred_comfort", "cuentos")
            )
        )

        submit_memory = st.form_submit_button(
            "Guardar recuerdos suaves",
            width="stretch"
        )

        if submit_memory:
            try:
                update_friend_profile(
                    user_id=user_id,
                    favorite_color=favorite_color,
                    favorite_activity=favorite_activity,
                    encouragement_style=encouragement_style,
                    preferred_comfort=preferred_comfort
                )

                st.session_state.friend_profile = {
                    "favorite_color": favorite_color.strip(),
                    "favorite_activity": favorite_activity.strip(),
                    "encouragement_style": encouragement_style.strip(),
                    "preferred_comfort": preferred_comfort.strip(),
                }

                if st.session_state.current_user:
                    st.session_state.current_user["favorite_color"] = favorite_color.strip()
                    st.session_state.current_user["favorite_activity"] = favorite_activity.strip()
                    st.session_state.current_user["encouragement_style"] = encouragement_style.strip()
                    st.session_state.current_user["preferred_comfort"] = preferred_comfort.strip()

                st.success("Memoria suave guardada correctamente.")
                st.rerun()

            except ValueError as error:
                st.error(str(error))


# ------------------------------------------------------------
# Panel de iniciativas del amigo imaginario
# ------------------------------------------------------------
def render_friend_initiatives_panel() -> str | None:
    """
    Muestra botones rápidos para que el Amigo Imaginario
    inicie dinámicas suaves y personalizadas.
    """
    iniciativas = build_friend_initiatives(
        friend_name=st.session_state.friend_name,
        friend_profile=st.session_state.friend_profile
    )

    st.markdown(
        f"""
        <div class="info-card">
            <div class="info-title">Ideas que puede iniciar {st.session_state.friend_name}</div>
            <div class="info-text">
                Puedes pedirle un cuento, un juego, una respiración o una sorpresa.
                Estas opciones usan los gustos guardados para que la experiencia se sienta más personal.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    col_1, col_2, col_3, col_4, col_5 = st.columns(5)
    mensaje_iniciativa = None

    with col_1:
        if st.button("Cuento", key="friend_init_cuento", width="stretch"):
            update_friend_companion_state("cuento")
            mensaje_iniciativa = iniciativas["cuento"]

    with col_2:
        if st.button("Juego", key="friend_init_juego", width="stretch"):
            update_friend_companion_state("juego")
            mensaje_iniciativa = iniciativas["juego"]

    with col_3:
        if st.button("Respirar", key="friend_init_respiracion", width="stretch"):
            update_friend_companion_state("respiracion")
            mensaje_iniciativa = iniciativas["respiracion"]

    with col_4:
        if st.button("Ánimo", key="friend_init_animo", width="stretch"):
            update_friend_companion_state("animo")
            mensaje_iniciativa = iniciativas["animo"]

    with col_5:
        if st.button("Sorpresa", key="friend_init_sorpresa", width="stretch"):
            update_friend_companion_state("feliz")
            mensaje_iniciativa = iniciativas["sorpresa"]

    return mensaje_iniciativa


# ------------------------------------------------------------
# Panel de creación y personalización del amigo imaginario
# ------------------------------------------------------------
def render_friend_creation_panel(user_id: int) -> None:
    """
    Muestra una sesión de creación para el amigo imaginario:
    nombre + avatar + guardado persistente.
    """
    st.markdown(
        """
        <div class="info-card">
            <div class="info-title">Sesión de creación de tu amigo imaginario</div>
            <div class="info-text">
                Aquí puedes ponerle nombre y personalizar su avatar.
                Cuando guardes, ese amigo aparecerá en el módulo de conversación.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    col_preview, col_form = st.columns([1.05, 1.35], gap="large")

    with col_preview:
        st.markdown("### Vista previa")
        render_friend_avatar_preview()

    with col_form:
        with st.form("friend_creation_form"):
            friend_name_input = st.text_input(
                "Nombre del amigo imaginario",
                value=st.session_state.friend_name,
                max_chars=30,
                placeholder="Ejemplo: Nube, Soli, Luno"
            )

            face_shape = st.selectbox(
                "Forma de rostro",
                options=AVATAR_FORM_OPTIONS["face_shape"],
                index=AVATAR_FORM_OPTIONS["face_shape"].index(
                    st.session_state.friend_avatar.get("face_shape", "redondo")
                )
            )

            primary_color = st.selectbox(
                "Color principal",
                options=AVATAR_FORM_OPTIONS["primary_color"],
                index=AVATAR_FORM_OPTIONS["primary_color"].index(
                    st.session_state.friend_avatar.get("primary_color", "azul")
                )
            )

            hair_style = st.selectbox(
                "Tipo de cabello",
                options=AVATAR_FORM_OPTIONS["hair_style"],
                index=AVATAR_FORM_OPTIONS["hair_style"].index(
                    st.session_state.friend_avatar.get("hair_style", "corto")
                )
            )

            hair_color = st.selectbox(
                "Color de cabello",
                options=AVATAR_FORM_OPTIONS["hair_color"],
                index=AVATAR_FORM_OPTIONS["hair_color"].index(
                    st.session_state.friend_avatar.get("hair_color", "castano")
                )
            )

            eye_style = st.selectbox(
                "Ojos",
                options=AVATAR_FORM_OPTIONS["eye_style"],
                index=AVATAR_FORM_OPTIONS["eye_style"].index(
                    st.session_state.friend_avatar.get("eye_style", "felices")
                )
            )

            mouth_style = st.selectbox(
                "Boca",
                options=AVATAR_FORM_OPTIONS["mouth_style"],
                index=AVATAR_FORM_OPTIONS["mouth_style"].index(
                    st.session_state.friend_avatar.get("mouth_style", "sonrisa")
                )
            )

            accessory = st.selectbox(
                "Accesorio",
                options=AVATAR_FORM_OPTIONS["accessory"],
                index=AVATAR_FORM_OPTIONS["accessory"].index(
                    st.session_state.friend_avatar.get("accessory", "estrella")
                )
            )

            background_style = st.selectbox(
                "Fondo",
                options=AVATAR_FORM_OPTIONS["background_style"],
                index=AVATAR_FORM_OPTIONS["background_style"].index(
                    st.session_state.friend_avatar.get("background_style", "cielo")
                )
            )

            submit_creation = st.form_submit_button(
                "Guardar amigo imaginario",
                width="stretch"
            )

            if submit_creation:
                try:
                    update_friend_name(
                        user_id=user_id,
                        friend_name=friend_name_input
                    )

                    update_imaginary_friend_profile(
                        user_id=user_id,
                        face_shape=face_shape,
                        primary_color=primary_color,
                        hair_style=hair_style,
                        hair_color=hair_color,
                        eye_style=eye_style,
                        mouth_style=mouth_style,
                        accessory=accessory,
                        background_style=background_style
                    )

                    st.session_state.friend_name = friend_name_input.strip()
                    st.session_state.friend_avatar = {
                        "face_shape": face_shape,
                        "primary_color": primary_color,
                        "hair_style": hair_style,
                        "hair_color": hair_color,
                        "eye_style": eye_style,
                        "mouth_style": mouth_style,
                        "accessory": accessory,
                        "background_style": background_style,
                    }

                    if st.session_state.current_user:
                        st.session_state.current_user["friend_name"] = friend_name_input.strip()

                    st.success("Tu amigo imaginario fue guardado correctamente.")
                    st.rerun()

                except ValueError as error:
                    st.error(str(error))


# ------------------------------------------------------------
# Panel de biblioteca estructurada
# ------------------------------------------------------------
def render_biblioteca_panel(user_id: int) -> None:
    """
    Renderiza el panel de búsqueda y lectura de artículos.
    Usa API compartida si existe token; si no, usa fallback local.
    """
    if has_shared_api_session():
        token = st.session_state.get("auth_token")

        try:
            categorias_api, tipos_lector_api = get_library_filter_options(token)

            categorias = ["Todas"] + categorias_api
            tipos_lector = ["Todos"] + tipos_lector_api

            if st.session_state.article_category_filter not in categorias:
                st.session_state.article_category_filter = "Todas"

            if st.session_state.article_reader_filter not in tipos_lector:
                st.session_state.article_reader_filter = "Todos"

            st.markdown(
                """
                <div class="info-card">
                    <div class="info-title">Biblioteca estructurada</div>
                    <div class="info-text">
                        Busca artículos por tema o tipo de lector. También puedes usar cualquier artículo como base
                        para conversar con el asistente educativo.
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

            col_f1, col_f2, col_f3 = st.columns([2, 1, 1], gap="medium")

            with col_f1:
                st.text_input(
                    "Buscar artículo",
                    key="article_search_text",
                    placeholder="Ejemplo: dislexia, ansiedad, crisis, aula..."
                )

            with col_f2:
                st.selectbox(
                    "Categoría",
                    options=categorias,
                    key="article_category_filter"
                )

            with col_f3:
                st.selectbox(
                    "Tipo de lector",
                    options=tipos_lector,
                    key="article_reader_filter"
                )

            resultados = list_library_articles(
                token=token,
                search_text=st.session_state.article_search_text,
                category=st.session_state.article_category_filter,
                reader_type=st.session_state.article_reader_filter,
            )

            ids_resultados = [articulo["id"] for articulo in resultados]

            if resultados:
                if st.session_state.selected_article_id not in ids_resultados:
                    st.session_state.selected_article_id = resultados[0]["id"]
            else:
                st.session_state.selected_article_id = None

            col_lista, col_detalle = st.columns([1.05, 1.45], gap="large")

            with col_lista:
                st.caption(f"Resultados encontrados: {len(resultados)}")

                if not resultados:
                    st.warning("No encontré artículos con esos filtros.")
                else:
                    for articulo in resultados:
                        st.markdown(
                            f"""
                            <div class="article-card">
                                <div class="article-title">{articulo["title"]}</div>
                                <div class="article-meta">{articulo["category"]} · {articulo["reader_type"]}</div>
                                <div class="article-desc">{articulo["short_description"]}</div>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )

                        if st.button(
                            "Abrir artículo",
                            key=f"abrir_articulo_{articulo['id']}",
                            width="stretch"
                        ):
                            st.session_state.selected_article_id = articulo["id"]
                            st.rerun()

            with col_detalle:
                if not st.session_state.selected_article_id:
                    st.info("Selecciona un artículo para leerlo aquí.")
                    return

                articulo = get_library_article(
                    token=token,
                    article_id=st.session_state.selected_article_id
                )

                if not articulo:
                    st.warning("No pude cargar el artículo seleccionado.")
                    return

                st.markdown(f"## {articulo['title']}")
                st.caption(f"{articulo['category']} · {articulo['reader_type']}")

                st.markdown(
                    f"""
                    <div class="info-card">
                        <div class="info-text">{articulo["short_description"]}</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                st.markdown(articulo["content"])

                col_a, col_b = st.columns(2)

                with col_a:
                    if st.button(
                        "Llevar este artículo al chat educativo",
                        key=f"usar_articulo_chat_{articulo['id']}",
                        width="stretch"
                    ):
                        st.session_state.pending_message = (
                            f"Quiero entender mejor este artículo.\n\n"
                            f"Título: {articulo['title']}\n"
                            f"Categoría: {articulo['category']}\n"
                            f"Tipo de lector: {articulo['reader_type']}\n"
                            f"Resumen: {articulo['short_description']}\n\n"
                            f"Contenido del artículo:\n{articulo['content']}\n\n"
                            "Explícamelo con lenguaje sencillo y dame 3 ideas prácticas."
                        )
                        st.rerun()

                with col_b:
                    if st.button(
                        "Crear un chat nuevo sobre este tema",
                        key=f"nuevo_chat_articulo_{articulo['id']}",
                        width="stretch"
                    ):
                        st.session_state.pending_message = (
                            f"Quiero hablar sobre este tema: {articulo['title']}. "
                            "Ayúdame a entenderlo mejor con palabras sencillas."
                        )
                        st.session_state.conversation_id = None
                        st.session_state.mensajes = []
                        st.rerun()

            return

        except Exception as error:
            st.error(f"No se pudo cargar la biblioteca compartida: {error}")
            return

    # --------------------------------------------------------
    # Fallback local
    # --------------------------------------------------------
    categorias = ["Todas"] + list_article_categories()
    tipos_lector = ["Todos"] + list_reader_types()

    if st.session_state.article_category_filter not in categorias:
        st.session_state.article_category_filter = "Todas"

    if st.session_state.article_reader_filter not in tipos_lector:
        st.session_state.article_reader_filter = "Todos"

    st.markdown(
        """
        <div class="info-card">
            <div class="info-title">Biblioteca estructurada</div>
            <div class="info-text">
                Busca artículos por tema o tipo de lector. También puedes usar cualquier artículo como base
                para conversar con el asistente educativo.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    col_f1, col_f2, col_f3 = st.columns([2, 1, 1], gap="medium")

    with col_f1:
        st.text_input(
            "Buscar artículo",
            key="article_search_text",
            placeholder="Ejemplo: dislexia, ansiedad, crisis, aula..."
        )

    with col_f2:
        st.selectbox(
            "Categoría",
            options=categorias,
            key="article_category_filter"
        )

    with col_f3:
        st.selectbox(
            "Tipo de lector",
            options=tipos_lector,
            key="article_reader_filter"
        )

    resultados = search_articles(
        search_text=st.session_state.article_search_text,
        category=st.session_state.article_category_filter,
        reader_type=st.session_state.article_reader_filter,
        limit=100
    )

    ids_resultados = [articulo["id"] for articulo in resultados]

    if resultados:
        if st.session_state.selected_article_id not in ids_resultados:
            st.session_state.selected_article_id = resultados[0]["id"]
    else:
        st.session_state.selected_article_id = None

    col_lista, col_detalle = st.columns([1.05, 1.45], gap="large")

    with col_lista:
        st.caption(f"Resultados encontrados: {len(resultados)}")

        if not resultados:
            st.warning("No encontré artículos con esos filtros.")
        else:
            for articulo in resultados:
                st.markdown(
                    f"""
                    <div class="article-card">
                        <div class="article-title">{articulo["title"]}</div>
                        <div class="article-meta">{articulo["category"]} · {articulo["reader_type"]}</div>
                        <div class="article-desc">{articulo["short_description"]}</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                if st.button(
                    "Abrir artículo",
                    key=f"abrir_articulo_{articulo['id']}",
                    width="stretch"
                ):
                    st.session_state.selected_article_id = articulo["id"]
                    st.rerun()

    with col_detalle:
        if not st.session_state.selected_article_id:
            st.info("Selecciona un artículo para leerlo aquí.")
            return

        articulo = get_article_by_id(st.session_state.selected_article_id)

        if not articulo:
            st.warning("No pude cargar el artículo seleccionado.")
            return

        st.markdown(f"## {articulo['title']}")
        st.caption(f"{articulo['category']} · {articulo['reader_type']}")

        st.markdown(
            f"""
            <div class="info-card">
                <div class="info-text">{articulo["short_description"]}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

        st.markdown(articulo["content"])

        col_a, col_b = st.columns(2)

        with col_a:
            if st.button(
                "Llevar este artículo al chat educativo",
                key=f"usar_articulo_chat_{articulo['id']}",
                width="stretch"
            ):
                st.session_state.pending_message = (
                    f"Quiero entender mejor este artículo.\n\n"
                    f"Título: {articulo['title']}\n"
                    f"Categoría: {articulo['category']}\n"
                    f"Tipo de lector: {articulo['reader_type']}\n"
                    f"Resumen: {articulo['short_description']}\n\n"
                    f"Contenido del artículo:\n{articulo['content']}\n\n"
                    "Explícamelo con lenguaje sencillo y dame 3 ideas prácticas."
                )
                st.rerun()

        with col_b:
            if st.button(
                "Crear un chat nuevo sobre este tema",
                key=f"nuevo_chat_articulo_{articulo['id']}",
                width="stretch"
            ):
                st.session_state.pending_message = (
                    f"Quiero hablar sobre este tema: {articulo['title']}. "
                    "Ayúdame a entenderlo mejor con palabras sencillas."
                )
                st.session_state.conversation_id = None
                st.session_state.mensajes = []
                st.rerun()


# ------------------------------------------------------------
# Panel para convertir documentos en artículos
# ------------------------------------------------------------
def render_document_ingestion_panel() -> None:
    """
    Permite subir un documento y convertirlo en un artículo
    para la biblioteca usando Gemini.
    """
    st.markdown(
        """
        <div class="info-card">
            <div class="info-title">Generar artículo desde documento</div>
            <div class="info-text">
                Sube un PDF, TXT o MD. La app extraerá el texto y generará un artículo estructurado
                para guardarlo en la biblioteca.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    uploaded_doc = st.file_uploader(
        "Sube un documento",
        type=["pdf", "txt", "md"],
        key="admin_document_uploader"
    )

    col_meta_1, col_meta_2 = st.columns(2)

    with col_meta_1:
        categoria_destino = st.text_input(
            "Categoría destino",
            value="General",
            key="admin_doc_category"
        )

    with col_meta_2:
        reader_type_destino = st.selectbox(
            "Tipo de lector destino",
            options=["Usuario", "Padre/Cuidador", "Docente"],
            key="admin_doc_reader_type"
        )

    titulo_sugerido = st.text_input(
        "Título sugerido (opcional)",
        placeholder="Si lo dejas vacío, se tomará del archivo o lo propondrá la IA",
        key="admin_doc_title"
    )

    info_documento = None

    if uploaded_doc is not None:
        try:
            info_documento = extract_text_from_uploaded_file(
                uploaded_doc,
                max_chars=45000
            )

            col_info_1, col_info_2, col_info_3 = st.columns(3)

            with col_info_1:
                st.caption(f"Archivo: {info_documento['filename']}")

            with col_info_2:
                st.caption(f"Texto útil: {info_documento['used_length']} caracteres")

            with col_info_3:
                if info_documento["was_truncated"]:
                    st.caption("Se usará una parte del texto")
                else:
                    st.caption("Se usará el texto completo")

            with st.expander("Vista previa del texto extraído"):
                st.text(info_documento["preview"])

        except Exception as error:
            st.error(f"No pude leer el documento: {error}")

    col_accion_1, col_accion_2 = st.columns(2)

    with col_accion_1:
        generar_guardar = st.button(
            "Generar y guardar artículo",
            width="stretch",
            key="admin_generate_article_from_doc"
        )

    with col_accion_2:
        llevar_chat = st.button(
            "Usar documento como base para chat",
            width="stretch",
            key="admin_send_doc_to_chat"
        )

    if generar_guardar:
        if uploaded_doc is None:
            st.warning("Primero sube un documento.")
        else:
            try:
                with st.spinner("Extrayendo texto y generando artículo..."):
                    info_documento = extract_text_from_uploaded_file(
                        uploaded_doc,
                        max_chars=45000
                    )

                    articulo_generado = generar_articulo_desde_documento(
                        texto_fuente=info_documento["text"],
                        category=categoria_destino,
                        reader_type=reader_type_destino,
                        suggested_title=titulo_sugerido,
                        source_name=info_documento["base_title"]
                    )

                    article_id = create_article(
                        title=articulo_generado["title"],
                        category=articulo_generado["category"],
                        reader_type=articulo_generado["reader_type"],
                        short_description=articulo_generado["short_description"],
                        content=articulo_generado["content"]
                    )

                st.session_state.selected_article_id = article_id
                st.success("Artículo generado y guardado correctamente.")

                if info_documento["was_truncated"]:
                    st.info(
                        "El documento era largo, así que se usó una parte del texto para generar el artículo."
                    )

                st.rerun()

            except Exception as error:
                st.error(f"No se pudo generar el artículo: {error}")

    if llevar_chat:
        if uploaded_doc is None:
            st.warning("Primero sube un documento.")
        else:
            try:
                info_documento = extract_text_from_uploaded_file(
                    uploaded_doc,
                    max_chars=20000
                )

                st.session_state.pending_message = (
                    f"Quiero entender mejor este documento.\n\n"
                    f"Archivo: {info_documento['filename']}\n"
                    f"Título sugerido: {titulo_sugerido or info_documento['base_title']}\n"
                    f"Categoría sugerida: {categoria_destino}\n"
                    f"Tipo de lector: {reader_type_destino}\n\n"
                    f"Contenido del documento:\n{info_documento['text']}\n\n"
                    "Explícamelo con lenguaje sencillo y conviértelo en ideas prácticas."
                )

                st.success("Documento enviado como base para el chat educativo.")
                st.rerun()

            except Exception as error:
                st.error(f"No se pudo preparar el documento para el chat: {error}")


# ------------------------------------------------------------
# Panel de administración
# ------------------------------------------------------------
def render_admin_panel() -> None:
    """
    Renderiza el panel de administración para artículos,
    importación/exportación, documentos, métricas y usuarios.
    """
    st.markdown(
        """
        <div class="info-card">
            <div class="info-title">Panel de administración</div>
            <div class="info-text">
                Desde aquí puedes crear, editar, eliminar, importar, exportar o generar artículos desde documentos,
                revisar métricas de utilidad y gestionar permisos de administrador.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    tab_articulos, tab_import_export, tab_documentos, tab_metricas, tab_usuarios = st.tabs(
        ["Administrar artículos", "Importar / Exportar", "Documentos", "Métricas", "Usuarios"]
    )

    with tab_articulos:
        articulos = search_articles(limit=500)

        opciones_articulos = [("nuevo", "Crear artículo nuevo")]
        opciones_articulos += [
            (str(articulo["id"]), f"{articulo['title']} · {articulo['category']} · {articulo['reader_type']}")
            for articulo in articulos
        ]

        valores_opciones = [opcion[0] for opcion in opciones_articulos]
        etiquetas_opciones = {opcion[0]: opcion[1] for opcion in opciones_articulos}

        seleccion = st.selectbox(
            "Selecciona un artículo para editar o crea uno nuevo",
            options=valores_opciones,
            format_func=lambda clave: etiquetas_opciones[clave]
        )

        articulo_actual = None

        if seleccion != "nuevo":
            articulo_actual = get_article_by_id(int(seleccion))
            st.session_state.admin_edit_article_id = int(seleccion)
        else:
            st.session_state.admin_edit_article_id = None

        with st.form("admin_article_form"):
            title = st.text_input(
                "Título",
                value=articulo_actual["title"] if articulo_actual else ""
            )

            col1, col2 = st.columns(2)

            with col1:
                category = st.text_input(
                    "Categoría",
                    value=articulo_actual["category"] if articulo_actual else ""
                )

            with col2:
                reader_type = st.selectbox(
                    "Tipo de lector",
                    options=["Usuario", "Padre/Cuidador", "Docente"],
                    index=["Usuario", "Padre/Cuidador", "Docente"].index(
                        articulo_actual["reader_type"]
                    ) if articulo_actual and articulo_actual["reader_type"] in ["Usuario", "Padre/Cuidador", "Docente"] else 0
                )

            short_description = st.text_area(
                "Descripción breve",
                value=articulo_actual["short_description"] if articulo_actual else "",
                height=120
            )

            content = st.text_area(
                "Contenido del artículo",
                value=articulo_actual["content"] if articulo_actual else "",
                height=320
            )

            col_guardar, col_eliminar = st.columns(2)

            with col_guardar:
                submit_save = st.form_submit_button(
                    "Guardar cambios",
                    width="stretch"
                )

            with col_eliminar:
                submit_delete = st.form_submit_button(
                    "Eliminar artículo",
                    width="stretch"
                )

            if submit_save:
                try:
                    if articulo_actual:
                        update_article(
                            article_id=articulo_actual["id"],
                            title=title,
                            category=category,
                            reader_type=reader_type,
                            short_description=short_description,
                            content=content
                        )
                        st.success("Artículo actualizado correctamente.")
                    else:
                        new_id = create_article(
                            title=title,
                            category=category,
                            reader_type=reader_type,
                            short_description=short_description,
                            content=content
                        )
                        st.session_state.selected_article_id = new_id
                        st.success("Artículo creado correctamente.")

                    st.rerun()

                except ValueError as error:
                    st.error(str(error))

            if submit_delete:
                if articulo_actual:
                    delete_article(articulo_actual["id"])

                    if st.session_state.selected_article_id == articulo_actual["id"]:
                        st.session_state.selected_article_id = None

                    st.success("Artículo eliminado correctamente.")
                    st.rerun()
                else:
                    st.warning("No hay un artículo seleccionado para eliminar.")

    with tab_import_export:
        st.markdown("### Plantillas")
        col_temp_1, col_temp_2 = st.columns(2)

        with col_temp_1:
            st.download_button(
                "Descargar plantilla CSV",
                data=build_template_csv(),
                file_name="plantilla_articulos.csv",
                mime="text/csv",
                width="stretch"
            )

        with col_temp_2:
            st.download_button(
                "Descargar plantilla JSON",
                data=build_template_json(),
                file_name="plantilla_articulos.json",
                mime="application/json",
                width="stretch"
            )

        st.markdown("### Importar artículos")
        st.caption("Columnas esperadas: title, category, reader_type, short_description, content")

        duplicate_mode_ui = st.selectbox(
            "Cómo tratar duplicados",
            options=[
                "Omitir duplicados",
                "Reemplazar duplicados",
                "Permitir duplicados"
            ]
        )

        duplicate_mode_map = {
            "Omitir duplicados": "skip",
            "Reemplazar duplicados": "replace",
            "Permitir duplicados": "allow"
        }

        uploaded_file = st.file_uploader(
            "Sube un archivo CSV o JSON",
            type=["csv", "json"]
        )

        parsed_rows = []

        if uploaded_file is not None:
            try:
                parsed_rows = parse_uploaded_articles(uploaded_file)
                st.success(f"Archivo leído correctamente. Registros detectados: {len(parsed_rows)}")

                with st.expander("Vista previa de los primeros registros"):
                    st.json(parsed_rows[:3])

            except Exception as error:
                st.error(f"No pude leer el archivo: {error}")

        if st.button("Importar artículos", width="stretch"):
            if not uploaded_file:
                st.warning("Primero sube un archivo CSV o JSON.")
            else:
                try:
                    if not parsed_rows:
                        parsed_rows = parse_uploaded_articles(uploaded_file)

                    result = import_articles(
                        records=parsed_rows,
                        duplicate_mode=duplicate_mode_map[duplicate_mode_ui]
                    )

                    st.success(
                        f"Importación terminada. Creados: {result['created']} · "
                        f"Actualizados: {result['updated']} · "
                        f"Omitidos: {result['skipped']}"
                    )

                    if result["errors"]:
                        with st.expander("Errores detectados durante la importación"):
                            for error in result["errors"]:
                                st.write(f"- {error}")

                    st.rerun()

                except Exception as error:
                    st.error(f"No se pudo importar el archivo: {error}")

        st.markdown("### Exportar artículos")
        articulos_export = list_all_articles(limit=5000)

        col_exp_1, col_exp_2 = st.columns(2)

        with col_exp_1:
            st.download_button(
                "Exportar biblioteca a CSV",
                data=build_export_csv(articulos_export),
                file_name="biblioteca_articulos.csv",
                mime="text/csv",
                width="stretch"
            )

        with col_exp_2:
            st.download_button(
                "Exportar biblioteca a JSON",
                data=build_export_json(articulos_export),
                file_name="biblioteca_articulos.json",
                mime="application/json",
                width="stretch"
            )

    with tab_documentos:
        render_document_ingestion_panel()

    with tab_metricas:
        render_feedback_metrics_panel()

    with tab_usuarios:
        usuarios = list_users(limit=200)

        st.caption("Aquí puedes revisar usuarios y activar o quitar permisos de administrador.")

        for usuario in usuarios:
            col_info, col_toggle = st.columns([3, 1])

            with col_info:
                rol = "Administrador" if usuario["is_admin"] else "Usuario"
                st.markdown(
                    f"**{usuario['display_name']}**  \n@{usuario['username']} · {rol}"
                )

            with col_toggle:
                nuevo_estado = st.checkbox(
                    "Admin",
                    value=usuario["is_admin"],
                    key=f"admin_toggle_{usuario['id']}"
                )

                if nuevo_estado != usuario["is_admin"]:
                    set_user_admin_status(
                        user_id=usuario["id"],
                        is_admin=nuevo_estado
                    )

                    if usuario["id"] == st.session_state.user_id:
                        st.session_state.is_admin = nuevo_estado

                    if st.session_state.current_user and usuario["id"] == st.session_state.current_user.get("id"):
                        st.session_state.current_user["is_admin"] = nuevo_estado

                    st.rerun()


# ------------------------------------------------------------
# Obtener datos básicos del usuario OIDC actual
# ------------------------------------------------------------
def get_google_oidc_identity() -> dict:
    """
    Extrae datos del usuario autenticado por OIDC en Streamlit.
    """
    if not getattr(st.user, "is_logged_in", False):
        return {
            "sub": "",
            "email": "",
            "name": ""
        }

    google_sub = str(getattr(st.user, "sub", "") or "").strip()
    email = str(getattr(st.user, "email", "") or "").strip().lower()
    name = str(getattr(st.user, "name", "") or "").strip()

    return {
        "sub": google_sub,
        "email": email,
        "name": name
    }


# ------------------------------------------------------------
# Sincronizar sesión local con login de Google
# ------------------------------------------------------------
def sync_google_login_to_local_user() -> None:
    """
    Si el usuario ya inició sesión con Google mediante OIDC,
    lo busca en SQLite o lo crea automáticamente y luego
    inicia sesión local en la app.

    Nota:
        Esta ruta funciona como fallback local. La sesión Google
        aún no genera token JWT compartido para FastAPI.
    """
    if not getattr(st.user, "is_logged_in", False):
        return

    if st.session_state.user_id is not None:
        return

    oidc_user = get_google_oidc_identity()

    google_sub = oidc_user["sub"]
    email = oidc_user["email"]
    name = oidc_user["name"]

    if not google_sub or not email:
        st.error("No pude leer correctamente la identidad de Google.")
        return

    usuario = get_user_by_google_sub(google_sub)

    if not usuario:
        usuario = create_google_user(
            google_sub=google_sub,
            email=email,
            display_name=name
        )

    iniciar_sesion(
        usuario=usuario,
        auth_token=None,
        reset_chat_state=True
    )


# ------------------------------------------------------------
# Cerrar sesión completa local + Google OIDC
# ------------------------------------------------------------
def logout_everything() -> None:
    """
    Limpia la sesión local y, si existe sesión OIDC, la cierra
    con Streamlit.
    """
    cerrar_sesion()

    if getattr(st.user, "is_logged_in", False):
        st.logout()


# ------------------------------------------------------------
# Pantalla de autenticación
# ------------------------------------------------------------
def render_auth_screen() -> None:
    """
    Muestra login compartido vía FastAPI, registro compartido
    y acceso con Google OIDC.
    """
    st.markdown('<div class="auth-shell">', unsafe_allow_html=True)

    st.markdown('<div class="main-title">Amigo Imaginario Neurodivergente</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="main-subtitle">Fase 17 · Login compartido web / móvil + fallback Google</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        """
        <div class="hero-card">
            <div class="hero-title">Entra como quieras</div>
            <div class="hero-text">
                Puedes usar tu cuenta compartida entre web y móvil o entrar con Google.
                Si es tu primera vez con Google, tu cuenta local se creará automáticamente.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        f"""
        <div class="info-card">
            <div class="info-title">Aviso de uso</div>
            <div class="info-text">{LEGAL_NOTICE_TEXT}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

    col_info, col_auth = st.columns([1.05, 1.25], gap="large")

    with col_info:
        st.markdown(
            """
            <div class="info-card">
                <div class="info-title">Qué puedes hacer aquí</div>
                <div class="info-text">
                    • Conversar con un acompañante empático<br>
                    • Crear y personalizar tu amigo imaginario<br>
                    • Guardar historial por usuario<br>
                    • Entrar con cuenta compartida web / móvil<br>
                    • Entrar con Google
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        st.markdown("### Acceso con Google")
        st.caption("Google entra en modo local de respaldo mientras terminamos la sincronización completa con API.")

        st.button(
            "Continuar con Google",
            width="stretch",
            on_click=st.login
        )

    with col_auth:
        tab_login, tab_register = st.tabs(["Iniciar sesión", "Crear cuenta"])

        with tab_login:
            with st.form("login_form"):
                username = st.text_input(
                    "Nombre de usuario",
                    placeholder="Ejemplo: maria123"
                )

                password = st.text_input(
                    "Contraseña",
                    type="password",
                    placeholder="Tu contraseña"
                )

                submit_login = st.form_submit_button("Entrar", width="stretch")

                if submit_login:
                    try:
                        if not username.strip():
                            st.error("Escribe tu usuario.")
                        elif not password:
                            st.error("Escribe tu contraseña.")
                        else:
                            auth = login_web_user(username, password)
                            iniciar_sesion(
                                usuario=auth["user"],
                                auth_token=auth["access_token"],
                                reset_chat_state=True
                            )
                            st.success("Sesión iniciada correctamente.")
                            st.rerun()
                    except Exception as error:
                        st.error(str(error))

        with tab_register:
            with st.form("register_form"):
                display_name = st.text_input(
                    "Nombre visible",
                    placeholder="Cómo quieres que te llamemos"
                )

                username = st.text_input(
                    "Nombre de usuario",
                    placeholder="Debe ser único"
                )

                password = st.text_input(
                    "Contraseña",
                    type="password",
                    placeholder="Mínimo 8 caracteres"
                )

                confirm_password = st.text_input(
                    "Confirmar contraseña",
                    type="password",
                    placeholder="Escribe la contraseña de nuevo"
                )

                submit_register = st.form_submit_button("Crear cuenta", width="stretch")

                if submit_register:
                    try:
                        if password != confirm_password:
                            st.error("Las contraseñas no coinciden.")
                        elif len(username.strip()) < 3:
                            st.error("El nombre de usuario debe tener al menos 3 caracteres.")
                        elif len(password) < 8:
                            st.error("La contraseña debe tener al menos 8 caracteres.")
                        else:
                            auth = register_web_user(display_name, username, password)
                            iniciar_sesion(
                                usuario=auth["user"],
                                auth_token=auth["access_token"],
                                reset_chat_state=True
                            )
                            st.success("Cuenta creada correctamente.")
                            st.rerun()
                    except Exception as error:
                        st.error(str(error))

    st.markdown('</div>', unsafe_allow_html=True)


# ------------------------------------------------------------
# Procesar mensaje de chat
# ------------------------------------------------------------
def procesar_mensaje_chat(
    user_id: int,
    modulo_actual: str,
    mensaje_usuario: str
) -> None:
    """
    Procesa un mensaje del usuario.

    Incluye:
    - validación para no usar admin_panel como chat
    - envío por API compartida cuando hay token
    - fallback local
    - control de tokens en modo local
    """
    if not es_modulo_chat(modulo_actual):
        st.error("Este módulo no utiliza chat.")
        return

    # --------------------------------------------------------
    # Flujo con API compartida FastAPI
    # Aquí el backend ya valida permisos, guests y tokens.
    # --------------------------------------------------------
    if has_shared_api_session():
        token = st.session_state.get("auth_token")
        conversation_id = st.session_state.get("conversation_id")

        if not conversation_id:
            crear_y_cargar_nueva_conversacion(modulo_actual, user_id)
            conversation_id = st.session_state.get("conversation_id")

        with st.chat_message("user"):
            st.markdown(mensaje_usuario)

        with st.chat_message("assistant"):
            with st.spinner("Pensando..."):
                try:
                    result = send_web_chat_message(
                        token=token,
                        conversation_id=conversation_id,
                        content=mensaje_usuario
                    )

                    user_message = result.get("user_message", {})
                    assistant_message = result.get("assistant_message", {})

                    if result.get("token_status"):
                        st.session_state.token_status = result["token_status"]

                    if not assistant_message.get("content", "").strip():
                        assistant_message["content"] = (
                            "No pude generar una respuesta en este momento. "
                            "Intenta nuevamente."
                        )

                except Exception as error:
                    st.error(f"No se pudo enviar el mensaje: {error}")
                    return

            st.markdown(assistant_message["content"])

        st.session_state.mensajes.append({
            "id": user_message.get("id"),
            "role": user_message.get("role", "user"),
            "content": user_message.get("content", mensaje_usuario),
        })

        st.session_state.mensajes.append({
            "id": assistant_message.get("id"),
            "role": assistant_message.get("role", "assistant"),
            "content": assistant_message.get("content", ""),
        })

        cargar_conversacion(conversation_id, user_id)
        refrescar_tokens_sesion()
        st.rerun()
        return

    # --------------------------------------------------------
    # Fallback local con control de tokens
    # --------------------------------------------------------
    if not st.session_state.conversation_id:
        crear_y_cargar_nueva_conversacion(modulo_actual, user_id)

    conversation_id = st.session_state.conversation_id

    puede_enviar, token_status = can_send_message_with_tokens(user_id)

    user_message_id = add_message(
        conversation_id=conversation_id,
        role="user",
        content=mensaje_usuario
    )

    st.session_state.mensajes.append({
        "id": user_message_id,
        "role": "user",
        "content": mensaje_usuario
    })

    update_title_if_default(
        conversation_id=conversation_id,
        user_id=user_id,
        user_message=mensaje_usuario
    )

    with st.chat_message("user"):
        st.markdown(mensaje_usuario)

    if not puede_enviar:
        respuesta = build_no_tokens_assistant_message(user_id)

        with st.chat_message("assistant"):
            st.markdown(respuesta)

        assistant_message_id = add_message(
            conversation_id=conversation_id,
            role="assistant",
            content=respuesta
        )

        st.session_state.mensajes.append({
            "id": assistant_message_id,
            "role": "assistant",
            "content": respuesta
        })

        refrescar_tokens_sesion()
        cargar_conversacion(conversation_id, user_id)
        st.rerun()
        return

    with st.chat_message("assistant"):
        with st.spinner("Pensando..."):
            try:
                if modulo_actual == "biblioteca_inteligente":
                    respuesta = generar_respuesta_biblioteca_rag(
                        mensajes=st.session_state.mensajes
                    )
                else:
                    respuesta = generar_respuesta(
                        modulo=modulo_actual,
                        mensajes=st.session_state.mensajes,
                        friend_name=st.session_state.friend_name,
                        friend_profile=st.session_state.friend_profile
                    )

                if not respuesta or not respuesta.strip():
                    respuesta = (
                        "No pude generar una respuesta en este momento. "
                        "Intenta reformular tu mensaje."
                    )

            except Exception as error:
                respuesta = (
                    "El servicio está temporalmente ocupado o hubo un problema "
                    "al responder. Intenta nuevamente en unos segundos."
                )
                st.caption(f"Detalle técnico: {error}")

        st.markdown(respuesta)

    # --------------------------------------------------------
    # Consumir token después de generar respuesta
    # --------------------------------------------------------
    consume_user_token(
        user_id=user_id,
        conversation_id=conversation_id,
        module=modulo_actual,
        amount=1,
        reason="chat_message",
    )

    assistant_message_id = add_message(
        conversation_id=conversation_id,
        role="assistant",
        content=respuesta
    )

    st.session_state.mensajes.append({
        "id": assistant_message_id,
        "role": "assistant",
        "content": respuesta
    })

    refrescar_tokens_sesion()
    cargar_conversacion(conversation_id, user_id)
    st.rerun()
# ------------------------------------------------------------
# Panel de administración de roles, guests y tokens
# ------------------------------------------------------------
def render_access_control_admin_panel() -> None:
    """
    Panel principal para superadmin:
    - usuarios
    - roles
    - cuentas guest
    - tokens
    - acceso al panel de biblioteca existente
    """
    token = st.session_state.get("auth_token")

    if not token:
        st.warning(
            "Este panel requiere sesión compartida con FastAPI. "
            "Cierra sesión e inicia con el formulario normal para obtener token."
        )
        return

    st.markdown(
        """
        <div class="info-card">
            <div class="info-title">Panel de administración</div>
            <div class="info-text">
                Administra usuarios, roles, cuentas guest, tokens y biblioteca.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    tab_usuarios, tab_guests, tab_crear_guest, tab_tokens, tab_biblioteca = st.tabs(
        [
            "Usuarios",
            "Cuentas guest",
            "Crear guest",
            "Tokens",
            "Biblioteca",
        ]
    )

    # --------------------------------------------------------
    # Usuarios y roles
    # --------------------------------------------------------
    with tab_usuarios:
        st.subheader("Usuarios registrados")

        try:
            usuarios = admin_list_users(token)
        except Exception as error:
            st.error(f"No se pudieron cargar usuarios: {error}")
            usuarios = []

        if not usuarios:
            st.info("No hay usuarios disponibles.")
        else:
            for usuario in usuarios:
                with st.expander(
                    f"{usuario.get('display_name')} · @{usuario.get('username')} · {usuario.get('role_label')}"
                ):
                    st.write(f"ID: {usuario.get('id')}")
                    st.write(f"Tipo de cuenta: {usuario.get('account_type')}")
                    st.write(f"Estado activo: {usuario.get('is_active')}")

                    rol_actual = usuario.get("role", "child")

                    opciones_roles = [
                        "superadmin",
                        "parent_admin",
                        "child",
                    ]

                    rol_nuevo = st.selectbox(
                        "Rol",
                        opciones_roles,
                        index=opciones_roles.index(rol_actual)
                        if rol_actual in opciones_roles
                        else 2,
                        key=f"rol_usuario_{usuario.get('id')}",
                    )

                    if st.button(
                        "Actualizar rol",
                        key=f"btn_rol_usuario_{usuario.get('id')}"
                    ):
                        try:
                            admin_update_user_role(
                                token=token,
                                user_id=usuario["id"],
                                role=rol_nuevo,
                            )
                            st.success("Rol actualizado correctamente.")
                            st.rerun()
                        except Exception as error:
                            st.error(f"No se pudo actualizar el rol: {error}")

    # --------------------------------------------------------
    # Cuentas guest
    # --------------------------------------------------------
    with tab_guests:
        st.subheader("Cuentas guest temporales")

        try:
            guests = admin_list_guests(token)
        except Exception as error:
            st.error(f"No se pudieron cargar cuentas guest: {error}")
            guests = []

        if not guests:
            st.info("Aún no hay cuentas guest.")
        else:
            for guest in guests:
                with st.expander(
                    f"{guest.get('display_name')} · @{guest.get('username')} · {guest.get('guest_status')}"
                ):
                    st.write(f"Tipo: {guest.get('role_label')}")
                    st.write(f"Horas asignadas: {guest.get('guest_hours')}")
                    st.write(f"Expira: {guest.get('guest_expires_at')}")
                    st.write(f"Tiempo restante: {guest.get('remaining_guest_time')}")

                    col_extender, col_desactivar = st.columns(2)

                    with col_extender:
                        horas_extra = st.number_input(
                            "Horas extra",
                            min_value=1,
                            max_value=720,
                            value=1,
                            key=f"horas_extra_guest_{guest.get('id')}",
                        )

                        if st.button(
                            "Extender acceso",
                            key=f"btn_extender_guest_{guest.get('id')}"
                        ):
                            try:
                                admin_extend_guest(
                                    token=token,
                                    user_id=guest["id"],
                                    extra_hours=int(horas_extra),
                                )
                                st.success("Acceso extendido correctamente.")
                                st.rerun()
                            except Exception as error:
                                st.error(f"No se pudo extender el acceso: {error}")

                    with col_desactivar:
                        st.write("")
                        st.write("")

                        if st.button(
                            "Desactivar cuenta",
                            key=f"btn_desactivar_guest_{guest.get('id')}"
                        ):
                            try:
                                admin_deactivate_guest(
                                    token=token,
                                    user_id=guest["id"],
                                )
                                st.success("Cuenta guest desactivada.")
                                st.rerun()
                            except Exception as error:
                                st.error(f"No se pudo desactivar la cuenta: {error}")

    # --------------------------------------------------------
    # Crear guest
    # --------------------------------------------------------
    with tab_crear_guest:
        st.subheader("Crear cuenta guest")

        with st.form("form_crear_guest"):
            display_name = st.text_input("Nombre visible")
            username = st.text_input("Usuario guest")
            password = st.text_input("Contraseña", type="password")

            guest_type = st.selectbox(
                "Tipo de guest",
                ["guest_child", "guest_parent"],
                format_func=lambda value: "Guest niño" if value == "guest_child" else "Guest padre",
            )

            hours = st.number_input(
                "Horas de acceso",
                min_value=1,
                max_value=720,
                value=4,
            )

            token_limit = st.number_input(
                "Tokens asignados",
                min_value=0,
                max_value=1000,
                value=10,
            )

            crear = st.form_submit_button("Crear cuenta guest")

        if crear:
            try:
                admin_create_guest(
                    token=token,
                    username=username,
                    password=password,
                    display_name=display_name,
                    guest_type=guest_type,
                    hours=int(hours),
                    token_limit=int(token_limit),
                )
                st.success("Cuenta guest creada correctamente.")
                st.rerun()
            except Exception as error:
                st.error(f"No se pudo crear la cuenta guest: {error}")

    # --------------------------------------------------------
    # Tokens
    # --------------------------------------------------------
    with tab_tokens:
        st.subheader("Configuración de tokens")

        try:
            usuarios = admin_list_users(token)
        except Exception as error:
            st.error(f"No se pudieron cargar usuarios: {error}")
            usuarios = []

        if not usuarios:
            st.info("No hay usuarios disponibles.")
        else:
            ids_usuarios = [usuario["id"] for usuario in usuarios]

            usuario_id = st.selectbox(
                "Selecciona usuario",
                ids_usuarios,
                format_func=lambda user_id: next(
                    f"{usuario['display_name']} · @{usuario['username']} · {usuario['role_label']}"
                    for usuario in usuarios
                    if usuario["id"] == user_id
                ),
            )

            usuario_actual = next(
                usuario
                for usuario in usuarios
                if usuario["id"] == usuario_id
            )

            token_status = usuario_actual.get("token_status") or {}

            with st.form(f"form_tokens_{usuario_id}"):
                daily_limit = st.number_input(
                    "Tokens por periodo",
                    min_value=0,
                    max_value=10000,
                    value=int(token_status.get("daily_limit", 20)),
                )

                reset_interval_hours = st.number_input(
                    "Reiniciar cada cuántas horas",
                    min_value=1,
                    max_value=720,
                    value=int(token_status.get("reset_interval_hours", 24)),
                )

                low_threshold = st.number_input(
                    "Advertir cuando queden",
                    min_value=0,
                    max_value=1000,
                    value=int(token_status.get("low_threshold", 5)),
                )

                actualizar = st.form_submit_button("Actualizar tokens")

            if actualizar:
                try:
                    admin_update_token_policy(
                        token=token,
                        user_id=usuario_id,
                        daily_limit=int(daily_limit),
                        reset_interval_hours=int(reset_interval_hours),
                        low_threshold=int(low_threshold),
                    )
                    st.success("Tokens actualizados correctamente.")
                    st.rerun()
                except Exception as error:
                    st.error(f"No se pudieron actualizar los tokens: {error}")

    # --------------------------------------------------------
    # Biblioteca existente
    # --------------------------------------------------------
    with tab_biblioteca:
        st.subheader("Administración de biblioteca")
        render_admin_panel()

# ------------------------------------------------------------
# Vista principal autenticada
# ------------------------------------------------------------
def render_app() -> None:
    """
    Renderiza la aplicación principal una vez autenticado.

    Corrección importante:
        admin_panel se muestra como panel administrativo,
        no como conversación.
    """
    user_id = st.session_state.user_id
    display_name = st.session_state.display_name
    username = st.session_state.username
    is_admin = st.session_state.is_admin
    shared_api = has_shared_api_session()

    # --------------------------------------------------------
    # Obtener módulos permitidos por rol
    # --------------------------------------------------------
    modulos_visibles = obtener_modulos_visibles_sesion()

    if st.session_state.modulo_actual not in modulos_visibles:
        st.session_state.modulo_actual = modulos_visibles[0]
        st.session_state.ultimo_modulo = modulos_visibles[0]
        st.session_state.conversation_id = None
        st.session_state.mensajes = []

    modulo_actual = st.session_state.modulo_actual

    # --------------------------------------------------------
    # Solo asegurar conversación si es módulo de chat
    # --------------------------------------------------------
    if es_modulo_chat(modulo_actual):
        asegurar_conversacion_activa(modulo_actual, user_id)
    else:
        st.session_state.conversation_id = None
        st.session_state.mensajes = []

    info_modulo = MODULE_INFO[modulo_actual]
    conversaciones_modulo = obtener_conversaciones_modulo(modulo_actual, user_id)

    # --------------------------------------------------------
    # Sidebar
    # --------------------------------------------------------
    with st.sidebar:
        st.subheader("Tu sesión")
        st.write(f"**{display_name}**")

        rol_sidebar = st.session_state.get("role_label") or (
            "Administrador" if is_admin else "Usuario"
        )

        st.caption(f"@{username} · {rol_sidebar}")

        if shared_api:
            st.caption("Modo compartido web / móvil")
        else:
            st.caption("Modo local de respaldo")

        # ----------------------------------------------------
        # Mostrar tokens en sidebar
        # ----------------------------------------------------
        token_status_sidebar = refrescar_tokens_sesion()

        if token_status_sidebar:
            if token_status_sidebar.get("is_unlimited"):
                st.caption("Tokens: ilimitados")
            else:
                st.caption(
                    f"Tokens: {token_status_sidebar.get('remaining_tokens', 0)}/"
                    f"{token_status_sidebar.get('daily_limit', 0)}"
                )

        if st.button("Cerrar sesión", width="stretch"):
            logout_everything()
            st.rerun()

        st.divider()

        st.subheader("Accesibilidad")

        st.selectbox(
            "Tamaño de texto",
            options=["Normal", "Grande", "Muy grande"],
            key="ui_font_size"
        )

        st.toggle(
            "Mayor contraste",
            key="ui_high_contrast"
        )

        st.toggle(
            "Modo enfoque",
            key="ui_focus_mode",
            help="Reduce elementos secundarios para concentrarte en lo principal."
        )

        st.divider()

        # ----------------------------------------------------
        # Conversaciones solo para módulos de chat
        # ----------------------------------------------------
        st.subheader("Conversaciones")
        st.caption(MODULE_LABELS[modulo_actual])

        if es_modulo_chat(modulo_actual):
            if st.button("Nuevo chat", width="stretch"):
                crear_y_cargar_nueva_conversacion(modulo_actual, user_id)
                st.rerun()

            st.markdown(
                '<div class="sidebar-note">Historial del usuario actual en este módulo</div>',
                unsafe_allow_html=True
            )
            st.write("")

            if not conversaciones_modulo:
                st.info("Todavía no tienes conversaciones en este módulo.")
            else:
                for conversacion in conversaciones_modulo:
                    titulo = conversacion.get("title", "Conversación")
                    fecha = formatear_fecha(conversacion.get("updated_at", ""))
                    texto_boton = f"{titulo}\n{fecha}"

                    es_actual = conversacion.get("id") == st.session_state.conversation_id
                    etiqueta = f"● {texto_boton}" if es_actual else texto_boton

                    if st.button(
                        etiqueta,
                        key=f"conv_{conversacion.get('id')}",
                        width="stretch"
                    ):
                        cargar_conversacion(conversacion.get("id"), user_id)
                        st.rerun()
        else:
            st.info("Este módulo no usa conversaciones.")

    # --------------------------------------------------------
    # Encabezado principal
    # --------------------------------------------------------
    st.markdown(
        '<div class="main-title">Amigo Imaginario Neurodivergente</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="main-subtitle">Fase 17 · Roles, guests, tokens y aviso legal</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        f"""
        <div class="hero-card">
            <div class="hero-title">Hola, {display_name}</div>
            <div class="hero-text">
                Tu navegación se ajusta automáticamente al rol de tu cuenta y al estado de tus tokens.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # --------------------------------------------------------
    # Tokens visibles en dashboard
    # --------------------------------------------------------
    render_token_status_card()

    # --------------------------------------------------------
    # Estadísticas
    # --------------------------------------------------------
    col_stat_1, col_stat_2, col_stat_3 = st.columns(3)

    with col_stat_1:
        render_stat_card(
            "Módulo actual",
            MODULE_LABELS[modulo_actual],
            "Espacio activo en este momento"
        )

    with col_stat_2:
        if es_modulo_chat(modulo_actual):
            render_stat_card(
                "Chats en este módulo",
                str(len(conversaciones_modulo)),
                "Conversaciones guardadas para este usuario"
            )
        else:
            render_stat_card(
                "Panel activo",
                "Administración",
                "Herramientas exclusivas del superadmin"
            )

    with col_stat_3:
        if modulo_actual == "amigo_imaginario":
            render_stat_card(
                "Nombre del amigo",
                st.session_state.friend_name,
                "Nombre personalizado del acompañante"
            )
        else:
            total_articulos = len(list_all_articles(limit=5000))
            render_stat_card(
                "Artículos disponibles",
                str(total_articulos),
                "Contenido actual de la biblioteca"
            )

    # --------------------------------------------------------
    # Selector de módulo filtrado por rol
    # --------------------------------------------------------
    col_modulo, col_accion = st.columns([4, 1], gap="medium")

    with col_modulo:
        modulo_seleccionado = st.selectbox(
            "Selecciona un módulo",
            options=modulos_visibles,
            format_func=lambda clave: MODULE_LABELS[clave],
            index=modulos_visibles.index(modulo_actual)
            if modulo_actual in modulos_visibles
            else 0
        )

    with col_accion:
        st.write("")
        st.write("")

        if es_modulo_chat(modulo_actual):
            if st.button("Nuevo chat", width="stretch"):
                crear_y_cargar_nueva_conversacion(modulo_actual, user_id)
                st.rerun()
        else:
            st.button("Panel activo", disabled=True, width="stretch")

    if modulo_seleccionado != st.session_state.modulo_actual:
        st.session_state.modulo_actual = modulo_seleccionado
        st.session_state.ultimo_modulo = modulo_seleccionado
        st.session_state.conversation_id = None
        st.session_state.mensajes = []
        st.session_state.pending_message = None

        if modulo_seleccionado != "biblioteca_inteligente":
            st.session_state.selected_article_id = None

        if es_modulo_chat(modulo_seleccionado):
            asegurar_conversacion_activa(modulo_seleccionado, user_id)

        st.rerun()

    modulo_actual = st.session_state.modulo_actual
    info_modulo = MODULE_INFO[modulo_actual]

    st.markdown(
        f"""
        <div class="info-card">
            <div class="info-title">{MODULE_LABELS[modulo_actual]}</div>
            <div class="info-text">{info_modulo["descripcion"]}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

    if es_modulo_chat(modulo_actual) and st.session_state.conversation_id:
        st.caption(f"Chat actual: {st.session_state.conversation_id}")

    if not st.session_state.ui_focus_mode:
        chip_admin = "Sí" if is_admin else "No"
        chip_sync = "Compartido" if shared_api else "Local"

        chips_html = f"""
        <span class="chip">Cuenta: @{username}</span>
        <span class="chip">Módulo: {MODULE_LABELS[modulo_actual]}</span>
        <span class="chip">Texto: {st.session_state.ui_font_size}</span>
        <span class="chip">Admin: {chip_admin}</span>
        <span class="chip">Modo: {chip_sync}</span>
        """

        if modulo_actual == "amigo_imaginario":
            chips_html += f'<span class="chip">Amigo: {st.session_state.friend_name}</span>'

        st.markdown(chips_html, unsafe_allow_html=True)

    # --------------------------------------------------------
    # Flujo: Administración
    # --------------------------------------------------------
    if modulo_actual == "admin_panel":
        if not is_admin:
            st.error("No tienes permiso para acceder al panel de administración.")
        else:
            render_access_control_admin_panel()

    # --------------------------------------------------------
    # Flujo: Biblioteca Inteligente
    # --------------------------------------------------------
    elif modulo_actual == "biblioteca_inteligente":
        if is_admin:
            tab_chat, tab_biblioteca, tab_admin = st.tabs(
                ["Chat educativo", "Biblioteca", "Administración de biblioteca"]
            )
        else:
            tab_chat, tab_biblioteca = st.tabs(
                ["Chat educativo", "Biblioteca"]
            )
            tab_admin = None

        with tab_chat:
            st.markdown(
                """
                <div class="info-card">
                    <div class="info-title">Chat educativo con apoyo de biblioteca interna</div>
                    <div class="info-text">
                        Puedes usar artículos como base para conversar y pedir explicaciones más sencillas.
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

            mensaje_desde_ejemplo = None

            if not st.session_state.ui_focus_mode:
                st.caption("Prueba con uno de estos ejemplos rápidos:")

                col_1, col_2, col_3 = st.columns(3)
                ejemplos = info_modulo["ejemplos"]

                with col_1:
                    if st.button(
                        ejemplos[0],
                        key="ejemplo_biblio_1",
                        width="stretch"
                    ):
                        mensaje_desde_ejemplo = ejemplos[0]

                with col_2:
                    if st.button(
                        ejemplos[1],
                        key="ejemplo_biblio_2",
                        width="stretch"
                    ):
                        mensaje_desde_ejemplo = ejemplos[1]

                with col_3:
                    if st.button(
                        ejemplos[2],
                        key="ejemplo_biblio_3",
                        width="stretch"
                    ):
                        mensaje_desde_ejemplo = ejemplos[2]

            render_chat_history_with_feedback(
                user_id=user_id,
                modulo_actual=modulo_actual
            )

            mensaje_chat = st.chat_input(info_modulo["placeholder"])
            mensaje_usuario = None

            if st.session_state.pending_message:
                mensaje_usuario = st.session_state.pending_message
                st.session_state.pending_message = None
            elif mensaje_chat:
                mensaje_usuario = mensaje_chat
            elif mensaje_desde_ejemplo:
                mensaje_usuario = mensaje_desde_ejemplo

            if mensaje_usuario:
                procesar_mensaje_chat(
                    user_id=user_id,
                    modulo_actual=modulo_actual,
                    mensaje_usuario=mensaje_usuario
                )

        with tab_biblioteca:
            render_biblioteca_panel(user_id)

        if tab_admin is not None:
            with tab_admin:
                render_admin_panel()

    # --------------------------------------------------------
    # Flujo: Amigo Imaginario
    # --------------------------------------------------------
    elif modulo_actual == "amigo_imaginario":
        tab_chat, tab_mi_amigo, tab_recuerdos = st.tabs(
            ["Chat", "Mi amigo", "Recuerdos suaves"]
        )

        with tab_chat:
            col_chat, col_companion = st.columns([2.3, 1], gap="large")

            with col_chat:
                mensaje_desde_ejemplo = None
                mensaje_desde_iniciativa = None

                st.markdown(
                    f"""
                    <div class="info-card">
                        <div class="info-title">Ahora estás hablando con {st.session_state.friend_name}</div>
                        <div class="info-text">
                            Este amigo imaginario puede acompañar, escuchar, contar mini historias,
                            proponer juegos tranquilos, iniciar dinámicas suaves y seguir la conversación con más calidez.
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                mensaje_desde_iniciativa = render_friend_initiatives_panel()

                if not st.session_state.ui_focus_mode:
                    st.caption("Prueba con uno de estos ejemplos rápidos:")

                    col_1, col_2, col_3 = st.columns(3)
                    ejemplos = info_modulo["ejemplos"]

                    with col_1:
                        if st.button(
                            ejemplos[0],
                            key="ejemplo_1_amigo_imaginario",
                            width="stretch"
                        ):
                            update_friend_companion_state("feliz")
                            mensaje_desde_ejemplo = ejemplos[0]

                    with col_2:
                        if st.button(
                            ejemplos[1],
                            key="ejemplo_2_amigo_imaginario",
                            width="stretch"
                        ):
                            update_friend_companion_state("juego")
                            mensaje_desde_ejemplo = ejemplos[1]

                    with col_3:
                        if st.button(
                            ejemplos[2],
                            key="ejemplo_3_amigo_imaginario",
                            width="stretch"
                        ):
                            update_friend_companion_state("cuento")
                            mensaje_desde_ejemplo = ejemplos[2]

                render_chat_history_with_feedback(
                    user_id=user_id,
                    modulo_actual=modulo_actual
                )

                mensaje_chat = st.chat_input(info_modulo["placeholder"])
                mensaje_usuario = None

                if mensaje_desde_iniciativa:
                    mensaje_usuario = mensaje_desde_iniciativa
                elif mensaje_desde_ejemplo:
                    mensaje_usuario = mensaje_desde_ejemplo
                elif mensaje_chat:
                    update_friend_companion_state("feliz")
                    mensaje_usuario = mensaje_chat

                if mensaje_usuario:
                    procesar_mensaje_chat(
                        user_id=user_id,
                        modulo_actual=modulo_actual,
                        mensaje_usuario=mensaje_usuario
                    )

            with col_companion:
                render_friend_companion_panel()

        with tab_mi_amigo:
            render_friend_creation_panel(user_id)

        with tab_recuerdos:
            render_friend_memory_panel(user_id)

            st.markdown(
                f"""
                <div class="info-card">
                    <div class="info-title">Lo que {st.session_state.friend_name} recuerda de ti</div>
                    <div class="info-text">
                        Color favorito: {st.session_state.friend_profile.get("favorite_color") or "Todavía no guardado"}<br>
                        Actividad favorita: {st.session_state.friend_profile.get("favorite_activity") or "Todavía no guardada"}<br>
                        Cómo te gusta que te animen: {st.session_state.friend_profile.get("encouragement_style") or "Todavía no guardado"}<br>
                        Cuando necesitas apoyo prefieres: {st.session_state.friend_profile.get("preferred_comfort") or "cuentos"}
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

    # --------------------------------------------------------
    # Flujo: Modo Padres
    # --------------------------------------------------------
    elif modulo_actual == "modo_padres":
        mensaje_desde_ejemplo = None

        if not st.session_state.ui_focus_mode:
            st.caption("Prueba con uno de estos ejemplos rápidos:")

            col_1, col_2, col_3 = st.columns(3)
            ejemplos = info_modulo["ejemplos"]

            with col_1:
                if st.button(
                    ejemplos[0],
                    key=f"ejemplo_1_{modulo_actual}",
                    width="stretch"
                ):
                    mensaje_desde_ejemplo = ejemplos[0]

            with col_2:
                if st.button(
                    ejemplos[1],
                    key=f"ejemplo_2_{modulo_actual}",
                    width="stretch"
                ):
                    mensaje_desde_ejemplo = ejemplos[1]

            with col_3:
                if st.button(
                    ejemplos[2],
                    key=f"ejemplo_3_{modulo_actual}",
                    width="stretch"
                ):
                    mensaje_desde_ejemplo = ejemplos[2]

        render_chat_history_with_feedback(
            user_id=user_id,
            modulo_actual=modulo_actual
        )

        mensaje_chat = st.chat_input(info_modulo["placeholder"])
        mensaje_usuario = None

        if mensaje_chat:
            mensaje_usuario = mensaje_chat
        elif mensaje_desde_ejemplo:
            mensaje_usuario = mensaje_desde_ejemplo

        if mensaje_usuario:
            procesar_mensaje_chat(
                user_id=user_id,
                modulo_actual=modulo_actual,
                mensaje_usuario=mensaje_usuario
            )

    else:
        st.error("Módulo no reconocido o no permitido para tu cuenta.")

    st.divider()
    render_aviso_legal()

# ============================================================
# Arranque principal de la aplicación
# Este bloque debe estar SIEMPRE al final de app.py.
# Si no existe, Streamlit carga una pantalla en negro porque
# solo define funciones, pero nunca renderiza la interfaz.
# ============================================================

try:
    # --------------------------------------------------------
    # Inicializar estado visual y variables de sesión
    # --------------------------------------------------------
    inicializar_estado()

    # --------------------------------------------------------
    # Aplicar estilos visuales de la app
    # --------------------------------------------------------
    aplicar_estilos()

    # --------------------------------------------------------
    # Inicializar base de datos local y migraciones
    # --------------------------------------------------------
    initialize_database()

    # --------------------------------------------------------
    # Validar configuración general del proyecto
    # --------------------------------------------------------
    errores_config = validar_configuracion()

    if errores_config:
        st.error("Hay un problema de configuración antes de iniciar la app.")

        for error in errores_config:
            st.write(f"- {error}")

        st.info("Revisa tu archivo .env y vuelve a ejecutar la aplicación.")
        st.stop()

    # --------------------------------------------------------
    # Restaurar sesión JWT compartida si existe
    # --------------------------------------------------------
    restore_api_session()

    # --------------------------------------------------------
    # Sincronizar login de Google si se usa ese método
    # --------------------------------------------------------
    sync_google_login_to_local_user()

    # --------------------------------------------------------
    # Normalizar módulo actual para evitar pantalla negra
    # cuando quedó guardado un módulo viejo en session_state.
    # --------------------------------------------------------
    if "modulo_actual" not in st.session_state:
        st.session_state.modulo_actual = "amigo_imaginario"

    if "ultimo_modulo" not in st.session_state:
        st.session_state.ultimo_modulo = st.session_state.modulo_actual

    # --------------------------------------------------------
    # Router principal
    # --------------------------------------------------------
    if st.session_state.get("user_id") is None:
        render_auth_screen()
    else:
        render_app()

# ------------------------------------------------------------
# Mostrar errores directamente en pantalla
# Esto evita que Streamlit se quede en negro sin explicar qué pasó.
# ------------------------------------------------------------
except Exception as error:
    st.error("La app encontró un problema al cargar.")
    st.exception(error)

    st.info(
        "Puedes limpiar la sesión abriendo esta URL: "
        "http://localhost:8501/?reset=1"
    )
