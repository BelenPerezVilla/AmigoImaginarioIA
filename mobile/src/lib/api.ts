// ============================================================
// src/lib/api.ts
// Cliente de API para la app móvil.
// Incluye roles, permisos, guests, tokens, aviso legal,
// biblioteca, conversaciones y soporte para Modo Padres.
// ============================================================

import { Platform } from "react-native";

// ------------------------------------------------------------
// IP local real de tu computadora.
// Cambia este valor si cambia tu red.
// ------------------------------------------------------------
const DEV_MACHINE_IP = "172.16.1.107";

// ------------------------------------------------------------
// URL base del backend.
// En celular físico no uses localhost.
// ------------------------------------------------------------
export const API_BASE_URL =
  Platform.OS === "web"
    ? "http://localhost:8000"
    : `http://${DEV_MACHINE_IP}:8000`;

// ------------------------------------------------------------
// Timeout general para Gemini y FastAPI.
// ------------------------------------------------------------
const API_TIMEOUT_MS = 60000;

// ------------------------------------------------------------
// Tipos de tokens
// ------------------------------------------------------------
export type TokenStatus = {
  daily_limit: number;
  remaining_tokens: number;
  used_tokens: number;
  low_threshold: number;
  reset_interval_hours: number;
  last_reset_at: string;
  next_reset_at: string;
  is_low: boolean;
  is_empty: boolean;
  is_unlimited: boolean;
  message: string;
  reset_text: string;
};

// ------------------------------------------------------------
// Tipos de permisos
// ------------------------------------------------------------
export type UserPermissions = {
  can_access_amigo: boolean;
  can_access_biblioteca: boolean;
  can_access_modo_padres: boolean;
  can_access_admin: boolean;

  can_manage_users: boolean;
  can_manage_guests: boolean;
  can_manage_library: boolean;

  can_customize_child_friend: boolean;
  can_view_tokens: boolean;

  // Campos opcionales por compatibilidad con permisos nuevos
  can_view_library?: boolean;
  can_chat_with_friend?: boolean;
};

// ------------------------------------------------------------
// Tipos base
// ------------------------------------------------------------
export type AppUser = {
  id: number;
  username: string;
  display_name: string;
  is_admin: boolean;

  friend_name: string;
  favorite_color: string;
  favorite_activity: string;
  encouragement_style: string;
  preferred_comfort: string;

  role: string;
  role_label: string;
  account_type: string;
  guest_type: string;
  guest_status: string;
  guest_hours: number;
  guest_expires_at: string;
  is_active: boolean;

  permissions: UserPermissions;
  allowed_modules: string[];
  token_status?: TokenStatus | null;
};

export type ImaginaryFriendAvatar = {
  face_shape: string;
  primary_color: string;
  hair_style: string;
  hair_color: string;
  eye_style: string;
  mouth_style: string;
  accessory: string;
  background_style: string;
};

export type AuthResponse = {
  access_token: string;
  token_type: string;
  user: AppUser;
};

export type Conversation = {
  id: number;
  user_id: number;
  module: string;
  title: string;
  created_at: string;
  updated_at: string;
};

export type Message = {
  id: number;
  role: "user" | "assistant";
  content: string;
  created_at: string;
};

export type SendMessageResponse = {
  user_message: Message;
  assistant_message: Message;
  token_status?: TokenStatus | null;
};

export type Article = {
  id: number;
  title: string;
  category: string;
  reader_type: string;
  short_description: string;
  content: string;
  created_at: string;
};

export type UpdateFriendPreferencesPayload = {
  friend_name: string;
  favorite_color: string;
  favorite_activity: string;
  encouragement_style: string;
  preferred_comfort: string;
};

export type UpdateAvatarPayload = {
  face_shape: string;
  primary_color: string;
  hair_style: string;
  hair_color: string;
  eye_style: string;
  mouth_style: string;
  accessory: string;
  background_style: string;
};

export type FavoriteStateResponse = {
  article_id: number;
  is_favorite: boolean;
};

export type SendArticleToChatResponse = {
  conversation_id: number;
  module: string;
  title: string;
};

