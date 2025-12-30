"""Query para obtener artículo por ID."""

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class GetArticleByIdQuery:
    """
    Query para obtener un artículo por su ID.

    CQRS Read Side: Solo lectura, sin modificar estado.

    Args:
        article_id: UUID del artículo a obtener
    """

    article_id: UUID

    def __post_init__(self):
        """Validación básica."""
        if not isinstance(self.article_id, UUID):
            raise TypeError("article_id debe ser UUID")
