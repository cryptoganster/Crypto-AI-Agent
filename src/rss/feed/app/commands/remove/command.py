"""Command para remover fuente RSS."""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class RemoveRssFeedCommand:
    """Command para remover fuente RSS usando Source aggregate."""

    # Primitivos (CQRS estricto)
    source_id: str  # SourceId como string
    removed_by: Optional[str] = None
    correlation_id: Optional[str] = None

    # Configuración de eliminación
    force_removal: bool = False  # Forzar eliminación aunque tenga artículos asociados
    cleanup_articles: bool = True  # Limpiar artículos asociados
    archive_before_removal: bool = True  # Archivar antes de eliminar
    removal_reason: Optional[str] = None  # Razón de la eliminación
