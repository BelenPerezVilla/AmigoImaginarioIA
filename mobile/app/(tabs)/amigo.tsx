import { useEffect, useMemo, useState } from "react";
import {
  ActivityIndicator,
  Alert,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from "react-native";
import { useLocalSearchParams } from "expo-router";

import ChatModuleScreen from "../../src/components/ChatModuleScreen";
import FriendSettingsPanel from "../../src/components/FriendSettingsPanel";
import {
  type AdminUser,
  type SupportChild,
  adminListUsersRequest,
  getSupportChildrenRequest,
} from "../../src/lib/api";
import { useAuth } from "../../src/lib/auth";
import {
  canChatWithAmigo,
  canConfigureAmigo,
  isParent,
  isSuperadmin,
} from "../../src/lib/roleAccess";

type AmigoMode = "chat" | "configuracion";

export default function AmigoScreen() {
  const params = useLocalSearchParams();
  const { token, user } = useAuth();

  const initialConversationId = params.conversationId
    ? Number(params.conversationId)
    : null;

  const [mode, setMode] = useState<AmigoMode>(
    canChatWithAmigo(user) ? "chat" : "configuracion"
  );

  const [loadingTargets, setLoadingTargets] = useState(false);
  const [children, setChildren] = useState<SupportChild[]>([]);
  const [adminChildren, setAdminChildren] = useState<AdminUser[]>([]);
  const [selectedChildId, setSelectedChildId] = useState<number | null>(null);

  const showChat = canChatWithAmigo(user);
  const showConfig = canConfigureAmigo(user);

  const configTargets = useMemo(() => {
    if (isSuperadmin(user)) {
      return adminChildren
        .filter((item) => ["child", "guest_child"].includes(item.role))
        .map((item) => ({
          id: item.id,
          display_name: item.display_name,
          username: item.username,
        }));
    }

    return children.map((item) => ({
      id: item.id,
      display_name: item.display_name,
      username: item.username,
    }));
  }, [user, adminChildren, children]);

  const selectedTarget = useMemo(() => {
    return configTargets.find((item) => item.id === selectedChildId) || null;
  }, [configTargets, selectedChildId]);

  const loadConfigTargets = async () => {
    if (!token || !showConfig) return;

    try {
      setLoadingTargets(true);

      if (isSuperadmin(user)) {
        const users = await adminListUsersRequest(token);
        setAdminChildren(users);
        const firstChild = users.find((item) =>
          ["child", "guest_child"].includes(item.role)
        );
        setSelectedChildId((prev) => prev || firstChild?.id || null);
        return;
      }

      if (isParent(user)) {
        const linkedChildren = await getSupportChildrenRequest(token);
        setChildren(linkedChildren);
        setSelectedChildId((prev) => prev || linkedChildren[0]?.id || null);
      }
    } catch (error: any) {
      Alert.alert(
        "Error",
        error?.message || "No se pudieron cargar los usuarios configurables."
      );
    } finally {
      setLoadingTargets(false);
    }
  };

  useEffect(() => {
    if (showConfig) {
      loadConfigTargets();
    }
  }, [token, user?.role]);

  if (!showChat && !showConfig) {
    return (
      <View style={styles.centered}>
        <Text style={styles.centerTitle}>Sin permiso</Text>
        <Text style={styles.centerText}>
          Tu cuenta no tiene acceso al módulo Amigo Imaginario.
        </Text>
      </View>
    );
  }

  if (showChat && !showConfig) {
    return (
      <ChatModuleScreen
        module="amigo_imaginario"
        title="Amigo Imaginario"
        placeholder="Escribe lo que sientes o lo que quieras contar..."
        companionName="Lumi"
        companionSubtitle="Conversa con calma, juega suavemente y siente compañía."
        avatarVariant="lumi"
        initialConversationId={initialConversationId}
        quickExamples={[
          "Hola Lumi",
          "Hoy me siento triste",
          "Cuéntame un cuento corto",
          "Quiero un juego tranquilo",
        ]}
      />
    );
  }

  if (showConfig && !showChat) {
    return (
      <View style={styles.flex}>
        <View style={styles.header}>
          <Text style={styles.title}>Mi amigo</Text>
          <Text style={styles.subtitle}>
            Configura el amigo imaginario del niño vinculado.
          </Text>
        </View>

        {loadingTargets ? (
          <View style={styles.centered}>
            <ActivityIndicator size="large" color="#2f64b9" />
            <Text style={styles.centerText}>Cargando niños vinculados...</Text>
          </View>
        ) : configTargets.length === 0 ? (
          <View style={styles.centered}>
            <Text style={styles.centerTitle}>Sin niños vinculados</Text>
            <Text style={styles.centerText}>
              El superadmin debe vincular esta cuenta de padre con una cuenta de niño.
            </Text>
          </View>
        ) : (
          <>
            <ScrollView
              horizontal
              showsHorizontalScrollIndicator={false}
              style={styles.childrenRow}
              contentContainerStyle={styles.childrenContent}
            >
              {configTargets.map((child) => {
                const active = selectedChildId === child.id;

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

            <FriendSettingsPanel
              targetUserId={selectedChildId}
              targetName={selectedTarget?.display_name}
            />
          </>
        )}
      </View>
    );
  }

  return (
    <View style={styles.flex}>
      <View style={styles.modeTabs}>
        <Pressable
          style={[styles.modeTab, mode === "chat" && styles.modeTabActive]}
          onPress={() => setMode("chat")}
        >
          <Text
            style={[
              styles.modeTabText,
              mode === "chat" && styles.modeTabTextActive,
            ]}
          >
            Chat
          </Text>
        </Pressable>

        <Pressable
          style={[
            styles.modeTab,
            mode === "configuracion" && styles.modeTabActive,
          ]}
          onPress={() => setMode("configuracion")}
        >
          <Text
            style={[
              styles.modeTabText,
              mode === "configuracion" && styles.modeTabTextActive,
            ]}
          >
            Configuración
          </Text>
        </Pressable>
      </View>

      {mode === "chat" ? (
        <ChatModuleScreen
          module="amigo_imaginario"
          title="Amigo Imaginario"
          placeholder="Escribe lo que sientes o lo que quieras contar..."
          companionName="Lumi"
          companionSubtitle="Conversa con calma, juega suavemente y siente compañía."
          avatarVariant="lumi"
          initialConversationId={initialConversationId}
          quickExamples={[
            "Hola Lumi",
            "Hoy me siento triste",
            "Cuéntame un cuento corto",
            "Quiero un juego tranquilo",
          ]}
        />
      ) : loadingTargets ? (
        <View style={styles.centered}>
          <ActivityIndicator size="large" color="#2f64b9" />
          <Text style={styles.centerText}>Cargando usuarios...</Text>
        </View>
      ) : (
        <>
          <ScrollView
            horizontal
            showsHorizontalScrollIndicator={false}
            style={styles.childrenRow}
            contentContainerStyle={styles.childrenContent}
          >
            {configTargets.map((child) => {
              const active = selectedChildId === child.id;

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

          <FriendSettingsPanel
            targetUserId={selectedChildId}
            targetName={selectedTarget?.display_name}
          />
        </>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  flex: {
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
  centerTitle: {
    color: "#0f172a",
    fontWeight: "900",
    fontSize: 20,
  },
  centerText: {
    color: "#64748b",
    textAlign: "center",
    lineHeight: 20,
    marginTop: 8,
  },
  header: {
    backgroundColor: "#ffffff",
    padding: 18,
    borderBottomWidth: 1,
    borderBottomColor: "#e2e8f0",
  },
  title: {
    color: "#0f172a",
    fontSize: 22,
    fontWeight: "900",
  },
  subtitle: {
    color: "#64748b",
    marginTop: 6,
    lineHeight: 20,
  },
  modeTabs: {
    flexDirection: "row",
    backgroundColor: "#ffffff",
    padding: 8,
    gap: 8,
  },
  modeTab: {
    flex: 1,
    backgroundColor: "#e9eef8",
    borderRadius: 14,
    paddingVertical: 11,
    alignItems: "center",
  },
  modeTabActive: {
    backgroundColor: "#2f64b9",
  },
  modeTabText: {
    color: "#334155",
    fontWeight: "900",
  },
  modeTabTextActive: {
    color: "#ffffff",
  },
  childrenRow: {
    backgroundColor: "#ffffff",
    maxHeight: 58,
  },
  childrenContent: {
    padding: 10,
    gap: 8,
  },
  childChip: {
    backgroundColor: "#e9eef8",
    borderRadius: 999,
    paddingHorizontal: 14,
    paddingVertical: 10,
  },
  childChipActive: {
    backgroundColor: "#2f64b9",
  },
  childChipText: {
    color: "#334155",
    fontWeight: "900",
  },
  childChipTextActive: {
    color: "#ffffff",
  },
});