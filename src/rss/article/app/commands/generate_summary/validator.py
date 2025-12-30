"""Validator para GenerateArticleSummary command."""

from dataclasses import dataclass
from typing import List

from .command import GenerateArticleSummaryCommand


@dataclass(frozen=True)
class ValidationResult:
    """Resultado de validación."""

    is_valid: bool
    errors: List[str]

    @classmethod
    def success(cls) -> "ValidationResult":
        return cls(is_valid=True, errors=[])

    @classmethod
    def failure(cls, errors: List[str]) -> "ValidationResult":
        return cls(is_valid=False, errors=errors)


class GenerateArticleSummaryValidator:
    """Validador para GenerateArticleSummary command."""

    def validate(self, command: GenerateArticleSummaryCommand) -> ValidationResult:
        """Valida el comando."""
        errors = []

        if not command.article_id:
            errors.append("article_id es requerido")
        elif not isinstance(command.article_id, str):
            errors.append("article_id debe ser string")
        elif len(command.article_id) < 10:
            errors.append("article_id debe tener al menos 10 caracteres")

        if command.summary_length <= 0:
            errors.append("summary_length debe ser positivo")
        elif command.summary_length > 10000:
            errors.append("summary_length no puede exceder 10000 caracteres")

        if not isinstance(command.force_regenerate, bool):
            errors.append("force_regenerate debe ser booleano")

        if not isinstance(command.update_article, bool):
            errors.append("update_article debe ser booleano")

        if command.correlation_id is not None:
            if not isinstance(command.correlation_id, str):
                errors.append("correlation_id debe ser string")

        if errors:
            return ValidationResult.failure(errors)

        return ValidationResult.success()
