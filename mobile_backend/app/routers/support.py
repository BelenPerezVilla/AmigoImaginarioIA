# ============================================================
# mobile_backend/app/routers/support.py
# Endpoints para app móvil:
# - resumen del hijo
# - solicitudes de apoyo de padres
# - respuestas del superadmin / psicólogo
# - contactos recomendados
# - recomendaciones de contacto para chat de Modo Padres
# ============================================================

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from database.access_control import normalize_role
from database.support_db import (
    create_support_request,
    get_child_activity_summary,
    get_support_request_by_id,
    list_children_for_parent,
    list_recommended_contacts_for_request,
    list_support_contacts,
    list_support_replies,
    list_support_requests_for_parent,
    search_support_contacts_by_text,
)
from mobile_backend.app.core.deps import get_current_user
from database.chat_db import (
    get_imaginary_friend_profile,
    get_user_by_id,
    update_friend_name,
    update_friend_profile,
    update_imaginary_friend_profile,
)
from database.support_db import parent_can_view_child
from mobile_backend.app.schemas import (
    UpdateFriendPreferencesRequest,
    UpdateImaginaryFriendAvatarRequest,
)



router = APIRouter(prefix="/api/support", tags=["support"])


# ============================================================
# Schemas locales del router
# ============================================================

class ChildOut(BaseModel):
    id: int
    username: str
    display_name: str
    role: str = ""
    linked_at: str = ""


class TokenWalletOut(BaseModel):
    daily_limit: int = 0
    remaining_tokens: int = 0
    used_tokens: int = 0
    low_threshold: int = 0
    last_reset_at: str = ""
    next_reset_at: str = ""


class SupportSummaryOut(BaseModel):
    total_requests: int = 0
    open_requests: int = 0
    in_review_requests: int = 0
    closed_requests: int = 0


class ChildActivitySummaryOut(BaseModel):
    child: dict
    conversations_by_module: list[dict]
    messages_by_module: list[dict]
    recent_activity: list[dict]
    token_wallet: dict
    support_summary: dict
    note: str


class CreateSupportRequestIn(BaseModel):
    child_user_id: Optional[int] = None
    subject: str = Field(min_length=1, max_length=180)
    message: str = Field(min_length=1, max_length=4000)
    priority: str = Field(default="normal", max_length=20)


class SupportRequestOut(BaseModel):
    id: int
    parent_user_id: int
    child_user_id: Optional[int] = None
    subject: str
    message: str
    priority: str
    status: str
    created_at: str
    updated_at: str
    child_name: Optional[str] = None
    child_username: Optional[str] = None
    parent_name: Optional[str] = None
    parent_username: Optional[str] = None


class SupportReplyOut(BaseModel):
    id: int
    request_id: int
    author_user_id: int
    message: str
    created_at: str
    author_name: str = ""
    author_username: str = ""


class SupportContactOut(BaseModel):
    id: int
    name: str
    specialty: str
    organization: str = ""
    phone: str = ""
    email: str = ""
    address: str = ""
    notes: str = ""
    is_active: int = 1
    created_at: str = ""
    updated_at: str = ""
    recommendation_note: Optional[str] = None
    recommended_at: Optional[str] = None
    recommended_by_name: Optional[str] = None


class ContactRecommendationOut(BaseModel):
    should_show: bool
    message: str
    contacts: list[SupportContactOut]


# ============================================================
# Helpers de permisos
# ============================================================

def get_current_role(current_user: dict) -> str:
    return normalize_role(
        current_user.get("role"),
        bool(current_user.get("is_admin", False)),
    )


def require_parent_or_superadmin(current_user: dict) -> str:
    role = get_current_role(current_user)

    if role not in {"parent_admin", "guest_parent", "superadmin"}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tu cuenta no tiene permiso para acceder a seguimiento de padres.",
        )

    return role


