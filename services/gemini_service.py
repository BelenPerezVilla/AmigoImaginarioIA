# ============================================================
# services/gemini_service.py
# Servicio Gemini para:
# - conversación normal por módulo
# - generación de artículos desde documentos
# - respuestas del módulo educativo con RAG simple
# ============================================================

import time

from google import genai

from config import GEMINI_API_KEY, GEMINI_MODEL
from prompts import SYSTEM_PROMPTS
from services.rag_service import recuperar_contexto_biblioteca


# ------------------------------------------------------------
# Cliente principal de Gemini
# ------------------------------------------------------------
client = genai.Client(api_key=GEMINI_API_KEY)


# ------------------------------------------------------------
# Construir contexto conversacional
# ------------------------------------------------------------
def construir_contexto_texto(mensajes: list[dict]) -> str:
    """
    Convierte el historial reciente a texto plano.

    Parámetros:
        mensajes (list[dict]): historial del chat

    Retorna:
        str: contexto formateado
    """
    lineas = []

    for mensaje in mensajes[-10:]:
        rol = "Usuario" if mensaje["role"] == "user" else "Asistente"
        contenido = str(mensaje["content"]).strip()
        lineas.append(f"{rol}: {contenido}")

    return "\n".join(lineas).strip()


# ------------------------------------------------------------
# Llamada robusta al modelo
# ------------------------------------------------------------
def llamar_modelo(prompt: str) -> str:
    """
    Llama a Gemini con reintentos y fallback de modelo.

    Parámetros:
        prompt (str): prompt final a enviar

    Retorna:
        str: texto generado por el modelo
    """
    modelos_a_probar = [
        GEMINI_MODEL,
        "gemini-2.5-flash-lite",
    ]

    ultimo_error = None

    for modelo in modelos_a_probar:
        for intento in range(3):
            try:
                response = client.models.generate_content(
                    model=modelo,
                    contents=prompt,
                )

                texto = getattr(response, "text", None)

                if texto and texto.strip():
                    return texto.strip()

                raise ValueError("La respuesta del modelo llegó vacía.")

            except Exception as error:
                ultimo_error = error
                mensaje_error = str(error)

                # Reintento simple para saturación temporal
                if "503" in mensaje_error or "UNAVAILABLE" in mensaje_error:
                    time.sleep(2 * (intento + 1))
                    continue

                break

    raise RuntimeError(f"No se pudo generar respuesta. Detalle: {ultimo_error}")


# ------------------------------------------------------------
# Generar respuesta general por módulo
# ------------------------------------------------------------
def generar_respuesta(modulo: str, mensajes: list[dict]) -> str:
    """
    Genera una respuesta de chat según el módulo.

    Parámetros:
        modulo (str): módulo activo
        mensajes (list[dict]): historial de conversación

    Retorna:
        str: respuesta generada
    """
    instrucciones = SYSTEM_PROMPTS.get(
        modulo,
        "Responde con claridad, empatía y responsabilidad."
    )

    contexto = construir_contexto_texto(mensajes)

    prompt_final = f"""
Instrucciones del sistema:
{instrucciones}

Conversación:
{contexto}
""".strip()

    return llamar_modelo(prompt_final)


# ------------------------------------------------------------
# Generar respuesta educativa con RAG
# ------------------------------------------------------------
def generar_respuesta_biblioteca_rag(mensajes: list[dict]) -> str:
    """
    Genera una respuesta para Biblioteca Inteligente usando
    primero fragmentos relevantes de la biblioteca interna.

    Parámetros:
        mensajes (list[dict]): historial de conversación

    Retorna:
        str: respuesta del modelo con apoyo de contexto interno
    """
    instrucciones = SYSTEM_PROMPTS.get(
        "biblioteca_inteligente",
        "Explica con claridad y responsabilidad."
    )

    contexto_chat = construir_contexto_texto(mensajes)
    recuperacion = recuperar_contexto_biblioteca(mensajes)

    contexto_interno = recuperacion["context_text"]
    fuentes = recuperacion["sources"]

    # Si no hay contexto útil, usar el flujo educativo normal
    if not contexto_interno:
        return generar_respuesta("biblioteca_inteligente", mensajes)

    prompt_final = f"""
Instrucciones del sistema:
{instrucciones}

Reglas adicionales para esta respuesta:
- Usa primero el contexto interno recuperado desde la biblioteca.
- Si una idea sí viene del contexto, apóyate en ella claramente.
- Si el contexto no alcanza para responder por completo, complétalo de forma prudente y clara.
- No inventes que algo está en la biblioteca si no aparece en los fragmentos.
- Responde en español.
- Mantén la respuesta ordenada, sencilla y práctica.

Contexto interno recuperado:
{contexto_interno}

Conversación actual:
{contexto_chat}
""".strip()

    respuesta = llamar_modelo(prompt_final)

    if fuentes:
        fuentes_texto = "\n".join(f"- {fuente}" for fuente in fuentes[:4])
        respuesta = f"""{respuesta}

---
**Fuentes internas consultadas**
{fuentes_texto}
""".strip()

    return respuesta


