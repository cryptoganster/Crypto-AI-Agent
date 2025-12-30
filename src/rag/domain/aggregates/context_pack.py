"""ContextPack aggregate root para RAG context assembly."""

from datetime import datetime, timezone
from typing import List, Optional

from src.chunking.domain.exceptions import (
    ChunkRelevanceOrderException,
    ContextPackFullException,
)
from src.chunking.domain.value_objects import ChunkId, VectorEmbedding
from src.rag.domain.value_objects import ContextPackId
from src.shared.kernel.aggregate_root import IAggregateRoot
from src.shared.kernel.domain_event import IDomainEvent


class ContextPack(IAggregateRoot[ContextPackId]):
    """
    Aggregate root para context pack de RAG.

    Representa un conjunto de chunks y summaries recuperados
    para generación de contenido. Es efímero y puede ser
    recreado en cualquier momento.

    Responsabilidades:
    - Mantener referencias a chunks relevantes
    - Trackear tokens totales para no exceder límite
    - Mantener orden por relevancia descendente
    - Trackear fuentes únicas de contenido

    Invariantes:
    - total_tokens <= max_tokens
    - relevance_scores en orden descendente
    - chunk_ids y relevance_scores tienen misma longitud
    - sources no tiene duplicados

    Attributes:
        id: Identificador único del context pack
        query: Query original que generó este pack
        query_embedding: Embedding del query
        chunk_ids: Lista de IDs de chunks incluidos
        total_tokens: Total de tokens en el pack
        relevance_scores: Scores de relevancia de cada chunk
        sources: URLs únicas de artículos fuente
        max_tokens: Límite máximo de tokens
        created_at: Timestamp de creación

    Examples:
        >>> pack = ContextPack.create(
        ...     query="Bitcoin ETF regulation",
        ...     query_embedding=embedding,
        ...     max_tokens=4000
        ... )
        >>> pack.add_chunk(
        ...     chunk_id=ChunkId.generate(),
        ...     token_count=500,
        ...     relevance_score=0.95,
        ...     source_url="https://example.com/article1"
        ... )
        >>> pack.is_full()
        False
        >>> pack.total_tokens
        500
    """

    def __init__(
        self,
        id: ContextPackId,
        query: str,
        query_embedding: VectorEmbedding,
        max_tokens: int = 4000,
        chunk_ids: Optional[List[ChunkId]] = None,
        total_tokens: int = 0,
        relevance_scores: Optional[List[float]] = None,
        sources: Optional[List[str]] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
    ):
        """
        Inicializa ContextPack aggregate.

        Args:
            id: Identificador único del context pack
            query: Query original que generó este pack
            query_embedding: Embedding del query
            max_tokens: Límite máximo de tokens (default: 4000)
            chunk_ids: Lista de IDs de chunks incluidos
            total_tokens: Total de tokens en el pack
            relevance_scores: Scores de relevancia de cada chunk
            sources: URLs únicas de artículos fuente
            created_at: Timestamp de creación
            updated_at: Timestamp de última actualización
        """
        super().__init__()

        self._id = id
        self._query = query
        self._query_embedding = query_embedding
        self._max_tokens = max_tokens
        self._chunk_ids = chunk_ids or []
        self._total_tokens = total_tokens
        self._relevance_scores = relevance_scores or []
        self._sources = sources or []
        self._created_at = created_at or datetime.now(timezone.utc)
        self._updated_at = updated_at or datetime.now(timezone.utc)

        # Validar invariantes iniciales
        if self._max_tokens <= 0:
            raise ValueError("max_tokens debe ser mayor a 0")

        if not self._query or not self._query.strip():
            raise ValueError("query no puede estar vacío")

        if self._total_tokens < 0:
            raise ValueError("total_tokens no puede ser negativo")

        if self._total_tokens > self._max_tokens:
            raise ValueError(
                f"total_tokens ({self._total_tokens}) excede max_tokens ({self._max_tokens})"
            )

        # Validar consistencia de listas
        if len(self._chunk_ids) != len(self._relevance_scores):
            raise ValueError(
                "chunk_ids y relevance_scores deben tener la misma longitud"
            )

    @property
    def id(self) -> ContextPackId:
        """ID único del context pack."""
        return self._id

    @property
    def query(self) -> str:
        """Query original."""
        return self._query

    @property
    def query_embedding(self) -> VectorEmbedding:
        """Embedding del query."""
        return self._query_embedding

    @property
    def max_tokens(self) -> int:
        """Límite máximo de tokens."""
        return self._max_tokens

    @property
    def chunk_ids(self) -> List[ChunkId]:
        """Lista de IDs de chunks incluidos."""
        return self._chunk_ids

    @property
    def total_tokens(self) -> int:
        """Total de tokens en el pack."""
        return self._total_tokens

    @property
    def relevance_scores(self) -> List[float]:
        """Scores de relevancia de cada chunk."""
        return self._relevance_scores

    @property
    def sources(self) -> List[str]:
        """URLs únicas de artículos fuente."""
        return self._sources

    @property
    def created_at(self) -> datetime:
        """Timestamp de creación."""
        return self._created_at

    @property
    def updated_at(self) -> datetime:
        """Timestamp de última actualización."""
        return self._updated_at

    @classmethod
    def create(
        cls,
        query: str,
        query_embedding: VectorEmbedding,
        max_tokens: int = 4000,
        context_pack_id: Optional[ContextPackId] = None,
    ) -> "ContextPack":
        """
        Factory method para crear un nuevo ContextPack.

        Args:
            query: Query original
            query_embedding: Embedding del query
            max_tokens: Límite máximo de tokens (default: 4000)
            context_pack_id: ID opcional (se genera si no se provee)

        Returns:
            ContextPack nuevo y vacío

        Raises:
            ValueError: Si los parámetros son inválidos

        Examples:
            >>> pack = ContextPack.create(
            ...     query="Bitcoin regulation",
            ...     query_embedding=embedding,
            ...     max_tokens=4000
            ... )
            >>> pack.total_tokens
            0
            >>> len(pack.chunk_ids)
            0
        """
        pack_id = context_pack_id or ContextPackId.generate()

        return cls(
            id=pack_id,
            query=query,
            query_embedding=query_embedding,
            max_tokens=max_tokens,
        )

    def add_chunk(
        self,
        chunk_id: ChunkId,
        token_count: int,
        relevance_score: float,
        source_url: str,
    ) -> None:
        """
        Agrega chunk al context pack.

        Invariantes:
        - No exceder max_tokens
        - Relevance scores ordenados descendentemente
        - Token count debe ser positivo
        - Relevance score debe estar en [0.0, 1.0]

        Args:
            chunk_id: ID del chunk a agregar
            token_count: Número de tokens del chunk
            relevance_score: Score de relevancia [0.0, 1.0]
            source_url: URL del artículo fuente

        Raises:
            ContextPackFullException: Si agregar el chunk excedería max_tokens
            ChunkRelevanceOrderException: Si el score no está en orden descendente
            ValueError: Si los parámetros son inválidos

        Examples:
            >>> pack = ContextPack.create("query", embedding, max_tokens=1000)
            >>> pack.add_chunk(
            ...     chunk_id=ChunkId.generate(),
            ...     token_count=500,
            ...     relevance_score=0.95,
            ...     source_url="https://example.com/article"
            ... )
            >>> pack.total_tokens
            500
            >>> len(pack.chunk_ids)
            1
        """
        # Validar parámetros
        if token_count <= 0:
            raise ValueError(f"token_count debe ser positivo, recibido: {token_count}")

        if not (0.0 <= relevance_score <= 1.0):
            raise ValueError(
                f"relevance_score debe estar en [0.0, 1.0], recibido: {relevance_score}"
            )

        if not source_url or not source_url.startswith(("http://", "https://")):
            raise ValueError(f"source_url inválida: {source_url}")

        # Invariante: No exceder max_tokens
        if self._total_tokens + token_count > self._max_tokens:
            raise ContextPackFullException(
                current_tokens=self._total_tokens,
                max_tokens=self._max_tokens,
                attempted_tokens=token_count,
            )

        # Invariante: Mantener orden por relevancia descendente
        if self._relevance_scores and relevance_score > self._relevance_scores[-1]:
            raise ChunkRelevanceOrderException(
                new_score=relevance_score,
                last_score=self._relevance_scores[-1],
            )

        # Agregar chunk
        self._chunk_ids.append(chunk_id)
        self._relevance_scores.append(relevance_score)
        self._total_tokens += token_count
        self._updated_at = datetime.now(timezone.utc)

        # Agregar source si es nueva
        if source_url not in self._sources:
            self._sources.append(source_url)

    def is_full(self) -> bool:
        """
        Verifica si el context pack está lleno.

        Un pack está lleno cuando alcanzó o excedió su max_tokens.

        Returns:
            True si total_tokens >= max_tokens, False en caso contrario

        Examples:
            >>> pack = ContextPack.create("query", embedding, max_tokens=1000)
            >>> pack.is_full()
            False
            >>> pack.add_chunk(ChunkId.generate(), 1000, 0.9, "https://example.com")
            >>> pack.is_full()
            True
        """
        return self._total_tokens >= self._max_tokens

    def get_remaining_tokens(self) -> int:
        """
        Calcula tokens restantes disponibles.

        Returns:
            Número de tokens que aún pueden agregarse

        Examples:
            >>> pack = ContextPack.create("query", embedding, max_tokens=1000)
            >>> pack.get_remaining_tokens()
            1000
            >>> pack.add_chunk(ChunkId.generate(), 300, 0.9, "https://example.com")
            >>> pack.get_remaining_tokens()
            700
        """
        return max(0, self._max_tokens - self._total_tokens)

    def get_chunk_count(self) -> int:
        """
        Obtiene el número de chunks en el pack.

        Returns:
            Cantidad de chunks agregados

        Examples:
            >>> pack = ContextPack.create("query", embedding)
            >>> pack.get_chunk_count()
            0
            >>> pack.add_chunk(ChunkId.generate(), 100, 0.9, "https://example.com")
            >>> pack.get_chunk_count()
            1
        """
        return len(self._chunk_ids)

    def get_source_count(self) -> int:
        """
        Obtiene el número de fuentes únicas.

        Returns:
            Cantidad de URLs únicas de artículos fuente

        Examples:
            >>> pack = ContextPack.create("query", embedding)
            >>> pack.add_chunk(ChunkId.generate(), 100, 0.9, "https://example.com/1")
            >>> pack.add_chunk(ChunkId.generate(), 100, 0.8, "https://example.com/1")
            >>> pack.get_source_count()
            1
            >>> pack.add_chunk(ChunkId.generate(), 100, 0.7, "https://example.com/2")
            >>> pack.get_source_count()
            2
        """
        return len(self._sources)

    def get_average_relevance(self) -> float:
        """
        Calcula el score promedio de relevancia.

        Returns:
            Promedio de relevance_scores, 0.0 si no hay chunks

        Examples:
            >>> pack = ContextPack.create("query", embedding)
            >>> pack.get_average_relevance()
            0.0
            >>> pack.add_chunk(ChunkId.generate(), 100, 0.9, "https://example.com")
            >>> pack.add_chunk(ChunkId.generate(), 100, 0.7, "https://example.com")
            >>> pack.get_average_relevance()
            0.8
        """
        if not self._relevance_scores:
            return 0.0
        return sum(self._relevance_scores) / len(self._relevance_scores)
