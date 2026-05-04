# ============================================================
# mobile_backend/app/routers/auth.py
# Endpoints de autenticación y perfil para la app móvil.
# ============================================================

from fastapi import APIRouter, Depends, HTTPException, status

from database.chat_db import (
    authenticate_user,
    create_user,
    get_imaginary_friend_profile,
    get_user_by_id,
    update_friend_name,
    update_friend_profile,
    update_imaginary_friend_profile,
)
from mobile_backend.app.core.deps import get_current_user
from mobile_backend.app.core.security import create_access_token
from mobile_backend.app.schemas import (
    AuthResponse,
    ImaginaryFriendAvatarOut,
    LoginRequest,
    RegisterRequest,
    UpdateFriendPreferencesRequest,
    UpdateImaginaryFriendAvatarRequest,
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
# Convertir dict de avatar a esquema de salida
# ------------------------------------------------------------
def build_avatar_out(profile: dict) -> ImaginaryFriendAvatarOut:
    return ImaginaryFriendAvatarOut(
        face_shape=profile.get("face_shape", "redondo") or "redondo",
        primary_color=profile.get("primary_color", "azul") or "azul",
        hair_style=profile.get("hair_style", "corto") or "corto",
        hair_color=profile.get("hair_color", "castano") or "castano",
        eye_style=profile.get("eye_style", "felices") or "felices",
        mouth_style=profile.get("mouth_style", "sonrisa") or "sonrisa",
        accessory=profile.get("accessory", "estrella") or "estrella",
        background_style=profile.get("background_style", "cielo") or "cielo",
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
        # Guardar nombre del amigo
        update_friend_name(
            user_id=current_user["id"],
            friend_name=payload.friend_name,
        )

        # Guardar memoria suave del vínculo
        update_friend_profile(
            user_id=current_user["id"],
            favorite_color=payload.favorite_color,
            favorite_activity=payload.favorite_activity,
            encouragement_style=payload.encouragement_style,
            preferred_comfort=payload.preferred_comfort,
        )

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


# ------------------------------------------------------------
# Obtener avatar actual del amigo imaginario
# ------------------------------------------------------------
@router.get("/me/avatar", response_model=ImaginaryFriendAvatarOut)
def get_avatar(
    current_user: dict = Depends(get_current_user),
) -> ImaginaryFriendAvatarOut:
    profile = get_imaginary_friend_profile(current_user["id"])
    return build_avatar_out(profile)


# ------------------------------------------------------------
# Actualizar avatar visual del amigo imaginario
# ------------------------------------------------------------
@router.patch("/me/avatar", response_model=ImaginaryFriendAvatarOut)
def update_avatar(
    payload: UpdateImaginaryFriendAvatarRequest,
    current_user: dict = Depends(get_current_user),
) -> ImaginaryFriendAvatarOut:
    update_imaginary_friend_profile(
        user_id=current_user["id"],
        face_shape=payload.face_shape,
        primary_color=payload.primary_color,
        hair_style=payload.hair_style,
        hair_color=payload.hair_color,
        eye_style=payload.eye_style,
        mouth_style=payload.mouth_style,
        accessory=payload.accessory,
        background_style=payload.background_style,
    )

    updated_profile = get_imaginary_friend_profile(current_user["id"])
    return build_avatar_out(updated_profile)