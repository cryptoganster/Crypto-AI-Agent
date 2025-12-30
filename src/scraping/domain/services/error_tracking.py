"""Domain Service para tracking y coordinación de errores en operaciones de scraping.

PROPÓSITO: Centralizar lógica de contadores de errores y análisis de patrones
durante operaciones de scraping RSS.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from src.rss.article.domain.aggregates import RssArticle
from src.rss.feed.domain.aggregates import Source
from src.scraping.domain.aggregates import Scraping
from src.scraping.domain.entities import ScrapingManager, ScrapingRecord
from src.scraping.domain.interfaces.services.error_tracking import (
    ErrorCategory,
    ErrorEvent,
    ErrorMetrics,
    ErrorSeverity,
    IErrorTrackingService,
)


class ErrorTrackingService(IErrorTrackingService):
    """
    Domain Service para tracking y análisis de errores en operaciones de scraping.

    RESPONSABILIDADES:
    - Coordinar contadores de errores entre entities
    - Analizar patrones de errores
    - Determinar severidad y categorización
    - Calcular métricas de salud basadas en errores
    - Generar recomendaciones de recuperación
    """

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
        message_lower = error_message.lower()
        exception_lower = (exception_type or "").lower()

        # Patrones de timeout específicos
        if any(
            pattern in message_lower
            for pattern in [
                "timeout",
                "timed out",
                "connection timeout",
            ]
        ):
            return ErrorCategory.TIMEOUT

        # Patrones de red y conexión
        if any(
            pattern in message_lower
            for pattern in [
                "connection",
                "network",
                "unreachable",
                "refused",
                "reset",
            ]
        ):
            return ErrorCategory.NETWORK

        # Errores de timeout
        if any(
            keyword in message_lower
            for keyword in [
                "timeout",
                "timed out",
                "time limit",
                "deadline",
            ]
        ):
            return ErrorCategory.TIMEOUT

        # Patrones de parsing
        if any(
            pattern in message_lower
            for pattern in [
                "parse",
                "xml",
                "malformed",
                "invalid",
                "format",
                "encoding",
            ]
        ):
            return ErrorCategory.PARSING

        # Patrones de rate limiting
        if any(
            pattern in message_lower
            for pattern in [
                "rate limit",
                "too many requests",
                "429",
                "throttle",
            ]
        ):
            return ErrorCategory.RATE_LIMIT

        # Patrones de autenticación
        if any(
            pattern in message_lower
            for pattern in [
                "unauthorized",
                "forbidden",
                "401",
                "403",
                "authentication",
                "permission",
            ]
        ):
            return ErrorCategory.AUTHENTICATION

        # Errores de validación - mapear a PARSING ya que ErrorCategory.VALIDATION no existe en shared
        if any(
            keyword in message_lower
            for keyword in [
                "validation",
                "invalid",
                "required",
                "missing",
                "format",
            ]
        ):
            return ErrorCategory.PARSING

        # Errores de autenticación
        if any(
            keyword in message_lower
            for keyword in [
                "auth",
                "unauthorized",
                "forbidden",
                "401",
                "403",
                "credentials",
            ]
        ):
            return ErrorCategory.AUTHENTICATION

        # Errores de rate limiting
        if any(
            keyword in message_lower
            for keyword in [
                "rate limit",
                "too many requests",
                "429",
                "quota",
                "throttle",
            ]
        ):
            return ErrorCategory.RATE_LIMIT

        # Errores del servidor
        if any(
            keyword in message_lower
            for keyword in [
                "500",
                "502",
                "503",
                "504",
                "server error",
                "internal error",
            ]
        ):
            return ErrorCategory.SERVER_ERROR

        return ErrorCategory.UNKNOWN

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
        # Errores críticos por categoría
        if category in [
            ErrorCategory.AUTHENTICATION,
            ErrorCategory.SERVER_ERROR,
        ]:
            return ErrorSeverity.CRITICAL

        # Severidad por número de errores consecutivos
        if consecutive_count >= 10:
            return ErrorSeverity.CRITICAL
        elif consecutive_count >= 5:
            return ErrorSeverity.HIGH
        elif consecutive_count >= 3:
            return ErrorSeverity.MEDIUM

        # Errores recurrentes son más severos
        if is_recurring:
            if category == ErrorCategory.NETWORK:
                return ErrorSeverity.HIGH
            elif category in [
                ErrorCategory.TIMEOUT,
                ErrorCategory.RATE_LIMIT,
            ]:
                return ErrorSeverity.MEDIUM

        # Severidad base por categoría
        severity_map = {
            ErrorCategory.NETWORK: ErrorSeverity.MEDIUM,
            ErrorCategory.TIMEOUT: ErrorSeverity.MEDIUM,
            ErrorCategory.PARSING: ErrorSeverity.LOW,
            ErrorCategory.RATE_LIMIT: ErrorSeverity.MEDIUM,
            ErrorCategory.UNKNOWN: ErrorSeverity.LOW,
        }

        return severity_map.get(category, ErrorSeverity.LOW)

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
        if not error_events:
            return ErrorMetrics(
                total_errors=0,
                consecutive_errors=0,
                error_rate=0.0,
                last_error_time=None,
                errors_by_category={},
                errors_by_severity={},
            )

        # Filtrar por ventana de tiempo si se especifica
        if time_window:
            cutoff_time = datetime.now() - time_window
            error_events = [e for e in error_events if e.timestamp >= cutoff_time]

        # Ordenar por timestamp
        sorted_events = sorted(error_events, key=lambda e: e.timestamp)

        # Calcular errores consecutivos (desde el final)
        consecutive_errors = 0
        for event in reversed(sorted_events):
            consecutive_errors += 1
            # Si hay un gap significativo, romper la secuencia
            if len(sorted_events) > consecutive_errors:
                prev_event = sorted_events[-(consecutive_errors + 1)]
                if (
                    event.timestamp - prev_event.timestamp
                ).total_seconds() > 3600:  # 1 hora
                    break

        # Contar por categoría
        errors_by_category = {}
        for event in error_events:
            errors_by_category[event.category] = (
                errors_by_category.get(event.category, 0) + 1
            )

        # Contar por severidad
        errors_by_severity = {}
        for event in error_events:
            errors_by_severity[event.severity] = (
                errors_by_severity.get(event.severity, 0) + 1
            )

        # Calcular tasa de errores
        error_rate = len(error_events) / max(total_operations, 1)

        return ErrorMetrics(
            total_errors=len(error_events),
            consecutive_errors=consecutive_errors,
            error_rate=min(error_rate, 1.0),
            last_error_time=sorted_events[-1].timestamp if sorted_events else None,
            errors_by_category=errors_by_category,
            errors_by_severity=errors_by_severity,
        )

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
        # Pausar por errores críticos
        if metrics.has_critical_errors():
            return True, "Errores críticos detectados"

        # Pausar por demasiados errores consecutivos
        if metrics.is_error_threshold_exceeded(max_consecutive=5):
            return (
                True,
                f"Demasiados errores consecutivos: {metrics.consecutive_errors}",
            )

        # Pausar por alta tasa de errores
        if metrics.is_high_error_rate(threshold=0.8):
            return (
                True,
                f"Tasa de errores muy alta: {metrics.error_rate:.1%}",
            )

        return False, None

    def get_recovery_recommendations(self, metrics: ErrorMetrics) -> List[str]:
        """
        Genera recomendaciones para recuperación basadas en métricas de error.

        Args:
            metrics: Métricas de errores

        Returns:
            Lista de recomendaciones de recuperación
        """
        recommendations = []

        dominant_category = metrics.get_dominant_error_category()

        if dominant_category == ErrorCategory.NETWORK:
            recommendations.extend(
                [
                    "Verificar conectividad de red",
                    "Revisar configuración de DNS",
                    "Considerar usar proxy o VPN",
                    "Aumentar timeouts de conexión",
                ]
            )

        elif dominant_category == ErrorCategory.TIMEOUT:
            recommendations.extend(
                [
                    "Aumentar timeouts de scraping",
                    "Reducir número de scraping concurrentes",
                    "Implementar reintentos con backoff exponencial",
                    "Verificar rendimiento del servidor RSS",
                ]
            )

        elif dominant_category == ErrorCategory.PARSING:
            recommendations.extend(
                [
                    "Validar formato del feed RSS",
                    "Actualizar parser RSS",
                    "Implementar fallbacks para feeds malformados",
                    "Contactar al proveedor del feed",
                ]
            )

        elif dominant_category == ErrorCategory.RATE_LIMIT:
            recommendations.extend(
                [
                    "Reducir frecuencia de scraping",
                    "Implementar rate limiting inteligente",
                    "Usar múltiples IPs si es posible",
                    "Contactar al proveedor para aumentar límites",
                ]
            )

        elif dominant_category == ErrorCategory.AUTHENTICATION:
            recommendations.extend(
                [
                    "Verificar credenciales de acceso",
                    "Renovar tokens de autenticación",
                    "Revisar permisos de acceso",
                    "Contactar al administrador del feed",
                ]
            )

        # Recomendaciones generales por severidad
        if metrics.has_critical_errors():
            recommendations.insert(0, "CRÍTICO: Pausar operaciones inmediatamente")

        if metrics.is_high_error_rate():
            recommendations.append("Revisar configuración general del sistema")

        if metrics.is_error_threshold_exceeded():
            recommendations.append(
                "Implementar circuit breaker para prevenir cascada de errores"
            )

        return recommendations

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
        category = self.categorize_error(message, exception_type)
        severity = self.determine_severity(category, 1, False)

        return ErrorEvent(
            timestamp=datetime.now(),
            category=category,
            severity=severity,
            message=message,
            source_id=source_id,
            context=context or {},
        )

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
        if len(error_events) < 3:
            return False, None

        recent_events = [
            e for e in error_events if e.timestamp >= datetime.now() - pattern_window
        ]

        if len(recent_events) < 3:
            return False, None

        # Detectar errores repetitivos de la misma categoría
        category_counts = {}
        for event in recent_events:
            category_counts[event.category] = category_counts.get(event.category, 0) + 1

        for category, count in category_counts.items():
            if count >= 3:
                return (
                    True,
                    f"Patrón detectado: {count} errores de tipo {category.value} en {pattern_window}",
                )

        # Detectar escalada de severidad
        severities = [
            e.severity for e in sorted(recent_events, key=lambda x: x.timestamp)
        ]
        if len(severities) >= 3:
            severity_values = {
                ErrorSeverity.LOW: 1,
                ErrorSeverity.MEDIUM: 2,
                ErrorSeverity.HIGH: 3,
                ErrorSeverity.CRITICAL: 4,
            }

            if all(
                severity_values[severities[i]] <= severity_values[severities[i + 1]]
                for i in range(len(severities) - 1)
            ):
                return (
                    True,
                    "Patrón detectado: escalada de severidad de errores",
                )

        return False, None
