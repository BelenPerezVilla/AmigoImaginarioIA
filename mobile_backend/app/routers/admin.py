# ============================================================
# mobile_backend/app/routers/admin.py
# Endpoints del panel superadmin:
# - usuarios y roles
# - cuentas guest
# - tokens
# - personalización del amigo de un niño
# ============================================================

from fastapi import APIRouter, Depends, HTTPException, status

from database.access_control import (
    create_guest_user,
    deactivate_guest_user,
    extend_guest_user,
    get_remaining_guest_text,
    list_guest_users,
    list_users_with_access,
    set_user_token_policy,
    update_user_role,
)
from database.chat_db import (
    get_user_by_id,
    update_friend_name,
    update_friend_profile,
    update_imaginary_friend_profile,
    get_imaginary_friend_profile,
)
from mobile_backend.app.core.deps import get_current_superadmin
from mobile_backend.app.routers.auth import build_user_out, build_avatar_out
from mobile_backend.app.schemas import (
    AdminUserOut,
    CreateGuestRequest,
    ExtendGuestRequest,
    GenericMessageOut,
    ImaginaryFriendAvatarOut,
    RoleUpdateRequest,
    TokenPolicyRequest,
    TokenStatusOut,
    UpdateFriendPreferencesRequest,
    UpdateImaginaryFriendAvatarRequest,
    UserOut,
)

router = APIRouter(prefix="/api/admin", tags=["admin"])


# ------------------------------------------------------------
# Convertir usuario admin a salida enriquecida
# ------------------------------------------------------------
def build_admin_user_out(user: dict) -> AdminUserOut:
    """
    Convierte dict de usuario a AdminUserOut.
    """
    base_user = UserOut(**build_user_out(user).model_dump())

    return AdminUserOut(
        **base_user.model_dump(),
        guest_created_by=user.get("guest_created_by"),
        remaining_guest_time=get_remaining_guest_text(user.get("guest_expires_at")),
    )


# ------------------------------------------------------------
# Listar usuarios
# ------------------------------------------------------------
@router.get("/users", response_model=list[AdminUserOut])
def get_users(current_user: dict = Depends(get_current_superadmin)) -> list[AdminUserOut]:
    users = list_users_with_access(limit=500)
    return [build_admin_user_out(user) for user in users]


# ------------------------------------------------------------
# Cambiar rol de usuario permanente
# ------------------------------------------------------------
@router.patch("/users/{user_id}/role", response_model=AdminUserOut)
def change_user_role(
    user_id: int,
    payload: RoleUpdateRequest,
    current_user: dict = Depends(get_current_superadmin),
) -> AdminUserOut:
    try:
        updated = update_user_role(user_id=user_id, role=payload.role)
        return build_admin_user_out(updated)
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error


# ------------------------------------------------------------
# Actualizar tokens de un usuario
# ------------------------------------------------------------
@router.patch("/users/{user_id}/tokens", response_model=TokenStatusOut)
def change_user_tokens(
    user_id: int,
    payload: TokenPolicyRequest,
    current_user: dict = Depends(get_current_superadmin),
) -> TokenStatusOut:
    try:
        status_data = set_user_token_policy(
            user_id=user_id,
            daily_limit=payload.daily_limit,
            reset_interval_hours=payload.reset_interval_hours,
            low_threshold=payload.low_threshold,
        )
        return TokenStatusOut(**status_data)
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error


# ------------------------------------------------------------
# Crear cuenta guest temporal
# ------------------------------------------------------------
@router.post("/guests", response_model=AdminUserOut)
def create_guest(
    payload: CreateGuestRequest,
    current_user: dict = Depends(get_current_superadmin),
) -> AdminUserOut:
    try:
        created = create_guest_user(
            created_by_user_id=current_user["id"],
            username=payload.username,
            password=payload.password,
            display_name=payload.display_name,
            guest_type=payload.guest_type,
            hours=payload.hours,
            token_limit=payload.token_limit,
        )
        return build_admin_user_out(created)
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error


# ------------------------------------------------------------
# Listar cuentas guest
# ------------------------------------------------------------
@router.get("/guests", response_model=list[AdminUserOut])
def get_guests(current_user: dict = Depends(get_current_superadmin)) -> list[AdminUserOut]:
    guests = list_guest_users(limit=500)
    return [build_admin_user_out(guest) for guest in guests]


# ------------------------------------------------------------
# Extender cuenta guest
# ------------------------------------------------------------
@router.patch("/guests/{user_id}/extend", response_model=AdminUserOut)
def extend_guest(
    user_id: int,
    payload: ExtendGuestRequest,
    current_user: dict = Depends(get_current_superadmin),
) -> AdminUserOut:
    try:
        updated = extend_guest_user(user_id=user_id, extra_hours=payload.extra_hours)
        return build_admin_user_out(updated)
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error


# ------------------------------------------------------------
# Desactivar cuenta guest
# ------------------------------------------------------------
@router.patch("/guests/{user_id}/deactivate", response_model=AdminUserOut)
def deactivate_guest(
    user_id: int,
    current_user: dict = Depends(get_current_superadmin),
) -> AdminUserOut:
    try:
        updated = deactivate_guest_user(user_id=user_id)
        return build_admin_user_out(updated)
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error


# ------------------------------------------------------------
# Personalizar preferencias del amigo de un usuario
# ------------------------------------------------------------
@router.patch("/users/{user_id}/friend/preferences", response_model=UserOut)
def update_child_friend_preferences(
    user_id: int,
    payload: UpdateFriendPreferencesRequest,
    current_user: dict = Depends(get_current_superadmin),
) -> UserOut:
    target = get_user_by_id(user_id)

    if not target:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado.",
        )

    update_friend_name(user_id=user_id, friend_name=payload.friend_name)
    update_friend_profile(
        user_id=user_id,
        favorite_color=payload.favorite_color,
        favorite_activity=payload.favorite_activity,
        encouragement_style=payload.encouragement_style,
        preferred_comfort=payload.preferred_comfort,
    )

    updated = get_user_by_id(user_id)
    return build_user_out(updated)


# ------------------------------------------------------------
# Personalizar avatar del amigo de un usuario
# ------------------------------------------------------------
@router.patch("/users/{user_id}/friend/avatar", response_model=ImaginaryFriendAvatarOut)
def update_child_friend_avatar(
    user_id: int,
    payload: UpdateImaginaryFriendAvatarRequest,
    current_user: dict = Depends(get_current_superadmin),
) -> ImaginaryFriendAvatarOut:
    target = get_user_by_id(user_id)

    if not target:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado.",
        )

    update_imaginary_friend_profile(
        user_id=user_id,
        face_shape=payload.face_shape,
        primary_color=payload.primary_color,
        hair_style=payload.hair_style,
        hair_color=payload.hair_color,
        eye_style=payload.eye_style,
        mouth_style=payload.mouth_style,
        accessory=payload.accessory,
        background_style=payload.background_style,
    )

    profile = get_imaginary_friend_profile(user_id)
    return build_avatar_out(profile)


# ------------------------------------------------------------
# Ping de admin
# ------------------------------------------------------------
@router.get("/health", response_model=GenericMessageOut)
def admin_health(current_user: dict = Depends(get_current_superadmin)) -> GenericMessageOut:
    return GenericMessageOut(message="Panel superadmin disponible.")