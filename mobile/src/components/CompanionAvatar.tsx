// ============================================================
// src/components/CompanionAvatar.tsx
// Avatar visual del acompañante configurable desde móvil.
// ============================================================

import { StyleSheet, Text, View } from "react-native";
import type { ImaginaryFriendAvatar } from "../lib/api";

// ------------------------------------------------------------
// Props del componente
// ------------------------------------------------------------
type CompanionAvatarProps = {
  size?: number;
  label?: string;
  showBadge?: boolean;
  profile: ImaginaryFriendAvatar;
};

// ------------------------------------------------------------
// Resolver color visual por nombre común
// ------------------------------------------------------------
function colorValue(name: string): string {
  const value = String(name || "").trim().toLowerCase();

  const map: Record<string, string> = {
    azul: "#4f8ef7",
    rosa: "#ef7bb3",
    verde: "#49b97f",
    morado: "#8d6cf7",
    amarillo: "#f1c84b",
    naranja: "#f19a4b",
    turquesa: "#35b8b8",
    negro: "#2d2d2d",
    blanco: "#f5f7fb",
    castano: "#7b4b2a",
    castaño: "#7b4b2a",
    rubio: "#e2c26d",
    rojo: "#d95c5c",
    cielo: "#dcecff",
  };

  return map[value] || "#4f8ef7";
}

// ------------------------------------------------------------
// Avatar principal
// ------------------------------------------------------------
export default function CompanionAvatar({
  size = 60,
  label = "L",
  showBadge = true,
  profile,
}: CompanionAvatarProps) {
  const primaryColor = colorValue(profile.primary_color);
  const hairColor = colorValue(profile.hair_color);

  const backgroundColor =
    profile.background_style === "nubes"
      ? "#eef6ff"
      : profile.background_style === "brillo"
      ? "#fff7d8"
      : profile.background_style === "suave"
      ? "#f2edff"
      : "#e8f2ff";

  const faceRadius =
    profile.face_shape === "ovalado"
      ? size * 0.28
      : profile.face_shape === "cuadrado"
      ? 14
      : size * 0.32;

  const eyeMode = profile.eye_style;
  const mouthMode = profile.mouth_style;
  const accessoryMode = profile.accessory;
  const hairMode = profile.hair_style;

  const outerSize = size;
  const faceWidth = size * 0.66;
  const faceHeight =
    profile.face_shape === "ovalado" ? size * 0.78 : size * 0.66;

  const badgeSymbol =
    accessoryMode === "corazon"
      ? "♥"
      : accessoryMode === "moño"
      ? "⌯"
      : accessoryMode === "luna"
      ? "☾"
      : accessoryMode === "ninguno"
      ? ""
      : "★";

  return (
    <View
      style={[
        styles.outer,
        {
          width: outerSize,
          height: outerSize,
          borderRadius: outerSize / 2,
          backgroundColor,
          borderColor: primaryColor,
        },
      ]}
    >
      {/* Cabello */}
      {hairMode !== "ninguno" && (
        <View
          style={[
            styles.hairBase,
            hairMode === "largo" && styles.hairLong,
            hairMode === "rizado" && styles.hairCurly,
            {
              backgroundColor: hairColor,
              width: faceWidth * 0.9,
            },
          ]}
        />
      )}

      {/* Rostro */}
      <View
        style={[
          styles.face,
          {
            width: faceWidth,
            height: faceHeight,
            borderRadius: faceRadius,
            backgroundColor: primaryColor,
          },
        ]}
      >
        {/* Ojos */}
        <View style={styles.eyesRow}>
          {eyeMode === "cerraditos" ? (
            <>
              <View style={styles.closedEye} />
              <View style={styles.closedEye} />
            </>
          ) : eyeMode === "grandes" ? (
            <>
              <View style={styles.bigEye} />
              <View style={styles.bigEye} />
            </>
          ) : (
            <>
              <View style={styles.eye} />
              <View style={styles.eye} />
            </>
          )}
        </View>

        {/* Boca */}
        {mouthMode === "abierta" ? (
          <View style={styles.openMouth} />
        ) : mouthMode === "curva" ? (
          <View style={styles.softMouth} />
        ) : (
          <View style={styles.smile} />
        )}

        {/* Letra decorativa */}
        <Text
          style={[
            styles.letter,
            {
              fontSize: size * 0.18,
            },
          ]}
        >
          {label.slice(0, 1).toUpperCase()}
        </Text>
      </View>

      {/* Badge accesorio */}
      {showBadge && accessoryMode !== "ninguno" && (
        <View
          style={[
            styles.badge,
            {
              width: size * 0.24,
              height: size * 0.24,
              borderRadius: size * 0.12,
              borderColor: primaryColor,
            },
          ]}
        >
          <Text
            style={[
              styles.badgeText,
              {
                color: primaryColor,
                fontSize: size * 0.13,
              },
            ]}
          >
            {badgeSymbol}
          </Text>
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  outer: {
    justifyContent: "center",
    alignItems: "center",
    borderWidth: 2,
    position: "relative",
    overflow: "hidden",
  },

  hairBase: {
    position: "absolute",
    top: 10,
    height: 16,
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
  },

  hairLong: {
    height: 24,
  },

  hairCurly: {
    height: 20,
    borderRadius: 20,
  },

  face: {
    justifyContent: "center",
    alignItems: "center",
    position: "relative",
  },

  eyesRow: {
    flexDirection: "row",
    gap: 10,
    marginBottom: 6,
  },

  eye: {
    width: 5,
    height: 5,
    borderRadius: 999,
    backgroundColor: "#17325e",
  },

  bigEye: {
    width: 8,
    height: 8,
    borderRadius: 999,
    backgroundColor: "#17325e",
  },

  closedEye: {
    width: 8,
    height: 2,
    borderRadius: 999,
    backgroundColor: "#17325e",
    marginTop: 3,
  },

  smile: {
    width: 14,
    height: 7,
    borderBottomWidth: 2.5,
    borderColor: "#1b4a8a",
    borderRadius: 20,
  },

  softMouth: {
    width: 12,
    height: 4,
    borderBottomWidth: 2,
    borderColor: "#1b4a8a",
    borderRadius: 20,
  },

  openMouth: {
    width: 10,
    height: 8,
    borderRadius: 6,
    backgroundColor: "#1b4a8a",
  },

  letter: {
    position: "absolute",
    bottom: 5,
    right: 8,
    color: "#ffffffcc",
    fontWeight: "800",
  },

  badge: {
    position: "absolute",
    right: 2,
    bottom: 2,
    backgroundColor: "#ffffff",
    justifyContent: "center",
    alignItems: "center",
    borderWidth: 1.4,
  },

  badgeText: {
    fontWeight: "800",
  },
});