export type LegalNoticeResponse = {
  text: string;
  version: string;
};

// ============================================================
// TIPOS: SOPORTE / MODO PADRES
// ============================================================

export type SupportChild = {
  id: number;
  username: string;
  display_name: string;
  role: string;
  linked_at: string;
};

export type ChildActivitySummary = {
  child: {
    id: number;
    username: string;
    display_name: string;
    role?: string;
  };
  conversations_by_module: Array<{
    module: string;
    total_conversations: number;
    last_activity: string;
  }>;
  messages_by_module: Array<{
    module: string;
    total_messages: number;
    user_messages: number;
    assistant_messages: number;
  }>;
  recent_activity: Array<{
    id: number;
    module: string;
    title: string;
    updated_at: string;
    total_messages: number;
  }>;
  token_wallet: {
    daily_limit?: number;
    remaining_tokens?: number;
    used_tokens?: number;
    low_threshold?: number;
    last_reset_at?: string;
    next_reset_at?: string;
  };
  support_summary: {
    total_requests?: number;
    open_requests?: number;
    in_review_requests?: number;
    closed_requests?: number;
  };
  note: string;
};

export type SupportRequest = {
  id: number;
  parent_user_id: number;
  child_user_id?: number | null;
  subject: string;
  message: string;
  priority: string;
  status: string;
  created_at: string;
  updated_at: string;
  child_name?: string | null;
  child_username?: string | null;
  parent_name?: string | null;
  parent_username?: string | null;
};

export type SupportReply = {
  id: number;
  request_id: number;
  author_user_id: number;
  message: string;
  created_at: string;
  author_name: string;
  author_username: string;
};

export type SupportContact = {
  id: number;
  name: string;
  specialty: string;
  organization: string;
  phone: string;
  email: string;
  address: string;
  notes: string;
  is_active: number;
  created_at?: string;
  updated_at?: string;
  recommendation_note?: string | null;
  recommended_at?: string | null;
  recommended_by_name?: string | null;
};

export type ChatContactRecommendation = {
  should_show: boolean;
  message: string;
  contacts: SupportContact[];
};

// ------------------------------------------------------------
// Construir headers para peticiones
// ------------------------------------------------------------
function buildHeaders(token?: string, isJson: boolean = true): HeadersInit {
  const headers: Record<string, string> = {};

  if (isJson) {
    headers["Content-Type"] = "application/json";
  }

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  return headers;
}

// ------------------------------------------------------------
// Fetch con timeout para evitar bloqueos largos
// ------------------------------------------------------------
async function fetchWithTimeout(
  url: string,
  options: RequestInit,
  timeoutMs: number = API_TIMEOUT_MS
): Promise<Response> {
  const controller = new AbortController();

  const timeoutId = setTimeout(() => {
    controller.abort();
  }, timeoutMs);

  try {
    const response = await fetch(url, {
      ...options,
      signal: controller.signal,
    });

    return response;
  } finally {
    clearTimeout(timeoutId);
  }
}

// ------------------------------------------------------------
// Consumidor general de API con manejo de errores
// ------------------------------------------------------------
async function apiRequest<T>(
  path: string,
  options: RequestInit = {},
  token?: string
): Promise<T> {
  const url = `${API_BASE_URL}${path}`;

  try {
    const response = await fetchWithTimeout(
      url,
      {
        ...options,
        headers: {
          ...buildHeaders(token, options.body !== undefined),
          ...(options.headers || {}),
        },
      },
      API_TIMEOUT_MS
    );

    let data: any = null;

    try {
      data = await response.json();
    } catch {
      data = null;
    }

    if (!response.ok) {
      const detail =
        data?.detail ||
        data?.message ||
        `Error del servidor (${response.status}).`;

      throw new Error(
        Array.isArray(detail) ? JSON.stringify(detail) : String(detail)
      );
    }

    return data as T;
  } catch (error: any) {
    if (error?.name === "AbortError") {
      throw new Error(
        "La petición tardó demasiado. Revisa que el backend esté encendido, que Gemini responda y que la IP sea correcta."
      );
    }

    if (
      String(error?.message || "").includes("Network request failed") ||
      String(error?.message || "").includes("fetch")
    ) {
      throw new Error(
        `No se pudo conectar con el backend en ${API_BASE_URL}. Revisa la IP, el puerto 8000 y que tu celular esté en la misma red.`
      );
    }

    throw error;
  }
}

