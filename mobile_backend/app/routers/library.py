# ============================================================
# mobile_backend/app/routers/library.py
# Endpoints de biblioteca para la app móvil.
# ============================================================

from fastapi import APIRouter, Depends, HTTPException, Query, status

from database.chat_db import get_article_by_id, search_articles
from mobile_backend.app.core.deps import get_current_user
from mobile_backend.app.schemas import ArticleOut

# ------------------------------------------------------------
# Router de biblioteca
# ------------------------------------------------------------
router = APIRouter(prefix="/api/library", tags=["library"])


# ------------------------------------------------------------
# Buscar artículos
# ------------------------------------------------------------
@router.get("/articles", response_model=list[ArticleOut])
def list_articles(
    search: str = Query(default=""),
    category: str = Query(default="Todas"),
    reader_type: str = Query(default="Todos"),
    current_user: dict = Depends(get_current_user),
) -> list[ArticleOut]:
    """
    Devuelve artículos filtrados por texto, categoría y tipo
    de lector.
    """
    articles = search_articles(
        search_text=search,
        category=category,
        reader_type=reader_type,
        limit=200
    )

    return [ArticleOut(**article) for article in articles]


# ------------------------------------------------------------
# Obtener artículo por id
# ------------------------------------------------------------
@router.get("/articles/{article_id}", response_model=ArticleOut)
def get_article(
    article_id: int,
    current_user: dict = Depends(get_current_user),
) -> ArticleOut:
    """
    Devuelve un artículo por su id.
    """
    article = get_article_by_id(article_id)

    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Artículo no encontrado."
        )

    return ArticleOut(**article)