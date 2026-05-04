import { useEffect, useMemo, useState } from "react";
import {
  ActivityIndicator,
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
  addFavoriteArticleRequest,
  type Article,
  getArticleById,
  listArticles,
  listFavoriteArticles,
  removeFavoriteArticleRequest,
  sendArticleToChatRequest,
} from "../../src/lib/api";
import { useAuth } from "../../src/lib/auth";

// ------------------------------------------------------------
// Obtener icono según categoría del artículo
// ------------------------------------------------------------
function getCategoryIcon(category: string): keyof typeof Ionicons.glyphMap {
  const value = String(category || "").toLowerCase();

  if (value.includes("tdah")) return "flash-outline";
  if (value.includes("aut")) return "planet-outline";
  if (value.includes("dislexia")) return "book-outline";
  if (value.includes("ansiedad")) return "leaf-outline";
  if (value.includes("famil")) return "people-outline";
  if (value.includes("escuela")) return "school-outline";

  return "library-outline";
}

// ------------------------------------------------------------
// Obtener color suave según tipo de lector
// ------------------------------------------------------------
function getReaderColors(readerType: string) {
  const value = String(readerType || "").toLowerCase();

  if (value.includes("padre") || value.includes("cuidador")) {
    return { bg: "#e8f4ff", text: "#2f64b9" };
  }

  if (value.includes("docente")) {
    return { bg: "#eaf8ef", text: "#2e8b57" };
  }

  return { bg: "#f3edff", text: "#6d46c2" };
}

// ------------------------------------------------------------
// Tarjeta visual de artículo
// ------------------------------------------------------------
function ArticleCard({
  article,
  isFavorite,
  onOpen,
  onToggleFavorite,
}: {
  article: Article;
  isFavorite: boolean;
  onOpen: (articleId: number) => void;
  onToggleFavorite: (articleId: number, nextState: boolean) => void;
}) {
  const iconName = getCategoryIcon(article.category);
  const readerColors = getReaderColors(article.reader_type);

  return (
    <Pressable style={styles.articleCard} onPress={() => onOpen(article.id)}>
      <View style={styles.articleHeaderRow}>
        <View style={styles.articleIconCircle}>
          <Ionicons name={iconName} size={20} color="#2f64b9" />
        </View>

        <View style={styles.articleHeaderText}>
          <Text style={styles.articleTitle} numberOfLines={2}>
            {article.title}
          </Text>

          <Text style={styles.articleCategory} numberOfLines={1}>
            {article.category}
          </Text>
        </View>

        <Pressable
          style={styles.favoriteIconButton}
          onPress={() => onToggleFavorite(article.id, !isFavorite)}
        >
          <Ionicons
            name={isFavorite ? "heart" : "heart-outline"}
            size={20}
            color={isFavorite ? "#e6527a" : "#64748b"}
          />
        </Pressable>
      </View>

      <Text style={styles.articleDescription} numberOfLines={3}>
        {article.short_description}
      </Text>

      <View style={styles.articleFooterRow}>
        <View
          style={[
            styles.readerBadge,
            { backgroundColor: readerColors.bg },
          ]}
        >
          <Text
            style={[
              styles.readerBadgeText,
              { color: readerColors.text },
            ]}
          >
            {article.reader_type}
          </Text>
        </View>

        <View style={styles.openRow}>
          <Text style={styles.openText}>Abrir</Text>
          <Ionicons name="chevron-forward" size={16} color="#2f64b9" />
        </View>
      </View>
    </Pressable>
  );
}