// ============================================================
// AUTENTICACIÓN
// ============================================================

export async function loginRequest(
  username: string,
  password: string
): Promise<AuthResponse> {
  return apiRequest<AuthResponse>("/api/auth/login", {
    method: "POST",
    body: JSON.stringify({
      username: username.trim(),
      password,
    }),
  });
}

export async function registerRequest(
  displayName: string,
  username: string,
  password: string
): Promise<AuthResponse> {
  return apiRequest<AuthResponse>("/api/auth/register", {
    method: "POST",
    body: JSON.stringify({
      display_name: displayName.trim(),
      username: username.trim(),
      password,
    }),
  });
}

export async function getCurrentUser(token: string): Promise<AppUser> {
  return apiRequest<AppUser>(
    "/api/auth/me",
    {
      method: "GET",
    },
    token
  );
}

export async function getLegalNoticeRequest(): Promise<LegalNoticeResponse> {
  return apiRequest<LegalNoticeResponse>("/api/auth/legal-notice", {
    method: "GET",
  });
}

export async function updateFriendPreferencesRequest(
  token: string,
  payload: UpdateFriendPreferencesPayload
): Promise<AppUser> {
  return apiRequest<AppUser>(
    "/api/auth/me/preferences",
    {
      method: "PATCH",
      body: JSON.stringify({
        friend_name: payload.friend_name.trim(),
        favorite_color: payload.favorite_color.trim(),
        favorite_activity: payload.favorite_activity.trim(),
        encouragement_style: payload.encouragement_style.trim(),
        preferred_comfort: payload.preferred_comfort.trim().toLowerCase(),
      }),
    },
    token
  );
}

// ============================================================
// TOKENS
// ============================================================

export async function getMyTokenStatusRequest(
  token: string
): Promise<TokenStatus> {
  return apiRequest<TokenStatus>(
    "/api/tokens/me",
    {
      method: "GET",
    },
    token
  );
}

// ============================================================
// AVATAR DEL AMIGO IMAGINARIO
// ============================================================

export async function getAvatarProfileRequest(
  token: string
): Promise<ImaginaryFriendAvatar> {
  return apiRequest<ImaginaryFriendAvatar>(
    "/api/auth/me/avatar",
    {
      method: "GET",
    },
    token
  );
}

export async function updateAvatarProfileRequest(
  token: string,
  payload: UpdateAvatarPayload
): Promise<ImaginaryFriendAvatar> {
  return apiRequest<ImaginaryFriendAvatar>(
    "/api/auth/me/avatar",
    {
      method: "PATCH",
      body: JSON.stringify({
        face_shape: payload.face_shape.trim(),
        primary_color: payload.primary_color.trim(),
        hair_style: payload.hair_style.trim(),
        hair_color: payload.hair_color.trim(),
        eye_style: payload.eye_style.trim(),
        mouth_style: payload.mouth_style.trim(),
        accessory: payload.accessory.trim(),
        background_style: payload.background_style.trim(),
      }),
    },
    token
  );
}

// ============================================================
// CONVERSACIONES
// ============================================================

export async function listConversations(
  module: string,
  token: string
): Promise<Conversation[]> {
  return apiRequest<Conversation[]>(
    `/api/chats/${module}`,
    {
      method: "GET",
    },
    token
  );
}

export async function createConversationRequest(
  module: string,
  token: string
): Promise<Conversation> {
  return apiRequest<Conversation>(
    `/api/chats/${module}`,
    {
      method: "POST",
    },
    token
  );
}

export async function getConversationMessages(
  conversationId: number,
  token: string
): Promise<Message[]> {
  return apiRequest<Message[]>(
    `/api/chats/conversations/${conversationId}`,
    {
      method: "GET",
    },
    token
  );
}

