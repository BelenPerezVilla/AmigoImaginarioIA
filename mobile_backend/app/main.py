# ============================================================
# mobile_backend/app/main.py
# Punto de entrada del backend móvil en FastAPI.
# ============================================================

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database.chat_db import initialize_database
from database.support_db import initialize_support_schema
from mobile_backend.app.core.config import ALLOWED_ORIGINS
from mobile_backend.app.routers import admin, auth, chats, library, tokens, support

# ------------------------------------------------------------
# Crear aplicación FastAPI
# ------------------------------------------------------------
app = FastAPI(
    title="Amigo Imaginario Mobile API",
    version="1.0.0",
    description="API base para la app móvil del proyecto."
)

# ------------------------------------------------------------
# Inicializar base de datos al arrancar
# ------------------------------------------------------------
initialize_database()
initialize_support_schema()

# ------------------------------------------------------------
# Configurar CORS para Expo / móvil
# ------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------------------------------------------
# Registrar routers
# ------------------------------------------------------------
app.include_router(auth.router)
app.include_router(chats.router)
app.include_router(library.router)
app.include_router(tokens.router)
app.include_router(admin.router)
app.include_router(support.router)


# ------------------------------------------------------------
# Endpoint de salud
# ------------------------------------------------------------
@app.get("/health")
def healthcheck() -> dict:
    """
    Endpoint simple para verificar que la API esté viva.
    """
    return {
        "ok": True,
        "service": "mobile-backend"
    }