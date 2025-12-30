"""Source Health Service - Domain Service para salud de Source.

Este servicio concentra la lógica de evaluación de salud para el aggregate
`Source`, reemplazando y unificando los servicios previos.

Principios:
- El servicio NO emite eventos. Solo realiza evaluación y retorna decisiones.
- El aggregate `Source` es el ÚNICO responsable de emitir eventos.
- Application layer orquesta: usa este servicio y luego invoca métodos del aggregate.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Literal, Optional, Tuple

from src.rss.feed.domain.aggregates import Source
from src.rss.feed.domain.interfaces.services.health import (
    ISourceHealthService,
)
from src.rss.feed.domain.value_objects.metrics import SourceMetrics
from src.shared.kernel import IDomainEvent, ITimeProvider

HealthChangeType = Literal["degraded", "recovered", "none"]


@dataclass(frozen=True)
class SourceHealthReport:
    """Reporte completo de salud de una fuente (aggregate `Source`)."""

    source_id: str
    source_name: str
    is_healthy: bool
    health_score: float  # 0-100
    issues: List[str]
    recommendations: List[str]
    last_check: datetime

    def requires_attention(self) -> bool:
        """Determina si la fuente requiere atención inmediata."""
        return self.health_score < 50.0 or len(self.issues) > 2


class SourceHealthService(ISourceHealthService):
    """
    Domain Service para evaluación de salud del aggregate `Source`.

    Responsabilidades:
    - Evaluar salud del Source y generar un reporte con score
    - Detectar degradación/recuperación de salud entre dos estados
    - Proveer payloads para emitir eventos (por el aggregate) sin emitirlos aquí
    """

    # Thresholds de salud (configurables)
    CRITICAL_SUCCESS_RATE_THRESHOLD = 30.0
    WARNING_SUCCESS_RATE_THRESHOLD = 70.0
    MAX_DOWNTIME_HOURS = 24.0
    MINIMUM_FETCH_COUNT = 5
    RECOVERY_MIN_SUCCESS_RATE = 80.0  # Para considerar recuperación sostenida

    def __init__(self, time_provider: ITimeProvider):
        self._time_provider = time_provider

    def evaluate_health(self, source: Source) -> SourceHealthReport:
        """Evalúa la salud completa del Source actual."""
        now = self._time_provider.utc_now()
        metrics: SourceMetrics = source.metrics
        issues: List[str] = []
        recommendations: List[str] = []

        # Score base
        health_score = 100.0

        # 1) Tasa de éxito
        if metrics.total_fetches >= self.MINIMUM_FETCH_COUNT:
            if metrics.success_rate < self.CRITICAL_SUCCESS_RATE_THRESHOLD:
                health_score -= 50.0
                issues.append(f"Tasa de éxito crítica: {metrics.success_rate:.1f}%")
                recommendations.append(
                    "Verificar conectividad y configuración de la fuente"
                )
            elif metrics.success_rate < self.WARNING_SUCCESS_RATE_THRESHOLD:
                health_score -= 20.0
                issues.append(f"Tasa de éxito baja: {metrics.success_rate:.1f}%")
                recommendations.append(
                    "Monitorear la fuente por problemas intermitentes"
                )

        # 2) Downtime prolongado sin scraping exitoso
        if metrics.last_successful_fetch_at:
            downtime = now - metrics.last_successful_fetch_at
            downtime_hours = downtime.total_seconds() / 3600
            if downtime_hours > self.MAX_DOWNTIME_HOURS:
                health_score -= 30.0
                issues.append(f"Sin éxito por {downtime_hours:.1f} horas")
                recommendations.append(
                    "Investigar problemas de conectividad o cambios en la fuente"
                )

        # 3) Fallos consecutivos
        if metrics.consecutive_failures > 5:
            health_score -= 20.0
            issues.append(f"Fallos consecutivos: {metrics.consecutive_failures}")
            recommendations.append("Revisar configuración y headers de la fuente")

        # 4) Estado activo
        if not source.status.is_active():
            health_score = 0.0
            issues.append("Fuente desactivada")
            recommendations.append("Activar fuente si debe estar operativa")

        # Normalizar
        health_score = max(0.0, min(100.0, health_score))

        return SourceHealthReport(
            source_id=str(source.id),
            source_name=str(source.name),
            is_healthy=(health_score >= 70.0 and len(issues) == 0),
            health_score=health_score,
            issues=issues,
            recommendations=recommendations,
            last_check=now,
        )

    def is_healthy_quick_check(self, source: Source) -> bool:
        """Chequeo rápido de salud sin construir reporte completo."""
        if not source.status.is_active():
            return False
        metrics = source.metrics
        if metrics.total_fetches == 0:
            return True
        if (
            metrics.total_fetches >= self.MINIMUM_FETCH_COUNT
            and metrics.success_rate < self.CRITICAL_SUCCESS_RATE_THRESHOLD
        ):
            return False
        if metrics.last_successful_fetch_at:
            now = self._time_provider.utc_now()
            downtime = now - metrics.last_successful_fetch_at
            if downtime.total_seconds() > (self.MAX_DOWNTIME_HOURS * 3600):
                return False
        return True

    def detect_degradation(
        self,
        current: Source,
        previous_metrics: Optional[SourceMetrics],
    ) -> bool:
        """Detecta si hay degradación relevante de salud comparado con métricas previas."""
        if previous_metrics is None:
            return False
        current_metrics = current.metrics
        # Heurística simple: caída de tasa de éxito por >= 20 puntos o aumento de fallos
        return (
            (previous_metrics.success_rate - current_metrics.success_rate) >= 20.0
            or current_metrics.consecutive_failures
            > previous_metrics.consecutive_failures + 3
        )

    def detect_recovery(
        self,
        current: Source,
        previous_metrics: Optional[SourceMetrics],
    ) -> bool:
        """Detecta si hay recuperación de salud comparado con métricas previas."""
        if previous_metrics is None:
            return False
        current_metrics = current.metrics
        # Heurística: tasa de éxito >= 80% y fallos consecutivos reseteados
        return (
            current_metrics.success_rate >= self.RECOVERY_MIN_SUCCESS_RATE
            and current_metrics.consecutive_failures == 0
            and (previous_metrics.success_rate < self.RECOVERY_MIN_SUCCESS_RATE)
        )

    def get_health_change(
        self,
        current: Source,
        previous_metrics: Optional[SourceMetrics],
    ) -> Tuple[HealthChangeType, Dict[str, Any]]:
        """
        Determina si hay cambio de salud y retorna un payload para evento.
        No emite eventos; el caller debe usar esta info para invocar al aggregate.
        """
        report = self.evaluate_health(current)
        current_metrics = current.metrics

        if previous_metrics is None:
            return "none", {}

        # Degradación
        if self.detect_degradation(current, previous_metrics):
            payload = {
                "source_id": current.id,
                "source_name": str(current.name),
                "source_url": str(current.url),
                "previous_health_score": previous_metrics.success_rate,
                "current_health_score": current_metrics.success_rate,
                "degradation_threshold": 80.0,
                "degraded_at": self._time_provider.utc_now(),
                "failure_count": current_metrics.failed_fetches,
                "last_successful_fetch": current_metrics.last_successful_fetch_at,
                "degradation_reason": "Success rate dropped significantly",
            }
            return "degraded", payload

        # Recuperación
        if self.detect_recovery(current, previous_metrics):
            downtime = None
            if (
                previous_metrics.last_error_at
                and current_metrics.last_successful_fetch_at
            ):
                downtime_delta = (
                    current_metrics.last_successful_fetch_at
                    - previous_metrics.last_error_at
                )
                downtime = str(downtime_delta)

            payload = {
                "source_id": current.id,
                "source_name": str(current.name),
                "source_url": str(current.url),
                "recovery_health_score": current_metrics.success_rate,
                "recovered_at": self._time_provider.utc_now(),
                "downtime_duration": downtime,
                "recovery_trigger": "Success rate improved above threshold",
            }
            return "recovered", payload

        return "none", {}

    async def test_source_connection(self, source: Source) -> SourceHealthReport:
        """
        Prueba la conexión de una fuente RSS.

        Este método realiza una evaluación completa de salud que incluye
        verificar el estado actual de la fuente.

        Args:
            source: Source aggregate a probar

        Returns:
            SourceHealthReport con el resultado de la prueba
        """
        # Reutilizar la evaluación de salud existente
        return self.evaluate_health(source)

    def validate_source_for_scraping(self, source: Source) -> bool:
        """
        Valida si Source aggregate está listo para operaciones de scraping.

        Esta es una regla de dominio que verifica el estado de salud
        y configuración del Source antes de permitir scraping.

        Args:
            source: El aggregate Source a validar

        Returns:
            True si el Source puede ser procesado para scraping
        """
        return (
            source.is_active
            and source.url is not None
            and str(source.url).strip() != ""
            and source.is_ready_for_basic_operations()
        )
