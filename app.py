# ============================================================
# app.py
# Fase 10:
# - autenticación con SQLite
# - historial por usuario
# - biblioteca estructurada
# - panel admin
# - importación / exportación de artículos
# - generación de artículos desde documentos
# - RAG simple para Biblioteca Inteligente
# - feedback útil / no útil
# - métricas básicas de utilidad
# - sin use_container_width
# ============================================================

from datetime import datetime
import csv
import io
import json

import streamlit as st

# ------------------------------------------------------------
# Configuración general del proyecto
# ------------------------------------------------------------
from config import validar_configuracion

# ------------------------------------------------------------
# Funciones de base de datos
# ------------------------------------------------------------
from database.chat_db import (
    add_message,
    authenticate_user,
    create_article,
    create_conversation,
    create_user,
    delete_article,
    get_article_by_id,
    get_conversation_by_id,
    get_feedback_for_message,
    get_feedback_summary,
    get_latest_conversation_by_module,
    get_messages_by_conversation,
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
    update_title_if_default,
)

# ------------------------------------------------------------
# Configuración visual y prompts
# ------------------------------------------------------------
from prompts import MODULE_INFO, MODULE_LABELS

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
# Configuración general de la página
# ------------------------------------------------------------
st.set_page_config(
    page_title="Amigo Imaginario Neurodivergente",
    page_icon="💙",
    layout="wide"
)


