# ============================================================
# mobile_backend/app/schemas.py
# Esquemas Pydantic del backend móvil.
# ============================================================

from pydantic import BaseModel, Field


# ------------------------------------------------------------
# Usuario
# ------------------------------------------------------------
class UserOut(BaseModel):
    id: int
    username: str
    display_name: str
    is_admin: bool


# ------------------------------------------------------------
# Registro
# ------------------------------------------------------------
class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=8, max_length=200)
    display_name: str = Field(default="", max_length=100)


# ------------------------------------------------------------
# Login
# ------------------------------------------------------------
class LoginRequest(BaseModel):
    username: str
    password: str


# ------------------------------------------------------------
# Respuesta de autenticación
# ------------------------------------------------------------
class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


# ------------------------------------------------------------
# Conversación
# ------------------------------------------------------------
class ConversationOut(BaseModel):
    id: int
    user_id: int
    module: str
    title: str
    created_at: str
    updated_at: str


# ------------------------------------------------------------
# Mensaje
# ------------------------------------------------------------
class MessageOut(BaseModel):
    id: int
    role: str
    content: str
    created_at: str


# ------------------------------------------------------------
# Crear conversación
# ------------------------------------------------------------
class CreateConversationRequest(BaseModel):
    module: str


# ------------------------------------------------------------
# Enviar mensaje
# ------------------------------------------------------------
class SendMessageRequest(BaseModel):
    content: str = Field(min_length=1, max_length=12000)


# ------------------------------------------------------------
# Respuesta al enviar mensaje
# ------------------------------------------------------------
class SendMessageResponse(BaseModel):
    user_message: MessageOut
    assistant_message: MessageOut


# ------------------------------------------------------------
# Artículo
# ------------------------------------------------------------
class ArticleOut(BaseModel):
    id: int
    title: str
    category: str
    reader_type: str
    short_description: str
    content: str
    created_at: str