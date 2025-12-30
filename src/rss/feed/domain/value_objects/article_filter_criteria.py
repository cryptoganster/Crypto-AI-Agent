"""Value Object: ArticleFilterCriteria - Criterios de filtrado para artículos RSS."""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from src.rss.feed.domain.value_objects.content_quality import ContentQuality


@dataclass(frozen=True)
class ArticleFilterCriteria:
    """
    Value Object que representa criterios de filtrado complejos para artículos RSS.

    Inmutable - encapsula reglas de negocio para filtrado de artículos.
    """

    min_quality: ContentQuality
    max_quality: Optional[ContentQuality] = None
    required_categories: Optional[List[str]] = None
    excluded_categories: Optional[List[str]] = None
    required_tags: Optional[List[str]] = None
    excluded_tags: Optional[List[str]] = None
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    required_statuses: Optional[List[str]] = None
    excluded_statuses: Optional[List[str]] = None
    source_ids_filter: Optional[List[str]] = None
    custom_filters: Optional[Dict[str, Any]] = None

    @classmethod
    def create_basic(cls, min_quality: ContentQuality) -> "ArticleFilterCriteria":
        """Crea criterios básicos con calidad mínima."""
        return cls(min_quality=min_quality)

    @classmethod
    def create_strict(cls) -> "ArticleFilterCriteria":
        """Crea criterios estrictos para artículos premium RSS."""
        return cls(
            min_quality=ContentQuality.HIGH,
            min_length=100,
            max_length=10000,
            excluded_statuses=[
                "draft",
                "error",
            ],
        )

    @classmethod
    def create_published_only(cls) -> "ArticleFilterCriteria":
        """Crea criterios para artículos publicados únicamente."""
        return cls(
            min_quality=ContentQuality.MEDIUM,
            required_statuses=["published"],
        )

    def is_permissive(self) -> bool:
        """Indica si los criterios son permisivos."""
        return (
            self.min_quality == ContentQuality.LOW
            and not self.required_categories
            and not self.required_tags
            and not self.min_length
            and not self.required_statuses
        )

    def has_category_filters(self) -> bool:
        """Indica si tiene filtros de categorías."""
        return bool(self.required_categories or self.excluded_categories)

    def has_tag_filters(self) -> bool:
        """Indica si tiene filtros de etiquetas."""
        return bool(self.required_tags or self.excluded_tags)

    def has_status_filters(self) -> bool:
        """Indica si tiene filtros de estado."""
        return bool(self.required_statuses or self.excluded_statuses)

    def has_source_filters(self) -> bool:
        """Indica si tiene filtros por fuente."""
        return bool(self.source_ids_filter)
