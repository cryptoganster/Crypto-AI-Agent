"""Result y DTO para GetPendingArticlesQuery."""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional
from uuid import UUID


@dataclass(frozen=True)
class PendingArticleDTO:
    """
    DTO para artículo pendiente (GetPendingArticlesQuery).

    CQRS Read Side: Solo datos necesarios para procesamiento.
    DTO ligero con campos mínimos.
    """

    # Identificación
    id: UUID
    source_id: UUID

    # Metadata básica
    title: str
    url: str

    # Estado de procesamiento
    has_scraped_content: bool
    has_plaintext_content: bool
    has_markdown_content: bool

    # Timestamps
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class GetPendingArticlesResult:
    """
    Resultado de GetPendingArticlesQuery.

    Patrón Result Object para manejar éxito/fallo.
    """

    success: bool
    articles: List[PendingArticleDTO] = None
    total_count: int = 0
    error_message: Optional[str] = None

    def __post_init__(self):
        """Inicializar lista vacía si es None."""
        if self.articles is None:
            object.__setattr__(self, "articles", [])

    @classmethod
    def success_result(
        cls, articles: List[PendingArticleDTO]
    ) -> "GetPendingArticlesResult":
        """Crea resultado exitoso."""
        return cls(success=True, articles=articles, total_count=len(articles))

    @classmethod
    def empty_result(cls) -> "GetPendingArticlesResult":
        """Crea resultado vacío (sin artículos pendientes)."""
        return cls(success=True, articles=[], total_count=0)

    @classmethod
    def failure(cls, error_message: str) -> "GetPendingArticlesResult":
        """Crea resultado de fallo."""
        return cls(success=False, error_message=error_message)
