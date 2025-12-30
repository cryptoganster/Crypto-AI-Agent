"""Null Logger implementation - No-op logger for when logging is optional."""

from typing import Any, Dict

from src.shared.kernel.logger import ILogger, LogLevel


class NullLogger(ILogger):
    """
    Null Object Pattern implementation for ILogger.

    No hace nada - usado cuando el logging es opcional pero se necesita
    un logger válido para satisfacer type hints.
    """

    def trace(self, _message: str, **_kwargs) -> None:
        """No-op."""
        pass

    def debug(self, _message: str, **_kwargs) -> None:
        """No-op."""
        pass

    def info(self, _message: str, **_kwargs) -> None:
        """No-op."""
        pass

    def warning(self, _message: str, **_kwargs) -> None:
        """No-op."""
        pass

    def error(self, _message: str, **_kwargs) -> None:
        """No-op."""
        pass

    def critical(self, _message: str, **_kwargs) -> None:
        """No-op."""
        pass

    def success(self, _message: str, **_kwargs) -> None:
        """No-op."""
        pass

    def exception(self, _message: str, **_kwargs) -> None:
        """No-op."""
        pass

    def log(self, _level: LogLevel, _message: str, **_kwargs) -> None:
        """No-op."""
        pass

    def bind(self, **_kwargs) -> "NullLogger":
        """Retorna self ya que no hay estado que mantener."""
        return self

    def patch(self, _patcher_func) -> "NullLogger":
        """Retorna self - no-op."""
        return self

    def contextualize(self, **_kwargs) -> "NullLogger":
        """Retorna self - no-op."""
        return self

    def with_context(self, _context: Dict[str, Any]) -> "NullLogger":
        """Retorna self - no-op."""
        return self
