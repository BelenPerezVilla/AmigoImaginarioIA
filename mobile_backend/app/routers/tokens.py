# ============================================================
# mobile_backend/app/routers/tokens.py
# Endpoints para consultar tokens / créditos de uso.
# ============================================================

from fastapi import APIRouter, Depends

from database.access_control import get_token_status
from mobile_backend.app.core.deps import get_current_user
from mobile_backend.app.schemas import TokenStatusOut

router = APIRouter(prefix="/api/tokens", tags=["tokens"])


# ------------------------------------------------------------
# Estado de tokens del usuario autenticado
# ------------------------------------------------------------
@router.get("/me", response_model=TokenStatusOut)
def my_token_status(current_user: dict = Depends(get_current_user)) -> TokenStatusOut:
    """
    Devuelve tokens restantes, consumo y próximo reinicio.
    """
    return TokenStatusOut(**get_token_status(current_user["id"]))