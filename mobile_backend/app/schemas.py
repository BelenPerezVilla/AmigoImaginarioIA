# ============================================================
# mobile_backend/app/schemas.py
# Esquemas Pydantic usados por el backend móvil.
# Incluye roles, guests, tokens y aviso legal.
# ============================================================

from typing import Any

from pydantic import BaseModel, Field


# ------------------------------------------------------------
# Estado de tokens devuelto por la API
# ------------------------------------------------------------
class TokenStatusOut(BaseModel):
    daily_limit: int
    remaining_tokens: int
    used_tokens: int
    low_threshold: int
    reset_interval_hours: int
    last_reset_at: str = ""
    next_reset_at: str = ""
    is_low: bool = False
    is_empty: bool = False
    is_unlimited: bool = False
    message: str = ""
    reset_text: str = ""


# ------------------------------------------------------------
# Permisos simples para navegación web/móvil
# ------------------------------------------------------------
class PermissionsOut(BaseModel):
    can_access_amigo: bool = False
    can_access_biblioteca: bool = False
    can_access_modo_padres: bool = False
    can_access_admin: bool = False
    can_manage_users: bool = False
    can_manage_guests: bool = False
    can_manage_library: bool = False
    can_customize_child_friend: bool = False
    can_view_tokens: bool = True


# ------------------------------------------------------------
# Usuario de salida para respuestas del backend
# ------------------------------------------------------------
class UserOut(BaseModel):
    id: int
    username: str
    display_name: str
    is_admin: bool
    friend_name: str = "Lumi"
    favorite_color: str = ""
    favorite_activity: str = ""
    encouragement_style: str = ""
    preferred_comfort: str = "cuentos"

    # --------------------------------------------------------
    # Campos nuevos de roles / guest / permisos
    # --------------------------------------------------------
    role: str = "child"
    role_label: str = "Usuario niño"
    account_type: str = "permanent"
    guest_type: str = ""
    guest_status: str = "none"
    guest_hours: int = 0
    guest_expires_at: str = ""
    is_active: bool = True
    permissions: PermissionsOut = Field(default_factory=PermissionsOut)
    allowed_modules: list[str] = Field(default_factory=list)
    token_status: TokenStatusOut | None = None


# ------------------------------------------------------------
# Perfil visual del avatar del amigo imaginario
# ------------------------------------------------------------
class ImaginaryFriendAvatarOut(BaseModel):
    face_shape: str = "redondo"
    primary_color: str = "azul"
    hair_style: str = "corto"
    hair_color: str = "castano"
    eye_style: str = "felices"
    mouth_style: str = "sonrisa"
    accessory: str = "estrella"
    background_style: str = "cielo"


# ------------------------------------------------------------
# Payload para registrar usuario
# ------------------------------------------------------------
class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=8, max_length=200)
    display_name: str = Field(default="", max_length=100)


# ------------------------------------------------------------
# Payload para login
# ------------------------------------------------------------
class LoginRequest(BaseModel):
    username: str
    password: str


# ------------------------------------------------------------
# Payload para actualizar preferencias del amigo imaginario
# ------------------------------------------------------------
class UpdateFriendPreferencesRequest(BaseModel):
    friend_name: str = Field(min_length=2, max_length=30)
    favorite_color: str = Field(default="", max_length=30)
    favorite_activity: str = Field(default="", max_length=50)
    encouragement_style: str = Field(default="", max_length=80)
    preferred_comfort: str = Field(default="cuentos", max_length=30)


# ------------------------------------------------------------
# Payload para actualizar avatar del amigo imaginario
# ------------------------------------------------------------
class UpdateImaginaryFriendAvatarRequest(BaseModel):
    face_shape: str = Field(default="redondo", max_length=30)
    primary_color: str = Field(default="azul", max_length=30)
    hair_style: str = Field(default="corto", max_length=30)
    hair_color: str = Field(default="castano", max_length=30)
    eye_style: str = Field(default="felices", max_length=30)
    mouth_style: str = Field(default="sonrisa", max_length=30)
    accessory: str = Field(default="estrella", max_length=30)
    background_style: str = Field(default="cielo", max_length=30)


# ------------------------------------------------------------
# Respuesta de autenticación
# ------------------------------------------------------------
class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


# ------------------------------------------------------------
# Conversación devuelta por la API
# ------------------------------------------------------------
class ConversationOut(BaseModel):
    id: int
    user_id: int
    module: str
    title: str
    created_at: str
    updated_at: str


# ------------------------------------------------------------
# Mensaje individual devuelto por la API
# ------------------------------------------------------------
class MessageOut(BaseModel):
    id: int
    role: str
    content: str
    created_at: str


# ------------------------------------------------------------
# Payload para enviar mensaje al chat
# ------------------------------------------------------------
class SendMessageRequest(BaseModel):
    content: str = Field(min_length=1, max_length=12000)


# ------------------------------------------------------------
# Respuesta al enviar un mensaje
# ------------------------------------------------------------
class SendMessageResponse(BaseModel):
    user_message: MessageOut
    assistant_message: MessageOut
    token_status: TokenStatusOut | None = None
    blocked_by_safety: bool = False
    safety_category: str = ""
    safety_message: str = ""


# ------------------------------------------------------------
# Artículo de biblioteca devuelto por la API
# ------------------------------------------------------------
class ArticleOut(BaseModel):
    id: int
    title: str
    category: str
    reader_type: str
    short_description: str
    content: str
    created_at: str


# ------------------------------------------------------------
# Estado de favorito para un artículo
# ------------------------------------------------------------
class FavoriteStateOut(BaseModel):
    article_id: int
    is_favorite: bool


# ------------------------------------------------------------
# Respuesta al mandar un artículo al chat del amigo
# ------------------------------------------------------------
class SendArticleToChatResponse(BaseModel):
    conversation_id: int
    module: str
    title: str


# ============================================================
# Esquemas de administración
# ============================================================

class RoleUpdateRequest(BaseModel):
    role: str = Field(max_length=30)


class CreateGuestRequest(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=8, max_length=200)
    display_name: str = Field(default="", max_length=100)
    guest_type: str = Field(default="guest_child", max_length=30)
    hours: int = Field(default=4, ge=1, le=720)
    token_limit: int = Field(default=10, ge=0, le=1000)


class ExtendGuestRequest(BaseModel):
    extra_hours: int = Field(default=1, ge=1, le=720)


class TokenPolicyRequest(BaseModel):
    daily_limit: int = Field(default=20, ge=0, le=10000)
    reset_interval_hours: int = Field(default=24, ge=1, le=720)
    low_threshold: int = Field(default=5, ge=0, le=1000)


class AdminUserOut(UserOut):
    guest_created_by: int | None = None
    remaining_guest_time: str = ""


class LegalNoticeOut(BaseModel):
    text: str
    version: str = "2026-05-06"


class GenericMessageOut(BaseModel):
    ok: bool = True
    message: str
    data: dict[str, Any] | None = None

# ------------------------------------------------------------
# Términos y condiciones
# ------------------------------------------------------------
class TermsOut(BaseModel):
    text: str
    version: str
    role: str = ""


class TermsStatusOut(BaseModel):
    accepted: bool
    version: str
    role: str = ""


class AcceptTermsRequest(BaseModel):
    accepted: bool = True
    version: str = ""