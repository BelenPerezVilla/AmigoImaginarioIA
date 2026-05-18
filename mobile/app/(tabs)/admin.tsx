import { useEffect, useMemo, useState } from "react";
import {
  ActivityIndicator,
  Alert,
  Modal,
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
  type ParentChildLink,
  type SupportContact,
  type SupportReply,
  type SupportRequest,
  adminAddSupportReplyRequest,
  adminCreateGuestRequest,
  adminCreateParentChildLinkRequest,
  adminCreateSupportContactRequest,
  adminDeactivateGuestRequest,
  adminDeactivateSupportContactRequest,
  adminDeleteParentChildLinkRequest,
  adminExtendGuestRequest,
  adminListGuestsRequest,
  adminListParentChildLinksRequest,
  adminListRequestContactsRequest,
  adminListSupportContactsRequest,
  adminListSupportRepliesRequest,
  adminListSupportRequestsRequest,
  adminListUsersRequest,
  adminRecommendContactRequest,
  adminUpdateSupportStatusRequest,
  adminUpdateUserRoleRequest,
  adminUpdateUserTokensRequest,
} from "../../src/lib/api";
import { useAuth } from "../../src/lib/auth";

type AdminTab =
  | "usuarios"
  | "tokens"
  | "guests"
  | "crearGuest"
  | "vinculos"
  | "apoyo"
  | "contactos";

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
    open: "Abierta",
    in_review: "En revisión",
    closed: "Cerrada",
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
  const [supportRequests, setSupportRequests] = useState<SupportRequest[]>([]);
  const [supportContacts, setSupportContacts] = useState<SupportContact[]>([]);
  const [parentChildLinks, setParentChildLinks] = useState<ParentChildLink[]>([]);

  const [selectedParentId, setSelectedParentId] = useState<number | null>(null);
  const [selectedChildId, setSelectedChildId] = useState<number | null>(null);

  const [selectedRequest, setSelectedRequest] =
    useState<SupportRequest | null>(null);
  const [requestReplies, setRequestReplies] = useState<SupportReply[]>([]);
  const [requestContacts, setRequestContacts] = useState<SupportContact[]>([]);
  const [replyText, setReplyText] = useState("");
  const [recommendationNote, setRecommendationNote] = useState("");

  const [tokenInputs, setTokenInputs] = useState<Record<number, TokenInputs>>(
    {}
  );

  const [guestName, setGuestName] = useState("");
  const [guestUsername, setGuestUsername] = useState("");
  const [guestPassword, setGuestPassword] = useState("");
  const [guestType, setGuestType] = useState<"guest_child" | "guest_parent">(
    "guest_child"
  );
  const [guestHours, setGuestHours] = useState("4");
  const [guestTokens, setGuestTokens] = useState("10");

  const [contactName, setContactName] = useState("");
  const [contactSpecialty, setContactSpecialty] = useState("");
  const [contactOrganization, setContactOrganization] = useState("");
  const [contactPhone, setContactPhone] = useState("");
  const [contactEmail, setContactEmail] = useState("");
  const [contactAddress, setContactAddress] = useState("");
  const [contactNotes, setContactNotes] = useState("");

  const [actionLoading, setActionLoading] = useState(false);
  const [detailsLoading, setDetailsLoading] = useState(false);

  const isSuperadmin = user?.role === "superadmin" || Boolean(user?.is_admin);

  const permanentUsers = useMemo(() => {
    return users.filter((item) => item.account_type !== "guest");
  }, [users]);

  const tokenUsers = useMemo(() => {
    return users.filter((item) => item.role !== "superadmin");
  }, [users]);

  const parentUsers = useMemo(() => {
    return users.filter((item) =>
      ["parent_admin", "guest_parent"].includes(item.role)
    );
  }, [users]);

  const childUsers = useMemo(() => {
    return users.filter((item) =>
      ["child", "guest_child"].includes(item.role)
    );
  }, [users]);

  const buildTokenInputs = (items: AdminUser[]) => {
    const nextInputs: Record<number, TokenInputs> = {};

    items.forEach((item) => {
      nextInputs[item.id] = {
        daily_limit: String(item.token_status?.daily_limit ?? 20),
        reset_interval_hours: String(
          item.token_status?.reset_interval_hours ?? 24
        ),
        low_threshold: String(item.token_status?.low_threshold ?? 5),
      };
    });

    setTokenInputs(nextInputs);
  };

  const loadData = async () => {
    if (!token || !isSuperadmin) return;

    try {
      setLoading(true);

      const [
        usersData,
        guestsData,
        supportRequestsData,
        supportContactsData,
        parentChildLinksData,
      ] = await Promise.all([
        adminListUsersRequest(token),
        adminListGuestsRequest(token),
        adminListSupportRequestsRequest(token, "Todas"),
        adminListSupportContactsRequest(token),
        adminListParentChildLinksRequest(token),
      ]);

      setUsers(usersData);
      setGuests(guestsData);
      setSupportRequests(supportRequestsData);
      setSupportContacts(supportContactsData);
      setParentChildLinks(parentChildLinksData);
      buildTokenInputs(usersData);

      const firstParent = usersData.find((item) =>
        ["parent_admin", "guest_parent"].includes(item.role)
      );

      const firstChild = usersData.find((item) =>
        ["child", "guest_child"].includes(item.role)
      );

      setSelectedParentId((prev) => {
        const stillExists = usersData.some((item) => item.id === prev);
        return stillExists ? prev : firstParent?.id || null;
      });

      setSelectedChildId((prev) => {
        const stillExists = usersData.some((item) => item.id === prev);
        return stillExists ? prev : firstChild?.id || null;
      });
    } catch (error: any) {
      Alert.alert(
        "Error",
        error?.message || "No se pudo cargar administración."
      );
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
      Alert.alert(
        "Error",
        error?.message || "No se pudieron actualizar los tokens."
      );
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

  const handleCreateParentChildLink = async () => {
    if (!token) return;

    if (!selectedParentId || !selectedChildId) {
      Alert.alert("Validación", "Selecciona un padre y un hijo.");
      return;
    }

    if (selectedParentId === selectedChildId) {
      Alert.alert("Validación", "El padre y el hijo no pueden ser el mismo usuario.");
      return;
    }

    try {
      setActionLoading(true);

      await adminCreateParentChildLinkRequest(token, {
        parent_user_id: selectedParentId,
        child_user_id: selectedChildId,
      });

      Alert.alert("Listo", "Padre e hijo vinculados correctamente.");
      await loadData();
    } catch (error: any) {
      Alert.alert("Error", error?.message || "No se pudo crear el vínculo.");
    } finally {
      setActionLoading(false);
    }
  };

  const handleDeleteParentChildLink = async (
    parentUserId: number,
    childUserId: number
  ) => {
    if (!token) return;

    try {
      setActionLoading(true);

      await adminDeleteParentChildLinkRequest(
        token,
        parentUserId,
        childUserId
      );

      Alert.alert("Listo", "Vínculo eliminado correctamente.");
      await loadData();
    } catch (error: any) {
      Alert.alert("Error", error?.message || "No se pudo eliminar el vínculo.");
    } finally {
      setActionLoading(false);
    }
  };

  const openRequestDetails = async (request: SupportRequest) => {
    if (!token) return;

    try {
      setSelectedRequest(request);
      setDetailsLoading(true);
      setReplyText("");
      setRecommendationNote("");

      const [repliesData, contactsData] = await Promise.all([
        adminListSupportRepliesRequest(token, request.id),
        adminListRequestContactsRequest(token, request.id),
      ]);

      setRequestReplies(repliesData);
      setRequestContacts(contactsData);
    } catch (error: any) {
      Alert.alert("Error", error?.message || "No se pudieron cargar los detalles.");
    } finally {
      setDetailsLoading(false);
    }
  };

  const reloadRequestDetails = async () => {
    if (!token || !selectedRequest) return;

    const [repliesData, contactsData] = await Promise.all([
      adminListSupportRepliesRequest(token, selectedRequest.id),
      adminListRequestContactsRequest(token, selectedRequest.id),
    ]);

    setRequestReplies(repliesData);
    setRequestContacts(contactsData);
  };

  const handleReplyRequest = async () => {
    if (!token || !selectedRequest) return;

    if (!replyText.trim()) {
      Alert.alert("Validación", "Escribe una respuesta.");
      return;
    }

    try {
      setActionLoading(true);

      await adminAddSupportReplyRequest(token, selectedRequest.id, {
        message: replyText,
        new_status: "in_review",
      });

      setReplyText("");
      await reloadRequestDetails();
      await loadData();

      Alert.alert("Listo", "Respuesta enviada correctamente.");
    } catch (error: any) {
      Alert.alert("Error", error?.message || "No se pudo enviar la respuesta.");
    } finally {
      setActionLoading(false);
    }
  };

  const handleUpdateRequestStatus = async (status: string) => {
    if (!token || !selectedRequest) return;

    try {
      setActionLoading(true);

      const updated = await adminUpdateSupportStatusRequest(
        token,
        selectedRequest.id,
        status
      );

      setSelectedRequest({
        ...selectedRequest,
        status: updated.status,
        updated_at: updated.updated_at,
      });

      await loadData();

      Alert.alert("Listo", "Estado actualizado.");
    } catch (error: any) {
      Alert.alert("Error", error?.message || "No se pudo actualizar el estado.");
    } finally {
      setActionLoading(false);
    }
  };

  const handleRecommendContact = async (contactId: number) => {
    if (!token || !selectedRequest) return;

    try {
      setActionLoading(true);

      await adminRecommendContactRequest(
        token,
        selectedRequest.id,
        contactId,
        recommendationNote
      );

      setRecommendationNote("");
      await reloadRequestDetails();

      Alert.alert("Listo", "Contacto del directorio recomendado en la solicitud.");
    } catch (error: any) {
      Alert.alert("Error", error?.message || "No se pudo recomendar el contacto.");
    } finally {
      setActionLoading(false);
    }
  };

  const handleCreateContact = async () => {
    if (!token) return;

    if (!contactName.trim()) {
      Alert.alert("Validación", "Escribe el nombre del contacto o lugar.");
      return;
    }

    try {
      setActionLoading(true);

      await adminCreateSupportContactRequest(token, {
        name: contactName,
        specialty: contactSpecialty,
        organization: contactOrganization,
        phone: contactPhone,
        email: contactEmail,
        address: contactAddress,
        notes: contactNotes,
      });

      setContactName("");
      setContactSpecialty("");
      setContactOrganization("");
      setContactPhone("");
      setContactEmail("");
      setContactAddress("");
      setContactNotes("");

      await loadData();

      Alert.alert("Listo", "Registro guardado correctamente en el directorio.");
    } catch (error: any) {
      Alert.alert("Error", error?.message || "No se pudo crear el registro del directorio.");
    } finally {
      setActionLoading(false);
    }
  };

  const handleDeactivateContact = async (contactId: number) => {
    if (!token) return;

    try {
      setActionLoading(true);

      await adminDeactivateSupportContactRequest(token, contactId);
      await loadData();

      Alert.alert("Listo", "Registro desactivado.");
    } catch (error: any) {
      Alert.alert("Error", error?.message || "No se pudo desactivar el registro del directorio.");
    } finally {
      setActionLoading(false);
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
          Gestiona usuarios, tokens, guests, vínculos, apoyo a padres y directorio profesional.
        </Text>
      </View>

      <View style={styles.tabs}>
        {[
          ["usuarios", "Usuarios"],
          ["tokens", "Tokens"],
          ["guests", "Guests"],
          ["crearGuest", "Crear"],
          ["vinculos", "Vínculos"],
          ["apoyo", "Apoyo"],
          ["contactos", "Directorio"],
        ].map(([key, label]) => (
          <Pressable
            key={key}
            style={[styles.tabButton, tab === key && styles.tabButtonActive]}
            onPress={() => setTab(key as AdminTab)}
          >
            <Text
              style={[
                styles.tabButtonText,
                tab === key && styles.tabButtonTextActive,
              ]}
            >
              {label}
            </Text>
          </Pressable>
        ))}
      </View>

      <ScrollView
        contentContainerStyle={styles.content}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={refreshData} />
        }
      >
        {tab === "usuarios" && (
          <>
            {permanentUsers.length === 0 ? (
              <View style={styles.card}>
                <Text style={styles.cardTitle}>Sin usuarios</Text>
                <Text style={styles.text}>No hay usuarios registrados.</Text>
              </View>
            ) : (
              permanentUsers.map((item) => (
                <View key={item.id} style={styles.card}>
                  <Text style={styles.cardTitle}>{item.display_name}</Text>
                  <Text style={styles.text}>@{item.username}</Text>
                  <Text style={styles.text}>Rol actual: {roleLabel(item.role)}</Text>
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
              ))
            )}
          </>
        )}

        {tab === "tokens" && (
          <>
            {tokenUsers.length === 0 ? (
              <View style={styles.card}>
                <Text style={styles.cardTitle}>Sin usuarios para tokens</Text>
                <Text style={styles.text}>
                  No hay usuarios configurables para tokens.
                </Text>
              </View>
            ) : (
              tokenUsers.map((item) => {
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
              })
            )}
          </>
        )}

        {tab === "guests" && (
          <>
            {guests.length === 0 ? (
              <View style={styles.card}>
                <Text style={styles.cardTitle}>Sin cuentas guest</Text>
                <Text style={styles.text}>Todavía no has creado cuentas guest.</Text>
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

        {tab === "vinculos" && (
          <>
            <View style={styles.card}>
              <Text style={styles.cardTitle}>Vincular padre con hijo</Text>
              <Text style={styles.text}>
                Selecciona una cuenta de padre y una cuenta de niño para que el
                padre pueda ver el seguimiento en Modo Padres.
              </Text>

              <Text style={styles.label}>Padre / madre</Text>

              {parentUsers.length === 0 ? (
                <Text style={styles.text}>No hay usuarios con rol de padre.</Text>
              ) : (
                <ScrollView
                  horizontal
                  showsHorizontalScrollIndicator={false}
                  contentContainerStyle={styles.horizontalChipContent}
                >
                  {parentUsers.map((parent) => {
                    const active = selectedParentId === parent.id;

                    return (
                      <Pressable
                        key={parent.id}
                        style={[
                          styles.roleButton,
                          active && styles.roleButtonActive,
                        ]}
                        onPress={() => setSelectedParentId(parent.id)}
                      >
                        <Text
                          style={[
                            styles.roleButtonText,
                            active && styles.roleButtonTextActive,
                          ]}
                        >
                          {parent.display_name}
                        </Text>
                        <Text
                          style={[
                            styles.smallChipText,
                            active && styles.roleButtonTextActive,
                          ]}
                        >
                          @{parent.username}
                        </Text>
                      </Pressable>
                    );
                  })}
                </ScrollView>
              )}

              <Text style={styles.label}>Hijo</Text>

              {childUsers.length === 0 ? (
                <Text style={styles.text}>No hay usuarios con rol de niño.</Text>
              ) : (
                <ScrollView
                  horizontal
                  showsHorizontalScrollIndicator={false}
                  contentContainerStyle={styles.horizontalChipContent}
                >
                  {childUsers.map((child) => {
                    const active = selectedChildId === child.id;

                    return (
                      <Pressable
                        key={child.id}
                        style={[
                          styles.roleButton,
                          active && styles.roleButtonActive,
                        ]}
                        onPress={() => setSelectedChildId(child.id)}
                      >
                        <Text
                          style={[
                            styles.roleButtonText,
                            active && styles.roleButtonTextActive,
                          ]}
                        >
                          {child.display_name}
                        </Text>
                        <Text
                          style={[
                            styles.smallChipText,
                            active && styles.roleButtonTextActive,
                          ]}
                        >
                          @{child.username}
                        </Text>
                      </Pressable>
                    );
                  })}
                </ScrollView>
              )}

              <Pressable
                style={[styles.primaryButton, actionLoading && styles.disabled]}
                onPress={handleCreateParentChildLink}
                disabled={actionLoading}
              >
                <Text style={styles.primaryButtonText}>
                  Vincular padre con hijo
                </Text>
              </Pressable>
            </View>

            <Text style={styles.sectionTitle}>Vínculos existentes</Text>

            {parentChildLinks.length === 0 ? (
              <View style={styles.card}>
                <Text style={styles.cardTitle}>Sin vínculos</Text>
                <Text style={styles.text}>
                  Todavía no hay padres vinculados con hijos.
                </Text>
              </View>
            ) : (
              parentChildLinks.map((link) => (
                <View key={link.id} style={styles.card}>
                  <Text style={styles.cardTitle}>
                    {link.parent_name} → {link.child_name}
                  </Text>

                  <Text style={styles.text}>Padre: @{link.parent_username}</Text>
                  <Text style={styles.text}>Hijo: @{link.child_username}</Text>
                  <Text style={styles.text}>Fecha: {link.created_at}</Text>

                  <Pressable
                    style={styles.dangerButtonFull}
                    onPress={() =>
                      handleDeleteParentChildLink(
                        link.parent_user_id,
                        link.child_user_id
                      )
                    }
                  >
                    <Text style={styles.dangerButtonText}>Eliminar vínculo</Text>
                  </Pressable>
                </View>
              ))
            )}
          </>
        )}

        {tab === "apoyo" && (
          <>
            {supportRequests.length === 0 ? (
              <View style={styles.card}>
                <Text style={styles.cardTitle}>Sin solicitudes</Text>
                <Text style={styles.text}>
                  Todavía no hay solicitudes enviadas por padres.
                </Text>
              </View>
            ) : (
              supportRequests.map((request) => (
                <Pressable
                  key={request.id}
                  style={styles.card}
                  onPress={() => openRequestDetails(request)}
                >
                  <View style={styles.requestHeader}>
                    <Text style={styles.cardTitle}>{request.subject}</Text>
                    <Text style={styles.statusBadge}>
                      {statusLabel(request.status)}
                    </Text>
                  </View>

                  <Text style={styles.text}>
                    Padre: {request.parent_name || request.parent_username || "-"}
                  </Text>
                  <Text style={styles.text}>
                    Niño: {request.child_name || request.child_username || "General"}
                  </Text>
                  <Text style={styles.text}>Prioridad: {request.priority}</Text>
                  <Text style={styles.text} numberOfLines={3}>
                    {request.message}
                  </Text>
                  <Text style={styles.openText}>Tocar para responder</Text>
                </Pressable>
              ))
            )}
          </>
        )}

        {tab === "contactos" && (
          <>
            <View style={styles.card}>
              <Text style={styles.cardTitle}>Nuevo registro del directorio</Text>

              <Text style={styles.label}>Nombre del profesional, centro o institución</Text>
              <TextInput
                style={styles.input}
                value={contactName}
                onChangeText={setContactName}
                placeholder="Ejemplo: Centro de apoyo infantil"
              />

              <Text style={styles.label}>Especialidad</Text>
              <TextInput
                style={styles.input}
                value={contactSpecialty}
                onChangeText={setContactSpecialty}
                placeholder="Psicología infantil, terapia, pediatría..."
              />

              <Text style={styles.label}>Organización</Text>
              <TextInput
                style={styles.input}
                value={contactOrganization}
                onChangeText={setContactOrganization}
                placeholder="Nombre de la clínica o institución"
              />

              <Text style={styles.label}>Teléfono</Text>
              <TextInput
                style={styles.input}
                value={contactPhone}
                onChangeText={setContactPhone}
                keyboardType="phone-pad"
              />

              <Text style={styles.label}>Correo</Text>
              <TextInput
                style={styles.input}
                value={contactEmail}
                onChangeText={setContactEmail}
                keyboardType="email-address"
                autoCapitalize="none"
              />

              <Text style={styles.label}>Dirección</Text>
              <TextInput
                style={styles.input}
                value={contactAddress}
                onChangeText={setContactAddress}
              />

              <Text style={styles.label}>Notas</Text>
              <TextInput
                style={[styles.input, styles.multilineInput]}
                value={contactNotes}
                onChangeText={setContactNotes}
                multiline
              />

              <Pressable
                style={[styles.primaryButton, actionLoading && styles.disabled]}
                onPress={handleCreateContact}
                disabled={actionLoading}
              >
                <Text style={styles.primaryButtonText}>Guardar en directorio</Text>
              </Pressable>
            </View>

            {supportContacts.map((contact) => (
              <View key={contact.id} style={styles.card}>
                <Text style={styles.cardTitle}>{contact.name}</Text>
                <Text style={styles.text}>
                  Especialidad: {contact.specialty || "-"}
                </Text>
                {!!contact.organization && (
                  <Text style={styles.text}>
                    Organización: {contact.organization}
                  </Text>
                )}
                {!!contact.phone && (
                  <Text style={styles.text}>Teléfono: {contact.phone}</Text>
                )}
                {!!contact.email && (
                  <Text style={styles.text}>Correo: {contact.email}</Text>
                )}
                {!!contact.address && (
                  <Text style={styles.text}>Dirección: {contact.address}</Text>
                )}
                {!!contact.notes && (
                  <Text style={styles.text}>Notas: {contact.notes}</Text>
                )}
                <Text style={styles.text}>
                  Estado: {Number(contact.is_active) === 1 ? "Activo" : "Inactivo"}
                </Text>

                {Number(contact.is_active) === 1 && (
                  <Pressable
                    style={styles.dangerButtonFull}
                    onPress={() => handleDeactivateContact(contact.id)}
                  >
                    <Text style={styles.dangerButtonText}>
                      Desactivar contacto
                    </Text>
                  </Pressable>
                )}
              </View>
            ))}
          </>
        )}
      </ScrollView>

      <Modal
        visible={!!selectedRequest}
        animationType="slide"
        transparent
        onRequestClose={() => setSelectedRequest(null)}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.modalCard}>
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>
                {selectedRequest?.subject || "Solicitud"}
              </Text>

              <Pressable onPress={() => setSelectedRequest(null)}>
                <Ionicons name="close" size={24} color="#0f172a" />
              </Pressable>
            </View>

            {detailsLoading ? (
              <ActivityIndicator size="large" color="#2f64b9" />
            ) : (
              <ScrollView showsVerticalScrollIndicator={false}>
                <Text style={styles.text}>
                  Estado: {statusLabel(selectedRequest?.status)}
                </Text>
                <Text style={styles.text}>
                  Prioridad: {selectedRequest?.priority}
                </Text>
                <Text style={styles.text}>
                  Padre:{" "}
                  {selectedRequest?.parent_name ||
                    selectedRequest?.parent_username ||
                    "-"}
                </Text>
                <Text style={styles.text}>
                  Niño:{" "}
                  {selectedRequest?.child_name ||
                    selectedRequest?.child_username ||
                    "General"}
                </Text>

                <Text style={styles.modalSectionTitle}>Mensaje del padre</Text>
                <Text style={styles.text}>{selectedRequest?.message}</Text>

                <Text style={styles.modalSectionTitle}>Cambiar estado</Text>

                <View style={styles.roleRow}>
                  {["open", "in_review", "closed"].map((status) => (
                    <Pressable
                      key={status}
                      style={[
                        styles.roleButton,
                        selectedRequest?.status === status &&
                          styles.roleButtonActive,
                      ]}
                      onPress={() => handleUpdateRequestStatus(status)}
                    >
                      <Text
                        style={[
                          styles.roleButtonText,
                          selectedRequest?.status === status &&
                            styles.roleButtonTextActive,
                        ]}
                      >
                        {statusLabel(status)}
                      </Text>
                    </Pressable>
                  ))}
                </View>

                <Text style={styles.modalSectionTitle}>Responder</Text>
                <TextInput
                  style={[styles.input, styles.multilineInput]}
                  value={replyText}
                  onChangeText={setReplyText}
                  placeholder="Escribe una respuesta para el padre..."
                  multiline
                />

                <Pressable
                  style={[styles.primaryButton, actionLoading && styles.disabled]}
                  onPress={handleReplyRequest}
                  disabled={actionLoading}
                >
                  <Text style={styles.primaryButtonText}>Enviar respuesta</Text>
                </Pressable>

                <Text style={styles.modalSectionTitle}>Respuestas</Text>

                {requestReplies.length === 0 ? (
                  <Text style={styles.text}>Aún no hay respuestas.</Text>
                ) : (
                  requestReplies.map((reply) => (
                    <View key={reply.id} style={styles.replyCard}>
                      <Text style={styles.cardTitle}>{reply.author_name}</Text>
                      <Text style={styles.text}>{reply.message}</Text>
                      <Text style={styles.dateText}>{reply.created_at}</Text>
                    </View>
                  ))
                )}

                <Text style={styles.modalSectionTitle}>
                  Directorio profesional
                </Text>

                {requestContacts.length === 0 ? (
                  <Text style={styles.text}>
                    No hay registros del directorio recomendados en esta solicitud.
                  </Text>
                ) : (
                  requestContacts.map((contact) => (
                    <View key={contact.id} style={styles.replyCard}>
                      <Text style={styles.cardTitle}>{contact.name}</Text>
                      <Text style={styles.text}>
                        Especialidad: {contact.specialty || "-"}
                      </Text>
                      {!!contact.phone && (
                        <Text style={styles.text}>Teléfono: {contact.phone}</Text>
                      )}
                      {!!contact.email && (
                        <Text style={styles.text}>Correo: {contact.email}</Text>
                      )}
                      {!!contact.recommendation_note && (
                        <Text style={styles.recommendationNote}>
                          Nota: {contact.recommendation_note}
                        </Text>
                      )}
                    </View>
                  ))
                )}

                <Text style={styles.modalSectionTitle}>
                  Recomendar otro contacto
                </Text>

                <TextInput
                  style={[styles.input, styles.multilineInputSmall]}
                  value={recommendationNote}
                  onChangeText={setRecommendationNote}
                  placeholder="Nota opcional para esta recomendación..."
                  multiline
                />

                {supportContacts
                  .filter((contact) => Number(contact.is_active) === 1)
                  .map((contact) => (
                    <View key={contact.id} style={styles.replyCard}>
                      <Text style={styles.cardTitle}>{contact.name}</Text>
                      <Text style={styles.text}>
                        Especialidad: {contact.specialty || "-"}
                      </Text>
                      {!!contact.phone && (
                        <Text style={styles.text}>Teléfono: {contact.phone}</Text>
                      )}

                      <Pressable
                        style={styles.secondaryButtonFull}
                        onPress={() => handleRecommendContact(contact.id)}
                      >
                        <Text style={styles.secondaryButtonText}>
                          Recomendar en solicitud
                        </Text>
                      </Pressable>
                    </View>
                  ))}
              </ScrollView>
            )}
          </View>
        </View>
      </Modal>
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
  sectionTitle: {
    color: "#0f172a",
    fontSize: 19,
    fontWeight: "900",
    marginBottom: 12,
    marginTop: 4,
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
  horizontalChipContent: {
    gap: 8,
    paddingRight: 12,
    paddingVertical: 4,
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
  smallChipText: {
    color: "#64748b",
    fontSize: 11,
    fontWeight: "700",
    marginTop: 2,
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
  multilineInput: {
    minHeight: 110,
    textAlignVertical: "top",
  },
  multilineInputSmall: {
    minHeight: 75,
    textAlignVertical: "top",
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
  secondaryButtonFull: {
    backgroundColor: "#dbeafe",
    paddingVertical: 11,
    borderRadius: 12,
    alignItems: "center",
    marginTop: 10,
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
  dangerButtonFull: {
    backgroundColor: "#fee2e2",
    paddingVertical: 11,
    borderRadius: 12,
    alignItems: "center",
    marginTop: 12,
  },
  dangerButtonText: {
    color: "#991b1b",
    fontWeight: "900",
  },
  disabled: {
    opacity: 0.55,
  },
  requestHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    gap: 10,
  },
  statusBadge: {
    backgroundColor: "#e9eef8",
    color: "#2f64b9",
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: 999,
    overflow: "hidden",
    fontWeight: "800",
    fontSize: 12,
  },
  openText: {
    marginTop: 8,
    color: "#2f64b9",
    fontWeight: "900",
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: "rgba(15,23,42,0.45)",
    justifyContent: "flex-end",
  },
  modalCard: {
    backgroundColor: "#ffffff",
    borderTopLeftRadius: 24,
    borderTopRightRadius: 24,
    padding: 18,
    maxHeight: "90%",
  },
  modalHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    gap: 12,
    alignItems: "center",
    marginBottom: 12,
  },
  modalTitle: {
    flex: 1,
    color: "#0f172a",
    fontSize: 19,
    fontWeight: "900",
  },
  modalSectionTitle: {
    color: "#0f172a",
    fontSize: 16,
    fontWeight: "900",
    marginTop: 16,
    marginBottom: 8,
  },
  replyCard: {
    backgroundColor: "#f8fafc",
    borderRadius: 16,
    padding: 14,
    marginBottom: 10,
  },
  dateText: {
    color: "#94a3b8",
    fontSize: 12,
    marginTop: 8,
  },
  recommendationNote: {
    color: "#2f64b9",
    marginTop: 8,
    fontWeight: "800",
    lineHeight: 20,
  },
});