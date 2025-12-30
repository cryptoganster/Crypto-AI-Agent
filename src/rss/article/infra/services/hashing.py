"""Implementación de ArticleHashingService en Infrastructure Layer."""

from hashlib import sha256
from typing import List, Optional

from src.rss.article.domain.aggregates.rss_article import RssArticle as Article
from src.rss.article.domain.interfaces.services.hashing import (
    IArticleHashingService,
)
from src.rss.article.domain.value_objects.similarity import (
    ContentHash,
    ContentHashAlgorithm,
)


class ArticleHashingService(IArticleHashingService):
    """
    Implementación de IArticleHashingService en Infrastructure Layer.

    Responsabilidades:
    - Generación de hashes de contenido usando SHA-256
    - Asignación de hashes a artículos
    - Validación de contenido antes del hashing
    - Comparación de hashes para detección de duplicados

    IMPORTANTE: Este servicio IMPORTA el Article aggregate (correcto según Clean Architecture).
    El aggregate NO debe importar este servicio.
    """

    def generate_and_assign_content_hash(
        self,
        article: Article,
        algorithm: Optional[ContentHashAlgorithm] = None,
    ) -> ContentHash:
        """
        Genera y asigna hash de contenido a un artículo RSS.

        Args:
            article: Artículo al que asignar el hash
            algorithm: Algoritmo de hashing (default: SHA256)

        Returns:
            ContentHash generado

        Raises:
            ValueError: Si no hay contenido suficiente para generar hash
        """
        if not self._has_sufficient_content_for_hashing(article):
            raise ValueError("No hay contenido extraído para generar hash")

        algo = algorithm or ContentHashAlgorithm.SHA256

        # Generar hash usando estrategia RSS (URL + título)
        content_hash = self._generate_rss_content_hash(article, algo)

        # Asignar hash al artículo usando el método público
        article.update_quality_assessment(content_hash=content_hash.hash_value)

        return content_hash

    def generate_hash_for_deduplication(
        self,
        url: str,
        title: str,
        algorithm: Optional[ContentHashAlgorithm] = None,
    ) -> ContentHash:
        """
        Genera hash para deduplicación sin necesidad de artículo completo.

        Útil para verificar duplicados antes de crear artículos.

        Args:
            url: URL del artículo
            title: Título del artículo
            algorithm: Algoritmo de hashing

        Returns:
            ContentHash para deduplicación
        """
        algo = algorithm or ContentHashAlgorithm.SHA256
        return ContentHash.from_url_and_title(url, title, algo)

    def generate_hash(self, article: Article) -> ContentHash:
        """
        Genera hash de contenido para un artículo.

        Args:
            article: Artículo para el que generar el hash

        Returns:
            ContentHash generado
        """
        return self.generate_and_assign_content_hash(article)

    def assign_hash_to_article(self, article: Article) -> None:
        """
        Asigna un hash de contenido a un artículo.

        Args:
            article: Artículo al que asignar el hash
        """
        # Generar hash usando estrategia RSS
        content_hash = self._generate_rss_content_hash(
            article, ContentHashAlgorithm.SHA256
        )
        article.update_quality_assessment(content_hash=content_hash.hash_value)

    def is_article_duplicate_by_hash(self, article: Article, other_hash: str) -> bool:
        """
        Verifica si un artículo es duplicado basándose en hash.

        Args:
            article: Artículo a verificar
            other_hash: Hash con el que comparar

        Returns:
            True si es duplicado, False otherwise
        """
        if not article.quality.content_hash:
            return False
        return article.quality.content_hash == other_hash

    def compare_content_hashes(self, hash1: ContentHash, hash2: ContentHash) -> bool:
        """
        Compara dos hashes de contenido.

        Args:
            hash1: Primer hash
            hash2: Segundo hash

        Returns:
            True si los hashes son idénticos
        """
        return hash1.hash_value == hash2.hash_value

    def generate_content_hash_from_text(
        self,
        text: str,
        algorithm: Optional[ContentHashAlgorithm] = None,
    ) -> ContentHash:
        """
        Genera hash directamente desde texto.

        Args:
            text: Contenido de texto para hashear
            algorithm: Algoritmo de hashing

        Returns:
            ContentHash generado
        """
        algo = algorithm or ContentHashAlgorithm.SHA256
        return ContentHash.from_content(text, algo)

    def are_articles_duplicate_by_hash(
        self, article1: Article, article2: Article
    ) -> bool:
        """
        Compara dos artículos por sus hashes de contenido.

        Método centralizado para comparación de hashes entre artículos.

        Args:
            article1: Primer artículo
            article2: Segundo artículo

        Returns:
            True si ambos artículos tienen el mismo hash de contenido
        """
        if not article1.quality.content_hash or not article2.quality.content_hash:
            return False
        return article1.quality.content_hash == article2.quality.content_hash

    def find_articles_with_hash(
        self, articles: List[Article], target_hash: str
    ) -> List[Article]:
        """
        Encuentra todos los artículos que tienen un hash específico.

        Args:
            articles: Lista de artículos donde buscar
            target_hash: Hash objetivo a buscar

        Returns:
            Lista de artículos que coinciden con el hash
        """
        return [a for a in articles if a.quality.content_hash == target_hash]

    def get_articles_without_hash(self, articles: List[Article]) -> List[Article]:
        """
        Encuentra artículos que no tienen hash de contenido asignado.

        Args:
            articles: Lista de artículos a verificar

        Returns:
            Lista de artículos sin hash asignado
        """
        return [a for a in articles if not a.quality.content_hash]

    # Private helper methods

    def _generate_rss_content_hash(
        self, article: Article, algorithm: ContentHashAlgorithm
    ) -> ContentHash:
        """
        Genera hash específico para contenido RSS.

        Estrategia: Combina URL y título para detectar duplicados
        incluso si el contenido del cuerpo difiere ligeramente.
        """
        return ContentHash.from_url_and_title(
            article.metadata.url.value, article.metadata.title.value, algorithm
        )

    def _has_sufficient_content_for_hashing(self, article: Article) -> bool:
        """
        Verifica si el artículo tiene contenido suficiente para generar hash.

        Returns:
            True si el artículo tiene contenido, URL y título válidos
        """
        # Verificar que tenga contenido (markdown o plaintext)
        has_content = (
            article.content.markdown and article.content.markdown.strip()
        ) or (article.content.plaintext and article.content.plaintext.strip())
        if not has_content:
            return False

        # Verificar que tenga URL y título válidos
        if not article.metadata.url or not article.metadata.title:
            return False

        return True
