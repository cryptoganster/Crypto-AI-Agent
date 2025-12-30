"""
Modelo ORM para ContextChunk.

Este modelo representa la tabla context_chunks en la base de datos.
"""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from src.shared.infra.persistence.sqlalchemy_base_model import Base


class ContextChunkModel(Base):
    """
    Modelo ORM para ContextChunk.

    Representa un chunk individual dentro de un ContextPack.

    Attributes:
        id: ID único del chunk
        context_pack_id: ID del ContextPack al que pertenece
        chunk_id: ID del ContentChunk original
        content: Contenido del chunk
        position: Posición en el pack (orden)
        relevance_score: Score de relevancia para la query
        token_count: Número de tokens en el chunk
        created_at: Timestamp de creación
        context_pack: Relación con ContextPackModel
    """

    __tablename__ = "context_chunks"

    # Primary Key
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))

    # Foreign Keys
    context_pack_id = Column(
        String,
        ForeignKey("context_packs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    chunk_id = Column(String, nullable=False, index=True)

    # Attributes
    content = Column(Text, nullable=False)
    position = Column(Integer, nullable=False)
    relevance_score = Column(Float, nullable=False)
    token_count = Column(Integer, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    context_pack = relationship("ContextPackModel", back_populates="chunks")

    def __repr__(self) -> str:
        return (
            f"<ContextChunkModel(id={self.id}, "
            f"context_pack_id={self.context_pack_id}, "
            f"position={self.position})>"
        )
