"""Implementación de ArticleDeduplicationService en Infrastructure Layer."""

from difflib import SequenceMatcher
from typing import List, Optional

from src.rss.article.domain.aggregates.rss_article import RssArticle as Article
from src.rss.article.domain.interfaces.repositories import IArticleReadRepository
from src.rss.article.domain.value_objects import ArticleId
from src.rss.feed.domain.aggregates import Source
from src.scraping.domain.interfaces.external.rss_feed_fetcher import ArticleData


class ArticleDeduplicationService:
    """
    Implementación de servicio de deduplicación en Infrastructure Layer.

    Responsabilidades:
    - Detectar duplicados usando similarity matching
    - Calcular similitud entre artículos
    - Encontrar artículos duplicados en una lista

    IMPORTANTE: Este servicio IMPORTA el Article aggregate (correcto según Clean Architecture).
    El aggregate NO debe importar este servicio.

    Usa algoritmo de similitud basado en:
    - Comparación de títulos
    - Comparación de contenido
    - Threshold configurable para determinar duplicados
    """

    def __init__(
        self,
        similarity_threshold: float = 0.85,
        article_queries: Optional[IArticleReadRepository] = None,
    ):
        """
        Inicializa el servicio de deduplicación.

        Args:
            similarity_threshold: Umbral de similitud (0.0-1.0) para considerar duplicados
            article_queries: Query adapter para verificación de duplicados por URL
        """
        if not 0.0 <= similarity_threshold <= 1.0:
            raise ValueError("similarity_threshold debe estar entre 0.0 y 1.0")
        self._similarity_threshold = similarity_threshold
        self._article_queries = article_queries

    async def check_duplicate_by_url(
        self,
        article_data: ArticleData,
        source: Source,
    ) -> bool:
        """
        Verifica si un artículo ya existe basándose en URL.

        Método optimizado para operaciones de fetch donde solo tenemos
        ArticleData y necesitamos verificación rápida antes de crear aggregate.

        Args:
            article_data: Datos del artículo desde RSS fetcher
            source: Source aggregate de origen

        Returns:
            True si el artículo ya existe (es duplicado)
        """
        if self._article_queries is None:
            # Si no hay article queries, no podemos verificar duplicados
            return False

        # Buscar por URL y source_id
        existing = await self._article_queries.find_by_url_and_source(
            url=article_data.url,
            source_id=str(source.id),
        )

        return existing is not None

    def is_duplicate(
        self,
        article: Article,
        existing_articles: List[Article],
    ) -> bool:
        """
        Verifica si un artículo es duplicado de alguno en la lista.

        Args:
            article: Article a verificar
            existing_articles: Lista de artículos existentes

        Returns:
            True si el artículo es duplicado de alguno en la lista
        """
        for existing in existing_articles:
            # No comparar consigo mismo
            if existing.id == article.id:
                continue

            similarity = self.calculate_similarity(article, existing)
            if similarity >= self._similarity_threshold:
                return True

        return False

    def find_duplicate(
        self,
        article: Article,
        existing_articles: List[Article],
    ) -> Optional[ArticleId]:
        """
        Encuentra el ID del primer duplicado en la lista.

        Args:
            article: Article a verificar
            existing_articles: Lista de artículos existentes

        Returns:
            ArticleId del duplicado encontrado, o None si no hay duplicados
        """
        for existing in existing_articles:
            # No comparar consigo mismo
            if existing.id == article.id:
                continue

            similarity = self.calculate_similarity(article, existing)
            if similarity >= self._similarity_threshold:
                return existing.id

        return None

    def calculate_similarity(
        self,
        article1: Article,
        article2: Article,
    ) -> float:
        """
        Calcula similitud entre dos artículos (0.0-1.0).

        Combina similitud de título (40%) y contenido (60%).

        Args:
            article1: Primer artículo
            article2: Segundo artículo

        Returns:
            Score de similitud entre 0.0 (completamente diferente) y 1.0 (idéntico)
        """
        # Calcular similitud de título (40%)
        title_similarity = self._calculate_text_similarity(
            str(article1.title) if article1.title else "",
            str(article2.title) if article2.title else "",
        )

        # Calcular similitud de contenido (60%)
        content1 = self._get_content_for_comparison(article1)
        content2 = self._get_content_for_comparison(article2)
        content_similarity = self._calculate_text_similarity(content1, content2)

        # Combinar con pesos
        total_similarity = (title_similarity * 0.4) + (content_similarity * 0.6)

        return total_similarity

    def find_all_duplicates(
        self,
        articles: List[Article],
    ) -> List[tuple[ArticleId, ArticleId]]:
        """
        Encuentra todos los pares de duplicados en una lista.

        Args:
            articles: Lista de artículos a analizar

        Returns:
            Lista de tuplas (article_id, duplicate_id) con los duplicados encontrados
        """
        duplicates = []

        for i, article in enumerate(articles):
            # Comparar solo con artículos posteriores para evitar duplicados
            for other in articles[i + 1 :]:
                similarity = self.calculate_similarity(article, other)
                if similarity >= self._similarity_threshold:
                    duplicates.append((article.id, other.id))

        return duplicates

    # Private helper methods

    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """
        Calcula similitud entre dos textos usando SequenceMatcher.

        Args:
            text1: Primer texto
            text2: Segundo texto

        Returns:
            Score de similitud entre 0.0 y 1.0
        """
        if not text1 or not text2:
            return 0.0

        # Normalizar textos (lowercase, strip)
        text1_normalized = text1.lower().strip()
        text2_normalized = text2.lower().strip()

        # Si son idénticos después de normalizar
        if text1_normalized == text2_normalized:
            return 1.0

        # Usar SequenceMatcher para calcular similitud
        matcher = SequenceMatcher(None, text1_normalized, text2_normalized)
        return matcher.ratio()

    def _get_content_for_comparison(self, article: Article) -> str:
        """
        Obtiene el mejor contenido disponible para comparación.

        Prioriza: plaintext > markdown > scrapped
        Limita a primeros 5000 caracteres para performance.

        Args:
            article: Article del que obtener contenido

        Returns:
            Contenido para comparación
        """
        content = ""

        if article.content.plaintext and article.content.plaintext.strip():
            content = article.content.plaintext.strip()
        elif article.content.markdown and article.content.markdown.strip():
            content = article.content.markdown.strip()
        elif article.content.scrapped and article.content.scrapped.strip():
            content = article.content.scrapped.strip()

        # Limitar longitud para performance (primeros 5000 caracteres)
        if len(content) > 5000:
            content = content[:5000]

        return content
