"""Domain Service para análisis y métricas de Scraping sessions."""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List, Optional

from src.scraping.domain.aggregates import Scraping
from src.scraping.domain.interfaces.services.analytics import (
    IScrapingAnalyticsService,
)
from src.scraping.domain.interfaces.services.analytics import (
    ScrapingStatistics as IScrapingStatistics,
)
from src.scraping.domain.value_objects.status import ScrapingStatus


@dataclass(frozen=True)
class ScrapingStatistics(IScrapingStatistics):
    """DTO para estadísticas agregadas de Scraping sessions."""

    total_sessions: int
    completed_sessions: int
    failed_sessions: int
    active_sessions: int
    avg_duration_seconds: float
    total_articles_discovered: int
    total_sources_processed: int
    success_rate: float


class ScrapingAnalyticsService(IScrapingAnalyticsService):
    """
    Domain Service para análisis de Scraping sessions.

    Extrae lógica de negocio de cálculo de métricas y estadísticas
    que NO pertenece al aggregate ni a la infraestructura.

    Principios DDD:
    - Stateless service
    - Lógica de dominio pura
    - Sin dependencias de infraestructura
    - Reutilizable desde Application Layer
    """

    def calculate_session_statistics(
        self,
        sessions: List[Scraping],
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
        # Filtrar por fechas si se proporcionan
        filtered_sessions = self._filter_by_dates(sessions, start_date, end_date)

        total_sessions = len(filtered_sessions)
        completed_sessions = self._count_by_status(
            filtered_sessions, ScrapingStatus.COMPLETED
        )
        failed_sessions = self._count_by_status(
            filtered_sessions, ScrapingStatus.FAILED
        )
        active_sessions = self._count_active_sessions(filtered_sessions)

        avg_duration = self._calculate_avg_duration(filtered_sessions)
        total_articles = self._sum_articles_discovered(filtered_sessions)
        total_sources = self._sum_sources_processed(filtered_sessions)
        success_rate = self._calculate_success_rate(completed_sessions, total_sessions)

        return ScrapingStatistics(
            total_sessions=total_sessions,
            completed_sessions=completed_sessions,
            failed_sessions=failed_sessions,
            active_sessions=active_sessions,
            avg_duration_seconds=avg_duration,
            total_articles_discovered=total_articles,
            total_sources_processed=total_sources,
            success_rate=success_rate,
        )

    def calculate_average_duration(
        self,
        sessions: List[Scraping],
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
        filtered = (
            [s for s in sessions if s.state.status == status_filter]
            if status_filter
            else sessions
        )

        return self._calculate_avg_duration(filtered)

    # ==================== PRIVATE HELPERS ====================

    def _filter_by_dates(
        self,
        sessions: List[Scraping],
        start_date: Optional[datetime],
        end_date: Optional[datetime],
    ) -> List[Scraping]:
        """Filtra sesiones por rango de fechas."""
        if not start_date and not end_date:
            return sessions

        filtered = sessions
        if start_date:
            filtered = [s for s in filtered if s.timestamps.created_at >= start_date]
        if end_date:
            filtered = [s for s in filtered if s.timestamps.created_at <= end_date]

        return filtered

    def _count_by_status(self, sessions: List[Scraping], status: ScrapingStatus) -> int:
        """Cuenta sesiones por estado."""
        return len([s for s in sessions if s.state.status == status])

    def _count_active_sessions(self, sessions: List[Scraping]) -> int:
        """Cuenta sesiones activas (pending, running)."""
        return len(
            [
                s
                for s in sessions
                if s.state.status in [ScrapingStatus.PENDING, ScrapingStatus.RUNNING]
            ]
        )

    def _calculate_avg_duration(self, sessions: List[Scraping]) -> float:
        """Calcula duración promedio de sesiones."""
        sessions_with_duration = [
            s
            for s in sessions
            if s.state.status
            in [
                ScrapingStatus.COMPLETED,
                ScrapingStatus.FAILED,
                ScrapingStatus.CANCELLED,
            ]
            and s.timestamps.created_at
            and s.timestamps.updated_at
        ]

        if not sessions_with_duration:
            return 0.0

        # Calcular duración desde timestamps
        total_duration = sum(
            (s.timestamps.updated_at - s.timestamps.created_at).total_seconds()
            for s in sessions_with_duration
        )
        return total_duration / len(sessions_with_duration)

    def _sum_articles_discovered(self, sessions: List[Scraping]) -> int:
        """Suma total de artículos descubiertos desde scraping_history."""
        total = 0
        for session in sessions:
            # Contar desde scraping_history records completados
            for record in session.scraping_history:
                if hasattr(record, "articles_found"):
                    total += getattr(record, "articles_found", 0)
        return total

    def _sum_sources_processed(self, sessions: List[Scraping]) -> int:
        """Suma total de sources procesados."""
        return sum(
            len(getattr(s, "sources_completed", []) or [])
            + len(getattr(s, "sources_failed", []) or [])
            for s in sessions
        )

    def _calculate_success_rate(self, completed: int, total: int) -> float:
        """Calcula tasa de éxito porcentual."""
        return (completed / total * 100) if total > 0 else 0.0