# ------------------------------------------------------------
# Inicializar estado de sesión
# ------------------------------------------------------------
def inicializar_estado() -> None:
    """
    Inicializa variables necesarias en session_state para:
    - autenticación
    - conversación
    - preferencias visuales
    - biblioteca
    - administración
    """
    if "user_id" not in st.session_state:
        st.session_state.user_id = None

    if "username" not in st.session_state:
        st.session_state.username = None

    if "display_name" not in st.session_state:
        st.session_state.display_name = None

    if "is_admin" not in st.session_state:
        st.session_state.is_admin = False

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

            .auth-card {{
                background-color: {bg_card};
                border: 1px solid {border_card};
                border-radius: 18px;
                padding: 18px;
                margin-bottom: 14px;
            }}

            .section-label {{
                font-size: 0.95rem;
                font-weight: 700;
                margin-bottom: 0.35rem;
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
        </style>
        """,
        unsafe_allow_html=True
    )


# ------------------------------------------------------------
# Formatear fecha
# ------------------------------------------------------------
def formatear_fecha(texto_fecha: str) -> str:
    """
    Convierte una fecha SQLite a formato corto legible.
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
# Iniciar sesión
# ------------------------------------------------------------
def iniciar_sesion(usuario: dict) -> None:
    """
    Guarda al usuario autenticado en session_state.
    """
    st.session_state.user_id = usuario["id"]
    st.session_state.username = usuario["username"]
    st.session_state.display_name = usuario["display_name"]
    st.session_state.is_admin = bool(usuario.get("is_admin", False))
    st.session_state.modulo_actual = "amigo_imaginario"
    st.session_state.ultimo_modulo = "amigo_imaginario"
    st.session_state.conversation_id = None
    st.session_state.mensajes = []
    st.session_state.pending_message = None


# ------------------------------------------------------------
# Cerrar sesión
# ------------------------------------------------------------
def cerrar_sesion() -> None:
    """
    Limpia el estado de autenticación y conversación.
    """
    st.session_state.user_id = None
    st.session_state.username = None
    st.session_state.display_name = None
    st.session_state.is_admin = False
    st.session_state.modulo_actual = "amigo_imaginario"
    st.session_state.ultimo_modulo = "amigo_imaginario"
    st.session_state.conversation_id = None
    st.session_state.mensajes = []
    st.session_state.pending_message = None
    st.session_state.selected_article_id = None
    st.session_state.admin_edit_article_id = None


# ------------------------------------------------------------
# Cargar conversación
# ------------------------------------------------------------
def cargar_conversacion(conversation_id: int, user_id: int) -> None:
    """
    Carga una conversación del usuario a session_state.
    También conserva el id de cada mensaje para permitir feedback.
    """
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
    Crea una conversación nueva y guarda la bienvenida del módulo.
    """
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
    Garantiza que exista una conversación activa para el usuario.
    """
    conversation_id = st.session_state.get("conversation_id")

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
# Renderizar tarjeta estadística
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
# Parsear archivo subido para importación
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
# Renderizar historial con feedback
# ------------------------------------------------------------
def render_chat_history_with_feedback(user_id: int, modulo_actual: str) -> None:
    """
    Muestra el historial del chat y agrega st.feedback a las
    respuestas del asistente que pueden calificarse.
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
# Panel de métricas de feedback
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
# Pantalla de autenticación
# ------------------------------------------------------------
def render_auth_screen() -> None:
    """
    Muestra login y registro.
    """
    st.markdown('<div class="auth-shell">', unsafe_allow_html=True)

    st.markdown('<div class="main-title">Amigo Imaginario Neurodivergente</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="main-subtitle">Fase 10 · Feedback y métricas básicas</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        """
        <div class="hero-card">
            <div class="hero-title">Una plataforma más completa para conversar, aprender y mejorar</div>
            <div class="hero-text">
                Inicia sesión o crea una cuenta para conservar tu historial personal y, si eres administrador,
                revisar métricas básicas de utilidad de las respuestas.
            </div>
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
                    • Buscar artículos por tema o tipo de lector<br>
                    • Dar feedback sobre respuestas<br>
                    • Revisar métricas si tu cuenta es administradora
                </div>
            </div>
            """,
            unsafe_allow_html=True
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
                    usuario = authenticate_user(username, password)

                    if not usuario:
                        st.error("Usuario o contraseña incorrectos.")
                    else:
                        iniciar_sesion(usuario)
                        st.rerun()

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
                    if password != confirm_password:
                        st.error("Las contraseñas no coinciden.")
                    else:
                        try:
                            usuario = create_user(
                                username=username,
                                password=password,
                                display_name=display_name
                            )
                            iniciar_sesion(usuario)
                            st.rerun()
                        except ValueError as error:
                            st.error(str(error))

    st.markdown('</div>', unsafe_allow_html=True)


# ------------------------------------------------------------
# Panel de biblioteca estructurada
# ------------------------------------------------------------
def render_biblioteca_panel() -> None:
    """
    Renderiza el panel de búsqueda y lectura de artículos.
    """
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

    # --------------------------------------------------------
    # Administración de artículos
    # --------------------------------------------------------
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
                    index=[
                        "Usuario",
                        "Padre/Cuidador",
                        "Docente"
                    ].index(articulo_actual["reader_type"]) if articulo_actual and articulo_actual["reader_type"] in ["Usuario", "Padre/Cuidador", "Docente"] else 0
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

    # --------------------------------------------------------
    # Importación y exportación
    # --------------------------------------------------------
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

    # --------------------------------------------------------
    # Generación desde documentos
    # --------------------------------------------------------
    with tab_documentos:
        render_document_ingestion_panel()

    # --------------------------------------------------------
    # Métricas de utilidad
    # --------------------------------------------------------
    with tab_metricas:
        render_feedback_metrics_panel()

    # --------------------------------------------------------
    # Administración de usuarios
    # --------------------------------------------------------
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

                    st.rerun()


# ------------------------------------------------------------
# Procesar mensaje del chat
# ------------------------------------------------------------
def procesar_mensaje_chat(user_id: int, modulo_actual: str, mensaje_usuario: str) -> None:
    """
    Procesa un mensaje del usuario, lo guarda y genera respuesta.
    """
    if not st.session_state.conversation_id:
        crear_y_cargar_nueva_conversacion(modulo_actual, user_id)

    conversation_id = st.session_state.conversation_id

    # Guardar mensaje del usuario en base y conservar su id
    user_message_id = add_message(
        conversation_id=conversation_id,
        role="user",
        content=mensaje_usuario
    )

    # Guardar mensaje del usuario en sesión
    st.session_state.mensajes.append({
        "id": user_message_id,
        "role": "user",
        "content": mensaje_usuario
    })

    # Actualizar título automático si aplica
    update_title_if_default(
        conversation_id=conversation_id,
        user_id=user_id,
        user_message=mensaje_usuario
    )

    # Mostrar mensaje del usuario
    with st.chat_message("user"):
        st.markdown(mensaje_usuario)

    # Generar respuesta
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
                        mensajes=st.session_state.mensajes
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

    # Guardar respuesta del asistente y conservar su id
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

    # Recargar conversación para refrescar historial
    cargar_conversacion(conversation_id, user_id)
    st.rerun()


# ------------------------------------------------------------
# Vista principal autenticada
# ------------------------------------------------------------
def render_app() -> None:
    """
    Renderiza la aplicación principal una vez autenticado.
    """
    user_id = st.session_state.user_id
    display_name = st.session_state.display_name
    username = st.session_state.username
    is_admin = st.session_state.is_admin

    asegurar_conversacion_activa(st.session_state.modulo_actual, user_id)

    modulo_actual = st.session_state.modulo_actual
    info_modulo = MODULE_INFO[modulo_actual]

    conversaciones_modulo = list_conversations_by_module(
        user_id=user_id,
        module=modulo_actual,
        limit=30
    )

    # --------------------------------------------------------
    # Sidebar
    # --------------------------------------------------------
    with st.sidebar:
        st.subheader("Tu sesión")
        st.write(f"**{display_name}**")
        rol_sidebar = "Administrador" if is_admin else "Usuario"
        st.caption(f"@{username} · {rol_sidebar}")

        if st.button("Cerrar sesión", width="stretch"):
            cerrar_sesion()
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

        st.subheader("Conversaciones")
        st.caption(MODULE_LABELS[modulo_actual])

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
                titulo = conversacion["title"]
                fecha = formatear_fecha(conversacion["updated_at"])
                texto_boton = f"{titulo}\n{fecha}"

                es_actual = conversacion["id"] == st.session_state.conversation_id
                etiqueta = f"● {texto_boton}" if es_actual else texto_boton

                if st.button(
                    etiqueta,
                    key=f"conv_{conversacion['id']}",
                    width="stretch"
                ):
                    cargar_conversacion(conversacion["id"], user_id)
                    st.rerun()

    # --------------------------------------------------------
    # Encabezado principal
    # --------------------------------------------------------
    st.markdown('<div class="main-title">Amigo Imaginario Neurodivergente</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="main-subtitle">Fase 10 · Feedback y métricas básicas</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        f"""
        <div class="hero-card">
            <div class="hero-title">Hola, {display_name}</div>
            <div class="hero-text">
                Puedes seguir conversando y, si tu cuenta es administradora, también revisar métricas
                de utilidad para mejorar el sistema.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    col_stat_1, col_stat_2, col_stat_3 = st.columns(3)

    with col_stat_1:
        render_stat_card(
            "Módulo actual",
            MODULE_LABELS[modulo_actual],
            "Espacio activo en este momento"
        )

    with col_stat_2:
        render_stat_card(
            "Chats en este módulo",
            str(len(conversaciones_modulo)),
            "Conversaciones guardadas para este usuario"
        )

    with col_stat_3:
        total_articulos = len(list_all_articles(limit=5000))
        render_stat_card(
            "Artículos disponibles",
            str(total_articulos),
            "Contenido actual de la biblioteca"
        )

    # --------------------------------------------------------
    # Selector de módulo
    # --------------------------------------------------------
    col_modulo, col_accion = st.columns([4, 1], gap="medium")

    with col_modulo:
        modulo_seleccionado = st.selectbox(
            "Selecciona un módulo",
            options=list(MODULE_LABELS.keys()),
            format_func=lambda clave: MODULE_LABELS[clave],
            index=list(MODULE_LABELS.keys()).index(modulo_actual)
        )

    with col_accion:
        st.write("")
        st.write("")
        if st.button("Nuevo chat", width="stretch"):
            crear_y_cargar_nueva_conversacion(modulo_actual, user_id)
            st.rerun()

    if modulo_seleccionado != st.session_state.ultimo_modulo:
        st.session_state.modulo_actual = modulo_seleccionado
        st.session_state.ultimo_modulo = modulo_seleccionado
        st.session_state.conversation_id = None
        st.session_state.mensajes = []
        st.session_state.pending_message = None

        if modulo_seleccionado != "biblioteca_inteligente":
            st.session_state.selected_article_id = None

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

    conversacion_actual = get_conversation_by_id(st.session_state.conversation_id, user_id)
    if conversacion_actual:
        st.caption(f"Chat actual: {conversacion_actual['title']}")

    if not st.session_state.ui_focus_mode:
        chip_admin = "Sí" if is_admin else "No"
        st.markdown(
            f"""
            <span class="chip">Cuenta: @{username}</span>
            <span class="chip">Módulo: {MODULE_LABELS[modulo_actual]}</span>
            <span class="chip">Texto: {st.session_state.ui_font_size}</span>
            <span class="chip">Admin: {chip_admin}</span>
            """,
            unsafe_allow_html=True
        )

    # --------------------------------------------------------
    # Biblioteca inteligente con panel admin opcional
    # --------------------------------------------------------
    if modulo_actual == "biblioteca_inteligente":
        if is_admin:
            tab_chat, tab_biblioteca, tab_admin = st.tabs(
                ["Chat educativo", "Biblioteca", "Administración"]
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
                        Este chat intenta recuperar primero artículos y fragmentos relevantes de tu biblioteca
                        antes de generar la respuesta.
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
                    if st.button(ejemplos[0], key="ejemplo_biblio_1", width="stretch"):
                        mensaje_desde_ejemplo = ejemplos[0]

                with col_2:
                    if st.button(ejemplos[1], key="ejemplo_biblio_2", width="stretch"):
                        mensaje_desde_ejemplo = ejemplos[1]

                with col_3:
                    if st.button(ejemplos[2], key="ejemplo_biblio_3", width="stretch"):
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
            render_biblioteca_panel()

        if tab_admin is not None:
            with tab_admin:
                render_admin_panel()

    # --------------------------------------------------------
    # Resto de módulos
    # --------------------------------------------------------
    else:
        mensaje_desde_ejemplo = None

        if not st.session_state.ui_focus_mode:
            st.caption("Prueba con uno de estos ejemplos rápidos:")

            col_1, col_2, col_3 = st.columns(3)
            ejemplos = info_modulo["ejemplos"]

            with col_1:
                if st.button(ejemplos[0], key=f"ejemplo_1_{modulo_actual}", width="stretch"):
                    mensaje_desde_ejemplo = ejemplos[0]

            with col_2:
                if st.button(ejemplos[1], key=f"ejemplo_2_{modulo_actual}", width="stretch"):
                    mensaje_desde_ejemplo = ejemplos[1]

            with col_3:
                if st.button(ejemplos[2], key=f"ejemplo_3_{modulo_actual}", width="stretch"):
                    mensaje_desde_ejemplo = ejemplos[2]

        render_chat_history_with_feedback(
            user_id=user_id,
            modulo_actual=modulo_actual
        )

        mensaje_chat = st.chat_input(info_modulo["placeholder"])
        mensaje_usuario = mensaje_chat if mensaje_chat else mensaje_desde_ejemplo

        if mensaje_usuario:
            procesar_mensaje_chat(
                user_id=user_id,
                modulo_actual=modulo_actual,
                mensaje_usuario=mensaje_usuario
            )

    # --------------------------------------------------------
    # Aviso ético
    # --------------------------------------------------------
    st.divider()
    st.markdown(
        """
        <div class="ethics-box">
            Este sistema es un apoyo complementario y no sustituye atención,
            diagnóstico ni seguimiento profesional.
        </div>
        """,
        unsafe_allow_html=True
    )


# ------------------------------------------------------------
# Inicialización general
# ------------------------------------------------------------
inicializar_estado()
aplicar_estilos()
initialize_database()

errores_config = validar_configuracion()

if errores_config:
    st.error("Hay un problema de configuración antes de iniciar la app.")

    for error in errores_config:
        st.write(f"- {error}")

    st.info("Revisa tu archivo .env y vuelve a ejecutar la aplicación.")
    st.stop()


# ------------------------------------------------------------
# Router principal
# ------------------------------------------------------------
if st.session_state.user_id is None:
    render_auth_screen()
else:
    render_app()