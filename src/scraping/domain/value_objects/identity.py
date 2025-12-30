"""ScrapingIdentity Value Object - Identidad del Scraping aggregate."""

from dataclasses import dataclass

from src.rss.feed.domain.value_objects import SourceId


@dataclass(frozen=True)
class ScrapingIdentity:
    """
    Identidad del Scraping aggregate.

    Agrupa los campos que identifican únicamente una sesión de scraping:
    - ID único de la sesión
    - Source ID asociado (para compatibilidad)
    - Versión para optimistic locking

    Este VO es inmutable y siempre viaja junto en el aggregate.
    """

    id: str
    source_id: SourceId
    version: int = 0

    def __post_init__(self) -> None:
        """Valida la identidad."""
        if not self.id:
            raise ValueError("Scraping ID no puede estar vacío")

        if not isinstance(self.source_id, SourceId):
            raise ValueError("source_id debe ser un SourceId")

        if self.version < 0:
            raise ValueError("version no puede ser negativa")

    def with_incremented_version(self) -> "ScrapingIdentity":
        """
        Retorna nueva instancia con versión incrementada.

        Usado para optimistic locking en persistencia.

        Returns:
            Nueva ScrapingIdentity con version + 1
        """
        return ScrapingIdentity(
            id=self.id,
            source_id=self.source_id,
            version=self.version + 1,
        )

    def __str__(self) -> str:
        """Representación string."""
        return f"Scraping({self.id}, source={self.source_id}, v{self.version})"
