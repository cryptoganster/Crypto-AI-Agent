"""Interface para ArticleHashingService - Inversión de Dependencias DDD."""

from typing import TYPE_CHECKING, Optional, Protocol

from src.rss.article.domain.value_objects.similarity import (
    ContentHash,
    ContentHashAlgorithm,
)

if TYPE_CHECKING:
    from src.rss.article.domain.aggregates.rss_article import RssArticle as Article


class IArticleHashingService(Protocol):
    """
    Interface para ArticleHashingService siguiendo principio de Inversión de Dependencias.

    Define el contrato para servicios de generación y gestión de hashes de artículos RSS
    sin acoplarse a implementaciones concretas.
    """

    def generate_and_assign_content_hash(
        self,
        article: "Article",
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
        ...

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
        ...

    def generate_hash(self, article: "Article") -> ContentHash:
        """
        Genera hash de contenido para un artículo.

        Args:
            article: Artículo para el que generar el hash

        Returns:
            ContentHash generado
        """
        ...

    def assign_hash_to_article(self, article: "Article") -> None:
        """
        Asigna un hash de contenido a un artículo.

        Args:
            article: Artículo al que asignar el hash
        """
        ...

    def is_article_duplicate_by_hash(self, article: "Article", other_hash: str) -> bool:
        """
        Verifica si un artículo es duplicado basándose en hash.

        Args:
            article: Artículo a verificar
            other_hash: Hash con el que comparar

        Returns:
            True si es duplicado, False otherwise
        """
        ...

    def compare_content_hashes(self, hash1: ContentHash, hash2: ContentHash) -> bool:
        """
        Compara dos hashes de contenido.

        Args:
            hash1: Primer hash
            hash2: Segundo hash

        Returns:
            True si los hashes son idénticos
        """
        ...

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
        ...

    def are_articles_duplicate_by_hash(
        self, article1: "Article", article2: "Article"
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
        ...

    def find_articles_with_hash(
        self, articles: list["Article"], target_hash: str
    ) -> list["Article"]:
        """
        Encuentra todos los artículos que tienen un hash específico.

        Args:
            articles: Lista de artículos donde buscar
            target_hash: Hash objetivo a buscar

        Returns:
            Lista de artículos que coinciden con el hash
        """
        ...

    def get_articles_without_hash(self, articles: list["Article"]) -> list["Article"]:
        """
        Encuentra artículos que no tienen hash de contenido asignado.

        Args:
            articles: Lista de artículos a verificar

        Returns:
            Lista de artículos sin hash asignado
        """
        ...
