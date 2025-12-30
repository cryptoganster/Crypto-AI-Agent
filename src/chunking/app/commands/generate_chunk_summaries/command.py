"""Command para generar summaries de chunks."""

from dataclasses import dataclass


@dataclass(frozen=True)
class GenerateChunkSummariesCommand:
    """
    Command para generar summaries de chunks de un artículo.

    Este comando genera summaries individuales para cada chunk usando
    el servicio de summarization. Los summaries se usan posteriormente
    para generar el summary global y el TLDR.

    Attributes:
        article_id: ID del artículo cuyos chunks se van a summarizar
        correlation_id: ID de correlación para tracking (opcional)
        triggered_by: Identificador de quién/qué disparó el comando (opcional)

    Example:
        >>> command = GenerateChunkSummariesCommand(
        ...     article_id="art-123",
        ...     correlation_id="corr-456",
        ...     triggered_by="ArticleAIProcessingPipeline"
        ... )
    """

    article_id: str
    correlation_id: str | None = None
    triggered_by: str | None = None
