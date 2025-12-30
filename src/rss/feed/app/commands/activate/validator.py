"""Validator para ActivateSource command."""

from typing import List, Optional

from .command import ActivateSourceCommand


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


class ActivateRssFeedValidator:
    """Validator para ActivateSourceCommand."""

    def validate(self, command: ActivateSourceCommand) -> ValidationResult:
        """
        Valida comando de activación de fuente RSS usando Source aggregate.

        Args:
            command: Comando a validar

        Returns:
            ValidationResult: Resultado de validación
        """
        errors = []

        # Validar source_id (puede ser string o Value Object)
        source_id_str = str(command.source_id) if command.source_id else ""
        if not source_id_str:
            errors.append("source_id es requerido")
        elif not source_id_str.strip():
            errors.append("source_id no puede estar vacío")

        # Validar activated_by si se proporciona
        if command.activated_by is not None and not str(command.activated_by).strip():
            errors.append("activated_by no puede estar vacío si se proporciona")

        # Validar correlation_id si se proporciona
        if (
            command.correlation_id is not None
            and not str(command.correlation_id).strip()
        ):
            errors.append("correlation_id no puede estar vacío si se proporciona")

        if errors:
            return ValidationResult.failure(errors)

        return ValidationResult.success()
