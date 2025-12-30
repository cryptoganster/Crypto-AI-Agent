"""Query para obtener estado de procesamiento de artículo."""

from dataclasses import dataclass


@dataclass(frozen=True)
class GetProcessingStatusQuery:
    """
    Query para obtener estado de procesamiento de un artículo.

    Attributes:
        article_id: ID del artículo
    """

    article_id: str

    def __post_init__(self):
        """Valida el query."""
        if not self.article_id or not self.article_id.strip():
            raise ValueError("article_id no puede estar vacío")
