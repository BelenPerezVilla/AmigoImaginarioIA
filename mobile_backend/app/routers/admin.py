# ============================================================
# mobile_backend/app/routers/admin.py
# Administración móvil para superadmin:
# - usuarios
# - roles
# - tokens
# - cuentas guest
# ============================================================

from fastapi import APIRouter, Depends, HTTPException, status
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
from mobile_backend.app.core.deps import get_current_user

router = APIRouter(prefix="/api/admin", tags=["admin"])


# ============================================================
# Schemas
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