"""Resultado del comando StartScraping."""

from dataclasses import dataclass
from typing import List, Optional


@dataclass(frozen=True)
class StartScrapingResult:
    """
    Resultado de StartScrapingCommand.

    Este resultado indica si el scraping fue iniciado correctamente.
    NO contiene resultados del scraping (eso viene vía eventos).

    Attributes:
        success: Si el scraping fue iniciado
        scraping_id: ID de la sesión creada
        sources_count: Número de sources a procesar
        source_ids: IDs de sources a procesar
        invalid_urls: URLs que no pudieron ser resueltas
        error: Mensaje de error si falló
        error_code: Código de error si falló
    """

    success: bool
    scraping_id: str
    sources_count: int = 0
    source_ids: tuple = ()
    invalid_urls: tuple = ()
    error: Optional[str] = None
    error_code: Optional[str] = None

    @classmethod
    def started(
        cls,
        scraping_id: str,
        source_ids: List[str],
        invalid_urls: Optional[List[str]] = None,
    ) -> "StartScrapingResult":
        """Crea resultado de scraping iniciado."""
        return cls(
            success=True,
            scraping_id=scraping_id,
            sources_count=len(source_ids),
            source_ids=tuple(source_ids),
            invalid_urls=tuple(invalid_urls or []),
        )

    @classmethod
    def failure(
        cls,
        error: str,
        error_code: str,
    ) -> "StartScrapingResult":
        """Crea resultado de fallo."""
        return cls(
            success=False,
            scraping_id="none",
            error=error,
            error_code=error_code,
        )

    @classmethod
    def no_sources(
        cls,
        invalid_urls: Optional[List[str]] = None,
    ) -> "StartScrapingResult":
        """Crea resultado cuando no hay sources."""
        return cls(
            success=False,
            scraping_id="none",
            invalid_urls=tuple(invalid_urls or []),
            error="No hay sources disponibles para scraping",
            error_code="NO_SOURCES",
        )