export async function sendMessageRequest(
  conversationId: number,
  content: string,
  token: string
): Promise<SendMessageResponse> {
  return apiRequest<SendMessageResponse>(
    `/api/chats/conversations/${conversationId}/messages`,
    {
      method: "POST",
      body: JSON.stringify({ content }),
    },
    token
  );
}

// ============================================================
// BIBLIOTECA
// ============================================================

export async function listArticles(
  token: string,
  search: string = "",
  category: string = "Todas",
  readerType: string = "Todos"
): Promise<Article[]> {
  const query = new URLSearchParams({
    search,
    category,
    reader_type: readerType,
  });

  return apiRequest<Article[]>(
    `/api/library/articles?${query.toString()}`,
    {
      method: "GET",
    },
    token
  );
}

export async function getArticleById(
  token: string,
  articleId: number
): Promise<Article> {
  return apiRequest<Article>(
    `/api/library/articles/${articleId}`,
    {
      method: "GET",
    },
    token
  );
}

export async function listFavoriteArticles(
  token: string
): Promise<Article[]> {
  return apiRequest<Article[]>(
    "/api/library/favorites",
    {
      method: "GET",
    },
    token
  );
}

export async function addFavoriteArticleRequest(
  token: string,
  articleId: number
): Promise<FavoriteStateResponse> {
  return apiRequest<FavoriteStateResponse>(
    `/api/library/favorites/${articleId}`,
    {
      method: "POST",
    },
    token
  );
}

export async function removeFavoriteArticleRequest(
  token: string,
  articleId: number
): Promise<FavoriteStateResponse> {
  return apiRequest<FavoriteStateResponse>(
    `/api/library/favorites/${articleId}`,
    {
      method: "DELETE",
    },
    token
  );
}

export async function sendArticleToChatRequest(
  token: string,
  articleId: number
): Promise<SendArticleToChatResponse> {
  return apiRequest<SendArticleToChatResponse>(
    `/api/library/articles/${articleId}/send-to-chat`,
    {
      method: "POST",
    },
    token
  );
}

// ============================================================
// SOPORTE / MODO PADRES
// ============================================================

export async function getSupportChildrenRequest(
  token: string
): Promise<SupportChild[]> {
  return apiRequest<SupportChild[]>(
    "/api/support/children",
    {
      method: "GET",
    },
    token
  );
}

export async function getChildActivitySummaryRequest(
  token: string,
  childUserId: number
): Promise<ChildActivitySummary> {
  return apiRequest<ChildActivitySummary>(
    `/api/support/children/${childUserId}/summary`,
    {
      method: "GET",
    },
    token
  );
}

export async function getSupportContactsRequest(
  token: string
): Promise<SupportContact[]> {
  return apiRequest<SupportContact[]>(
    "/api/support/contacts",
    {
      method: "GET",
    },
    token
  );
}

export async function getSupportRequestsRequest(
  token: string
): Promise<SupportRequest[]> {
  return apiRequest<SupportRequest[]>(
    "/api/support/requests",
    {
      method: "GET",
    },
    token
  );
}

export async function createSupportRequestRequest(
  token: string,
  payload: {
    child_user_id?: number | null;
    subject: string;
    message: string;
    priority: string;
  }
): Promise<SupportRequest> {
  return apiRequest<SupportRequest>(
    "/api/support/requests",
    {
      method: "POST",
      body: JSON.stringify({
        child_user_id: payload.child_user_id ?? null,
        subject: payload.subject.trim(),
        message: payload.message.trim(),
        priority: payload.priority,
      }),
    },
    token
  );
}

export async function getSupportRequestRepliesRequest(
  token: string,
  requestId: number
): Promise<SupportReply[]> {
  return apiRequest<SupportReply[]>(
    `/api/support/requests/${requestId}/replies`,
    {
      method: "GET",
    },
    token
  );
}

export async function getSupportRequestContactsRequest(
  token: string,
  requestId: number
): Promise<SupportContact[]> {
  return apiRequest<SupportContact[]>(
    `/api/support/requests/${requestId}/contacts`,
    {
      method: "GET",
    },
    token
  );
}

