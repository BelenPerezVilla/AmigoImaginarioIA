# ============================================================
# mobile_backend/app/routers/chats.py
# Endpoints de conversaciones y mensajes para la app móvil.
# Incluye control de roles y consumo de tokens.
# ============================================================

from fastapi import APIRouter, Depends, HTTPException, status

from database.access_control import (
    assert_module_access,
    build_no_tokens_assistant_message,
    can_send_message_with_tokens,
    consume_user_token,
    get_token_status,
)
from database.chat_db import (
    add_message,
    create_conversation,
    get_conversation_by_id,
    get_messages_by_conversation,
    list_conversations_by_module,
    update_title_if_default,
)
from mobile_backend.app.core.deps import get_current_user
from mobile_backend.app.schemas import (
    ConversationOut,
    MessageOut,
    SendMessageRequest,
    SendMessageResponse,
    TokenStatusOut,
)
from services.gemini_service import (
    generar_respuesta,
    generar_respuesta_biblioteca_rag,
)

# ------------------------------------------------------------
# Router de chats
# ------------------------------------------------------------
router = APIRouter(prefix="/api/chats", tags=["chats"])


# ------------------------------------------------------------
# Construir perfil suave del usuario actual
# ------------------------------------------------------------
def build_friend_profile(current_user: dict) -> dict:
    """
    Construye el perfil suave del amigo imaginario a partir
    del usuario autenticado.
    """
    return {
        "favorite_color": current_user.get("favorite_color", "") or "",
        "favorite_activity": current_user.get("favorite_activity", "") or "",
        "encouragement_style": current_user.get("encouragement_style", "") or "",
        "preferred_comfort": current_user.get("preferred_comfort", "cuentos") or "cuentos",
    }


# ------------------------------------------------------------
# Validar acceso a módulo y convertir errores en HTTP
# ------------------------------------------------------------
def require_module_access(current_user: dict, module: str) -> None:
    """
    Verifica permisos de acceso al módulo solicitado.
    """
    try:
        assert_module_access(current_user, module)
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(error),
        ) from error


# ------------------------------------------------------------
# Listar conversaciones por módulo
# ------------------------------------------------------------
@router.get("/{module}", response_model=list[ConversationOut])
def list_module_conversations(
    module: str,
    current_user: dict = Depends(get_current_user),
) -> list[ConversationOut]:
    """
    Devuelve las conversaciones del usuario para un módulo.
    """
    require_module_access(current_user, module)

    conversations = list_conversations_by_module(
        user_id=current_user["id"],
        module=module,
        limit=100
    )

    return [ConversationOut(**conversation) for conversation in conversations]


# ------------------------------------------------------------
# Crear conversación
# ------------------------------------------------------------
@router.post("/{module}", response_model=ConversationOut)
def create_module_conversation(
    module: str,
    current_user: dict = Depends(get_current_user),
) -> ConversationOut:
    """
    Crea una conversación vacía para un módulo.
    """
    require_module_access(current_user, module)

    conversation_id = create_conversation(
        user_id=current_user["id"],
        module=module
    )

    conversation = get_conversation_by_id(
        conversation_id=conversation_id,
        user_id=current_user["id"]
    )

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="No se pudo crear la conversación."
        )

    return ConversationOut(**conversation)


# ------------------------------------------------------------
# Obtener mensajes de una conversación
# ------------------------------------------------------------
@router.get("/conversations/{conversation_id}", response_model=list[MessageOut])
def get_conversation_messages(
    conversation_id: int,
    current_user: dict = Depends(get_current_user),
) -> list[MessageOut]:
    """
    Devuelve los mensajes de una conversación del usuario.
    """
    conversation = get_conversation_by_id(
        conversation_id=conversation_id,
        user_id=current_user["id"]
    )

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversación no encontrada."
        )

    require_module_access(current_user, conversation["module"])

    messages = get_messages_by_conversation(
        conversation_id=conversation_id,
        user_id=current_user["id"]
    )

    return [MessageOut(**message) for message in messages]