# ------------------------------------------------------------
# Extraer bloque entre marcadores
# ------------------------------------------------------------
def extraer_bloque(texto: str, marcador_inicio: str, marcador_fin: str | None = None) -> str:
    """
    Extrae texto entre dos marcadores.

    Parámetros:
        texto (str): texto completo
        marcador_inicio (str): marcador inicial
        marcador_fin (str | None): marcador final opcional

    Retorna:
        str: contenido del bloque
    """
    inicio = texto.find(marcador_inicio)

    if inicio == -1:
        return ""

    inicio += len(marcador_inicio)

    if marcador_fin is None:
        fin = len(texto)
    else:
        fin = texto.find(marcador_fin, inicio)
        if fin == -1:
            fin = len(texto)

    return texto[inicio:fin].strip()


# ------------------------------------------------------------
# Parsear artículo generado
# ------------------------------------------------------------
def parsear_articulo_generado(texto: str, fallback_title: str) -> dict:
    """
    Convierte la respuesta del modelo en campos de artículo.

    Parámetros:
        texto (str): respuesta cruda del modelo
        fallback_title (str): título de respaldo

    Retorna:
        dict: artículo estructurado
    """
    title = extraer_bloque(
        texto,
        "[[TITLE]]",
        "[[SHORT_DESCRIPTION]]"
    )

    short_description = extraer_bloque(
        texto,
        "[[SHORT_DESCRIPTION]]",
        "[[CONTENT]]"
    )

    content = extraer_bloque(
        texto,
        "[[CONTENT]]",
        None
    )

    # Fallbacks simples por si el modelo no siguió el formato exacto
    if not title:
        title = fallback_title or "Artículo generado desde documento"

    if not short_description:
        short_description = "Artículo generado automáticamente a partir de un documento cargado."

    if not content:
        content = texto.strip()

    return {
        "title": title.strip(),
        "short_description": short_description.strip(),
        "content": content.strip(),
    }


# ------------------------------------------------------------
# Generar artículo desde documento
# ------------------------------------------------------------
def generar_articulo_desde_documento(
    texto_fuente: str,
    category: str,
    reader_type: str,
    suggested_title: str = "",
    source_name: str = ""
) -> dict:
    """
    Convierte el texto de un documento en un artículo listo
    para guardarse en la biblioteca.

    Parámetros:
        texto_fuente (str): contenido del documento
        category (str): categoría destino
        reader_type (str): tipo de lector
        suggested_title (str): título sugerido opcional
        source_name (str): nombre del archivo fuente

    Retorna:
        dict: artículo con title, short_description y content
    """
    titulo_base = suggested_title.strip() or source_name.strip() or "Documento cargado"

    prompt_final = f"""
Actúa como un asistente educativo especializado en neurodivergencia.

Tu tarea es transformar el documento fuente en un artículo educativo claro, ordenado y útil
para la biblioteca de una app.

Reglas:
- El artículo debe estar en español.
- Debe ser comprensible, práctico y fácil de leer.
- Adáptalo para este tipo de lector: {reader_type}
- La categoría objetivo es: {category}
- Si el documento es desordenado, reorganízalo.
- Si el documento es técnico, simplifícalo.
- No inventes datos que no estén sugeridos por el texto.
- Usa markdown en el contenido final.
- Incluye subtítulos y listas cuando ayuden.
- El título debe sonar natural y útil para una biblioteca educativa.

Responde exactamente con este formato y no agregues nada fuera de estos bloques:

[[TITLE]]
título final

[[SHORT_DESCRIPTION]]
descripción breve de 1 o 2 oraciones

[[CONTENT]]
contenido completo del artículo en markdown

Título sugerido:
{titulo_base}

Documento fuente:
\"\"\"
{texto_fuente}
\"\"\"
""".strip()

    respuesta = llamar_modelo(prompt_final)
    articulo = parsear_articulo_generado(respuesta, fallback_title=titulo_base)

    return {
        "title": articulo["title"],
        "category": category.strip(),
        "reader_type": reader_type.strip(),
        "short_description": articulo["short_description"],
        "content": articulo["content"],
    }