// ============================================================
// src/components/ChatModuleScreen.tsx
// Chat reutilizable con avatar configurable desde móvil.
// ============================================================

import {
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import {
  ActivityIndicator,
  Alert,
  Animated,
  KeyboardAvoidingView,
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from "react-native";
import { Ionicons } from "@expo/vector-icons";

import {
  type Conversation,
  type Message,
  type TokenStatus,
  createConversationRequest,
  getConversationMessages,
  getMyTokenStatusRequest,
  listConversations,
  sendMessageRequest,
} from "../lib/api";
import { useAuth } from "../lib/auth";
import CompanionAvatar from "./CompanionAvatar";
import {
  type AvatarVariant,
  buildCompanionSubtitle,
  buildCompanionTheme,
  buildPersonalizedExamples,
} from "../lib/companionTheme";

type ChatModuleScreenProps = {
  module: string;
  title: string;
  placeholder: string;
  companionName?: string;
  companionSubtitle?: string;
  quickExamples?: string[];
  avatarVariant?: AvatarVariant;
  initialConversationId?: number | null;
};

export default function ChatModuleScreen({
  module,
  title,
  placeholder,
  companionName = "Lumi",
  companionSubtitle = "Conversa con calma y en un espacio seguro.",
  quickExamples = [],
  avatarVariant = "lumi",
  initialConversationId = null,
}: ChatModuleScreenProps) {
  const { token, user, avatarProfile } = useAuth();

  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [selectedConversationId, setSelectedConversationId] = useState<number | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const [tokenStatus, setTokenStatus] = useState<TokenStatus | null>(
    user?.token_status || null
  );

  const scrollRef = useRef<ScrollView>(null);
  const floatAnim = useRef(new Animated.Value(0)).current;
  const [typingDots, setTypingDots] = useState(".");

  useEffect(() => {
    const animation = Animated.loop(
      Animated.sequence([
        Animated.timing(floatAnim, {
          toValue: -6,
          duration: 1400,
          useNativeDriver: true,
        }),
        Animated.timing(floatAnim, {
          toValue: 0,
          duration: 1400,
          useNativeDriver: true,
        }),
      ])
    );

    animation.start();

    return () => {
      animation.stop();
    };
  }, [floatAnim]);

  useEffect(() => {
    if (!sending) {
      setTypingDots(".");
      return;
    }

    const interval = setInterval(() => {
      setTypingDots((prev) => {
        if (prev === ".") return "..";
        if (prev === "..") return "...";
        return ".";
      });
    }, 420);

    return () => clearInterval(interval);
  }, [sending]);

  const visibleCompanionName = useMemo(() => {
    if (module === "amigo_imaginario") {
      return user?.friend_name || companionName;
    }

    return companionName;
  }, [module, user, companionName]);

  const theme = useMemo(() => {
    return buildCompanionTheme(
      avatarProfile?.primary_color || user?.favorite_color || "",
      avatarVariant
    );
  }, [user, avatarProfile, avatarVariant]);

  const visibleSubtitle = useMemo(() => {
    if (module === "amigo_imaginario") {
      return buildCompanionSubtitle(
        visibleCompanionName,
        user?.encouragement_style || "",
        user?.preferred_comfort || ""
      );
    }

    return companionSubtitle;
  }, [module, visibleCompanionName, user, companionSubtitle]);

  const visibleExamples = useMemo(() => {
    if (module === "amigo_imaginario") {
      return buildPersonalizedExamples(
        quickExamples,
        user?.preferred_comfort || "",
        user?.favorite_activity || "",
        visibleCompanionName
      );
    }

    return quickExamples;
  }, [module, quickExamples, user, visibleCompanionName]);

  useEffect(() => {
  if (!token) return;

  const bootstrap = async () => {
    try {
      setLoading(true);

      const status = await getMyTokenStatusRequest(token);
      setTokenStatus(status);

      const fetched = await listConversations(module, token);
      setConversations(fetched);

      // ------------------------------------------------------
      // Si llega una conversación inicial desde otra pantalla,
      // se intenta abrir esa primero.
      // ------------------------------------------------------
      let targetConversationId: number | null = null;

      if (initialConversationId) {
        const existsInList = fetched.some(
          (conversation) => conversation.id === initialConversationId
        );

        if (existsInList) {
          targetConversationId = initialConversationId;
        }
      }

      if (!targetConversationId && fetched.length > 0) {
        targetConversationId = fetched[0].id;
      }

      if (!targetConversationId) {
        const created = await createConversationRequest(module, token);
        setConversations([created]);
        targetConversationId = created.id;
      }

      setSelectedConversationId(targetConversationId);

      const fetchedMessages = await getConversationMessages(
        targetConversationId,
        token
      );

      setMessages(fetchedMessages);
    } catch (error: any) {
      Alert.alert("Error", error?.message || "No se pudo cargar el chat.");
    } finally {
      setLoading(false);
    }
  };

  bootstrap();
}, [module, token, initialConversationId]);

  useEffect(() => {
    if (!token || !selectedConversationId) return;

    const loadMessages = async () => {
      try {
        const fetchedMessages = await getConversationMessages(
          selectedConversationId,
          token
        );
        setMessages(fetchedMessages);

        setTimeout(() => {
          scrollRef.current?.scrollToEnd({ animated: false });
        }, 120);
      } catch (error: any) {
        Alert.alert("Error", error?.message || "No se pudieron cargar los mensajes.");
      }
    };

    loadMessages();
  }, [selectedConversationId, token]);

  useEffect(() => {
    setTimeout(() => {
      scrollRef.current?.scrollToEnd({ animated: true });
    }, 120);
  }, [messages, sending]);

  const handleNewConversation = async () => {
    if (!token) return;

    try {
      const created = await createConversationRequest(module, token);
      setConversations([created, ...conversations]);
      setSelectedConversationId(created.id);
      setMessages([]);
      setInput("");
    } catch (error: any) {
      Alert.alert("Error", error?.message || "No se pudo crear la conversación.");
    }
  };

  const handleSend = async (forcedContent?: string) => {
    if (!token || !selectedConversationId) return;

    const content = (forcedContent ?? input).trim();

    if (!content) {
      return;
    }

    if (tokenStatus?.is_empty && !tokenStatus.is_unlimited) {
      Alert.alert(
        "Tokens agotados",
        tokenStatus.message || "Por ahora no tienes tokens disponibles. Revisa cuándo se reinician."
      );
      return;
    }

    try {
      setSending(true);

      if (!forcedContent) {
        setInput("");
      }

      const tempUserMessage: Message = {
        id: Date.now(),
        role: "user",
        content,
        created_at: new Date().toISOString(),
      };

      setMessages((prev) => [...prev, tempUserMessage]);

      const result = await sendMessageRequest(selectedConversationId, content, token);

      if (result.token_status) {
        setTokenStatus(result.token_status);
      }

      setMessages((prev) => [
        ...prev.filter((message) => message.id !== tempUserMessage.id),
        result.user_message,
        result.assistant_message,
      ]);

      const refreshed = await listConversations(module, token);
      setConversations(refreshed);
    } catch (error: any) {
      Alert.alert("Error", error?.message || "No se pudo enviar el mensaje.");
    } finally {
      setSending(false);
    }
  };

  if (loading) {
    return (
      <View style={styles.centered}>
        <ActivityIndicator size="large" color={theme.accent} />
        <Text style={styles.loadingText}>Cargando conversación...</Text>
      </View>
    );
  }

  return (
    <KeyboardAvoidingView
      style={styles.keyboardWrapper}
      behavior={Platform.OS === "ios" ? "padding" : undefined}
    >
      <View style={styles.screen}>
        <View style={styles.headerCard}>
          <View style={styles.headerTopRow}>
            <Animated.View style={{ transform: [{ translateY: floatAnim }] }}>
              <CompanionAvatar
                size={64}
                label={visibleCompanionName}
                profile={avatarProfile}
              />
            </Animated.View>

            <View style={styles.headerTextBlock}>
              <Text style={styles.headerTitle}>
                {title} · {visibleCompanionName}
              </Text>
              <Text style={styles.headerSubtitle}>{visibleSubtitle}</Text>
            </View>
          </View>

          <Pressable
            style={[styles.newChatButton, { backgroundColor: theme.accent }]}
            onPress={handleNewConversation}
          >
            <Ionicons name="add-circle-outline" size={18} color="#ffffff" />
            <Text style={styles.newChatButtonText}>Nuevo chat</Text>
          </Pressable>
        </View>

        {tokenStatus && !tokenStatus.is_unlimited && (
          <View
            style={[
              styles.tokenCard,
              tokenStatus.is_empty
                ? styles.tokenCardEmpty
                : tokenStatus.is_low
                ? styles.tokenCardLow
                : styles.tokenCardOk,
            ]}
          >
            <Ionicons
              name={tokenStatus.is_empty ? "pause-circle" : "flash"}
              size={18}
              color={tokenStatus.is_empty ? "#991b1b" : tokenStatus.is_low ? "#92400e" : "#1e3a8a"}
            />
            <View style={styles.tokenTextBlock}>
              <Text style={styles.tokenTitle}>
                Tokens: {tokenStatus.remaining_tokens} de {tokenStatus.daily_limit}
              </Text>
              <Text style={styles.tokenText}>
                {tokenStatus.is_empty
                  ? tokenStatus.message
                  : tokenStatus.is_low
                  ? tokenStatus.message
                  : `Se reinician en ${tokenStatus.reset_text}.`}
              </Text>
            </View>
          </View>
        )}

        {visibleExamples.length > 0 && (
          <ScrollView
            horizontal
            showsHorizontalScrollIndicator={false}
            style={styles.examplesRow}
            contentContainerStyle={styles.examplesRowContent}
          >
            {visibleExamples.map((example, index) => (
              <Pressable
                key={`${example}-${index}`}
                style={[
                  styles.exampleChip,
                  {
                    backgroundColor: theme.chipBackground,
                    borderColor: theme.chipBorder,
                  },
                ]}
                onPress={() => handleSend(example)}
                disabled={Boolean(tokenStatus?.is_empty && !tokenStatus.is_unlimited) || sending}
              >
                <Text
                  style={[
                    styles.exampleChipText,
                    { color: theme.chipText },
                  ]}
                >
                  {example}
                </Text>
              </Pressable>
            ))}
          </ScrollView>
        )}

        <ScrollView
          horizontal
          showsHorizontalScrollIndicator={false}
          style={styles.conversationsBar}
          contentContainerStyle={styles.conversationsContent}
        >
          {conversations.map((conversation) => {
            const isActive = conversation.id === selectedConversationId;

            return (
              <Pressable
                key={conversation.id}
                style={[
                  styles.conversationChip,
                  isActive
                    ? { backgroundColor: theme.accent }
                    : { backgroundColor: "#e9eef8" },
                ]}
                onPress={() => setSelectedConversationId(conversation.id)}
              >
                <Text
                  numberOfLines={1}
                  style={[
                    styles.conversationChipText,
                    isActive
                      ? styles.conversationChipTextActive
                      : styles.conversationChipTextInactive,
                  ]}
                >
                  {conversation.title}
                </Text>
              </Pressable>
            );
          })}
        </ScrollView>

        <ScrollView
          ref={scrollRef}
          style={styles.messagesArea}
          contentContainerStyle={styles.messagesContent}
          showsVerticalScrollIndicator={false}
        >
          {messages.length === 0 && (
            <View style={styles.emptyStateCard}>
              <CompanionAvatar
                size={54}
                label={visibleCompanionName}
                profile={avatarProfile}
              />

              <Text style={styles.emptyStateTitle}>
                {visibleCompanionName} está listo para hablar contigo
              </Text>

              <Text style={styles.emptyStateText}>
                Puedes escribir algo o usar uno de los ejemplos rápidos.
              </Text>
            </View>
          )}

          {messages.map((message) => {
            const isUser = message.role === "user";

            return (
              <View
                key={`${message.id}-${message.created_at}`}
                style={[
                  styles.messageWrapper,
                  isUser ? styles.userMessageWrapper : styles.assistantMessageWrapper,
                ]}
              >
                {!isUser && (
                  <View style={styles.assistantMetaRow}>
                    <CompanionAvatar
                      size={28}
                      label={visibleCompanionName}
                      showBadge={false}
                      profile={avatarProfile}
                    />
                    <Text style={styles.assistantNameText}>{visibleCompanionName}</Text>
                  </View>
                )}

                <View
                  style={[
                    styles.messageBubble,
                    isUser
                      ? [styles.userBubble, { backgroundColor: theme.userBubble }]
                      : [styles.assistantBubble, { backgroundColor: theme.assistantTint }],
                  ]}
                >
                  <Text
                    style={[
                      styles.messageText,
                      isUser ? styles.userMessageText : styles.assistantMessageText,
                    ]}
                  >
                    {message.content}
                  </Text>
                </View>
              </View>
            );
          })}

          {sending && (
            <View style={styles.assistantMessageWrapper}>
              <View style={styles.assistantMetaRow}>
                <CompanionAvatar
                  size={28}
                  label={visibleCompanionName}
                  showBadge={false}
                  profile={avatarProfile}
                />
                <Text style={styles.assistantNameText}>{visibleCompanionName}</Text>
              </View>

              <View
                style={[
                  styles.messageBubble,
                  styles.assistantBubble,
                  { backgroundColor: theme.assistantTint },
                ]}
              >
                <Text style={styles.assistantTypingText}>
                  {visibleCompanionName} está escribiendo{typingDots}
                </Text>
              </View>
            </View>
          )}
        </ScrollView>

        <View style={styles.inputCard}>
          <TextInput
            value={input}
            onChangeText={setInput}
            placeholder={
              tokenStatus?.is_empty && !tokenStatus.is_unlimited
                ? "Tus tokens se reiniciarán pronto..."
                : placeholder
            }
            placeholderTextColor="#8a94a6"
            style={styles.input}
            multiline
            editable={!sending && !(tokenStatus?.is_empty && !tokenStatus.is_unlimited)}
          />

          <View style={styles.inputFooter}>
            <Text style={[styles.inputHint, { color: theme.inputHint }]}>
              {module === "amigo_imaginario"
                ? `${visibleCompanionName} te escucha con ${user?.encouragement_style || "cariño"}.`
                : `Escribe con calma. ${visibleCompanionName} está aquí para ayudarte.`}
            </Text>

            <Pressable
              style={[
                styles.sendButton,
                { backgroundColor: theme.accent },
                (sending || (tokenStatus?.is_empty && !tokenStatus.is_unlimited)) &&
                  styles.sendButtonDisabled,
              ]}
              onPress={() => handleSend()}
              disabled={sending || Boolean(tokenStatus?.is_empty && !tokenStatus.is_unlimited)}
            >
              <Ionicons name="send" size={16} color="#ffffff" />
              <Text style={styles.sendButtonText}>Enviar</Text>
            </Pressable>
          </View>
        </View>
      </View>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  keyboardWrapper: {
    flex: 1,
    backgroundColor: "#f3f5f9",
  },
  screen: {
    flex: 1,
    backgroundColor: "#f3f5f9",
    paddingHorizontal: 16,
    paddingTop: 14,
    paddingBottom: 10,
  },
  centered: {
    flex: 1,
    backgroundColor: "#f3f5f9",
    justifyContent: "center",
    alignItems: "center",
    padding: 20,
  },
  loadingText: {
    marginTop: 12,
    color: "#526075",
    fontSize: 15,
  },
  tokenCard: {
    borderRadius: 16,
    padding: 12,
    marginBottom: 10,
    flexDirection: "row",
    alignItems: "flex-start",
    gap: 10,
    borderWidth: 1,
  },
  tokenCardOk: {
    backgroundColor: "#dbeafe",
    borderColor: "#bfdbfe",
  },
  tokenCardLow: {
    backgroundColor: "#fef3c7",
    borderColor: "#fde68a",
  },
  tokenCardEmpty: {
    backgroundColor: "#fee2e2",
    borderColor: "#fecaca",
  },
  tokenTextBlock: {
    flex: 1,
  },
  tokenTitle: {
    fontWeight: "800",
    color: "#0f172a",
    fontSize: 13,
  },
  tokenText: {
    marginTop: 3,
    color: "#475569",
    fontSize: 12,
    lineHeight: 17,
  },
  headerCard: {
    backgroundColor: "#ffffff",
    borderRadius: 22,
    padding: 16,
    marginBottom: 12,
    shadowColor: "#000",
    shadowOpacity: 0.06,
    shadowRadius: 10,
    shadowOffset: { width: 0, height: 5 },
    elevation: 3,
  },
  headerTopRow: {
    flexDirection: "row",
    alignItems: "center",
  },
  headerTextBlock: {
    flex: 1,
    marginLeft: 14,
  },
  headerTitle: {
    color: "#0f172a",
    fontSize: 18,
    fontWeight: "800",
  },
  headerSubtitle: {
    marginTop: 4,
    color: "#64748b",
    fontSize: 14,
    lineHeight: 20,
  },
  newChatButton: {
    marginTop: 14,
    alignSelf: "flex-start",
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
    paddingHorizontal: 14,
    paddingVertical: 11,
    borderRadius: 14,
  },
  newChatButtonText: {
    color: "#ffffff",
    fontWeight: "700",
    fontSize: 15,
  },
  examplesRow: {
    maxHeight: 52,
    marginBottom: 8,
  },
  examplesRowContent: {
    gap: 8,
    paddingRight: 10,
  },
  exampleChip: {
    borderRadius: 999,
    paddingHorizontal: 14,
    paddingVertical: 10,
    borderWidth: 1,
  },
  exampleChipText: {
    fontWeight: "700",
    fontSize: 13,
  },
  conversationsBar: {
    maxHeight: 48,
    marginBottom: 8,
  },
  conversationsContent: {
    gap: 8,
    paddingRight: 12,
  },
  conversationChip: {
    borderRadius: 999,
    paddingHorizontal: 14,
    paddingVertical: 10,
  },
  conversationChipText: {
    fontWeight: "600",
    maxWidth: 180,
  },
  conversationChipTextActive: {
    color: "#ffffff",
  },
  conversationChipTextInactive: {
    color: "#1f2937",
  },
  messagesArea: {
    flex: 1,
  },
  messagesContent: {
    paddingTop: 6,
    paddingBottom: 16,
  },
  emptyStateCard: {
    backgroundColor: "#ffffff",
    borderRadius: 20,
    padding: 18,
    alignItems: "center",
    marginBottom: 16,
    shadowColor: "#000",
    shadowOpacity: 0.05,
    shadowRadius: 8,
    shadowOffset: { width: 0, height: 4 },
    elevation: 2,
  },
  emptyStateTitle: {
    marginTop: 10,
    fontSize: 16,
    fontWeight: "800",
    color: "#0f172a",
    textAlign: "center",
  },
  emptyStateText: {
    marginTop: 6,
    color: "#64748b",
    textAlign: "center",
    lineHeight: 20,
  },
  messageWrapper: {
    marginBottom: 14,
  },
  userMessageWrapper: {
    alignItems: "flex-end",
  },
  assistantMessageWrapper: {
    alignItems: "flex-start",
  },
  assistantMetaRow: {
    flexDirection: "row",
    alignItems: "center",
    marginBottom: 6,
    paddingLeft: 2,
    gap: 8,
  },
  assistantNameText: {
    color: "#516076",
    fontWeight: "700",
    fontSize: 13,
  },
  messageBubble: {
    maxWidth: "84%",
    paddingHorizontal: 16,
    paddingVertical: 13,
    borderRadius: 20,
  },
  userBubble: {
    borderBottomRightRadius: 8,
  },
  assistantBubble: {
    borderBottomLeftRadius: 8,
    shadowColor: "#000",
    shadowOpacity: 0.04,
    shadowRadius: 6,
    shadowOffset: { width: 0, height: 3 },
    elevation: 1,
  },
  messageText: {
    fontSize: 16,
    lineHeight: 23,
  },
  userMessageText: {
    color: "#ffffff",
  },
  assistantMessageText: {
    color: "#101828",
  },
  assistantTypingText: {
    color: "#526075",
    fontSize: 15,
    fontStyle: "italic",
  },
  inputCard: {
    backgroundColor: "#ffffff",
    borderRadius: 22,
    padding: 14,
    marginTop: 8,
    shadowColor: "#000",
    shadowOpacity: 0.06,
    shadowRadius: 9,
    shadowOffset: { width: 0, height: 4 },
    elevation: 2,
  },
  input: {
    minHeight: 64,
    maxHeight: 130,
    color: "#111827",
    fontSize: 16,
    textAlignVertical: "top",
    paddingTop: 4,
  },
  inputFooter: {
    marginTop: 10,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    gap: 10,
  },
  inputHint: {
    flex: 1,
    fontSize: 12,
    lineHeight: 17,
  },
  sendButton: {
    paddingHorizontal: 16,
    paddingVertical: 11,
    borderRadius: 14,
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
  },
  sendButtonDisabled: {
    opacity: 0.6,
  },
  sendButtonText: {
    color: "#ffffff",
    fontWeight: "800",
    fontSize: 15,
  },
});
