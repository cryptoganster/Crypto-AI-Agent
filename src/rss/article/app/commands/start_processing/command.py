"""Comando para iniciar el pipeline de procesamiento de artículos."""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class StartArticleProcessingCommand:
    """
    Comando para iniciar el pipeline de procesamiento de artículos.

    Este comando inicia el flujo event-driven de procesamiento:
    1. ContentExtractorPipeline (scraping, plaintext, markdown)
    2. ContentAnalysisPipeline (metrics, language, summary, keywords, quality)

    Args:
        limit: Número máximo de artículos a procesar
        correlation_id: ID de correlación para tracking
    """

    limit: int = 100
    correlation_id: Optional[str] = None
