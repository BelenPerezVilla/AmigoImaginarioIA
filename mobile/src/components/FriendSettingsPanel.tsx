import { useEffect, useMemo, useState } from "react";
import {
  ActivityIndicator,
  Alert,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from "react-native";

import {
  type ChildFriendProfile,
  getChildFriendProfileRequest,
  updateChildAvatarProfileRequest,
  updateChildFriendPreferencesRequest,
} from "../lib/api";
import { useAuth } from "../lib/auth";
import CompanionAvatar from "./CompanionAvatar";

const COMFORT_OPTIONS = [
  { key: "cuentos", label: "Cuentos" },
  { key: "juegos", label: "Juegos tranquilos" },
  { key: "respiraciones", label: "Respiraciones" },
];

const COLOR_OPTIONS = ["azul", "rosa", "verde", "morado", "amarillo", "naranja"];

const AVATAR_OPTIONS = {
  face_shape: ["redondo", "ovalado", "suave"],
  primary_color: ["azul", "rosa", "verde", "morado", "amarillo", "naranja"],
  hair_style: ["corto", "largo", "rizado", "sin cabello"],
  hair_color: ["castano", "negro", "rubio", "rosa", "azul"],
  eye_style: ["felices", "tranquilos", "curiosos"],
  mouth_style: ["sonrisa", "suave", "neutral"],
  accessory: ["estrella", "lentes", "gorrito", "ninguno"],
  background_style: ["cielo", "bosque", "estrellas", "arcoiris"],
};

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
    <View style={styles.optionBlock}>
      <Text style={styles.inputLabel}>{title}</Text>

      <View style={styles.optionsRow}>
        {options.map((option) => {
          const active = value === option;

          return (
            <Pressable
              key={option}
              style={[styles.optionChip, active && styles.optionChipActive]}
              onPress={() => onSelect(option)}
            >
              <Text
                style={[
                  styles.optionChipText,
                  active && styles.optionChipTextActive,
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

export default function FriendSettingsPanel({
  targetUserId,
  targetName,
}: {
  targetUserId?: number | null;
  targetName?: string;
}) {
  const {
    token,
    user,
    avatarProfile,
    updateFriendPreferences,
    updateAvatarProfile,
  } = useAuth();

  const [loading, setLoading] = useState(Boolean(targetUserId));
  const [profile, setProfile] = useState<ChildFriendProfile | null>(null);

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

  const loadTargetProfile = async () => {
    if (!token || !targetUserId) return;

    try {
      setLoading(true);

      const data = await getChildFriendProfileRequest(token, targetUserId);
      setProfile(data);

      setFriendName(data.user.friend_name || "Lumi");
      setFavoriteColor(data.user.favorite_color || "");
      setFavoriteActivity(data.user.favorite_activity || "");
      setEncouragementStyle(data.user.encouragement_style || "");
      setPreferredComfort(data.user.preferred_comfort || "cuentos");

      setFaceShape(data.avatar.face_shape || "redondo");
      setPrimaryColor(data.avatar.primary_color || "azul");
      setHairStyle(data.avatar.hair_style || "corto");
      setHairColor(data.avatar.hair_color || "castano");
      setEyeStyle(data.avatar.eye_style || "felices");
      setMouthStyle(data.avatar.mouth_style || "sonrisa");
      setAccessory(data.avatar.accessory || "estrella");
      setBackgroundStyle(data.avatar.background_style || "cielo");
    } catch (error: any) {
      Alert.alert("Error", error?.message || "No se pudo cargar el perfil.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (targetUserId) {
      loadTargetProfile();
      return;
    }

    setFriendName(user?.friend_name || "Lumi");
    setFavoriteColor(user?.favorite_color || "");
    setFavoriteActivity(user?.favorite_activity || "");
    setEncouragementStyle(user?.encouragement_style || "");
    setPreferredComfort(user?.preferred_comfort || "cuentos");

    setFaceShape(avatarProfile.face_shape || "redondo");
    setPrimaryColor(avatarProfile.primary_color || "azul");
    setHairStyle(avatarProfile.hair_style || "corto");
    setHairColor(avatarProfile.hair_color || "castano");
    setEyeStyle(avatarProfile.eye_style || "felices");
    setMouthStyle(avatarProfile.mouth_style || "sonrisa");
    setAccessory(avatarProfile.accessory || "estrella");
    setBackgroundStyle(avatarProfile.background_style || "cielo");
  }, [targetUserId, token, user, avatarProfile]);

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

  const profileOwnerName =
    profile?.user.display_name || targetName || user?.display_name || "usuario";

  const handleSavePreferences = async () => {
    if (!token) return;

    if (!friendName.trim()) {
      Alert.alert("Validación", "Escribe el nombre del amigo imaginario.");
      return;
    }

    try {
      setSavingPreferences(true);

      const payload = {
        friend_name: friendName,
        favorite_color: favoriteColor,
        favorite_activity: favoriteActivity,
        encouragement_style: encouragementStyle,
        preferred_comfort: preferredComfort,
      };

      if (targetUserId) {
        await updateChildFriendPreferencesRequest(token, targetUserId, payload);
        await loadTargetProfile();
      } else {
        await updateFriendPreferences(payload);
      }

      Alert.alert("Guardado", "Preferencias guardadas correctamente.");
    } catch (error: any) {
      Alert.alert("Error", error?.message || "No se pudo guardar.");
    } finally {
      setSavingPreferences(false);
    }
  };

  const handleSaveAvatar = async () => {
    if (!token) return;

    try {
      setSavingAvatar(true);

      const payload = {
        face_shape: faceShape,
        primary_color: primaryColor,
        hair_style: hairStyle,
        hair_color: hairColor,
        eye_style: eyeStyle,
        mouth_style: mouthStyle,
        accessory,
        background_style: backgroundStyle,
      };

      if (targetUserId) {
        await updateChildAvatarProfileRequest(token, targetUserId, payload);
        await loadTargetProfile();
      } else {
        await updateAvatarProfile(payload);
      }

      Alert.alert("Guardado", "Avatar guardado correctamente.");
    } catch (error: any) {
      Alert.alert("Error", error?.message || "No se pudo guardar el avatar.");
    } finally {
      setSavingAvatar(false);
    }
  };

  if (loading) {
    return (
      <View style={styles.centered}>
        <ActivityIndicator size="large" color="#2f64b9" />
        <Text style={styles.centerText}>Cargando configuración...</Text>
      </View>
    );
  }

  return (
    <ScrollView style={styles.screen} contentContainerStyle={styles.content}>
      <View style={styles.card}>
        <Text style={styles.title}>Configurar amigo imaginario</Text>
        <Text style={styles.subtitle}>
          Estás configurando el amigo imaginario de {profileOwnerName}.
        </Text>

        <View style={styles.avatarPreview}>
          <CompanionAvatar
            size={86}
            label={friendName || "Lumi"}
            profile={previewProfile}
          />
          <Text style={styles.avatarName}>{friendName || "Lumi"}</Text>
        </View>
      </View>

      <View style={styles.card}>
        <Text style={styles.sectionTitle}>Personalidad y apoyo</Text>

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
          placeholder="Ejemplo: azul"
        />

        <View style={styles.optionsRow}>
          {COLOR_OPTIONS.map((color) => (
            <Pressable
              key={color}
              style={styles.optionChip}
              onPress={() => setFavoriteColor(color)}
            >
              <Text style={styles.optionChipText}>{color}</Text>
            </Pressable>
          ))}
        </View>

        <Text style={styles.inputLabel}>Actividad favorita</Text>
        <TextInput
          style={styles.input}
          value={favoriteActivity}
          onChangeText={setFavoriteActivity}
          placeholder="Ejemplo: dibujar, cuentos, rompecabezas"
        />

        <Text style={styles.inputLabel}>Cómo debe animarlo</Text>
        <TextInput
          style={[styles.input, styles.multilineInput]}
          value={encouragementStyle}
          onChangeText={setEncouragementStyle}
          placeholder="Ejemplo: con calma, con frases tiernas..."
          multiline
        />

        <Text style={styles.inputLabel}>Apoyo preferido</Text>
        <View style={styles.optionsRow}>
          {COMFORT_OPTIONS.map((option) => {
            const active = preferredComfort === option.key;

            return (
              <Pressable
                key={option.key}
                style={[styles.optionChip, active && styles.optionChipActive]}
                onPress={() => setPreferredComfort(option.key)}
              >
                <Text
                  style={[
                    styles.optionChipText,
                    active && styles.optionChipTextActive,
                  ]}
                >
                  {option.label}
                </Text>
              </Pressable>
            );
          })}
        </View>

        <Pressable
          style={[styles.primaryButton, savingPreferences && styles.disabled]}
          onPress={handleSavePreferences}
          disabled={savingPreferences}
        >
          <Text style={styles.primaryButtonText}>
            {savingPreferences ? "Guardando..." : "Guardar preferencias"}
          </Text>
        </Pressable>
      </View>

      <View style={styles.card}>
        <Text style={styles.sectionTitle}>Apariencia del avatar</Text>

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
          style={[styles.primaryButton, savingAvatar && styles.disabled]}
          onPress={handleSaveAvatar}
          disabled={savingAvatar}
        >
          <Text style={styles.primaryButtonText}>
            {savingAvatar ? "Guardando..." : "Guardar avatar"}
          </Text>
        </Pressable>
      </View>
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
    paddingBottom: 30,
  },
  centered: {
    flex: 1,
    backgroundColor: "#f5f7fb",
    justifyContent: "center",
    alignItems: "center",
    padding: 22,
  },
  centerText: {
    color: "#64748b",
    marginTop: 8,
  },
  card: {
    backgroundColor: "#ffffff",
    borderRadius: 18,
    padding: 16,
    marginBottom: 12,
  },
  title: {
    color: "#0f172a",
    fontSize: 22,
    fontWeight: "900",
  },
  subtitle: {
    color: "#64748b",
    marginTop: 6,
    lineHeight: 20,
  },
  sectionTitle: {
    color: "#0f172a",
    fontSize: 18,
    fontWeight: "900",
    marginBottom: 10,
  },
  avatarPreview: {
    alignItems: "center",
    marginTop: 16,
  },
  avatarName: {
    color: "#0f172a",
    fontWeight: "900",
    marginTop: 8,
  },
  inputLabel: {
    color: "#334155",
    fontWeight: "800",
    marginTop: 12,
    marginBottom: 6,
  },
  input: {
    backgroundColor: "#f8fafc",
    borderRadius: 14,
    paddingHorizontal: 14,
    paddingVertical: 13,
    color: "#0f172a",
  },
  multilineInput: {
    minHeight: 90,
    textAlignVertical: "top",
  },
  optionsRow: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 8,
    marginTop: 8,
  },
  optionBlock: {
    marginBottom: 8,
  },
  optionChip: {
    backgroundColor: "#e9eef8",
    borderRadius: 999,
    paddingHorizontal: 12,
    paddingVertical: 9,
  },
  optionChipActive: {
    backgroundColor: "#2f64b9",
  },
  optionChipText: {
    color: "#334155",
    fontWeight: "800",
    fontSize: 12,
  },
  optionChipTextActive: {
    color: "#ffffff",
  },
  primaryButton: {
    backgroundColor: "#2f64b9",
    borderRadius: 14,
    paddingVertical: 14,
    alignItems: "center",
    marginTop: 16,
  },
  primaryButtonText: {
    color: "#ffffff",
    fontWeight: "900",
  },
  disabled: {
    opacity: 0.55,
  },
});