"""Interface base para Logging en Domain-Driven Design."""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict


class LogLevel(Enum):
    """Niveles de logging soportados."""

    TRACE = "TRACE"
    DEBUG = "DEBUG"
    INFO = "INFO"
    SUCCESS = "SUCCESS"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class ILogger(ABC):
    """
    Interface base para logging en el dominio.

    Proporciona capacidades de logging estructurado con contexto
    y metadatos específicos del dominio.
    """

    @abstractmethod
    def trace(self, _message: str, **_kwargs) -> None:
        """Log a nivel TRACE para debugging muy detallado."""
        pass

    @abstractmethod
    def debug(self, _message: str, **_kwargs) -> None:
        """Log a nivel DEBUG para información de desarrollo."""
        pass

    @abstractmethod
    def info(self, _message: str, **_kwargs) -> None:
        """Log a nivel INFO para información general."""
        pass

    @abstractmethod
    def warning(self, _message: str, **_kwargs) -> None:
        """Log a nivel WARNING para situaciones que requieren atención."""
        pass

    @abstractmethod
    def error(self, _message: str, **_kwargs) -> None:
        """Log a nivel ERROR para errores que no detienen la ejecución."""
        pass

    @abstractmethod
    def critical(self, _message: str, **_kwargs) -> None:
        """Log a nivel CRITICAL para errores que pueden detener la aplicación."""
        pass

    @abstractmethod
    def success(self, _message: str, **_kwargs) -> None:
        """Log a nivel SUCCESS para operaciones exitosas."""
        pass

    @abstractmethod
    def exception(self, _message: str, **_kwargs) -> None:
        """Log an exception with traceback."""
        pass

    @abstractmethod
    def log(self, _level: LogLevel, _message: str, **_kwargs) -> None:
        """Log con nivel específico."""
        pass

    @abstractmethod
    def bind(self, **_kwargs) -> "ILogger":
        """
        Crea un nuevo logger con contexto adicional.
        Útil para añadir información de trazabilidad.
        """
        pass

    @abstractmethod
    def patch(self, _patcher_func) -> "ILogger":
        """Create a new logger with a custom patcher."""
        pass

    @abstractmethod
    def contextualize(self, **_kwargs) -> "ILogger":
        """Create a contextual logger for specific operations."""
        pass

    @abstractmethod
    def with_context(self, _context: Dict[str, Any]) -> "ILogger":
        """Crea un logger con contexto específico."""
        pass
