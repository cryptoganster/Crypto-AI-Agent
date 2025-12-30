"""Interface para Scraping Write Repository - CQRS Command Side."""

from typing import Protocol

from src.scraping.domain.aggregates import Scraping
from src.scraping.domain.value_objects import ScrapingIdentity


class IScrapingWriteRepository(Protocol):
    """
    Interface para operaciones de ESCRITURA del aggregate Scraping.

    Siguiendo CQRS, este repositorio solo maneja Commands (mutaciones).
    """

    async def save(self, scraping: Scraping) -> None:
        """Persiste o actualiza un Scraping aggregate."""
        ...

    async def delete(self, scraping_id: ScrapingIdentity) -> bool:
        """Elimina un Scraping por su ID."""
        ...

    async def exists(self, scraping_id: ScrapingIdentity) -> bool:
        """Verifica si existe un Scraping con el ID dado."""
        ...
