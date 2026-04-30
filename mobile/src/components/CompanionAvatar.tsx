// ============================================================
// src/components/CompanionAvatar.tsx
// Avatar visual del acompañante.
// Usa el tema dinámico construido desde companionTheme.ts
// ============================================================

import { StyleSheet, Text, View } from "react-native";
import type { AvatarVariant, CompanionTheme } from "../lib/companionTheme";

// ------------------------------------------------------------
// Props del avatar
// ------------------------------------------------------------
type CompanionAvatarProps = {
  size?: number;
  variant?: AvatarVariant;
  label?: string;
  showBadge?: boolean;
  theme: CompanionTheme;
};

// ------------------------------------------------------------
// Avatar principal
// ------------------------------------------------------------
export default function CompanionAvatar({
  size = 58,
  variant = "lumi",
  label = "L",
  showBadge = true,
  theme,
}: CompanionAvatarProps) {
  // ----------------------------------------------------------
  // Medidas internas relativas al tamaño
  // ----------------------------------------------------------
  const outerSize = size;
  const innerSize = size * 0.78;
  const eyeSize = Math.max(4, size * 0.08);
  const badgeSize = Math.max(16, size * 0.26);

  // ----------------------------------------------------------
  // Badge según la variante del acompañante
  // ----------------------------------------------------------
  const badgeSymbol = variant === "guide" ? "★" : "☁";

  return (
    <View
      style={[
        styles.outerCircle,
        {
          width: outerSize,
          height: outerSize,
          borderRadius: outerSize / 2,
          backgroundColor: theme.outer,
          borderColor: theme.accentStrong,
        },
      ]}
    >
      {/* Cabecita principal */}
      <View
        style={[
          styles.innerCircle,
          {
            width: innerSize,
            height: innerSize,
            borderRadius: innerSize / 2,
            backgroundColor: theme.inner,
          },
        ]}
      >
        {/* Ojos */}
        <View style={styles.eyesRow}>
          <View
            style={[
              styles.eye,
              {
                width: eyeSize,
                height: eyeSize,
                borderRadius: eyeSize / 2,
                backgroundColor: theme.eye,
              },
            ]}
          />
          <View
            style={[
              styles.eye,
              {
                width: eyeSize,
                height: eyeSize,
                borderRadius: eyeSize / 2,
                backgroundColor: theme.eye,
              },
            ]}
          />
        </View>

        {/* Sonrisa */}
        <View
          style={[
            styles.mouth,
            {
              borderColor: theme.mouth,
              width: innerSize * 0.24,
              height: innerSize * 0.12,
              borderBottomWidth: 2.5,
              borderRadius: innerSize * 0.12,
            },
          ]}
        />

        {/* Letra decorativa */}
        <Text
          style={[
            styles.avatarLetter,
            {
              color: "#ffffffcc",
              fontSize: size * 0.22,
            },
          ]}
        >
          {label.slice(0, 1).toUpperCase()}
        </Text>
      </View>

      {/* Badge */}
      {showBadge && (
        <View
          style={[
            styles.badge,
            {
              width: badgeSize,
              height: badgeSize,
              borderRadius: badgeSize / 2,
              backgroundColor: "#ffffff",
              borderColor: theme.accentStrong,
            },
          ]}
        >
          <Text
            style={{
              fontSize: badgeSize * 0.52,
              color: theme.accentStrong,
              lineHeight: badgeSize * 0.62,
            }}
          >
            {badgeSymbol}
          </Text>
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  outerCircle: {
    justifyContent: "center",
    alignItems: "center",
    borderWidth: 2,
    position: "relative",
  },

  innerCircle: {
    justifyContent: "center",
    alignItems: "center",
    position: "relative",
  },

  eyesRow: {
    flexDirection: "row",
    gap: 8,
    marginBottom: 6,
  },

  eye: {},

  mouth: {
    borderTopWidth: 0,
    borderLeftWidth: 0,
    borderRightWidth: 0,
    marginTop: 2,
  },

  avatarLetter: {
    position: "absolute",
    bottom: 8,
    right: 10,
    fontWeight: "800",
  },

  badge: {
    position: "absolute",
    right: -4,
    bottom: -2,
    justifyContent: "center",
    alignItems: "center",
    borderWidth: 1.5,
  },
});