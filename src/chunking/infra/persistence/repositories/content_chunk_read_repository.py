"""Read repository implementation for ContentChunk aggregate."""

from typing import List, Optional

from sqlalchemy import and_, exists, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.chunking.domain.aggregates.content_chunk import ContentChunk
from src.chunking.domain.interfaces.repositories.content_chunk_read_repository import (
    IContentChunkReadRepository,
)
from src.chunking.domain.value_objects.chunk_status import ChunkStatus
from src.chunking.infra.persistence.mappers.content_chunk_mapper import (
    ContentChunkMapper,
)
from src.chunking.infra.persistence.models.content_chunk_model import (
    ContentChunkModel,
)
from src.knowledge.domain.value_objects.source_reference import SourceReference


class SqlAlchemyContentChunkReadRepository(IContentChunkReadRepository):
    """
    Implementación SQLAlchemy de IContentChunkReadRepository.

    Responsabilidades:
    - Leer ContentChunk aggregates
    - Queries de solo lectura
    - Usar mapper para conversión ORM → domain
    """

    def __init__(self, session: AsyncSession):
        """
        Inicializa repository.

        Args:
            session: SQLAlchemy async session
        """
        self._session = session
        self._mapper = ContentChunkMapper()

    async def find_by_id(self, chunk_id: str) -> Optional[ContentChunk]:
        """
        Busca ContentChunk por ID.

        Args:
            chunk_id: ID del ContentChunk

        Returns:
            ContentChunk si existe, None si no
        """
        stmt = select(ContentChunkModel).where(ContentChunkModel.id == chunk_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()

        if model is None:
            return None

        return self._mapper.to_domain(model)

    async def find_by_source(
        self,
        source: SourceReference,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[ContentChunk]:
        """
        Busca todos los chunks de una fuente.

        Args:
            source: SourceReference (source_id + source_type)
            limit: Límite de resultados (opcional)
            offset: Offset para paginación (opcional)

        Returns:
            Lista de ContentChunks ordenados por position
        """
        stmt = (
            select(ContentChunkModel)
            .where(
                and_(
                    ContentChunkModel.source_id == source.source_id,
                    ContentChunkModel.source_type == source.source_type,
                )
            )
            .order_by(ContentChunkModel.position)
        )

        if offset is not None:
            stmt = stmt.offset(offset)
        if limit is not None:
            stmt = stmt.limit(limit)

        result = await self._session.execute(stmt)
        models = result.scalars().all()

        return [self._mapper.to_domain(model) for model in models]

    async def find_by_article_id(
        self,
        article_id: str,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[ContentChunk]:
        """
        DEPRECATED: Usar find_by_source() en su lugar.

        Busca todos los chunks de un artículo.

        Args:
            article_id: ID del artículo
            limit: Límite de resultados (opcional)
            offset: Offset para paginación (opcional)

        Returns:
            Lista de ContentChunks ordenados por position
        """
        stmt = (
            select(ContentChunkModel)
            .where(ContentChunkModel.article_id == article_id)
            .order_by(ContentChunkModel.position)
        )

        if offset is not None:
            stmt = stmt.offset(offset)
        if limit is not None:
            stmt = stmt.limit(limit)

        result = await self._session.execute(stmt)
        models = result.scalars().all()

        return [self._mapper.to_domain(model) for model in models]

    async def find_by_status(
        self,
        status: ChunkStatus,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[ContentChunk]:
        """
        Busca chunks por estado.

        Args:
            status: Estado a buscar
            limit: Límite de resultados (opcional)
            offset: Offset para paginación (opcional)

        Returns:
            Lista de ContentChunks con el estado especificado
        """
        stmt = (
            select(ContentChunkModel)
            .where(ContentChunkModel.status == status.value)
            .order_by(ContentChunkModel.created_at)
        )

        if offset is not None:
            stmt = stmt.offset(offset)
        if limit is not None:
            stmt = stmt.limit(limit)

        result = await self._session.execute(stmt)
        models = result.scalars().all()

        return [self._mapper.to_domain(model) for model in models]

    async def exists(self, chunk_id: str) -> bool:
        """
        Verifica si existe ContentChunk por ID.

        Args:
            chunk_id: ID del ContentChunk

        Returns:
            True si existe, False si no
        """
        stmt = select(exists().where(ContentChunkModel.id == chunk_id))
        result = await self._session.execute(stmt)
        return result.scalar()

    async def count_by_source(self, source: SourceReference) -> int:
        """
        Cuenta chunks de una fuente.

        Args:
            source: SourceReference (source_id + source_type)

        Returns:
            Número de chunks
        """
        stmt = (
            select(func.count())
            .select_from(ContentChunkModel)
            .where(
                and_(
                    ContentChunkModel.source_id == source.source_id,
                    ContentChunkModel.source_type == source.source_type,
                )
            )
        )
        result = await self._session.execute(stmt)
        return result.scalar()

    async def count_by_article_id(self, article_id: str) -> int:
        """
        DEPRECATED: Usar count_by_source() en su lugar.

        Cuenta chunks de un artículo.

        Args:
            article_id: ID del artículo

        Returns:
            Número de chunks
        """
        stmt = (
            select(func.count())
            .select_from(ContentChunkModel)
            .where(ContentChunkModel.article_id == article_id)
        )
        result = await self._session.execute(stmt)
        return result.scalar()

    async def count_by_status(self, status: ChunkStatus) -> int:
        """
        Cuenta chunks por estado.

        Args:
            status: Estado a contar

        Returns:
            Número de chunks con ese estado
        """
        stmt = (
            select(func.count())
            .select_from(ContentChunkModel)
            .where(ContentChunkModel.status == status.value)
        )
        result = await self._session.execute(stmt)
        return result.scalar()

    async def find_similar_by_embedding(
        self,
        embedding_vector: List[float],
        threshold: float,
        limit: int = 10,
        exclude_source: Optional[SourceReference] = None,
    ) -> List[tuple[ContentChunk, float]]:
        """
        Busca chunks similares usando búsqueda vectorial con pgvector.

        Args:
            embedding_vector: Vector de embedding para comparar
            threshold: Threshold de similitud (0.0-1.0)
            limit: Máximo número de resultados
            exclude_source: SourceReference a excluir (opcional)

        Returns:
            Lista de tuplas (ContentChunk, similarity_score) ordenadas por similitud

        Note:
            Usa operador de similitud coseno (<->) de pgvector.
            Similarity score se calcula como: 1 - distance
        """
        from sqlalchemy import text

        # Construir query con pgvector
        # Usamos <-> para distancia coseno (menor = más similar)
        query = """
            SELECT 
                id,
                source_id,
                source_type,
                article_id,
                content,
                embedding,
                embedding_model,
                summary_text,
                summary_sentence_count,
                position,
                start_char,
                end_char,
                token_count,
                token_encoding,
                source_url,
                status,
                created_at,
                updated_at,
                1 - (embedding <-> :embedding_vector::vector) as similarity_score
            FROM crypto_news_scraper.ai_content_chunks
            WHERE embedding IS NOT NULL
        """

        params = {
            "embedding_vector": str(embedding_vector),
            "threshold": threshold,
            "limit": limit,
        }

        # Agregar filtro de source si se especifica
        if exclude_source:
            query += " AND NOT (source_id = :exclude_source_id AND source_type = :exclude_source_type)"
            params["exclude_source_id"] = exclude_source.source_id
            params["exclude_source_type"] = exclude_source.source_type

        # Filtrar por threshold y ordenar
        query += """
            AND (1 - (embedding <-> :embedding_vector::vector)) >= :threshold
            ORDER BY embedding <-> :embedding_vector::vector
            LIMIT :limit
        """

        # Ejecutar query
        result = await self._session.execute(text(query), params)
        rows = result.fetchall()

        # Convertir rows a tuplas (ContentChunk, similarity_score)
        results = []
        for row in rows:
            # Crear modelo temporal para usar el mapper
            model = ContentChunkModel(
                id=row.id,
                source_id=row.source_id,
                source_type=row.source_type,
                article_id=row.article_id,
                content=row.content,
                embedding=row.embedding,
                embedding_model=row.embedding_model,
                summary_text=row.summary_text,
                summary_sentence_count=row.summary_sentence_count,
                position=row.position,
                start_char=row.start_char,
                end_char=row.end_char,
                token_count=row.token_count,
                token_encoding=row.token_encoding,
                source_url=row.source_url,
                status=row.status,
                created_at=row.created_at,
                updated_at=row.updated_at,
            )

            chunk = self._mapper.to_domain(model)
            similarity_score = float(row.similarity_score)

            results.append((chunk, similarity_score))

        return results
