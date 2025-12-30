"""Validator para CalculateArticleMetrics command."""

from dataclasses import dataclass
from typing import List

from .command import CalculateArticleMetricsCommand


@dataclass(frozen=True)
class ValidationResult:
    """Resultado de validación."""

    is_valid: bool
    errors: List[str]

    @classmethod
    def success(cls) -> "ValidationResult":
        """Crea resultado exitoso."""
        return cls(is_valid=True, errors=[])

    @classmethod
    def failure(cls, errors: List[str]) -> "ValidationResult":
        """Crea resultado fallido."""
        return cls(is_valid=False, errors=errors)


class CalculateArticleMetricsValidator:
    """
    Validador para CalculateArticleMetrics command.

    Responsabilidad: Validar reglas de negocio del comando.
    """

    def validate(self, command: CalculateArticleMetricsCommand) -> ValidationResult:
        """
        Valida el comando.

        Args:
            command: Comando a validar

        Returns:
            ValidationResult con errores si los hay
        """
        errors = []

        # Validar article_id
        if not command.article_id:
            errors.append("article_id es requerido")
        elif not isinstance(command.article_id, str):
            errors.append("article_id debe ser string")
        elif len(command.article_id) < 10:
            errors.append("article_id debe tener al menos 10 caracteres")

        # Validar flags booleanos
        if not isinstance(command.force_recalculate, bool):
            errors.append("force_recalculate debe ser booleano")

        if not isinstance(command.update_article, bool):
            errors.append("update_article debe ser booleano")

        # Validar correlation_id si existe
        if command.correlation_id is not None:
            if not isinstance(command.correlation_id, str):
                errors.append("correlation_id debe ser string")

        if errors:
            return ValidationResult.failure(errors)

        return ValidationResult.success()
