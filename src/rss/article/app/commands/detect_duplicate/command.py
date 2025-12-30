"""Command para detectar artículos duplicados usando embeddings."""

from dataclasses import dataclass


@dataclass(frozen=True)
class DetectDuplicateArticleCommand:
    """
    Command para detectar duplicados semánticos de un artículo.

    Este comando se emite cuando un artículo tiene su embedding generado
    y necesitamos verificar si es duplicado de artículos existentes.

    Attributes:
        article_id: ID del artículo a verificar
        max_results: Máximo número de duplicados a retornar (default: 10)
    """

    article_id: str
    max_results: int = 10