export async function getChatContactRecommendationRequest(
  token: string,
  message: string
): Promise<ChatContactRecommendation> {
  const query = new URLSearchParams({
    message,
  });

  return apiRequest<ChatContactRecommendation>(
    `/api/support/chat-contact-recommendation?${query.toString()}`,
    {
      method: "GET",
    },
    token
  );
}

// ============================================================
// ADMIN / SUPERADMIN
// ============================================================

export type AdminUser = AppUser & {
  token_status?: TokenStatus | null;
};

export type AdminGuestPayload = {
  username: string;
  password: string;
  display_name: string;
  guest_type: "guest_child" | "guest_parent";
  hours: number;
  token_limit: number;
};

export async function adminListUsersRequest(
  token: string
): Promise<AdminUser[]> {
  return apiRequest<AdminUser[]>(
    "/api/admin/users",
    {
      method: "GET",
    },
    token
  );
}

export async function adminUpdateUserRoleRequest(
  token: string,
  userId: number,
  role: string
): Promise<AdminUser> {
  return apiRequest<AdminUser>(
    `/api/admin/users/${userId}/role`,
    {
      method: "PATCH",
      body: JSON.stringify({ role }),
    },
    token
  );
}

export async function adminUpdateUserTokensRequest(
  token: string,
  userId: number,
  payload: {
    daily_limit: number;
    reset_interval_hours: number;
    low_threshold: number;
  }
): Promise<TokenStatus> {
  return apiRequest<TokenStatus>(
    `/api/admin/users/${userId}/tokens`,
    {
      method: "PATCH",
      body: JSON.stringify(payload),
    },
    token
  );
}

export async function adminListGuestsRequest(
  token: string
): Promise<AdminUser[]> {
  return apiRequest<AdminUser[]>(
    "/api/admin/guests",
    {
      method: "GET",
    },
    token
  );
}

export async function adminCreateGuestRequest(
  token: string,
  payload: AdminGuestPayload
): Promise<AdminUser> {
  return apiRequest<AdminUser>(
    "/api/admin/guests",
    {
      method: "POST",
      body: JSON.stringify(payload),
    },
    token
  );
}

export async function adminExtendGuestRequest(
  token: string,
  userId: number,
  extraHours: number
): Promise<AdminUser> {
  return apiRequest<AdminUser>(
    `/api/admin/guests/${userId}/extend`,
    {
      method: "PATCH",
      body: JSON.stringify({
        extra_hours: extraHours,
      }),
    },
    token
  );
}

export async function adminDeactivateGuestRequest(
  token: string,
  userId: number
): Promise<AdminUser> {
  return apiRequest<AdminUser>(
    `/api/admin/guests/${userId}/deactivate`,
    {
      method: "PATCH",
      body: JSON.stringify({}),
    },
    token
  );
}

// ============================================================
// CONFIGURACIÓN DEL AMIGO DE HIJOS / MODO PADRES
// ============================================================

export type ChildFriendProfile = {
  user: {
    id: number;
    username: string;
    display_name: string;
    role: string;
    friend_name: string;
    favorite_color: string;
    favorite_activity: string;
    encouragement_style: string;
    preferred_comfort: string;
  };
  avatar: ImaginaryFriendAvatar;
};

export async function getChildFriendProfileRequest(
  token: string,
  childUserId: number
): Promise<ChildFriendProfile> {
  return apiRequest<ChildFriendProfile>(
    `/api/support/children/${childUserId}/friend-profile`,
    {
      method: "GET",
    },
    token
  );
}

export async function updateChildFriendPreferencesRequest(
  token: string,
  childUserId: number,
  payload: UpdateFriendPreferencesPayload
): Promise<ChildFriendProfile> {
  return apiRequest<ChildFriendProfile>(
    `/api/support/children/${childUserId}/friend-preferences`,
    {
      method: "PATCH",
      body: JSON.stringify({
        friend_name: payload.friend_name.trim(),
        favorite_color: payload.favorite_color.trim(),
        favorite_activity: payload.favorite_activity.trim(),
        encouragement_style: payload.encouragement_style.trim(),
        preferred_comfort: payload.preferred_comfort.trim().toLowerCase(),
      }),
    },
    token
  );
}

