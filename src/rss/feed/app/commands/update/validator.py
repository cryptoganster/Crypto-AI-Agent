"""Validador para UpdateSourceCommand."""

from typing import List

from .command import UpdateSourceCommand
from .exception import InvalidSourceUpdateError


class UpdateRssFeedValidator:
    """Validador para UpdateSourceCommand usando Source aggregate."""

    def validate(self, command: UpdateSourceCommand) -> None:
        """
        Valida comando UpdateSource.

        Args:
            command: Comando a validar

        Raises:
            InvalidSourceUpdateError: Si la validación falla
        """
        errors = []

        # Validar primitivos obligatorios
        if not command.source_id or not isinstance(command.source_id, str):
            errors.append("source_id es requerido y debe ser string válido")

        if command.source_id and not command.source_id.strip():
            errors.append("source_id no puede estar vacío")

        # Validar que al menos una actualización está especificada
        has_update = any(
            [
                command.name,
                command.description,
                command.source_config,
            ]
        )

        if not has_update:
            errors.append(
                "Debe especificar al menos un campo para actualizar (name, description, source_config)"
            )

        # Validar name si se proporciona
        if command.name is not None:
            if not isinstance(command.name, str) or not command.name.strip():
                errors.append("name debe ser string no vacío si se especifica")
            elif len(command.name.strip()) > 255:
                errors.append("name no puede exceder 255 caracteres")

        # Validar description si se proporciona
        if command.description is not None:
            if not isinstance(command.description, str):
                errors.append("description debe ser string si se especifica")
            elif len(command.description) > 1000:
                errors.append("description no puede exceder 1000 caracteres")

        # Validar source_config si se proporciona
        if command.source_config is not None:
            config_errors = self._validate_source_config(command.source_config)
            errors.extend(config_errors)

        # Validar correlation_id si se proporciona
        if command.correlation_id is not None:
            if (
                not isinstance(command.correlation_id, str)
                or not command.correlation_id.strip()
            ):
                errors.append(
                    "correlation_id debe ser string no vacío si se especifica"
                )

        # Lanzar excepción si hay errores
        if errors:
            raise InvalidSourceUpdateError("; ".join(errors))

    def _validate_source_config(self, config: dict) -> list[str]:
        """
        Valida configuración específica de source.

        Args:
            config: Diccionario de configuración

        Returns:
            Lista de errores de validación
        """
        errors = []

        if not isinstance(config, dict):
            errors.append("source_config debe ser un diccionario")
            return errors

        # Validar campos conocidos de SourceConfiguration
        valid_fields = {
            "fetch_enabled",
            "priority",
            "quality_threshold",
            "max_fetch_retries",
            "fetch_timeout_seconds",
            "user_agent",
        }

        # Validar que no hay campos desconocidos
        invalid_fields = set(config.keys()) - valid_fields
        if invalid_fields:
            errors.append(
                f"Campos de configuración no válidos: {', '.join(invalid_fields)}"
            )

        # Validar tipos y rangos específicos
        if "fetch_enabled" in config:
            if not isinstance(config["fetch_enabled"], bool):
                errors.append("fetch_enabled debe ser boolean")

        if "priority" in config:
            if not isinstance(config["priority"], int) or not (
                1 <= config["priority"] <= 10
            ):
                errors.append("priority debe ser entero entre 1 y 10")

        if "quality_threshold" in config:
            if not isinstance(config["quality_threshold"], (int, float)) or not (
                0.0 <= config["quality_threshold"] <= 1.0
            ):
                errors.append("quality_threshold debe ser número entre 0.0 y 1.0")

        if "max_fetch_retries" in config:
            if (
                not isinstance(config["max_fetch_retries"], int)
                or config["max_fetch_retries"] < 0
            ):
                errors.append("max_fetch_retries debe ser entero no negativo")

        if "fetch_timeout_seconds" in config:
            if (
                not isinstance(config["fetch_timeout_seconds"], int)
                or config["fetch_timeout_seconds"] <= 0
            ):
                errors.append("fetch_timeout_seconds debe ser entero positivo")

        if "user_agent" in config:
            if (
                not isinstance(config["user_agent"], str)
                or not config["user_agent"].strip()
            ):
                errors.append("user_agent debe ser string no vacío")

        return errors
