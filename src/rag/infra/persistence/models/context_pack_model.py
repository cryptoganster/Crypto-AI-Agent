"""
Modelo ORM para ContextPack.

Este modelo representa la tabla context_packs en la base de datos.
"""

from datetime import datetime
from typing import List
from uuid import uuid4

from sqlalchemy import JSON, Column, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import relationship

from src.shared.infra.persistence.sqlalchemy_base_model import Base


class ContextPackModel(Base):
    """
    Modelo ORM para ContextPack.

    Representa un paquete de contexto ensamblado para RAG.

    Attributes:
        id: ID único del context pack
        article_id: ID del artículo fuente
        query: Query que generó este pack
        created_at: Timestamp de creación
        total_chunks: Número total de chunks en el pack
        total_tokens: Total de tokens en el pack
        avg_relevance_score: Score promedio de relevancia
        metadata: Metadatos adicionales (JSON)
        chunks: Relación con ContextChunkModel
    """

    __tablename__ = "context_packs"

    # Primary Key
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))

    # Foreign Keys
    article_id = Column(String, nullable=False, index=True)

    # Attributes
    query = Column(Text, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    total_chunks = Column(Integer, nullable=False, default=0)
    total_tokens = Column(Integer, nullable=False, default=0)
    avg_relevance_score = Column(Float, nullable=True)

    # Metadata (JSON) - Renombrado a pack_metadata para evitar conflicto con SQLAlchemy
    pack_metadata = Column(JSON, nullable=True)

    # Relationships
    chunks = relationship(
        "ContextChunkModel",
        back_populates="context_pack",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return (
            f"<ContextPackModel(id={self.id}, "
            f"article_id={self.article_id}, "
            f"total_chunks={self.total_chunks})>"
        )
