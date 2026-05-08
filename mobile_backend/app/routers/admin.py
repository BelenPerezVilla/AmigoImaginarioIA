# ============================================================
# mobile_backend/app/routers/admin.py
# Administración móvil para superadmin:
# - usuarios
# - roles
# - tokens
# - cuentas guest
# - solicitudes de apoyo de padres
# - contactos recomendados
# ============================================================

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from database.access_control import (
    assert_superadmin,
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
)
from mobile_backend.app.core.deps import get_current_user

router = APIRouter(prefix="/api/admin", tags=["admin"])


# ============================================================
# Schemas: usuarios / guests / tokens
# ============================================================

class UpdateRoleRequest(BaseModel):
    role: str = Field(min_length=1)


class UpdateTokensRequest(BaseModel):
    daily_limit: int = Field(ge=0)
    reset_interval_hours: int = Field(default=24, ge=1)
    low_threshold: int = Field(default=5, ge=0)


class CreateGuestRequest(BaseModel):
    username: str = Field(min_length=3)
    password: str = Field(min_length=8)
    display_name: str = Field(min_length=1)
    guest_type: str = Field(min_length=1)
    hours: int = Field(default=4, ge=1)
    token_limit: int = Field(default=10, ge=0)


class ExtendGuestRequest(BaseModel):
    extra_hours: int = Field(default=1, ge=1)


# ============================================================
# Schemas: apoyo a padres
# ============================================================

class AddSupportReplyRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    new_status: str = Field(default="in_review")


class UpdateSupportStatusRequest(BaseModel):
    status: str = Field(min_length=1)


class CreateSupportContactRequest(BaseModel):
    name: str = Field(min_length=1, max_length=180)
    specialty: str = Field(default="", max_length=180)
    organization: str = Field(default="", max_length=180)
    phone: str = Field(default="", max_length=80)
    email: str = Field(default="", max_length=180)
    address: str = Field(default="", max_length=300)
    notes: str = Field(default="", max_length=1000)


class RecommendContactRequest(BaseModel):
    note: str = Field(default="", max_length=1000)


# ============================================================
# Helper
# ============================================================

def require_superadmin(current_user: dict) -> None:
    try:
        assert_superadmin(current_user)
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(error),
        ) from error


# ============================================================
# Usuarios
# ============================================================

@router.get("/users")
def admin_list_users(
    current_user: dict = Depends(get_current_user),
) -> list[dict]:
    require_superadmin(current_user)
    return list_users_with_access(limit=500)


@router.patch("/users/{user_id}/role")
def admin_update_user_role(
    user_id: int,
    payload: UpdateRoleRequest,
    current_user: dict = Depends(get_current_user),
) -> dict:
    require_superadmin(current_user)

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
    current_user: dict = Depends(get_current_user),
) -> dict:
    require_superadmin(current_user)

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
    current_user: dict = Depends(get_current_user),
) -> list[dict]:
    require_superadmin(current_user)
    return list_guest_users(limit=500)


@router.post("/guests")
def admin_create_guest(
    payload: CreateGuestRequest,
    current_user: dict = Depends(get_current_user),
) -> dict:
    require_superadmin(current_user)

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
    current_user: dict = Depends(get_current_user),
) -> dict:
    require_superadmin(current_user)

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
    current_user: dict = Depends(get_current_user),
) -> dict:
    require_superadmin(current_user)

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
    current_user: dict = Depends(get_current_user),
) -> list[dict]:
    require_superadmin(current_user)

    return list_support_requests_for_superadmin(
        status_filter=status_filter,
    )


@router.get("/support-requests/{request_id}/replies")
def admin_list_support_replies(
    request_id: int,
    current_user: dict = Depends(get_current_user),
) -> list[dict]:
    require_superadmin(current_user)

    return list_support_replies(request_id)


@router.post("/support-requests/{request_id}/reply")
def admin_add_support_reply(
    request_id: int,
    payload: AddSupportReplyRequest,
    current_user: dict = Depends(get_current_user),
) -> dict:
    require_superadmin(current_user)

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
    current_user: dict = Depends(get_current_user),
) -> dict:
    require_superadmin(current_user)

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
    current_user: dict = Depends(get_current_user),
) -> list[dict]:
    require_superadmin(current_user)

    return list_recommended_contacts_for_request(request_id)


@router.post("/support-requests/{request_id}/contacts/{contact_id}/recommend")
def admin_recommend_contact_for_request(
    request_id: int,
    contact_id: int,
    payload: RecommendContactRequest,
    current_user: dict = Depends(get_current_user),
) -> dict:
    require_superadmin(current_user)

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
# Contactos recomendados
# ============================================================

@router.get("/support-contacts")
def admin_list_support_contacts(
    current_user: dict = Depends(get_current_user),
) -> list[dict]:
    require_superadmin(current_user)

    return list_support_contacts(active_only=False)


@router.post("/support-contacts")
def admin_create_support_contact(
    payload: CreateSupportContactRequest,
    current_user: dict = Depends(get_current_user),
) -> dict:
    require_superadmin(current_user)

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
    current_user: dict = Depends(get_current_user),
) -> dict:
    require_superadmin(current_user)

    try:
        return deactivate_support_contact(contact_id)
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error