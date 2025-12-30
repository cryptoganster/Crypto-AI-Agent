"""RssFeedHealth Value Object - Estado de salud del RssFeed."""

from dataclasses import dataclass
from typing import Optional

from src.rss.feed.domain.value_objects.metrics import RssFeedMetrics
from src.rss.feed.domain.value_objects.status import RssFeedStatus


@dataclass(frozen=True)
class RssFeedHealth:
    """
    Value Object compuesto para salud del RssFeed.

    Agrupa el estado operacional y las métricas de salud
    del RssFeed aggregate.

    Attributes:
        status: Estado actual de la fuente (active, inactive, suspended, error)
        metrics: Métricas agregadas de fetch operations (opcional)
    """

    status: RssFeedStatus
    metrics: Optional[RssFeedMetrics]

    @classmethod
    def create_inactive(cls) -> "RssFeedHealth":
        """
        Crea instancia con estado inactivo inicial.

        Returns:
            Nueva instancia con status inactive y sin métricas
        """
        return cls(
            status=RssFeedStatus.inactive(),
            metrics=None,
        )

    @classmethod
    def create_active(cls) -> "RssFeedHealth":
        """
        Crea instancia con estado activo.

        Returns:
            Nueva instancia con status active y sin métricas
        """
        return cls(
            status=RssFeedStatus.active(),
            metrics=None,
        )

    def is_healthy(self) -> bool:
        """
        Determina si la fuente está saludable.

        Una fuente se considera saludable si:
        - Está activa
        - Tiene success rate >= 70%
        - Tiene menos de 3 fallos consecutivos

        Returns:
            True si la fuente está saludable
        """
        if self.metrics is None:
            # Fuente nueva sin métricas se considera saludable
            return True

        return (
            self.metrics.success_rate >= 0.7
            and self.metrics.consecutive_failures < 3
            and self.status.is_active()
        )

    def is_active(self) -> bool:
        """
        Verifica si la fuente está activa.

        Returns:
            True si el status es active
        """
        return self.status.is_active()

    def with_status(self, status: RssFeedStatus) -> "RssFeedHealth":
        """
        Crea nueva instancia con status actualizado.

        Args:
            status: Nuevo status

        Returns:
            Nueva instancia con status actualizado
        """
        return RssFeedHealth(
            status=status,
            metrics=self.metrics,
        )

    def with_metrics(self, metrics: Optional[RssFeedMetrics]) -> "RssFeedHealth":
        """
        Crea nueva instancia con métricas actualizadas.

        Args:
            metrics: Nuevas métricas

        Returns:
            Nueva instancia con métricas actualizadas
        """
        return RssFeedHealth(
            status=self.status,
            metrics=metrics,
        )

    def with_reset_metrics(self) -> "RssFeedHealth":
        """
        Crea nueva instancia con métricas reseteadas.

        Útil cuando se reactiva una fuente después de resolver problemas.

        Returns:
            Nueva instancia con métricas reseteadas
        """
        if self.metrics is None:
            return self

        reset_metrics = RssFeedMetrics(
            total_fetch_attempts=self.metrics.total_fetch_attempts,
            successful_fetches=self.metrics.successful_fetches,
            failed_fetches=0,  # Reset
            consecutive_failures=0,  # Reset
            last_fetch_at=self.metrics.last_fetch_at,
            last_successful_fetch_at=self.metrics.last_successful_fetch_at,
            last_error_at=None,  # Reset
            last_error_message=None,  # Reset
            average_response_time_ms=self.metrics.average_response_time_ms,
            total_articles_discovered=self.metrics.total_articles_discovered,
            last_articles_count=self.metrics.last_articles_count,
        )

        return RssFeedHealth(
            status=self.status,
            metrics=reset_metrics,
        )


# Alias para compatibilidad hacia atrás
SourceHealth = RssFeedHealth
