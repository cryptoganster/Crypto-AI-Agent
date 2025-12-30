"""Resultados para el comando CreateSource - Types y Builder consolidados."""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import List, Optional, Union
from uuid import UUID


class CreateRssFeedResultStatus(Enum):
    """Estados posibles para los resultados de operaciones CreateSource."""

    SUCCESS = "success"
    VALIDATION_FAILURE = "validation_failure"
    DUPLICATE_FAILURE = "duplicate_failure"
    NETWORK_FAILURE = "network_failure"
    FAILURE = "failure"


@dataclass(frozen=True)
class CreateSourceSuccess:
    """Resultado exitoso de creación de content source."""

    source_id: UUID
    name: str
    url: str
    created_at: datetime
    status: CreateSourceResultStatus
    is_active: bool = False
    estimated_daily_fetches: int = 4
    priority: str = "medium"
    events_published: int = 0
    warnings: Optional[List[str]] = None

    @property
    def is_success(self) -> bool:
        return True

    @property
    def is_failure(self) -> bool:
        return False


@dataclass(frozen=True)
class CreateSourceFailure:
    """Resultado de fallo general."""

    error_code: str
    error_message: str
    status: CreateSourceResultStatus
    field_errors: Optional[dict[str, str]] = None
    suggested_fixes: Optional[List[str]] = None
    correlation_id: Optional[str] = None

    @property
    def is_success(self) -> bool:
        return False

    @property
    def is_failure(self) -> bool:
        return True


@dataclass(frozen=True)
class CreateSourceValidationFailure:
    """Resultado de fallo por errores de validación."""

    error_code: str
    error_message: str
    status: CreateSourceResultStatus
    validation_errors: List[str]
    field_errors: dict[str, str]
    suggested_fixes: Optional[List[str]] = None
    correlation_id: Optional[str] = None

    @property
    def is_success(self) -> bool:
        return False

    @property
    def is_failure(self) -> bool:
        return True


@dataclass(frozen=True)
class CreateSourceDuplicateFailure:
    """Resultado de fallo por fuente duplicada."""

    error_code: str
    error_message: str
    status: CreateSourceResultStatus
    duplicate_url: str
    existing_source_id: UUID
    existing_source_name: str
    similarity_score: float = 1.0
    field_errors: Optional[dict[str, str]] = None
    suggested_fixes: Optional[List[str]] = None
    correlation_id: Optional[str] = None

    @property
    def is_success(self) -> bool:
        return False

    @property
    def is_failure(self) -> bool:
        return True


@dataclass(frozen=True)
class CreateSourceNetworkFailure:
    """Resultado de fallo por problemas de red."""

    error_code: str
    error_message: str
    status: CreateSourceResultStatus
    url_attempted: str
    response_code: Optional[int] = None
    timeout_seconds: Optional[int] = None
    field_errors: Optional[dict[str, str]] = None
    suggested_fixes: Optional[List[str]] = None
    retry_after_seconds: Optional[int] = None
    correlation_id: Optional[str] = None

    @property
    def is_success(self) -> bool:
        return False

    @property
    def is_failure(self) -> bool:
        return True


# Union type para todos los posibles resultados
CreateSourceResult = Union[
    CreateSourceSuccess,
    CreateSourceValidationFailure,
    CreateSourceDuplicateFailure,
    CreateSourceNetworkFailure,
    CreateSourceFailure,
]


class CreateRssFeedResultBuilder:
    """Builder para construir resultados de CreateSource."""

    @staticmethod
    def success(
        source_id: str,
        name: str,
        url: str,
        is_active: bool = False,
        estimated_daily_fetches: int = 4,
        priority: str = "medium",
        events_published: int = 0,
        warnings: Optional[List[str]] = None,
        created_at: Optional[datetime] = None,
    ) -> CreateSourceSuccess:
        """Construye un resultado exitoso."""
        return CreateSourceSuccess(
            source_id=UUID(source_id) if isinstance(source_id, str) else source_id,
            name=name,
            url=url,
            created_at=created_at or datetime.now(),
            status=CreateSourceResultStatus.SUCCESS,
            is_active=is_active,
            estimated_daily_fetches=estimated_daily_fetches,
            priority=priority,
            events_published=events_published,
            warnings=warnings,
        )

    @staticmethod
    def validation_failure(
        error_code: str,
        error_message: str,
        validation_errors: List[str],
        field_errors: dict[str, str],
        suggested_fixes: Optional[List[str]] = None,
        correlation_id: Optional[str] = None,
    ) -> CreateSourceValidationFailure:
        """Construye un resultado de fallo de validación."""
        return CreateSourceValidationFailure(
            error_code=error_code,
            error_message=error_message,
            status=CreateSourceResultStatus.VALIDATION_FAILURE,
            validation_errors=validation_errors,
            field_errors=field_errors,
            suggested_fixes=suggested_fixes,
            correlation_id=correlation_id,
        )

    @staticmethod
    def duplicate_failure(
        error_code: str,
        error_message: str,
        duplicate_url: str,
        existing_source_id: UUID,
        existing_source_name: str,
        similarity_score: float = 1.0,
        field_errors: Optional[dict[str, str]] = None,
        suggested_fixes: Optional[List[str]] = None,
        correlation_id: Optional[str] = None,
    ) -> CreateSourceDuplicateFailure:
        """Construye un resultado de fallo por duplicado."""
        return CreateSourceDuplicateFailure(
            error_code=error_code,
            error_message=error_message,
            status=CreateSourceResultStatus.DUPLICATE_FAILURE,
            duplicate_url=duplicate_url,
            existing_source_id=existing_source_id,
            existing_source_name=existing_source_name,
            similarity_score=similarity_score,
            field_errors=field_errors,
            suggested_fixes=suggested_fixes,
            correlation_id=correlation_id,
        )

    @staticmethod
    def network_failure(
        error_code: str,
        error_message: str,
        url_attempted: str,
        response_code: Optional[int] = None,
        timeout_seconds: Optional[int] = None,
        field_errors: Optional[dict[str, str]] = None,
        suggested_fixes: Optional[List[str]] = None,
        retry_after_seconds: Optional[int] = None,
        correlation_id: Optional[str] = None,
    ) -> CreateSourceNetworkFailure:
        """Construye un resultado de fallo de red."""
        return CreateSourceNetworkFailure(
            error_code=error_code,
            error_message=error_message,
            status=CreateSourceResultStatus.NETWORK_FAILURE,
            url_attempted=url_attempted,
            response_code=response_code,
            timeout_seconds=timeout_seconds,
            field_errors=field_errors,
            suggested_fixes=suggested_fixes,
            retry_after_seconds=retry_after_seconds,
            correlation_id=correlation_id,
        )

    @staticmethod
    def failure(
        error_code: str,
        error_message: str,
        field_errors: Optional[dict[str, str]] = None,
        suggested_fixes: Optional[List[str]] = None,
        correlation_id: Optional[str] = None,
    ) -> CreateSourceFailure:
        """Construye un resultado de fallo general."""
        return CreateSourceFailure(
            error_code=error_code,
            error_message=error_message,
            status=CreateSourceResultStatus.FAILURE,
            field_errors=field_errors,
            suggested_fixes=suggested_fixes,
            correlation_id=correlation_id,
        )
