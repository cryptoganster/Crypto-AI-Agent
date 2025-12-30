"""Validator para UpdateScrapingConfigCommand."""

from typing import List

from .command import UpdateScrapingConfigCommand
from .exception import UpdateScrapingConfigValidationException


class UpdateScrapingConfigValidator:
    """
    Validator para UpdateScrapingConfigCommand.

    Responsabilidad única: Validar comandos UpdateScrapingConfig antes de ejecución.
    """

    def validate(self, command: UpdateScrapingConfigCommand) -> None:
        """
        Valida el comando.

        Args:
            command: Comando a validar

        Raises:
            UpdateScrapingConfigValidationException: Si la validación falla
        """
        errors: List[str] = []

        # Validar source_id
        if not command.source_id:
            errors.append("source_id es requerido")
        elif not isinstance(command.source_id, str):
            errors.append("source_id debe ser string")

        # Validar scraping_config
        if not command.scraping_config:
            errors.append("scraping_config es requerido")
        elif not isinstance(command.scraping_config, dict):
            errors.append("scraping_config debe ser un diccionario")
        else:
            # Validar campos de configuración
            config_errors = self._validate_config_fields(command.scraping_config)
            errors.extend(config_errors)

        # Lanzar excepción si hay errores
        if errors:
            raise UpdateScrapingConfigValidationException("; ".join(errors))

    def _validate_config_fields(self, config: dict) -> List[str]:
        """
        Valida los campos de configuración de scraping.

        Args:
            config: Diccionario de configuración

        Returns:
            Lista de errores de validación
        """
        errors = []

        # Campos válidos conocidos
        valid_fields = {
            "interval_seconds",
            "max_concurrency",
            "request_timeout",
            "max_articles_per_fetch",
            "retry_attempts",
            "quality_threshold",
            "user_agent",
        }

        # Verificar campos desconocidos
        unknown_fields = set(config.keys()) - valid_fields
        if unknown_fields:
            errors.append(
                f"Campos de configuración desconocidos: {', '.join(unknown_fields)}"
            )

        # Validar interval_seconds
        if "interval_seconds" in config:
            interval = config["interval_seconds"]
            if not isinstance(interval, int):
                errors.append("interval_seconds debe ser entero")
            elif interval <= 0:
                errors.append("interval_seconds debe ser mayor a 0")
            elif interval > 86400:  # 24 horas
                errors.append("interval_seconds no puede exceder 86400 (24 horas)")

        # Validar max_concurrency
        if "max_concurrency" in config:
            concurrency = config["max_concurrency"]
            if not isinstance(concurrency, int):
                errors.append("max_concurrency debe ser entero")
            elif concurrency <= 0:
                errors.append("max_concurrency debe ser mayor a 0")
            elif concurrency > 20:
                errors.append("max_concurrency no puede exceder 20")

        # Validar request_timeout
        if "request_timeout" in config:
            timeout = config["request_timeout"]
            if not isinstance(timeout, int):
                errors.append("request_timeout debe ser entero")
            elif timeout <= 0:
                errors.append("request_timeout debe ser mayor a 0")
            elif timeout > 300:
                errors.append("request_timeout no puede exceder 300 segundos")

        # Validar max_articles_per_fetch
        if "max_articles_per_fetch" in config:
            max_articles = config["max_articles_per_fetch"]
            if not isinstance(max_articles, int):
                errors.append("max_articles_per_fetch debe ser entero")
            elif max_articles <= 0:
                errors.append("max_articles_per_fetch debe ser mayor a 0")
            elif max_articles > 1000:
                errors.append("max_articles_per_fetch no puede exceder 1000")

        # Validar retry_attempts
        if "retry_attempts" in config:
            retries = config["retry_attempts"]
            if not isinstance(retries, int):
                errors.append("retry_attempts debe ser entero")
            elif retries < 0:
                errors.append("retry_attempts no puede ser negativo")
            elif retries > 10:
                errors.append("retry_attempts no puede exceder 10")

        # Validar quality_threshold
        if "quality_threshold" in config:
            threshold = config["quality_threshold"]
            if not isinstance(threshold, (int, float)):
                errors.append("quality_threshold debe ser numérico")
            elif not (0.0 <= threshold <= 1.0):
                errors.append("quality_threshold debe estar entre 0.0 y 1.0")

        # Validar user_agent
        if "user_agent" in config:
            user_agent = config["user_agent"]
            if not isinstance(user_agent, str):
                errors.append("user_agent debe ser string")
            elif len(user_agent) > 500:
                errors.append("user_agent no puede exceder 500 caracteres")

        return errors
