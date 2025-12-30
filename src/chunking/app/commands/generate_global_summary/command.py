"""Command para generar summary global de un artículo."""

from dataclasses import dataclass


@dataclass(frozen=True)
class GenerateGlobalSummaryCommand:
    """
    Command para generar summary global de un artículo.

    Este comando toma todos los chunk summaries de un artículo
    y genera un summary global coherente usando el servicio de
    summarization.

    Attributes:
        article_id: ID del artículo para generar summary global
        correlation_id: ID de correlación para tracking (opcional)
        triggered_by: Identificador de quién/qué disparó el comando (opcional)
    """

    article_id: str
    correlation_id: str | None = None
    triggered_by: str | None = None
