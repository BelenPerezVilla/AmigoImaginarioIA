# ============================================================
# utils/avatar_svg.py
# Utilidades para construir un avatar SVG simple y tierno
# para el amigo imaginario.
# ============================================================

# ------------------------------------------------------------
# Opciones visuales disponibles para el avatar
# ------------------------------------------------------------
AVATAR_FORM_OPTIONS = {
    "face_shape": ["redondo", "ovalado", "nube"],
    "primary_color": ["azul", "rosa", "morado", "verde", "amarillo"],
    "hair_style": ["ninguno", "corto", "fleco", "rizado"],
    "hair_color": ["castano", "negro", "rubio", "rosa", "azul"],
    "eye_style": ["felices", "grandes", "dormidos"],
    "mouth_style": ["sonrisa", "sorpresa", "tierna"],
    "accessory": ["ninguno", "estrella", "moño", "corona", "lentes"],
    "background_style": ["cielo", "estrellas", "corazones"],
}

# ------------------------------------------------------------
# Configuración por defecto del avatar
# ------------------------------------------------------------
DEFAULT_FRIEND_AVATAR = {
    "face_shape": "redondo",
    "primary_color": "azul",
    "hair_style": "corto",
    "hair_color": "castano",
    "eye_style": "felices",
    "mouth_style": "sonrisa",
    "accessory": "estrella",
    "background_style": "cielo",
}


# ------------------------------------------------------------
# Paletas de colores
# ------------------------------------------------------------
PRIMARY_COLORS = {
    "azul": "#5AA9FF",
    "rosa": "#FF8BC2",
    "morado": "#A77BFF",
    "verde": "#66CC99",
    "amarillo": "#FFD766",
}

HAIR_COLORS = {
    "castano": "#7B4B2A",
    "negro": "#2C2C2C",
    "rubio": "#E6C24F",
    "rosa": "#F48FB1",
    "azul": "#5C8DFF",
}


# ------------------------------------------------------------
# Escapar texto simple para SVG/HTML
# ------------------------------------------------------------
def escape_text(value: str) -> str:
    """
    Escapa caracteres básicos para evitar que rompan el SVG.

    Parámetros:
        value (str): texto a escapar

    Retorna:
        str: texto seguro
    """
    return (
        str(value or "")
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .strip()
    )


# ------------------------------------------------------------
# Obtener valor del perfil con fallback
# ------------------------------------------------------------
def get_profile_value(profile: dict, key: str, fallback: str) -> str:
    """
    Obtiene un valor del perfil, o usa el fallback.

    Parámetros:
        profile (dict): perfil del avatar
        key (str): campo a leer
        fallback (str): valor por defecto

    Retorna:
        str: valor final
    """
    value = str(profile.get(key, fallback) or fallback).strip()
    return value if value else fallback


# ------------------------------------------------------------
# Construir fondo del avatar
# ------------------------------------------------------------
def build_background_svg(style: str) -> str:
    """
    Devuelve elementos SVG decorativos para el fondo.

    Parámetros:
        style (str): estilo visual del fondo

    Retorna:
        str: fragmento SVG
    """
    if style == "estrellas":
        return """
        <circle cx="50" cy="45" r="4" fill="#FFFFFF" opacity="0.9"/>
        <circle cx="200" cy="60" r="3" fill="#FFFFFF" opacity="0.8"/>
        <circle cx="80" cy="210" r="3" fill="#FFFFFF" opacity="0.9"/>
        <circle cx="210" cy="190" r="4" fill="#FFFFFF" opacity="0.8"/>
        <path d="M120 35 L124 45 L135 46 L127 53 L130 64 L120 58 L110 64 L113 53 L105 46 L116 45 Z"
              fill="#FFF7C2" opacity="0.9"/>
        """

    if style == "corazones":
        return """
        <path d="M55 55 C55 45, 70 42, 75 52 C80 42, 95 45, 95 55 C95 70, 75 82, 75 82 C75 82, 55 70, 55 55 Z"
              fill="#FFD1E6" opacity="0.8"/>
        <path d="M185 65 C185 57, 197 55, 201 62 C205 55, 217 57, 217 65 C217 77, 201 86, 201 86 C201 86, 185 77, 185 65 Z"
              fill="#FFD1E6" opacity="0.75"/>
        <path d="M200 205 C200 197, 212 195, 216 202 C220 195, 232 197, 232 205 C232 217, 216 226, 216 226 C216 226, 200 217, 200 205 Z"
              fill="#FFD1E6" opacity="0.7"/>
        """

    # Fondo cielo por defecto
    return """
    <circle cx="55" cy="55" r="18" fill="#FFFFFF" opacity="0.85"/>
    <circle cx="70" cy="50" r="14" fill="#FFFFFF" opacity="0.85"/>
    <circle cx="85" cy="57" r="16" fill="#FFFFFF" opacity="0.85"/>
    <circle cx="195" cy="55" r="10" fill="#FFFFFF" opacity="0.75"/>
    <circle cx="207" cy="50" r="8" fill="#FFFFFF" opacity="0.75"/>
    <circle cx="216" cy="56" r="9" fill="#FFFFFF" opacity="0.75"/>
    """