def ensure_parent_owns_request(current_user: dict, request_id: int) -> dict:
    request = get_support_request_by_id(request_id)

    if not request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Solicitud no encontrada.",
        )

    role = get_current_role(current_user)

    if role == "superadmin":
        return request

    if request["parent_user_id"] != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para ver esta solicitud.",
        )

    return request


# ============================================================
# Contactos recomendados
# ============================================================

def contact_to_out(contact: dict) -> SupportContactOut:
    return SupportContactOut(
        id=contact["id"],
        name=contact.get("name", ""),
        specialty=contact.get("specialty", ""),
        organization=contact.get("organization", ""),
        phone=contact.get("phone", ""),
        email=contact.get("email", ""),
        address=contact.get("address", ""),
        notes=contact.get("notes", ""),
        is_active=int(contact.get("is_active", 1)),
        created_at=contact.get("created_at", ""),
        updated_at=contact.get("updated_at", ""),
        recommendation_note=contact.get("recommendation_note"),
        recommended_at=contact.get("recommended_at"),
        recommended_by_name=contact.get("recommended_by_name"),
    )


@router.get("/contacts", response_model=list[SupportContactOut])
def get_contacts(
    current_user: dict = Depends(get_current_user),
) -> list[SupportContactOut]:
    """
    Lista contactos activos para padres y superadmin.
    """
    require_parent_or_superadmin(current_user)

    contacts = list_support_contacts(active_only=True)
    return [contact_to_out(contact) for contact in contacts]


# ============================================================
# Hijos y resumen
# ============================================================

@router.get("/children", response_model=list[ChildOut])
def get_my_children(
    current_user: dict = Depends(get_current_user),
) -> list[ChildOut]:
    """
    Lista hijos vinculados al padre autenticado.
    """
    role = require_parent_or_superadmin(current_user)

    if role == "superadmin":
        return []

    children = list_children_for_parent(current_user["id"])

    return [
        ChildOut(
            id=child["id"],
            username=child.get("username", ""),
            display_name=child.get("display_name", ""),
            role=child.get("role", ""),
            linked_at=child.get("linked_at", ""),
        )
        for child in children
    ]


@router.get("/children/{child_user_id}/summary", response_model=ChildActivitySummaryOut)
def get_child_summary(
    child_user_id: int,
    current_user: dict = Depends(get_current_user),
) -> ChildActivitySummaryOut:
    """
    Resumen del hijo para el padre.

    No genera diagnóstico. Solo muestra actividad registrada.
    """
    role = require_parent_or_superadmin(current_user)

    try:
        summary = get_child_activity_summary(
            parent_user_id=current_user["id"],
            child_user_id=child_user_id,
            allow_superadmin=(role == "superadmin"),
        )
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(error),
        ) from error

    return ChildActivitySummaryOut(**summary)


# ============================================================
# Solicitudes de apoyo
# ============================================================

@router.get("/requests", response_model=list[SupportRequestOut])
def get_my_support_requests(
    current_user: dict = Depends(get_current_user),
) -> list[SupportRequestOut]:
    """
    Lista solicitudes enviadas por el padre.
    """
    role = require_parent_or_superadmin(current_user)

    if role == "superadmin":
        return []

    requests = list_support_requests_for_parent(current_user["id"])
    return [SupportRequestOut(**request) for request in requests]


