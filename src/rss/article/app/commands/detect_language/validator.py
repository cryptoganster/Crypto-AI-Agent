"""Validator para DetectArticleLanguageCommand."""

from dataclasses import dataclass
from typing import List

from .command import DetectArticleLanguageCommand


@dataclass(frozen=True)
class ValidationResult:
    """Resultado de validación."""

    is_valid: bool
    errors: List[str]


class DetectArticleLanguageValidator:
    """
    Validador para DetectArticleLanguageCommand.

    Valida que los parámetros del comando sean correctos.
    """

    def validate(self, command: DetectArticleLanguageCommand) -> ValidationResult:
        """
        Valida el comando.

        Args:
            command: Comando a validar

        Returns:
            ValidationResult con errores si hay
        """
        errors: List[str] = []

        # Validar article_id
        if not command.article_id:
            errors.append("article_id es requerido")

        # Validar correlation_id si se proporciona
        if command.correlation_id and len(command.correlation_id) > 100:
            errors.append("correlation_id demasiado largo (max 100 caracteres)")

        # Validar triggered_by
        if command.triggered_by and len(command.triggered_by) > 50:
            errors.append("triggered_by demasiado largo (max 50 caracteres)")

        return ValidationResult(is_valid=len(errors) == 0, errors=errors)
