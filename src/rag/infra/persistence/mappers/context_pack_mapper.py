"""
Mapper entre ContextPack domain y ContextPackModel ORM.

Este mapper convierte entre:
- ContextPack (domain aggregate)
- ContextPackModel (ORM model)
"""

from typing import Any, Dict

from src.rag.domain.aggregates.context_pack import ContextPack, ContextChunk
from src.rag.domain.value_objects.context_pack_id import ContextPackId
from src.rag.infra.persistence.models.context_chunk_model import ContextChunkModel
from src.rag.infra.persistence.models.context_pack_model import ContextPackModel


class ContextPackMapper:
    """
    Mapper para ContextPack.

    Convierte entre agregados de dominio y modelos ORM.
    """

    @staticmethod
    def to_domain(model: ContextPackModel) -> ContextPack:
        """
        Convierte ContextPackModel a ContextPack domain.

        Args:
            model: Modelo ORM

        Returns:
            ContextPack aggregate
        """
        # Convertir chunks
        chunks = [
            ContextChunk(
                chunk_id=chunk_model.chunk_id,
                content=chunk_model.content,
                position=chunk_model.position,
                relevance_score=chunk_model.relevance_score,
                token_count=chunk_model.token_count,
            )
            for chunk_model in sorted(model.chunks, key=lambda c: c.position)
        ]

        return ContextPack(
            id=ContextPackId(model.id),
            article_id=model.article_id,
            query=model.query,
            chunks=chunks,
            created_at=model.created_at,
            metadata=model.metadata or {},
        )

    @staticmethod
    def to_model(context_pack: ContextPack) -> ContextPackModel:
        """
        Convierte ContextPack domain a ContextPackModel ORM.

        Args:
            context_pack: Aggregate de dominio

        Returns:
            ContextPackModel ORM
        """
        # Crear modelo principal
        model = ContextPackModel(
            id=str(context_pack.id),
            article_id=context_pack.article_id,
            query=context_pack.query,
            created_at=context_pack.created_at,
            total_chunks=context_pack.total_chunks,
            total_tokens=context_pack.total_tokens,
            avg_relevance_score=context_pack.avg_relevance_score,
            metadata=context_pack.metadata,
        )

        # Crear chunks
        chunk_models = [
            ContextChunkModel(
                context_pack_id=str(context_pack.id),
                chunk_id=chunk.chunk_id,
                content=chunk.content,
                position=chunk.position,
                relevance_score=chunk.relevance_score,
                token_count=chunk.token_count,
                created_at=context_pack.created_at,
            )
            for chunk in context_pack.chunks
        ]

        model.chunks = chunk_models

        return model

    @staticmethod
    def update_model(model: ContextPackModel, context_pack: ContextPack) -> None:
        """
        Actualiza ContextPackModel existente con datos de ContextPack.

        Args:
            model: Modelo ORM existente
            context_pack: Aggregate de dominio con datos actualizados
        """
        # Actualizar atributos principales
        model.query = context_pack.query
        model.total_chunks = context_pack.total_chunks
        model.total_tokens = context_pack.total_tokens
        model.avg_relevance_score = context_pack.avg_relevance_score
        model.metadata = context_pack.metadata

        # Actualizar chunks (reemplazar todos)
        model.chunks.clear()

        chunk_models = [
            ContextChunkModel(
                context_pack_id=str(context_pack.id),
                chunk_id=chunk.chunk_id,
                content=chunk.content,
                position=chunk.position,
                relevance_score=chunk.relevance_score,
                token_count=chunk.token_count,
                created_at=context_pack.created_at,
            )
            for chunk in context_pack.chunks
        ]

        model.chunks.extend(chunk_models)
