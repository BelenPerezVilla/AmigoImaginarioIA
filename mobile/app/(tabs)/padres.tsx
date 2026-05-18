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

import ChatModuleScreen from "../../src/components/ChatModuleScreen";
import {
  type ChildActivitySummary,
  type ParentalNotification,
  type SupportChild,
  type SupportContact,
  type SupportReply,
  type SupportRequest,
  createSupportRequestRequest,
  getChildActivitySummaryRequest,
  getParentalNotificationsRequest,
  getSupportChildrenRequest,
  getSupportContactsRequest,
  getSupportRequestContactsRequest,
  getSupportRequestRepliesRequest,
  getSupportRequestsRequest,
  markParentalNotificationReadRequest,
} from "../../src/lib/api";
import { useAuth } from "../../src/lib/auth";

type MainTab = "seguimiento" | "orientacion";
type SupportTab = "resumen" | "alertas" | "mensajes" | "contactos";

function formatModuleName(module: string): string {
  const map: Record<string, string> = {
    amigo_imaginario: "Amigo Imaginario",
    biblioteca_inteligente: "Biblioteca Inteligente",
    modo_padres: "Modo Padres",
  };

  return map[module] || module;
}

function formatStatus(status: string): string {
  const map: Record<string, string> = {
    open: "Abierta",
    in_review: "En revisión",
    closed: "Cerrada",
  };

  return map[status] || status;
}

function ContactCard({ contact }: { contact: SupportContact }) {
  return (
    <View style={styles.card}>
      <Text style={styles.cardTitle}>{contact.name}</Text>
      <Text style={styles.cardText}>Especialidad: {contact.specialty || "-"}</Text>
      {!!contact.organization && (
        <Text style={styles.cardText}>Organización: {contact.organization}</Text>
      )}
      {!!contact.phone && <Text style={styles.cardText}>Teléfono: {contact.phone}</Text>}
      {!!contact.email && <Text style={styles.cardText}>Correo: {contact.email}</Text>}
      {!!contact.address && <Text style={styles.cardText}>Dirección: {contact.address}</Text>}
      {!!contact.notes && <Text style={styles.cardText}>Notas: {contact.notes}</Text>}
      {!!contact.recommendation_note && (
        <Text style={styles.recommendationNote}>
          Nota recomendada: {contact.recommendation_note}
        </Text>
      )}
    </View>
  );
}

