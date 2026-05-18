# ============================================================
# mobile_backend/app/routers/auth.py
# Endpoints de autenticación y perfil para la app móvil.
# ============================================================

from fastapi import APIRouter, Depends, HTTPException, status

from database.access_control import (
    LEGAL_NOTICE_TEXT,
    decorate_user_for_access,
)
from database.chat_db import (
    authenticate_user,
    create_user,
    get_imaginary_friend_profile,
    get_user_by_id,
    update_friend_name,
    update_friend_profile,
    update_imaginary_friend_profile,
)

# Funciones para términos y condiciones
from database.safety_db import (
    TERMS_VERSION,
    accept_terms,
    get_terms_for_role,
    has_accepted_terms,
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
    LegalNoticeOut,
    UserOut,
    AcceptTermsRequest,
    TermsOut,
    TermsStatusOut,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])


# ------------------------------------------------------------
# Convertir dict de usuario a esquema UserOut
# ------------------------------------------------------------
def build_user_out(user: dict) -> UserOut:
    """
    Convierte usuario legacy/nuevo a UserOut con permisos y tokens.
    """
    user = decorate_user_for_access(user) or user

    return UserOut(
        id=user["id"],
        username=user["username"],
        display_name=user["display_name"],
        is_admin=bool(user.get("is_admin", False)),
        friend_name=user.get("friend_name", "Lumi") or "Lumi",
        favorite_color=user.get("favorite_color", "") or "",
        favorite_activity=user.get("favorite_activity", "") or "",
        encouragement_style=user.get("encouragement_style", "") or "",
        preferred_comfort=user.get("preferred_comfort", "cuentos") or "cuentos",
        role=user.get("role", "child") or "child",
        role_label=user.get("role_label", "Usuario niño") or "Usuario niño",
        account_type=user.get("account_type", "permanent") or "permanent",
        guest_type=user.get("guest_type", "") or "",
        guest_status=user.get("guest_status", "none") or "none",
        guest_hours=int(user.get("guest_hours") or 0),
        guest_expires_at=user.get("guest_expires_at", "") or "",
        is_active=bool(user.get("is_active", True)),
        permissions=user.get("permissions") or {},
        allowed_modules=user.get("allowed_modules") or [],
        token_status=user.get("token_status"),
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
    try:
        user = authenticate_user(payload.username, payload.password)
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(error),
        ) from error

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
# Aviso legal vigente
# ------------------------------------------------------------
@router.get("/legal-notice", response_model=LegalNoticeOut)
def legal_notice() -> LegalNoticeOut:
    return LegalNoticeOut(text=LEGAL_NOTICE_TEXT)

# ------------------------------------------------------------
# Términos públicos por rol
# ------------------------------------------------------------
@router.get("/terms", response_model=TermsOut)
def public_terms(role: str = "child") -> TermsOut:
    """
    Devuelve los términos y condiciones según el rol indicado.
    Sirve para mostrar el texto antes de iniciar sesión o registrarse.
    """
    terms = get_terms_for_role(role)

    return TermsOut(
        text=terms["text"],
        version=terms["version"],
        role=terms["role"],
    )


# ------------------------------------------------------------
# Estado de aceptación de términos del usuario actual
# ------------------------------------------------------------
@router.get("/me/terms/status", response_model=TermsStatusOut)
def my_terms_status(
    current_user: dict = Depends(get_current_user),
) -> TermsStatusOut:
    """
    Indica si el usuario ya aceptó la versión vigente de términos.
    """
    return TermsStatusOut(
        accepted=has_accepted_terms(current_user["id"], TERMS_VERSION),
        version=TERMS_VERSION,
        role=current_user.get("role", "child"),
    )


# ------------------------------------------------------------
# Guardar aceptación de términos
# ------------------------------------------------------------
@router.post("/me/terms/accept", response_model=TermsStatusOut)
def accept_my_terms(
    payload: AcceptTermsRequest,
    current_user: dict = Depends(get_current_user),
) -> TermsStatusOut:
    """
    Guarda la aceptación de términos de uso del usuario autenticado.
    """
    if payload.accepted is False:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Debes aceptar los términos para continuar.",
        )

    version = payload.version or TERMS_VERSION

    result = accept_terms(
        user_id=current_user["id"],
        role=current_user.get("role"),
        version=version,
    )

    return TermsStatusOut(
        accepted=bool(result.get("accepted")),
        version=result.get("version", TERMS_VERSION),
        role=result.get("role", current_user.get("role", "child")),
    )
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