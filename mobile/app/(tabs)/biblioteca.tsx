// Biblioteca Inteligente en móvil
import React, { useEffect, useState } from "react";
import {
  ActivityIndicator,
  Alert,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from "react-native";

import { Article, getArticleById, listArticles } from "../../src/lib/api";
import { useAuth } from "../../src/lib/auth";

export default function BibliotecaScreen() {
  const { token } = useAuth();

  const [search, setSearch] = useState("");
  const [articles, setArticles] = useState<Article[]>([]);
  const [selectedArticle, setSelectedArticle] = useState<Article | null>(null);
  const [loading, setLoading] = useState(true);

  const loadArticles = async (searchValue: string = "") => {
    if (!token) return;

    try {
      setLoading(true);
      const fetched = await listArticles(token, searchValue);
      setArticles(fetched);

      if (fetched.length > 0) {
        const detail = await getArticleById(token, fetched[0].id);
        setSelectedArticle(detail);
      } else {
        setSelectedArticle(null);
      }
    } catch (error: any) {
      Alert.alert("Error", error?.message || "No se pudieron cargar los artículos.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadArticles();
  }, [token]);

  const handleSearch = async () => {
    await loadArticles(search);
  };

  const handleSelectArticle = async (articleId: number) => {
    if (!token) return;

    try {
      const detail = await getArticleById(token, articleId);
      setSelectedArticle(detail);
    } catch (error: any) {
      Alert.alert("Error", error?.message || "No se pudo abrir el artículo.");
    }
  };

  return (
    <View style={styles.screen}>
      <View style={styles.searchCard}>
        <Text style={styles.title}>Biblioteca Inteligente</Text>
        <Text style={styles.subtitle}>
          Busca contenido educativo de forma sencilla.
        </Text>

        <TextInput
          style={styles.input}
          placeholder="Buscar por tema..."
          value={search}
          onChangeText={setSearch}
        />

        <Pressable style={styles.searchButton} onPress={handleSearch}>
          <Text style={styles.searchButtonText}>Buscar</Text>
        </Pressable>
      </View>

      {loading ? (
        <View style={styles.centered}>
          <ActivityIndicator size="large" color="#2f64b9" />
        </View>
      ) : (
        <ScrollView contentContainerStyle={styles.content}>
          {articles.map((article) => (
            <Pressable
              key={article.id}
              style={styles.articleCard}
              onPress={() => handleSelectArticle(article.id)}
            >
              <Text style={styles.articleTitle}>{article.title}</Text>
              <Text style={styles.articleMeta}>
                {article.category} · {article.reader_type}
              </Text>
              <Text style={styles.articleDesc}>{article.short_description}</Text>
            </Pressable>
          ))}

          {selectedArticle && (
            <View style={styles.detailCard}>
              <Text style={styles.detailTitle}>{selectedArticle.title}</Text>
              <Text style={styles.articleMeta}>
                {selectedArticle.category} · {selectedArticle.reader_type}
              </Text>
              <Text style={styles.detailText}>{selectedArticle.content}</Text>
            </View>
          )}
        </ScrollView>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  screen: {
    flex: 1,
    backgroundColor: "#f5f7fb",
  },
  searchCard: {
    backgroundColor: "#ffffff",
    margin: 16,
    borderRadius: 18,
    padding: 16,
  },
  title: {
    fontSize: 22,
    fontWeight: "800",
    color: "#0f172a",
  },
  subtitle: {
    marginTop: 6,
    color: "#64748b",
  },
  input: {
    backgroundColor: "#f8fafc",
    borderRadius: 14,
    paddingHorizontal: 14,
    paddingVertical: 12,
    marginTop: 12,
    color: "#111827",
  },
  searchButton: {
    marginTop: 10,
    backgroundColor: "#2f64b9",
    paddingVertical: 12,
    borderRadius: 14,
    alignItems: "center",
  },
  searchButtonText: {
    color: "#ffffff",
    fontWeight: "700",
  },
  centered: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
  },
  content: {
    paddingHorizontal: 16,
    paddingBottom: 24,
  },
  articleCard: {
    backgroundColor: "#ffffff",
    borderRadius: 18,
    padding: 16,
    marginBottom: 12,
  },
  articleTitle: {
    fontSize: 16,
    fontWeight: "800",
    color: "#0f172a",
  },
  articleMeta: {
    marginTop: 6,
    color: "#64748b",
    fontSize: 13,
  },
  articleDesc: {
    marginTop: 8,
    color: "#334155",
    lineHeight: 20,
  },
  detailCard: {
    backgroundColor: "#ffffff",
    borderRadius: 18,
    padding: 16,
    marginTop: 8,
  },
  detailTitle: {
    fontSize: 18,
    fontWeight: "800",
    color: "#0f172a",
  },
  detailText: {
    marginTop: 12,
    color: "#334155",
    lineHeight: 22,
  },
});