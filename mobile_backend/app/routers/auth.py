# ============================================================
# mobile_backend/app/routers/auth.py
# Endpoints de autenticación y perfil para la app móvil.
# ============================================================

from fastapi import APIRouter, Depends, HTTPException, status

from database.chat_db import (
    authenticate_user,
    create_user,
    get_user_by_id,
    update_friend_name,
    update_friend_profile,
)
from mobile_backend.app.core.deps import get_current_user
from mobile_backend.app.core.security import create_access_token
from mobile_backend.app.schemas import (
    AuthResponse,
    LoginRequest,
    RegisterRequest,
    UpdateFriendPreferencesRequest,
    UserOut,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])


# ------------------------------------------------------------
# Convertir dict de usuario a esquema UserOut
# ------------------------------------------------------------
def build_user_out(user: dict) -> UserOut:
    return UserOut(
        id=user["id"],
        username=user["username"],
        display_name=user["display_name"],
        is_admin=bool(user["is_admin"]),
        friend_name=user.get("friend_name", "Lumi") or "Lumi",
        favorite_color=user.get("favorite_color", "") or "",
        favorite_activity=user.get("favorite_activity", "") or "",
        encouragement_style=user.get("encouragement_style", "") or "",
        preferred_comfort=user.get("preferred_comfort", "cuentos") or "cuentos",
    )


# ------------------------------------------------------------
# Registro
# ------------------------------------------------------------
@router.post("/register", response_model=AuthResponse)
def register(payload: RegisterRequest) -> AuthResponse:
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
        user=build_user_out(user)
    )


# ------------------------------------------------------------
# Login
# ------------------------------------------------------------
@router.post("/login", response_model=AuthResponse)
def login(payload: LoginRequest) -> AuthResponse:
    user = authenticate_user(payload.username, payload.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario o contraseña incorrectos."
        )

    token = create_access_token(user_id=user["id"], username=user["username"])

    return AuthResponse(
        access_token=token,
        user=build_user_out(user)
    )


# ------------------------------------------------------------
# Usuario actual autenticado
# ------------------------------------------------------------
@router.get("/me", response_model=UserOut)
def me(current_user: dict = Depends(get_current_user)) -> UserOut:
    fresh_user = get_user_by_id(current_user["id"])

    if not fresh_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado."
        )

    return build_user_out(fresh_user)


# ------------------------------------------------------------
# Actualizar preferencias del amigo imaginario
# ------------------------------------------------------------
@router.patch("/me/preferences", response_model=UserOut)
def update_preferences(
    payload: UpdateFriendPreferencesRequest,
    current_user: dict = Depends(get_current_user),
) -> UserOut:
    try:
        # ----------------------------------------------------
        # Guardar nombre del amigo imaginario
        # ----------------------------------------------------
        update_friend_name(
            user_id=current_user["id"],
            friend_name=payload.friend_name,
        )

        # ----------------------------------------------------
        # Guardar memoria suave del vínculo
        # ----------------------------------------------------
        update_friend_profile(
            user_id=current_user["id"],
            favorite_color=payload.favorite_color,
            favorite_activity=payload.favorite_activity,
            encouragement_style=payload.encouragement_style,
            preferred_comfort=payload.preferred_comfort,
        )

        # ----------------------------------------------------
        # Devolver usuario actualizado desde base de datos
        # ----------------------------------------------------
        updated_user = get_user_by_id(current_user["id"])

        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado después de guardar."
            )

        return build_user_out(updated_user)

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error)
        ) from error