"""DTOs para RemoveSource command."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass(frozen=True)
class RemoveSourceRequestDto:
    """DTO de entrada para remover fuente RSS."""

    # Campos obligatorios
    source_id: str  # SourceId como string

    # Campos opcionales
    removed_by: Optional[str] = field(default=None)
    force_removal: bool = False
    cleanup_articles: bool = True
    archive_before_removal: bool = True
    removal_reason: Optional[str] = field(default=None)
    correlation_id: Optional[str] = field(default=None)


@dataclass(frozen=True)
class RemoveSourceResponseDto:
    """DTO de respuesta de eliminación de fuente."""

    success: bool
    source_id: str
    source_name: str
    source_url: str
    articles_associated: int
    articles_removed: int
    was_active_before_removal: bool
    removal_timestamp: datetime
    removed_at: Optional[datetime] = field(default=None)
    message: str = ""
    was_archived: bool = False
    cleanup_performed: bool = False
    cleanup_duration_seconds: Optional[float] = field(default=None)


@dataclass(frozen=True)
class SourceRemovalDetailsDto:
    """DTO para detalles de eliminación de fuente."""

    source_id: str
    source_name: str
    source_url: str
    articles_count: int
    status_before_removal: str
    removal_reason: Optional[str] = field(default=None)
