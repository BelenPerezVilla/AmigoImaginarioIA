# ============================================================
# mobile_backend/app/schemas.py
# Esquemas Pydantic usados por el backend móvil.
# ============================================================

from pydantic import BaseModel, Field


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