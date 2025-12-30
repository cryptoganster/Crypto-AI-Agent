"""Interface para Source Health Service."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime

# Forward reference para evitar import circular
from typing import TYPE_CHECKING, Any, Dict, List, Literal, Optional, Tuple

from src.rss.feed.domain.value_objects.metrics import SourceMetrics

if TYPE_CHECKING:
    from src.rss.feed.domain.aggregates import Source

HealthChangeType = Literal["degraded", "recovered", "none"]


class SourceHealthReport:
    """Reporte completo de salud de una fuente (aggregate `Source`)."""

    source_id: str
    source_name: str
    is_healthy: bool
    health_score: float
    issues: List[str]
    recommendations: List[str]
    last_check: datetime

    def requires_attention(self) -> bool:
        """Determina si la fuente requiere atención inmediata."""
        ...


class ISourceHealthService(ABC):
    """
    Interface para Domain Service de evaluación de salud del aggregate `Source`.

    Responsabilidades:
    - Evaluar salud del Source y generar un reporte con score
    - Detectar degradación/recuperación de salud entre dos estados
    - Proveer payloads para emitir eventos (por el aggregate) sin emitirlos aquí
    """

    @abstractmethod
    def evaluate_health(self, source: Source) -> SourceHealthReport:
        """
        Evalúa la salud completa del Source actual.

        Args:
            source: Source aggregate a evaluar

        Returns:
            SourceHealthReport con evaluación completa
        """
        ...

    @abstractmethod
    def is_healthy_quick_check(self, source: Source) -> bool:
        """
        Chequeo rápido de salud sin construir reporte completo.

        Args:
            source: Source aggregate a verificar

        Returns:
            True si está saludable, False en caso contrario
        """
        ...

    @abstractmethod
    def detect_degradation(
        self,
        current: Source,
        previous_metrics: Optional[SourceMetrics],
    ) -> bool:
        """
        Detecta si hay degradación relevante de salud comparado con métricas previas.

        Args:
            current: Source actual
            previous_metrics: Métricas previas para comparación

        Returns:
            True si hay degradación detectada
        """
        ...

    @abstractmethod
    def detect_recovery(
        self,
        current: Source,
        previous_metrics: Optional[SourceMetrics],
    ) -> bool:
        """
        Detecta si hay recuperación de salud comparado con métricas previas.

        Args:
            current: Source actual
            previous_metrics: Métricas previas para comparación

        Returns:
            True si hay recuperación detectada
        """
        ...

    @abstractmethod
    def get_health_change(
        self,
        current: Source,
        previous_metrics: Optional[SourceMetrics],
    ) -> Tuple[HealthChangeType, Dict[str, Any]]:
        """
        Determina si hay cambio de salud y retorna un payload para evento.

        No emite eventos; el caller debe usar esta info para invocar al aggregate.

        Args:
            current: Source actual
            previous_metrics: Métricas previas para comparación

        Returns:
            Tuple con tipo de cambio y payload para evento
        """
        ...

    @abstractmethod
    async def test_source_connection(self, source: Source) -> SourceHealthReport:
        """
        Prueba la conexión de una fuente RSS.

        Args:
            source: Source aggregate a probar

        Returns:
            SourceHealthReport con el resultado de la prueba
        """
        ...

    @abstractmethod
    def validate_source_for_scraping(self, source: Source) -> bool:
        """
        Valida si Source aggregate está listo para operaciones de scraping.

        Args:
            source: El aggregate Source a validar

        Returns:
            True si el Source puede ser procesado para scraping
        """
        ...
