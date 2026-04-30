// ============================================================
// src/lib/companionTheme.ts
// Utilidades para generar el tema visual del acompañante
// según el color favorito guardado en la app web.
// ============================================================

// ------------------------------------------------------------
// Variantes base del acompañante
// ------------------------------------------------------------
export type AvatarVariant = "lumi" | "guide";

// ------------------------------------------------------------
// Estructura del tema visual generado
// ------------------------------------------------------------
export type CompanionTheme = {
  accent: string;
  accentStrong: string;
  outer: string;
  inner: string;
  eye: string;
  mouth: string;
  softBackground: string;
  chipBackground: string;
  chipBorder: string;
  chipText: string;
  userBubble: string;
  assistantTint: string;
  inputHint: string;
};

// ------------------------------------------------------------
// Convertir nombres comunes de color a hex
// ------------------------------------------------------------
function namedColorToHex(value: string): string | null {
  const color = value.trim().toLowerCase();

  const map: Record<string, string> = {
    azul: "#2f64b9",
    azulcielo: "#4da6ff",
    azulmarino: "#1f3c88",
    celeste: "#65b8ff",
    rosa: "#e86ba3",
    rosado: "#e86ba3",
    lila: "#9b7bff",
    morado: "#7a5cff",
    violeta: "#7a5cff",
    verde: "#2e8b57",
    verdementa: "#55c98f",
    menta: "#55c98f",
    amarillo: "#e6b422",
    naranja: "#ef8c3b",
    rojo: "#d94b4b",
    coral: "#ff7f6e",
    turquesa: "#31b7b7",
    aqua: "#31b7b7",
    gris: "#6b7280",
    grisoscuro: "#4b5563",
    negro: "#222222",
    blanco: "#f3f4f6",
    blue: "#2f64b9",
    pink: "#e86ba3",
    purple: "#7a5cff",
    green: "#2e8b57",
    yellow: "#e6b422",
    orange: "#ef8c3b",
    red: "#d94b4b",
    mint: "#55c98f",
    turquoise: "#31b7b7",
  };

  return map[color] || null;
}

// ------------------------------------------------------------
// Validar si la cadena ya viene como hex
// ------------------------------------------------------------
function normalizeHex(value: string): string | null {
  const raw = value.trim();

  if (/^#[0-9a-fA-F]{6}$/.test(raw)) {
    return raw;
  }

  if (/^[0-9a-fA-F]{6}$/.test(raw)) {
    return `#${raw}`;
  }

  return null;
}

// ------------------------------------------------------------
// Convertir hex a RGB
// ------------------------------------------------------------
function hexToRgb(hex: string) {
  const normalized = hex.replace("#", "");

  return {
    r: parseInt(normalized.slice(0, 2), 16),
    g: parseInt(normalized.slice(2, 4), 16),
    b: parseInt(normalized.slice(4, 6), 16),
  };
}

// ------------------------------------------------------------
// Limitar números entre 0 y 255
// ------------------------------------------------------------
function clamp(value: number) {
  return Math.max(0, Math.min(255, Math.round(value)));
}

// ------------------------------------------------------------
// Convertir RGB a hex
// ------------------------------------------------------------
function rgbToHex(r: number, g: number, b: number) {
  const toHex = (n: number) => clamp(n).toString(16).padStart(2, "0");
  return `#${toHex(r)}${toHex(g)}${toHex(b)}`;
}

// ------------------------------------------------------------
// Aclarar color mezclándolo con blanco
// amount: 0 a 1
// ------------------------------------------------------------
function lighten(hex: string, amount: number) {
  const { r, g, b } = hexToRgb(hex);

  return rgbToHex(
    r + (255 - r) * amount,
    g + (255 - g) * amount,
    b + (255 - b) * amount
  );
}

// ------------------------------------------------------------
// Oscurecer color mezclándolo con negro
// amount: 0 a 1
// ------------------------------------------------------------
function darken(hex: string, amount: number) {
  const { r, g, b } = hexToRgb(hex);

  return rgbToHex(
    r * (1 - amount),
    g * (1 - amount),
    b * (1 - amount)
  );
}

