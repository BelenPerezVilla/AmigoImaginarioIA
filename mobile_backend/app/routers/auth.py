# ============================================================
# mobile_backend/app/routers/auth.py
# Endpoints de autenticación para la app móvil.
# ============================================================

from fastapi import APIRouter, HTTPException, status

from database.chat_db import authenticate_user, create_user
from mobile_backend.app.core.security import create_access_token
from mobile_backend.app.schemas import (
    AuthResponse,
    LoginRequest,
    RegisterRequest,
    UserOut,
)

# ------------------------------------------------------------
# Router de autenticación
# ------------------------------------------------------------
router = APIRouter(prefix="/api/auth", tags=["auth"])


# ------------------------------------------------------------
# Registro
# ------------------------------------------------------------
@router.post("/register", response_model=AuthResponse)
def register(payload: RegisterRequest) -> AuthResponse:
    """
    Registra un usuario nuevo y devuelve token.
    """
    try:
        user = create_user(
            username=payload.username,
            password=payload.password,
            display_name=payload.display_name,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error)
        ) from error

    token = create_access_token(user_id=user["id"], username=user["username"])

    return AuthResponse(
        access_token=token,
        user=UserOut(**user)
    )


# ------------------------------------------------------------
# Login
# ------------------------------------------------------------
@router.post("/login", response_model=AuthResponse)
def login(payload: LoginRequest) -> AuthResponse:
    """
    Inicia sesión y devuelve token.
    """
    user = authenticate_user(payload.username, payload.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario o contraseña incorrectos."
        )

    token = create_access_token(user_id=user["id"], username=user["username"])

    return AuthResponse(
        access_token=token,
        user=UserOut(**user)
    )