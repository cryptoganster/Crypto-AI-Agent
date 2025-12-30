"""Implementación de ArticleReadabilityService en Infrastructure Layer."""

import re
from typing import Dict, Optional

from src.rss.article.domain.aggregates.rss_article import RssArticle as Article
from src.rss.article.domain.interfaces.services.readability import (
    IArticleReadabilityService,
)
from src.rss.article.domain.value_objects.readability_score import ReadabilityScore


class ArticleReadabilityService(IArticleReadabilityService):
    """
    Implementación de IArticleReadabilityService en Infrastructure Layer.

    Responsabilidades:
    - Calcular Flesch Reading Ease score
    - Calcular Gunning Fog Index
    - Obtener estadísticas de contenido
    - Analizar complejidad del texto

    IMPORTANTE: Este servicio IMPORTA el Article aggregate (correcto según Clean Architecture).
    El aggregate NO debe importar este servicio.
    """

    def calculate_readability_score(self, article: Article) -> float:
        """
        Calcula el Flesch Reading Ease score del artículo.

        Args:
            article: Artículo a analizar

        Returns:
            Score entre 0.0 y 1.0 (1.0 = más legible)

        Raises:
            ValueError: Si el artículo no tiene contenido
        """
        if not self._has_content(article):
            raise ValueError(
                "El artículo debe tener contenido para calcular legibilidad"
            )
        text = self._get_clean_text(article)
        word_count = self._count_words(text)
        sentence_count = self._count_sentences(text)
        syllable_count = self._count_syllables(text)

        if sentence_count == 0 or word_count == 0:
            return 0.5

        avg_words_per_sentence = word_count / sentence_count
        avg_syllables_per_word = syllable_count / word_count

        flesch_score = (
            206.835 - (1.015 * avg_words_per_sentence) - (84.6 * avg_syllables_per_word)
        )

        normalized_score = max(0.0, min(1.0, flesch_score / 100.0))
        return normalized_score

    def calculate_gunning_fog_index(self, article: Article) -> Optional[float]:
        """Calcula el Gunning Fog Index (nivel de educación requerido)."""
        if not self._has_content(article):
            raise ValueError(
                "El artículo debe tener contenido para calcular Gunning Fog"
            )

        text = self._get_clean_text(article)
        word_count = self._count_words(text)
        sentence_count = self._count_sentences(text)
        complex_word_count = self._count_complex_words(text)

        if sentence_count == 0 or word_count == 0:
            return None

        avg_words_per_sentence = word_count / sentence_count
        percentage_complex = (complex_word_count / word_count) * 100
        fog_index = 0.4 * (avg_words_per_sentence + percentage_complex)

        return round(fog_index, 2)

    def get_content_statistics(self, article: Article) -> Dict[str, int]:
        """Obtiene estadísticas básicas del contenido."""
        if not self._has_content(article):
            raise ValueError(
                "El artículo debe tener contenido para obtener estadísticas"
            )

        text = self._get_clean_text(article)

        return {
            "word_count": self._count_words(text),
            "sentence_count": self._count_sentences(text),
            "paragraph_count": self._count_paragraphs(text),
            "character_count": len(text),
            "syllable_count": self._count_syllables(text),
            "complex_word_count": self._count_complex_words(text),
        }

    def analyze_complexity(self, article: Article) -> Dict[str, float]:
        """Análisis completo de complejidad del texto."""
        if not self._has_content(article):
            raise ValueError(
                "El artículo debe tener contenido para analizar complejidad"
            )

        text = self._get_clean_text(article)
        stats = self.get_content_statistics(article)

        avg_word_length = (
            stats["character_count"] / stats["word_count"]
            if stats["word_count"] > 0
            else 0.0
        )

        avg_sentence_length = (
            stats["word_count"] / stats["sentence_count"]
            if stats["sentence_count"] > 0
            else 0.0
        )

        readability_score = self.calculate_readability_score(article)
        fog_index = self.calculate_gunning_fog_index(article) or 0.0

        complexity_rating = self._calculate_complexity_rating(
            readability_score, fog_index, avg_word_length, avg_sentence_length
        )

        return {
            "readability_score": round(readability_score, 3),
            "fog_index": round(fog_index, 2),
            "avg_word_length": round(avg_word_length, 2),
            "avg_sentence_length": round(avg_sentence_length, 2),
            "complexity_rating": round(complexity_rating, 3),
        }

    # Private helper methods

    def _has_content(self, article: Article) -> bool:
        """Verifica si el artículo tiene contenido para analizar."""
        if article.content.plaintext and article.content.plaintext.strip():
            return True
        if article.content.markdown and article.content.markdown.strip():
            return True
        return False

    def _get_clean_text(self, article: Article) -> str:
        """Obtiene texto limpio del artículo para análisis."""
        if article.content.plaintext and article.content.plaintext.strip():
            return article.content.plaintext.strip()

        if article.content.markdown and article.content.markdown.strip():
            text = article.content.markdown.strip()
            text = re.sub(r"[#*_`\[\]()]", "", text)
            return text

        return ""

    def _count_words(self, text: str) -> int:
        """Cuenta palabras en el texto."""
        words = [w for w in text.split() if w.strip()]
        return len(words)

    def _count_sentences(self, text: str) -> int:
        """Cuenta oraciones en el texto."""
        sentences = re.split(r"[.!?]+", text)
        sentences = [s for s in sentences if s.strip()]
        return max(1, len(sentences))

    def _count_paragraphs(self, text: str) -> int:
        """Cuenta párrafos en el texto."""
        paragraphs = re.split(r"\n\s*\n", text)
        paragraphs = [p for p in paragraphs if p.strip()]
        return max(1, len(paragraphs))

    def _count_syllables(self, text: str) -> int:
        """Cuenta sílabas en el texto (aproximación)."""
        words = text.lower().split()
        total_syllables = 0

        for word in words:
            word = re.sub(r"[^a-z]", "", word)
            if not word:
                continue

            syllable_count = len(re.findall(r"[aeiouy]+", word))

            if word.endswith("e") and syllable_count > 1:
                syllable_count -= 1

            syllable_count = max(1, syllable_count)
            total_syllables += syllable_count

        return total_syllables

    def _count_complex_words(self, text: str) -> int:
        """Cuenta palabras complejas (3+ sílabas)."""
        words = text.lower().split()
        complex_count = 0

        for word in words:
            word = re.sub(r"[^a-z]", "", word)
            if not word:
                continue

            syllable_count = len(re.findall(r"[aeiouy]+", word))

            if word.endswith("e") and syllable_count > 1:
                syllable_count -= 1

            if syllable_count >= 3:
                complex_count += 1

        return complex_count

    def _calculate_complexity_rating(
        self,
        readability_score: float,
        fog_index: float,
        avg_word_length: float,
        avg_sentence_length: float,
    ) -> float:
        """Calcula rating de complejidad general (0.0-1.0)."""
        complexity_from_readability = 1.0 - readability_score
        complexity_from_fog = min(1.0, max(0.0, (fog_index - 6) / 11))
        complexity_from_word_length = min(1.0, max(0.0, (avg_word_length - 4) / 3))
        complexity_from_sentence_length = min(
            1.0, max(0.0, (avg_sentence_length - 10) / 15)
        )

        complexity_rating = (
            0.4 * complexity_from_readability
            + 0.3 * complexity_from_fog
            + 0.15 * complexity_from_word_length
            + 0.15 * complexity_from_sentence_length
        )

        return max(0.0, min(1.0, complexity_rating))
