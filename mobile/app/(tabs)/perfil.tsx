import { useEffect, useMemo, useState } from "react";
import {
  Alert,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from "react-native";

import CompanionAvatar from "../../src/components/CompanionAvatar";
import { useAuth } from "../../src/lib/auth";

// ------------------------------------------------------------
// Opciones de apoyo preferido
// ------------------------------------------------------------
const COMFORT_OPTIONS = [
  { key: "cuentos", label: "Cuentos" },
  { key: "juegos", label: "Juegos" },
  { key: "respiraciones", label: "Respiraciones" },
];

// ------------------------------------------------------------
// Sugerencias rápidas de color
// ------------------------------------------------------------
const COLOR_SUGGESTIONS = [
  "azul",
  "rosa",
  "verde",
  "morado",
  "amarillo",
  "naranja",
  "turquesa",
];

// ------------------------------------------------------------
// Opciones del avatar visual
// ------------------------------------------------------------
const AVATAR_OPTIONS = {
  face_shape: ["redondo", "ovalado", "cuadrado"],
  primary_color: ["azul", "rosa", "verde", "morado", "amarillo", "naranja", "turquesa"],
  hair_style: ["corto", "largo", "rizado", "ninguno"],
  hair_color: ["castano", "negro", "rubio", "rosa", "azul", "verde"],
  eye_style: ["felices", "cerraditos", "grandes"],
  mouth_style: ["sonrisa", "curva", "abierta"],
  accessory: ["estrella", "corazon", "luna", "moño", "ninguno"],
  background_style: ["cielo", "nubes", "brillo", "suave"],
};

// ------------------------------------------------------------
// Componente reutilizable de chips para seleccionar opciones
// ------------------------------------------------------------
function OptionSelector({
  title,
  value,
  options,
  onSelect,
}: {
  title: string;
  value: string;
  options: string[];
  onSelect: (value: string) => void;
}) {
  return (
    <View style={styles.selectorBlock}>
      <Text style={styles.inputLabel}>{title}</Text>

      <View style={styles.optionsRow}>
        {options.map((option) => {
          const isActive = value === option;

          return (
            <Pressable
              key={option}
              style={[
                styles.optionChip,
                isActive && styles.optionChipActive,
              ]}
              onPress={() => onSelect(option)}
            >
              <Text
                style={[
                  styles.optionChipText,
                  isActive && styles.optionChipTextActive,
                ]}
              >
                {option}
              </Text>
            </Pressable>
          );
        })}
      </View>
    </View>
  );
}

export default function PerfilScreen() {
  const {
    user,
    avatarProfile,
    signOut,
    updateFriendPreferences,
    updateAvatarProfile,
  } = useAuth();

  const [friendName, setFriendName] = useState("");
  const [favoriteColor, setFavoriteColor] = useState("");
  const [favoriteActivity, setFavoriteActivity] = useState("");
  const [encouragementStyle, setEncouragementStyle] = useState("");
  const [preferredComfort, setPreferredComfort] = useState("cuentos");

  const [faceShape, setFaceShape] = useState("redondo");
  const [primaryColor, setPrimaryColor] = useState("azul");
  const [hairStyle, setHairStyle] = useState("corto");
  const [hairColor, setHairColor] = useState("castano");
  const [eyeStyle, setEyeStyle] = useState("felices");
  const [mouthStyle, setMouthStyle] = useState("sonrisa");
  const [accessory, setAccessory] = useState("estrella");
  const [backgroundStyle, setBackgroundStyle] = useState("cielo");

  const [savingPreferences, setSavingPreferences] = useState(false);
  const [savingAvatar, setSavingAvatar] = useState(false);

  // ----------------------------------------------------------
  // Cargar valores actuales del usuario en el formulario
  // ----------------------------------------------------------
  useEffect(() => {
    if (!user) return;

    setFriendName(user.friend_name || "Lumi");
    setFavoriteColor(user.favorite_color || "");
    setFavoriteActivity(user.favorite_activity || "");
    setEncouragementStyle(user.encouragement_style || "");
    setPreferredComfort(user.preferred_comfort || "cuentos");
  }, [user]);

  // ----------------------------------------------------------
  // Cargar valores actuales del avatar en el formulario
  // ----------------------------------------------------------
  useEffect(() => {
    if (!avatarProfile) return;

    setFaceShape(avatarProfile.face_shape || "redondo");
    setPrimaryColor(avatarProfile.primary_color || "azul");
    setHairStyle(avatarProfile.hair_style || "corto");
    setHairColor(avatarProfile.hair_color || "castano");
    setEyeStyle(avatarProfile.eye_style || "felices");
    setMouthStyle(avatarProfile.mouth_style || "sonrisa");
    setAccessory(avatarProfile.accessory || "estrella");
    setBackgroundStyle(avatarProfile.background_style || "cielo");
  }, [avatarProfile]);

  const profileSummary = useMemo(() => {
    const companion = friendName.trim() || "Lumi";
    const comfortText =
      preferredComfort === "cuentos"
        ? "contar cuentos"
        : preferredComfort === "juegos"
        ? "proponer juegos tranquilos"
        : "hacer respiraciones suaves";

    return `${companion} podrá ${comfortText} y acompañarte de una forma más personal.`;
  }, [friendName, preferredComfort]);

  const previewProfile = useMemo(
    () => ({
      face_shape: faceShape,
      primary_color: primaryColor,
      hair_style: hairStyle,
      hair_color: hairColor,
      eye_style: eyeStyle,
      mouth_style: mouthStyle,
      accessory,
      background_style: backgroundStyle,
    }),
    [
      faceShape,
      primaryColor,
      hairStyle,
      hairColor,
      eyeStyle,
      mouthStyle,
      accessory,
      backgroundStyle,
    ]
  );

  const handleSavePreferences = async () => {
    try {
      setSavingPreferences(true);

      if (!friendName.trim()) {
        Alert.alert("Validación", "Escribe el nombre del amigo imaginario.");
        return;
      }

      await updateFriendPreferences({
        friend_name: friendName,
        favorite_color: favoriteColor,
        favorite_activity: favoriteActivity,
        encouragement_style: encouragementStyle,
        preferred_comfort: preferredComfort,
      });

      Alert.alert("Guardado", "Las preferencias del amigo imaginario se guardaron correctamente.");
    } catch (error: any) {
      Alert.alert("Error", error?.message || "No se pudo guardar la información.");
    } finally {
      setSavingPreferences(false);
    }
  };

  const handleSaveAvatar = async () => {
    try {
      setSavingAvatar(true);

      await updateAvatarProfile({
        face_shape: faceShape,
        primary_color: primaryColor,
        hair_style: hairStyle,
        hair_color: hairColor,
        eye_style: eyeStyle,
        mouth_style: mouthStyle,
        accessory,
        background_style: backgroundStyle,
      });

      Alert.alert("Guardado", "El avatar del amigo imaginario se actualizó correctamente.");
    } catch (error: any) {
      Alert.alert("Error", error?.message || "No se pudo guardar el avatar.");
    } finally {
      setSavingAvatar(false);
    }
  };

  const handleLogout = async () => {
    try {
      await signOut();
    } catch {
      Alert.alert("Error", "No se pudo cerrar la sesión.");
    }
  };

  return (
    <ScrollView style={styles.screen} contentContainerStyle={styles.content}>
      <View style={styles.card}>
        <Text style={styles.title}>Perfil</Text>

        <Text style={styles.fieldLabel}>Nombre visible</Text>
        <Text style={styles.fieldValue}>{user?.display_name || "-"}</Text>

        <Text style={styles.fieldLabel}>Usuario</Text>
        <Text style={styles.fieldValue}>{user?.username || "-"}</Text>

        <Text style={styles.fieldLabel}>Rol</Text>
        <Text style={styles.fieldValue}>
          {user?.is_admin ? "Administrador" : "Usuario"}
        </Text>
      </View>

      {/* Preferencias del amigo */}
      <View style={styles.card}>
        <Text style={styles.sectionTitle}>Mi amigo imaginario</Text>
        <Text style={styles.sectionSubtitle}>
          Personaliza cómo te acompaña desde el celular.
        </Text>

        <Text style={styles.inputLabel}>Nombre del amigo</Text>
        <TextInput
          style={styles.input}
          value={friendName}
          onChangeText={setFriendName}
          placeholder="Ejemplo: Lumi"
        />

        <Text style={styles.inputLabel}>Color favorito</Text>
        <TextInput
          style={styles.input}
          value={favoriteColor}
          onChangeText={setFavoriteColor}
          placeholder="Ejemplo: azul, rosa, verde o un hex"
        />

        <ScrollView
          horizontal
          showsHorizontalScrollIndicator={false}
          style={styles.suggestionsRow}
          contentContainerStyle={styles.suggestionsContent}
        >
          {COLOR_SUGGESTIONS.map((color) => (
            <Pressable
              key={color}
              style={styles.suggestionChip}
              onPress={() => setFavoriteColor(color)}
            >
              <Text style={styles.suggestionChipText}>{color}</Text>
            </Pressable>
          ))}
        </ScrollView>

        <Text style={styles.inputLabel}>Actividad favorita</Text>
        <TextInput
          style={styles.input}
          value={favoriteActivity}
          onChangeText={setFavoriteActivity}
          placeholder="Ejemplo: dibujar, cuentos, rompecabezas"
        />

        <Text style={styles.inputLabel}>Cómo te gusta que te animen</Text>
        <TextInput
          style={[styles.input, styles.multilineInput]}
          value={encouragementStyle}
          onChangeText={setEncouragementStyle}
          placeholder="Ejemplo: con calma, con frases tiernas, con humor suave"
          multiline
        />

        <Text style={styles.inputLabel}>Apoyo preferido</Text>
        <View style={styles.optionsRow}>
          {COMFORT_OPTIONS.map((option) => {
            const isActive = preferredComfort === option.key;

            return (
              <Pressable
                key={option.key}
                style={[
                  styles.optionChip,
                  isActive && styles.optionChipActive,
                ]}
                onPress={() => setPreferredComfort(option.key)}
              >
                <Text
                  style={[
                    styles.optionChipText,
                    isActive && styles.optionChipTextActive,
                  ]}
                >
                  {option.label}
                </Text>
              </Pressable>
            );
          })}
        </View>

        <View style={styles.previewCard}>
          <Text style={styles.previewTitle}>Vista previa</Text>
          <Text style={styles.previewText}>{profileSummary}</Text>
        </View>

        <Pressable
          style={[styles.saveButton, savingPreferences && styles.saveButtonDisabled]}
          onPress={handleSavePreferences}
          disabled={savingPreferences}
        >
          <Text style={styles.saveButtonText}>
            {savingPreferences ? "Guardando..." : "Guardar preferencias"}
          </Text>
        </Pressable>
      </View>

      {/* Apariencia del avatar */}
      <View style={styles.card}>
        <Text style={styles.sectionTitle}>Apariencia del avatar</Text>
        <Text style={styles.sectionSubtitle}>
          Cambia el estilo visual de tu amigo imaginario.
        </Text>

        <View style={styles.avatarPreviewWrapper}>
          <CompanionAvatar
            size={86}
            label={friendName || "Lumi"}
            profile={previewProfile}
          />
          <Text style={styles.avatarPreviewName}>{friendName || "Lumi"}</Text>
        </View>

        <OptionSelector
          title="Forma de rostro"
          value={faceShape}
          options={AVATAR_OPTIONS.face_shape}
          onSelect={setFaceShape}
        />

        <OptionSelector
          title="Color principal"
          value={primaryColor}
          options={AVATAR_OPTIONS.primary_color}
          onSelect={setPrimaryColor}
        />

        <OptionSelector
          title="Cabello"
          value={hairStyle}
          options={AVATAR_OPTIONS.hair_style}
          onSelect={setHairStyle}
        />

        <OptionSelector
          title="Color de cabello"
          value={hairColor}
          options={AVATAR_OPTIONS.hair_color}
          onSelect={setHairColor}
        />

        <OptionSelector
          title="Ojos"
          value={eyeStyle}
          options={AVATAR_OPTIONS.eye_style}
          onSelect={setEyeStyle}
        />

        <OptionSelector
          title="Boca"
          value={mouthStyle}
          options={AVATAR_OPTIONS.mouth_style}
          onSelect={setMouthStyle}
        />

        <OptionSelector
          title="Accesorio"
          value={accessory}
          options={AVATAR_OPTIONS.accessory}
          onSelect={setAccessory}
        />

        <OptionSelector
          title="Fondo"
          value={backgroundStyle}
          options={AVATAR_OPTIONS.background_style}
          onSelect={setBackgroundStyle}
        />

        <Pressable
          style={[styles.saveButton, savingAvatar && styles.saveButtonDisabled]}
          onPress={handleSaveAvatar}
          disabled={savingAvatar}
        >
          <Text style={styles.saveButtonText}>
            {savingAvatar ? "Guardando..." : "Guardar avatar"}
          </Text>
        </Pressable>
      </View>

      <Pressable style={styles.logoutButton} onPress={handleLogout}>
        <Text style={styles.logoutButtonText}>Cerrar sesión</Text>
      </Pressable>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  screen: {
    flex: 1,
    backgroundColor: "#f5f7fb",
  },
  content: {
    padding: 16,
    paddingBottom: 28,
  },
  card: {
    backgroundColor: "#ffffff",
    borderRadius: 18,
    padding: 18,
    marginBottom: 16,
  },
  title: {
    fontSize: 22,
    fontWeight: "800",
    color: "#0f172a",
    marginBottom: 14,
  },
  fieldLabel: {
    fontSize: 13,
    color: "#64748b",
    marginTop: 10,
  },
  fieldValue: {
    fontSize: 16,
    color: "#111827",
    fontWeight: "700",
    marginTop: 4,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: "800",
    color: "#0f172a",
  },
  sectionSubtitle: {
    marginTop: 6,
    color: "#64748b",
    lineHeight: 20,
  },
  inputLabel: {
    marginTop: 14,
    marginBottom: 8,
    color: "#334155",
    fontWeight: "700",
    fontSize: 14,
  },
  input: {
    backgroundColor: "#f8fafc",
    borderRadius: 14,
    paddingHorizontal: 14,
    paddingVertical: 14,
    fontSize: 15,
    color: "#111827",
  },
  multilineInput: {
    minHeight: 84,
    textAlignVertical: "top",
  },
  suggestionsRow: {
    maxHeight: 44,
    marginTop: 10,
  },
  suggestionsContent: {
    gap: 8,
    paddingRight: 8,
  },
  suggestionChip: {
    backgroundColor: "#eaf0fb",
    borderRadius: 999,
    paddingHorizontal: 14,
    paddingVertical: 10,
  },
  suggestionChipText: {
    color: "#2f64b9",
    fontWeight: "700",
    fontSize: 13,
  },
  selectorBlock: {
    marginTop: 6,
  },
  optionsRow: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 10,
    marginTop: 6,
  },
  optionChip: {
    backgroundColor: "#eef2f7",
    paddingHorizontal: 14,
    paddingVertical: 11,
    borderRadius: 999,
  },
  optionChipActive: {
    backgroundColor: "#2f64b9",
  },
  optionChipText: {
    color: "#334155",
    fontWeight: "700",
  },
  optionChipTextActive: {
    color: "#ffffff",
  },
  previewCard: {
    marginTop: 16,
    backgroundColor: "#f8fafc",
    borderRadius: 14,
    padding: 14,
  },
  previewTitle: {
    color: "#0f172a",
    fontWeight: "800",
    marginBottom: 6,
  },
  previewText: {
    color: "#475569",
    lineHeight: 20,
  },
  avatarPreviewWrapper: {
    marginTop: 18,
    alignItems: "center",
    justifyContent: "center",
  },
  avatarPreviewName: {
    marginTop: 10,
    fontWeight: "800",
    color: "#0f172a",
    fontSize: 16,
  },
  saveButton: {
    marginTop: 16,
    backgroundColor: "#2f64b9",
    paddingVertical: 14,
    borderRadius: 14,
    alignItems: "center",
  },
  saveButtonDisabled: {
    opacity: 0.6,
  },
  saveButtonText: {
    color: "#ffffff",
    fontWeight: "800",
    fontSize: 15,
  },
  logoutButton: {
    backgroundColor: "#dc2626",
    paddingVertical: 14,
    borderRadius: 14,
    alignItems: "center",
  },
  logoutButtonText: {
    color: "#ffffff",
    fontWeight: "800",
  },
});