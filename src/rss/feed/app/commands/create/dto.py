"""DTOs para el comando CreateSource - Solo DTOs relacionados a creación."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID


@dataclass(frozen=True)
class CreateSourceRequestDto:
    """DTO para solicitudes de creación de content source RSS desde API/UI."""

    # Campos obligatorios (sin valores por defecto)
    name: str
    source_url: str

    # Campos opcionales (con valores por defecto)
    source_type: str = "rss"
    category: Optional[str] = field(default=None)
    description: Optional[str] = field(default=None)
    fetch_interval_hours: int = 6
    max_items_per_fetch: int = 50
    include_full_content: bool = True
    keyword_filters: Optional[List[str]] = field(default=None)
    exclude_keywords: Optional[List[str]] = field(default=None)
    language_filter: Optional[str] = field(default=None)
    custom_user_agent: Optional[str] = field(default=None)
    connection_timeout_seconds: int = 30
    retry_attempts: int = 3
    auto_activate: bool = True
    additional_config: Optional[Dict[str, Any]] = field(default=None)


@dataclass(frozen=True)
class CreateSourceResponseDto:
    """DTO para respuesta de creación de content source RSS."""

    # Campos obligatorios (sin valores por defecto)
    success: bool
    source_id: UUID

    # Campos opcionales (con valores por defecto)
    message: str = ""
    created_at: Optional[datetime] = field(default=None)
    validation_errors: Optional[List[str]] = field(default=None)


@dataclass(frozen=True)
class ContentSourceValidationDto:
    """DTO para validación de content source."""

    # Campos obligatorios (sin valores por defecto)
    is_valid: bool
    source_url: str

    # Campos opcionales (con valores por defecto)
    validation_errors: Optional[List[str]] = field(default=None)
    validation_warnings: Optional[List[str]] = field(default=None)


@dataclass(frozen=True)
class ContentSourceConfigDto:
    """DTO para configuración de content source."""

    # Campos obligatorios (sin valores por defecto)
    fetch_interval_hours: int
    max_items_per_fetch: int

    # Campos opcionales (con valores por defecto)
    include_full_content: bool = True
    connection_timeout_seconds: int = 30
    retry_attempts: int = 3


@dataclass(frozen=True)
class ContentSourcePreviewDto:
    """DTO para preview de content source."""

    # Campos obligatorios (sin valores por defecto)
    feed_title: str
    sample_items_count: int

    # Campos opcionales (con valores por defecto)
    feed_description: Optional[str] = field(default=None)
    sample_items: Optional[List[Dict[str, Any]]] = field(default=None)


@dataclass(frozen=True)
class ContentSourceDuplicateCheckDto:
    """DTO para verificación de duplicados de content source."""

    # Campos obligatorios (sin valores por defecto)
    has_duplicates: bool

    # Campos opcionales (con valores por defecto)
    duplicate_sources: Optional[List[Dict[str, Any]]] = field(default=None)
    similarity_score: float = 0.0
    recommendation: str = "proceed"
