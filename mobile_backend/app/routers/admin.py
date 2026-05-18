# ============================================================
# mobile_backend/app/routers/admin.py
# Administración móvil para superadmin:
# - usuarios
# - roles
# - tokens
# - cuentas guest
# - solicitudes de apoyo de padres
# - directorio profesional
# - vínculos padre-hijo
# ============================================================

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from database.access_control import (
    create_guest_user,
    deactivate_guest_user,
    extend_guest_user,
    list_guest_users,
    list_users_with_access,
    set_user_token_policy,
    update_user_role,
)

from database.support_db import (
    add_support_reply,
    create_support_contact,
    deactivate_support_contact,
    list_recommended_contacts_for_request,
    list_support_contacts,
    list_support_replies,
    list_support_requests_for_superadmin,
    recommend_contact_for_request,
    update_support_request_status,
    link_parent_child,
    list_parent_child_links,
    unlink_parent_child,
)

from mobile_backend.app.core.deps import get_current_superadmin


# Router principal de administración.
# Todas las rutas de este archivo quedan protegidas por get_current_superadmin.
router = APIRouter(prefix="/api/admin", tags=["admin"])


# ============================================================
# Schemas: usuarios / guests / tokens
# ============================================================

class UpdateRoleRequest(BaseModel):
    # Rol nuevo que se asignará al usuario.
    role: str = Field(min_length=1)


class UpdateTokensRequest(BaseModel):
    # Límite diario de tokens del usuario.
    daily_limit: int = Field(ge=0)

    # Intervalo de reinicio del contador de tokens.
    reset_interval_hours: int = Field(default=24, ge=1)

    # Umbral bajo para alertas o control interno.
    low_threshold: int = Field(default=5, ge=0)


class CreateGuestRequest(BaseModel):
    # Datos para crear una cuenta invitada.
    username: str = Field(min_length=3)
    password: str = Field(min_length=8)
    display_name: str = Field(min_length=1)
    guest_type: str = Field(min_length=1)
    hours: int = Field(default=4, ge=1)
    token_limit: int = Field(default=10, ge=0)


class ExtendGuestRequest(BaseModel):
    # Horas extra que se agregarán a una cuenta invitada.
    extra_hours: int = Field(default=1, ge=1)


# ============================================================
# Schemas: apoyo a padres / directorio profesional
# ============================================================

class AddSupportReplyRequest(BaseModel):
    # Mensaje de respuesta del superadmin hacia la solicitud de apoyo.
    message: str = Field(min_length=1, max_length=4000)

    # Nuevo estado de la solicitud después de responder.
    new_status: str = Field(default="in_review")


class UpdateSupportStatusRequest(BaseModel):
    # Estado nuevo para la solicitud de apoyo.
    status: str = Field(min_length=1)


class CreateSupportContactRequest(BaseModel):
    # Información del profesional que se agregará al directorio.
    name: str = Field(min_length=1, max_length=180)
    specialty: str = Field(default="", max_length=180)
    organization: str = Field(default="", max_length=180)
    phone: str = Field(default="", max_length=80)
    email: str = Field(default="", max_length=180)
    address: str = Field(default="", max_length=300)
    notes: str = Field(default="", max_length=1000)


class RecommendContactRequest(BaseModel):
    # Nota opcional del superadmin al recomendar un profesional.
    note: str = Field(default="", max_length=1000)


class CreateParentChildLinkRequest(BaseModel):
    # ID del padre/tutor y del niño que se van a vincular.
    parent_user_id: int = Field(ge=1)
    child_user_id: int = Field(ge=1)


# ============================================================
# Usuarios
# ============================================================

@router.get("/users")
def admin_list_users(
    current_user: dict = Depends(get_current_superadmin),
) -> list[dict]:
    """
    Lista usuarios del sistema.
    Solo puede acceder el superadmin porque la dependencia get_current_superadmin
    ya valida el rol antes de entrar a esta función.
    """

    return list_users_with_access(limit=500)


