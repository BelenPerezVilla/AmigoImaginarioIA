# ============================================================
# mobile_backend/app/core/deps.py
# Dependencias de autenticación para FastAPI.
# ============================================================

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from database.chat_db import get_user_by_id
from mobile_backend.app.core.security import decode_access_token

# ------------------------------------------------------------
# Esquema Bearer
# ------------------------------------------------------------
bearer_scheme = HTTPBearer(auto_error=True)


# ------------------------------------------------------------
# Obtener usuario actual autenticado
# ------------------------------------------------------------
def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> dict:
    """
    Obtiene el usuario actual a partir del token Bearer.

    Parámetros:
        credentials: credenciales Bearer inyectadas por FastAPI

    Retorna:
        dict: usuario autenticado
    """
    token = credentials.credentials

    try:
        payload = decode_access_token(token)
        user_id = int(payload["sub"])
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado."
        ) from error

    user = get_user_by_id(user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no encontrado."
        )

    return user