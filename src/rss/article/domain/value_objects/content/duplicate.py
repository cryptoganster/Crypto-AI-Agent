"""Value Object para información de duplicación del artículo."""

from dataclasses import dataclass
from typing import Optional

from src.rss.article.domain.value_objects.metadata import ArticleId


@dataclass(frozen=True)
class ArticleDuplicate:
    """
    Value Object para información de duplicación.

    Encapsula el estado de duplicación de un artículo, indicando si es un duplicado
    y de qué artículo es duplicado.

    Invariantes:
    - Si is_duplicate es True, duplicate_of_article_id debe ser no-None
    - Los campos son inmutables (frozen dataclass)

    Attributes:
        is_duplicate: Indica si el artículo es un duplicado
        duplicate_of_article_id: ID del artículo original (si es duplicado)
    """

    is_duplicate: bool = False
    duplicate_of_article_id: Optional[ArticleId] = None

    def __post_init__(self):
        """
        Valida consistencia entre is_duplicate y duplicate_of_article_id.

        Si is_duplicate es True, duplicate_of_article_id debe estar presente.

        Raises:
            ValueError: Si is_duplicate es True pero duplicate_of_article_id es None
        """
        if self.is_duplicate and self.duplicate_of_article_id is None:
            raise ValueError(
                "Si is_duplicate es True, duplicate_of_article_id es requerido. "
                "No puede marcar un artículo como duplicado sin especificar el original."
            )

    @staticmethod
    def not_duplicate() -> "ArticleDuplicate":
        """
        Crea instancia para artículo no duplicado.

        Factory method para crear ArticleDuplicate indicando que el artículo
        no es un duplicado.

        Returns:
            ArticleDuplicate con is_duplicate=False y duplicate_of_article_id=None

        Example:
            >>> info = ArticleDuplicate.not_duplicate()
            >>> info.is_duplicate
            False
            >>> info.duplicate_of_article_id is None
            True
        """
        return ArticleDuplicate(is_duplicate=False, duplicate_of_article_id=None)

    @staticmethod
    def duplicate_of(article_id: ArticleId) -> "ArticleDuplicate":
        """
        Crea instancia para artículo duplicado.

        Factory method para crear ArticleDuplicate indicando que el artículo
        es un duplicado de otro artículo específico.

        Args:
            article_id: ID del artículo original del cual este es duplicado

        Returns:
            ArticleDuplicate con is_duplicate=True y duplicate_of_article_id establecido

        Raises:
            ValueError: Si article_id es None

        Example:
            >>> original_id = ArticleId.generate()
            >>> info = ArticleDuplicate.duplicate_of(original_id)
            >>> info.is_duplicate
            True
            >>> info.duplicate_of_article_id == original_id
            True
        """
        if article_id is None:
            raise ValueError("article_id no puede ser None al crear duplicado")

        return ArticleDuplicate(is_duplicate=True, duplicate_of_article_id=article_id)

    @property
    def has_original_reference(self) -> bool:
        """
        Verifica si tiene referencia al artículo original.

        Returns:
            True si duplicate_of_article_id no es None
        """
        return self.duplicate_of_article_id is not None

    def mark_as_not_duplicate(self) -> "ArticleDuplicate":
        """
        Retorna nueva instancia marcando el artículo como no duplicado.

        Útil para revertir el estado de duplicación.

        Returns:
            Nueva instancia de ArticleDuplicate con is_duplicate=False

        Example:
            >>> original_id = ArticleId.generate()
            >>> info = ArticleDuplicate.duplicate_of(original_id)
            >>> reverted = info.mark_as_not_duplicate()
            >>> reverted.is_duplicate
            False
            >>> reverted.duplicate_of_article_id is None
            True
        """
        return ArticleDuplicate.not_duplicate()

    def mark_as_duplicate_of(self, article_id: ArticleId) -> "ArticleDuplicate":
        """
        Retorna nueva instancia marcando el artículo como duplicado.

        Args:
            article_id: ID del artículo original

        Returns:
            Nueva instancia de ArticleDuplicate con is_duplicate=True

        Raises:
            ValueError: Si article_id es None
        """
        return ArticleDuplicate.duplicate_of(article_id)
