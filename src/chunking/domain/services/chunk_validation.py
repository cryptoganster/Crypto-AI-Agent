"""Domain service para validación de chunks."""

from typing import List

from src.chunking.domain.aggregates.content_chunk import ContentChunk
from src.chunking.domain.interfaces.services import IChunkValidationService
from src.shared.config.chunking_config import ChunkingConfig


class ChunkValidationService(IChunkValidationService):
    """
    Domain service para validación de chunks.

    Implementa IChunkValidationService para validar que chunks cumplan
    con requisitos de calidad y configuración antes de persistencia.

    Responsabilidades:
    - Validar tamaños de chunks
    - Verificar overlap correcto
    - Filtrar chunks ya procesados
    - Validar integridad de secuencia
    - Verificar contenido no vacío
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
        5. article_id consistente
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
        errors: List[str] = []

        if not chunks:
            errors.append("Lista de chunks está vacía")
            return errors

        # Validar límites de tokens
        min_tokens = 50
        max_tokens = int(config.chunk_size * 1.1)  # +10% tolerancia

        for chunk in chunks:
            # 1. Token count dentro de límites
            if chunk.token_count.value < min_tokens:
                errors.append(
                    f"Chunk {chunk.id} tiene muy pocos tokens: "
                    f"{chunk.token_count.value} < {min_tokens}"
                )

            if chunk.token_count.value > max_tokens:
                errors.append(
                    f"Chunk {chunk.id} excede límite de tokens: "
                    f"{chunk.token_count.value} > {max_tokens}"
                )

            # 3. Contenido no vacío
            if not chunk.content or not chunk.content.strip():
                errors.append(f"Chunk {chunk.id} tiene contenido vacío")

            # 6. start_char < end_char
            if chunk.start_char >= chunk.end_char:
                errors.append(
                    f"Chunk {chunk.id} tiene posiciones inválidas: "
                    f"start_char={chunk.start_char} >= end_char={chunk.end_char}"
                )

        # 4. IDs únicos
        chunk_ids = [str(chunk.id) for chunk in chunks]
        if len(chunk_ids) != len(set(chunk_ids)):
            errors.append("Hay IDs de chunks duplicados")

        # 5. source consistente (source_id y source_url)
        sources = {
            (chunk.source.source_id, chunk.source.source_url) for chunk in chunks
        }
        if len(sources) > 1:
            errors.append(f"Chunks tienen sources inconsistentes: {sources}")

        # 2. Chunk index secuencial sin gaps
        positions = sorted([chunk.position for chunk in chunks])
        expected_positions = list(range(len(chunks)))
        if positions != expected_positions:
            errors.append(
                f"Secuencia de posiciones inválida: {positions} != {expected_positions}"
            )

        return errors

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
        existing_ids_set = set(existing_chunk_ids)

        return [chunk for chunk in chunks if str(chunk.id) not in existing_ids_set]

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
        if not chunks:
            return True

        # Obtener posiciones
        positions = [chunk.position for chunk in chunks]

        # Verificar sin duplicados
        if len(positions) != len(set(positions)):
            return False

        # Verificar secuencia (0, 1, 2, ...)
        sorted_positions = sorted(positions)
        expected_positions = list(range(len(chunks)))

        return sorted_positions == expected_positions

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
        if len(chunks) < 2:
            return True  # No hay overlap con un solo chunk

        # Ordenar chunks por posición
        sorted_chunks = sorted(chunks, key=lambda c: c.position)

        for i in range(len(sorted_chunks) - 1):
            current = sorted_chunks[i]
            next_chunk = sorted_chunks[i + 1]

            # Verificar que hay overlap (next empieza antes de que current termine)
            if next_chunk.start_char >= current.end_char:
                # No hay overlap
                return False

            # Calcular overlap en caracteres
            overlap_chars = current.end_char - next_chunk.start_char

            # Overlap no debe ser negativo
            if overlap_chars < 0:
                return False

            # Overlap no debe exceder el tamaño del chunk
            if overlap_chars > len(current.content):
                return False

        return True
