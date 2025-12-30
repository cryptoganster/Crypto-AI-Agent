"""Mapper between ContentChunk domain aggregate and ORM model."""

from datetime import datetime
from typing import Optional

from src.chunking.domain.aggregates.content_chunk import ContentChunk
from src.chunking.domain.value_objects.chunk_id import ChunkId
from src.chunking.domain.value_objects.chunk_status import ChunkStatus
from src.chunking.domain.value_objects.chunk_summary import ChunkSummary
from src.chunking.domain.value_objects.token_count import TokenCount
from src.chunking.domain.value_objects.vector_embedding import VectorEmbedding
from src.chunking.infra.persistence.models.content_chunk_model import (
    ContentChunkModel,
)
from src.knowledge.domain.value_objects.source_reference import SourceReference


class ContentChunkMapper:
    """
    Mapper para convertir entre ContentChunk aggregate y ORM model.

    Responsabilidades:
    - Convertir aggregate de dominio a modelo ORM
    - Convertir modelo ORM a aggregate de dominio
    - Mapear Value Objects a primitivos y viceversa
    """

    @staticmethod
    def to_domain(model: ContentChunkModel) -> ContentChunk:
        """
        Convierte modelo ORM a aggregate de dominio.

        Args:
            model: ContentChunkModel ORM

        Returns:
            ContentChunk aggregate
        """
        # Mapear embedding si existe
        embedding = None
        if model.embedding is not None and model.embedding_model is not None:
            # Convertir lista a numpy array
            import numpy as np

            vector_array = np.array(model.embedding, dtype=np.float32)
            embedding = VectorEmbedding(
                vector=vector_array,
                model=model.embedding_model,
                dimension=len(model.embedding),
            )

        # Mapear summary si existe
        summary = None
        if model.summary_text is not None and model.summary_sentence_count is not None:
            summary = ChunkSummary(
                content=model.summary_text,
                sentence_count=model.summary_sentence_count,
            )

        # Crear SourceReference
        source = SourceReference(
            source_id=model.source_id,
            source_type=model.source_type,
        )

        # Crear aggregate
        from uuid import UUID

        return ContentChunk(
            id=ChunkId(UUID(model.id)),
            source=source,
            article_id=model.article_id,  # Mantener por compatibilidad
            content=model.content,
            position=model.position,
            start_char=model.start_char,
            end_char=model.end_char,
            token_count=TokenCount(
                value=model.token_count,
                encoding=model.token_encoding,
            ),
            source_url=model.source_url,
            embedding=embedding,
            summary=summary,
            status=ChunkStatus(model.status),
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    @staticmethod
    def to_model(aggregate: ContentChunk) -> ContentChunkModel:
        """
        Convierte aggregate de dominio a modelo ORM.

        Args:
            aggregate: ContentChunk aggregate

        Returns:
            ContentChunkModel ORM
        """
        # Extraer embedding si existe
        embedding_vector = None
        embedding_model = None
        if aggregate.embedding is not None:
            embedding_vector = aggregate.embedding.vector
            embedding_model = aggregate.embedding.model

        # Extraer summary si existe
        summary_text = None
        summary_sentence_count = None
        if aggregate.summary is not None:
            summary_text = aggregate.summary.content
            summary_sentence_count = aggregate.summary.sentence_count

        # Crear modelo
        return ContentChunkModel(
            id=str(aggregate.id),
            source_id=aggregate.source.source_id,
            source_type=aggregate.source.source_type,
            article_id=aggregate.article_id,  # Mantener por compatibilidad
            content=aggregate.content,
            embedding=embedding_vector,
            embedding_model=embedding_model,
            summary_text=summary_text,
            summary_sentence_count=summary_sentence_count,
            position=aggregate.position,
            start_char=aggregate.start_char,
            end_char=aggregate.end_char,
            token_count=aggregate.token_count.value,
            token_encoding=aggregate.token_count.encoding,
            source_url=aggregate.source_url,
            status=aggregate.status.value,
            created_at=aggregate.created_at,
            updated_at=aggregate.updated_at,
        )

    @staticmethod
    def update_model(model: ContentChunkModel, aggregate: ContentChunk) -> None:
        """
        Actualiza modelo ORM existente con datos del aggregate.

        Args:
            model: ContentChunkModel existente
            aggregate: ContentChunk con datos actualizados
        """
        # Actualizar campos básicos
        model.content = aggregate.content
        model.position = aggregate.position
        model.start_char = aggregate.start_char
        model.end_char = aggregate.end_char
        model.token_count = aggregate.token_count.value
        model.token_encoding = aggregate.token_count.encoding
        model.source_url = aggregate.source_url
        model.status = aggregate.status.value
        model.updated_at = aggregate.updated_at

        # Actualizar embedding si existe
        if aggregate.embedding is not None:
            model.embedding = aggregate.embedding.vector
            model.embedding_model = aggregate.embedding.model
        else:
            model.embedding = None
            model.embedding_model = None

        # Actualizar summary si existe
        if aggregate.summary is not None:
            model.summary_text = aggregate.summary.content
            model.summary_sentence_count = aggregate.summary.sentence_count
        else:
            model.summary_text = None
            model.summary_sentence_count = None
