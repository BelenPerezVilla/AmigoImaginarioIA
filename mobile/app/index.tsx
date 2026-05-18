// ============================================================
// mobile/app/index.tsx
// Redirección inicial según sesión.
// ============================================================

import { ActivityIndicator, StyleSheet, View } from "react-native";
import { Redirect } from "expo-router";

import { useAuth } from "../src/lib/auth";
import { BRAND } from "../src/lib/brand";

export default function IndexScreen() {
  const { token, isLoading } = useAuth();

  if (isLoading) {
    return (
      <View style={styles.centered}>
        <ActivityIndicator size="large" color={BRAND.colors.blueDark} />
      </View>
    );
  }

  if (!token) {
    return <Redirect href="/(auth)/login" />;
  }

  return <Redirect href="/(tabs)/home" />;
}

const styles = StyleSheet.create({
  centered: {
    flex: 1,
    backgroundColor: BRAND.colors.background,
    justifyContent: "center",
    alignItems: "center",
  },
});