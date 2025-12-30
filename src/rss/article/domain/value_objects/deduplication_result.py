"""Value Object: ArticleDeduplicationResult - Resultado de verificación de duplicados."""

from dataclasses import dataclass, field
from typing import Optional

from src.rss.article.domain.value_objects.metadata import ArticleId


@dataclass(frozen=True)
class RssArticleDeduplicationResult:
    """
    Value Object que representa el resultado de verificación de duplicados de un artículo.

    Inmutable y sin identidad - dos resultados con los mismos valores son equivalentes.
    """

    article_id: ArticleId
    is_duplicate: bool
    original_article_id: Optional[ArticleId] = None
    similarity_score: Optional[float] = None
    detection_method: str = "none"  # hash, similarity, hybrid

    def __post_init__(self):
        """Validaciones de invariantes del VO."""
        if self.is_duplicate and self.original_article_id is None:
            raise ValueError(
                "Si is_duplicate=True, original_article_id no puede ser None"
            )

        if self.similarity_score is not None and not (
            0.0 <= self.similarity_score <= 1.0
        ):
            raise ValueError("similarity_score debe estar entre 0.0 y 1.0")

        valid_methods = {"none", "hash", "similarity", "hybrid"}
        if self.detection_method not in valid_methods:
            raise ValueError(f"detection_method debe ser uno de {valid_methods}")


# Alias para compatibilidad
ArticleDeduplicationResult = RssArticleDeduplicationResult
