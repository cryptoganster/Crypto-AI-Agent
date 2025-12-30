"""Command para generar TLDR de un artículo."""

from dataclasses import dataclass


@dataclass(frozen=True)
class GenerateTLDRCommand:
    """
    Command para generar TLDR (Too Long; Didn't Read) de un artículo.

    Este comando toma todos los chunk summaries de un artículo
    y los fusiona en un TLDR conciso (3-5 bullets) usando el
    servicio de summarization.

    Attributes:
        article_id: ID del artículo para generar TLDR
        correlation_id: ID de correlación para tracking (opcional)
        triggered_by: Identificador de quién/qué disparó el comando (opcional)
    """

    article_id: str
    correlation_id: str | None = None
    triggered_by: str | None = None
