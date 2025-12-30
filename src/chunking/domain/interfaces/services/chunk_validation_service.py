"""Interface para servicio de validación de chunks."""

from typing import List, Protocol

from src.chunking.domain.aggregates.content_chunk import ContentChunk
from src.knowledge.domain.value_objects.source_reference import SourceReference
from src.shared.config.chunking_config import ChunkingConfig


class IChunkValidationService(Protocol):
    """
    Interface para servicio de validación de chunks.

    Responsabilidad: Validar que chunks cumplan con requisitos de calidad
    y configuración antes de persistencia o procesamiento.

    Implementaciones deben:
    - Validar tamaños de chunks
    - Verificar overlap correcto
    - Filtrar chunks ya procesados
    - Validar integridad de secuencia
    - Verificar contenido no vacío
    - Validar SourceReference consistente
    """

    def validate_chunks_for_persistence(
        self,
        chunks: List[ContentChunk],
        config: ChunkingConfig,
    ) -> List[str]:
        """
        Valida chunks antes de persistencia.

        Validaciones:
        1. Token count dentro de límites (min: 50, max: chunk_size + 10%)
        2. Chunk index secuencial sin gaps
        3. Contenido no vacío
        4. IDs únicos
        5. SourceReference consistente (mismo source_id y source_type)
        6. start_char < end_char

        Args:
            chunks: Lista de chunks a validar
            config: Configuración de chunking para límites

        Returns:
            Lista de errores de validación (vacía si todo OK)

        Example:
            >>> service = ChunkValidationService()
            >>> errors = service.validate_chunks_for_persistence(chunks, config)
            >>> if errors:
            ...     print(f"Validación falló: {errors}")
            >>> else:
            ...     print("Chunks válidos para persistir")
        """
        ...

    def filter_completed_chunks(
        self,
        chunks: List[ContentChunk],
        existing_chunk_ids: List[str],
    ) -> List[ContentChunk]:
        """
        Filtra chunks que ya fueron procesados.

        Útil para:
        - Evitar reprocesamiento de chunks
        - Reanudar procesamiento interrumpido
        - Procesamiento incremental

        Args:
            chunks: Lista de chunks a filtrar
            existing_chunk_ids: IDs de chunks ya procesados

        Returns:
            Lista de chunks que NO están en existing_chunk_ids

        Example:
            >>> service = ChunkValidationService()
            >>> existing = ["chunk-1", "chunk-2"]
            >>> new_chunks = service.filter_completed_chunks(
            ...     chunks=all_chunks,
            ...     existing_chunk_ids=existing
            ... )
            >>> # Solo retorna chunks con IDs no en existing
        """
        ...

    def validate_chunk_sequence(
        self,
        chunks: List[ContentChunk],
    ) -> bool:
        """
        Valida que secuencia de chunks sea correcta.

        Verifica:
        - Índices secuenciales (0, 1, 2, ...)
        - Sin gaps en secuencia
        - Sin duplicados de índice
        - Ordenamiento correcto

        Args:
            chunks: Lista de chunks a validar

        Returns:
            True si secuencia es válida, False si hay problemas

        Example:
            >>> service = ChunkValidationService()
            >>> is_valid = service.validate_chunk_sequence(chunks)
            >>> if not is_valid:
            ...     raise ValueError("Secuencia de chunks inválida")
        """
        ...

    def validate_chunk_overlap(
        self,
        chunks: List[ContentChunk],
        config: ChunkingConfig,
    ) -> bool:
        """
        Valida que overlap entre chunks sea correcto.

        Verifica:
        - Overlap aproximado al configurado
        - Contenido compartido entre chunks consecutivos
        - Overlap no excede chunk_size

        Args:
            chunks: Lista de chunks a validar
            config: Configuración con chunk_overlap_tokens

        Returns:
            True si overlap es correcto, False si hay problemas

        Example:
            >>> service = ChunkValidationService()
            >>> has_valid_overlap = service.validate_chunk_overlap(
            ...     chunks=chunks,
            ...     config=config
            ... )
        """
        ...
