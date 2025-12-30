"""ArticleReadModel - Read Model para Read Side.

CQRS ESTRICTO: Este Read Model es para queries de lectura únicamente.
NO tiene comportamiento, solo datos.

Para modificar artículos, usar Article Aggregate (write side).
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional
from uuid import UUID


@dataclass(frozen=True)
class ArticleReadModel:
    """
    Read Model para lectura de artículos (CQRS Read Side).

    Características:
    - Inmutable (frozen=True)
    - Solo datos primitivos
    - Sin comportamiento (no métodos de negocio)
    - Optimizado para queries

    NO usar para:
    - Modificar artículos (usar Article Aggregate)
    - Ejecutar lógica de negocio
    - Persistir cambios
    """

    # Identificación
    id: UUID
    source_id: UUID

    # Metadata
    title: str
    url: str
    summary: Optional[str] = None
    author: Optional[str] = None
    language: Optional[str] = None
    thumbnail_url: Optional[str] = None

    # RSS Metadata
    rss_guid: Optional[str] = None
    pub_date: Optional[datetime] = None

    # Content
    content_scraped: Optional[str] = None
    content_plaintext: Optional[str] = None
    content_markdown: Optional[str] = None
    markdown_without_url: Optional[str] = None

    # Analysis
    keywords: Optional[List[str]] = None
    categories: Optional[List[str]] = None

    # Metrics
    word_count: Optional[int] = None
    reading_time_minutes: Optional[int] = None

    # Quality
    quality_score: Optional[float] = None
    validation_score: Optional[float] = None
    validated_by: Optional[str] = None

    # Timestamps
    published_at: Optional[datetime] = None
    created_at: datetime = None
    updated_at: datetime = None
    version: int = 0

    # Status
    status: Optional[str] = None

    def __post_init__(self):
        """Validación básica de tipos (no lógica de negocio)."""
        if not isinstance(self.id, UUID):
            raise TypeError("id debe ser UUID")
        if not isinstance(self.source_id, UUID):
            raise TypeError("source_id debe ser UUID")
        if not isinstance(self.title, str):
            raise TypeError("title debe ser string")
        if not isinstance(self.url, str):
            raise TypeError("url debe ser string")
