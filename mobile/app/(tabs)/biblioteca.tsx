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
import { useRouter } from "expo-router";

import {
  type Article,
  addFavoriteArticleRequest,
  getArticleById,
  listArticles,
  listFavoriteArticles,
  removeFavoriteArticleRequest,
  sendArticleToChatRequest,
} from "../../src/lib/api";
import { useAuth } from "../../src/lib/auth";
import {
  canSeeBiblioteca,
  isBibliotecaReadOnly,
} from "../../src/lib/roleAccess";

const CATEGORY_OPTIONS = [
  "Todas",
  "General",
  "Emociones",
  "Comunicación",
  "Rutinas",
  "Crisis",
  "Neurodivergencia",
  "Padres",
];

const READER_OPTIONS = ["Todos", "Niños", "Padres"];

function normalizeText(value: string): string {
  return String(value || "").trim();
}

function ArticleCard({
  article,
  isFavorite,
  onOpen,
  onToggleFavorite,
  showFavoriteButton = true,
}: {
  article: Article;
  isFavorite: boolean;
  onOpen: (articleId: number) => void;
  onToggleFavorite: (articleId: number, nextState: boolean) => void;
  showFavoriteButton?: boolean;
}) {
  return (
    <Pressable style={styles.articleCard} onPress={() => onOpen(article.id)}>
      <View style={styles.articleHeader}>
        <View style={styles.articleTitleBlock}>
          <Text style={styles.articleTitle}>{article.title}</Text>

          <View style={styles.badgesRow}>
            {!!article.category && (
              <Text style={styles.badge}>{article.category}</Text>
            )}

            {!!article.reader_type && (
              <Text style={styles.badgeSecondary}>{article.reader_type}</Text>
            )}
          </View>
        </View>

        {showFavoriteButton && (
          <Pressable
            style={styles.favoriteIconButton}
            onPress={() => onToggleFavorite(article.id, !isFavorite)}
          >
            <Ionicons
              name={isFavorite ? "heart" : "heart-outline"}
              size={21}
              color={isFavorite ? "#e6527a" : "#64748b"}
            />
          </Pressable>
        )}
      </View>

      {!!article.short_description && (
        <Text style={styles.articleDescription} numberOfLines={3}>
          {article.short_description}
        </Text>
      )}

      <Text style={styles.openArticleText}>Tocar para leer</Text>
    </Pressable>
  );
}