// ------------------------------------------------------------
// Resolver el color base final
// ------------------------------------------------------------
function resolveBaseColor(
  favoriteColor: string | undefined,
  variant: AvatarVariant
): string {
  const fallback = variant === "guide" ? "#2e8b57" : "#2f64b9";

  if (!favoriteColor || !favoriteColor.trim()) {
    return fallback;
  }

  return (
    normalizeHex(favoriteColor) ||
    namedColorToHex(favoriteColor) ||
    fallback
  );
}

// ------------------------------------------------------------
// Construir el tema visual del acompañante
// ------------------------------------------------------------
export function buildCompanionTheme(
  favoriteColor: string | undefined,
  variant: AvatarVariant = "lumi"
): CompanionTheme {
  const accent = resolveBaseColor(favoriteColor, variant);

  return {
    accent,
    accentStrong: darken(accent, 0.14),
    outer: lighten(accent, 0.78),
    inner: lighten(accent, 0.10),
    eye: darken(accent, 0.58),
    mouth: darken(accent, 0.34),
    softBackground: lighten(accent, 0.92),
    chipBackground: lighten(accent, 0.88),
    chipBorder: lighten(accent, 0.72),
    chipText: darken(accent, 0.12),
    userBubble: accent,
    assistantTint: lighten(accent, 0.96),
    inputHint: darken(accent, 0.10),
  };
}

// ------------------------------------------------------------
// Construir un subtítulo personalizado
// según preferencias suaves del usuario.
// ------------------------------------------------------------
export function buildCompanionSubtitle(
  name: string,
  encouragementStyle: string,
  preferredComfort: string
): string {
  const style = (encouragementStyle || "").trim().toLowerCase();
  const comfort = (preferredComfort || "").trim().toLowerCase();

  let stylePart = "te acompaña con calma";
  let comfortPart = "y puede escucharte con cariño";

  if (style.includes("alegre") || style.includes("energ")) {
    stylePart = "te anima con energía suave";
  } else if (style.includes("suave") || style.includes("calma")) {
    stylePart = "te acompaña con voz tranquila";
  } else if (style.includes("cuento")) {
    stylePart = "te habla de forma tierna y creativa";
  }

  if (comfort.includes("cuento")) {
    comfortPart = "y puede contarte cuentos cortitos";
  } else if (comfort.includes("juego")) {
    comfortPart = "y puede proponerte juegos tranquilos";
  } else if (comfort.includes("respira")) {
    comfortPart = "y puede ayudarte con respiraciones suaves";
  } else if (comfort.includes("sorpresa")) {
    comfortPart = "y puede sorprenderte con ideas bonitas";
  }

  return `${name} ${stylePart} ${comfortPart}.`;
}

// ------------------------------------------------------------
// Generar ejemplos rápidos personalizados
// ------------------------------------------------------------
export function buildPersonalizedExamples(
  baseExamples: string[],
  preferredComfort: string,
  favoriteActivity: string,
  companionName: string
): string[] {
  const result = [...baseExamples];
  const comfort = (preferredComfort || "").trim().toLowerCase();
  const activity = (favoriteActivity || "").trim().toLowerCase();

  // Insertar sugerencia según confort preferido
  if (comfort.includes("cuento")) {
    result.unshift(`Cuéntame un cuento, ${companionName}`);
  } else if (comfort.includes("juego")) {
    result.unshift(`Quiero jugar contigo, ${companionName}`);
  } else if (comfort.includes("respira")) {
    result.unshift(`Haz una respiración conmigo, ${companionName}`);
  } else if (comfort.includes("sorpresa")) {
    result.unshift(`Dame una sorpresa bonita, ${companionName}`);
  }

  // Insertar sugerencia usando actividad favorita
  if (activity) {
    result.push(`¿Jugamos algo sobre ${activity}?`);
  }

  // Quitar duplicados y limitar tamaño
  return Array.from(new Set(result)).slice(0, 6);
}