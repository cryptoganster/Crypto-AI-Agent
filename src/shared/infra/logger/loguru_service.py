"""Implementación de logging con Loguru para Clean Architecture."""

import sys

# import os  # Unused import commented out
from pathlib import Path
from typing import Any, Dict, Optional

from loguru import logger

from src.shared.config.logging_config import LoggingConfig
from src.shared.kernel.logger import ILogger, LogLevel


class LoguruService(ILogger):
    """
    Servicio de logging basado en Loguru.

    Implementa ILogger proporcionando una abstracción limpia
    sobre Loguru para el resto del sistema.
    """

    def __init__(self, config: LoggingConfig):
        self._config = config
        self._logger = logger
        self._setup_logger()

    def _setup_logger(self) -> None:
        """Configura Loguru según la configuración proporcionada."""

        # Limpiar handlers existentes
        self._logger.remove()

        # Configurar logging de consola
        if self._config.enable_console_logging:
            console_format = self._config.format
            if self._config.enable_json_logging:
                console_format = self._get_json_format()

            self._logger.add(
                sys.stderr,
                format=console_format,
                level=self._config.level,
                serialize=self._config.serialize,
                backtrace=self._config.backtrace,
                diagnose=self._config.diagnose,
                colorize=not self._config.serialize,
                enqueue=False,  # Evitar multiprocessing semaphores (async-safe en FastAPI)
                filter=self._filter_streamlit_warnings,  # Filtrar warnings esperados de Streamlit
            )

        # Configurar logging a archivo
        if self._config.enable_file_logging:
            self._setup_file_logging()

        # Configurar logging de errores separado
        self._setup_error_logging()

        # Configurar logging de warnings separado
        self._setup_warning_logging()

    def _setup_file_logging(self) -> None:
        """Configura logging a archivo principal."""

        # Crear directorio si no existe
        log_path = Path(self._config.file_path)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_format = self._config.format
        if self._config.enable_json_logging:
            file_format = self._get_json_format()

        self._logger.add(
            self._config.file_path,
            format=file_format,
            level=self._config.level,
            rotation=self._config.rotation,
            retention=self._config.retention,
            compression=self._config.compression,
            serialize=self._config.serialize,
            backtrace=self._config.backtrace,
            diagnose=self._config.diagnose,
            enqueue=False,  # Evitar multiprocessing semaphores
        )

    def _setup_error_logging(self) -> None:
        """Configura logging específico para errores."""

        # Crear directorio si no existe
        error_log_path = Path(self._config.error_file_path)
        error_log_path.parent.mkdir(parents=True, exist_ok=True)

        error_format = self._config.format
        if self._config.enable_json_logging:
            error_format = self._get_json_format()

        self._logger.add(
            self._config.error_file_path,
            format=error_format,
            level="ERROR",
            rotation=self._config.rotation,
            retention=self._config.retention,
            compression=self._config.compression,
            serialize=self._config.serialize,
            backtrace=True,
            diagnose=True,
            enqueue=False,  # Evitar multiprocessing semaphores
            filter=lambda record: record["level"].name in ["ERROR", "CRITICAL"],
        )

    def _setup_warning_logging(self) -> None:
        """Configura logging específico para warnings."""
        if not self._config.enable_warning_logging:
            return

        # Crear directorio si no existe
        warning_log_path = Path(self._config.warning_file_path)
        warning_log_path.parent.mkdir(parents=True, exist_ok=True)

        warning_format = self._config.format
        if self._config.enable_json_logging:
            warning_format = self._get_json_format()

        self._logger.add(
            self._config.warning_file_path,
            format=warning_format,
            level="WARNING",
            rotation=self._config.rotation,
            retention=self._config.retention,
            compression=self._config.compression,
            serialize=self._config.serialize,
            backtrace=False,
            diagnose=False,
            enqueue=False,  # Evitar multiprocessing semaphores
            filter=lambda record: record["level"].name == "WARNING",
        )

    def _filter_streamlit_warnings(self, record: Dict[str, Any]) -> bool:
        """Filtrar warnings esperados de Streamlit en background threads."""
        # Suprimir warnings de ScriptRunContext que son normales en threads
        if "ScriptRunContext" in str(record.get("message", "")):
            return False
        return True

    def _get_json_format(self) -> str:
        """Retorna formato JSON para structured logging."""
        return "{time} {level} {name} {function} {line} {message}"

    # Implementación de ILogger

    def trace(self, message: str, **kwargs) -> None:
        """Log a trace message."""
        self._logger.opt(depth=1).trace(message, **kwargs)

    def debug(self, message: str, **kwargs) -> None:
        """Log a debug message."""
        self._logger.opt(depth=1).debug(message, **kwargs)

    def info(self, message: str, **kwargs) -> None:
        """Log an info message."""
        self._logger.opt(depth=1).info(message, **kwargs)

    def success(self, message: str, **kwargs) -> None:
        """Log a success message."""
        self._logger.opt(depth=1).success(message, **kwargs)

    def warning(self, message: str, **kwargs) -> None:
        """Log a warning message."""
        # Si exc_info=True está presente, capturar traceback
        exc_info = kwargs.pop("exc_info", False)
        if exc_info:
            self._logger.opt(depth=1, exception=True).warning(message, **kwargs)
        else:
            self._logger.opt(depth=1).warning(message, **kwargs)

    def error(self, message: str, **kwargs) -> None:
        """Log an error message."""
        # Si exc_info=True está presente, capturar traceback
        exc_info = kwargs.pop("exc_info", False)
        if exc_info:
            self._logger.opt(depth=1, exception=True).error(message, **kwargs)
        else:
            self._logger.opt(depth=1).error(message, **kwargs)

    def critical(self, message: str, **kwargs) -> None:
        """Log a critical message."""
        self._logger.opt(depth=1).critical(message, **kwargs)

    def exception(self, message: str, **kwargs) -> None:
        """Log an exception with traceback."""
        self._logger.opt(depth=1, exception=True).error(message, **kwargs)

    def log(self, level: LogLevel, message: str, **kwargs) -> None:
        """Log a message at the specified level."""
        self._logger.opt(depth=1).log(level.value, message, **kwargs)

    def bind(self, **kwargs) -> "LoguruService":
        """Create a new logger with bound context data."""
        new_logger = self._logger.bind(**kwargs)

        # Crear nueva instancia con el logger bound
        bound_service = LoguruService.__new__(LoguruService)
        bound_service._config = self._config
        bound_service._logger = new_logger
        return bound_service

    def patch(self, patcher_func) -> "LoguruService":
        """Create a new logger with a custom patcher."""
        patched_logger = self._logger.patch(patcher_func)

        # Crear nueva instancia con el logger patched
        patched_service = LoguruService.__new__(LoguruService)
        patched_service._config = self._config
        patched_service._logger = patched_logger
        return patched_service

    def contextualize(self, **kwargs) -> "LoguruService":
        """Create a contextual logger for specific operations."""
        return self.bind(**kwargs)

    def with_context(self, context: Dict[str, Any]) -> "LoguruService":
        """Crea un logger con contexto específico."""
        return self.bind(**context)

    # Métodos específicos de Loguru

    def configure_handler(self, handler_config: Dict[str, Any]) -> None:
        """Configura un handler personalizado."""
        self._logger.add(**handler_config)

    def remove_handler(self, handler_id: int) -> None:
        """Remueve un handler específico."""
        self._logger.remove(handler_id)

    def start_intercept(self, level: str = "DEBUG") -> None:
        """Intercepta logs de stdlib logging."""
        import logging

        class InterceptHandler(logging.Handler):
            def emit(self, record):
                # Obtener el nivel correspondiente
                try:
                    level = self._logger.level(record.levelname).name
                except ValueError:
                    level = record.levelno

                # Encontrar caller desde donde se originó el log
                frame, depth = sys._getframe(6), 6
                while frame and frame.f_code.co_filename == logging.__file__:
                    frame = frame.f_back
                    depth += 1

                self._logger.opt(depth=depth, exception=record.exc_info).log(
                    level, record.getMessage()
                )

        # Interceptar logging estándar
        logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)

    def add_correlation_id(self, correlation_id: str) -> "LoguruService":
        """Añade correlation ID para tracking distribuido."""
        return self.bind(correlation_id=correlation_id)

    def add_request_context(
        self, request_id: str, user_id: Optional[str] = None
    ) -> "LoguruService":
        """Añade contexto de request para APIs."""
        context = {"request_id": request_id}
        if user_id:
            context["user_id"] = user_id
        return self.bind(**context)

    def add_operation_context(self, operation: str, component: str) -> "LoguruService":
        """Añade contexto de operación para Clean Architecture."""
        return self.bind(operation=operation, component=component)

    def get_raw_logger(self):
        """Retorna el logger de Loguru para casos especiales."""
        return self._logger
