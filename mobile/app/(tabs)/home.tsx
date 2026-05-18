// ============================================================
// mobile/app/(tabs)/home.tsx
// Inicio móvil con identidad visual AbrazoIA y permisos por rol.
// ============================================================

import React from "react";
import {
  Image,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { useRouter } from "expo-router";

import { useAuth } from "../../src/lib/auth";
import { BRAND, BRAND_LOGO } from "../../src/lib/brand";
import {
  canSeeAdmin,
  canSeeAmigo,
  canSeeBiblioteca,
  canSeePadres,
  isChild,
  isParent,
  isSuperadmin,
  roleLabel,
} from "../../src/lib/roleAccess";

type HomeCardProps = {
  title: string;
  text: string;
  icon: keyof typeof Ionicons.glyphMap;
  onPress: () => void;
  accent?: "coral" | "lilac" | "sky" | "purple";
};

function HomeCard({
  title,
  text,
  icon,
  onPress,
  accent = "sky",
}: HomeCardProps) {
  const accentColor =
    accent === "coral"
      ? BRAND.colors.coralDark
      : accent === "lilac"
      ? BRAND.colors.lilac
      : accent === "purple"
      ? BRAND.colors.purple
      : BRAND.colors.skyDark;

  return (
    <Pressable style={styles.card} onPress={onPress}>
      <View style={[styles.cardIcon, { backgroundColor: `${accentColor}22` }]}>
        <Ionicons name={icon} size={22} color={accentColor} />
      </View>

      <View style={styles.cardTextBlock}>
        <Text style={styles.cardTitle}>{title}</Text>
        <Text style={styles.cardText}>{text}</Text>
      </View>

      <Ionicons name="chevron-forward" size={20} color="#94a3b8" />
    </Pressable>
  );
}

export default function HomeScreen() {
  const router = useRouter();
  const { user } = useAuth();

  const subtitle = isChild(user)
    ? "Tu espacio está listo para conversar con tu amigo imaginario."
    : isParent(user)
    ? "Puedes revisar seguimiento, orientación y configurar el amigo del niño."
    : isSuperadmin(user)
    ? "Tienes acceso completo a los módulos y administración."
    : "Aquí tienes acceso rápido a tus módulos principales.";

  return (
    <ScrollView style={styles.screen} contentContainerStyle={styles.content}>
      <View style={styles.heroCard}>
        <View style={styles.brandRow}>
          <Image source={BRAND_LOGO} style={styles.logo} resizeMode="contain" />

          <View style={styles.brandTextBlock}>
            <Text style={styles.brandName}>{BRAND.name}</Text>
            <Text style={styles.brandTagline}>{BRAND.tagline}</Text>
          </View>
        </View>

        <View style={styles.heroDivider} />

        <Text style={styles.heroTitle}>
          Hola, {user?.display_name || "bienvenido"}
        </Text>
        <Text style={styles.heroSubtitle}>{subtitle}</Text>
        <Text style={styles.roleBadge}>{roleLabel(user)}</Text>
      </View>

      {canSeeAmigo(user) && (
        <HomeCard
          title="Amigo Imaginario"
          text={
            isParent(user)
              ? "Configura el amigo imaginario del niño vinculado."
              : "Conversa con tu acompañante emocional."
          }
          icon="chatbubble-ellipses"
          accent="coral"
          onPress={() => router.push("/(tabs)/amigo")}
        />
      )}

      {canSeeBiblioteca(user) && (
        <HomeCard
          title="Biblioteca Inteligente"
          text={
            isParent(user)
              ? "Consulta artículos y material educativo en modo solo lectura."
              : "Explora artículos y material educativo."
          }
          icon="library"
          accent="lilac"
          onPress={() => router.push("/(tabs)/biblioteca")}
        />
      )}

      {canSeePadres(user) && (
        <HomeCard
          title="Modo Padres"
          text="Seguimiento, orientación, mensajes y contactos recomendados."
          icon="people"
          accent="sky"
          onPress={() => router.push("/(tabs)/padres")}
        />
      )}

      {canSeeAdmin(user) && (
        <HomeCard
          title="Administración"
          text="Gestiona usuarios, roles, tokens, cuentas guest y apoyo a padres."
          icon="settings"
          accent="purple"
          onPress={() => router.push("/(tabs)/admin")}
        />
      )}

      <HomeCard
        title="Perfil"
        text="Consulta tu cuenta, preferencias y sesión."
        icon="person-circle"
        accent="sky"
        onPress={() => router.push("/(tabs)/perfil")}
      />
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  screen: {
    flex: 1,
    backgroundColor: BRAND.colors.background,
  },
  content: {
    padding: 16,
    paddingBottom: 30,
  },
  heroCard: {
    backgroundColor: BRAND.colors.card,
    borderRadius: 26,
    padding: 18,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: "#F1E8F6",
    shadowColor: "#000",
    shadowOpacity: 0.06,
    shadowRadius: 12,
    shadowOffset: { width: 0, height: 7 },
    elevation: 3,
  },
  brandRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 14,
  },
  logo: {
    width: 92,
    height: 92,
    borderRadius: 22,
  },
  brandTextBlock: {
    flex: 1,
  },
  brandName: {
    color: BRAND.colors.purple,
    fontSize: 28,
    fontWeight: "900",
  },
  brandTagline: {
    color: BRAND.colors.coralDark,
    marginTop: 4,
    fontWeight: "900",
    lineHeight: 19,
  },
  heroDivider: {
    height: 1,
    backgroundColor: "#F1E8F6",
    marginVertical: 16,
  },
  heroTitle: {
    color: BRAND.colors.text,
    fontSize: 23,
    fontWeight: "900",
  },
  heroSubtitle: {
    color: BRAND.colors.muted,
    marginTop: 8,
    lineHeight: 20,
  },
  roleBadge: {
    alignSelf: "flex-start",
    backgroundColor: BRAND.colors.softCoral,
    color: BRAND.colors.coralDark,
    overflow: "hidden",
    borderRadius: 999,
    paddingHorizontal: 12,
    paddingVertical: 7,
    marginTop: 12,
    fontWeight: "900",
  },
  card: {
    backgroundColor: BRAND.colors.card,
    borderRadius: 18,
    padding: 16,
    marginBottom: 12,
    flexDirection: "row",
    alignItems: "center",
    gap: 12,
    borderWidth: 1,
    borderColor: "#EEF2F7",
  },
  cardIcon: {
    width: 46,
    height: 46,
    borderRadius: 16,
    justifyContent: "center",
    alignItems: "center",
  },
  cardTextBlock: {
    flex: 1,
  },
  cardTitle: {
    color: BRAND.colors.text,
    fontSize: 17,
    fontWeight: "900",
  },
  cardText: {
    color: BRAND.colors.muted,
    marginTop: 5,
    lineHeight: 20,
  },
});
