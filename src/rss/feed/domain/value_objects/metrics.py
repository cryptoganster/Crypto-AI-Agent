"""Source Metrics Value Object."""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List, NamedTuple, Optional

from src.shared.kernel import IValueObject


class FetchData(NamedTuple):
    """Datos primitivos de un fetch para cálculo de métricas."""

    is_successful: bool
    is_failed: bool
    articles_found: int
    articles_new: int
    response_time_ms: Optional[float]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]


@dataclass(frozen=True)
class RssFeedMetrics(IValueObject):
    """Métricas de rendimiento de un RssFeed."""

    total_fetches: int = 0
    successful_fetches: int = 0
    failed_fetches: int = 0
    total_articles_discovered: int = 0
    total_articles_new: int = 0
    last_fetch_at: Optional[datetime] = None
    last_error_at: Optional[datetime] = None
    last_successful_fetch_at: Optional[datetime] = None
    average_response_time_ms: float = 0.0
    consecutive_failures: int = 0
    health_score: float = 100.0

    @property
    def success_rate(self) -> float:
        """Tasa de éxito de fetches."""
        if self.total_fetches == 0:
            return 0.0
        return (self.successful_fetches / self.total_fetches) * 100.0

    @property
    def error_rate(self) -> float:
        """Tasa de error de fetches."""
        if self.total_fetches == 0:
            return 0.0
        return (self.failed_fetches / self.total_fetches) * 100.0

    def with_successful_fetch(
        self,
        articles_discovered: int = 0,
        articles_new: int = 0,
        response_time_ms: float = 0.0,
    ) -> "RssFeedMetrics":
        """Crea nueva instancia con fetch exitoso registrado."""
        new_total = self.total_fetches + 1
        new_successful = self.successful_fetches + 1

        # Calcular nuevo promedio de tiempo de respuesta
        if self.total_fetches > 0:
            new_avg_response = (
                self.average_response_time_ms * self.total_fetches + response_time_ms
            ) / new_total
        else:
            new_avg_response = response_time_ms

        return RssFeedMetrics(
            total_fetches=new_total,
            successful_fetches=new_successful,
            failed_fetches=self.failed_fetches,
            total_articles_discovered=self.total_articles_discovered
            + articles_discovered,
            total_articles_new=self.total_articles_new + articles_new,
            last_fetch_at=datetime.now(timezone.utc),
            last_error_at=self.last_error_at,
            last_successful_fetch_at=datetime.now(timezone.utc),
            average_response_time_ms=new_avg_response,
        )

    def with_failed_fetch(
        self, error_time: Optional[datetime] = None
    ) -> "RssFeedMetrics":
        """Crea nueva instancia con fetch fallido registrado."""
        return RssFeedMetrics(
            total_fetches=self.total_fetches + 1,
            successful_fetches=self.successful_fetches,
            failed_fetches=self.failed_fetches + 1,
            total_articles_discovered=self.total_articles_discovered,
            total_articles_new=self.total_articles_new,
            last_fetch_at=datetime.now(timezone.utc),
            last_error_at=error_time or datetime.now(timezone.utc),
            last_successful_fetch_at=self.last_successful_fetch_at,
            average_response_time_ms=self.average_response_time_ms,
        )

    @classmethod
    def calculate_from_history(
        cls, fetch_data_list: List[FetchData]
    ) -> "RssFeedMetrics":
        """
        Factory method para calcular métricas desde datos primitivos de fetch.

        Args:
            fetch_data_list: Lista de datos primitivos de fetch

        Returns:
            RssFeedMetrics calculadas desde los datos
        """
        if not fetch_data_list:
            return cls()

        # Clasificar por estado
        successful = [f for f in fetch_data_list if f.is_successful]
        failed = [f for f in fetch_data_list if f.is_failed]

        # Calcular totales de artículos
        total_articles_discovered = sum(f.articles_found for f in successful)
        total_articles_new = sum(f.articles_new for f in successful)

        # Calcular tiempo promedio de respuesta
        response_times = [f.response_time_ms for f in successful if f.response_time_ms]
        avg_response = (
            sum(response_times) / len(response_times) if response_times else 0.0
        )

        # Encontrar timestamps relevantes
        last_successful_fetch = max(
            (f.completed_at for f in successful if f.completed_at),
            default=None,
        )

        last_error = max(
            (f.started_at for f in failed if f.started_at),
            default=None,
        )

        last_fetch = max(
            (f.started_at for f in fetch_data_list if f.started_at),
            default=None,
        )

        return cls(
            total_fetches=len(fetch_data_list),
            successful_fetches=len(successful),
            failed_fetches=len(failed),
            total_articles_discovered=total_articles_discovered,
            total_articles_new=total_articles_new,
            last_fetch_at=last_fetch,
            last_error_at=last_error,
            last_successful_fetch_at=last_successful_fetch,
            average_response_time_ms=avg_response,
        )

    @classmethod
    def empty(cls) -> "SourceMetrics":
        """
        Factory method para crear métricas vacías.

        Returns:
            SourceMetrics con valores iniciales vacíos
        """
        return cls()

    def is_healthy(self, min_success_rate: float = 80.0) -> bool:
        """
        Determina si las métricas indican una fuente saludable.

        Args:
            min_success_rate: Tasa mínima de éxito requerida

        Returns:
            True si la fuente está saludable
        """
        if self.total_fetches == 0:
            return True  # Sin historial, asumimos saludable

        return self.success_rate >= min_success_rate

    def has_recent_activity(self, hours: int = 24) -> bool:
        """
        Verifica si hay actividad reciente.

        Args:
            hours: Horas hacia atrás para considerar "reciente"

        Returns:
            True si hay fetch en las últimas X horas
        """
        if not self.last_fetch_at:
            return False

        from datetime import timedelta

        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        return self.last_fetch_at >= cutoff

    def get_performance_level(self) -> str:
        """
        Evalúa el nivel de performance basado en métricas.

        Returns:
            Nivel de performance: 'excellent', 'good', 'poor', 'critical'
        """
        if self.total_fetches == 0:
            return "unknown"

        success_rate = self.success_rate

        if success_rate >= 95.0:
            return "excellent"
        elif success_rate >= 80.0:
            return "good"
        elif success_rate >= 60.0:
            return "poor"
        else:
            return "critical"


# Alias para compatibilidad hacia atrás
SourceMetrics = RssFeedMetrics
RssSourceMetrics = RssFeedMetrics
