import React from "react";
import { Pressable, ScrollView, StyleSheet, Text, View } from "react-native";
import { useRouter } from "expo-router";

import { useAuth } from "../../src/lib/auth";
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
        <Text style={styles.heroTitle}>
          Hola, {user?.display_name || "bienvenido"}
        </Text>
        <Text style={styles.heroSubtitle}>{subtitle}</Text>
        <Text style={styles.roleBadge}>{roleLabel(user)}</Text>
      </View>

      {canSeeAmigo(user) && (
        <Pressable
          style={styles.card}
          onPress={() => router.push("/(tabs)/amigo")}
        >
          <Text style={styles.cardTitle}>Amigo Imaginario</Text>
          <Text style={styles.cardText}>
            {isParent(user)
              ? "Configura el amigo imaginario del niño vinculado."
              : "Conversa con tu acompañante emocional."}
          </Text>
        </Pressable>
      )}

      {canSeeBiblioteca(user) && (
        <Pressable
          style={styles.card}
          onPress={() => router.push("/(tabs)/biblioteca")}
        >
          <Text style={styles.cardTitle}>Biblioteca Inteligente</Text>
          <Text style={styles.cardText}>
            {isParent(user)
              ? "Consulta artículos y material educativo en modo solo lectura."
              : "Explora artículos y material educativo."}
          </Text>
        </Pressable>
      )}

      {canSeePadres(user) && (
        <Pressable
          style={styles.card}
          onPress={() => router.push("/(tabs)/padres")}
        >
          <Text style={styles.cardTitle}>Modo Padres</Text>
          <Text style={styles.cardText}>
            Seguimiento, orientación, mensajes y contactos recomendados.
          </Text>
        </Pressable>
      )}

      {canSeeAdmin(user) && (
        <Pressable
          style={styles.card}
          onPress={() => router.push("/(tabs)/admin")}
        >
          <Text style={styles.cardTitle}>Administración</Text>
          <Text style={styles.cardText}>
            Gestiona usuarios, roles, tokens y cuentas guest.
          </Text>
        </Pressable>
      )}

      <Pressable
        style={styles.card}
        onPress={() => router.push("/(tabs)/perfil")}
      >
        <Text style={styles.cardTitle}>Perfil</Text>
        <Text style={styles.cardText}>
          Consulta tu cuenta, preferencias y sesión.
        </Text>
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
    paddingBottom: 30,
  },
  heroCard: {
    backgroundColor: "#2f64b9",
    borderRadius: 22,
    padding: 20,
    marginBottom: 16,
  },
  heroTitle: {
    color: "#ffffff",
    fontSize: 24,
    fontWeight: "900",
  },
  heroSubtitle: {
    color: "#dbeafe",
    marginTop: 8,
    lineHeight: 20,
  },
  roleBadge: {
    alignSelf: "flex-start",
    backgroundColor: "rgba(255,255,255,0.18)",
    color: "#ffffff",
    overflow: "hidden",
    borderRadius: 999,
    paddingHorizontal: 12,
    paddingVertical: 7,
    marginTop: 12,
    fontWeight: "900",
  },
  card: {
    backgroundColor: "#ffffff",
    borderRadius: 18,
    padding: 18,
    marginBottom: 12,
  },
  cardTitle: {
    color: "#0f172a",
    fontSize: 18,
    fontWeight: "900",
  },
  cardText: {
    color: "#64748b",
    marginTop: 6,
    lineHeight: 20,
  },
});