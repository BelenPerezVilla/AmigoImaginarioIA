# ============================================================
# services/api_client.py
# Cliente HTTP compartido para que la app web consuma
# el backend FastAPI.
#
# Incluye:
# - funciones HTTP genéricas
# - autenticación
# - tokens
# - panel superadmin
# - cuentas guest
# - administración de roles
# ============================================================

import os
from typing import Any

import requests


# ------------------------------------------------------------
# URL base del backend FastAPI.
# En desarrollo local normalmente será:
# http://127.0.0.1:8000
# ------------------------------------------------------------
API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000").rstrip("/")


# ------------------------------------------------------------
# Timeout general para peticiones HTTP.
# Se aumenta a 60 segundos porque Gemini puede tardar.
# ------------------------------------------------------------
API_TIMEOUT_SECONDS = int(os.getenv("API_TIMEOUT_SECONDS", "60"))


# ------------------------------------------------------------
# Construir headers comunes para las peticiones HTTP
# ------------------------------------------------------------
def build_headers(token: str | None = None, json_content: bool = True) -> dict[str, str]:
    """
    Construye los headers base para consumir FastAPI.

    Parámetros:
        token (str | None): token JWT opcional.
        json_content (bool): indica si se enviará contenido JSON.

    Retorna:
        dict[str, str]: headers listos para requests.
    """
    headers: dict[str, str] = {}

    if json_content:
        headers["Content-Type"] = "application/json"

    if token:
        headers["Authorization"] = f"Bearer {token}"

    return headers


# ------------------------------------------------------------
# Procesar respuesta y lanzar error entendible si falla
# ------------------------------------------------------------
def handle_response(response: requests.Response) -> Any:
    """
    Procesa la respuesta del backend.

    Parámetros:
        response (requests.Response): respuesta HTTP.

    Retorna:
        Any: contenido JSON del backend.

    Lanza:
        Exception: si la respuesta no fue exitosa.
    """
    try:
        data = response.json()
    except Exception:
        data = None

    if not response.ok:
        detail = None

        if isinstance(data, dict):
            detail = data.get("detail") or data.get("message")

        if not detail:
            detail = f"Error del servidor ({response.status_code})."

        raise Exception(detail)

    return data


# ------------------------------------------------------------
# Realizar petición GET
# ------------------------------------------------------------
def api_get(
    path: str,
    token: str | None = None,
    params: dict | None = None,
) -> Any:
    """
    Ejecuta una petición GET al backend.

    Parámetros:
        path (str): ruta relativa del endpoint.
        token (str | None): token JWT opcional.
        params (dict | None): parámetros query string.

    Retorna:
        Any: respuesta JSON del backend.
    """
    response = requests.get(
        f"{API_BASE_URL}{path}",
        headers=build_headers(token=token, json_content=False),
        params=params,
        timeout=API_TIMEOUT_SECONDS,
    )

    return handle_response(response)


# ------------------------------------------------------------
# Realizar petición POST
# ------------------------------------------------------------
def api_post(
    path: str,
    payload: dict | None = None,
    token: str | None = None,
) -> Any:
    """
    Ejecuta una petición POST al backend.

    Parámetros:
        path (str): ruta relativa del endpoint.
        payload (dict | None): cuerpo JSON a enviar.
        token (str | None): token JWT opcional.

    Retorna:
        Any: respuesta JSON del backend.
    """
    response = requests.post(
        f"{API_BASE_URL}{path}",
        headers=build_headers(token=token, json_content=True),
        json=payload or {},
        timeout=API_TIMEOUT_SECONDS,
    )

    return handle_response(response)


# ------------------------------------------------------------
# Realizar petición PATCH
# ------------------------------------------------------------
def api_patch(
    path: str,
    payload: dict | None = None,
    token: str | None = None,
) -> Any:
    """
    Ejecuta una petición PATCH al backend.

    Parámetros:
        path (str): ruta relativa del endpoint.
        payload (dict | None): cuerpo JSON a enviar.
        token (str | None): token JWT opcional.

    Retorna:
        Any: respuesta JSON del backend.
    """
    response = requests.patch(
        f"{API_BASE_URL}{path}",
        headers=build_headers(token=token, json_content=True),
        json=payload or {},
        timeout=API_TIMEOUT_SECONDS,
    )

    return handle_response(response)


