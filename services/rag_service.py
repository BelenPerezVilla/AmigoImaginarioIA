# ============================================================
# services/rag_service.py
# Recuperación simple de contexto (RAG) sobre la biblioteca.
# - Lee artículos desde SQLite
# - Divide artículos en fragmentos
# - Puntúa relevancia por coincidencia de términos
# - Devuelve contexto listo para usar con Gemini
# ============================================================

import re
import unicodedata

from database.chat_db import list_all_articles


# ------------------------------------------------------------
# Stopwords simples en español para limpiar la búsqueda
# ------------------------------------------------------------
STOPWORDS = {
    "a", "al", "algo", "alguna", "algunas", "alguno", "algunos",
    "ante", "antes", "como", "con", "contra", "cual", "cuales",
    "de", "del", "desde", "donde", "dos", "el", "ella", "ellas",
    "ellos", "en", "entre", "era", "eramos", "es", "esa", "esas",
    "ese", "eso", "esos", "esta", "estaba", "estado", "estas",
    "este", "esto", "estos", "fue", "ha", "han", "hay", "la",
    "las", "le", "les", "lo", "los", "mas", "me", "mi", "mis",
    "mucho", "muy", "no", "nos", "o", "otra", "otras", "otro",
    "otros", "para", "pero", "poco", "por", "porque", "que",
    "se", "ser", "si", "sin", "sobre", "su", "sus", "te", "tiene",
    "tienen", "tu", "tus", "un", "una", "unas", "uno", "unos", "y", "ya"
}


# ------------------------------------------------------------
# Normalizar texto para búsqueda
# ------------------------------------------------------------
def normalizar_texto(texto: str) -> str:
    """
    Convierte texto a minúsculas, quita acentos y limpia espacios.

    Parámetros:
        texto (str): texto original

    Retorna:
        str: texto normalizado
    """
    texto = str(texto or "").lower().strip()

    # Quitar acentos para comparar mejor palabras parecidas
    texto = "".join(
        caracter for caracter in unicodedata.normalize("NFD", texto)
        if unicodedata.category(caracter) != "Mn"
    )

    # Colapsar espacios repetidos
    texto = " ".join(texto.split())

    return texto


# ------------------------------------------------------------
# Tokenizar texto
# ------------------------------------------------------------
def tokenizar(texto: str) -> list[str]:
    """
    Convierte un texto en tokens simples para búsqueda.

    Parámetros:
        texto (str): texto a tokenizar

    Retorna:
        list[str]: lista de tokens filtrados
    """
    texto = normalizar_texto(texto)
    tokens = re.findall(r"\b[a-zA-Z0-9áéíóúüñ]+\b", texto)

    # Filtrar stopwords y tokens demasiado cortos
    return [
        token for token in tokens
        if token not in STOPWORDS and len(token) >= 3
    ]


# ------------------------------------------------------------
# Construir consulta desde el historial del chat
# ------------------------------------------------------------
def construir_query_desde_mensajes(mensajes: list[dict], max_user_msgs: int = 3) -> str:
    """
    Construye una consulta usando los mensajes más recientes del usuario.

    Parámetros:
        mensajes (list[dict]): historial del chat
        max_user_msgs (int): cuántos mensajes del usuario considerar

    Retorna:
        str: consulta compuesta
    """
    mensajes_usuario = [
        m["content"]
        for m in mensajes
        if m.get("role") == "user"
    ]

    mensajes_recientes = mensajes_usuario[-max_user_msgs:]

    return " ".join(str(mensaje).strip() for mensaje in mensajes_recientes).strip()


# ------------------------------------------------------------
# Dividir contenido en secciones útiles
# ------------------------------------------------------------
def dividir_contenido_en_secciones(content: str) -> list[str]:
    """
    Divide el contenido markdown del artículo en secciones simples.

    Parámetros:
        content (str): contenido del artículo

    Retorna:
        list[str]: secciones del artículo
    """
    texto = str(content or "").strip()

    if not texto:
        return []

    # Intentar dividir por encabezados markdown
    secciones = re.split(r"\n(?=#+\s)", texto)

    # Si no salieron secciones útiles, dividir por párrafos amplios
    if len(secciones) <= 1:
        secciones = re.split(r"\n\s*\n", texto)

    # Limpiar secciones vacías
    return [seccion.strip() for seccion in secciones if seccion.strip()]