@router.post("/requests", response_model=SupportRequestOut)
def create_request(
    payload: CreateSupportRequestIn,
    current_user: dict = Depends(get_current_user),
) -> SupportRequestOut:
    """
    Crea una solicitud del padre al superadmin / psicólogo.
    """
    role = require_parent_or_superadmin(current_user)

    if role == "superadmin":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El superadmin no crea solicitudes como padre desde este endpoint.",
        )

    try:
        request = create_support_request(
            parent_user_id=current_user["id"],
            child_user_id=payload.child_user_id,
            subject=payload.subject,
            message=payload.message,
            priority=payload.priority,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error

    return SupportRequestOut(**request)


@router.get("/requests/{request_id}/replies", response_model=list[SupportReplyOut])
def get_request_replies(
    request_id: int,
    current_user: dict = Depends(get_current_user),
) -> list[SupportReplyOut]:
    """
    Lista respuestas de una solicitud.
    """
    require_parent_or_superadmin(current_user)
    ensure_parent_owns_request(current_user, request_id)

    replies = list_support_replies(request_id)
    return [SupportReplyOut(**reply) for reply in replies]


@router.get("/requests/{request_id}/contacts", response_model=list[SupportContactOut])
def get_request_contacts(
    request_id: int,
    current_user: dict = Depends(get_current_user),
) -> list[SupportContactOut]:
    """
    Lista contactos recomendados dentro de una solicitud.
    """
    require_parent_or_superadmin(current_user)
    ensure_parent_owns_request(current_user, request_id)

    contacts = list_recommended_contacts_for_request(request_id)
    return [contact_to_out(contact) for contact in contacts]


# ============================================================
# Recomendaciones de contacto para chat de Orientación general
# ============================================================

def needs_contact_recommendation(message: str) -> bool:
    text = str(message or "").lower()

    keywords = [
        "contacto",
        "contactos",
        "especialista",
        "especialistas",
        "psicólogo",
        "psicologa",
        "psicóloga",
        "terapeuta",
        "terapia",
        "pediatra",
        "neurólogo",
        "neurologo",
        "clínica",
        "clinica",
        "centro",
        "lugar",
        "lugares",
        "institución",
        "institucion",
        "recomienda",
        "recomiendas",
        "recomendación",
        "recomendacion",
        "dónde",
        "donde",
        "a quién",
        "a quien",
        "apoyo profesional",
        "apoyo especializado",
    ]

    return any(keyword in text for keyword in keywords)


def build_contact_line(contact: dict) -> str:
    parts = [contact.get("name", "Contacto")]

    if contact.get("specialty"):
        parts.append(f"Especialidad: {contact.get('specialty')}")

    if contact.get("organization"):
        parts.append(f"Organización: {contact.get('organization')}")

    if contact.get("phone"):
        parts.append(f"Teléfono: {contact.get('phone')}")

    if contact.get("email"):
        parts.append(f"Correo: {contact.get('email')}")

    if contact.get("address"):
        parts.append(f"Dirección: {contact.get('address')}")

    return "\n".join(parts)


@router.get("/chat-contact-recommendation", response_model=ContactRecommendationOut)
def get_chat_contact_recommendation(
    message: str = Query(default=""),
    current_user: dict = Depends(get_current_user),
) -> ContactRecommendationOut:
    """
    Devuelve una recomendación de contactos para el chat de Modo Padres.

    La app móvil puede llamar esto después de enviar un mensaje en
    Orientación general.
    """
    role = require_parent_or_superadmin(current_user)

    if role not in {"parent_admin", "guest_parent"}:
        return ContactRecommendationOut(
            should_show=False,
            message="",
            contacts=[],
        )

    if not needs_contact_recommendation(message):
        return ContactRecommendationOut(
            should_show=False,
            message="",
            contacts=[],
        )

    contacts = search_support_contacts_by_text(message, limit=3)

    if not contacts:
        return ContactRecommendationOut(
            should_show=True,
            contacts=[],
            message=(
                "También revisé los contactos registrados, pero por ahora no encontré "
                "uno que coincida directamente con lo que mencionas. Como recomendación general, "
                "puedes buscar apoyo con un profesional especializado en desarrollo infantil, "
                "psicología infantil, orientación familiar, pediatría o neurodivergencia.\n\n"
                "Recuerda verificar disponibilidad, costos, horarios y credenciales. "
                "Esta plataforma brinda orientación general y no sustituye atención psicológica, "
                "médica ni terapéutica profesional."
            ),
        )

    contacts_text = "\n\n".join(build_contact_line(contact) for contact in contacts)

    return ContactRecommendationOut(
        should_show=True,
        contacts=[contact_to_out(contact) for contact in contacts],
        message=(
            "También podrías revisar estos contactos registrados en el sistema:\n\n"
            f"{contacts_text}\n\n"
            "Antes de contactar o asistir, verifica disponibilidad, horarios, costos "
            "y credenciales profesionales. Esta recomendación es orientativa y no sustituye "
            "una valoración psicológica, médica ni terapéutica profesional."
        ),
    )

# ============================================================
# Configuración del amigo imaginario del hijo
# ============================================================

def ensure_can_manage_child_friend(
    current_user: dict,
    child_user_id: int,
) -> None:
    role = get_current_role(current_user)

    if role == "superadmin":
        return

    if role in {"parent_admin", "guest_parent"}:
        if parent_can_view_child(current_user["id"], child_user_id):
            return

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="No tienes permiso para configurar el amigo imaginario de este usuario.",
    )


