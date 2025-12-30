"""Domain service para ensamblar context packs para RAG."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from src.chunking.domain.aggregates.content_chunk import ContentChunk
from src.chunking.domain.exceptions import ContextPackFullException
from src.chunking.domain.interfaces.services import IVectorStore
from src.chunking.domain.value_objects import VectorEmbedding
from src.rag.domain.aggregates.context_pack import ContextPack


class RAGContextAssemblyService:
    """
    Domain service para ensamblar context packs para RAG.

    Responsabilidades:
    - Recuperar chunks relevantes usando búsqueda vectorial
    - Ordenar por relevancia y fecha
    - Limitar tokens totales
    - Formatear para LLM

    Examples:
        >>> service = RAGContextAssemblyService(vector_store, max_tokens=4000)
        >>> pack = await service.assemble_context_pack(
        ...     query="Bitcoin ETF regulation",
        ...     query_embedding=embedding,
        ...     top_k=20
        ... )
        >>> pack.total_tokens <= 4000
        True
    """

    def __init__(
        self,
        vector_store: IVectorStore,
        max_tokens: int = 4000,
    ):
        """
        Inicializa RAGContextAssemblyService.

        Args:
            vector_store: Vector store para búsqueda semántica
            max_tokens: Límite máximo de tokens por context pack

        Raises:
            ValueError: Si max_tokens <= 0
        """
        if max_tokens <= 0:
            raise ValueError(f"max_tokens debe ser > 0, recibido: {max_tokens}")

        self._vector_store = vector_store
        self._max_tokens = max_tokens

    async def assemble_context_pack(
        self,
        query: str,
        query_embedding: VectorEmbedding,
        top_k: int = 20,
        filters: Optional[Dict[str, Any]] = None,
    ) -> ContextPack:
        """
        Ensambla context pack para RAG.

        Recupera chunks relevantes, los ordena por relevancia y fecha,
        y los agrega al context pack hasta alcanzar el límite de tokens.

        Args:
            query: Query de búsqueda
            query_embedding: Embedding del query
            top_k: Número de chunks a recuperar (default: 20)
            filters: Filtros adicionales (fecha, source, etc.)

        Returns:
            ContextPack con chunks relevantes

        Raises:
            ValueError: Si los parámetros son inválidos

        Examples:
            >>> service = RAGContextAssemblyService(vector_store)
            >>> pack = await service.assemble_context_pack(
            ...     query="Bitcoin regulation",
            ...     query_embedding=embedding,
            ...     top_k=10
            ... )
            >>> pack.get_chunk_count() <= 10
            True
            >>> pack.total_tokens <= service._max_tokens
            True
        """
        # Validar parámetros
        if not query or not query.strip():
            raise ValueError("query no puede estar vacío")

        if top_k <= 0:
            raise ValueError(f"top_k debe ser > 0, recibido: {top_k}")

        # Buscar chunks similares
        search_results = await self._vector_store.search_similar(
            query_embedding=query_embedding,
            top_k=top_k,
            filters=filters,
        )

        # Crear context pack
        context_pack = ContextPack.create(
            query=query,
            query_embedding=query_embedding,
            max_tokens=self._max_tokens,
        )

        # Ordenar resultados por relevancia (ya vienen ordenados) y fecha
        sorted_results = self._sort_by_relevance_and_date(search_results)

        # Agregar chunks hasta límite de tokens
        for chunk, score in sorted_results:
            try:
                context_pack.add_chunk(
                    chunk_id=chunk.id,
                    token_count=chunk.token_count.value,
                    relevance_score=score,
                    source_url=chunk.source_url,
                )
            except ContextPackFullException:
                # Pack está lleno, detener
                break

        return context_pack

    def _sort_by_relevance_and_date(
        self,
        results: List[tuple[ContentChunk, float]],
    ) -> List[tuple[ContentChunk, float]]:
        """
        Ordena resultados por relevancia (primero) y fecha (segundo).

        Args:
            results: Lista de (chunk, score) de búsqueda vectorial

        Returns:
            Lista ordenada por relevancia descendente, luego fecha descendente

        Examples:
            >>> results = [(chunk1, 0.9), (chunk2, 0.9), (chunk3, 0.8)]
            >>> sorted_results = service._sort_by_relevance_and_date(results)
            >>> # chunk1 y chunk2 tienen mismo score, se ordenan por fecha
            >>> # chunk3 tiene menor score, va al final
        """
        # Ordenar por:
        # 1. Relevancia descendente (score más alto primero)
        # 2. Fecha descendente (más reciente primero)
        return sorted(
            results,
            key=lambda x: (
                -x[1],  # Relevancia descendente (negativo para invertir)
                -(
                    x[0].published_at.timestamp() if x[0].published_at else 0
                ),  # Fecha descendente
            ),
        )

    async def assemble_with_source_deduplication(
        self,
        query: str,
        query_embedding: VectorEmbedding,
        top_k: int = 20,
        max_chunks_per_source: int = 3,
        filters: Optional[Dict[str, Any]] = None,
    ) -> ContextPack:
        """
        Ensambla context pack con deduplicación de fuentes.

        Limita el número de chunks por fuente para asegurar diversidad
        de contenido en el context pack.

        Args:
            query: Query de búsqueda
            query_embedding: Embedding del query
            top_k: Número de chunks a recuperar
            max_chunks_per_source: Máximo de chunks por fuente (default: 3)
            filters: Filtros adicionales

        Returns:
            ContextPack con chunks de fuentes diversas

        Examples:
            >>> pack = await service.assemble_with_source_deduplication(
            ...     query="Bitcoin",
            ...     query_embedding=embedding,
            ...     max_chunks_per_source=2
            ... )
            >>> # Ninguna fuente debería tener más de 2 chunks
        """
        if max_chunks_per_source <= 0:
            raise ValueError(
                f"max_chunks_per_source debe ser > 0, recibido: {max_chunks_per_source}"
            )

        # Buscar chunks similares
        search_results = await self._vector_store.search_similar(
            query_embedding=query_embedding,
            top_k=top_k,
            filters=filters,
        )

        # Crear context pack
        context_pack = ContextPack.create(
            query=query,
            query_embedding=query_embedding,
            max_tokens=self._max_tokens,
        )

        # Ordenar resultados
        sorted_results = self._sort_by_relevance_and_date(search_results)

        # Trackear chunks por fuente
        chunks_per_source: Dict[str, int] = {}

        # Agregar chunks con límite por fuente
        for chunk, score in sorted_results:
            source_url = chunk.source_url

            # Verificar límite por fuente
            if chunks_per_source.get(source_url, 0) >= max_chunks_per_source:
                continue

            try:
                context_pack.add_chunk(
                    chunk_id=chunk.id,
                    token_count=chunk.token_count.value,
                    relevance_score=score,
                    source_url=source_url,
                )

                # Incrementar contador de fuente
                chunks_per_source[source_url] = chunks_per_source.get(source_url, 0) + 1

            except ContextPackFullException:
                # Pack está lleno, detener
                break

        return context_pack

    async def get_context_pack_summary(
        self,
        context_pack: ContextPack,
    ) -> Dict[str, Any]:
        """
        Genera resumen del context pack para logging/debugging.

        Args:
            context_pack: Context pack a resumir

        Returns:
            Diccionario con estadísticas del pack

        Examples:
            >>> pack = await service.assemble_context_pack(...)
            >>> summary = await service.get_context_pack_summary(pack)
            >>> summary["chunk_count"]
            10
            >>> summary["total_tokens"]
            3500
        """
        return {
            "query": context_pack.query,
            "chunk_count": context_pack.get_chunk_count(),
            "total_tokens": context_pack.total_tokens,
            "max_tokens": context_pack.max_tokens,
            "remaining_tokens": context_pack.get_remaining_tokens(),
            "source_count": context_pack.get_source_count(),
            "average_relevance": context_pack.get_average_relevance(),
            "is_full": context_pack.is_full(),
            "sources": context_pack.sources,
            "created_at": context_pack.created_at.isoformat(),
        }
