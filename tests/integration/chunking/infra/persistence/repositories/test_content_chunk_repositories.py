"""Integration tests para ContentChunk repositories."""

from datetime import datetime, timezone

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.chunking.domain.aggregates.content_chunk import ContentChunk
from src.chunking.domain.value_objects.chunk_id import ChunkId
from src.chunking.domain.value_objects.chunk_status import ChunkStatus
from src.chunking.domain.value_objects.chunk_summary import ChunkSummary
from src.chunking.domain.value_objects.token_count import TokenCount
from src.chunking.domain.value_objects.vector_embedding import VectorEmbedding
from src.chunking.infra.persistence.repositories.content_chunk_read_repository import (
    SqlAlchemyContentChunkReadRepository,
)
from src.chunking.infra.persistence.repositories.content_chunk_write_repository import (
    SqlAlchemyContentChunkWriteRepository,
)


@pytest.mark.integration
class TestContentChunkRepositories:
    """Integration tests para ContentChunk repositories."""

    @pytest.fixture
    def write_repository(self, db_session: AsyncSession):
        """Crea write repository con sesión de test."""
        return SqlAlchemyContentChunkWriteRepository(db_session)

    @pytest.fixture
    def read_repository(self, db_session: AsyncSession):
        """Crea read repository con sesión de test."""
        return SqlAlchemyContentChunkReadRepository(db_session)

    @pytest.fixture
    def sample_chunk(self) -> ContentChunk:
        """Crea ContentChunk de ejemplo."""
        now = datetime.now(timezone.utc)

        return ContentChunk(
            id=ChunkId("chunk-test-123"),
            article_id="art-test-456",
            content="This is a test chunk content for integration testing.",
            position=0,
            start_char=0,
            end_char=100,
            token_count=TokenCount(value=50, encoding="cl100k_base"),
            source_url="https://example.com/test-article",
            embedding=None,
            summary=None,
            status=ChunkStatus.PENDING,
            created_at=now,
            updated_at=now,
        )

    async def test_save_and_retrieve_chunk(
        self,
        write_repository,
        read_repository,
        sample_chunk,
        db_session,
    ):
        """Debería guardar y recuperar ContentChunk correctamente."""
        # Act - Save
        await write_repository.save(sample_chunk)
        await db_session.commit()

        # Act - Retrieve
        retrieved = await read_repository.find_by_id(str(sample_chunk.id))

        # Assert
        assert retrieved is not None
        assert str(retrieved.id) == str(sample_chunk.id)
        assert retrieved.article_id == sample_chunk.article_id
        assert retrieved.content == sample_chunk.content
        assert retrieved.position == sample_chunk.position
        assert retrieved.start_char == sample_chunk.start_char
        assert retrieved.end_char == sample_chunk.end_char
        assert retrieved.token_count.value == sample_chunk.token_count.value
        assert retrieved.source_url == sample_chunk.source_url
        assert retrieved.status == sample_chunk.status

    async def test_find_by_article_id_ordered_by_position(
        self,
        write_repository,
        read_repository,
        db_session,
    ):
        """Debería encontrar chunks por article_id ordenados por position."""
        # Arrange - Crear múltiples chunks en orden no secuencial
        now = datetime.now(timezone.utc)
        article_id = "art-multi-chunks"

        chunks = [
            ContentChunk(
                id=ChunkId(f"chunk-{i}"),
                article_id=article_id,
                content=f"Chunk {i} content",
                position=i,
                start_char=i * 100,
                end_char=(i + 1) * 100,
                token_count=TokenCount(value=50, encoding="cl100k_base"),
                source_url="https://example.com/article",
                status=ChunkStatus.PENDING,
                created_at=now,
                updated_at=now,
            )
            for i in [2, 0, 1]  # Orden no secuencial
        ]

        for chunk in chunks:
            await write_repository.save(chunk)
        await db_session.commit()

        # Act
        retrieved = await read_repository.find_by_article_id(article_id)

        # Assert
        assert len(retrieved) == 3
        # Verificar que están ordenados por position
        assert retrieved[0].position == 0
        assert retrieved[1].position == 1
        assert retrieved[2].position == 2

    async def test_find_by_status(
        self,
        write_repository,
        read_repository,
        db_session,
    ):
        """Debería encontrar chunks por estado."""
        # Arrange
        now = datetime.now(timezone.utc)

        pending_chunk = ContentChunk(
            id=ChunkId("chunk-pending"),
            article_id="art-status-test",
            content="Pending chunk",
            position=0,
            start_char=0,
            end_char=100,
            token_count=TokenCount(value=50, encoding="cl100k_base"),
            source_url="https://example.com/article",
            status=ChunkStatus.PENDING,
            created_at=now,
            updated_at=now,
        )

        embedded_chunk = ContentChunk(
            id=ChunkId("chunk-embedded"),
            article_id="art-status-test",
            content="Embedded chunk",
            position=1,
            start_char=100,
            end_char=200,
            token_count=TokenCount(value=50, encoding="cl100k_base"),
            source_url="https://example.com/article",
            embedding=VectorEmbedding(
                vector=[0.1] * 768,
                model="test-model",
                dimension=768,
            ),
            status=ChunkStatus.EMBEDDED,
            created_at=now,
            updated_at=now,
        )

        await write_repository.save(pending_chunk)
        await write_repository.save(embedded_chunk)
        await db_session.commit()

        # Act
        pending_chunks = await read_repository.find_by_status(ChunkStatus.PENDING)
        embedded_chunks = await read_repository.find_by_status(ChunkStatus.EMBEDDED)

        # Assert
        assert len(pending_chunks) >= 1
        assert len(embedded_chunks) >= 1
        assert all(c.status == ChunkStatus.PENDING for c in pending_chunks)
        assert all(c.status == ChunkStatus.EMBEDDED for c in embedded_chunks)

    async def test_update_chunk_with_embedding(
        self,
        write_repository,
        read_repository,
        sample_chunk,
        db_session,
    ):
        """Debería actualizar chunk agregando embedding."""
        # Arrange - Save initial
        await write_repository.save(sample_chunk)
        await db_session.commit()

        # Act - Add embedding
        embedding = VectorEmbedding(
            vector=[0.1, 0.2, 0.3] + [0.0] * 765,
            model="nomic-embed-text-v1.5",
            dimension=768,
        )
        sample_chunk.embed(embedding)

        await write_repository.save(sample_chunk)
        await db_session.commit()

        # Assert
        retrieved = await read_repository.find_by_id(str(sample_chunk.id))
        assert retrieved is not None
        assert retrieved.status == ChunkStatus.EMBEDDED
        assert retrieved.embedding is not None
        assert retrieved.embedding.dimension == 768
        assert retrieved.embedding.model == "nomic-embed-text-v1.5"

    async def test_update_chunk_with_summary(
        self,
        write_repository,
        read_repository,
        db_session,
    ):
        """Debería actualizar chunk agregando summary."""
        # Arrange - Create chunk with embedding
        now = datetime.now(timezone.utc)

        embedding = VectorEmbedding(
            vector=[0.1] * 768,
            model="test-model",
            dimension=768,
        )

        chunk = ContentChunk(
            id=ChunkId("chunk-summary-test"),
            article_id="art-summary",
            content="Test content for summary",
            position=0,
            start_char=0,
            end_char=100,
            token_count=TokenCount(value=50, encoding="cl100k_base"),
            source_url="https://example.com/article",
            embedding=embedding,
            status=ChunkStatus.EMBEDDED,
            created_at=now,
            updated_at=now,
        )

        await write_repository.save(chunk)
        await db_session.commit()

        # Act - Add summary
        summary = ChunkSummary(
            text="This is a test summary. It has three sentences. Here is the third.",
            sentence_count=3,
        )
        chunk.summarize(summary)

        await write_repository.save(chunk)
        await db_session.commit()

        # Assert
        retrieved = await read_repository.find_by_id(str(chunk.id))
        assert retrieved is not None
        assert retrieved.status == ChunkStatus.SUMMARIZED
        assert retrieved.summary is not None
        assert retrieved.summary.sentence_count == 3

    async def test_update_chunk_to_completed(
        self,
        write_repository,
        read_repository,
        db_session,
    ):
        """Debería actualizar chunk a estado COMPLETED."""
        # Arrange - Create chunk with embedding and summary
        now = datetime.now(timezone.utc)

        embedding = VectorEmbedding(
            vector=[0.1] * 768,
            model="test-model",
            dimension=768,
        )

        summary = ChunkSummary(
            text="Summary text. Second sentence. Third sentence.",
            sentence_count=3,
        )

        chunk = ContentChunk(
            id=ChunkId("chunk-complete-test"),
            article_id="art-complete",
            content="Test content",
            position=0,
            start_char=0,
            end_char=100,
            token_count=TokenCount(value=50, encoding="cl100k_base"),
            source_url="https://example.com/article",
            embedding=embedding,
            summary=summary,
            status=ChunkStatus.SUMMARIZED,
            created_at=now,
            updated_at=now,
        )

        await write_repository.save(chunk)
        await db_session.commit()

        # Act - Mark as completed
        chunk.mark_as_completed()

        await write_repository.save(chunk)
        await db_session.commit()

        # Assert
        retrieved = await read_repository.find_by_id(str(chunk.id))
        assert retrieved is not None
        assert retrieved.status == ChunkStatus.COMPLETED
        assert retrieved.is_completed() is True

    async def test_delete_chunk(
        self,
        write_repository,
        read_repository,
        sample_chunk,
        db_session,
    ):
        """Debería eliminar chunk correctamente."""
        # Arrange
        await write_repository.save(sample_chunk)
        await db_session.commit()

        # Act
        await write_repository.delete(str(sample_chunk.id))
        await db_session.commit()

        # Assert
        retrieved = await read_repository.find_by_id(str(sample_chunk.id))
        assert retrieved is None

    async def test_delete_by_article_id(
        self,
        write_repository,
        read_repository,
        db_session,
    ):
        """Debería eliminar todos los chunks de un artículo."""
        # Arrange
        now = datetime.now(timezone.utc)
        article_id = "art-delete-all"

        chunks = [
            ContentChunk(
                id=ChunkId(f"chunk-del-{i}"),
                article_id=article_id,
                content=f"Chunk {i}",
                position=i,
                start_char=i * 100,
                end_char=(i + 1) * 100,
                token_count=TokenCount(value=50, encoding="cl100k_base"),
                source_url="https://example.com/article",
                status=ChunkStatus.PENDING,
                created_at=now,
                updated_at=now,
            )
            for i in range(3)
        ]

        for chunk in chunks:
            await write_repository.save(chunk)
        await db_session.commit()

        # Act
        await write_repository.delete_by_article_id(article_id)
        await db_session.commit()

        # Assert
        retrieved = await read_repository.find_by_article_id(article_id)
        assert len(retrieved) == 0

    async def test_exists_returns_true_when_exists(
        self,
        write_repository,
        read_repository,
        sample_chunk,
        db_session,
    ):
        """Debería retornar True cuando chunk existe."""
        # Arrange
        await write_repository.save(sample_chunk)
        await db_session.commit()

        # Act
        exists = await read_repository.exists(str(sample_chunk.id))

        # Assert
        assert exists is True

    async def test_exists_returns_false_when_not_exists(
        self,
        read_repository,
    ):
        """Debería retornar False cuando chunk no existe."""
        # Act
        exists = await read_repository.exists("non-existent-id")

        # Assert
        assert exists is False

    async def test_count_by_article_id(
        self,
        write_repository,
        read_repository,
        db_session,
    ):
        """Debería contar chunks por article_id."""
        # Arrange
        now = datetime.now(timezone.utc)
        article_id = "art-count-test"

        chunks = [
            ContentChunk(
                id=ChunkId(f"chunk-count-{i}"),
                article_id=article_id,
                content=f"Chunk {i}",
                position=i,
                start_char=i * 100,
                end_char=(i + 1) * 100,
                token_count=TokenCount(value=50, encoding="cl100k_base"),
                source_url="https://example.com/article",
                status=ChunkStatus.PENDING,
                created_at=now,
                updated_at=now,
            )
            for i in range(5)
        ]

        for chunk in chunks:
            await write_repository.save(chunk)
        await db_session.commit()

        # Act
        count = await read_repository.count_by_article_id(article_id)

        # Assert
        assert count == 5

    async def test_count_by_status(
        self,
        write_repository,
        read_repository,
        db_session,
    ):
        """Debería contar chunks por estado."""
        # Arrange
        now = datetime.now(timezone.utc)

        # Crear chunks con diferentes estados
        for i, status in enumerate(
            [ChunkStatus.PENDING, ChunkStatus.PENDING, ChunkStatus.EMBEDDED]
        ):
            chunk = ContentChunk(
                id=ChunkId(f"chunk-status-count-{i}"),
                article_id=f"art-{i}",
                content=f"Chunk {i}",
                position=0,
                start_char=0,
                end_char=100,
                token_count=TokenCount(value=50, encoding="cl100k_base"),
                source_url="https://example.com/article",
                status=status,
                created_at=now,
                updated_at=now,
            )
            await write_repository.save(chunk)

        await db_session.commit()

        # Act
        pending_count = await read_repository.count_by_status(ChunkStatus.PENDING)
        embedded_count = await read_repository.count_by_status(ChunkStatus.EMBEDDED)

        # Assert
        assert pending_count >= 2
        assert embedded_count >= 1

    async def test_find_by_article_id_with_pagination(
        self,
        write_repository,
        read_repository,
        db_session,
    ):
        """Debería paginar resultados correctamente."""
        # Arrange
        now = datetime.now(timezone.utc)
        article_id = "art-pagination"

        chunks = [
            ContentChunk(
                id=ChunkId(f"chunk-page-{i}"),
                article_id=article_id,
                content=f"Chunk {i}",
                position=i,
                start_char=i * 100,
                end_char=(i + 1) * 100,
                token_count=TokenCount(value=50, encoding="cl100k_base"),
                source_url="https://example.com/article",
                status=ChunkStatus.PENDING,
                created_at=now,
                updated_at=now,
            )
            for i in range(10)
        ]

        for chunk in chunks:
            await write_repository.save(chunk)
        await db_session.commit()

        # Act - Primera página
        page1 = await read_repository.find_by_article_id(article_id, limit=3, offset=0)

        # Act - Segunda página
        page2 = await read_repository.find_by_article_id(article_id, limit=3, offset=3)

        # Assert
        assert len(page1) == 3
        assert len(page2) == 3
        assert page1[0].position == 0
        assert page1[1].position == 1
        assert page1[2].position == 2
        assert page2[0].position == 3
        assert page2[1].position == 4
        assert page2[2].position == 5
