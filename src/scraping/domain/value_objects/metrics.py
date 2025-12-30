"""ScrapingMetrics Value Object para métricas de sesiones de scraping."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ScrapingMetrics:
    """
    Value Object para métricas de sesiones de scraping.

    Encapsula todas las métricas relacionadas con el rendimiento y resultados
    de una sesión de scraping, incluyendo artículos descubiertos, sources procesados
    y métricas de performance.

    Attributes:
        articles_discovered: Total de artículos descubiertos
        articles_new: Artículos nuevos (no existían antes)
        articles_updated: Artículos actualizados (ya existían)
        sources_successful: Sources procesados exitosamente
        sources_failed: Sources que fallaron
        total_processing_time_seconds: Tiempo total de procesamiento
        average_response_time_ms: Tiempo promedio de respuesta en milisegundos

    Example:
        >>> metrics = ScrapingMetrics(
        ...     articles_discovered=100,
        ...     articles_new=80,
        ...     articles_updated=20,
        ...     sources_successful=5,
        ...     sources_failed=1,
        ...     total_processing_time_seconds=120.5,
        ...     average_response_time_ms=450.0
        ... )
        >>> metrics.calculate_success_rate()
        0.83
    """

    articles_discovered: int = 0
    articles_new: int = 0
    articles_updated: int = 0
    sources_successful: int = 0
    sources_failed: int = 0
    total_processing_time_seconds: float = 0.0
    average_response_time_ms: float = 0.0

    def __post_init__(self):
        """Valida que los valores sean no negativos."""
        if self.articles_discovered < 0:
            raise ValueError("articles_discovered no puede ser negativo")
        if self.articles_new < 0:
            raise ValueError("articles_new no puede ser negativo")
        if self.articles_updated < 0:
            raise ValueError("articles_updated no puede ser negativo")
        if self.sources_successful < 0:
            raise ValueError("sources_successful no puede ser negativo")
        if self.sources_failed < 0:
            raise ValueError("sources_failed no puede ser negativo")
        if self.total_processing_time_seconds < 0:
            raise ValueError("total_processing_time_seconds no puede ser negativo")
        if self.average_response_time_ms < 0:
            raise ValueError("average_response_time_ms no puede ser negativo")

    def calculate_success_rate(self) -> float:
        """
        Calcula la tasa de éxito de sources procesados.

        Returns:
            Tasa de éxito entre 0.0 y 1.0

        Example:
            >>> metrics = ScrapingMetrics(
            ...     sources_successful=5,
            ...     sources_failed=1
            ... )
            >>> metrics.calculate_success_rate()
            0.83
        """
        total_sources = self.sources_successful + self.sources_failed
        if total_sources == 0:
            return 0.0
        return round(self.sources_successful / total_sources, 2)

    def calculate_throughput(self) -> float:
        """
        Calcula el throughput en artículos por segundo.

        Returns:
            Artículos procesados por segundo

        Example:
            >>> metrics = ScrapingMetrics(
            ...     articles_discovered=100,
            ...     total_processing_time_seconds=50.0
            ... )
            >>> metrics.calculate_throughput()
            2.0
        """
        if self.total_processing_time_seconds == 0:
            return 0.0
        return round(self.articles_discovered / self.total_processing_time_seconds, 2)

    def to_dict(self) -> dict:
        """
        Serializa las métricas a diccionario.

        Returns:
            Diccionario con todas las métricas
        """
        return {
            "articles_discovered": self.articles_discovered,
            "articles_new": self.articles_new,
            "articles_updated": self.articles_updated,
            "sources_successful": self.sources_successful,
            "sources_failed": self.sources_failed,
            "total_processing_time_seconds": self.total_processing_time_seconds,
            "average_response_time_ms": self.average_response_time_ms,
            "success_rate": self.calculate_success_rate(),
            "throughput": self.calculate_throughput(),
        }

    @classmethod
    def empty(cls) -> "ScrapingMetrics":
        """
        Crea métricas vacías (todos los valores en 0).

        Returns:
            Métricas con valores iniciales
        """
        return cls()

    @classmethod
    def from_dict(cls, data: dict) -> "ScrapingMetrics":
        """
        Crea una instancia desde un diccionario.

        Args:
            data: Diccionario con los valores de métricas

        Returns:
            Nueva instancia de ScrapingMetrics
        """
        return cls(
            articles_discovered=data.get("articles_discovered", 0),
            articles_new=data.get("articles_new", 0),
            articles_updated=data.get("articles_updated", 0),
            sources_successful=data.get("sources_successful", 0),
            sources_failed=data.get("sources_failed", 0),
            total_processing_time_seconds=data.get(
                "total_processing_time_seconds", 0.0
            ),
            average_response_time_ms=data.get("average_response_time_ms", 0.0),
        )