# ------------------------------------------------------------
# Realizar petición DELETE
# ------------------------------------------------------------
def api_delete(
    path: str,
    token: str | None = None,
) -> Any:
    """
    Ejecuta una petición DELETE al backend.

    Parámetros:
        path (str): ruta relativa del endpoint.
        token (str | None): token JWT opcional.

    Retorna:
        Any: respuesta JSON del backend.
    """
    response = requests.delete(
        f"{API_BASE_URL}{path}",
        headers=build_headers(token=token, json_content=False),
        timeout=API_TIMEOUT_SECONDS,
    )

    return handle_response(response)


# ============================================================
# Autenticación
# ============================================================

# ------------------------------------------------------------
# Iniciar sesión desde Streamlit usando FastAPI
# ------------------------------------------------------------
def login_user(username: str, password: str) -> dict:
    """
    Inicia sesión contra el backend FastAPI.

    Parámetros:
        username (str): usuario.
        password (str): contraseña.

    Retorna:
        dict: access_token y datos del usuario.
    """
    return api_post(
        "/api/auth/login",
        {
            "username": username,
            "password": password,
        },
    )


# ------------------------------------------------------------
# Registrar usuario desde Streamlit usando FastAPI
# ------------------------------------------------------------
def register_user(username: str, password: str, display_name: str = "") -> dict:
    """
    Registra un usuario contra el backend FastAPI.

    Parámetros:
        username (str): nombre de usuario.
        password (str): contraseña.
        display_name (str): nombre visible.

    Retorna:
        dict: access_token y datos del usuario.
    """
    return api_post(
        "/api/auth/register",
        {
            "username": username,
            "password": password,
            "display_name": display_name,
        },
    )


# ------------------------------------------------------------
# Obtener usuario autenticado
# ------------------------------------------------------------
def get_me(token: str) -> dict:
    """
    Consulta los datos actualizados del usuario autenticado.

    Parámetros:
        token (str): token JWT.

    Retorna:
        dict: usuario autenticado.
    """
    return api_get(
        "/api/auth/me",
        token=token,
    )


# ------------------------------------------------------------
# Obtener aviso legal desde backend
# ------------------------------------------------------------
def get_legal_notice() -> dict:
    """
    Obtiene el aviso legal vigente desde FastAPI.

    Retorna:
        dict: texto y versión del aviso legal.
    """
    return api_get("/api/auth/legal-notice")


# ============================================================
# Tokens / créditos de uso
# ============================================================

# ------------------------------------------------------------
# Consultar tokens del usuario autenticado
# ------------------------------------------------------------
def get_my_tokens(token: str) -> dict:
    """
    Consulta el estado de tokens del usuario actual.

    Parámetros:
        token (str): token JWT.

    Retorna:
        dict: tokens restantes, usados, reinicio y advertencias.
    """
    return api_get(
        "/api/tokens/me",
        token=token,
    )


# ============================================================
# Panel superadmin: usuarios
# ============================================================

# ------------------------------------------------------------
# Listar usuarios
# ------------------------------------------------------------
def admin_list_users(token: str) -> list[dict]:
    """
    Lista usuarios registrados.

    Solo debe usarse con cuenta superadmin.

    Parámetros:
        token (str): token JWT del superadmin.

    Retorna:
        list[dict]: usuarios del sistema.
    """
    return api_get(
        "/api/admin/users",
        token=token,
    )


# ------------------------------------------------------------
# Actualizar rol de usuario
# ------------------------------------------------------------
def admin_update_role(token: str, user_id: int, role: str) -> dict:
    """
    Actualiza el rol de un usuario.

    Parámetros:
        token (str): token JWT del superadmin.
        user_id (int): ID del usuario.
        role (str): nuevo rol.

    Retorna:
        dict: usuario actualizado.
    """
    return api_patch(
        f"/api/admin/users/{user_id}/role",
        {
            "role": role,
        },
        token=token,
    )


# ------------------------------------------------------------
# Actualizar política de tokens de usuario
# ------------------------------------------------------------
def admin_update_tokens(
    token: str,
    user_id: int,
    payload: dict,
) -> dict:
    """
    Actualiza los tokens de un usuario.

    Parámetros:
        token (str): token JWT del superadmin.
        user_id (int): ID del usuario.
        payload (dict): configuración de tokens.

    Payload esperado:
        {
            "daily_limit": 20,
            "reset_interval_hours": 24,
            "low_threshold": 5
        }

    Retorna:
        dict: estado actualizado de tokens.
    """
    return api_patch(
        f"/api/admin/users/{user_id}/tokens",
        payload,
        token=token,
    )