# ------------------------------------------------------------
# Construir rostro
# ------------------------------------------------------------
def build_face_svg(face_shape: str) -> str:
    """
    Devuelve la forma base del rostro.

    Parámetros:
        face_shape (str): redondo, ovalado o nube

    Retorna:
        str: fragmento SVG
    """
    if face_shape == "ovalado":
        return """
        <ellipse cx="140" cy="120" rx="48" ry="56" fill="#F9E3CE" />
        """

    if face_shape == "nube":
        return """
        <circle cx="115" cy="120" r="28" fill="#F9E3CE" />
        <circle cx="140" cy="104" r="34" fill="#F9E3CE" />
        <circle cx="168" cy="120" r="28" fill="#F9E3CE" />
        <ellipse cx="140" cy="132" rx="48" ry="28" fill="#F9E3CE" />
        """

    # redondo por defecto
    return """
    <circle cx="140" cy="120" r="50" fill="#F9E3CE" />
    """


# ------------------------------------------------------------
# Construir cabello
# ------------------------------------------------------------
def build_hair_svg(hair_style: str, hair_color: str) -> str:
    """
    Devuelve el cabello del avatar.

    Parámetros:
        hair_style (str): estilo del cabello
        hair_color (str): color del cabello

    Retorna:
        str: fragmento SVG
    """
    color = HAIR_COLORS.get(hair_color, HAIR_COLORS["castano"])

    if hair_style == "ninguno":
        return ""

    if hair_style == "fleco":
        return f"""
        <path d="M92 108 C95 70, 185 70, 188 108
                 C173 96, 165 92, 154 107
                 C145 92, 135 92, 126 108
                 C117 94, 107 95, 92 108 Z"
              fill="{color}" />
        """

    if hair_style == "rizado":
        return f"""
        <circle cx="100" cy="94" r="14" fill="{color}" />
        <circle cx="118" cy="82" r="14" fill="{color}" />
        <circle cx="140" cy="78" r="15" fill="{color}" />
        <circle cx="162" cy="82" r="14" fill="{color}" />
        <circle cx="180" cy="94" r="14" fill="{color}" />
        <circle cx="90" cy="110" r="10" fill="{color}" />
        <circle cx="190" cy="110" r="10" fill="{color}" />
        """

    # corto por defecto
    return f"""
    <path d="M92 108 C95 70, 185 70, 188 108
             C180 92, 165 84, 140 84
             C115 84, 100 92, 92 108 Z"
          fill="{color}" />
    """


# ------------------------------------------------------------
# Construir ojos
# ------------------------------------------------------------
def build_eyes_svg(eye_style: str) -> str:
    """
    Devuelve los ojos del avatar.

    Parámetros:
        eye_style (str): felices, grandes o dormidos

    Retorna:
        str: fragmento SVG
    """
    if eye_style == "grandes":
        return """
        <circle cx="122" cy="120" r="6.5" fill="#2B2B2B" />
        <circle cx="158" cy="120" r="6.5" fill="#2B2B2B" />
        <circle cx="124" cy="118" r="2" fill="#FFFFFF" />
        <circle cx="160" cy="118" r="2" fill="#FFFFFF" />
        """

    if eye_style == "dormidos":
        return """
        <path d="M114 121 Q122 117 130 121" stroke="#2B2B2B" stroke-width="3" fill="none" stroke-linecap="round"/>
        <path d="M150 121 Q158 117 166 121" stroke="#2B2B2B" stroke-width="3" fill="none" stroke-linecap="round"/>
        """

    # felices por defecto
    return """
    <path d="M114 120 Q122 128 130 120" stroke="#2B2B2B" stroke-width="3" fill="none" stroke-linecap="round"/>
    <path d="M150 120 Q158 128 166 120" stroke="#2B2B2B" stroke-width="3" fill="none" stroke-linecap="round"/>
    """


# ------------------------------------------------------------
# Construir boca
# ------------------------------------------------------------
def build_mouth_svg(mouth_style: str) -> str:
    """
    Devuelve la boca del avatar.

    Parámetros:
        mouth_style (str): sonrisa, sorpresa o tierna

    Retorna:
        str: fragmento SVG
    """
    if mouth_style == "sorpresa":
        return """
        <ellipse cx="140" cy="147" rx="6" ry="9" fill="#F28AAE" />
        """

    if mouth_style == "tierna":
        return """
        <path d="M129 145 Q140 152 151 145" stroke="#C45A7A" stroke-width="3" fill="none" stroke-linecap="round"/>
        """

    # sonrisa por defecto
    return """
    <path d="M126 143 Q140 156 154 143" stroke="#C45A7A" stroke-width="3" fill="none" stroke-linecap="round"/>
    """


