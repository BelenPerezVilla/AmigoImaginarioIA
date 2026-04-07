# ============================================================
# utils/document_ingestion.py
# Utilidades para leer documentos subidos desde Streamlit y
# extraer texto de TXT, MD y PDF.
# ============================================================

from io import BytesIO
from pathlib import Path

from pypdf import PdfReader


# ------------------------------------------------------------
# Limpiar texto extraído
# ------------------------------------------------------------
def limpiar_texto(texto: str) -> str:
    """
    Limpia espacios innecesarios y líneas vacías repetidas.

    Parámetros:
        texto (str): texto original

    Retorna:
        str: texto limpio
    """
    lineas_limpias = []

    for linea in str(texto or "").splitlines():
        linea = " ".join(linea.strip().split())
        if linea:
            lineas_limpias.append(linea)

    return "\n".join(lineas_limpias).strip()


# ------------------------------------------------------------
# Construir título base desde nombre de archivo
# ------------------------------------------------------------
def titulo_desde_nombre_archivo(filename: str) -> str:
    """
    Convierte el nombre del archivo en un título base legible.

    Parámetros:
        filename (str): nombre del archivo

    Retorna:
        str: título sugerido
    """
    stem = Path(filename).stem
    stem = stem.replace("_", " ").replace("-", " ")
    stem = " ".join(stem.split()).strip()

    return stem.title() if stem else "Documento sin título"


# ------------------------------------------------------------
# Extraer texto desde PDF
# ------------------------------------------------------------
def extraer_texto_pdf(bytes_data: bytes) -> str:
    """
    Extrae texto de un PDF usando pypdf.

    Parámetros:
        bytes_data (bytes): contenido binario del PDF

    Retorna:
        str: texto extraído
    """
    reader = PdfReader(BytesIO(bytes_data))
    paginas = []

    for page in reader.pages:
        paginas.append(page.extract_text() or "")

    return "\n\n".join(paginas).strip()


# ------------------------------------------------------------
# Extraer texto desde TXT o MD
# ------------------------------------------------------------
def extraer_texto_plano(bytes_data: bytes) -> str:
    """
    Extrae texto desde un archivo plano.

    Parámetros:
        bytes_data (bytes): contenido binario del archivo

    Retorna:
        str: texto decodificado
    """
    return bytes_data.decode("utf-8-sig", errors="ignore").strip()


# ------------------------------------------------------------
# Extraer texto desde archivo subido
# ------------------------------------------------------------
def extract_text_from_uploaded_file(uploaded_file, max_chars: int = 45000) -> dict:
    """
    Lee un archivo subido desde Streamlit y devuelve su texto.

    Parámetros:
        uploaded_file: archivo UploadedFile de Streamlit
        max_chars (int): máximo de caracteres que se usarán

    Retorna:
        dict: información del documento y texto extraído
    """
    if uploaded_file is None:
        raise ValueError("No se recibió ningún archivo.")

    filename = uploaded_file.name or "documento"
    extension = Path(filename).suffix.lower()
    bytes_data = uploaded_file.getvalue()

    if extension in {".txt", ".md"}:
        texto = extraer_texto_plano(bytes_data)
    elif extension == ".pdf":
        texto = extraer_texto_pdf(bytes_data)
    else:
        raise ValueError("Formato no soportado. Usa PDF, TXT o MD.")

    texto_limpio = limpiar_texto(texto)

    if not texto_limpio:
        raise ValueError("No se pudo extraer texto útil del archivo.")

    texto_recortado = texto_limpio[:max_chars]

    return {
        "filename": filename,
        "extension": extension,
        "base_title": titulo_desde_nombre_archivo(filename),
        "text": texto_recortado,
        "preview": texto_recortado[:2500],
        "full_length": len(texto_limpio),
        "used_length": len(texto_recortado),
        "was_truncated": len(texto_recortado) < len(texto_limpio),
    }