# ------------------------------------------------------------
# Convertir un artículo en fragmentos recuperables
# ------------------------------------------------------------
def convertir_articulo_a_fragmentos(article: dict) -> list[dict]:
    """
    Convierte un artículo en fragmentos que luego se pueden puntuar.

    Parámetros:
        article (dict): artículo de la biblioteca

    Retorna:
        list[dict]: fragmentos del artículo
    """
    title = article.get("title", "")
    category = article.get("category", "")
    reader_type = article.get("reader_type", "")
    short_description = article.get("short_description", "")
    content = article.get("content", "")

    secciones = dividir_contenido_en_secciones(content)
    fragmentos = []

    # Fragmento inicial con resumen
    fragmentos.append({
        "article_id": article.get("id"),
        "title": title,
        "category": category,
        "reader_type": reader_type,
        "section_name": "Resumen",
        "text": short_description.strip(),
    })

    # Fragmentos por sección
    for index, seccion in enumerate(secciones, start=1):
        nombre_seccion = f"Sección {index}"

        # Si inicia con encabezado markdown, úsalo como nombre
        primera_linea = seccion.splitlines()[0].strip()
        if primera_linea.startswith("#"):
            nombre_seccion = primera_linea.lstrip("#").strip() or nombre_seccion

        fragmentos.append({
            "article_id": article.get("id"),
            "title": title,
            "category": category,
            "reader_type": reader_type,
            "section_name": nombre_seccion,
            "text": seccion.strip(),
        })

    return fragmentos


# ------------------------------------------------------------
# Puntuar relevancia de un fragmento
# ------------------------------------------------------------
def puntuar_fragmento(query_text: str, query_tokens: list[str], fragmento: dict) -> float:
    """
    Calcula una puntuación simple de relevancia.

    Parámetros:
        query_text (str): consulta completa normalizada
        query_tokens (list[str]): tokens de la consulta
        fragmento (dict): fragmento del artículo

    Retorna:
        float: score de relevancia
    """
    titulo = fragmento.get("title", "")
    categoria = fragmento.get("category", "")
    lector = fragmento.get("reader_type", "")
    texto = fragmento.get("text", "")

    texto_fragmento = " ".join([
        titulo,
        categoria,
        lector,
        texto,
    ])

    tokens_fragmento = set(tokenizar(texto_fragmento))

    # Coincidencia básica por tokens
    coincidencias = sum(1 for token in query_tokens if token in tokens_fragmento)

    # Bonos adicionales por matches en campos importantes
    score = float(coincidencias)

    titulo_norm = normalizar_texto(titulo)
    categoria_norm = normalizar_texto(categoria)
    lector_norm = normalizar_texto(lector)
    texto_norm = normalizar_texto(texto)

    for token in query_tokens:
        if token in titulo_norm:
            score += 2.0
        if token in categoria_norm:
            score += 1.5
        if token in lector_norm:
            score += 1.0

    # Bonus si la consulta completa aparece parcial en el texto
    if query_text and query_text in texto_norm:
        score += 3.0

    return score


# ------------------------------------------------------------
# Recuperar contexto desde la biblioteca
# ------------------------------------------------------------
def recuperar_contexto_biblioteca(
    mensajes: list[dict],
    max_fragmentos: int = 4,
    max_articulos: int = 500
) -> dict:
    """
    Recupera fragmentos relevantes desde la biblioteca para usarlos
    como contexto en el módulo educativo.

    Parámetros:
        mensajes (list[dict]): historial del chat
        max_fragmentos (int): máximo de fragmentos a devolver
        max_articulos (int): máximo de artículos a revisar

    Retorna:
        dict: contexto recuperado y fuentes
    """
    query = construir_query_desde_mensajes(mensajes)
    query_norm = normalizar_texto(query)
    query_tokens = tokenizar(query)

    if not query_tokens:
        return {
            "query": query,
            "fragments": [],
            "context_text": "",
            "sources": [],
        }

    articulos = list_all_articles(limit=max_articulos)
    candidatos = []

    for articulo in articulos:
        fragmentos = convertir_articulo_a_fragmentos(articulo)

        for fragmento in fragmentos:
            score = puntuar_fragmento(
                query_text=query_norm,
                query_tokens=query_tokens,
                fragmento=fragmento
            )

            if score > 0:
                fragmento_con_score = dict(fragmento)
                fragmento_con_score["score"] = score
                candidatos.append(fragmento_con_score)

    # Ordenar por score descendente
    candidatos.sort(key=lambda item: item["score"], reverse=True)

    # Evitar demasiados fragmentos del mismo artículo
    seleccionados = []
    articulos_usados = {}

    for candidato in candidatos:
        article_id = candidato["article_id"]
        usados = articulos_usados.get(article_id, 0)

        # Máximo 2 fragmentos por artículo para dar variedad
        if usados >= 2:
            continue

        seleccionados.append(candidato)
        articulos_usados[article_id] = usados + 1

        if len(seleccionados) >= max_fragmentos:
            break

    # Construir texto de contexto final
    bloques_contexto = []
    fuentes = []

    for index, fragmento in enumerate(seleccionados, start=1):
        fuente = f"{fragmento['title']} ({fragmento['category']} · {fragmento['reader_type']})"
        fuentes.append(fuente)

        bloques_contexto.append(
            f"""[Fragmento {index}]
Fuente: {fuente}
Sección: {fragmento['section_name']}
Contenido:
{fragmento['text']}
"""
        )

    # Quitar duplicados de fuentes conservando orden
    fuentes_unicas = list(dict.fromkeys(fuentes))

    return {
        "query": query,
        "fragments": seleccionados,
        "context_text": "\n\n".join(bloques_contexto).strip(),
        "sources": fuentes_unicas,
    }