export default function PadresScreen() {
  const { token, user } = useAuth();

  const [mainTab, setMainTab] = useState<MainTab>("seguimiento");
  const [supportTab, setSupportTab] = useState<SupportTab>("resumen");

  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const [children, setChildren] = useState<SupportChild[]>([]);
  const [selectedChildId, setSelectedChildId] = useState<number | null>(null);
  const [summary, setSummary] = useState<ChildActivitySummary | null>(null);

  const [contacts, setContacts] = useState<SupportContact[]>([]);
  const [requests, setRequests] = useState<SupportRequest[]>([]);
  const [notifications, setNotifications] = useState<ParentalNotification[]>([]);

  const [subject, setSubject] = useState("");
  const [message, setMessage] = useState("");
  const [priority, setPriority] = useState<"normal" | "alta">("normal");
  const [sendingRequest, setSendingRequest] = useState(false);

  const [selectedRequest, setSelectedRequest] = useState<SupportRequest | null>(null);
  const [requestReplies, setRequestReplies] = useState<SupportReply[]>([]);
  const [requestContacts, setRequestContacts] = useState<SupportContact[]>([]);
  const [loadingDetails, setLoadingDetails] = useState(false);

  const role = String(user?.role || "").trim();

  const canUseParentMode = useMemo(() => {
    return ["parent_admin", "guest_parent", "superadmin"].includes(role) || user?.is_admin;
  }, [role, user]);

  const selectedChild = useMemo(() => {
    return children.find((child) => child.id === selectedChildId) || null;
  }, [children, selectedChildId]);

  const loadData = async () => {
    if (!token) return;

    try {
      setLoading(true);

      const [childrenData, contactsData, requestsData, notificationsData] = await Promise.all([
        getSupportChildrenRequest(token),
        getSupportContactsRequest(token),
        getSupportRequestsRequest(token),
        getParentalNotificationsRequest(token),
      ]);

      setChildren(childrenData);
      setContacts(contactsData);
      setRequests(requestsData);
      setNotifications(notificationsData);

      const childToUse = selectedChildId || childrenData[0]?.id || null;

      setSelectedChildId(childToUse);

      if (childToUse) {
        const summaryData = await getChildActivitySummaryRequest(token, childToUse);
        setSummary(summaryData);
      } else {
        setSummary(null);
      }
    } catch (error: any) {
      Alert.alert("Error", error?.message || "No se pudo cargar Modo Padres.");
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
  }, [token]);

  useEffect(() => {
    const loadSummary = async () => {
      if (!token || !selectedChildId) return;

      try {
        const summaryData = await getChildActivitySummaryRequest(token, selectedChildId);
        setSummary(summaryData);
      } catch (error: any) {
        Alert.alert("Error", error?.message || "No se pudo cargar el resumen.");
      }
    };

    loadSummary();
  }, [token, selectedChildId]);

  const handleCreateRequest = async () => {
    if (!token) return;

    if (!subject.trim()) {
      Alert.alert("Validación", "Escribe un asunto.");
      return;
    }

    if (!message.trim()) {
      Alert.alert("Validación", "Escribe tu mensaje.");
      return;
    }

    try {
      setSendingRequest(true);

      await createSupportRequestRequest(token, {
        child_user_id: selectedChildId,
        subject,
        message,
        priority,
      });

      setSubject("");
      setMessage("");
      setPriority("normal");

      const requestsData = await getSupportRequestsRequest(token);
      setRequests(requestsData);

      Alert.alert("Listo", "Tu solicitud fue enviada correctamente.");
    } catch (error: any) {
      Alert.alert("Error", error?.message || "No se pudo enviar la solicitud.");
    } finally {
      setSendingRequest(false);
    }
  };

  const handleMarkNotificationRead = async (notificationId: number) => {
    if (!token) return;

    try {
      const updated = await markParentalNotificationReadRequest(token, notificationId);

      setNotifications((prev) =>
        prev.map((notification) =>
          notification.id === notificationId ? updated : notification
        )
      );
    } catch (error: any) {
      Alert.alert("Error", error?.message || "No se pudo marcar la alerta como leída.");
    }
  };

  const openRequestDetails = async (request: SupportRequest) => {
    if (!token) return;

    try {
      setSelectedRequest(request);
      setLoadingDetails(true);

      const [repliesData, contactsData] = await Promise.all([
        getSupportRequestRepliesRequest(token, request.id),
        getSupportRequestContactsRequest(token, request.id),
      ]);

      setRequestReplies(repliesData);
      setRequestContacts(contactsData);
    } catch (error: any) {
      Alert.alert("Error", error?.message || "No se pudieron cargar los detalles.");
    } finally {
      setLoadingDetails(false);
    }
  };

  if (!canUseParentMode) {
    return (
      <View style={styles.centered}>
        <Ionicons name="lock-closed-outline" size={42} color="#64748b" />
        <Text style={styles.centerTitle}>Sin permiso</Text>
        <Text style={styles.centerText}>
          Tu cuenta no tiene acceso al Modo Padres.
        </Text>
      </View>
    );
  }

  if (mainTab === "orientacion") {
    return (
      <View style={styles.flex}>
        <View style={styles.topTabs}>
          <Pressable
            style={styles.topTab}
            onPress={() => setMainTab("seguimiento")}
          >
            <Text
              style={[
                styles.topTabText,
              ]}
            >
              Seguimiento
            </Text>
          </Pressable>

          <Pressable
            style={[styles.topTab, styles.topTabActive]}
            onPress={() => setMainTab("orientacion")}
          >
            <Text
              style={[
                styles.topTabText,
                styles.topTabTextActive,
              ]}
            >
              Orientación general
            </Text>
          </Pressable>
        </View>

        <ChatModuleScreen
          module="modo_padres"
          title="Modo Padres"
          placeholder="Describe la situación que quieres trabajar..."
          companionName="Guía"
          companionSubtitle="Espacio práctico y calmado para orientación familiar."
          avatarVariant="guide"
          quickExamples={[
            "Mi hijo se frustra muy rápido",
            "¿Cómo puedo calmar una crisis?",
            "¿Me recomiendas algún especialista?",
            "¿Dónde puedo buscar apoyo profesional?",
          ]}
        />
      </View>
    );
  }

  if (loading) {
    return (
      <View style={styles.centered}>
        <ActivityIndicator size="large" color="#2f64b9" />
        <Text style={styles.centerText}>Cargando seguimiento...</Text>
      </View>
    );
  }

  return (
    <View style={styles.flex}>
      <View style={styles.topTabs}>
        <Pressable
          style={[styles.topTab, styles.topTabActive]}
          onPress={() => setMainTab("seguimiento")}
        >
          <Text
            style={[
              styles.topTabText,
              styles.topTabTextActive,
            ]}
          >
            Seguimiento
          </Text>
        </Pressable>

        <Pressable
          style={styles.topTab}
          onPress={() => setMainTab("orientacion")}
        >
          <Text
            style={[
              styles.topTabText,
            ]}
          >
            Orientación general
          </Text>
        </Pressable>
      </View>

      <ScrollView
        style={styles.screen}
        contentContainerStyle={styles.content}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={refreshData} />
        }
      >
        <View style={styles.heroCard}>
          <Text style={styles.heroTitle}>Seguimiento y apoyo</Text>
          <Text style={styles.heroText}>
            Consulta actividad general, envía mensajes al psicólogo/superadmin
            y revisa contactos recomendados.
          </Text>
        </View>

        <View style={styles.segmentRow}>
          <Pressable
            style={[styles.segmentChip, supportTab === "resumen" && styles.segmentChipActive]}
            onPress={() => setSupportTab("resumen")}
          >
            <Text
              style={[
                styles.segmentChipText,
                supportTab === "resumen" && styles.segmentChipTextActive,
              ]}
            >
              Resumen
            </Text>
          </Pressable>

          <Pressable
            style={[styles.segmentChip, supportTab === "alertas" && styles.segmentChipActive]}
            onPress={() => setSupportTab("alertas")}
          >
            <Text
              style={[
                styles.segmentChipText,
                supportTab === "alertas" && styles.segmentChipTextActive,
              ]}
            >
              Alertas
            </Text>
          </Pressable>

          <Pressable
            style={[styles.segmentChip, supportTab === "mensajes" && styles.segmentChipActive]}
            onPress={() => setSupportTab("mensajes")}
          >
            <Text
              style={[
                styles.segmentChipText,
                supportTab === "mensajes" && styles.segmentChipTextActive,
              ]}
            >
              Mensajes
            </Text>
          </Pressable>

          <Pressable
            style={[styles.segmentChip, supportTab === "contactos" && styles.segmentChipActive]}
            onPress={() => setSupportTab("contactos")}
          >
            <Text
              style={[
                styles.segmentChipText,
                supportTab === "contactos" && styles.segmentChipTextActive,
              ]}
            >
              Contactos
            </Text>
          </Pressable>
        </View>

        {supportTab === "resumen" && (
          <>
            {children.length === 0 ? (
              <View style={styles.card}>
                <Text style={styles.cardTitle}>Sin hijo vinculado</Text>
                <Text style={styles.cardText}>
                  El superadmin debe vincular esta cuenta de padre con una cuenta de niño.
                </Text>
              </View>
            ) : (
              <>
                <Text style={styles.label}>Selecciona hijo</Text>

                <ScrollView
                  horizontal
                  showsHorizontalScrollIndicator={false}
                  style={styles.childrenRow}
                  contentContainerStyle={styles.childrenContent}
                >
                  {children.map((child) => {
                    const active = child.id === selectedChildId;

                    return (
                      <Pressable
                        key={child.id}
                        style={[styles.childChip, active && styles.childChipActive]}
                        onPress={() => setSelectedChildId(child.id)}
                      >
                        <Text
                          style={[
                            styles.childChipText,
                            active && styles.childChipTextActive,
                          ]}
                        >
                          {child.display_name}
                        </Text>
                      </Pressable>
                    );
                  })}
                </ScrollView>

                <Text style={styles.sectionTitle}>
                  Resumen de {selectedChild?.display_name || "hijo"}
                </Text>

                <View style={styles.metricsRow}>
                  <View style={styles.metricCard}>
                    <Text style={styles.metricValue}>
                      {summary?.token_wallet?.remaining_tokens ?? 0}
                    </Text>
                    <Text style={styles.metricLabel}>Tokens restantes</Text>
                  </View>

                  <View style={styles.metricCard}>
                    <Text style={styles.metricValue}>
                      {summary?.token_wallet?.used_tokens ?? 0}
                    </Text>
                    <Text style={styles.metricLabel}>Tokens usados</Text>
                  </View>

                  <View style={styles.metricCard}>
                    <Text style={styles.metricValue}>
                      {summary?.support_summary?.open_requests ?? 0}
                    </Text>
                    <Text style={styles.metricLabel}>Solicitudes abiertas</Text>
                  </View>
                </View>

                <Text style={styles.sectionTitle}>Actividad por módulo</Text>

                {summary?.messages_by_module?.length ? (
                  summary.messages_by_module.map((item) => (
                    <View key={item.module} style={styles.card}>
                      <Text style={styles.cardTitle}>
                        {formatModuleName(item.module)}
                      </Text>
                      <Text style={styles.cardText}>
                        Mensajes totales: {item.total_messages || 0}
                      </Text>
                      <Text style={styles.cardText}>
                        Mensajes del usuario: {item.user_messages || 0}
                      </Text>
                      <Text style={styles.cardText}>
                        Respuestas del sistema: {item.assistant_messages || 0}
                      </Text>
                    </View>
                  ))
                ) : (
                  <Text style={styles.emptyText}>Sin actividad registrada todavía.</Text>
                )}

                <Text style={styles.sectionTitle}>Actividad reciente</Text>

                {summary?.recent_activity?.length ? (
                  summary.recent_activity.map((item) => (
                    <View key={item.id} style={styles.card}>
                      <Text style={styles.cardTitle}>
                        {item.title || "Conversación"}
                      </Text>
                      <Text style={styles.cardText}>
                        Módulo: {formatModuleName(item.module)}
                      </Text>
                      <Text style={styles.cardText}>
                        Mensajes: {item.total_messages || 0}
                      </Text>
                      <Text style={styles.cardText}>
                        Última actividad: {item.updated_at}
                      </Text>
                    </View>
                  ))
                ) : (
                  <Text style={styles.emptyText}>Sin conversaciones recientes.</Text>
                )}

                {!!summary?.note && (
                  <Text style={styles.legalNote}>{summary.note}</Text>
                )}
              </>
            )}
          </>
        )}

        {supportTab === "alertas" && (
          <>
            <Text style={styles.sectionTitle}>Alertas parentales</Text>

            <View style={styles.card}>
              <Text style={styles.cardTitle}>Control de contenido sensible</Text>
              <Text style={styles.cardText}>
                Aquí aparecerán avisos cuando AbrazoIA bloquee un intento de
                contenido no permitido en una cuenta de hijo vinculada.
              </Text>
            </View>

            {notifications.length === 0 ? (
              <Text style={styles.emptyText}>
                No hay alertas parentales registradas.
              </Text>
            ) : (
              notifications.map((notification) => {
                const isUnread = Number(notification.is_read) === 0;

                return (
                  <View
                    key={notification.id}
                    style={[styles.card, isUnread && styles.alertUnreadCard]}
                  >
                    <View style={styles.requestHeader}>
                      <Text style={styles.cardTitle}>{notification.title}</Text>
                      {isUnread && <Text style={styles.alertBadge}>Nueva</Text>}
                    </View>

                    <Text style={styles.cardText}>
                      Hijo: {notification.child_name || notification.child_username}
                    </Text>
                    <Text style={styles.cardText}>
                      Categoría: {notification.category || "contenido sensible"}
                    </Text>
                    <Text style={styles.cardText}>{notification.message}</Text>
                    <Text style={styles.dateText}>{notification.created_at}</Text>

                    {isUnread && (
                      <Pressable
                        style={styles.secondaryButton}
                        onPress={() => handleMarkNotificationRead(notification.id)}
                      >
                        <Text style={styles.secondaryButtonText}>
                          Marcar como leída
                        </Text>
                      </Pressable>
                    )}
                  </View>
                );
              })
            )}
          </>
        )}

        {supportTab === "mensajes" && (
          <>
            <View style={styles.card}>
              <Text style={styles.cardTitle}>Mensaje al psicólogo/superadmin</Text>
              <Text style={styles.cardText}>
                Escribe una duda o situación. El superadmin podrá responder y recomendar contactos.
              </Text>

              <Text style={styles.label}>Asunto</Text>
              <TextInput
                style={styles.input}
                value={subject}
                onChangeText={setSubject}
                placeholder="Ejemplo: ¿Cómo apoyar cuando se frustra?"
              />

              <Text style={styles.label}>Mensaje</Text>
              <TextInput
                style={[styles.input, styles.multilineInput]}
                value={message}
                onChangeText={setMessage}
                placeholder="Describe qué pasa y qué tipo de apoyo buscas."
                multiline
              />

              <Text style={styles.label}>Prioridad</Text>
              <View style={styles.segmentRow}>
                <Pressable
                  style={[
                    styles.segmentChip,
                    priority === "normal" && styles.segmentChipActive,
                  ]}
                  onPress={() => setPriority("normal")}
                >
                  <Text
                    style={[
                      styles.segmentChipText,
                      priority === "normal" && styles.segmentChipTextActive,
                    ]}
                  >
                    Normal
                  </Text>
                </Pressable>

                <Pressable
                  style={[
                    styles.segmentChip,
                    priority === "alta" && styles.segmentChipActive,
                  ]}
                  onPress={() => setPriority("alta")}
                >
                  <Text
                    style={[
                      styles.segmentChipText,
                      priority === "alta" && styles.segmentChipTextActive,
                    ]}
                  >
                    Alta
                  </Text>
                </Pressable>
              </View>

              <Pressable
                style={[styles.primaryButton, sendingRequest && styles.disabledButton]}
                onPress={handleCreateRequest}
                disabled={sendingRequest}
              >
                <Text style={styles.primaryButtonText}>
                  {sendingRequest ? "Enviando..." : "Enviar solicitud"}
                </Text>
              </Pressable>
            </View>

            <Text style={styles.sectionTitle}>Mis solicitudes</Text>

            {requests.length === 0 ? (
              <Text style={styles.emptyText}>Aún no has enviado solicitudes.</Text>
            ) : (
              requests.map((request) => (
                <Pressable
                  key={request.id}
                  style={styles.card}
                  onPress={() => openRequestDetails(request)}
                >
                  <View style={styles.requestHeader}>
                    <Text style={styles.cardTitle}>{request.subject}</Text>
                    <Text style={styles.statusBadge}>
                      {formatStatus(request.status)}
                    </Text>
                  </View>

                  <Text style={styles.cardText}>
                    Prioridad: {request.priority}
                  </Text>
                  <Text style={styles.cardText}>
                    Relacionado con: {request.child_name || "General"}
                  </Text>
                  <Text style={styles.cardText} numberOfLines={3}>
                    {request.message}
                  </Text>
                  <Text style={styles.openText}>Tocar para ver respuestas</Text>
                </Pressable>
              ))
            )}
          </>
        )}

        {supportTab === "contactos" && (
          <>
            <Text style={styles.sectionTitle}>Contactos recomendados</Text>

            {contacts.length === 0 ? (
              <Text style={styles.emptyText}>
                Aún no hay contactos recomendados registrados.
              </Text>
            ) : (
              contacts.map((contact) => (
                <ContactCard key={contact.id} contact={contact} />
              ))
            )}
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

            {loadingDetails ? (
              <ActivityIndicator size="large" color="#2f64b9" />
            ) : (
              <ScrollView showsVerticalScrollIndicator={false}>
                <Text style={styles.cardText}>
                  Estado: {formatStatus(selectedRequest?.status || "")}
                </Text>
                <Text style={styles.cardText}>
                  Prioridad: {selectedRequest?.priority}
                </Text>

                <Text style={styles.modalSectionTitle}>Mensaje enviado</Text>
                <Text style={styles.cardText}>{selectedRequest?.message}</Text>

                <Text style={styles.modalSectionTitle}>Respuestas</Text>

                {requestReplies.length === 0 ? (
                  <Text style={styles.emptyText}>Aún no hay respuestas.</Text>
                ) : (
                  requestReplies.map((reply) => (
                    <View key={reply.id} style={styles.replyCard}>
                      <Text style={styles.cardTitle}>{reply.author_name}</Text>
                      <Text style={styles.cardText}>{reply.message}</Text>
                      <Text style={styles.dateText}>{reply.created_at}</Text>
                    </View>
                  ))
                )}

                <Text style={styles.modalSectionTitle}>Contactos recomendados</Text>

                {requestContacts.length === 0 ? (
                  <Text style={styles.emptyText}>
                    No hay contactos agregados a esta solicitud.
                  </Text>
                ) : (
                  requestContacts.map((contact) => (
                    <ContactCard key={contact.id} contact={contact} />
                  ))
                )}
              </ScrollView>
            )}
          </View>
        </View>
      </Modal>
    </View>
  );
}

const styles = StyleSheet.create({
  flex: {
    flex: 1,
    backgroundColor: "#f5f7fb",
  },
  screen: {
    flex: 1,
    backgroundColor: "#f5f7fb",
  },
  content: {
    padding: 16,
    paddingBottom: 30,
  },
  topTabs: {
    flexDirection: "row",
    backgroundColor: "#ffffff",
    padding: 8,
    gap: 8,
  },
  topTab: {
    flex: 1,
    paddingVertical: 12,
    borderRadius: 14,
    alignItems: "center",
    backgroundColor: "#eef2f7",
  },
  topTabActive: {
    backgroundColor: "#2f64b9",
  },
  topTabText: {
    color: "#334155",
    fontWeight: "800",
  },
  topTabTextActive: {
    color: "#ffffff",
  },
  heroCard: {
    backgroundColor: "#2f64b9",
    borderRadius: 22,
    padding: 20,
    marginBottom: 16,
  },
  heroTitle: {
    color: "#ffffff",
    fontSize: 22,
    fontWeight: "900",
  },
  heroText: {
    color: "#dbeafe",
    marginTop: 8,
    lineHeight: 20,
  },
  segmentRow: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 8,
    marginBottom: 14,
  },
  segmentChip: {
    backgroundColor: "#e9eef8",
    paddingHorizontal: 14,
    paddingVertical: 10,
    borderRadius: 999,
  },
  segmentChipActive: {
    backgroundColor: "#2f64b9",
  },
  segmentChipText: {
    color: "#334155",
    fontWeight: "800",
  },
  segmentChipTextActive: {
    color: "#ffffff",
  },
  label: {
    color: "#334155",
    fontWeight: "800",
    marginBottom: 8,
    marginTop: 8,
  },
  childrenRow: {
    maxHeight: 46,
    marginBottom: 14,
  },
  childrenContent: {
    gap: 8,
    paddingRight: 10,
  },
  childChip: {
    backgroundColor: "#e9eef8",
    paddingHorizontal: 14,
    paddingVertical: 11,
    borderRadius: 999,
  },
  childChipActive: {
    backgroundColor: "#2f64b9",
  },
  childChipText: {
    color: "#334155",
    fontWeight: "800",
  },
  childChipTextActive: {
    color: "#ffffff",
  },
  sectionTitle: {
    color: "#0f172a",
    fontSize: 19,
    fontWeight: "900",
    marginBottom: 12,
    marginTop: 4,
  },
  metricsRow: {
    flexDirection: "row",
    gap: 10,
    marginBottom: 16,
  },
  metricCard: {
    flex: 1,
    backgroundColor: "#ffffff",
    borderRadius: 18,
    padding: 14,
  },
  metricValue: {
    color: "#0f172a",
    fontSize: 25,
    fontWeight: "900",
  },
  metricLabel: {
    color: "#64748b",
    marginTop: 4,
    fontSize: 12,
    fontWeight: "700",
  },
  card: {
    backgroundColor: "#ffffff",
    borderRadius: 18,
    padding: 16,
    marginBottom: 12,
  },
  cardTitle: {
    color: "#0f172a",
    fontSize: 16,
    fontWeight: "900",
    marginBottom: 6,
  },
  cardText: {
    color: "#475569",
    lineHeight: 20,
    marginTop: 2,
  },
  recommendationNote: {
    color: "#2f64b9",
    marginTop: 8,
    fontWeight: "700",
    lineHeight: 20,
  },
  legalNote: {
    color: "#64748b",
    fontSize: 12,
    lineHeight: 18,
    marginTop: 8,
  },
  emptyText: {
    color: "#64748b",
    lineHeight: 20,
    marginBottom: 12,
  },
  input: {
    backgroundColor: "#f8fafc",
    borderRadius: 14,
    paddingHorizontal: 14,
    paddingVertical: 13,
    fontSize: 15,
    color: "#0f172a",
    marginBottom: 10,
  },
  multilineInput: {
    minHeight: 110,
    textAlignVertical: "top",
  },
  primaryButton: {
    backgroundColor: "#2f64b9",
    borderRadius: 14,
    paddingVertical: 14,
    alignItems: "center",
    marginTop: 8,
  },
  disabledButton: {
    opacity: 0.55,
  },
  primaryButtonText: {
    color: "#ffffff",
    fontWeight: "900",
  },
  secondaryButton: {
    backgroundColor: "#e9eef8",
    borderRadius: 14,
    paddingVertical: 12,
    alignItems: "center",
    marginTop: 12,
  },
  secondaryButtonText: {
    color: "#2f64b9",
    fontWeight: "900",
  },
  alertUnreadCard: {
    borderWidth: 1,
    borderColor: "#f59e0b",
    backgroundColor: "#fffbeb",
  },
  alertBadge: {
    backgroundColor: "#f59e0b",
    color: "#ffffff",
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: 999,
    overflow: "hidden",
    fontWeight: "900",
    fontSize: 12,
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
    fontWeight: "800",
  },
  centered: {
    flex: 1,
    backgroundColor: "#f5f7fb",
    justifyContent: "center",
    alignItems: "center",
    padding: 22,
  },
  centerTitle: {
    color: "#0f172a",
    fontWeight: "900",
    fontSize: 20,
    marginTop: 12,
  },
  centerText: {
    color: "#64748b",
    textAlign: "center",
    lineHeight: 20,
    marginTop: 8,
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
    maxHeight: "88%",
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
});