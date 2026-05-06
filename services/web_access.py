# ============================================================
# services/web_access.py
# Cliente web para roles, guests, tokens y aviso legal.
# ============================================================

from services.api_client import api_get, api_patch, api_post


# ------------------------------------------------------------
# Consultar tokens del usuario actual
# ------------------------------------------------------------
def get_my_token_status(token: str) -> dict:
    """
    Obtiene tokens restantes, usados y próximo reinicio.
    """
    return api_get("/api/tokens/me", token=token)


# ------------------------------------------------------------
# Obtener aviso legal vigente
# ------------------------------------------------------------
def get_legal_notice() -> dict:
    """
    Obtiene el aviso legal vigente desde el backend.
    """
    return api_get("/api/auth/legal-notice")


# ------------------------------------------------------------
# Listar usuarios para superadmin
# ------------------------------------------------------------
def admin_list_users(token: str) -> list[dict]:
    """
    Lista usuarios con roles, guests y tokens.
    """
    return api_get("/api/admin/users", token=token)


# ------------------------------------------------------------
# Cambiar rol de usuario
# ------------------------------------------------------------
def admin_update_user_role(token: str, user_id: int, role: str) -> dict:
    """
    Cambia el rol de un usuario permanente.
    """
    return api_patch(
        f"/api/admin/users/{user_id}/role",
        payload={"role": role},
        token=token,
    )


# ------------------------------------------------------------
# Crear cuenta guest
# ------------------------------------------------------------
def admin_create_guest(
    token: str,
    username: str,
    password: str,
    display_name: str,
    guest_type: str,
    hours: int,
    token_limit: int,
) -> dict:
    """
    Crea una cuenta guest temporal.
    """
    return api_post(
        "/api/admin/guests",
        payload={
            "username": username,
            "password": password,
            "display_name": display_name,
            "guest_type": guest_type,
            "hours": hours,
            "token_limit": token_limit,
        },
        token=token,
    )


# ------------------------------------------------------------
# Listar cuentas guest
# ------------------------------------------------------------
def admin_list_guests(token: str) -> list[dict]:
    """
    Lista cuentas guest temporales.
    """
    return api_get("/api/admin/guests", token=token)


# ------------------------------------------------------------
# Extender cuenta guest
# ------------------------------------------------------------
def admin_extend_guest(token: str, user_id: int, extra_hours: int) -> dict:
    """
    Extiende tiempo de una cuenta guest.
    """
    return api_patch(
        f"/api/admin/guests/{user_id}/extend",
        payload={"extra_hours": extra_hours},
        token=token,
    )


# ------------------------------------------------------------
# Desactivar cuenta guest
# ------------------------------------------------------------
def admin_deactivate_guest(token: str, user_id: int) -> dict:
    """
    Desactiva una cuenta guest.
    """
    return api_patch(
        f"/api/admin/guests/{user_id}/deactivate",
        payload={},
        token=token,
    )


# ------------------------------------------------------------
# Cambiar política de tokens
# ------------------------------------------------------------
def admin_update_token_policy(
    token: str,
    user_id: int,
    daily_limit: int,
    reset_interval_hours: int,
    low_threshold: int,
) -> dict:
    """
    Cambia límite y reinicio de tokens de un usuario.
    """
    return api_patch(
        f"/api/admin/users/{user_id}/tokens",
        payload={
            "daily_limit": daily_limit,
            "reset_interval_hours": reset_interval_hours,
            "low_threshold": low_threshold,
        },
        token=token,
    )
