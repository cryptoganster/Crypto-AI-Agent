"""Tests para ChunkValidationService."""

from uuid import uuid4

import pytest

from src.chunking.domain.aggregates import ContentChunk
from src.chunking.domain.services.chunk_validation import ChunkValidationService
from src.chunking.domain.value_objects.chunk_id import ChunkId
from src.chunking.domain.value_objects.token_count import TokenCount
from src.knowledge.domain.value_objects.source_reference import SourceReference
from src.shared.config.chunking_config import ChunkingConfig


class TestChunkValidationService:
    """Tests para ChunkValidationService."""

    @pytest.fixture
    def service(self):
        """Fixture para ChunkValidationService."""
        return ChunkValidationService()

    @pytest.fixture
    def config(self):
        """Fixture para ChunkingConfig."""
        return ChunkingConfig(
            chunk_size=1400,
            chunk_overlap=150,
        )

    @pytest.fixture
    def valid_chunks(self):
        """Fixture para chunks válidos."""
        article_id = str(uuid4())
        source = SourceReference(
            source_type="rss_article",
            source_id=article_id,
            source_url="https://example.com/article",
        )

        return [
            ContentChunk(
                id=ChunkId.generate(),
                source=source,
                content="Chunk 0 content with sufficient length for validation",
                position=0,
                start_char=0,
                end_char=100,
                token_count=TokenCount(100),
            ),
            ContentChunk(
                id=ChunkId.generate(),
                source=source,
                content="Chunk 1 content with sufficient length for validation",
                position=1,
                start_char=80,
                end_char=180,
                token_count=TokenCount(100),
            ),
            ContentChunk(
                id=ChunkId.generate(),
                source=source,
                content="Chunk 2 content with sufficient length for validation",
                position=2,
                start_char=160,
                end_char=260,
                token_count=TokenCount(100),
            ),
        ]

    # Tests para validate_chunks_for_persistence

    def test_validate_chunks_for_persistence_with_valid_chunks_returns_no_errors(
        self, service, config, valid_chunks
    ):
        """Debería retornar lista vacía cuando chunks son válidos."""
        # Act
        errors = service.validate_chunks_for_persistence(valid_chunks, config)

        # Assert
        assert errors == []

    def test_validate_chunks_for_persistence_with_empty_list_returns_error(
        self, service, config
    ):
        """Debería retornar error cuando lista está vacía."""
        # Act
        errors = service.validate_chunks_for_persistence([], config)

        # Assert
        assert len(errors) == 1
        assert "vacía" in errors[0]

    def test_validate_chunks_for_persistence_with_too_few_tokens_returns_error(
        self, service, config
    ):
        """Debería retornar error cuando chunk tiene muy pocos tokens."""
        # Arrange
        source = SourceReference(
            source_type="rss_article",
            source_id=str(uuid4()),
            source_url="https://example.com/article",
        )
        chunk = ContentChunk(
            id=ChunkId.generate(),
            source=source,
            content="Short",
            position=0,
            start_char=0,
            end_char=5,
            token_count=TokenCount(10),  # Menos de 50
        )

        # Act
        errors = service.validate_chunks_for_persistence([chunk], config)

        # Assert
        assert len(errors) > 0
        assert any("muy pocos tokens" in error for error in errors)

    def test_validate_chunks_for_persistence_with_too_many_tokens_returns_error(
        self, service, config
    ):
        """Debería retornar error cuando chunk excede límite de tokens."""
        # Arrange
        source = SourceReference(
            source_type="rss_article",
            source_id=str(uuid4()),
            source_url="https://example.com/article",
        )
        chunk = ContentChunk(
            id=ChunkId.generate(),
            source=source,
            content="Very long content" * 100,
            position=0,
            start_char=0,
            end_char=1000,
            token_count=TokenCount(2000),  # Excede 1400 * 1.1 = 1540
        )

        # Act
        errors = service.validate_chunks_for_persistence([chunk], config)

        # Assert
        assert len(errors) > 0
        assert any("excede límite" in error for error in errors)

    def test_validate_chunks_for_persistence_with_empty_content_returns_error(
        self, service, config
    ):
        """Debería retornar error cuando chunk tiene contenido vacío."""
        # Note: ContentChunk aggregate ya valida esto en constructor.
        # Este test verifica que el aggregate protege sus invariantes.
        # El servicio de validación es una capa adicional de seguridad.

        # Arrange
        source = SourceReference(
            source_type="rss_article",
            source_id=str(uuid4()),
            source_url="https://example.com/article",
        )

        # Act & Assert
        # Verificar que el aggregate rechaza contenido vacío
        with pytest.raises(ValueError, match="content no puede estar vacío"):
            ContentChunk(
                id=ChunkId.generate(),
                source=source,
                content="",  # Vacío
                position=0,
                start_char=0,
                end_char=0,
                token_count=TokenCount(100),
            )

        # También verificar con solo espacios
        with pytest.raises(ValueError, match="content no puede estar vacío"):
            ContentChunk(
                id=ChunkId.generate(),
                source=source,
                content="   ",  # Solo espacios
                position=0,
                start_char=0,
                end_char=3,
                token_count=TokenCount(100),
            )

    def test_validate_chunks_for_persistence_with_invalid_positions_returns_error(
        self, service, config
    ):
        """Debería retornar error cuando start_char >= end_char."""
        # Note: ContentChunk aggregate ya valida esto en constructor.
        # Este test verifica que el aggregate protege sus invariantes.
        # El servicio de validación es una capa adicional de seguridad.

        # Arrange
        source = SourceReference(
            source_type="rss_article",
            source_id=str(uuid4()),
            source_url="https://example.com/article",
        )

        # Act & Assert
        # Verificar que el aggregate rechaza posiciones inválidas
        with pytest.raises(ValueError, match="end_char debe ser > start_char"):
            ContentChunk(
                id=ChunkId.generate(),
                source=source,
                content="Content",
                position=0,
                start_char=100,
                end_char=50,  # Inválido
                token_count=TokenCount(100),
            )

    def test_validate_chunks_for_persistence_with_duplicate_ids_returns_error(
        self, service, config
    ):
        """Debería retornar error cuando hay IDs duplicados."""
        # Arrange
        chunk_id = ChunkId.generate()
        article_id = str(uuid4())
        source = SourceReference(
            source_type="rss_article",
            source_id=article_id,
            source_url="https://example.com/article",
        )

        chunks = [
            ContentChunk(
                id=chunk_id,  # Mismo ID
                source=source,
                content="Chunk 1",
                position=0,
                start_char=0,
                end_char=100,
                token_count=TokenCount(100),
            ),
            ContentChunk(
                id=chunk_id,  # Mismo ID
                source=source,
                content="Chunk 2",
                position=1,
                start_char=80,
                end_char=180,
                token_count=TokenCount(100),
            ),
        ]

        # Act
        errors = service.validate_chunks_for_persistence(chunks, config)

        # Assert
        assert len(errors) > 0
        assert any("duplicados" in error for error in errors)

    def test_validate_chunks_for_persistence_with_inconsistent_article_ids_returns_error(
        self, service, config
    ):
        """Debería retornar error cuando sources son inconsistentes."""
        # Arrange
        source1 = SourceReference(
            source_type="rss_article",
            source_id=str(uuid4()),
            source_url="https://example.com/article1",
        )
        source2 = SourceReference(
            source_type="rss_article",
            source_id=str(uuid4()),
            source_url="https://example.com/article2",
        )

        chunks = [
            ContentChunk(
                id=ChunkId.generate(),
                source=source1,  # Diferente
                content="Chunk 1",
                position=0,
                start_char=0,
                end_char=100,
                token_count=TokenCount(100),
            ),
            ContentChunk(
                id=ChunkId.generate(),
                source=source2,  # Diferente
                content="Chunk 2",
                position=1,
                start_char=80,
                end_char=180,
                token_count=TokenCount(100),
            ),
        ]

        # Act
        errors = service.validate_chunks_for_persistence(chunks, config)

        # Assert
        assert len(errors) > 0
        assert any("inconsistentes" in error for error in errors)

    def test_validate_chunks_for_persistence_with_gaps_in_sequence_returns_error(
        self, service, config
    ):
        """Debería retornar error cuando hay gaps en secuencia."""
        # Arrange
        article_id = str(uuid4())
        source = SourceReference(
            source_type="rss_article",
            source_id=article_id,
            source_url="https://example.com/article",
        )

        chunks = [
            ContentChunk(
                id=ChunkId.generate(),
                source=source,
                content="Chunk 0",
                position=0,
                start_char=0,
                end_char=100,
                token_count=TokenCount(100),
            ),
            ContentChunk(
                id=ChunkId.generate(),
                source=source,
                content="Chunk 2",
                position=2,  # Gap: falta position=1
                start_char=80,
                end_char=180,
                token_count=TokenCount(100),
            ),
        ]

        # Act
        errors = service.validate_chunks_for_persistence(chunks, config)

        # Assert
        assert len(errors) > 0
        assert any("Secuencia de posiciones inválida" in error for error in errors)

    # Tests para filter_completed_chunks

    def test_filter_completed_chunks_removes_existing_chunks(
        self, service, valid_chunks
    ):
        """Debería filtrar chunks que ya existen."""
        # Arrange
        existing_ids = [str(valid_chunks[0].id), str(valid_chunks[1].id)]

        # Act
        filtered = service.filter_completed_chunks(valid_chunks, existing_ids)

        # Assert
        assert len(filtered) == 1
        assert filtered[0].id == valid_chunks[2].id

    def test_filter_completed_chunks_with_no_existing_returns_all(
        self, service, valid_chunks
    ):
        """Debería retornar todos los chunks cuando no hay existentes."""
        # Act
        filtered = service.filter_completed_chunks(valid_chunks, [])

        # Assert
        assert len(filtered) == len(valid_chunks)
        assert filtered == valid_chunks

    def test_filter_completed_chunks_with_all_existing_returns_empty(
        self, service, valid_chunks
    ):
        """Debería retornar lista vacía cuando todos existen."""
        # Arrange
        existing_ids = [str(chunk.id) for chunk in valid_chunks]

        # Act
        filtered = service.filter_completed_chunks(valid_chunks, existing_ids)

        # Assert
        assert len(filtered) == 0

    # Tests para validate_chunk_sequence

    def test_validate_chunk_sequence_with_valid_sequence_returns_true(
        self, service, valid_chunks
    ):
        """Debería retornar True cuando secuencia es válida."""
        # Act
        is_valid = service.validate_chunk_sequence(valid_chunks)

        # Assert
        assert is_valid is True

    def test_validate_chunk_sequence_with_empty_list_returns_true(self, service):
        """Debería retornar True cuando lista está vacía."""
        # Act
        is_valid = service.validate_chunk_sequence([])

        # Assert
        assert is_valid is True

    def test_validate_chunk_sequence_with_duplicate_positions_returns_false(
        self, service
    ):
        """Debería retornar False cuando hay posiciones duplicadas."""
        # Arrange
        article_id = str(uuid4())
        source = SourceReference(
            source_type="rss_article",
            source_id=article_id,
            source_url="https://example.com/article",
        )

        chunks = [
            ContentChunk(
                id=ChunkId.generate(),
                source=source,
                content="Chunk 0",
                position=0,
                start_char=0,
                end_char=100,
                token_count=TokenCount(100),
            ),
            ContentChunk(
                id=ChunkId.generate(),
                source=source,
                content="Chunk 0 duplicate",
                position=0,  # Duplicado
                start_char=80,
                end_char=180,
                token_count=TokenCount(100),
            ),
        ]

        # Act
        is_valid = service.validate_chunk_sequence(chunks)

        # Assert
        assert is_valid is False

    def test_validate_chunk_sequence_with_gaps_returns_false(self, service):
        """Debería retornar False cuando hay gaps en secuencia."""
        # Arrange
        article_id = str(uuid4())
        source = SourceReference(
            source_type="rss_article",
            source_id=article_id,
            source_url="https://example.com/article",
        )

        chunks = [
            ContentChunk(
                id=ChunkId.generate(),
                source=source,
                content="Chunk 0",
                position=0,
                start_char=0,
                end_char=100,
                token_count=TokenCount(100),
            ),
            ContentChunk(
                id=ChunkId.generate(),
                source=source,
                content="Chunk 2",
                position=2,  # Gap
                start_char=80,
                end_char=180,
                token_count=TokenCount(100),
            ),
        ]

        # Act
        is_valid = service.validate_chunk_sequence(chunks)

        # Assert
        assert is_valid is False

    # Tests para validate_chunk_overlap

    def test_validate_chunk_overlap_with_valid_overlap_returns_true(
        self, service, config, valid_chunks
    ):
        """Debería retornar True cuando overlap es válido."""
        # Act
        is_valid = service.validate_chunk_overlap(valid_chunks, config)

        # Assert
        assert is_valid is True

    def test_validate_chunk_overlap_with_single_chunk_returns_true(
        self, service, config
    ):
        """Debería retornar True cuando hay un solo chunk."""
        # Arrange
        source = SourceReference(
            source_type="rss_article",
            source_id=str(uuid4()),
            source_url="https://example.com/article",
        )
        chunk = ContentChunk(
            id=ChunkId.generate(),
            source=source,
            content="Single chunk",
            position=0,
            start_char=0,
            end_char=100,
            token_count=TokenCount(100),
        )

        # Act
        is_valid = service.validate_chunk_overlap([chunk], config)

        # Assert
        assert is_valid is True

    def test_validate_chunk_overlap_with_no_overlap_returns_false(
        self, service, config
    ):
        """Debería retornar False cuando no hay overlap."""
        # Arrange
        article_id = str(uuid4())
        source = SourceReference(
            source_type="rss_article",
            source_id=article_id,
            source_url="https://example.com/article",
        )

        chunks = [
            ContentChunk(
                id=ChunkId.generate(),
                source=source,
                content="Chunk 0",
                position=0,
                start_char=0,
                end_char=100,
                token_count=TokenCount(100),
            ),
            ContentChunk(
                id=ChunkId.generate(),
                source=source,
                content="Chunk 1",
                position=1,
                start_char=100,  # No overlap
                end_char=200,
                token_count=TokenCount(100),
            ),
        ]

        # Act
        is_valid = service.validate_chunk_overlap(chunks, config)

        # Assert
        assert is_valid is False

    def test_validate_chunk_overlap_with_negative_overlap_returns_false(
        self, service, config
    ):
        """Debería retornar False cuando overlap es negativo."""
        # Arrange
        article_id = str(uuid4())
        source = SourceReference(
            source_type="rss_article",
            source_id=article_id,
            source_url="https://example.com/article",
        )

        chunks = [
            ContentChunk(
                id=ChunkId.generate(),
                source=source,
                content="Chunk 0",
                position=0,
                start_char=0,
                end_char=100,
                token_count=TokenCount(100),
            ),
            ContentChunk(
                id=ChunkId.generate(),
                source=source,
                content="Chunk 1",
                position=1,
                start_char=150,  # Gap (overlap negativo)
                end_char=250,
                token_count=TokenCount(100),
            ),
        ]

        # Act
        is_valid = service.validate_chunk_overlap(chunks, config)

        # Assert
        assert is_valid is False
