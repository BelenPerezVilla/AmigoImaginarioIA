// ============================================================
// mobile/app/(tabs)/home.tsx
// Pantalla de inicio móvil con módulos según rol y aviso legal.
// ============================================================

import React from "react";
import { Pressable, ScrollView, StyleSheet, Text, View } from "react-native";
import { useRouter } from "expo-router";

import { useAuth } from "../../src/lib/auth";

const LEGAL_NOTICE =
  "Aviso de uso: esta plataforma es una herramienta digital de apoyo, orientación general y acompañamiento guiado. No sustituye atención psicológica, médica, terapéutica ni educativa profesional.";

export default function HomeScreen() {
  const router = useRouter();
  const { user } = useAuth();

  const permissions = user?.permissions;
  const tokenStatus = user?.token_status;

  return (
    <ScrollView style={styles.screen} contentContainerStyle={styles.content}>
      <View style={styles.heroCard}>
        <Text style={styles.heroTitle}>
          Hola, {user?.display_name || "bienvenido"}
        </Text>
        <Text style={styles.heroSubtitle}>
          Rol: {user?.role_label || "Usuario"}. Aquí verás solo los módulos disponibles para tu cuenta.
        </Text>
      </View>

      {tokenStatus && !tokenStatus.is_unlimited && (
        <View
          style={[
            styles.tokenCard,
            tokenStatus.is_empty
              ? styles.tokenCardEmpty
              : tokenStatus.is_low
              ? styles.tokenCardLow
              : styles.tokenCardOk,
          ]}
        >
          <Text style={styles.tokenTitle}>
            Tokens disponibles: {tokenStatus.remaining_tokens} de {tokenStatus.daily_limit}
          </Text>
          <Text style={styles.tokenText}>
            {tokenStatus.message || `Se reinician en ${tokenStatus.reset_text}.`}
          </Text>
        </View>
      )}

      {permissions?.can_access_amigo && (
        <Pressable style={styles.card} onPress={() => router.push("/(tabs)/amigo")}>
          <Text style={styles.cardTitle}>Amigo Imaginario</Text>
          <Text style={styles.cardText}>
            Conversa con tu acompañante emocional.
          </Text>
        </Pressable>
      )}

      {permissions?.can_access_biblioteca && (
        <Pressable
          style={styles.card}
          onPress={() => router.push("/(tabs)/biblioteca")}
        >
          <Text style={styles.cardTitle}>Biblioteca Inteligente</Text>
          <Text style={styles.cardText}>
            Explora artículos y material educativo.
          </Text>
        </Pressable>
      )}

      {permissions?.can_access_modo_padres && (
        <Pressable style={styles.card} onPress={() => router.push("/(tabs)/padres")}>
          <Text style={styles.cardTitle}>Modo Padres</Text>
          <Text style={styles.cardText}>
            Orientación práctica y emocional para cuidadores.
          </Text>
        </Pressable>
      )}

      <Pressable style={styles.card} onPress={() => router.push("/(tabs)/perfil")}>
        <Text style={styles.cardTitle}>Perfil</Text>
        <Text style={styles.cardText}>
          Revisa tu cuenta, rol, tokens y cierra sesión cuando lo necesites.
        </Text>
      </Pressable>

      <View style={styles.legalCard}>
        <Text style={styles.legalTitle}>Aviso importante</Text>
        <Text style={styles.legalText}>{LEGAL_NOTICE}</Text>
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
  },
  heroCard: {
    backgroundColor: "#2f64b9",
    borderRadius: 22,
    padding: 22,
    marginBottom: 16,
  },
  heroTitle: {
    color: "#ffffff",
    fontSize: 24,
    fontWeight: "800",
  },
  heroSubtitle: {
    color: "#dbeafe",
    marginTop: 8,
    lineHeight: 20,
  },
  tokenCard: {
    borderRadius: 18,
    padding: 14,
    marginBottom: 14,
    borderWidth: 1,
  },
  tokenCardOk: {
    backgroundColor: "#dbeafe",
    borderColor: "#bfdbfe",
  },
  tokenCardLow: {
    backgroundColor: "#fef3c7",
    borderColor: "#fde68a",
  },
  tokenCardEmpty: {
    backgroundColor: "#fee2e2",
    borderColor: "#fecaca",
  },
  tokenTitle: {
    color: "#0f172a",
    fontWeight: "800",
    fontSize: 15,
  },
  tokenText: {
    color: "#475569",
    marginTop: 6,
    lineHeight: 19,
  },
  card: {
    backgroundColor: "#ffffff",
    borderRadius: 18,
    padding: 18,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: "#e2e8f0",
  },
  cardTitle: {
    fontSize: 18,
    fontWeight: "800",
    color: "#0f172a",
  },
  cardText: {
    marginTop: 6,
    color: "#64748b",
    lineHeight: 20,
  },
  legalCard: {
    backgroundColor: "#eef2ff",
    borderRadius: 16,
    padding: 14,
    borderWidth: 1,
    borderColor: "#c7d2fe",
    marginTop: 8,
  },
  legalTitle: {
    color: "#1e3a8a",
    fontWeight: "800",
  },
  legalText: {
    color: "#475569",
    marginTop: 6,
    lineHeight: 19,
    fontSize: 13,
  },
});
