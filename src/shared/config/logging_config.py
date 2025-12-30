"""Logging configuration."""

import os
from dataclasses import dataclass


@dataclass
class LoggingConfig:
    """Configuración de logging con Loguru."""

    level: str = "INFO"
    format: str = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
        "<level>{message}</level>"
    )
    rotation: str = "1 day"
    retention: str = "2 days"
    compression: None = None
    serialize: bool = False
    backtrace: bool = False
    diagnose: bool = False

    file_path: str = "logs/log_{time:DD_MMM_YYYY}.log"
    error_file_path: str = "logs/log_error_{time:DD_MMM_YYYY}.log"
    warning_file_path: str = "logs/log_warning_{time:DD_MMM_YYYY}.log"

    enable_file_logging: bool = True
    enable_console_logging: bool = True
    enable_json_logging: bool = False
    enable_warning_logging: bool = True

    @classmethod
    def from_env(cls) -> "LoggingConfig":
        """Crea configuración desde variables de entorno."""
        return cls(
            level=os.getenv("LOG_LEVEL", "INFO"),
            rotation=os.getenv("LOG_ROTATION", "1 day"),
            retention=os.getenv("LOG_RETENTION", "2 days"),
            file_path=os.getenv("LOG_FILE_PATH", "logs/log_{time:DD_MMM_YYYY}.log"),
            error_file_path=os.getenv(
                "ERROR_LOG_FILE_PATH", "logs/log_error_{time:DD_MMM_YYYY}.log"
            ),
            warning_file_path=os.getenv(
                "WARNING_LOG_FILE_PATH", "logs/log_warning_{time:DD_MMM_YYYY}.log"
            ),
            enable_file_logging=os.getenv("ENABLE_FILE_LOGGING", "true").lower()
            == "true",
            enable_console_logging=os.getenv("ENABLE_CONSOLE_LOGGING", "true").lower()
            == "true",
            enable_json_logging=os.getenv("ENABLE_JSON_LOGGING", "false").lower()
            == "true",
            enable_warning_logging=os.getenv("ENABLE_WARNING_LOGGING", "true").lower()
            == "true",
            serialize=os.getenv("LOG_SERIALIZE", "false").lower() == "true",
            backtrace=os.getenv("LOG_BACKTRACE", "true").lower() == "true",
            diagnose=os.getenv("LOG_DIAGNOSE", "true").lower() == "true",
        )
