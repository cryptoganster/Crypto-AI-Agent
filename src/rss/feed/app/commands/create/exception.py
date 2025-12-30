"""Excepciones para el comando CreateSource refactorizado para usar Source aggregate."""

from typing import Optional
from uuid import UUID


class CreateSourceException(Exception):
    """
    Excepción principal para errores en el comando CreateSource.

    Encapsula todos los tipos de errores que pueden ocurrir al crear un Source.
    """

    def __init__(self, message: str, error_code: str = "CREATE_SOURCE_ERROR") -> None:
        self.error_code = error_code
        super().__init__(message)


class DuplicateSourceException(CreateSourceException):
    """Excepción lanzada cuando se intenta crear una fuente duplicada."""

    def __init__(self, source_url: str, existing_id: str) -> None:
        self.source_url = source_url
        self.existing_id = existing_id
        super().__init__(
            f"Ya existe una fuente con la URL {source_url} (ID: {existing_id})",
            "DUPLICATE_SOURCE_URL",
        )


class CreateSourceValidationException(CreateSourceException):
    """Excepción lanzada cuando fallan las validaciones del comando."""

    def __init__(self, message: str, field: Optional[str] = None):
        self.field = field
        super().__init__(message, "VALIDATION_ERROR")


class SourceRepositoryException(CreateSourceException):
    """Excepción lanzada cuando hay errores en el repositorio Source."""

    def __init__(self, message: str, operation: str = "unknown"):
        self.operation = operation
        super().__init__(
            f"Error en repositorio Source durante '{operation}': {message}",
            "SOURCE_REPOSITORY_ERROR",
        )


# Legacy exception for backward compatibility
class DuplicateContentSourceException(Exception):
    """Excepción legacy para compatibilidad hacia atrás."""

    def __init__(self, message: str, existing_source_id: Optional[UUID] = None):
        super().__init__(message)
        self.existing_source_id = existing_source_id