# ------------------------------------------------------------
# Enviar mensaje a una conversación
# ------------------------------------------------------------
@router.post("/conversations/{conversation_id}/messages", response_model=SendMessageResponse)
def send_message_to_conversation(
    conversation_id: int,
    payload: SendMessageRequest,
    current_user: dict = Depends(get_current_user),
) -> SendMessageResponse:
    """
    Guarda el mensaje del usuario, valida tokens, genera respuesta de IA
    y devuelve ambos mensajes.
    """
    conversation = get_conversation_by_id(
        conversation_id=conversation_id,
        user_id=current_user["id"]
    )

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversación no encontrada."
        )

    require_module_access(current_user, conversation["module"])

    # --------------------------------------------------------
    # Validar tokens antes de llamar al modelo
    # --------------------------------------------------------
    can_send, token_status = can_send_message_with_tokens(current_user["id"])

    # --------------------------------------------------------
    # Guardar mensaje del usuario
    # --------------------------------------------------------
    user_message_id = add_message(
        conversation_id=conversation_id,
        role="user",
        content=payload.content
    )

    update_title_if_default(
        conversation_id=conversation_id,
        user_id=current_user["id"],
        user_message=payload.content
    )

    if not can_send:
        assistant_message_id = add_message(
            conversation_id=conversation_id,
            role="assistant",
            content=build_no_tokens_assistant_message(current_user["id"]),
        )

        updated_messages = get_messages_by_conversation(
            conversation_id=conversation_id,
            user_id=current_user["id"]
        )

        user_message = next(message for message in updated_messages if message["id"] == user_message_id)
        assistant_message = next(message for message in updated_messages if message["id"] == assistant_message_id)

        return SendMessageResponse(
            user_message=MessageOut(**user_message),
            assistant_message=MessageOut(**assistant_message),
            token_status=TokenStatusOut(**get_token_status(current_user["id"])),
        )

    # --------------------------------------------------------
    # Reconstruir historial actual para generar respuesta
    # --------------------------------------------------------
    mensajes = get_messages_by_conversation(
        conversation_id=conversation_id,
        user_id=current_user["id"]
    )

    mensajes_prompt = [
        {
            "role": message["role"],
            "content": message["content"]
        }
        for message in mensajes
    ]

    # --------------------------------------------------------
    # Seleccionar generador según módulo
    # --------------------------------------------------------
    try:
        if conversation["module"] == "biblioteca_inteligente":
            assistant_content = generar_respuesta_biblioteca_rag(
                mensajes=mensajes_prompt
            )
        else:
            assistant_content = generar_respuesta(
                modulo=conversation["module"],
                mensajes=mensajes_prompt,
                friend_name=current_user.get("friend_name", "Lumi") or "Lumi",
                friend_profile=build_friend_profile(current_user),
            )
    except RuntimeError:
        assistant_content = (
            "No pude generar una respuesta en este momento. "
            "Revisa que la API key de Gemini esté vigente y configurada correctamente."
        )
    except Exception:
        assistant_content = (
            "Ocurrió un problema al generar la respuesta. "
            "Intenta nuevamente o revisa la consola del backend."
        )

    # --------------------------------------------------------
    # Consumir token solo después de tener respuesta controlada
    # --------------------------------------------------------
    token_status = consume_user_token(
        user_id=current_user["id"],
        conversation_id=conversation_id,
        module=conversation["module"],
        amount=1,
        reason="chat_message",
    )

    # --------------------------------------------------------
    # Guardar respuesta de la IA
    # --------------------------------------------------------
    assistant_message_id = add_message(
        conversation_id=conversation_id,
        role="assistant",
        content=assistant_content
    )

    updated_messages = get_messages_by_conversation(
        conversation_id=conversation_id,
        user_id=current_user["id"]
    )

    user_message = next(
        message for message in updated_messages
        if message["id"] == user_message_id
    )

    assistant_message = next(
        message for message in updated_messages
        if message["id"] == assistant_message_id
    )

    return SendMessageResponse(
        user_message=MessageOut(**user_message),
        assistant_message=MessageOut(**assistant_message),
        token_status=TokenStatusOut(**token_status),
    )