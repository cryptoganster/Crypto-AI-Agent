"""Validator para StartScrapingCommand."""

from typing import List

from src.scraping.app.commands.start_scraping.command import StartScrapingCommand
from src.scraping.app.commands.start_scraping.exception import (
    StartScrapingValidationError,
)


class StartScrapingValidator:
    """
    Validator para StartScrapingCommand.

    Valida que los parámetros del comando sean correctos.
    """

    def validate(self, command: StartScrapingCommand) -> None:
        """
        Valida el comando.

        Args:
            command: Comando a validar

        Raises:
            StartScrapingValidationError: Si la validación falla
        """
        errors: List[str] = []

        # Validar source_ids si se especifican
        if command.source_ids:
            if len(command.source_ids) > 100:
                errors.append("source_ids no puede exceder 100 sources")

            for source_id in command.source_ids:
                if not source_id or not isinstance(source_id, str):
                    errors.append("source_ids contiene valores inválidos")
                    break

        # Validar max_concurrent
        if command.max_concurrent <= 0:
            errors.append("max_concurrent debe ser mayor a 0")
        elif command.max_concurrent > 20:
            errors.append("max_concurrent no puede exceder 20")

        # Validar timeout_seconds
        if command.timeout_seconds <= 0:
            errors.append("timeout_seconds debe ser mayor a 0")
        elif command.timeout_seconds > 300:
            errors.append("timeout_seconds no puede exceder 300")

        # Validar triggered_by
        valid_triggers = {"manual", "scheduler", "api"}
        if command.triggered_by not in valid_triggers:
            errors.append(f"triggered_by debe ser uno de: {valid_triggers}")

        if errors:
            raise StartScrapingValidationError("; ".join(errors))