export default function BibliotecaScreen() {
  const router = useRouter();
  const { token, user } = useAuth();

  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const [articles, setArticles] = useState<Article[]>([]);
  const [favoriteIds, setFavoriteIds] = useState<number[]>([]);

  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("Todas");
  const [readerType, setReaderType] = useState("Todos");

  const [selectedArticle, setSelectedArticle] = useState<Article | null>(null);
  const [articleModalVisible, setArticleModalVisible] = useState(false);

  const [actionLoading, setActionLoading] = useState(false);

  const canAccessLibrary = canSeeBiblioteca(user);
  const readOnlyMode = isBibliotecaReadOnly(user);

  const filteredArticles = useMemo(() => {
    return articles;
  }, [articles]);

  const loadData = async () => {
    if (!token || !canAccessLibrary) {
      setLoading(false);
      return;
    }

    try {
      setLoading(true);

      const articlesData = await listArticles(
        token,
        normalizeText(search),
        category,
        readerType
      );

      setArticles(articlesData);

      if (!readOnlyMode) {
        const favoritesData = await listFavoriteArticles(token);
        setFavoriteIds(favoritesData.map((item) => item.id));
      } else {
        setFavoriteIds([]);
      }
    } catch (error: any) {
      Alert.alert(
        "Error",
        error?.message || "No se pudo cargar la biblioteca."
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
  }, [token, canAccessLibrary, readOnlyMode]);

  const handleSearch = async () => {
    await loadData();
  };

  const handleOpenArticle = async (articleId: number) => {
    if (!token) return;

    try {
      setActionLoading(true);

      const article = await getArticleById(token, articleId);
      setSelectedArticle(article);
      setArticleModalVisible(true);
    } catch (error: any) {
      Alert.alert(
        "Error",
        error?.message || "No se pudo abrir el artículo."
      );
    } finally {
      setActionLoading(false);
    }
  };

  const handleToggleFavorite = async (
    articleId: number,
    nextState: boolean
  ) => {
    if (!token) return;

    if (readOnlyMode) {
      return;
    }

    try {
      setActionLoading(true);

      if (nextState) {
        await addFavoriteArticleRequest(token, articleId);
        setFavoriteIds((prev) => [...new Set([...prev, articleId])]);
      } else {
        await removeFavoriteArticleRequest(token, articleId);
        setFavoriteIds((prev) => prev.filter((id) => id !== articleId));
      }
    } catch (error: any) {
      Alert.alert(
        "Error",
        error?.message || "No se pudo actualizar favoritos."
      );
    } finally {
      setActionLoading(false);
    }
  };

  const handleSendToFriend = async () => {
    if (!token || !selectedArticle) return;

    if (readOnlyMode) {
      return;
    }

    try {
      setActionLoading(true);

      const result = await sendArticleToChatRequest(token, selectedArticle.id);

      setArticleModalVisible(false);
      setSelectedArticle(null);

      Alert.alert(
        "Listo",
        "El artículo fue enviado al chat del Amigo Imaginario."
      );

      router.push({
        pathname: "/(tabs)/amigo",
        params: {
          conversationId: String(result.conversation_id),
        },
      });
    } catch (error: any) {
      Alert.alert(
        "Error",
        error?.message || "No se pudo enviar el artículo al chat."
      );
    } finally {
      setActionLoading(false);
    }
  };

  if (!canAccessLibrary) {
    return (
      <View style={styles.centered}>
        <Ionicons name="lock-closed-outline" size={42} color="#64748b" />
        <Text style={styles.emptyTitle}>Sin permiso</Text>
        <Text style={styles.emptyText}>
          Tu cuenta no tiene acceso a la Biblioteca Inteligente.
        </Text>
      </View>
    );
  }

  if (loading) {
    return (
      <View style={styles.centered}>
        <ActivityIndicator size="large" color="#2f64b9" />
        <Text style={styles.loadingText}>Cargando biblioteca...</Text>
      </View>
    );
  }

  return (
    <View style={styles.screen}>
      <ScrollView
        contentContainerStyle={styles.content}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={refreshData} />
        }
      >
        <View style={styles.heroCard}>
          <Text style={styles.heroTitle}>Biblioteca Inteligente</Text>

          <Text style={styles.heroText}>
            {readOnlyMode
              ? "Consulta artículos y material de apoyo. Tu cuenta de padre está en modo solo lectura."
              : "Explora artículos, guarda favoritos y envía contenido al chat educativo."}
          </Text>

          {readOnlyMode && (
            <View style={styles.readOnlyBadge}>
              <Ionicons name="eye-outline" size={16} color="#ffffff" />
              <Text style={styles.readOnlyBadgeText}>Solo lectura</Text>
            </View>
          )}
        </View>

        <View style={styles.filterCard}>
          <Text style={styles.label}>Buscar artículo</Text>

          <View style={styles.searchRow}>
            <TextInput
              style={styles.searchInput}
              value={search}
              onChangeText={setSearch}
              placeholder="Buscar por tema, palabra clave..."
              placeholderTextColor="#94a3b8"
              returnKeyType="search"
              onSubmitEditing={handleSearch}
            />

            <Pressable
              style={styles.searchButton}
              onPress={handleSearch}
              disabled={actionLoading}
            >
              <Ionicons name="search" size={18} color="#ffffff" />
            </Pressable>
          </View>

          <Text style={styles.label}>Categoría</Text>

          <ScrollView
            horizontal
            showsHorizontalScrollIndicator={false}
            style={styles.chipsRow}
            contentContainerStyle={styles.chipsContent}
          >
            {CATEGORY_OPTIONS.map((item) => {
              const active = category === item;

              return (
                <Pressable
                  key={item}
                  style={[styles.chip, active && styles.chipActive]}
                  onPress={() => setCategory(item)}
                >
                  <Text
                    style={[
                      styles.chipText,
                      active && styles.chipTextActive,
                    ]}
                  >
                    {item}
                  </Text>
                </Pressable>
              );
            })}
          </ScrollView>

          <Text style={styles.label}>Tipo de lector</Text>

          <ScrollView
            horizontal
            showsHorizontalScrollIndicator={false}
            style={styles.chipsRow}
            contentContainerStyle={styles.chipsContent}
          >
            {READER_OPTIONS.map((item) => {
              const active = readerType === item;

              return (
                <Pressable
                  key={item}
                  style={[styles.chip, active && styles.chipActive]}
                  onPress={() => setReaderType(item)}
                >
                  <Text
                    style={[
                      styles.chipText,
                      active && styles.chipTextActive,
                    ]}
                  >
                    {item}
                  </Text>
                </Pressable>
              );
            })}
          </ScrollView>

          <Pressable style={styles.applyButton} onPress={handleSearch}>
            <Text style={styles.applyButtonText}>Aplicar filtros</Text>
          </Pressable>
        </View>

        <View style={styles.sectionHeader}>
          <Text style={styles.sectionTitle}>Artículos</Text>
          <Text style={styles.sectionCounter}>
            {filteredArticles.length} resultado(s)
          </Text>
        </View>

        {filteredArticles.length === 0 ? (
          <View style={styles.emptyCard}>
            <Ionicons name="document-text-outline" size={38} color="#94a3b8" />
            <Text style={styles.emptyTitle}>Sin artículos</Text>
            <Text style={styles.emptyText}>
              No se encontraron artículos con los filtros seleccionados.
            </Text>
          </View>
        ) : (
          filteredArticles.map((article) => (
            <ArticleCard
              key={article.id}
              article={article}
              isFavorite={favoriteIds.includes(article.id)}
              onOpen={handleOpenArticle}
              onToggleFavorite={handleToggleFavorite}
              showFavoriteButton={!readOnlyMode}
            />
          ))
        )}
      </ScrollView>

      <Modal
        visible={articleModalVisible}
        animationType="slide"
        transparent
        onRequestClose={() => setArticleModalVisible(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.modalCard}>
            <View style={styles.modalHeader}>
              <View style={styles.modalTitleBlock}>
                <Text style={styles.modalTitle}>
                  {selectedArticle?.title || "Artículo"}
                </Text>

                <View style={styles.badgesRow}>
                  {!!selectedArticle?.category && (
                    <Text style={styles.badge}>{selectedArticle.category}</Text>
                  )}

                  {!!selectedArticle?.reader_type && (
                    <Text style={styles.badgeSecondary}>
                      {selectedArticle.reader_type}
                    </Text>
                  )}
                </View>
              </View>

              <Pressable
                style={styles.closeButton}
                onPress={() => setArticleModalVisible(false)}
              >
                <Ionicons name="close" size={24} color="#0f172a" />
              </Pressable>
            </View>

            <ScrollView
              showsVerticalScrollIndicator={false}
              contentContainerStyle={styles.modalContent}
            >
              {!!selectedArticle?.short_description && (
                <Text style={styles.modalDescription}>
                  {selectedArticle.short_description}
                </Text>
              )}

              <Text style={styles.articleContent}>
                {selectedArticle?.content || ""}
              </Text>

              {readOnlyMode && (
                <View style={styles.noticeBox}>
                  <Ionicons
                    name="information-circle-outline"
                    size={20}
                    color="#2f64b9"
                  />
                  <Text style={styles.noticeText}>
                    Estás viendo este artículo en modo solo lectura.
                  </Text>
                </View>
              )}

              {!readOnlyMode && selectedArticle && (
                <>
                  <Pressable
                    style={[
                      styles.favoriteButton,
                      actionLoading && styles.disabledButton,
                    ]}
                    onPress={() =>
                      handleToggleFavorite(
                        selectedArticle.id,
                        !favoriteIds.includes(selectedArticle.id)
                      )
                    }
                    disabled={actionLoading}
                  >
                    <Ionicons
                      name={
                        favoriteIds.includes(selectedArticle.id)
                          ? "heart"
                          : "heart-outline"
                      }
                      size={18}
                      color="#ffffff"
                    />
                    <Text style={styles.favoriteButtonText}>
                      {favoriteIds.includes(selectedArticle.id)
                        ? "Quitar de favoritos"
                        : "Guardar en favoritos"}
                    </Text>
                  </Pressable>

                  <Pressable
                    style={[
                      styles.sendToChatButton,
                      actionLoading && styles.disabledButton,
                    ]}
                    onPress={handleSendToFriend}
                    disabled={actionLoading}
                  >
                    <Ionicons
                      name="chatbubble-ellipses-outline"
                      size={18}
                      color="#ffffff"
                    />
                    <Text style={styles.sendToChatButtonText}>
                      Llevar al chat educativo
                    </Text>
                  </Pressable>
                </>
              )}
            </ScrollView>
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
  content: {
    padding: 16,
    paddingBottom: 32,
  },
  centered: {
    flex: 1,
    backgroundColor: "#f5f7fb",
    justifyContent: "center",
    alignItems: "center",
    padding: 22,
  },
  loadingText: {
    color: "#64748b",
    marginTop: 10,
  },
  heroCard: {
    backgroundColor: "#2f64b9",
    borderRadius: 22,
    padding: 20,
    marginBottom: 14,
  },
  heroTitle: {
    color: "#ffffff",
    fontSize: 24,
    fontWeight: "900",
  },
  heroText: {
    color: "#dbeafe",
    marginTop: 8,
    lineHeight: 20,
  },
  readOnlyBadge: {
    alignSelf: "flex-start",
    flexDirection: "row",
    alignItems: "center",
    gap: 7,
    backgroundColor: "rgba(255,255,255,0.18)",
    borderRadius: 999,
    paddingHorizontal: 12,
    paddingVertical: 7,
    marginTop: 12,
  },
  readOnlyBadgeText: {
    color: "#ffffff",
    fontWeight: "900",
  },
  filterCard: {
    backgroundColor: "#ffffff",
    borderRadius: 18,
    padding: 16,
    marginBottom: 14,
  },
  label: {
    color: "#334155",
    fontWeight: "900",
    marginBottom: 8,
    marginTop: 6,
  },
  searchRow: {
    flexDirection: "row",
    gap: 8,
    marginBottom: 10,
  },
  searchInput: {
    flex: 1,
    backgroundColor: "#f8fafc",
    borderRadius: 14,
    paddingHorizontal: 14,
    paddingVertical: 12,
    color: "#0f172a",
  },
  searchButton: {
    width: 48,
    borderRadius: 14,
    backgroundColor: "#2f64b9",
    justifyContent: "center",
    alignItems: "center",
  },
  chipsRow: {
    maxHeight: 44,
    marginBottom: 8,
  },
  chipsContent: {
    gap: 8,
    paddingRight: 10,
  },
  chip: {
    backgroundColor: "#e9eef8",
    borderRadius: 999,
    paddingHorizontal: 13,
    paddingVertical: 9,
  },
  chipActive: {
    backgroundColor: "#2f64b9",
  },
  chipText: {
    color: "#334155",
    fontWeight: "800",
    fontSize: 12,
  },
  chipTextActive: {
    color: "#ffffff",
  },
  applyButton: {
    backgroundColor: "#0f172a",
    borderRadius: 14,
    paddingVertical: 13,
    alignItems: "center",
    marginTop: 8,
  },
  applyButtonText: {
    color: "#ffffff",
    fontWeight: "900",
  },
  sectionHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 10,
  },
  sectionTitle: {
    color: "#0f172a",
    fontSize: 19,
    fontWeight: "900",
  },
  sectionCounter: {
    color: "#64748b",
    fontWeight: "700",
  },
  articleCard: {
    backgroundColor: "#ffffff",
    borderRadius: 18,
    padding: 16,
    marginBottom: 12,
  },
  articleHeader: {
    flexDirection: "row",
    gap: 10,
    alignItems: "flex-start",
  },
  articleTitleBlock: {
    flex: 1,
  },
  articleTitle: {
    color: "#0f172a",
    fontSize: 17,
    fontWeight: "900",
    lineHeight: 22,
  },
  badgesRow: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 7,
    marginTop: 8,
  },
  badge: {
    backgroundColor: "#dbeafe",
    color: "#1e3a8a",
    borderRadius: 999,
    overflow: "hidden",
    paddingHorizontal: 10,
    paddingVertical: 5,
    fontSize: 12,
    fontWeight: "800",
  },
  badgeSecondary: {
    backgroundColor: "#f1f5f9",
    color: "#475569",
    borderRadius: 999,
    overflow: "hidden",
    paddingHorizontal: 10,
    paddingVertical: 5,
    fontSize: 12,
    fontWeight: "800",
  },
  favoriteIconButton: {
    backgroundColor: "#f8fafc",
    borderRadius: 999,
    padding: 9,
  },
  articleDescription: {
    color: "#64748b",
    marginTop: 10,
    lineHeight: 20,
  },
  openArticleText: {
    color: "#2f64b9",
    fontWeight: "900",
    marginTop: 12,
  },
  emptyCard: {
    backgroundColor: "#ffffff",
    borderRadius: 18,
    padding: 22,
    alignItems: "center",
  },
  emptyTitle: {
    color: "#0f172a",
    fontSize: 19,
    fontWeight: "900",
    marginTop: 10,
    textAlign: "center",
  },
  emptyText: {
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
    maxHeight: "90%",
  },
  modalHeader: {
    flexDirection: "row",
    alignItems: "flex-start",
    gap: 10,
    marginBottom: 10,
  },
  modalTitleBlock: {
    flex: 1,
  },
  modalTitle: {
    color: "#0f172a",
    fontSize: 20,
    fontWeight: "900",
    lineHeight: 25,
  },
  closeButton: {
    backgroundColor: "#f8fafc",
    borderRadius: 999,
    padding: 8,
  },
  modalContent: {
    paddingBottom: 18,
  },
  modalDescription: {
    color: "#475569",
    lineHeight: 21,
    marginBottom: 14,
    fontWeight: "700",
  },
  articleContent: {
    color: "#0f172a",
    fontSize: 15,
    lineHeight: 23,
  },
  noticeBox: {
    backgroundColor: "#eff6ff",
    borderRadius: 14,
    padding: 13,
    marginTop: 18,
    flexDirection: "row",
    alignItems: "flex-start",
    gap: 9,
  },
  noticeText: {
    flex: 1,
    color: "#1e3a8a",
    lineHeight: 19,
    fontWeight: "700",
  },
  favoriteButton: {
    backgroundColor: "#e6527a",
    borderRadius: 14,
    paddingVertical: 14,
    alignItems: "center",
    justifyContent: "center",
    marginTop: 18,
    flexDirection: "row",
    gap: 8,
  },
  favoriteButtonText: {
    color: "#ffffff",
    fontWeight: "900",
  },
  sendToChatButton: {
    backgroundColor: "#2f64b9",
    borderRadius: 14,
    paddingVertical: 14,
    alignItems: "center",
    justifyContent: "center",
    marginTop: 10,
    flexDirection: "row",
    gap: 8,
  },
  sendToChatButtonText: {
    color: "#ffffff",
    fontWeight: "900",
  },
  disabledButton: {
    opacity: 0.55,
  },
});