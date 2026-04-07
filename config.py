# ============================================================
# config.py
# Configuración general del proyecto:
# - carga variables de entorno
# - valida API key y modelo
# - define la ruta de la base de datos SQLite
# ============================================================

import os
from dotenv import load_dotenv

# ------------------------------------------------------------
# Cargar variables del archivo .env
# ------------------------------------------------------------
load_dotenv()

# ------------------------------------------------------------
# Configuración de Gemini
# ------------------------------------------------------------
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip()

# ------------------------------------------------------------
# Ruta de la base de datos SQLite
# ------------------------------------------------------------
DATABASE_PATH = os.getenv("DATABASE_PATH", "data/app.db").strip()


def validar_configuracion() -> list[str]:
    """
    Valida que la configuración mínima exista.

    Retorna:
        list[str]: lista de errores encontrados
    """
    errores = []

    # Validar API key
    if not GEMINI_API_KEY:
        errores.append("Falta configurar GEMINI_API_KEY en el archivo .env.")

    # Validar modelo
    if not GEMINI_MODEL:
        errores.append("Falta configurar GEMINI_MODEL en el archivo .env.")

    # Validar ruta de base de datos
    if not DATABASE_PATH:
        errores.append("Falta configurar DATABASE_PATH en el archivo .env.")

    return errores