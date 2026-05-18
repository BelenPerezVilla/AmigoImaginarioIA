// ============================================================
// mobile/app/(auth)/login.tsx
// Pantalla de login y registro con identidad visual AbrazoIA.
// ============================================================

import { useState } from "react";
import {
  ActivityIndicator,
  Image,
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
import { BRAND, BRAND_LOGO } from "../../src/lib/brand";

export default function LoginScreen() {
  const { token, signIn, signUp, isLoading } = useAuth();

  const [mode, setMode] = useState<"login" | "register">("login");
  const [displayName, setDisplayName] = useState("");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [acceptedTerms, setAcceptedTerms] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [errorText, setErrorText] = useState("");

  if (isLoading) {
    return (
      <View style={styles.centered}>
        <ActivityIndicator size="large" color={BRAND.colors.coralDark} />
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

      if (!acceptedTerms) {
        setErrorText("Debes leer y aceptar el uso y condiciones para continuar.");
        return;
      }

      if (mode === "register") {
        if (!displayName.trim()) {
          setErrorText("Escribe tu nombre visible.");
          return;
        }

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
        <ScrollView
          contentContainerStyle={styles.container}
          keyboardShouldPersistTaps="handled"
        >
          <View style={styles.brandCard}>
            <Image source={BRAND_LOGO} style={styles.logo} resizeMode="contain" />

            <Text style={styles.title}>{BRAND.name}</Text>
            <Text style={styles.tagline}>{BRAND.tagline}</Text>
            <Text style={styles.subtitle}>{BRAND.shortDescription}</Text>
          </View>

          <View style={styles.modeRow}>
            <Pressable
              style={[
                styles.modeButton,
                mode === "login" && styles.modeButtonActive,
              ]}
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
              style={[
                styles.modeButton,
                mode === "register" && styles.modeButtonActive,
              ]}
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
            <Text style={styles.formTitle}>
              {mode === "login" ? "Bienvenido de nuevo" : "Crear cuenta"}
            </Text>
            <Text style={styles.formSubtitle}>
              {mode === "login"
                ? "Entra a tu espacio de acompañamiento."
                : "Crea una cuenta para comenzar con AbrazoIA."}
            </Text>

            {mode === "register" && (
              <TextInput
                style={styles.input}
                placeholder="Nombre visible"
                placeholderTextColor="#94a3b8"
                value={displayName}
                onChangeText={setDisplayName}
              />
            )}

            <TextInput
              style={styles.input}
              placeholder="Nombre de usuario"
              placeholderTextColor="#94a3b8"
              value={username}
              onChangeText={setUsername}
              autoCapitalize="none"
            />

            <TextInput
              style={styles.input}
              placeholder="Contraseña"
              placeholderTextColor="#94a3b8"
              value={password}
              onChangeText={setPassword}
              secureTextEntry
            />

            {mode === "register" && (
              <TextInput
                style={styles.input}
                placeholder="Confirmar contraseña"
                placeholderTextColor="#94a3b8"
                value={confirmPassword}
                onChangeText={setConfirmPassword}
                secureTextEntry
              />
            )}

            <Pressable
              style={styles.termsBox}
              onPress={() => setAcceptedTerms((prev) => !prev)}
            >
              <View style={[styles.checkbox, acceptedTerms && styles.checkboxActive]}>
                {acceptedTerms && <Text style={styles.checkboxCheck}>✓</Text>}
              </View>

              <Text style={styles.termsText}>
                He leído y acepto el uso y condiciones de AbrazoIA. Entiendo que
                es una herramienta de apoyo y orientación, no sustituye atención
                médica, psicológica ni terapéutica profesional.
              </Text>
            </Pressable>

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
                  ? "Entrar a AbrazoIA"
                  : "Crear cuenta"}
              </Text>
            </Pressable>

            <Text style={styles.noteText}>
              Plataforma de apoyo y orientación. No sustituye atención médica,
              psicológica ni terapéutica profesional.
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
    backgroundColor: BRAND.colors.background,
  },
  flex: {
    flex: 1,
  },
  centered: {
    flex: 1,
    backgroundColor: BRAND.colors.background,
    justifyContent: "center",
    alignItems: "center",
  },
  container: {
    padding: 20,
    justifyContent: "center",
    flexGrow: 1,
  },
  brandCard: {
    backgroundColor: BRAND.colors.card,
    borderRadius: 28,
    padding: 22,
    marginBottom: 18,
    alignItems: "center",
    borderWidth: 1,
    borderColor: "#F1E8F6",
    shadowColor: "#000",
    shadowOpacity: 0.06,
    shadowRadius: 14,
    shadowOffset: { width: 0, height: 8 },
    elevation: 3,
  },
  logo: {
    width: 210,
    height: 210,
    marginBottom: 4,
  },
  title: {
    color: BRAND.colors.purple,
    fontSize: 32,
    fontWeight: "900",
  },
  tagline: {
    color: BRAND.colors.coralDark,
    marginTop: 6,
    fontWeight: "900",
    textAlign: "center",
  },
  subtitle: {
    color: BRAND.colors.muted,
    marginTop: 8,
    lineHeight: 20,
    fontSize: 14,
    textAlign: "center",
  },
  modeRow: {
    flexDirection: "row",
    gap: 10,
    marginBottom: 16,
  },
  modeButton: {
    flex: 1,
    backgroundColor: "#E9EEF8",
    paddingVertical: 12,
    borderRadius: 16,
    alignItems: "center",
  },
  modeButtonActive: {
    backgroundColor: BRAND.colors.coral,
  },
  modeButtonText: {
    color: "#334155",
    fontWeight: "800",
  },
  modeButtonTextActive: {
    color: "#ffffff",
  },
  formCard: {
    backgroundColor: BRAND.colors.card,
    borderRadius: 24,
    padding: 18,
    shadowColor: "#000",
    shadowOpacity: 0.05,
    shadowRadius: 10,
    shadowOffset: { width: 0, height: 4 },
    elevation: 2,
  },
  formTitle: {
    color: BRAND.colors.text,
    fontSize: 22,
    fontWeight: "900",
  },
  formSubtitle: {
    color: BRAND.colors.muted,
    marginTop: 4,
    marginBottom: 14,
    lineHeight: 20,
  },
  input: {
    backgroundColor: "#F8FAFC",
    borderRadius: 14,
    paddingHorizontal: 14,
    paddingVertical: 14,
    fontSize: 15,
    color: "#111827",
    marginBottom: 12,
  },
  termsBox: {
    flexDirection: "row",
    gap: 10,
    backgroundColor: "#f8fafc",
    borderRadius: 16,
    padding: 12,
    marginBottom: 12,
  },
  checkbox: {
    width: 22,
    height: 22,
    borderRadius: 7,
    borderWidth: 2,
    borderColor: BRAND.colors.coralDark,
    alignItems: "center",
    justifyContent: "center",
    marginTop: 2,
  },
  checkboxActive: {
    backgroundColor: BRAND.colors.coralDark,
  },
  checkboxCheck: {
    color: "#ffffff",
    fontWeight: "900",
    fontSize: 14,
  },
  termsText: {
    flex: 1,
    color: "#64748b",
    lineHeight: 18,
    fontSize: 12,
  },
  errorText: {
    color: "#DC2626",
    marginBottom: 10,
    fontWeight: "700",
  },
  submitButton: {
    backgroundColor: BRAND.colors.purple,
    paddingVertical: 14,
    borderRadius: 14,
    alignItems: "center",
  },
  submitButtonDisabled: {
    opacity: 0.6,
  },
  submitButtonText: {
    color: "#ffffff",
    fontWeight: "900",
    fontSize: 15,
  },
  noteText: {
    marginTop: 12,
    color: BRAND.colors.muted,
    textAlign: "center",
    fontSize: 12,
    lineHeight: 18,
  },
});