export async function updateChildAvatarProfileRequest(
  token: string,
  childUserId: number,
  payload: UpdateAvatarPayload
): Promise<ChildFriendProfile> {
  return apiRequest<ChildFriendProfile>(
    `/api/support/children/${childUserId}/avatar`,
    {
      method: "PATCH",
      body: JSON.stringify({
        face_shape: payload.face_shape.trim(),
        primary_color: payload.primary_color.trim(),
        hair_style: payload.hair_style.trim(),
        hair_color: payload.hair_color.trim(),
        eye_style: payload.eye_style.trim(),
        mouth_style: payload.mouth_style.trim(),
        accessory: payload.accessory.trim(),
        background_style: payload.background_style.trim(),
      }),
    },
    token
  );
}

// ============================================================
// ADMIN / APOYO A PADRES / CONTACTOS
// ============================================================

export async function adminListSupportRequestsRequest(
  token: string,
  statusFilter: string = "Todas"
): Promise<SupportRequest[]> {
  const query = new URLSearchParams({
    status_filter: statusFilter,
  });

  return apiRequest<SupportRequest[]>(
    `/api/admin/support-requests?${query.toString()}`,
    {
      method: "GET",
    },
    token
  );
}

export async function adminListSupportRepliesRequest(
  token: string,
  requestId: number
): Promise<SupportReply[]> {
  return apiRequest<SupportReply[]>(
    `/api/admin/support-requests/${requestId}/replies`,
    {
      method: "GET",
    },
    token
  );
}

export async function adminAddSupportReplyRequest(
  token: string,
  requestId: number,
  payload: {
    message: string;
    new_status: string;
  }
): Promise<SupportReply> {
  return apiRequest<SupportReply>(
    `/api/admin/support-requests/${requestId}/reply`,
    {
      method: "POST",
      body: JSON.stringify({
        message: payload.message.trim(),
        new_status: payload.new_status,
      }),
    },
    token
  );
}

export async function adminUpdateSupportStatusRequest(
  token: string,
  requestId: number,
  status: string
): Promise<SupportRequest> {
  return apiRequest<SupportRequest>(
    `/api/admin/support-requests/${requestId}/status`,
    {
      method: "PATCH",
      body: JSON.stringify({
        status,
      }),
    },
    token
  );
}

export async function adminListRequestContactsRequest(
  token: string,
  requestId: number
): Promise<SupportContact[]> {
  return apiRequest<SupportContact[]>(
    `/api/admin/support-requests/${requestId}/contacts`,
    {
      method: "GET",
    },
    token
  );
}

export async function adminRecommendContactRequest(
  token: string,
  requestId: number,
  contactId: number,
  note: string
): Promise<SupportContact> {
  return apiRequest<SupportContact>(
    `/api/admin/support-requests/${requestId}/contacts/${contactId}/recommend`,
    {
      method: "POST",
      body: JSON.stringify({
        note: note.trim(),
      }),
    },
    token
  );
}

export async function adminListSupportContactsRequest(
  token: string
): Promise<SupportContact[]> {
  return apiRequest<SupportContact[]>(
    "/api/admin/support-contacts",
    {
      method: "GET",
    },
    token
  );
}

export async function adminCreateSupportContactRequest(
  token: string,
  payload: {
    name: string;
    specialty: string;
    organization: string;
    phone: string;
    email: string;
    address: string;
    notes: string;
  }
): Promise<SupportContact> {
  return apiRequest<SupportContact>(
    "/api/admin/support-contacts",
    {
      method: "POST",
      body: JSON.stringify({
        name: payload.name.trim(),
        specialty: payload.specialty.trim(),
        organization: payload.organization.trim(),
        phone: payload.phone.trim(),
        email: payload.email.trim(),
        address: payload.address.trim(),
        notes: payload.notes.trim(),
      }),
    },
    token
  );
}

export async function adminDeactivateSupportContactRequest(
  token: string,
  contactId: number
): Promise<SupportContact> {
  return apiRequest<SupportContact>(
    `/api/admin/support-contacts/${contactId}/deactivate`,
    {
      method: "PATCH",
      body: JSON.stringify({}),
    },
    token
  );
}