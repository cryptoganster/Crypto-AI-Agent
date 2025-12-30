"""Interface para Error Tracking Service."""

from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


class ErrorCategory(Enum):
    """Categorías de errores en operaciones de scraping."""

    NETWORK = "network"
    TIMEOUT = "timeout"
    PARSING = "parsing"
    RATE_LIMIT = "rate_limit"
    AUTHENTICATION = "authentication"
    SERVER_ERROR = "server_error"
    UNKNOWN = "unknown"


class ErrorSeverity(Enum):
    """Severidad de errores."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorEvent:
    """Evento de error con contexto completo."""

    timestamp: datetime
    category: ErrorCategory
    severity: ErrorSeverity
    message: str
    source_id: Optional[str]
    context: Dict[str, Any]


class ErrorMetrics:
    """Métricas consolidadas de errores."""

    total_errors: int
    consecutive_errors: int
    error_rate: float
    last_error_time: Optional[datetime]
    errors_by_category: Dict[ErrorCategory, int]
    errors_by_severity: Dict[ErrorSeverity, int]

    def has_critical_errors(self) -> bool:
        """Verifica si hay errores críticos."""
        ...

    def is_error_threshold_exceeded(self, max_consecutive: int = 5) -> bool:
        """Verifica si se excedió el umbral de errores consecutivos."""
        ...

    def is_high_error_rate(self, threshold: float = 0.5) -> bool:
        """Verifica si la tasa de errores es alta."""
        ...

    def get_dominant_error_category(self) -> Optional[ErrorCategory]:
        """Obtiene la categoría de error dominante."""
        ...


class IErrorTrackingService(ABC):
    """
    Interface para Domain Service de tracking y análisis de errores en scraping.

    RESPONSABILIDADES:
    - Coordinar contadores de errores entre entities
    - Analizar patrones de errores
    - Determinar severidad y categorización
    - Calcular métricas de salud basadas en errores
    - Generar recomendaciones de recuperación
    """

    @abstractmethod
    def categorize_error(
        self, error_message: str, exception_type: Optional[str] = None
    ) -> ErrorCategory:
        """
        Categoriza un error basado en su mensaje y tipo.

        Args:
            error_message: Mensaje del error
            exception_type: Tipo de excepción (opcional)

        Returns:
            Categoría del error
        """
        ...

    @abstractmethod
    def determine_severity(
        self,
        category: ErrorCategory,
        consecutive_count: int,
        is_recurring: bool = False,
    ) -> ErrorSeverity:
        """
        Determina la severidad de un error.

        Args:
            category: Categoría del error
            consecutive_count: Número de errores consecutivos
            is_recurring: Si es un error recurrente

        Returns:
            Severidad del error
        """
        ...

    @abstractmethod
    def calculate_error_metrics(
        self,
        error_events: List[ErrorEvent],
        total_operations: int,
        time_window: Optional[timedelta] = None,
    ) -> ErrorMetrics:
        """
        Calcula métricas consolidadas de errores.

        Args:
            error_events: Lista de eventos de error
            total_operations: Total de operaciones realizadas
            time_window: Ventana de tiempo para análisis (opcional)

        Returns:
            Métricas consolidadas de errores
        """
        ...

    @abstractmethod
    def should_pause_operations(
        self, metrics: ErrorMetrics
    ) -> Tuple[bool, Optional[str]]:
        """
        Determina si se deben pausar las operaciones basado en métricas de error.

        Args:
            metrics: Métricas de errores

        Returns:
            Tuple (should_pause: bool, reason: Optional[str])
        """
        ...

    @abstractmethod
    def get_recovery_recommendations(self, metrics: ErrorMetrics) -> List[str]:
        """
        Genera recomendaciones para recuperación basadas en métricas de error.

        Args:
            metrics: Métricas de errores

        Returns:
            Lista de recomendaciones de recuperación
        """
        ...

    @abstractmethod
    def create_error_event(
        self,
        message: str,
        source_id: Optional[str] = None,
        exception_type: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> ErrorEvent:
        """
        Crea un evento de error con categorización automática.

        Args:
            message: Mensaje del error
            source_id: ID de la source afectada (opcional)
            exception_type: Tipo de excepción (opcional)
            context: Contexto adicional (opcional)

        Returns:
            Evento de error categorizado
        """
        ...

    @abstractmethod
    def is_error_pattern_detected(
        self,
        error_events: List[ErrorEvent],
        pattern_window: timedelta = timedelta(hours=1),
    ) -> Tuple[bool, Optional[str]]:
        """
        Detecta patrones problemáticos en los errores.

        Args:
            error_events: Lista de eventos de error
            pattern_window: Ventana de tiempo para análisis de patrones

        Returns:
            Tuple (pattern_detected: bool, pattern_description: Optional[str])
        """
        ...
