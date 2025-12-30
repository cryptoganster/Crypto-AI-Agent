"""Handler para GetArticleChunksQuery."""

from typing import List

from src.chunking.app.queries.get_article_chunks.dto import (
    ArticleChunkDTO,
    ArticleChunksResultDTO,
)
from src.chunking.app.queries.get_article_chunks.query import GetArticleChunksQuery
from src.chunking.domain.interfaces.repositories.content_chunk_read_repository import (
    IContentChunkReadRepository,
)
from src.shared.kernel.logger import ILogger


class GetArticleChunksHandler:
    """
    Handler para GetArticleChunksQuery.

    Responsabilidad: Consultar chunks de un artículo desde el repository
    sin modificar ningún estado.

    Este handler es una query pura (CQRS) que solo lee estado.
    """

    def __init__(
        self,
        chunk_repository: IContentChunkReadRepository,
        logger: ILogger,
    ):
        """
        Inicializa el handler.

        Args:
            chunk_repository: Repository para leer chunks
            logger: Logger para registrar operaciones
        """
        self._chunk_repository = chunk_repository
        self._logger = logger.bind(
            layer="application",
            component="GetArticleChunksHandler",
        )

    async def handle(self, query: GetArticleChunksQuery) -> ArticleChunksResultDTO:
        """
        Ejecuta la query para obtener chunks de un artículo.

        Args:
            query: Query con los parámetros de búsqueda

        Returns:
            DTO con los chunks y metadata de paginación

        Example:
            >>> query = GetArticleChunksQuery(article_id="art-123")
            >>> result = await handler.handle(query)
            >>> print(f"Total chunks: {result.total_chunks}")
            >>> print(f"Retornados: {result.returned_chunks}")
            >>> for chunk in result.chunks:
            ...     print(f"Chunk {chunk.position}: {chunk.text_preview}")
        """
        self._logger.debug(
            "Consultando chunks de artículo",
            article_id=query.article_id,
            include_embeddings=query.include_embeddings,
            include_summaries=query.include_summaries,
            limit=query.limit,
            offset=query.offset,
        )

        # Obtener chunks desde repository (NO modifica estado)
        chunks = await self._chunk_repository.find_by_article_id(
            article_id=query.article_id,
            limit=query.limit,
            offset=query.offset,
        )

        # Contar total de chunks del artículo
        total_chunks = await self._chunk_repository.count_by_article_id(
            article_id=query.article_id
        )

        # Convertir aggregates a DTOs
        chunk_dtos = self._convert_to_dtos(
            chunks=chunks,
            include_embeddings=query.include_embeddings,
            include_summaries=query.include_summaries,
        )

        # Determinar si hay más chunks disponibles
        has_more = False
        if query.limit is not None:
            has_more = (query.offset + len(chunk_dtos)) < total_chunks

        # Crear resultado
        result = ArticleChunksResultDTO(
            article_id=query.article_id,
            chunks=chunk_dtos,
            total_chunks=total_chunks,
            returned_chunks=len(chunk_dtos),
            offset=query.offset,
            has_more=has_more,
        )

        self._logger.debug(
            "Chunks obtenidos",
            article_id=query.article_id,
            total_chunks=result.total_chunks,
            returned_chunks=result.returned_chunks,
            has_more=result.has_more,
        )

        return result

    def _convert_to_dtos(
        self,
        chunks: List,
        include_embeddings: bool,
        include_summaries: bool,
    ) -> List[ArticleChunkDTO]:
        """
        Convierte ContentChunk aggregates a DTOs.

        Args:
            chunks: Lista de ContentChunk aggregates
            include_embeddings: Si incluir embeddings en DTOs
            include_summaries: Si incluir summaries en DTOs

        Returns:
            Lista de ArticleChunkDTO
        """
        dtos = []

        for chunk in chunks:
            # Extraer embedding si se solicitó
            embedding = None
            embedding_dimension = None
            if include_embeddings and chunk.embedding is not None:
                embedding = (
                    chunk.embedding.vector.tolist()
                )  # Convertir numpy array a lista
                embedding_dimension = chunk.embedding.dimension
            elif chunk.embedding is not None:
                # Solo incluir dimensión aunque no se incluya el embedding
                embedding_dimension = chunk.embedding.dimension

            # Extraer summary si se solicitó
            summary = None
            if include_summaries and chunk.summary is not None:
                summary = str(chunk.summary)

            # Crear DTO
            dto = ArticleChunkDTO(
                chunk_id=str(chunk.id),
                article_id=str(chunk.article_id),
                position=chunk.position,
                text=str(chunk.content),
                token_count=chunk.token_count.value,
                summary=summary,
                embedding=embedding,
                embedding_dimension=embedding_dimension,
                is_completed=chunk.is_completed(),  # Es un método, no propiedad
            )
            dtos.append(dto)

        return dtos