def build_child_friend_profile(child_user_id: int) -> dict:
    user = get_user_by_id(child_user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado.",
        )

    avatar = get_imaginary_friend_profile(child_user_id)

    return {
        "user": {
            "id": user["id"],
            "username": user["username"],
            "display_name": user["display_name"],
            "role": user.get("role", ""),
            "friend_name": user.get("friend_name", "Lumi") or "Lumi",
            "favorite_color": user.get("favorite_color", "") or "",
            "favorite_activity": user.get("favorite_activity", "") or "",
            "encouragement_style": user.get("encouragement_style", "") or "",
            "preferred_comfort": user.get("preferred_comfort", "cuentos") or "cuentos",
        },
        "avatar": {
            "face_shape": avatar.get("face_shape", "redondo") or "redondo",
            "primary_color": avatar.get("primary_color", "azul") or "azul",
            "hair_style": avatar.get("hair_style", "corto") or "corto",
            "hair_color": avatar.get("hair_color", "castano") or "castano",
            "eye_style": avatar.get("eye_style", "felices") or "felices",
            "mouth_style": avatar.get("mouth_style", "sonrisa") or "sonrisa",
            "accessory": avatar.get("accessory", "estrella") or "estrella",
            "background_style": avatar.get("background_style", "cielo") or "cielo",
        },
    }


@router.get("/children/{child_user_id}/friend-profile")
def get_child_friend_profile(
    child_user_id: int,
    current_user: dict = Depends(get_current_user),
) -> dict:
    require_parent_or_superadmin(current_user)
    ensure_can_manage_child_friend(current_user, child_user_id)

    return build_child_friend_profile(child_user_id)


@router.patch("/children/{child_user_id}/friend-preferences")
def update_child_friend_preferences(
    child_user_id: int,
    payload: UpdateFriendPreferencesRequest,
    current_user: dict = Depends(get_current_user),
) -> dict:
    require_parent_or_superadmin(current_user)
    ensure_can_manage_child_friend(current_user, child_user_id)

    try:
        update_friend_name(
            user_id=child_user_id,
            friend_name=payload.friend_name,
        )

        update_friend_profile(
            user_id=child_user_id,
            favorite_color=payload.favorite_color,
            favorite_activity=payload.favorite_activity,
            encouragement_style=payload.encouragement_style,
            preferred_comfort=payload.preferred_comfort,
        )

        return build_child_friend_profile(child_user_id)

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error


@router.patch("/children/{child_user_id}/avatar")
def update_child_avatar(
    child_user_id: int,
    payload: UpdateImaginaryFriendAvatarRequest,
    current_user: dict = Depends(get_current_user),
) -> dict:
    require_parent_or_superadmin(current_user)
    ensure_can_manage_child_friend(current_user, child_user_id)

    update_imaginary_friend_profile(
        user_id=child_user_id,
        face_shape=payload.face_shape,
        primary_color=payload.primary_color,
        hair_style=payload.hair_style,
        hair_color=payload.hair_color,
        eye_style=payload.eye_style,
        mouth_style=payload.mouth_style,
        accessory=payload.accessory,
        background_style=payload.background_style,
    )

    return build_child_friend_profile(child_user_id)