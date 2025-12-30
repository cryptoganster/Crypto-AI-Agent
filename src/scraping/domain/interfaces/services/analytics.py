"""Interface para Scraping Analytics Service."""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

if TYPE_CHECKING:
    from src.scraping.domain.aggregates import Scraping

from src.scraping.domain.value_objects.status import ScrapingStatus


class ScrapingStatistics:
    """DTO para estadísticas agregadas de Scraping sessions."""

    total_sessions: int
    completed_sessions: int
    failed_sessions: int
    active_sessions: int
    avg_duration_seconds: float
    total_articles_discovered: int
    total_sources_processed: int
    success_rate: float


class IScrapingAnalyticsService(ABC):
    """
    Interface para Domain Service de análisis de Scraping sessions.

    Extrae lógica de negocio de cálculo de métricas y estadísticas
    que NO pertenece al aggregate ni a la infraestructura.

    Principios DDD:
    - Stateless service
    - Lógica de dominio pura
    - Sin dependencias de infraestructura
    - Reutilizable desde Application Layer
    """

    @abstractmethod
    def calculate_session_statistics(
        self,
        sessions: List["Scraping"],
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> ScrapingStatistics:
        """
        Calcula estadísticas agregadas de Scraping sessions.

        Args:
            sessions: Lista de Scraping sessions a analizar
            start_date: Fecha inicio opcional (para filtrado)
            end_date: Fecha fin opcional (para filtrado)

        Returns:
            ScrapingStatistics con métricas agregadas
        """
        ...

    @abstractmethod
    def calculate_average_duration(
        self,
        sessions: List["Scraping"],
        status_filter: Optional[ScrapingStatus] = None,
    ) -> float:
        """
        Calcula duración promedio de sesiones.

        Args:
            sessions: Lista de Scraping sessions
            status_filter: Filtro opcional por estado

        Returns:
            Duración promedio en segundos
        """
        ...
