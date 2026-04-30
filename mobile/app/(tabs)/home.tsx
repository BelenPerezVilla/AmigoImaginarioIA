// Pantalla de inicio móvil
import React from "react";
import { Pressable, ScrollView, StyleSheet, Text, View } from "react-native";
import { useRouter } from "expo-router";

import { useAuth } from "../../src/lib/auth";

export default function HomeScreen() {
  const router = useRouter();
  const { user } = useAuth();

  return (
    <ScrollView style={styles.screen} contentContainerStyle={styles.content}>
      <View style={styles.heroCard}>
        <Text style={styles.heroTitle}>
          Hola, {user?.display_name || "bienvenido"}
        </Text>
        <Text style={styles.heroSubtitle}>
          Aquí tienes acceso rápido a tus módulos principales.
        </Text>
      </View>

      <Pressable style={styles.card} onPress={() => router.push("/(tabs)/amigo")}>
        <Text style={styles.cardTitle}>Amigo Imaginario</Text>
        <Text style={styles.cardText}>
          Conversa con tu acompañante emocional.
        </Text>
      </Pressable>

      <Pressable
        style={styles.card}
        onPress={() => router.push("/(tabs)/biblioteca")}
      >
        <Text style={styles.cardTitle}>Biblioteca Inteligente</Text>
        <Text style={styles.cardText}>
          Explora artículos y material educativo.
        </Text>
      </Pressable>

      <Pressable style={styles.card} onPress={() => router.push("/(tabs)/padres")}>
        <Text style={styles.cardTitle}>Modo Padres</Text>
        <Text style={styles.cardText}>
          Orientación práctica y emocional para cuidadores.
        </Text>
      </Pressable>

      <Pressable style={styles.card} onPress={() => router.push("/(tabs)/perfil")}>
        <Text style={styles.cardTitle}>Perfil</Text>
        <Text style={styles.cardText}>
          Revisa tu cuenta y cierra sesión cuando lo necesites.
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
  card: {
    backgroundColor: "#ffffff",
    borderRadius: 18,
    padding: 18,
    marginBottom: 12,
    shadowColor: "#000",
    shadowOpacity: 0.05,
    shadowRadius: 8,
    shadowOffset: { width: 0, height: 4 },
    elevation: 2,
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
});