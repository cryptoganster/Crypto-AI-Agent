"""Implementación de ArticleKeywordService en Infrastructure Layer."""

import re
from collections import Counter
from typing import Dict, List, Optional

from src.rss.article.domain.aggregates.rss_article import RssArticle as Article
from src.rss.article.domain.interfaces.services.keyword import (
    IArticleKeywordService,
)


class ArticleKeywordService(IArticleKeywordService):
    """
    Implementación de IArticleKeywordService en Infrastructure Layer.

    Responsabilidades:
    - Extracción de keywords usando técnicas de NLP
    - Filtrado de stopwords
    - Cálculo de relevancia por frecuencia (TF)
    - Extracción de n-gramas

    IMPORTANTE: Este servicio IMPORTA el Article aggregate (correcto según Clean Architecture).
    El aggregate NO debe importar este servicio.

    Algoritmo: Term Frequency (TF) con filtrado de stopwords.
    """

    # Stopwords comunes en inglés y español
    STOPWORDS_EN = {
        "the",
        "a",
        "an",
        "and",
        "or",
        "but",
        "in",
        "on",
        "at",
        "to",
        "for",
        "of",
        "with",
        "by",
        "from",
        "as",
        "is",
        "was",
        "are",
        "were",
        "be",
        "been",
        "being",
        "have",
        "has",
        "had",
        "do",
        "does",
        "did",
        "will",
        "would",
        "should",
        "could",
        "may",
        "might",
        "must",
        "can",
        "this",
        "that",
        "these",
        "those",
        "i",
        "you",
        "he",
        "she",
        "it",
        "we",
        "they",
        "what",
        "which",
        "who",
        "when",
        "where",
        "why",
        "how",
        "all",
        "each",
        "every",
        "both",
        "few",
        "more",
        "most",
        "other",
        "some",
        "such",
        "no",
        "nor",
        "not",
        "only",
        "own",
        "same",
        "so",
        "than",
        "too",
        "very",
        "s",
        "t",
        "just",
        "don",
        "now",
        "d",
        "ll",
        "m",
        "o",
        "re",
        "ve",
        "y",
        "ain",
        "aren",
        "couldn",
        "didn",
        "doesn",
        "hadn",
        "hasn",
        "haven",
        "isn",
        "ma",
        "mightn",
        "mustn",
        "needn",
        "shan",
        "shouldn",
        "wasn",
        "weren",
        "won",
        "wouldn",
    }

    STOPWORDS_ES = {
        "el",
        "la",
        "de",
        "que",
        "y",
        "a",
        "en",
        "un",
        "ser",
        "se",
        "no",
        "haber",
        "por",
        "con",
        "su",
        "para",
        "como",
        "estar",
        "tener",
        "le",
        "lo",
        "todo",
        "pero",
        "más",
        "hacer",
        "o",
        "poder",
        "decir",
        "este",
        "ir",
        "otro",
        "ese",
        "si",
        "me",
        "ya",
        "ver",
        "porque",
        "dar",
        "cuando",
        "él",
        "muy",
        "sin",
        "vez",
        "mucho",
        "saber",
        "qué",
        "sobre",
        "mi",
        "alguno",
        "mismo",
        "yo",
        "también",
        "hasta",
        "año",
        "dos",
        "querer",
        "entre",
        "así",
        "primero",
        "desde",
        "grande",
        "eso",
        "ni",
        "nos",
        "llegar",
        "pasar",
        "tiempo",
        "ella",
        "sí",
        "día",
        "uno",
        "bien",
        "poco",
        "deber",
        "entonces",
        "poner",
        "cosa",
        "tanto",
        "hombre",
        "parecer",
        "nuestro",
        "tan",
        "donde",
        "ahora",
        "parte",
        "después",
        "vida",
        "quedar",
        "siempre",
        "creer",
        "hablar",
        "llevar",
        "dejar",
        "nada",
        "cada",
        "seguir",
        "menos",
        "nuevo",
        "encontrar",
        "algo",
        "solo",
        "decir",
        "estos",
        "trabajar",
        "primera",
        "saber",
        "puede",
        "quién",
        "tal",
        "durante",
        "ellos",
        "estado",
        "hacer",
        "podría",
        "forma",
        "caso",
        "mismo",
        "ante",
        "ellas",
        "misma",
        "contra",
        "aquí",
        "fueron",
        "cómo",
        "hay",
        "sido",
        "está",
        "estaba",
        "estamos",
        "están",
        "estoy",
        "eran",
        "eres",
        "es",
        "sea",
        "sean",
        "siendo",
        "somos",
        "son",
        "soy",
        "tenía",
        "tengo",
        "tiene",
        "tienen",
        "tienes",
    }

    def __init__(self):
        """Inicializa el servicio de keywords."""
        self._stopwords = self.STOPWORDS_EN | self.STOPWORDS_ES

    def extract_keywords(
        self,
        article: Article,
        max_keywords: int = 10,
        min_score: float = 0.3,
    ) -> Optional[List[str]]:
        """
        Extrae keywords del artículo usando Term Frequency.

        Usa content_plaintext si está disponible, sino content_markdown o content.

        Args:
            article: Artículo del que extraer keywords
            max_keywords: Máximo número de keywords a extraer
            min_score: Score mínimo de relevancia (no usado en esta implementación simple)

        Returns:
            Lista de keywords ordenadas por relevancia, o None si no hay contenido

        Raises:
            ValueError: Si el artículo no tiene contenido
        """
        # Obtener contenido para análisis
        content = self._get_content_for_analysis(article)

        if not content:
            raise ValueError("El artículo debe tener contenido para extraer keywords")

        # Tokenizar y limpiar
        words = self._tokenize(content)

        # Filtrar stopwords y palabras cortas
        filtered_words = [
            word for word in words if word not in self._stopwords and len(word) >= 3
        ]

        if not filtered_words:
            return None

        # Calcular frecuencias
        word_freq = Counter(filtered_words)

        # Obtener top keywords
        top_keywords = [word for word, _ in word_freq.most_common(max_keywords)]

        return top_keywords if top_keywords else None

    def extract_keywords_with_scores(
        self,
        article: Article,
        max_keywords: int = 10,
        min_score: float = 0.3,
    ) -> Dict[str, float]:
        """
        Extrae keywords con scores normalizados.

        Args:
            article: Artículo del que extraer keywords
            max_keywords: Máximo número de keywords
            min_score: Score mínimo de relevancia

        Returns:
            Diccionario {keyword: score} ordenado por relevancia

        Raises:
            ValueError: Si el artículo no tiene contenido
        """
        # Obtener contenido
        content = self._get_content_for_analysis(article)

        if not content:
            raise ValueError("El artículo debe tener contenido para extraer keywords")

        # Tokenizar y filtrar
        words = self._tokenize(content)
        filtered_words = [
            word for word in words if word not in self._stopwords and len(word) >= 3
        ]

        if not filtered_words:
            return {}

        # Calcular frecuencias
        word_freq = Counter(filtered_words)

        if not word_freq:
            return {}

        # Normalizar scores (0.0 - 1.0)
        max_freq = max(word_freq.values())
        normalized_scores = {
            word: freq / max_freq
            for word, freq in word_freq.items()
            if freq / max_freq >= min_score
        }

        # Ordenar por score y tomar top N
        sorted_keywords = sorted(
            normalized_scores.items(), key=lambda x: x[1], reverse=True
        )[:max_keywords]

        return dict(sorted_keywords)

    def filter_stopwords(self, words: List[str], language: str = "en") -> List[str]:
        """
        Filtra stopwords de una lista de palabras.

        Args:
            words: Lista de palabras a filtrar
            language: Idioma para stopwords (en, es, etc.)

        Returns:
            Lista de palabras sin stopwords
        """
        if language == "es":
            stopwords = self.STOPWORDS_ES
        else:
            stopwords = self.STOPWORDS_EN

        return [word for word in words if word.lower() not in stopwords]

    def extract_ngrams(
        self,
        article: Article,
        n: int = 2,
        max_ngrams: int = 5,
    ) -> List[str]:
        """
        Extrae n-gramas (frases) del artículo.

        Args:
            article: Artículo del que extraer n-gramas
            n: Tamaño del n-grama (2=bigrams, 3=trigrams)
            max_ngrams: Máximo número de n-gramas

        Returns:
            Lista de n-gramas relevantes

        Raises:
            ValueError: Si el artículo no tiene contenido
        """
        # Obtener contenido
        content = self._get_content_for_analysis(article)

        if not content:
            raise ValueError("El artículo debe tener contenido para extraer n-gramas")

        # Tokenizar
        words = self._tokenize(content)

        # Filtrar stopwords
        filtered_words = [
            word for word in words if word not in self._stopwords and len(word) >= 3
        ]

        if len(filtered_words) < n:
            return []

        # Generar n-gramas
        ngrams = []
        for i in range(len(filtered_words) - n + 1):
            ngram = " ".join(filtered_words[i : i + n])
            ngrams.append(ngram)

        # Contar frecuencias
        ngram_freq = Counter(ngrams)

        # Obtener top n-gramas
        top_ngrams = [ngram for ngram, _ in ngram_freq.most_common(max_ngrams)]

        return top_ngrams

    # Private helper methods

    def _get_content_for_analysis(self, article: Article) -> Optional[str]:
        """
        Obtiene el mejor contenido disponible para análisis.

        Prioridad: content_vo.plaintext > content_vo.markdown

        Args:
            article: Artículo del que obtener contenido

        Returns:
            Contenido para análisis o None si no hay contenido
        """
        # Priorizar plaintext (mejor para NLP)
        if article.content.plaintext and article.content.plaintext.strip():
            return article.content.plaintext

        # Fallback a markdown
        if article.content.markdown and article.content.markdown.strip():
            return article.content.markdown

        return None

    def _tokenize(self, text: str) -> List[str]:
        """
        Tokeniza texto en palabras.

        Args:
            text: Texto a tokenizar

        Returns:
            Lista de palabras en minúsculas
        """
        # Convertir a minúsculas
        text = text.lower()

        # Extraer solo palabras (letras y números)
        words = re.findall(r"\b[a-záéíóúñ]+\b", text)

        return words