export default function BibliotecaScreen() {
  const router = useRouter();
  const { token } = useAuth();

  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);

  const [searchText, setSearchText] = useState("");
  const [articles, setArticles] = useState<Article[]>([]);
  const [favoriteIds, setFavoriteIds] = useState<number[]>([]);
  const [selectedArticle, setSelectedArticle] = useState<Article | null>(null);
  const [detailVisible, setDetailVisible] = useState(false);

  const [selectedCategory, setSelectedCategory] = useState("Todas");
  const [selectedReaderType, setSelectedReaderType] = useState("Todos");
  const [viewMode, setViewMode] = useState<"todos" | "favoritos">("todos");

  // ----------------------------------------------------------
  // Cargar artículos
  // ----------------------------------------------------------
  const loadArticles = async () => {
    if (!token) return;

    const fetched = await listArticles(
      token,
      searchText.trim(),
      "Todas",
      "Todos"
    );

    setArticles(fetched);
  };

  // ----------------------------------------------------------
  // Cargar favoritos
  // ----------------------------------------------------------
  const loadFavorites = async () => {
    if (!token) return;

    const favorites = await listFavoriteArticles(token);
    setFavoriteIds(favorites.map((item) => item.id));
  };

  // ----------------------------------------------------------
  // Carga inicial
  // ----------------------------------------------------------
  const bootstrap = async () => {
    if (!token) return;

    try {
      setLoading(true);
      await Promise.all([loadArticles(), loadFavorites()]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    bootstrap();
  }, [token]);

  // ----------------------------------------------------------
  // Recarga manual
  // ----------------------------------------------------------
  const handleRefresh = async () => {
    if (!token) return;

    try {
      setRefreshing(true);
      await Promise.all([loadArticles(), loadFavorites()]);
    } finally {
      setRefreshing(false);
    }
  };

  // ----------------------------------------------------------
  // Categorías disponibles
  // ----------------------------------------------------------
  const categories = useMemo(() => {
    const values = Array.from(
      new Set(
        articles
          .map((item) => item.category?.trim())
          .filter(Boolean)
      )
    );

    return ["Todas", ...values];
  }, [articles]);

  // ----------------------------------------------------------
  // Tipos de lector disponibles
  // ----------------------------------------------------------
  const readerTypes = useMemo(() => {
    const values = Array.from(
      new Set(
        articles
          .map((item) => item.reader_type?.trim())
          .filter(Boolean)
      )
    );

    return ["Todos", ...values];
  }, [articles]);

  // ----------------------------------------------------------
  // Aplicar filtros visuales
  // ----------------------------------------------------------
  const filteredArticles = useMemo(() => {
    return articles.filter((article) => {
      const matchesCategory =
        selectedCategory === "Todas" ||
        article.category === selectedCategory;

      const matchesReader =
        selectedReaderType === "Todos" ||
        article.reader_type === selectedReaderType;

      const text = searchText.trim().toLowerCase();

      const matchesSearch =
        !text ||
        article.title.toLowerCase().includes(text) ||
        article.short_description.toLowerCase().includes(text) ||
        article.category.toLowerCase().includes(text) ||
        article.reader_type.toLowerCase().includes(text);

      const matchesFavorite =
        viewMode === "todos" || favoriteIds.includes(article.id);

      return matchesCategory && matchesReader && matchesSearch && matchesFavorite;
    });
  }, [
    articles,
    selectedCategory,
    selectedReaderType,
    searchText,
    viewMode,
    favoriteIds,
  ]);

  const featuredArticle = useMemo(() => {
    return filteredArticles.length > 0 ? filteredArticles[0] : null;
  }, [filteredArticles]);

  // ----------------------------------------------------------
  // Abrir detalle de artículo
  // ----------------------------------------------------------
  const handleOpenArticle = async (articleId: number) => {
    if (!token) return;

    const detail = await getArticleById(token, articleId);
    setSelectedArticle(detail);
    setDetailVisible(true);
  };

  // ----------------------------------------------------------
  // Guardar o quitar favorito
  // ----------------------------------------------------------
  const handleToggleFavorite = async (articleId: number, nextState: boolean) => {
    if (!token) return;

    try {
      setActionLoading(true);

      if (nextState) {
        await addFavoriteArticleRequest(token, articleId);
        setFavoriteIds((prev) => Array.from(new Set([...prev, articleId])));
      } else {
        await removeFavoriteArticleRequest(token, articleId);
        setFavoriteIds((prev) => prev.filter((id) => id !== articleId));
      }
    } finally {
      setActionLoading(false);
    }
  };

  // ----------------------------------------------------------
  // Mandar artículo al chat del Amigo
  // ----------------------------------------------------------
  const handleSendToFriend = async () => {
    if (!token || !selectedArticle) return;

    try {
      setActionLoading(true);

      const result = await sendArticleToChatRequest(token, selectedArticle.id);

      setDetailVisible(false);

      router.push({
        pathname: "/(tabs)/amigo",
        params: {
          conversationId: String(result.conversation_id),
          refresh: String(Date.now()),
        },
      });
    } finally {
      setActionLoading(false);
    }
  };

  if (loading) {
    return (
      <View style={styles.centered}>
        <ActivityIndicator size="large" color="#2f64b9" />
        <Text style={styles.loadingText}>Cargando biblioteca...</Text>
      </View>
    );
  }

  return (
    <>
      <ScrollView
        style={styles.screen}
        contentContainerStyle={styles.content}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={handleRefresh} />
        }
        showsVerticalScrollIndicator={false}
      >
        <View style={styles.heroCard}>
          <View style={styles.heroIconCircle}>
            <Ionicons name="library-outline" size={24} color="#ffffff" />
          </View>

          <Text style={styles.heroTitle}>Biblioteca Inteligente</Text>
          <Text style={styles.heroSubtitle}>
            Explora información explicada de forma más clara, visual y amable.
          </Text>
        </View>

        <View style={styles.searchCard}>
          <View style={styles.searchInputWrapper}>
            <Ionicons name="search-outline" size={18} color="#64748b" />
            <TextInput
              style={styles.searchInput}
              placeholder="Buscar por tema, categoría o lector..."
              placeholderTextColor="#94a3b8"
              value={searchText}
              onChangeText={setSearchText}
            />
          </View>

          <Pressable style={styles.searchButton} onPress={loadArticles}>
            <Text style={styles.searchButtonText}>Buscar</Text>
          </Pressable>
        </View>

        <Text style={styles.filterTitle}>Vista</Text>
        <View style={styles.modeRow}>
          <Pressable
            style={[
              styles.modeChip,
              viewMode === "todos" && styles.modeChipActive,
            ]}
            onPress={() => setViewMode("todos")}
          >
            <Text
              style={[
                styles.modeChipText,
                viewMode === "todos" && styles.modeChipTextActive,
              ]}
            >
              Todos
            </Text>
          </Pressable>

          <Pressable
            style={[
              styles.modeChip,
              viewMode === "favoritos" && styles.modeChipActive,
            ]}
            onPress={() => setViewMode("favoritos")}
          >
            <Ionicons
              name={viewMode === "favoritos" ? "heart" : "heart-outline"}
              size={14}
              color={viewMode === "favoritos" ? "#ffffff" : "#334155"}
            />
            <Text
              style={[
                styles.modeChipText,
                viewMode === "favoritos" && styles.modeChipTextActive,
              ]}
            >
              Favoritos
            </Text>
          </Pressable>
        </View>

        <Text style={styles.filterTitle}>Categorías</Text>
        <ScrollView
          horizontal
          showsHorizontalScrollIndicator={false}
          style={styles.filterRow}
          contentContainerStyle={styles.filterRowContent}
        >
          {categories.map((category) => {
            const isActive = selectedCategory === category;

            return (
              <Pressable
                key={category}
                style={[
                  styles.filterChip,
                  isActive && styles.filterChipActive,
                ]}
                onPress={() => setSelectedCategory(category)}
              >
                <Text
                  style={[
                    styles.filterChipText,
                    isActive && styles.filterChipTextActive,
                  ]}
                >
                  {category}
                </Text>
              </Pressable>
            );
          })}
        </ScrollView>

        <Text style={styles.filterTitle}>Pensado para</Text>
        <ScrollView
          horizontal
          showsHorizontalScrollIndicator={false}
          style={styles.filterRow}
          contentContainerStyle={styles.filterRowContent}
        >
          {readerTypes.map((readerType) => {
            const isActive = selectedReaderType === readerType;

            return (
              <Pressable
                key={readerType}
                style={[
                  styles.filterChipSoft,
                  isActive && styles.filterChipSoftActive,
                ]}
                onPress={() => setSelectedReaderType(readerType)}
              >
                <Text
                  style={[
                    styles.filterChipSoftText,
                    isActive && styles.filterChipSoftTextActive,
                  ]}
                >
                  {readerType}
                </Text>
              </Pressable>
            );
          })}
        </ScrollView>

        <View style={styles.resultsRow}>
          <Text style={styles.resultsText}>
            {filteredArticles.length} artículo(s) encontrado(s)
          </Text>
        </View>

        {featuredArticle && (
          <Pressable
            style={styles.featuredCard}
            onPress={() => handleOpenArticle(featuredArticle.id)}
          >
            <View style={styles.featuredTopRow}>
              <View style={styles.featuredBadge}>
                <Text style={styles.featuredBadgeText}>Destacado</Text>
              </View>

              <Pressable
                style={styles.favoriteIconButton}
                onPress={() =>
                  handleToggleFavorite(
                    featuredArticle.id,
                    !favoriteIds.includes(featuredArticle.id)
                  )
                }
              >
                <Ionicons
                  name={
                    favoriteIds.includes(featuredArticle.id)
                      ? "heart"
                      : "heart-outline"
                  }
                  size={20}
                  color={
                    favoriteIds.includes(featuredArticle.id)
                      ? "#e6527a"
                      : "#64748b"
                  }
                />
              </Pressable>
            </View>

            <Text style={styles.featuredTitle}>{featuredArticle.title}</Text>
            <Text style={styles.featuredDescription} numberOfLines={3}>
              {featuredArticle.short_description}
            </Text>

            <View style={styles.featuredMetaRow}>
              <Text style={styles.featuredMetaText}>
                {featuredArticle.category}
              </Text>
              <Text style={styles.featuredMetaSeparator}>•</Text>
              <Text style={styles.featuredMetaText}>
                {featuredArticle.reader_type}
              </Text>
            </View>
          </Pressable>
        )}

        <Text style={styles.sectionTitle}>Artículos</Text>

        {filteredArticles.length === 0 ? (
          <View style={styles.emptyCard}>
            <Ionicons name="document-text-outline" size={28} color="#2f64b9" />
            <Text style={styles.emptyTitle}>No encontré resultados</Text>
            <Text style={styles.emptyText}>
              Prueba con otra búsqueda o cambia los filtros.
            </Text>
          </View>
        ) : (
          <View style={styles.articleList}>
            {filteredArticles.map((article) => (
              <ArticleCard
                key={article.id}
                article={article}
                isFavorite={favoriteIds.includes(article.id)}
                onOpen={handleOpenArticle}
                onToggleFavorite={handleToggleFavorite}
              />
            ))}
          </View>
        )}
      </ScrollView>

      <Modal
        visible={detailVisible}
        animationType="slide"
        transparent
        onRequestClose={() => setDetailVisible(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.modalSheet}>
            <View style={styles.modalHandle} />

            <View style={styles.modalHeaderRow}>
              <Text style={styles.modalTitle}>Detalle del artículo</Text>

              <Pressable onPress={() => setDetailVisible(false)}>
                <Ionicons name="close" size={22} color="#334155" />
              </Pressable>
            </View>

            {selectedArticle ? (
              <ScrollView
                showsVerticalScrollIndicator={false}
                contentContainerStyle={styles.modalContent}
              >
                <Text style={styles.detailTitle}>{selectedArticle.title}</Text>

                <View style={styles.detailBadgesRow}>
                  <View style={styles.detailBadge}>
                    <Text style={styles.detailBadgeText}>
                      {selectedArticle.category}
                    </Text>
                  </View>

                  <View style={styles.detailBadgeSoft}>
                    <Text style={styles.detailBadgeSoftText}>
                      {selectedArticle.reader_type}
                    </Text>
                  </View>
                </View>

                <Text style={styles.detailIntro}>
                  {selectedArticle.short_description}
                </Text>

                <Text style={styles.detailContent}>
                  {selectedArticle.content}
                </Text>

                <View style={styles.detailActionsRow}>
                  <Pressable
                    style={styles.favoriteActionButton}
                    onPress={() =>
                      handleToggleFavorite(
                        selectedArticle.id,
                        !favoriteIds.includes(selectedArticle.id)
                      )
                    }
                  >
                    <Ionicons
                      name={
                        favoriteIds.includes(selectedArticle.id)
                          ? "heart"
                          : "heart-outline"
                      }
                      size={18}
                      color="#e6527a"
                    />
                    <Text style={styles.favoriteActionText}>
                      {favoriteIds.includes(selectedArticle.id)
                        ? "Quitar favorito"
                        : "Guardar favorito"}
                    </Text>
                  </Pressable>

                  <Pressable
                    style={[
                      styles.sendToFriendButton,
                      actionLoading && styles.sendToFriendButtonDisabled,
                    ]}
                    onPress={handleSendToFriend}
                    disabled={actionLoading}
                  >
                    <Ionicons name="chatbubble-ellipses-outline" size={18} color="#ffffff" />
                    <Text style={styles.sendToFriendText}>
                      {actionLoading ? "Enviando..." : "Hablar con Amigo"}
                    </Text>
                  </Pressable>
                </View>
              </ScrollView>
            ) : (
              <View style={styles.centered}>
                <ActivityIndicator size="small" color="#2f64b9" />
              </View>
            )}
          </View>
        </View>
      </Modal>
    </>
  );
}

