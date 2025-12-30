"""Interface para vector store (almacenamiento y búsqueda de embeddings)."""

from typing import Any, Dict, List, Optional, Protocol, Tuple

from src.chunking.domain.aggregates.content_chunk import ContentChunk
from src.chunking.domain.value_objects.vector_embedding import VectorEmbedding
from src.knowledge.domain.value_objects.source_reference import SourceReference


class IVectorStore(Protocol):
    """
    Interface para vector store.

    Define el contrato para servicios que almacenan y buscan embeddings vectoriales
    usando bases de datos vectoriales como PostgreSQL + pgvector. Permite búsqueda
    semántica eficiente usando similitud coseno.

    Implementaciones:
    - PgVectorStoreAdapter: Usa PostgreSQL + pgvector con índices HNSW
    - ChromaDBAdapter: Usa ChromaDB (alternativa)
    - PineconeAdapter: Usa Pinecone (cloud)

    Responsabilidades:
    - Almacenar chunks con sus embeddings en la base de datos vectorial
    - Buscar chunks similares usando similitud coseno
    - Recuperar TLDRs de artículos procesados
    - Eliminar chunks cuando un artículo es eliminado o reprocesado
    - Mantener índices HNSW para búsqueda eficiente

    Invariantes:
    - Todos los chunks almacenados deben tener embeddings válidos
    - Los embeddings deben estar normalizados (magnitud = 1.0)
    - La búsqueda debe retornar resultados ordenados por similitud descendente
    - Los scores de similitud deben estar en rango [0, 1]

    Performance:
    - Búsqueda vectorial: < 100ms para top-10 en 1M+ chunks (Requirements 11.4)
    - Almacenamiento: Bulk inserts para eficiencia (Requirements 11.3)
    - Índice HNSW: m=16, ef_construction=64 (Requirements 4.3)

    Examples:
        >>> store: IVectorStore = PgVectorStoreAdapter(session)
        >>>
        >>> # Almacenar chunks
        >>> chunks = [chunk1, chunk2, chunk3]
        >>> chunk_ids = await store.store_chunks(chunks, "article-123")
        >>> len(chunk_ids)
        3
        >>>
        >>> # Buscar similares
        >>> query_embedding = VectorEmbedding(...)
        >>> results = await store.search_similar(query_embedding, top_k=5)
        >>> len(results) <= 5
        True
        >>> results[0][1] >= results[1][1]  # Ordenados por score
        True
        >>>
        >>> # Obtener TLDRs
        >>> tldrs = await store.get_tldrs(["article-123", "article-456"])
        >>> len(tldrs) <= 2
        True
        >>>
        >>> # Eliminar chunks
        >>> await store.delete_chunks("article-123")
    """

    async def store_chunks(
        self,
        chunks: List[ContentChunk],
        source_id: str,
        source_type: str,
    ) -> List[str]:
        """
        Almacena chunks con embeddings en la base de datos vectorial.

        Persiste los chunks junto con sus embeddings, summaries y metadata
        en la tabla ai_content_chunks. Usa bulk inserts para eficiencia.
        Los chunks deben tener embeddings válidos antes de ser almacenados.

        Args:
            chunks: Lista de ContentChunk con embeddings generados
            source_id: ID del contenido fuente (article, feed, etc.)
            source_type: Tipo de contenido fuente (article, feed, etc.)

        Returns:
            Lista de IDs de chunks creados (en el mismo orden que los chunks)

        Raises:
            ValueError: Si la lista está vacía o algún chunk no tiene embedding
            ValueError: Si source_id o source_type están vacíos
            DatabaseException: Si el almacenamiento falla

        Examples:
            >>> chunks = [
            ...     ContentChunk(id=ChunkId(...), embedding=VectorEmbedding(...), ...),
            ...     ContentChunk(id=ChunkId(...), embedding=VectorEmbedding(...), ...),
            ... ]
            >>> chunk_ids = await store.store_chunks(
            ...     chunks,
            ...     source_id="article-123",
            ...     source_type="article"
            ... )
            >>> len(chunk_ids) == len(chunks)
            True
            >>> all(isinstance(cid, str) for cid in chunk_ids)
            True

        Notes:
            - Todos los chunks deben tener embeddings válidos (status >= EMBEDDED)
            - Los embeddings deben estar normalizados (magnitud = 1.0)
            - Usa bulk inserts para mejor performance (Requirements 11.3)
            - Los chunks se almacenan con su posición original en el contenido
            - Si el contenido ya tiene chunks, considerar eliminarlos primero

        Performance:
            - Bulk insert de 100 chunks: ~500ms
            - Usa transacciones para atomicidad
            - Los índices HNSW se actualizan automáticamente

        Validations:
            - Verifica que todos los chunks tengan embedding
            - Verifica que los embeddings estén normalizados
            - Verifica que source_id y source_type sean consistentes
            - Verifica que las posiciones sean únicas y ordenadas
        """
        ...

    async def search_similar(
        self,
        query_embedding: VectorEmbedding,
        top_k: int = 10,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Tuple[ContentChunk, float]]:
        """
        Busca chunks similares usando similitud coseno.

        Ejecuta búsqueda vectorial usando el operador de distancia coseno (<->)
        de pgvector. Retorna los top-k chunks más similares ordenados por score
        descendente. Opcionalmente aplica filtros adicionales (fecha, source, topics).

        Args:
            query_embedding: Embedding del query de búsqueda
            top_k: Número máximo de resultados a retornar (default: 10)
            filters: Filtros opcionales para refinar búsqueda
                - date_from: datetime - Filtrar chunks desde esta fecha
                - date_to: datetime - Filtrar chunks hasta esta fecha
                - source_urls: List[str] - Filtrar por URLs de fuentes
                - topics: List[str] - Filtrar por topics
                - source_ids: List[str] - Filtrar por IDs de contenido fuente
                - source_types: List[str] - Filtrar por tipos de contenido
                - min_similarity: float - Score mínimo de similitud (0-1)

        Returns:
            Lista de tuplas (ContentChunk, similarity_score) ordenadas por score
            descendente. El score está en rango [0, 1] donde 1 = idéntico.

        Raises:
            ValueError: Si top_k <= 0 o query_embedding es inválido
            ValueError: Si los filtros son inválidos
            DatabaseException: Si la búsqueda falla

        Examples:
            >>> query_embedding = VectorEmbedding(...)
            >>>
            >>> # Búsqueda simple
            >>> results = await store.search_similar(query_embedding, top_k=5)
            >>> len(results) <= 5
            True
            >>> results[0][1] >= results[1][1]  # Ordenados por score
            True
            >>>
            >>> # Búsqueda con filtros
            >>> from datetime import datetime, timedelta
            >>> filters = {
            ...     "date_from": datetime.now() - timedelta(days=7),
            ...     "topics": ["Bitcoin", "Ethereum"],
            ...     "source_types": ["article"],
            ...     "min_similarity": 0.7,
            ... }
            >>> results = await store.search_similar(
            ...     query_embedding,
            ...     top_k=10,
            ...     filters=filters
            ... )
            >>> all(score >= 0.7 for _, score in results)
            True

        Notes:
            - Usa índice HNSW para búsqueda eficiente (Requirements 4.3, 11.4)
            - Similitud coseno: 1 - (embedding <-> query_embedding)
            - Los chunks retornados incluyen embedding, summary y metadata
            - Si no hay resultados, retorna lista vacía
            - Los filtros se aplican DESPUÉS de la búsqueda vectorial

        Performance:
            - Búsqueda top-10 en 1M chunks: < 100ms (Requirements 11.4)
            - Usa índice HNSW con m=16, ef_construction=64
            - Filtros adicionales pueden aumentar latencia

        Query SQL (ejemplo):
            SELECT *, 1 - (embedding <-> query_vector) AS similarity
            FROM ai_content_chunks
            WHERE embedding IS NOT NULL
            ORDER BY embedding <-> query_vector
            LIMIT top_k;
        """
        ...

    async def get_tldrs(self, source_ids: List[str]) -> List[Dict[str, Any]]:
        """
        Obtiene TLDRs (resúmenes ultra-concisos) de contenido procesado.

        Recupera los TLDRs almacenados para los contenidos especificados.
        Los TLDRs son resúmenes de 3-5 bullets que capturan la información
        más importante del contenido.

        Args:
            source_ids: Lista de IDs de contenido fuente (articles, feeds, etc.)

        Returns:
            Lista de diccionarios con TLDRs:
            [
                {
                    "source_id": "article-123",
                    "source_type": "article",
                    "tldr": "- Bullet 1\n- Bullet 2\n- Bullet 3",
                    "bullet_count": 3,
                    "created_at": datetime(...),
                },
                ...
            ]

            Si un contenido no tiene TLDR, no aparece en la lista.

        Raises:
            ValueError: Si la lista de source_ids está vacía
            DatabaseException: Si la consulta falla

        Examples:
            >>> source_ids = ["article-123", "article-456", "article-789"]
            >>> tldrs = await store.get_tldrs(source_ids)
            >>> len(tldrs) <= len(source_ids)
            True
            >>>
            >>> # Verificar estructura
            >>> tldr = tldrs[0]
            >>> "source_id" in tldr
            True
            >>> "source_type" in tldr
            True
            >>> "tldr" in tldr
            True
            >>> "bullet_count" in tldr
            True
            >>> 3 <= tldr["bullet_count"] <= 5
            True

        Notes:
            - Solo retorna TLDRs de contenido que ha sido procesado completamente
            - Los TLDRs se almacenan en la tabla ai_processed_content
            - Si un contenido no tiene TLDR, no aparece en los resultados
            - Los TLDRs están formateados como bullets markdown
            - Útil para mostrar resúmenes rápidos en UI

        Performance:
            - Consulta simple con índice en source_id
            - Latencia: < 50ms para 100 contenidos

        Use Cases:
            - Mostrar resúmenes en lista de contenido
            - Generar newsletters con TLDRs
            - Proveer contexto rápido en RAG
        """
        ...

    async def delete_chunks(self, source_id: str) -> None:
        """
        Elimina todos los chunks de un contenido fuente.

        Elimina todos los chunks asociados a un contenido de la base de datos
        vectorial. Útil cuando un contenido es eliminado o necesita ser
        reprocesado desde cero.

        Args:
            source_id: ID del contenido fuente cuyos chunks se eliminarán

        Raises:
            ValueError: Si source_id está vacío
            DatabaseException: Si la eliminación falla

        Examples:
            >>> # Eliminar chunks de un artículo
            >>> await store.delete_chunks("article-123")
            >>>
            >>> # Verificar que se eliminaron
            >>> results = await store.search_similar(
            ...     query_embedding,
            ...     filters={"source_ids": ["article-123"]}
            ... )
            >>> len(results)
            0

        Notes:
            - Elimina TODOS los chunks del contenido (no es selectivo)
            - Usa transacción para atomicidad
            - Los índices HNSW se actualizan automáticamente
            - Si el contenido no tiene chunks, la operación es idempotente
            - Útil antes de reprocesar un contenido

        Performance:
            - Eliminación de 100 chunks: ~200ms
            - Usa índice en source_id para eficiencia

        Use Cases:
            - Eliminar contenido completo del sistema
            - Reprocesar contenido con nueva configuración
            - Limpiar chunks de contenido obsoleto
            - Rollback de procesamiento fallido

        SQL (ejemplo):
            DELETE FROM ai_content_chunks
            WHERE source_id = ?;
        """
        ...
