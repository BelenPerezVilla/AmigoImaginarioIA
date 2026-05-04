# ============================================================
# services/web_auth.py
# Funciones de autenticación para la app web usando FastAPI.
# ============================================================

from services.api_client import api_get, api_post


# ------------------------------------------------------------
# Iniciar sesión contra el backend compartido
# ------------------------------------------------------------
def login_web_user(username: str, password: str) -> dict:
    """
    Hace login contra el backend FastAPI compartido.

    Parámetros:
        username (str): nombre de usuario
        password (str): contraseña

    Retorna:
        dict: respuesta con access_token, token_type y user
    """
    return api_post(
        "/api/auth/login",
        {
            "username": username.strip(),
            "password": password,
        }
    )


# ------------------------------------------------------------
# Registrar usuario contra el backend compartido
# ------------------------------------------------------------
def register_web_user(display_name: str, username: str, password: str) -> dict:
    """
    Registra un usuario nuevo contra el backend FastAPI.

    Parámetros:
        display_name (str): nombre visible
        username (str): nombre de usuario
        password (str): contraseña

    Retorna:
        dict: respuesta con access_token, token_type y user
    """
    return api_post(
        "/api/auth/register",
        {
            "display_name": display_name.strip(),
            "username": username.strip(),
            "password": password,
        }
    )


# ------------------------------------------------------------
# Obtener usuario autenticado actual
# ------------------------------------------------------------
def get_current_web_user(token: str) -> dict:
    """
    Recupera el usuario autenticado actual usando el token JWT.

    Parámetros:
        token (str): token JWT

    Retorna:
        dict: datos del usuario autenticado
    """
    return api_get(
        "/api/auth/me",
        token=token
    )