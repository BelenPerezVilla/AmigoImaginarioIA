# ============================================================
# services/web_library.py
# Funciones para que la app web consuma la biblioteca
# a través del backend FastAPI compartido.
# ============================================================

from services.api_client import api_get


# ------------------------------------------------------------
# Listar artículos de biblioteca usando el backend
# ------------------------------------------------------------
def list_library_articles(
    token: str,
    search_text: str = "",
    category: str = "Todas",
    reader_type: str = "Todos",
) -> list[dict]:
    """
    Obtiene artículos filtrados desde el backend compartido.

    Parámetros:
        token (str): token JWT del usuario autenticado
        search_text (str): texto de búsqueda
        category (str): categoría o 'Todas'
        reader_type (str): tipo de lector o 'Todos'

    Retorna:
        list[dict]: artículos encontrados
    """
    return api_get(
        "/api/library/articles",
        token=token,
        params={
            "search": search_text.strip(),
            "category": category,
            "reader_type": reader_type,
        }
    )


# ------------------------------------------------------------
# Obtener un artículo por id usando el backend
# ------------------------------------------------------------
def get_library_article(token: str, article_id: int) -> dict:
    """
    Obtiene el detalle de un artículo desde el backend compartido.

    Parámetros:
        token (str): token JWT del usuario autenticado
        article_id (int): id del artículo

    Retorna:
        dict: artículo encontrado
    """
    return api_get(
        f"/api/library/articles/{article_id}",
        token=token
    )


# ------------------------------------------------------------
# Obtener opciones de filtros a partir de los artículos
# ------------------------------------------------------------
def get_library_filter_options(token: str) -> tuple[list[str], list[str]]:
    """
    Genera categorías y tipos de lector disponibles usando
    la API de biblioteca.

    Parámetros:
        token (str): token JWT del usuario autenticado

    Retorna:
        tuple[list[str], list[str]]: categorías, tipos de lector
    """
    articles = list_library_articles(
        token=token,
        search_text="",
        category="Todas",
        reader_type="Todos",
    )

    categories = sorted({
        str(article.get("category", "")).strip()
        for article in articles
        if str(article.get("category", "")).strip()
    })

    reader_types = sorted({
        str(article.get("reader_type", "")).strip()
        for article in articles
        if str(article.get("reader_type", "")).strip()
    })

    return categories, reader_types