const styles = StyleSheet.create({
  screen: {
    flex: 1,
    backgroundColor: "#f5f7fb",
  },
  content: {
    padding: 16,
    paddingBottom: 28,
  },
  centered: {
    flex: 1,
    backgroundColor: "#f5f7fb",
    justifyContent: "center",
    alignItems: "center",
    padding: 20,
  },
  loadingText: {
    marginTop: 12,
    color: "#64748b",
    fontSize: 15,
  },
  heroCard: {
    backgroundColor: "#2f64b9",
    borderRadius: 24,
    padding: 20,
    marginBottom: 16,
  },
  heroIconCircle: {
    width: 46,
    height: 46,
    borderRadius: 23,
    backgroundColor: "#4a7cd0",
    justifyContent: "center",
    alignItems: "center",
    marginBottom: 12,
  },
  heroTitle: {
    color: "#ffffff",
    fontSize: 24,
    fontWeight: "800",
  },
  heroSubtitle: {
    marginTop: 8,
    color: "#dbeafe",
    lineHeight: 21,
    fontSize: 14,
  },
  searchCard: {
    backgroundColor: "#ffffff",
    borderRadius: 18,
    padding: 14,
    marginBottom: 16,
  },
  searchInputWrapper: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: "#f8fafc",
    borderRadius: 14,
    paddingHorizontal: 12,
    paddingVertical: 12,
  },
  searchInput: {
    flex: 1,
    marginLeft: 8,
    color: "#111827",
    fontSize: 15,
  },
  searchButton: {
    marginTop: 10,
    backgroundColor: "#2f64b9",
    borderRadius: 14,
    alignItems: "center",
    paddingVertical: 12,
  },
  searchButtonText: {
    color: "#ffffff",
    fontWeight: "800",
  },
  filterTitle: {
    color: "#334155",
    fontWeight: "800",
    fontSize: 15,
    marginBottom: 8,
    marginTop: 4,
  },
  modeRow: {
    flexDirection: "row",
    gap: 10,
    marginBottom: 12,
  },
  modeChip: {
    backgroundColor: "#eef2f7",
    borderRadius: 999,
    paddingHorizontal: 14,
    paddingVertical: 10,
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
  },
  modeChipActive: {
    backgroundColor: "#2f64b9",
  },
  modeChipText: {
    color: "#334155",
    fontWeight: "700",
  },
  modeChipTextActive: {
    color: "#ffffff",
  },
  filterRow: {
    maxHeight: 48,
    marginBottom: 12,
  },
  filterRowContent: {
    gap: 8,
    paddingRight: 8,
  },
  filterChip: {
    backgroundColor: "#e8eefb",
    borderRadius: 999,
    paddingHorizontal: 14,
    paddingVertical: 10,
  },
  filterChipActive: {
    backgroundColor: "#2f64b9",
  },
  filterChipText: {
    color: "#2f64b9",
    fontWeight: "700",
  },
  filterChipTextActive: {
    color: "#ffffff",
  },
  filterChipSoft: {
    backgroundColor: "#eef2f7",
    borderRadius: 999,
    paddingHorizontal: 14,
    paddingVertical: 10,
  },
  filterChipSoftActive: {
    backgroundColor: "#0f172a",
  },
  filterChipSoftText: {
    color: "#334155",
    fontWeight: "700",
  },
  filterChipSoftTextActive: {
    color: "#ffffff",
  },
  resultsRow: {
    marginBottom: 12,
  },
  resultsText: {
    color: "#64748b",
    fontSize: 13,
    fontWeight: "600",
  },
  featuredCard: {
    backgroundColor: "#ffffff",
    borderRadius: 20,
    padding: 18,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: "#dbeafe",
  },
  featuredTopRow: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
  },
  featuredBadge: {
    backgroundColor: "#e8f0ff",
    borderRadius: 999,
    paddingHorizontal: 12,
    paddingVertical: 8,
  },
  featuredBadgeText: {
    color: "#2f64b9",
    fontWeight: "800",
    fontSize: 12,
  },
  featuredTitle: {
    marginTop: 14,
    color: "#0f172a",
    fontSize: 19,
    fontWeight: "800",
    lineHeight: 25,
  },
  featuredDescription: {
    marginTop: 10,
    color: "#475569",
    lineHeight: 21,
  },
  featuredMetaRow: {
    flexDirection: "row",
    alignItems: "center",
    marginTop: 14,
  },
  featuredMetaText: {
    color: "#64748b",
    fontWeight: "700",
    fontSize: 13,
  },
  featuredMetaSeparator: {
    color: "#94a3b8",
    marginHorizontal: 8,
  },
  sectionTitle: {
    color: "#0f172a",
    fontSize: 18,
    fontWeight: "800",
    marginBottom: 12,
  },
  articleList: {
    gap: 12,
  },
  articleCard: {
    backgroundColor: "#ffffff",
    borderRadius: 18,
    padding: 16,
  },
  articleHeaderRow: {
    flexDirection: "row",
    alignItems: "flex-start",
  },
  articleIconCircle: {
    width: 42,
    height: 42,
    borderRadius: 21,
    backgroundColor: "#eaf0fb",
    justifyContent: "center",
    alignItems: "center",
    marginRight: 12,
  },
  articleHeaderText: {
    flex: 1,
  },
  articleTitle: {
    color: "#0f172a",
    fontSize: 16,
    fontWeight: "800",
    lineHeight: 22,
  },
  articleCategory: {
    marginTop: 4,
    color: "#64748b",
    fontSize: 13,
    fontWeight: "600",
  },
  favoriteIconButton: {
    padding: 4,
    marginLeft: 8,
  },
  articleDescription: {
    marginTop: 12,
    color: "#475569",
    lineHeight: 20,
  },
  articleFooterRow: {
    marginTop: 14,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
  },
  readerBadge: {
    borderRadius: 999,
    paddingHorizontal: 12,
    paddingVertical: 8,
  },
  readerBadgeText: {
    fontWeight: "800",
    fontSize: 12,
  },
  openRow: {
    flexDirection: "row",
    alignItems: "center",
  },
  openText: {
    color: "#2f64b9",
    fontWeight: "800",
    marginRight: 2,
  },
  emptyCard: {
    backgroundColor: "#ffffff",
    borderRadius: 18,
    padding: 22,
    alignItems: "center",
  },
  emptyTitle: {
    marginTop: 10,
    color: "#0f172a",
    fontSize: 16,
    fontWeight: "800",
  },
  emptyText: {
    marginTop: 6,
    color: "#64748b",
    textAlign: "center",
    lineHeight: 20,
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: "#00000044",
    justifyContent: "flex-end",
  },
  modalSheet: {
    backgroundColor: "#ffffff",
    borderTopLeftRadius: 24,
    borderTopRightRadius: 24,
    maxHeight: "88%",
    paddingHorizontal: 18,
    paddingTop: 10,
    paddingBottom: 18,
  },
  modalHandle: {
    width: 54,
    height: 6,
    borderRadius: 999,
    backgroundColor: "#d0d7e2",
    alignSelf: "center",
    marginBottom: 14,
  },
  modalHeaderRow: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    marginBottom: 12,
  },
  modalTitle: {
    color: "#0f172a",
    fontWeight: "800",
    fontSize: 18,
  },
  modalContent: {
    paddingBottom: 16,
  },
  detailTitle: {
    color: "#0f172a",
    fontSize: 22,
    fontWeight: "800",
    lineHeight: 28,
  },
  detailBadgesRow: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 8,
    marginTop: 12,
    marginBottom: 14,
  },
  detailBadge: {
    backgroundColor: "#e8f0ff",
    borderRadius: 999,
    paddingHorizontal: 12,
    paddingVertical: 8,
  },
  detailBadgeText: {
    color: "#2f64b9",
    fontWeight: "800",
    fontSize: 12,
  },
  detailBadgeSoft: {
    backgroundColor: "#eef2f7",
    borderRadius: 999,
    paddingHorizontal: 12,
    paddingVertical: 8,
  },
  detailBadgeSoftText: {
    color: "#334155",
    fontWeight: "800",
    fontSize: 12,
  },
  detailIntro: {
    color: "#334155",
    fontWeight: "700",
    lineHeight: 22,
    marginBottom: 14,
  },
  detailContent: {
    color: "#475569",
    lineHeight: 23,
    fontSize: 15,
  },
  detailActionsRow: {
    marginTop: 18,
    gap: 12,
  },
  favoriteActionButton: {
    backgroundColor: "#fff0f4",
    borderRadius: 14,
    paddingVertical: 13,
    paddingHorizontal: 14,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 8,
  },
  favoriteActionText: {
    color: "#e6527a",
    fontWeight: "800",
  },
  sendToFriendButton: {
    backgroundColor: "#2f64b9",
    borderRadius: 14,
    paddingVertical: 14,
    paddingHorizontal: 14,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 8,
  },
  sendToFriendButtonDisabled: {
    opacity: 0.6,
  },
  sendToFriendText: {
    color: "#ffffff",
    fontWeight: "800",
  },
});