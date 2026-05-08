import { useEffect, useMemo, useState } from "react";
import {
  ActivityIndicator,
  Alert,
  Pressable,
  RefreshControl,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from "react-native";
import { Ionicons } from "@expo/vector-icons";

import {
  type AdminUser,
  adminCreateGuestRequest,
  adminDeactivateGuestRequest,
  adminExtendGuestRequest,
  adminListGuestsRequest,
  adminListUsersRequest,
  adminUpdateUserRoleRequest,
  adminUpdateUserTokensRequest,
} from "../../src/lib/api";
import { useAuth } from "../../src/lib/auth";

type AdminTab = "usuarios" | "tokens" | "guests" | "crearGuest";

type TokenInputs = {
  daily_limit: string;
  reset_interval_hours: string;
  low_threshold: string;
};

function roleLabel(role: string): string {
  const map: Record<string, string> = {
    superadmin: "Superadmin",
    parent_admin: "Admin padre",
    child: "Niño",
    guest_child: "Guest niño",
    guest_parent: "Guest padre",
  };

  return map[role] || role;
}

function statusLabel(status?: string): string {
  const map: Record<string, string> = {
    active: "Activo",
    expired: "Expirado",
    inactive: "Inactivo",
    none: "No aplica",
  };

  return map[status || ""] || status || "-";
}

export default function AdminScreen() {
  const { token, user } = useAuth();

  const [tab, setTab] = useState<AdminTab>("usuarios");
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const [users, setUsers] = useState<AdminUser[]>([]);
  const [guests, setGuests] = useState<AdminUser[]>([]);

  const [tokenInputs, setTokenInputs] = useState<Record<number, TokenInputs>>({});

  const [guestName, setGuestName] = useState("");
  const [guestUsername, setGuestUsername] = useState("");
  const [guestPassword, setGuestPassword] = useState("");
  const [guestType, setGuestType] = useState<"guest_child" | "guest_parent">(
    "guest_child"
  );
  const [guestHours, setGuestHours] = useState("4");
  const [guestTokens, setGuestTokens] = useState("10");

  const isSuperadmin = user?.role === "superadmin" || Boolean(user?.is_admin);

  const permanentUsers = useMemo(() => {
    return users.filter((item) => item.account_type !== "guest");
  }, [users]);

  const tokenUsers = useMemo(() => {
    return users.filter((item) => item.role !== "superadmin");
  }, [users]);

  const buildTokenInputs = (items: AdminUser[]) => {
    const nextInputs: Record<number, TokenInputs> = {};

    items.forEach((item) => {
      nextInputs[item.id] = {
        daily_limit: String(item.token_status?.daily_limit ?? 20),
        reset_interval_hours: String(item.token_status?.reset_interval_hours ?? 24),
        low_threshold: String(item.token_status?.low_threshold ?? 5),
      };
    });

    setTokenInputs(nextInputs);
  };

  const loadData = async () => {
    if (!token || !isSuperadmin) return;

    try {
      setLoading(true);

      const [usersData, guestsData] = await Promise.all([
        adminListUsersRequest(token),
        adminListGuestsRequest(token),
      ]);

      setUsers(usersData);
      setGuests(guestsData);
      buildTokenInputs(usersData);
    } catch (error: any) {
      Alert.alert("Error", error?.message || "No se pudo cargar administración.");
    } finally {
      setLoading(false);
    }
  };

  const refreshData = async () => {
    try {
      setRefreshing(true);
      await loadData();
    } finally {
      setRefreshing(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [token, isSuperadmin]);

  const handleChangeRole = async (userId: number, role: string) => {
    if (!token) return;

    try {
      await adminUpdateUserRoleRequest(token, userId, role);
      Alert.alert("Listo", "Rol actualizado correctamente.");
      await loadData();
    } catch (error: any) {
      Alert.alert("Error", error?.message || "No se pudo actualizar el rol.");
    }
  };

  const setTokenField = (
    userId: number,
    field: keyof TokenInputs,
    value: string
  ) => {
    setTokenInputs((prev) => ({
      ...prev,
      [userId]: {
        ...(prev[userId] || {
          daily_limit: "20",
          reset_interval_hours: "24",
          low_threshold: "5",
        }),
        [field]: value,
      },
    }));
  };

  const handleUpdateTokens = async (item: AdminUser) => {
    if (!token) return;

    const values = tokenInputs[item.id];

    if (!values) return;

    try {
      await adminUpdateUserTokensRequest(token, item.id, {
        daily_limit: Number(values.daily_limit) || 0,
        reset_interval_hours: Number(values.reset_interval_hours) || 24,
        low_threshold: Number(values.low_threshold) || 0,
      });

      Alert.alert("Listo", "Tokens actualizados correctamente.");
      await loadData();
    } catch (error: any) {
      Alert.alert("Error", error?.message || "No se pudieron actualizar los tokens.");
    }
  };

  const handleCreateGuest = async () => {
    if (!token) return;

    if (!guestName.trim() || !guestUsername.trim() || !guestPassword.trim()) {
      Alert.alert("Validación", "Completa nombre, usuario y contraseña.");
      return;
    }

    if (guestPassword.length < 8) {
      Alert.alert("Validación", "La contraseña debe tener al menos 8 caracteres.");
      return;
    }

    try {
      await adminCreateGuestRequest(token, {
        username: guestUsername.trim(),
        password: guestPassword,
        display_name: guestName.trim(),
        guest_type: guestType,
        hours: Number(guestHours) || 4,
        token_limit: Number(guestTokens) || 10,
      });

      setGuestName("");
      setGuestUsername("");
      setGuestPassword("");
      setGuestType("guest_child");
      setGuestHours("4");
      setGuestTokens("10");

      Alert.alert("Listo", "Cuenta guest creada correctamente.");
      await loadData();
      setTab("guests");
    } catch (error: any) {
      Alert.alert("Error", error?.message || "No se pudo crear la cuenta guest.");
    }
  };

  const handleExtendGuest = async (userId: number) => {
    if (!token) return;

    try {
      await adminExtendGuestRequest(token, userId, 1);
      Alert.alert("Listo", "Se agregó 1 hora a la cuenta guest.");
      await loadData();
    } catch (error: any) {
      Alert.alert("Error", error?.message || "No se pudo extender el guest.");
    }
  };

  const handleDeactivateGuest = async (userId: number) => {
    if (!token) return;

    try {
      await adminDeactivateGuestRequest(token, userId);
      Alert.alert("Listo", "Cuenta guest desactivada.");
      await loadData();
    } catch (error: any) {
      Alert.alert("Error", error?.message || "No se pudo desactivar el guest.");
    }
  };

  if (!isSuperadmin) {
    return (
      <View style={styles.centered}>
        <Ionicons name="lock-closed-outline" size={42} color="#64748b" />
        <Text style={styles.title}>Sin permiso</Text>
        <Text style={styles.text}>
          Esta sección solo está disponible para superadmin.
        </Text>
      </View>
    );
  }

  if (loading) {
    return (
      <View style={styles.centered}>
        <ActivityIndicator size="large" color="#2f64b9" />
        <Text style={styles.text}>Cargando administración...</Text>
      </View>
    );
  }

  return (
    <View style={styles.screen}>
      <View style={styles.header}>
        <Text style={styles.title}>Administración</Text>
        <Text style={styles.text}>
          Gestiona usuarios, roles, tokens y cuentas guest.
        </Text>
      </View>

      <View style={styles.tabs}>
        <Pressable
          style={[styles.tabButton, tab === "usuarios" && styles.tabButtonActive]}
          onPress={() => setTab("usuarios")}
        >
          <Text
            style={[
              styles.tabButtonText,
              tab === "usuarios" && styles.tabButtonTextActive,
            ]}
          >
            Usuarios
          </Text>
        </Pressable>

        <Pressable
          style={[styles.tabButton, tab === "tokens" && styles.tabButtonActive]}
          onPress={() => setTab("tokens")}
        >
          <Text
            style={[
              styles.tabButtonText,
              tab === "tokens" && styles.tabButtonTextActive,
            ]}
          >
            Tokens
          </Text>
        </Pressable>

        <Pressable
          style={[styles.tabButton, tab === "guests" && styles.tabButtonActive]}
          onPress={() => setTab("guests")}
        >
          <Text
            style={[
              styles.tabButtonText,
              tab === "guests" && styles.tabButtonTextActive,
            ]}
          >
            Guests
          </Text>
        </Pressable>

        <Pressable
          style={[styles.tabButton, tab === "crearGuest" && styles.tabButtonActive]}
          onPress={() => setTab("crearGuest")}
        >
          <Text
            style={[
              styles.tabButtonText,
              tab === "crearGuest" && styles.tabButtonTextActive,
            ]}
          >
            Crear
          </Text>
        </Pressable>
      </View>

      <ScrollView
        contentContainerStyle={styles.content}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={refreshData} />
        }
      >
        {tab === "usuarios" && (
          <>
            {permanentUsers.map((item) => (
              <View key={item.id} style={styles.card}>
                <Text style={styles.cardTitle}>{item.display_name}</Text>
                <Text style={styles.text}>@{item.username}</Text>
                <Text style={styles.text}>
                  Rol actual: {roleLabel(item.role)}
                </Text>
                <Text style={styles.text}>
                  Estado: {item.is_active ? "Activo" : "Inactivo"}
                </Text>

                <Text style={styles.label}>Cambiar rol</Text>

                <View style={styles.roleRow}>
                  {["superadmin", "parent_admin", "child"].map((role) => (
                    <Pressable
                      key={role}
                      style={[
                        styles.roleButton,
                        item.role === role && styles.roleButtonActive,
                      ]}
                      onPress={() => handleChangeRole(item.id, role)}
                    >
                      <Text
                        style={[
                          styles.roleButtonText,
                          item.role === role && styles.roleButtonTextActive,
                        ]}
                      >
                        {roleLabel(role)}
                      </Text>
                    </Pressable>
                  ))}
                </View>
              </View>
            ))}
          </>
        )}

        {tab === "tokens" && (
          <>
            {tokenUsers.map((item) => {
              const values = tokenInputs[item.id] || {
                daily_limit: String(item.token_status?.daily_limit ?? 20),
                reset_interval_hours: String(
                  item.token_status?.reset_interval_hours ?? 24
                ),
                low_threshold: String(item.token_status?.low_threshold ?? 5),
              };

              return (
                <View key={item.id} style={styles.card}>
                  <Text style={styles.cardTitle}>{item.display_name}</Text>
                  <Text style={styles.text}>@{item.username}</Text>
                  <Text style={styles.text}>Rol: {roleLabel(item.role)}</Text>

                  <View style={styles.tokenInfoBox}>
                    <Text style={styles.tokenInfoText}>
                      Restantes: {item.token_status?.remaining_tokens ?? 0}
                    </Text>
                    <Text style={styles.tokenInfoText}>
                      Usados: {item.token_status?.used_tokens ?? 0}
                    </Text>
                    <Text style={styles.tokenInfoText}>
                      Reinicio: {item.token_status?.reset_text || "-"}
                    </Text>
                  </View>

                  <Text style={styles.label}>Límite diario</Text>
                  <TextInput
                    style={styles.input}
                    keyboardType="numeric"
                    value={values.daily_limit}
                    onChangeText={(value) =>
                      setTokenField(item.id, "daily_limit", value)
                    }
                  />

                  <Text style={styles.label}>Reinicio cada cuántas horas</Text>
                  <TextInput
                    style={styles.input}
                    keyboardType="numeric"
                    value={values.reset_interval_hours}
                    onChangeText={(value) =>
                      setTokenField(item.id, "reset_interval_hours", value)
                    }
                  />

                  <Text style={styles.label}>Alerta de pocos tokens</Text>
                  <TextInput
                    style={styles.input}
                    keyboardType="numeric"
                    value={values.low_threshold}
                    onChangeText={(value) =>
                      setTokenField(item.id, "low_threshold", value)
                    }
                  />

                  <Pressable
                    style={styles.primaryButton}
                    onPress={() => handleUpdateTokens(item)}
                  >
                    <Text style={styles.primaryButtonText}>Guardar tokens</Text>
                  </Pressable>
                </View>
              );
            })}
          </>
        )}

        {tab === "guests" && (
          <>
            {guests.length === 0 ? (
              <View style={styles.card}>
                <Text style={styles.cardTitle}>Sin cuentas guest</Text>
                <Text style={styles.text}>
                  Todavía no has creado cuentas guest.
                </Text>
              </View>
            ) : (
              guests.map((item) => (
                <View key={item.id} style={styles.card}>
                  <Text style={styles.cardTitle}>{item.display_name}</Text>
                  <Text style={styles.text}>@{item.username}</Text>
                  <Text style={styles.text}>Rol: {roleLabel(item.role)}</Text>
                  <Text style={styles.text}>
                    Estado: {statusLabel(item.guest_status)}
                  </Text>
                  <Text style={styles.text}>
                    Horas asignadas: {item.guest_hours || 0}
                  </Text>
                  <Text style={styles.text}>
                    Expira: {item.guest_expires_at || "-"}
                  </Text>

                  <View style={styles.actionsRow}>
                    <Pressable
                      style={styles.secondaryButton}
                      onPress={() => handleExtendGuest(item.id)}
                    >
                      <Text style={styles.secondaryButtonText}>+1 hora</Text>
                    </Pressable>

                    <Pressable
                      style={styles.dangerButton}
                      onPress={() => handleDeactivateGuest(item.id)}
                    >
                      <Text style={styles.dangerButtonText}>Desactivar</Text>
                    </Pressable>
                  </View>
                </View>
              ))
            )}
          </>
        )}

        {tab === "crearGuest" && (
          <View style={styles.card}>
            <Text style={styles.cardTitle}>Crear cuenta guest</Text>

            <Text style={styles.label}>Nombre visible</Text>
            <TextInput
              style={styles.input}
              value={guestName}
              onChangeText={setGuestName}
              placeholder="Ejemplo: Invitado niño"
            />

            <Text style={styles.label}>Usuario</Text>
            <TextInput
              style={styles.input}
              value={guestUsername}
              onChangeText={setGuestUsername}
              placeholder="guest_nino_1"
              autoCapitalize="none"
            />

            <Text style={styles.label}>Contraseña</Text>
            <TextInput
              style={styles.input}
              value={guestPassword}
              onChangeText={setGuestPassword}
              placeholder="Mínimo 8 caracteres"
              secureTextEntry
            />

            <Text style={styles.label}>Tipo de guest</Text>

            <View style={styles.roleRow}>
              <Pressable
                style={[
                  styles.roleButton,
                  guestType === "guest_child" && styles.roleButtonActive,
                ]}
                onPress={() => setGuestType("guest_child")}
              >
                <Text
                  style={[
                    styles.roleButtonText,
                    guestType === "guest_child" && styles.roleButtonTextActive,
                  ]}
                >
                  Guest niño
                </Text>
              </Pressable>

              <Pressable
                style={[
                  styles.roleButton,
                  guestType === "guest_parent" && styles.roleButtonActive,
                ]}
                onPress={() => setGuestType("guest_parent")}
              >
                <Text
                  style={[
                    styles.roleButtonText,
                    guestType === "guest_parent" && styles.roleButtonTextActive,
                  ]}
                >
                  Guest padre
                </Text>
              </Pressable>
            </View>

            <Text style={styles.label}>Horas de acceso</Text>
            <TextInput
              style={styles.input}
              value={guestHours}
              onChangeText={setGuestHours}
              keyboardType="numeric"
            />

            <Text style={styles.label}>Tokens asignados</Text>
            <TextInput
              style={styles.input}
              value={guestTokens}
              onChangeText={setGuestTokens}
              keyboardType="numeric"
            />

            <Pressable style={styles.primaryButton} onPress={handleCreateGuest}>
              <Text style={styles.primaryButtonText}>Crear guest</Text>
            </Pressable>
          </View>
        )}
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  screen: {
    flex: 1,
    backgroundColor: "#f5f7fb",
  },
  centered: {
    flex: 1,
    backgroundColor: "#f5f7fb",
    justifyContent: "center",
    alignItems: "center",
    padding: 22,
  },
  header: {
    backgroundColor: "#ffffff",
    padding: 18,
    borderBottomWidth: 1,
    borderBottomColor: "#e2e8f0",
  },
  title: {
    color: "#0f172a",
    fontSize: 24,
    fontWeight: "900",
  },
  text: {
    color: "#64748b",
    marginTop: 4,
    lineHeight: 20,
  },
  tabs: {
    flexDirection: "row",
    flexWrap: "wrap",
    padding: 10,
    backgroundColor: "#ffffff",
    gap: 8,
  },
  tabButton: {
    flexGrow: 1,
    backgroundColor: "#e9eef8",
    borderRadius: 999,
    paddingVertical: 10,
    paddingHorizontal: 12,
    alignItems: "center",
  },
  tabButtonActive: {
    backgroundColor: "#2f64b9",
  },
  tabButtonText: {
    color: "#334155",
    fontWeight: "800",
    fontSize: 12,
  },
  tabButtonTextActive: {
    color: "#ffffff",
  },
  content: {
    padding: 16,
    paddingBottom: 30,
  },
  card: {
    backgroundColor: "#ffffff",
    borderRadius: 18,
    padding: 16,
    marginBottom: 12,
  },
  cardTitle: {
    color: "#0f172a",
    fontSize: 17,
    fontWeight: "900",
    marginBottom: 6,
  },
  label: {
    color: "#334155",
    fontWeight: "800",
    marginTop: 12,
    marginBottom: 6,
  },
  roleRow: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 8,
    marginTop: 6,
  },
  roleButton: {
    backgroundColor: "#e9eef8",
    borderRadius: 999,
    paddingHorizontal: 12,
    paddingVertical: 9,
  },
  roleButtonActive: {
    backgroundColor: "#2f64b9",
  },
  roleButtonText: {
    color: "#334155",
    fontWeight: "800",
    fontSize: 12,
  },
  roleButtonTextActive: {
    color: "#ffffff",
  },
  tokenInfoBox: {
    backgroundColor: "#f8fafc",
    borderRadius: 14,
    padding: 12,
    marginTop: 12,
  },
  tokenInfoText: {
    color: "#475569",
    lineHeight: 20,
  },
  input: {
    backgroundColor: "#f8fafc",
    borderRadius: 14,
    paddingHorizontal: 14,
    paddingVertical: 13,
    color: "#0f172a",
  },
  primaryButton: {
    backgroundColor: "#2f64b9",
    borderRadius: 14,
    paddingVertical: 14,
    alignItems: "center",
    marginTop: 16,
  },
  primaryButtonText: {
    color: "#ffffff",
    fontWeight: "900",
  },
  actionsRow: {
    flexDirection: "row",
    gap: 10,
    marginTop: 12,
  },
  secondaryButton: {
    flex: 1,
    backgroundColor: "#dbeafe",
    paddingVertical: 11,
    borderRadius: 12,
    alignItems: "center",
  },
  secondaryButtonText: {
    color: "#1e3a8a",
    fontWeight: "900",
  },
  dangerButton: {
    flex: 1,
    backgroundColor: "#fee2e2",
    paddingVertical: 11,
    borderRadius: 12,
    alignItems: "center",
  },
  dangerButtonText: {
    color: "#991b1b",
    fontWeight: "900",
  },
});