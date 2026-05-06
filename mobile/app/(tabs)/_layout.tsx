// ============================================================
// mobile/app/(tabs)/_layout.tsx
// Layout protegido por sesión con navegación según rol.
// ============================================================

import React from "react";
import { Redirect, Tabs } from "expo-router";
import { Ionicons } from "@expo/vector-icons";

import { useAuth } from "../../src/lib/auth";

export default function TabsLayout() {
  const { token, isLoading, user } = useAuth();

  if (!isLoading && !token) {
    return <Redirect href="/(auth)/login" />;
  }

  const permissions = user?.permissions;

  return (
    <Tabs
      screenOptions={{
        headerShown: true,
        tabBarActiveTintColor: "#2f64b9",
        tabBarInactiveTintColor: "#94a3b8",
      }}
    >
      <Tabs.Screen
        name="home"
        options={{
          title: "Inicio",
          tabBarIcon: ({ color, size }) => (
            <Ionicons name="home" color={color} size={size} />
          ),
        }}
      />

      <Tabs.Screen
        name="amigo"
        options={{
          title: "Amigo",
          href: permissions?.can_access_amigo === false ? null : undefined,
          tabBarIcon: ({ color, size }) => (
            <Ionicons name="chatbubble-ellipses" color={color} size={size} />
          ),
        }}
      />

      <Tabs.Screen
        name="biblioteca"
        options={{
          title: "Biblioteca",
          href: permissions?.can_access_biblioteca ? undefined : null,
          tabBarIcon: ({ color, size }) => (
            <Ionicons name="library" color={color} size={size} />
          ),
        }}
      />

      <Tabs.Screen
        name="padres"
        options={{
          title: "Padres",
          href: permissions?.can_access_modo_padres ? undefined : null,
          tabBarIcon: ({ color, size }) => (
            <Ionicons name="people" color={color} size={size} />
          ),
        }}
      />

      <Tabs.Screen
        name="perfil"
        options={{
          title: "Perfil",
          tabBarIcon: ({ color, size }) => (
            <Ionicons name="person-circle" color={color} size={size} />
          ),
        }}
      />
    </Tabs>
  );
}