# ------------------------------------------------------------
# Construir accesorio
# ------------------------------------------------------------
def build_accessory_svg(accessory: str, primary_color: str) -> str:
    """
    Devuelve el accesorio del avatar.

    Parámetros:
        accessory (str): tipo de accesorio
        primary_color (str): color principal

    Retorna:
        str: fragmento SVG
    """
    color = PRIMARY_COLORS.get(primary_color, PRIMARY_COLORS["azul"])

    if accessory == "ninguno":
        return ""

    if accessory == "moño":
        return f"""
        <circle cx="185" cy="92" r="8" fill="{color}" />
        <ellipse cx="176" cy="92" rx="10" ry="7" fill="{color}" />
        <ellipse cx="194" cy="92" rx="10" ry="7" fill="{color}" />
        """

    if accessory == "corona":
        return f"""
        <path d="M118 70 L128 88 L140 70 L152 88 L162 70 L166 92 L114 92 Z"
              fill="#FFD766" stroke="#E2B93F" stroke-width="2"/>
        """

    if accessory == "lentes":
        return """
        <circle cx="122" cy="121" r="11" stroke="#4A4A4A" stroke-width="3" fill="none"/>
        <circle cx="158" cy="121" r="11" stroke="#4A4A4A" stroke-width="3" fill="none"/>
        <line x1="133" y1="121" x2="147" y2="121" stroke="#4A4A4A" stroke-width="3"/>
        """

    # estrella por defecto
    return f"""
    <path d="M188 88 L191 96 L199 97 L193 102 L195 110 L188 106 L181 110 L183 102 L177 97 L185 96 Z"
          fill="#FFD766" />
    """


# ------------------------------------------------------------
# Construir cuerpo del avatar
# ------------------------------------------------------------
def build_body_svg(primary_color: str) -> str:
    """
    Devuelve el cuerpo simple del avatar.

    Parámetros:
        primary_color (str): color principal del amigo

    Retorna:
        str: fragmento SVG
    """
    color = PRIMARY_COLORS.get(primary_color, PRIMARY_COLORS["azul"])

    return f"""
    <path d="M95 205 C100 175, 180 175, 185 205 L185 240 L95 240 Z"
          fill="{color}" />
    <circle cx="105" cy="215" r="6" fill="#FFFFFF" opacity="0.45"/>
    <circle cx="118" cy="223" r="4" fill="#FFFFFF" opacity="0.35"/>
    """


# ------------------------------------------------------------
# Construir SVG completo del avatar
# ------------------------------------------------------------
def build_friend_avatar_svg(friend_name: str, avatar_profile: dict, size: int = 260) -> str:
    """
    Construye un SVG completo del amigo imaginario.

    Parámetros:
        friend_name (str): nombre del amigo
        avatar_profile (dict): configuración visual del avatar
        size (int): tamaño de render

    Retorna:
        str: SVG listo para mostrar en Streamlit
    """
    profile = {**DEFAULT_FRIEND_AVATAR, **(avatar_profile or {})}

    face_shape = get_profile_value(profile, "face_shape", DEFAULT_FRIEND_AVATAR["face_shape"])
    primary_color = get_profile_value(profile, "primary_color", DEFAULT_FRIEND_AVATAR["primary_color"])
    hair_style = get_profile_value(profile, "hair_style", DEFAULT_FRIEND_AVATAR["hair_style"])
    hair_color = get_profile_value(profile, "hair_color", DEFAULT_FRIEND_AVATAR["hair_color"])
    eye_style = get_profile_value(profile, "eye_style", DEFAULT_FRIEND_AVATAR["eye_style"])
    mouth_style = get_profile_value(profile, "mouth_style", DEFAULT_FRIEND_AVATAR["mouth_style"])
    accessory = get_profile_value(profile, "accessory", DEFAULT_FRIEND_AVATAR["accessory"])
    background_style = get_profile_value(profile, "background_style", DEFAULT_FRIEND_AVATAR["background_style"])

    safe_name = escape_text(friend_name or "Lumi")
    background_color = PRIMARY_COLORS.get(primary_color, PRIMARY_COLORS["azul"])

    svg = f"""
    <svg width="{size}" height="{size + 50}" viewBox="0 0 280 320" xmlns="http://www.w3.org/2000/svg">
        <defs>
            <linearGradient id="bgGrad" x1="0" x2="1" y1="0" y2="1">
                <stop offset="0%" stop-color="{background_color}" stop-opacity="0.28"/>
                <stop offset="100%" stop-color="#FFFFFF" stop-opacity="0.18"/>
            </linearGradient>
            <filter id="softShadow" x="-20%" y="-20%" width="140%" height="140%">
                <feDropShadow dx="0" dy="6" stdDeviation="6" flood-color="#000000" flood-opacity="0.18"/>
            </filter>
        </defs>

        <rect x="20" y="20" rx="28" ry="28" width="240" height="240" fill="url(#bgGrad)" />

        {build_background_svg(background_style)}

        <g filter="url(#softShadow)">
            {build_body_svg(primary_color)}
            {build_face_svg(face_shape)}
            {build_hair_svg(hair_style, hair_color)}
            {build_eyes_svg(eye_style)}
            {build_mouth_svg(mouth_style)}
            {build_accessory_svg(accessory, primary_color)}
        </g>

        <text x="140" y="292" text-anchor="middle"
              style="font-size:20px; font-weight:700; fill:#1F2937; font-family:Arial, sans-serif;">
            {safe_name}
        </text>
    </svg>
    """

    return svg.strip()