"""Result Object para ScrapeSourceCommand."""

from dataclasses import dataclass
from typing import List, Optional


@dataclass(frozen=True)
class ScrapeSourceResult:
    """
    Resultado de la ejecución de ScrapeSourceCommand.

    Contiene información sobre el resultado del scraping
    de una única source RSS.

    Attributes:
        success: Si la operación fue exitosa
        source_id: ID de la source scrapeada
        articles_count: Número de artículos obtenidos
        new_articles_count: Número de artículos nuevos (no duplicados)
        article_ids: Lista de IDs de artículos creados
        error: Mensaje de error si falló
        pipeline_id: ID del pipeline que solicitó el scraping
    """

    success: bool
    source_id: str
    articles_count: int = 0
    new_articles_count: int = 0
    article_ids: tuple = ()
    error: Optional[str] = None
    pipeline_id: Optional[str] = None

    @classmethod
    def success_result(
        cls,
        source_id: str,
        articles_count: int,
        new_articles_count: int,
        article_ids: List[str],
        pipeline_id: Optional[str] = None,
    ) -> "ScrapeSourceResult":
        """
        Crea resultado exitoso.

        Args:
            source_id: ID de la source
            articles_count: Total de artículos obtenidos
            new_articles_count: Artículos nuevos
            article_ids: IDs de artículos creados
            pipeline_id: ID del pipeline

        Returns:
            ScrapeSourceResult exitoso
        """
        return cls(
            success=True,
            source_id=source_id,
            articles_count=articles_count,
            new_articles_count=new_articles_count,
            article_ids=tuple(article_ids),
            pipeline_id=pipeline_id,
        )

    @classmethod
    def failure_result(
        cls,
        source_id: str,
        error: str,
        pipeline_id: Optional[str] = None,
    ) -> "ScrapeSourceResult":
        """
        Crea resultado de fallo.

        Args:
            source_id: ID de la source
            error: Mensaje de error
            pipeline_id: ID del pipeline

        Returns:
            ScrapeSourceResult fallido
        """
        return cls(
            success=False,
            source_id=source_id,
            error=error,
            pipeline_id=pipeline_id,
        )
