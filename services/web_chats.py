# ============================================================
# services/web_chats.py
# Funciones para que la app web consuma conversaciones y
# mensajes a través del backend FastAPI compartido.
# ============================================================

from services.api_client import api_get, api_post


# ------------------------------------------------------------
# Listar conversaciones por módulo
# ------------------------------------------------------------
def list_web_conversations_by_module(
    token: str,
    module: str,
) -> list[dict]:
    """
    Obtiene las conversaciones del usuario para un módulo.

    Parámetros:
        token (str): token JWT del usuario autenticado
        module (str): nombre del módulo

    Retorna:
        list[dict]: conversaciones del módulo
    """
    return api_get(
        f"/api/chats/{module}",
        token=token
    )


# ------------------------------------------------------------
# Crear conversación nueva para un módulo
# ------------------------------------------------------------
def create_web_conversation(
    token: str,
    module: str,
) -> dict:
    """
    Crea una conversación nueva para el módulo indicado.

    Parámetros:
        token (str): token JWT del usuario autenticado
        module (str): nombre del módulo

    Retorna:
        dict: conversación creada
    """
    return api_post(
        f"/api/chats/{module}",
        payload={},
        token=token
    )


# ------------------------------------------------------------
# Obtener mensajes de una conversación
# ------------------------------------------------------------
def get_web_conversation_messages(
    token: str,
    conversation_id: int,
) -> list[dict]:
    """
    Recupera todos los mensajes de una conversación.

    Parámetros:
        token (str): token JWT del usuario autenticado
        conversation_id (int): id de la conversación

    Retorna:
        list[dict]: mensajes de la conversación
    """
    return api_get(
        f"/api/chats/conversations/{conversation_id}",
        token=token
    )


# ------------------------------------------------------------
# Enviar mensaje al backend compartido
# ------------------------------------------------------------
def send_web_chat_message(
    token: str,
    conversation_id: int,
    content: str,
) -> dict:
    """
    Envía un mensaje a una conversación y deja que el backend
    genere la respuesta del asistente.

    Parámetros:
        token (str): token JWT del usuario autenticado
        conversation_id (int): id de la conversación
        content (str): mensaje del usuario

    Retorna:
        dict: respuesta con user_message y assistant_message
    """
    return api_post(
        f"/api/chats/conversations/{conversation_id}/messages",
        payload={"content": content},
        token=token
    )