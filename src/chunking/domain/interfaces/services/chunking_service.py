"""Interface para servicio de chunking de contenido."""

from typing import List, Protocol

from src.chunking.domain.aggregates.content_chunk import ContentChunk
from src.knowledge.domain.value_objects.source_reference import SourceReference
from src.shared.config.chunking_config import ChunkingConfig


class IChunkingService(Protocol):
    """
    Interface para servicio de chunking de contenido.

    Responsabilidad: Dividir contenido de artículos en chunks semánticos
    con overlap para preservar contexto.

    Implementaciones deben:
    - Respetar límites de tokens configurados
    - Aplicar overlap entre chunks
    - Usar separadores jerárquicos
    - Preservar contexto semántico
    - Generar IDs únicos para chunks
    """

    def chunk_text(
        self,
        text: str,
        source_ref: SourceReference,
        config: ChunkingConfig,
    ) -> List[ContentChunk]:
        """
        Divide texto en chunks semánticos.

        Estrategia:
        1. Dividir por separadores jerárquicos (párrafos, oraciones, palabras)
        2. Respetar chunk_size_tokens (1200-1500 tokens)
        3. Aplicar chunk_overlap_tokens (150 tokens)
        4. Generar chunk_id único por chunk
        5. Asignar chunk_index secuencial
        6. Calcular token_count por chunk

        Args:
            text: Contenido a dividir (markdown o plaintext)
            source_ref: Referencia al contenido fuente (article, feed, etc.)
            config: Configuración de chunking (tamaños, overlap, separadores)

        Returns:
            Lista de ContentChunk con:
            - chunk_id: UUID único
            - source_reference: Referencia al contenido fuente
            - chunk_index: Posición en secuencia (0-based)
            - content: Texto del chunk
            - token_count: Número de tokens
            - start_char: Posición inicial en texto original
            - end_char: Posición final en texto original

        Raises:
            ValueError: Si text está vacío o config es inválido

        Example:
            >>> service = ChunkingService()
            >>> config = ChunkingConfig(
            ...     chunk_size_tokens=1200,
            ...     chunk_overlap_tokens=150,
            ...     separators=["\\n\\n", "\\n", ". ", " "]
            ... )
            >>> source_ref = SourceReference(
            ...     source_id="art-123",
            ...     source_type=SourceType.ARTICLE
            ... )
            >>> chunks = service.chunk_text(
            ...     text="Long article content...",
            ...     source_ref=source_ref,
            ...     config=config
            ... )
            >>> len(chunks)
            5
            >>> chunks[0].chunk_index
            0
            >>> chunks[0].token_count
            1200
        """
        ...
