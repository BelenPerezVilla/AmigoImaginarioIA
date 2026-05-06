# ============================================================
# mobile_backend/app/core/deps.py
# Dependencias de autenticación y autorización para FastAPI.
# ============================================================

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from database.access_control import (
    assert_superadmin,
    decorate_user_for_access,
    validate_user_can_login,
)
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
    También valida si la cuenta guest sigue vigente.
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

    try:
        validate_user_can_login(user_id)
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(error),
        ) from error

    decorated_user = decorate_user_for_access(user)

    if not decorated_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no encontrado."
        )

    return decorated_user


# ------------------------------------------------------------
# Obtener usuario superadmin autenticado
# ------------------------------------------------------------
def get_current_superadmin(
    current_user: dict = Depends(get_current_user),
) -> dict:
    """
    Valida que el usuario actual sea superadmin.
    """
    try:
        assert_superadmin(current_user)
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(error),
        ) from error

    return current_user