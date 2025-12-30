"""SQLAlchemy model for ContentChunk aggregate."""

from datetime import datetime

from sqlalchemy import Column, DateTime, Float, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY

from src.shared.infra.persistence.sqlalchemy_base_model import Base


class ContentChunkModel(Base):
    """
    ORM model for ai_content_chunks table.

    Representa un chunk de contenido como Aggregate Root independiente.
    Cada chunk puede ser consultado y actualizado sin cargar el artículo completo.
    """

    __tablename__ = "ai_content_chunks"
    __table_args__ = (
        # Composite indexes for efficient queries
        # Nuevos índices con source_id y source_type
        Index(
            "ix_content_chunks_source_position", "source_id", "source_type", "position"
        ),
        Index("ix_content_chunks_source_status", "source_id", "source_type", "status"),
        # Índices legacy (mantener por compatibilidad)
        Index("ix_content_chunks_article_position", "article_id", "position"),
        Index("ix_content_chunks_status", "status"),
        Index("ix_content_chunks_article_status", "article_id", "status"),
        {"schema": "crypto_news_scraper"},
    )

    # Primary key
    id = Column(String, primary_key=True)

    # Reference to source (external aggregate)
    # Mantiene article_id por compatibilidad, pero source_id es el campo principal
    article_id = Column(
        String, nullable=False, index=True
    )  # DEPRECATED: usar source_id
    source_id = Column(String, nullable=False, index=True)
    source_type = Column(String, nullable=False, default="rss_article", index=True)

    # Content
    content = Column(Text, nullable=False)

    # Embedding (vector de 768 dimensiones)
    embedding = Column(ARRAY(Float), nullable=True)
    embedding_model = Column(String, nullable=True)

    # Summary
    summary_text = Column(Text, nullable=True)
    summary_sentence_count = Column(Integer, nullable=True)

    # Position in article
    position = Column(Integer, nullable=False)
    start_char = Column(Integer, nullable=False)
    end_char = Column(Integer, nullable=False)

    # Metadata
    token_count = Column(Integer, nullable=False)
    token_encoding = Column(String, nullable=False)
    source_url = Column(String, nullable=False)

    # Status
    status = Column(String, nullable=False, default="PENDING")

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    def __repr__(self) -> str:
        return (
            f"<ContentChunkModel(id={self.id}, "
            f"source_id={self.source_id}, "
            f"source_type={self.source_type}, "
            f"position={self.position}, "
            f"status={self.status})>"
        )
