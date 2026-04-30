# ============================================================
# mobile_backend/app/core/config.py
# Configuración del backend móvil.
# ============================================================

import os
from dotenv import load_dotenv

# ------------------------------------------------------------
# Cargar variables de entorno
# ------------------------------------------------------------
load_dotenv()

# ------------------------------------------------------------
# Configuración JWT
# La clave debe tener al menos 32 caracteres para evitar
# advertencias de seguridad con HS256.
# ------------------------------------------------------------
JWT_SECRET = os.getenv(
    "JWT_SECRET",
    "amigo_imaginario_mobile_clave_super_segura_2026"
).strip()

JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256").strip()
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "43200"))

# ------------------------------------------------------------
# Configuración CORS
# ------------------------------------------------------------
_raw_origins = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:8081,http://127.0.0.1:8081,exp://127.0.0.1:8081"
)

ALLOWED_ORIGINS = [
    origin.strip()
    for origin in _raw_origins.split(",")
    if origin.strip()
]