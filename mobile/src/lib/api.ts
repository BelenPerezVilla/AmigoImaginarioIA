// ============================================================
// src/lib/api.ts
// Cliente de API para la app móvil.
// Incluye roles, permisos, guests, tokens y aviso legal.
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
