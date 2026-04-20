# ============================================================
# mobile_backend/app/core/security.py
# Utilidades para crear y validar tokens JWT.
# ============================================================

from datetime import datetime, timedelta, timezone

import jwt

from mobile_backend.app.core.config import (
    JWT_ALGORITHM,
    JWT_EXPIRE_MINUTES,
    JWT_SECRET,
)


# ------------------------------------------------------------
# Crear token de acceso
# ------------------------------------------------------------
def create_access_token(user_id: int, username: str) -> str:
    """
    Genera un token JWT para el usuario autenticado.

    Parámetros:
        user_id (int): identificador del usuario
        username (str): nombre de usuario

    Retorna:
        str: token firmado
    """
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=JWT_EXPIRE_MINUTES)

    payload = {
        "sub": str(user_id),
        "username": username,
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    }

    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


# ------------------------------------------------------------
# Decodificar token
# ------------------------------------------------------------
def decode_access_token(token: str) -> dict:
    """
    Decodifica y valida un token JWT.

    Parámetros:
        token (str): token de acceso

    Retorna:
        dict: payload del token
    """
    return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])