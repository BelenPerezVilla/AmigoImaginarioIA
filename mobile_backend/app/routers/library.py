# ============================================================
# mobile_backend/app/routers/library.py
# Endpoints de biblioteca para la app móvil.
# Incluye:
# - listado y detalle de artículos
# - favoritos
# - enviar artículo al chat del amigo imaginario
# ============================================================

from fastapi import APIRouter, Depends, HTTPException, Query, status

from database.chat_db import (
    add_article_to_favorites,
    add_message,
    create_conversation,
    get_article_by_id,
    get_conversation_by_id,
    get_friend_profile,
    get_latest_conversation_by_module,
    get_messages_by_conversation,
    is_article_favorite,
    list_favorite_articles,
    remove_article_from_favorites,
    search_articles,
    update_title_if_default,
)
from mobile_backend.app.core.deps import get_current_user
from mobile_backend.app.schemas import (
    ArticleOut,
    FavoriteStateOut,
    SendArticleToChatResponse,
)
from services.gemini_service import generar_respuesta

router = APIRouter(prefix="/api/library", tags=["library"])


# ------------------------------------------------------------
# Convertir artículo a esquema de salida
# ------------------------------------------------------------
def build_article_out(article: dict) -> ArticleOut:
    return ArticleOut(
        id=article["id"],
        title=article["title"],
        category=article["category"],
        reader_type=article["reader_type"],
        short_description=article["short_description"],
        content=article["content"],
        created_at=article["created_at"],
    )


# ------------------------------------------------------------
# Construir prompt para mandar artículo al amigo imaginario
# ------------------------------------------------------------
def build_article_prompt(article: dict) -> str:
    """
    Genera el mensaje que se enviará al chat del amigo
    usando un artículo de la biblioteca como contexto.
    """
    content_clean = str(article.get("content", "") or "").strip()

    # --------------------------------------------------------
    # Limitar longitud para no saturar el prompt
    # --------------------------------------------------------
    if len(content_clean) > 3500:
        content_clean = f"{content_clean[:3500].rstrip()}..."

    return f"""
Quiero hablar contigo sobre un artículo de la biblioteca.

Título: {article["title"]}
Categoría: {article["category"]}
Pensado para: {article["reader_type"]}

Resumen:
{article["short_description"]}

Contenido:
{content_clean}

Ayúdame a entenderlo con palabras sencillas, con un tono amable y cercano.
Si puedes, dame también una idea práctica para aplicar hoy.
""".strip()


# ------------------------------------------------------------
# Listar artículos
# ------------------------------------------------------------
@router.get("/articles", response_model=list[ArticleOut])
def list_articles(
    search: str = Query(default=""),
    category: str = Query(default="Todas"),
    reader_type: str = Query(default="Todos"),
    current_user: dict = Depends(get_current_user),
) -> list[ArticleOut]:
    articles = search_articles(
        search_text=search,
        category=category,
        reader_type=reader_type,
        limit=100,
    )

    return [build_article_out(article) for article in articles]


# ------------------------------------------------------------
# Obtener detalle de artículo
# ------------------------------------------------------------
@router.get("/articles/{article_id}", response_model=ArticleOut)
def get_article(
    article_id: int,
    current_user: dict = Depends(get_current_user),
) -> ArticleOut:
    article = get_article_by_id(article_id)

    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Artículo no encontrado."
        )

    return build_article_out(article)


# ------------------------------------------------------------
# Listar favoritos
# ------------------------------------------------------------
@router.get("/favorites", response_model=list[ArticleOut])
def get_favorites(
    current_user: dict = Depends(get_current_user),
) -> list[ArticleOut]:
    articles = list_favorite_articles(current_user["id"])
    return [build_article_out(article) for article in articles]


# ------------------------------------------------------------
# Agregar artículo a favoritos
# ------------------------------------------------------------
@router.post("/favorites/{article_id}", response_model=FavoriteStateOut)
def add_favorite(
    article_id: int,
    current_user: dict = Depends(get_current_user),
) -> FavoriteStateOut:
    try:
        add_article_to_favorites(current_user["id"], article_id)
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error)
        ) from error

    return FavoriteStateOut(
        article_id=article_id,
        is_favorite=True,
    )


# ------------------------------------------------------------
# Quitar artículo de favoritos
# ------------------------------------------------------------
@router.delete("/favorites/{article_id}", response_model=FavoriteStateOut)
def remove_favorite(
    article_id: int,
    current_user: dict = Depends(get_current_user),
) -> FavoriteStateOut:
    remove_article_from_favorites(current_user["id"], article_id)

    return FavoriteStateOut(
        article_id=article_id,
        is_favorite=False,
    )


# ------------------------------------------------------------
# Mandar artículo al chat del amigo imaginario
# ------------------------------------------------------------
@router.post("/articles/{article_id}/send-to-chat", response_model=SendArticleToChatResponse)
def send_article_to_chat(
    article_id: int,
    current_user: dict = Depends(get_current_user),
) -> SendArticleToChatResponse:
    article = get_article_by_id(article_id)

    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Artículo no encontrado."
        )

    # --------------------------------------------------------
    # Buscar o crear conversación del amigo imaginario
    # --------------------------------------------------------
    conversation = get_latest_conversation_by_module(
        user_id=current_user["id"],
        module="amigo_imaginario",
    )

    if conversation:
        conversation_id = conversation["id"]
    else:
        conversation_id = create_conversation(
            user_id=current_user["id"],
            module="amigo_imaginario",
            title="Nueva conversación",
        )

    # --------------------------------------------------------
    # Construir mensaje del usuario con contexto del artículo
    # --------------------------------------------------------
    user_prompt = build_article_prompt(article)

    add_message(
        conversation_id=conversation_id,
        role="user",
        content=user_prompt,
    )

    update_title_if_default(
        conversation_id=conversation_id,
        user_id=current_user["id"],
        user_message=f"Artículo: {article['title']}",
    )

    # --------------------------------------------------------
    # Recuperar historial y generar respuesta del amigo
    # --------------------------------------------------------
    friend_profile = get_friend_profile(current_user["id"])

    messages = get_messages_by_conversation(
        conversation_id=conversation_id,
        user_id=current_user["id"],
    )

    prompt_messages = [
        {
            "role": message["role"],
            "content": message["content"],
        }
        for message in messages
    ]

    assistant_content = generar_respuesta(
        modulo="amigo_imaginario",
        mensajes=prompt_messages,
        friend_name=friend_profile.get("friend_name", "Lumi"),
        friend_profile=friend_profile,
    )

    add_message(
        conversation_id=conversation_id,
        role="assistant",
        content=assistant_content,
    )

    updated_conversation = get_conversation_by_id(
        conversation_id=conversation_id,
        user_id=current_user["id"],
    )

    return SendArticleToChatResponse(
        conversation_id=conversation_id,
        module="amigo_imaginario",
        title=updated_conversation["title"] if updated_conversation else "Nueva conversación",
    )