# ============================================================
# Panel superadmin: cuentas guest
# ============================================================

# ------------------------------------------------------------
# Crear cuenta guest temporal
# ------------------------------------------------------------
def admin_create_guest(token: str, payload: dict) -> dict:
    """
    Crea una cuenta guest temporal.

    Parámetros:
        token (str): token JWT del superadmin.
        payload (dict): datos de la cuenta guest.

    Payload esperado:
        {
            "username": "guestnino1",
            "password": "Guest12345",
            "display_name": "Niño Invitado",
            "guest_type": "guest_child",
            "hours": 4,
            "token_limit": 10
        }

    Retorna:
        dict: usuario guest creado.
    """
    return api_post(
        "/api/admin/guests",
        payload,
        token=token,
    )


# ------------------------------------------------------------
# Listar cuentas guest
# ------------------------------------------------------------
def admin_list_guests(token: str) -> list[dict]:
    """
    Lista todas las cuentas guest.

    Parámetros:
        token (str): token JWT del superadmin.

    Retorna:
        list[dict]: cuentas guest.
    """
    return api_get(
        "/api/admin/guests",
        token=token,
    )


# ------------------------------------------------------------
# Extender tiempo de cuenta guest
# ------------------------------------------------------------
def admin_extend_guest(token: str, user_id: int, extra_hours: int) -> dict:
    """
    Extiende el acceso de una cuenta guest.

    Parámetros:
        token (str): token JWT del superadmin.
        user_id (int): ID del usuario guest.
        extra_hours (int): horas extra.

    Retorna:
        dict: cuenta guest actualizada.
    """
    return api_patch(
        f"/api/admin/guests/{user_id}/extend",
        {
            "extra_hours": extra_hours,
        },
        token=token,
    )


# ------------------------------------------------------------
# Desactivar cuenta guest
# ------------------------------------------------------------
def admin_deactivate_guest(token: str, user_id: int) -> dict:
    """
    Desactiva una cuenta guest.

    Parámetros:
        token (str): token JWT del superadmin.
        user_id (int): ID del usuario guest.

    Retorna:
        dict: cuenta guest actualizada.
    """
    return api_patch(
        f"/api/admin/guests/{user_id}/deactivate",
        {},
        token=token,
    )


# ============================================================
# Panel superadmin: personalización del amigo imaginario
# ============================================================

# ------------------------------------------------------------
# Actualizar preferencias del amigo imaginario de un usuario
# ------------------------------------------------------------
def admin_update_friend_preferences(
    token: str,
    user_id: int,
    payload: dict,
) -> dict:
    """
    Actualiza las preferencias del amigo imaginario de un usuario.

    Solo debe usarlo superadmin.

    Parámetros:
        token (str): token JWT del superadmin.
        user_id (int): ID del usuario niño.
        payload (dict): preferencias.

    Payload esperado:
        {
            "friend_name": "Lumi",
            "favorite_color": "azul",
            "favorite_activity": "dibujar",
            "encouragement_style": "tranquilo",
            "preferred_comfort": "cuentos"
        }

    Retorna:
        dict: usuario actualizado.
    """
    return api_patch(
        f"/api/admin/users/{user_id}/friend/preferences",
        payload,
        token=token,
    )


# ------------------------------------------------------------
# Actualizar avatar del amigo imaginario de un usuario
# ------------------------------------------------------------
def admin_update_friend_avatar(
    token: str,
    user_id: int,
    payload: dict,
) -> dict:
    """
    Actualiza el avatar del amigo imaginario de un usuario.

    Solo debe usarlo superadmin.

    Parámetros:
        token (str): token JWT del superadmin.
        user_id (int): ID del usuario niño.
        payload (dict): configuración visual del avatar.

    Retorna:
        dict: avatar actualizado.
    """
    return api_patch(
        f"/api/admin/users/{user_id}/friend/avatar",
        payload,
        token=token,
    )


# ============================================================
# Compatibilidad con servicios existentes
# ============================================================

# ------------------------------------------------------------
# Ping básico del backend
# ------------------------------------------------------------
def api_health() -> dict:
    """
    Verifica si el backend FastAPI está activo.

    Retorna:
        dict: estado del backend.
    """
    return api_get("/health")