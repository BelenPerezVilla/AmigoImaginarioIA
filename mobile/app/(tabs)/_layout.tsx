// ============================================================
// mobile/app/(tabs)/_layout.tsx
// Layout protegido por sesión, navegación por rol y marca AbrazoIA.
// ============================================================

import React from "react";
import { Redirect, Tabs } from "expo-router";
import { Ionicons } from "@expo/vector-icons";

import { useAuth } from "../../src/lib/auth";
import { BRAND } from "../../src/lib/brand";

export default function TabsLayout() {
  const { token, isLoading, user } = useAuth();

  if (!isLoading && !token) {
    return <Redirect href="/(auth)/login" />;
  }

  const role = String(user?.role || "").trim();

  const isSuperadmin = role === "superadmin" || Boolean(user?.is_admin);
  const isParent = role === "parent_admin" || role === "guest_parent";
  const isChild = role === "child" || role === "guest_child";

  const canShowAmigo =
    isSuperadmin ||
    isParent ||
    isChild ||
    Boolean(user?.permissions?.can_access_amigo);

  const canShowBiblioteca =
    isSuperadmin ||
    isParent ||
    Boolean(user?.permissions?.can_access_biblioteca);

  const canShowPadres =
    isSuperadmin ||
    isParent ||
    Boolean(user?.permissions?.can_access_modo_padres);

  // Administración solo debe aparecer al superadmin.
  // Padres, niños e invitados no deben ver esta pestaña aunque tuvieran
  // permisos heredados en una sesión vieja.
  const canShowAdmin = isSuperadmin;

  return (
    <Tabs
      screenOptions={{
        headerShown: true,
        headerTitleStyle: {
          color: BRAND.colors.purple,
          fontWeight: "900",
        },
        headerTintColor: BRAND.colors.purple,
        tabBarActiveTintColor: BRAND.colors.coralDark,
        tabBarInactiveTintColor: "#94a3b8",
      }}
    >
      <Tabs.Screen
        name="home"
        options={{
          title: BRAND.name,
          tabBarLabel: "Inicio",
          tabBarIcon: ({ color, size }) => (
            <Ionicons name="home" color={color} size={size} />
          ),
        }}
      />

      <Tabs.Screen
        name="amigo"
        options={{
          title: "Amigo",
          href: canShowAmigo ? undefined : null,
          tabBarIcon: ({ color, size }) => (
            <Ionicons name="chatbubble-ellipses" color={color} size={size} />
          ),
        }}
      />

      <Tabs.Screen
        name="biblioteca"
        options={{
          title: "Biblioteca",
          href: canShowBiblioteca ? undefined : null,
          tabBarIcon: ({ color, size }) => (
            <Ionicons name="library" color={color} size={size} />
          ),
        }}
      />

      <Tabs.Screen
        name="padres"
        options={{
          title: "Padres",
          href: canShowPadres ? undefined : null,
          tabBarIcon: ({ color, size }) => (
            <Ionicons name="people" color={color} size={size} />
          ),
        }}
      />

      <Tabs.Screen
        name="admin"
        options={{
          title: "Admin",
          href: canShowAdmin ? undefined : null,
          tabBarIcon: ({ color, size }) => (
            <Ionicons name="settings" color={color} size={size} />
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
