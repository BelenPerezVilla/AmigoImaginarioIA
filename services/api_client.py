# ============================================================
# services/api_client.py
# Cliente HTTP compartido para que la app web consuma
# el backend FastAPI.
# ============================================================

import os
import requests


# ------------------------------------------------------------
# URL base del backend FastAPI
# En desarrollo local normalmente será http://127.0.0.1:8000
# ------------------------------------------------------------
API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000").rstrip("/")


# ------------------------------------------------------------
# Construir headers comunes para las peticiones HTTP
# ------------------------------------------------------------
def build_headers(token: str | None = None, json_content: bool = True) -> dict:
    """
    Construye los headers base para las peticiones.

    Parámetros:
        token (str | None): token JWT opcional
        json_content (bool): indica si se enviará JSON

    Retorna:
        dict: headers listos para requests
    """
    headers: dict[str, str] = {}

    if json_content:
        headers["Content-Type"] = "application/json"

    if token:
        headers["Authorization"] = f"Bearer {token}"

    return headers


# ------------------------------------------------------------
# Procesar respuesta y lanzar un error entendible si falla
# ------------------------------------------------------------
def handle_response(response: requests.Response):
    """
    Procesa la respuesta del backend.

    Parámetros:
        response (requests.Response): respuesta HTTP

    Retorna:
        dict | list: contenido JSON parseado

    Lanza:
        Exception: si la respuesta no fue exitosa
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
def api_get(path: str, token: str | None = None, params: dict | None = None):
    """
    Ejecuta una petición GET al backend.

    Parámetros:
        path (str): ruta relativa del endpoint
        token (str | None): token JWT opcional
        params (dict | None): parámetros query string

    Retorna:
        dict | list: respuesta JSON del backend
    """
    response = requests.get(
        f"{API_BASE_URL}{path}",
        headers=build_headers(token=token, json_content=False),
        params=params,
        timeout=20,
    )
    return handle_response(response)


# ------------------------------------------------------------
# Realizar petición POST
# ------------------------------------------------------------
def api_post(path: str, payload: dict, token: str | None = None):
    """
    Ejecuta una petición POST al backend.

    Parámetros:
        path (str): ruta relativa del endpoint
        payload (dict): cuerpo JSON a enviar
        token (str | None): token JWT opcional

    Retorna:
        dict | list: respuesta JSON del backend
    """
    response = requests.post(
        f"{API_BASE_URL}{path}",
        headers=build_headers(token=token, json_content=True),
        json=payload,
        timeout=20,
    )
    return handle_response(response)


# ------------------------------------------------------------
# Realizar petición PATCH
# ------------------------------------------------------------
def api_patch(path: str, payload: dict, token: str | None = None):
    """
    Ejecuta una petición PATCH al backend.

    Parámetros:
        path (str): ruta relativa del endpoint
        payload (dict): cuerpo JSON a enviar
        token (str | None): token JWT opcional

    Retorna:
        dict | list: respuesta JSON del backend
    """
    response = requests.patch(
        f"{API_BASE_URL}{path}",
        headers=build_headers(token=token, json_content=True),
        json=payload,
        timeout=20,
    )
    return handle_response(response)


# ------------------------------------------------------------
# Realizar petición DELETE
# ------------------------------------------------------------
def api_delete(path: str, token: str | None = None):
    """
    Ejecuta una petición DELETE al backend.

    Parámetros:
        path (str): ruta relativa del endpoint
        token (str | None): token JWT opcional

    Retorna:
        dict | list: respuesta JSON del backend
    """
    response = requests.delete(
        f"{API_BASE_URL}{path}",
        headers=build_headers(token=token, json_content=False),
        timeout=20,
    )
    return handle_response(response)