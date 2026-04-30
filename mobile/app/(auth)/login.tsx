// Pantalla de login y registro
import { useState } from "react";
import {
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { Redirect } from "expo-router";

import { useAuth } from "../../src/lib/auth";

export default function LoginScreen() {
  const { token, signIn, signUp, isLoading } = useAuth();

  const [mode, setMode] = useState<"login" | "register">("login");
  const [displayName, setDisplayName] = useState("");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [errorText, setErrorText] = useState("");

  if (isLoading) {
    return (
      <View style={styles.centered}>
        <ActivityIndicator size="large" color="#2f64b9" />
      </View>
    );
  }

  if (token) {
    return <Redirect href="/(tabs)/home" />;
  }

 const handleSubmit = async () => {
  try {
    setErrorText("");
    setSubmitting(true);

    if (!username.trim()) {
      setErrorText("Escribe un nombre de usuario.");
      return;
    }

    if (username.trim().length < 3) {
      setErrorText("El nombre de usuario debe tener al menos 3 caracteres.");
      return;
    }

    if (password.length < 8) {
      setErrorText("La contraseña debe tener al menos 8 caracteres.");
      return;
    }

    if (mode === "register") {
      if (password !== confirmPassword) {
        setErrorText("Las contraseñas no coinciden.");
        return;
      }

      await signUp(displayName, username, password);
    } else {
      await signIn(username, password);
    }
  } catch (error: any) {
    setErrorText(error?.message || "No se pudo completar la acción.");
  } finally {
    setSubmitting(false);
  }
};

  return (
    <SafeAreaView style={styles.safe}>
      <KeyboardAvoidingView
        style={styles.flex}
        behavior={Platform.OS === "ios" ? "padding" : undefined}
      >
        <ScrollView contentContainerStyle={styles.container}>
          <View style={styles.heroCard}>
            <Text style={styles.title}>Amigo Imaginario</Text>
            <Text style={styles.subtitle}>
              Accede a tu espacio de conversación, biblioteca y apoyo.
            </Text>
          </View>

          <View style={styles.modeRow}>
            <Pressable
              style={[styles.modeButton, mode === "login" && styles.modeButtonActive]}
              onPress={() => setMode("login")}
            >
              <Text
                style={[
                  styles.modeButtonText,
                  mode === "login" && styles.modeButtonTextActive,
                ]}
              >
                Iniciar sesión
              </Text>
            </Pressable>

            <Pressable
              style={[styles.modeButton, mode === "register" && styles.modeButtonActive]}
              onPress={() => setMode("register")}
            >
              <Text
                style={[
                  styles.modeButtonText,
                  mode === "register" && styles.modeButtonTextActive,
                ]}
              >
                Crear cuenta
              </Text>
            </Pressable>
          </View>

          <View style={styles.formCard}>
            {mode === "register" && (
              <TextInput
                style={styles.input}
                placeholder="Nombre visible"
                value={displayName}
                onChangeText={setDisplayName}
              />
            )}

            <TextInput
              style={styles.input}
              placeholder="Nombre de usuario"
              value={username}
              onChangeText={setUsername}
              autoCapitalize="none"
            />

            <TextInput
              style={styles.input}
              placeholder="Contraseña"
              value={password}
              onChangeText={setPassword}
              secureTextEntry
            />

            {mode === "register" && (
              <TextInput
                style={styles.input}
                placeholder="Confirmar contraseña"
                value={confirmPassword}
                onChangeText={setConfirmPassword}
                secureTextEntry
              />
            )}

            {!!errorText && <Text style={styles.errorText}>{errorText}</Text>}

            <Pressable
              style={[styles.submitButton, submitting && styles.submitButtonDisabled]}
              onPress={handleSubmit}
              disabled={submitting}
            >
              <Text style={styles.submitButtonText}>
                {submitting
                  ? "Procesando..."
                  : mode === "login"
                  ? "Entrar"
                  : "Crear cuenta"}
              </Text>
            </Pressable>

            <Text style={styles.noteText}>
              Login con Google móvil lo agregamos en la siguiente fase.
            </Text>
          </View>
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: {
    flex: 1,
    backgroundColor: "#f5f7fb",
  },
  flex: {
    flex: 1,
  },
  centered: {
    flex: 1,
    backgroundColor: "#f5f7fb",
    justifyContent: "center",
    alignItems: "center",
  },
  container: {
    padding: 20,
    justifyContent: "center",
    flexGrow: 1,
  },
  heroCard: {
    backgroundColor: "#2f64b9",
    borderRadius: 22,
    padding: 22,
    marginBottom: 20,
  },
  title: {
    color: "#ffffff",
    fontSize: 28,
    fontWeight: "800",
  },
  subtitle: {
    color: "#dbeafe",
    marginTop: 8,
    lineHeight: 20,
    fontSize: 14,
  },
  modeRow: {
    flexDirection: "row",
    gap: 10,
    marginBottom: 16,
  },
  modeButton: {
    flex: 1,
    backgroundColor: "#e5e7eb",
    paddingVertical: 12,
    borderRadius: 14,
    alignItems: "center",
  },
  modeButtonActive: {
    backgroundColor: "#ffffff",
  },
  modeButtonText: {
    color: "#334155",
    fontWeight: "700",
  },
  modeButtonTextActive: {
    color: "#0f172a",
  },
  formCard: {
    backgroundColor: "#ffffff",
    borderRadius: 22,
    padding: 18,
    shadowColor: "#000",
    shadowOpacity: 0.05,
    shadowRadius: 10,
    shadowOffset: { width: 0, height: 4 },
    elevation: 2,
  },
  input: {
    backgroundColor: "#f8fafc",
    borderRadius: 14,
    paddingHorizontal: 14,
    paddingVertical: 14,
    fontSize: 15,
    color: "#111827",
    marginBottom: 12,
  },
  errorText: {
    color: "#dc2626",
    marginBottom: 10,
    fontWeight: "600",
  },
  submitButton: {
    backgroundColor: "#2f64b9",
    paddingVertical: 14,
    borderRadius: 14,
    alignItems: "center",
  },
  submitButtonDisabled: {
    opacity: 0.6,
  },
  submitButtonText: {
    color: "#ffffff",
    fontWeight: "800",
    fontSize: 15,
  },
  noteText: {
    marginTop: 12,
    color: "#64748b",
    textAlign: "center",
    fontSize: 13,
  },
});