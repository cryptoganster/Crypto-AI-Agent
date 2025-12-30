"""Interface para servicio de extracción de keywords de artículos."""

from typing import Dict, List, Optional, Protocol

from src.rss.article.domain.aggregates.rss_article import RssArticle as Article
from src.rss.article.domain.value_objects.metadata import ArticleLanguage
from src.rss.article.domain.value_objects.metadata.language import (
    ArticleLanguage as ContentLanguage,
)


class IArticleKeywordService(Protocol):
    """
    Interface para servicio de extracción de keywords.

    RESPONSABILIDAD ÚNICA: Extracción de keywords de artículos.
    - NO hace análisis de sentimiento
    - NO hace categorización
    - NO hace validación de calidad
    """

    def extract_keywords(
        self,
        article: Article,
        max_keywords: int = 10,
        min_score: float = 0.3,
    ) -> Optional[List[str]]:
        """
        Extrae keywords relevantes del contenido del artículo.

        Args:
            article: Artículo del que extraer keywords
            max_keywords: Máximo número de keywords a extraer
            min_score: Score mínimo para considerar keyword relevante

        Returns:
            Lista de keywords extraídas ordenadas por relevancia, o None si falla
        """
        ...

    def extract_keywords_with_scores(
        self,
        article: Article,
        max_keywords: int = 10,
        min_score: float = 0.3,
    ) -> Dict[str, float]:
        """
        Extrae keywords con sus scores de relevancia.

        Args:
            article: Artículo del que extraer keywords
            max_keywords: Máximo número de keywords a extraer
            min_score: Score mínimo para considerar keyword relevante

        Returns:
            Diccionario {keyword: score} ordenado por relevancia
        """
        ...

    def filter_stopwords(self, words: List[str], language: str = "en") -> List[str]:
        """
        Filtra palabras comunes (stopwords) de una lista.

        Args:
            words: Lista de palabras a filtrar
            language: Idioma para stopwords (en, es, etc.)

        Returns:
            Lista de palabras sin stopwords
        """
        ...

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
            max_ngrams: Máximo número de n-gramas a extraer

        Returns:
            Lista de n-gramas relevantes
        """
        ...
