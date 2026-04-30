// ============================================================
// src/lib/api.ts
// Cliente de API para la app móvil.
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
  timeoutMs: number = 12000
): Promise<Response> {
  // Crear controlador para cancelar la petición
  const controller = new AbortController();

  // Programar timeout
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
      12000
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
    // Error por timeout
    if (error?.name === "AbortError") {
      throw new Error(
        "La petición tardó demasiado. Revisa que el backend esté encendido y que la IP sea correcta."
      );
    }

    // Error de red típico en React Native
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

// ------------------------------------------------------------
// Iniciar sesión
// ------------------------------------------------------------
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

// ------------------------------------------------------------
// Registrar usuario
// ------------------------------------------------------------
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

// ------------------------------------------------------------
// Obtener usuario autenticado actual
// ------------------------------------------------------------
export async function getCurrentUser(token: string): Promise<AppUser> {
  return apiRequest<AppUser>(
    "/api/auth/me",
    {
      method: "GET",
    },
    token
  );
}

// ------------------------------------------------------------
// Actualizar preferencias del amigo imaginario
// ------------------------------------------------------------
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
// CONVERSACIONES
// ============================================================

// ------------------------------------------------------------
// Listar conversaciones por módulo
// ------------------------------------------------------------
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

// ------------------------------------------------------------
// Crear conversación nueva para un módulo
// ------------------------------------------------------------
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

// ------------------------------------------------------------
// Obtener mensajes de una conversación
// ------------------------------------------------------------
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

// ------------------------------------------------------------
// Enviar mensaje a una conversación
// ------------------------------------------------------------
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

// ------------------------------------------------------------
// Listar artículos de biblioteca
// ------------------------------------------------------------
export async function listArticles(
  token: string,
  search: string = ""
): Promise<Article[]> {
  const query = new URLSearchParams({
    search,
    category: "Todas",
    reader_type: "Todos",
  });

  return apiRequest<Article[]>(
    `/api/library/articles?${query.toString()}`,
    {
      method: "GET",
    },
    token
  );
}

// ------------------------------------------------------------
// Obtener detalle de artículo
// ------------------------------------------------------------
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