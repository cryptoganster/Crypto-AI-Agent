"""Validator para RemoveSource command."""

from typing import List, Optional

from .command import RemoveSourceCommand


class ValidationResult:
    """Resultado de validación."""

    def __init__(self, is_valid: bool, errors: Optional[List[str]] = None):
        self.is_valid = is_valid
        self.errors = errors or []

    @classmethod
    def success(cls) -> "ValidationResult":
        return cls(is_valid=True)

    @classmethod
    def failure(cls, errors: List[str]) -> "ValidationResult":
        return cls(is_valid=False, errors=errors)


class RemoveRssFeedValidator:
    """Validator para RemoveSourceCommand."""

    def validate(self, command: RemoveSourceCommand) -> ValidationResult:
        """
        Valida comando de eliminación de fuente RSS.

        Args:
            command: Comando a validar

        Returns:
            ValidationResult: Resultado de validación
        """
        errors = []

        # Validar source_id
        if not command.source_id:
            errors.append("source_id es requerido")
        elif not command.source_id.strip():
            errors.append("source_id no puede estar vacío")

        # Validar removed_by si se proporciona
        if command.removed_by is not None and not command.removed_by.strip():
            errors.append("removed_by no puede estar vacío si se proporciona")

        # Validar removal_reason si se proporciona
        if command.removal_reason is not None and not command.removal_reason.strip():
            errors.append("removal_reason no puede estar vacío si se proporciona")

        # Validar consistencia de parámetros
        if command.archive_before_removal and not command.cleanup_articles:
            # Recomendación, no error crítico
            pass

        if errors:
            return ValidationResult.failure(errors)

        return ValidationResult.success()
