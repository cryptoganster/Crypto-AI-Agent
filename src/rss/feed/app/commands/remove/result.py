"""Results para RemoveSource command."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass(frozen=True)
class RemoveRssFeedResult:
    """Result del comando RemoveSource."""

    # Campos obligatorios (sin valores por defecto)
    success: bool
    source_id: str

    # Campos opcionales (con valores por defecto)
    source_name: Optional[str] = field(default=None)
    source_url: Optional[str] = field(default=None)
    articles_removed: int = 0
    message: str = ""
    error_code: Optional[str] = field(default=None)
    removed_at: Optional[datetime] = field(default=None)
    was_archived: bool = False

    @classmethod
    def success_result(
        cls,
        source_id: str,
        source_name: Optional[str] = None,
        source_url: Optional[str] = None,
        articles_removed: int = 0,
        was_archived: bool = False,
    ) -> "RemoveSourceResult":
        """Factory method para resultado exitoso."""
        return cls(
            success=True,
            source_id=source_id,
            source_name=source_name,
            source_url=source_url,
            articles_removed=articles_removed,
            message=f"Fuente RSS '{source_name}' eliminada exitosamente. {articles_removed} artículos removidos.",
            removed_at=datetime.now(timezone.utc),
            was_archived=was_archived,
        )

    @classmethod
    def failure_result(
        cls,
        source_id: str,
        message: str,
        error_code: Optional[str] = None,
    ) -> "RemoveSourceResult":
        """Factory method para resultado fallido."""
        return cls(
            success=False,
            source_id=source_id,
            message=message,
            error_code=error_code,
        )

    @classmethod
    def source_not_found_by_id(cls, source_id: str) -> "RemoveSourceResult":
        """Factory method para feed no encontrado."""
        return cls.failure_result(
            source_id="",
            message=f"Fuente RSS con ID {source_id} no encontrada",
            error_code="SOURCE_NOT_FOUND",
        )

    @classmethod
    def source_not_found(cls, source_id: str) -> "RemoveSourceResult":
        """Factory method para fuente no encontrada (alias)."""
        return cls.source_not_found_by_id(source_id)

    @classmethod
    def source_not_found_in_context(
        cls, source_id: str, context_id: str
    ) -> "RemoveSourceResult":
        """Factory method para fuente no encontrada."""
        return cls.failure_result(
            source_id=source_id,
            message=f"Fuente RSS con ID {source_id} no encontrada en contexto {context_id}",
            error_code="SOURCE_NOT_FOUND",
        )

    @classmethod
    def removal_blocked_by_articles(
        cls, source_id: str, articles_count: int
    ) -> "RemoveSourceResult":
        """Factory method para eliminación bloqueada por artículos."""
        return cls.failure_result(
            source_id=source_id,
            message=f"Eliminación bloqueada: fuente {source_id} tiene {articles_count} artículos asociados. "
            f"Use cleanup_articles=True o force_removal=True.",
            error_code="REMOVAL_BLOCKED_BY_ARTICLES",
        )
