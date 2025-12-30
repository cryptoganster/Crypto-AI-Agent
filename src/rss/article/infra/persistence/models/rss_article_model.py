"""RssArticle SQLAlchemy Model para RssArticle aggregate.

Este modelo pertenece al bounded context Article y mapea el RssArticle aggregate
a la tabla 'articles' en el schema 'crypto_news_scraper'.

Convenciones de ID:
- id: Primary Key del aggregate (UUID)
- source_id: Foreign Key al bounded context Source
"""

from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import (
    ARRAY,
    JSONB,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.sql import func

from src.shared.infra.persistence import Base
from src.shared.kernel.logger import ILogger

if TYPE_CHECKING:
    from src.rss.article.domain.aggregates import RssArticle
    from src.rss.article.domain.value_objects.metadata import RssArticleId
    from src.shared.domain.value_objects import Level


class RssArticleModel(Base):
    """
    SQLAlchemy model para RssArticle aggregate.

    Mapea el RssArticle aggregate a tabla de base de datos,
    siguiendo principios de Infrastructure Layer en Clean Architecture.

    Convenciones de ID:
    - id: Primary Key (UUID) - identificador único del RssArticle
    - source_id: Foreign Key al Source aggregate
    """

    __tablename__ = "rss_articles"
    __table_args__ = (
        # Core Article Indexes
        Index("idx_rss_articles_source_id", "source_id"),
        Index("idx_rss_articles_content_hash", "content_hash"),
        Index("idx_rss_articles_processing_stage", "processing_stage"),
        Index("idx_rss_articles_quality_level", "quality_level"),
        Index("idx_rss_articles_language", "language"),
        # Time-based Indexes
        Index("idx_rss_articles_created_at", "created_at"),
        Index("idx_rss_articles_fetched_at", "fetched_at"),
        Index("idx_rss_articles_pub_date", "pub_date"),
        # Combined Indexes for common queries
        Index("idx_rss_articles_source_pub_date", "source_id", "pub_date"),
        # RSS Content Indexes
        Index("idx_rss_articles_rss_guid", "rss_guid"),
        # Deduplication Indexes
        Index("idx_rss_articles_url_source", "url", "source_id"),
        Index("idx_rss_articles_title_source", "title", "source_id"),
        # Unique constraint para deduplication
        Index("uq_rss_articles_url_source", "url", "source_id", unique=True),
        # Schema configuration
        {"schema": "crypto_news_scraper"},
    )

    # === PRIMARY KEY ===
    # Convención: 'id' como PK del aggregate
    id = Column(
        PGUUID(as_uuid=True),
        primary_key=True,
        nullable=False,
        comment="Article aggregate root ID (PK)",
    )

    # === TIMESTAMPS ===
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Fecha de creación del artículo",
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="Fecha de última actualización",
    )

    # === FOREIGN KEYS ===
    # Referencia al bounded context Source (tabla rss_feeds)
    source_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey("crypto_news_scraper.rss_feeds.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="ID de la fuente (Source aggregate)",
    )

    # === RSS METADATA ===
    rss_guid = Column(
        String(500),
        nullable=True,
        index=True,
        comment="GUID único del artículo en el feed RSS",
    )

    title = Column(
        String(1000),
        nullable=False,
        index=True,
        comment="Título del artículo",
    )

    url = Column(Text, nullable=False, comment="URL original del artículo")

    description = Column(
        Text,
        nullable=True,
        comment="Descripción/resumen del artículo",
    )

    pub_date = Column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
        comment="Fecha de publicación según el feed RSS",
    )

    # === CONTENT ===
    content_scraped = Column(
        Text,
        nullable=True,
        comment="Contenido HTML completo scrapeado desde la URL original",
    )

    content_plaintext = Column(
        Text,
        nullable=True,
        comment="Texto plano limpio sin HTML/Markdown (para NLP)",
    )

    content_markdown = Column(
        Text,
        nullable=True,
        comment="Contenido en formato Markdown (PRINCIPAL)",
    )

    markdown_without_url = Column(
        Text,
        nullable=True,
        comment="Contenido en formato Markdown sin URLs (para procesamiento AI/ML)",
    )

    summary = Column(
        Text,
        nullable=True,
        comment="Resumen generado del artículo",
    )

    # === CATEGORIZATION ===
    categories = Column(
        ARRAY(String),
        nullable=True,
        default=list,
        comment="Categorías del artículo",
    )

    tags = Column(
        ARRAY(String),
        nullable=True,
        default=list,
        comment="Tags/palabras clave del artículo",
    )

    keywords = Column(
        ARRAY(String),
        nullable=True,
        default=list,
        comment="Keywords extraídas automáticamente del contenido",
    )

    coin_mentions = Column(
        JSONB,
        nullable=True,
        comment="Menciones de criptomonedas detectadas",
    )

    enclosures = Column(
        JSONB,
        nullable=True,
        default=list,
        comment="URLs de media/archivos adjuntos",
    )

    thumbnail_url = Column(
        String(1000),
        nullable=True,
        comment="URL de imagen thumbnail del artículo",
    )

    # === PROCESSING ===
    processing_stage = Column(
        String(50),
        nullable=True,
        index=True,
        comment="Etapa específica de procesamiento",
    )

    # === QUALITY & DEDUPLICATION ===
    content_hash = Column(
        String(64),
        nullable=True,
        index=True,
        comment="Hash SHA-256 del contenido para deduplicación",
    )

    quality_score = Column(
        Integer,
        nullable=True,
        comment="Puntuación de calidad del artículo (0-100)",
    )

    quality_level = Column(
        String(20),
        nullable=True,
        comment="Nivel de calidad: low, medium, high, premium",
    )

    word_count = Column(
        Integer,
        nullable=True,
        comment="Número de palabras del artículo",
    )

    reading_time_minutes = Column(
        Integer,
        nullable=True,
        comment="Tiempo estimado de lectura en minutos",
    )

    is_coin_checked = Column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
        index=True,
        comment="Indica si el artículo fue verificado para menciones de criptomonedas",
    )

    # === AUTHOR ===
    author = Column(
        String(255),
        nullable=True,
        comment="Nombre del autor del artículo",
    )

    author_email = Column(
        String(255),
        nullable=True,
        comment="Email del autor del artículo",
    )

    # === TIMESTAMPS DE PROCESAMIENTO ===
    fetched_at = Column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
        comment="Timestamp de cuando se obtuvo del feed",
    )

    processed_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="Timestamp de cuando se procesó el contenido",
    )

    published_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="Timestamp de cuando se publicó/activó",
    )

    archived_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="Timestamp de cuando se archivó",
    )

    # === ERROR HANDLING ===
    error_message = Column(
        Text,
        nullable=True,
        comment="Mensaje de error durante el procesamiento",
    )

    error_type = Column(
        String(100),
        nullable=True,
        comment="Tipo de error: PARSING, VALIDATION, NETWORK, etc.",
    )

    retry_count = Column(
        Integer,
        default=0,
        nullable=False,
        comment="Número de intentos de reprocesamiento",
    )

    # === LANGUAGE ===
    language = Column(
        String(10),
        nullable=True,
        default=None,
        comment="Código de idioma del artículo (es, en, fr, etc.)",
    )

    # === ENGAGEMENT ===
    view_count = Column(
        Integer,
        default=0,
        nullable=False,
        comment="Número de visualizaciones del artículo",
    )

    engagement_score = Column(
        Float,
        nullable=True,
        comment="Puntuación de engagement calculada",
    )

    # === DUPLICATE TRACKING ===
    is_duplicate = Column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
        index=True,
        comment="Indica si el artículo es duplicado de otro",
    )

    # Referencia al Article del cual este es duplicado
    duplicate_of_id = Column(
        PGUUID(as_uuid=True),
        nullable=True,
        index=True,
        comment="ID del artículo del cual este es duplicado",
    )

    # === VALIDATION ===
    validation_score = Column(
        Float,
        nullable=True,
        comment="Score de validación del artículo (0.0 a 1.0)",
    )

    validated_by = Column(
        String(255),
        nullable=True,
        comment="Identificador de quién validó el artículo",
    )

    validated_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="Timestamp de cuándo se validó",
    )

    # === ERROR TRACKING ===
    has_error = Column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
        index=True,
        comment="Indica si el artículo tiene errores",
    )

    error_marked_by = Column(
        String(255),
        nullable=True,
        comment="Identificador de quién marcó el error",
    )

    error_marked_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="Timestamp de cuándo se marcó el error",
    )

    # === READABILITY ===
    readability_score = Column(
        Float,
        nullable=True,
        comment="Score de legibilidad del contenido",
    )

    # === VERSION ===
    version = Column(
        Integer,
        nullable=False,
        default=1,
        comment="Versión para control de concurrencia optimista",
    )

    def __init__(self, **kwargs):
        """Constructor con logging inyectado."""
        super().__init__(**kwargs)
        self._logger: ILogger = kwargs.get("logger")

    def update_version(self) -> None:
        """Incrementa la versión para control de concurrencia optimista."""
        if self.version is None:
            self.version = 1
        else:
            self.version += 1
        self.updated_at = datetime.now(timezone.utc)

    def mark_as_processed(self, processing_stage: Optional[str] = None) -> None:
        """Marca artículo como procesado."""
        self.processed_at = datetime.now(timezone.utc)
        if processing_stage:
            self.processing_stage = processing_stage
        self.update_version()

    def record_error(self, error_message: str, error_type: str = "GENERAL") -> None:
        """Registra error de procesamiento."""
        self.error_message = error_message[:1000]
        self.error_type = error_type
        self.retry_count += 1
        self.update_version()

    def clear_error(self) -> None:
        """Limpia información de error."""
        self.error_message = None
        self.error_type = None
        self.retry_count = 0
        self.update_version()

    def is_duplicate_by_guid(self, other_guid: str) -> bool:
        """Verifica si es duplicado por GUID."""
        return self.rss_guid == other_guid

    def is_duplicate_by_url(self, other_url: str) -> bool:
        """Verifica si es duplicado por URL."""
        return self.url == other_url

    def is_recent(self, hours: int = 24) -> bool:
        """Verifica si el artículo es reciente."""
        if not self.pub_date:
            return False

        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        return self.pub_date >= cutoff

    def __repr__(self) -> str:
        title_preview = self.title[:50] if self.title else "N/A"
        return f"<ArticleModel(id={self.id}, title='{title_preview}...')>"
