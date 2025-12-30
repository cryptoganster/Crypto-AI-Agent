"""Command para generar embeddings de chunks."""

from dataclasses import dataclass


@dataclass(frozen=True)
class GenerateChunkEmbeddingsCommand:
    """
    Command para generar embeddings de chunks de un artículo.

    Este comando genera embeddings vectoriales para todos los chunks
    de un artículo usando el servicio de embeddings configurado.

    Attributes:
        article_id: ID del artículo cuyos chunks necesitan embeddings
        correlation_id: ID de correlación para tracking (opcional)
        triggered_by: Identificador de quién/qué disparó el comando (opcional)

    Example:
        >>> command = GenerateChunkEmbeddingsCommand(
        ...     article_id="art-123",
        ...     correlation_id="corr-456",
        ...     triggered_by="ArticleAIProcessingPipeline"
        ... )
    """

    article_id: str
    correlation_id: str | None = None
    triggered_by: str | None = None