@router.patch("/users/{user_id}/role")
def admin_update_user_role(
    user_id: int,
    payload: UpdateRoleRequest,
    current_user: dict = Depends(get_current_superadmin),
) -> dict:
    """
    Actualiza el rol de un usuario.
    Solo el superadmin puede modificar roles.
    """

    try:
        return update_user_role(
            user_id=user_id,
            role=payload.role,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error


@router.patch("/users/{user_id}/tokens")
def admin_update_user_tokens(
    user_id: int,
    payload: UpdateTokensRequest,
    current_user: dict = Depends(get_current_superadmin),
) -> dict:
    """
    Actualiza la política de tokens de un usuario.
    Solo el superadmin puede modificar límites de uso.
    """

    try:
        return set_user_token_policy(
            user_id=user_id,
            daily_limit=payload.daily_limit,
            reset_interval_hours=payload.reset_interval_hours,
            low_threshold=payload.low_threshold,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error


# ============================================================
# Guests
# ============================================================

@router.get("/guests")
def admin_list_guests(
    current_user: dict = Depends(get_current_superadmin),
) -> list[dict]:
    """
    Lista cuentas invitadas.
    Solo el superadmin puede consultar esta información.
    """

    return list_guest_users(limit=500)


@router.post("/guests")
def admin_create_guest(
    payload: CreateGuestRequest,
    current_user: dict = Depends(get_current_superadmin),
) -> dict:
    """
    Crea una cuenta invitada.
    Se guarda el ID del superadmin que la creó.
    """

    try:
        return create_guest_user(
            created_by_user_id=current_user["id"],
            username=payload.username,
            password=payload.password,
            display_name=payload.display_name,
            guest_type=payload.guest_type,
            hours=payload.hours,
            token_limit=payload.token_limit,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error


@router.patch("/guests/{user_id}/extend")
def admin_extend_guest(
    user_id: int,
    payload: ExtendGuestRequest,
    current_user: dict = Depends(get_current_superadmin),
) -> dict:
    """
    Extiende la vigencia de una cuenta invitada.
    """

    try:
        return extend_guest_user(
            user_id=user_id,
            extra_hours=payload.extra_hours,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error


@router.patch("/guests/{user_id}/deactivate")
def admin_deactivate_guest(
    user_id: int,
    current_user: dict = Depends(get_current_superadmin),
) -> dict:
    """
    Desactiva una cuenta invitada.
    """

    try:
        return deactivate_guest_user(user_id)
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error


# ============================================================
# Apoyo a padres / solicitudes
# ============================================================

@router.get("/support-requests")
def admin_list_support_requests(
    status_filter: str = Query(default="Todas"),
    current_user: dict = Depends(get_current_superadmin),
) -> list[dict]:
    """
    Lista solicitudes de apoyo recibidas desde padres/tutores.
    """

    return list_support_requests_for_superadmin(
        status_filter=status_filter,
    )


@router.get("/support-requests/{request_id}/replies")
def admin_list_support_replies(
    request_id: int,
    current_user: dict = Depends(get_current_superadmin),
) -> list[dict]:
    """
    Lista respuestas de una solicitud de apoyo específica.
    """

    return list_support_replies(request_id)


@router.post("/support-requests/{request_id}/reply")
def admin_add_support_reply(
    request_id: int,
    payload: AddSupportReplyRequest,
    current_user: dict = Depends(get_current_superadmin),
) -> dict:
    """
    Agrega una respuesta del superadmin a una solicitud de apoyo.
    """

    try:
        return add_support_reply(
            request_id=request_id,
            author_user_id=current_user["id"],
            message=payload.message,
            new_status=payload.new_status,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error


@router.patch("/support-requests/{request_id}/status")
def admin_update_support_status(
    request_id: int,
    payload: UpdateSupportStatusRequest,
    current_user: dict = Depends(get_current_superadmin),
) -> dict:
    """
    Actualiza el estado de una solicitud de apoyo.
    """

    try:
        return update_support_request_status(
            request_id=request_id,
            status=payload.status,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error


@router.get("/support-requests/{request_id}/contacts")
def admin_list_request_recommended_contacts(
    request_id: int,
    current_user: dict = Depends(get_current_superadmin),
) -> list[dict]:
    """
    Lista contactos profesionales recomendados para una solicitud.
    """

    return list_recommended_contacts_for_request(request_id)


@router.post("/support-requests/{request_id}/contacts/{contact_id}/recommend")
def admin_recommend_contact_for_request(
    request_id: int,
    contact_id: int,
    payload: RecommendContactRequest,
    current_user: dict = Depends(get_current_superadmin),
) -> dict:
    """
    Recomienda un contacto profesional a una solicitud de apoyo.
    """

    try:
        return recommend_contact_for_request(
            request_id=request_id,
            contact_id=contact_id,
            recommended_by_user_id=current_user["id"],
            note=payload.note,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error


# ============================================================
# Directorio profesional
# ============================================================

@router.get("/support-contacts")
def admin_list_support_contacts(
    current_user: dict = Depends(get_current_superadmin),
) -> list[dict]:
    """
    Lista contactos del directorio profesional, incluyendo activos e inactivos.
    Solo el superadmin puede ver esta vista administrativa.
    """

    return list_support_contacts(active_only=False)


@router.post("/support-contacts")
def admin_create_support_contact(
    payload: CreateSupportContactRequest,
    current_user: dict = Depends(get_current_superadmin),
) -> dict:
    """
    Crea un contacto profesional en el directorio.
    Esta acción queda restringida al superadmin.
    """

    try:
        return create_support_contact(
            name=payload.name,
            specialty=payload.specialty,
            organization=payload.organization,
            phone=payload.phone,
            email=payload.email,
            address=payload.address,
            notes=payload.notes,
            created_by_user_id=current_user["id"],
        )
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error


@router.patch("/support-contacts/{contact_id}/deactivate")
def admin_deactivate_support_contact(
    contact_id: int,
    current_user: dict = Depends(get_current_superadmin),
) -> dict:
    """
    Desactiva un contacto profesional del directorio.
    Esta acción queda restringida al superadmin.
    """

    try:
        return deactivate_support_contact(
            contact_id,
            updated_by_user_id=current_user["id"],
        )
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error


# ============================================================
# Vínculos padre-hijo
# ============================================================

@router.get("/parent-child-links")
def admin_list_parent_child_links(
    current_user: dict = Depends(get_current_superadmin),
) -> list[dict]:
    """
    Lista vínculos existentes entre padres/tutores e hijos.
    """

    return list_parent_child_links()


@router.post("/parent-child-links")
def admin_create_parent_child_link(
    payload: CreateParentChildLinkRequest,
    current_user: dict = Depends(get_current_superadmin),
) -> dict:
    """
    Crea un vínculo entre padre/tutor e hijo.
    Solo el superadmin puede administrar estos vínculos.
    """

    try:
        return link_parent_child(
            parent_user_id=payload.parent_user_id,
            child_user_id=payload.child_user_id,
            created_by_user_id=current_user["id"],
        )
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error


@router.delete("/parent-child-links/{parent_user_id}/{child_user_id}")
def admin_delete_parent_child_link(
    parent_user_id: int,
    child_user_id: int,
    current_user: dict = Depends(get_current_superadmin),
) -> dict:
    """
    Elimina un vínculo entre padre/tutor e hijo.
    """

    try:
        unlink_parent_child(
            parent_user_id=parent_user_id,
            child_user_id=child_user_id,
        )

        return {
            "ok": True,
            "message": "Vínculo eliminado correctamente.",
            "parent_user_id": parent_user_id,
            "child_user_id": child_user_id,
        }
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error