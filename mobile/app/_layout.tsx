// ============================================================
// mobile/app/_layout.tsx
// Layout raíz de Expo Router.
// Este archivo envuelve TODA la app con AuthProvider.
// ============================================================

import { Stack } from "expo-router";

import { AuthProvider } from "../src/lib/auth";

export default function RootLayout() {
  return (
    <AuthProvider>
      <Stack
        screenOptions={{
          headerShown: false,
        }}
      />
    </AuthProvider>
  );
}