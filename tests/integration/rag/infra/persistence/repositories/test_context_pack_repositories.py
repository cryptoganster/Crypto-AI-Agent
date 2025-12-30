"""
Tests de integración para ContextPack repositories.

Verifica persistencia y recuperación de ContextPacks en base de datos real.
"""

from datetime import datetime, timezone

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.rag.domain.aggregates.context_pack import ContextPack
from src.rag.domain.value_objects.context_chunk import ContextChunk
from src.rag.domain.value_objects.context_pack_id import ContextPackId
from src.rag.infra.persistence.repositories.context_pack_read_repository import (
    SqlAlchemyContextPackReadRepository,
)
from src.rag.infra.persistence.repositories.context_pack_write_repository import (
    SqlAlchemyContextPackWriteRepository,
)


@pytest.mark.integration
class TestContextPackRepositories:
    """Tests de integración para repositorios de ContextPack."""

    @pytest.fixture
    def write_repository(self, db_session: AsyncSession):
        """Crea write repository con sesión de test."""
        return SqlAlchemyContextPackWriteRepository(db_session)

    @pytest.fixture
    def read_repository(self, db_session: AsyncSession):
        """Crea read repository con sesión de test."""
        return SqlAlchemyContextPackReadRepository(db_session)

    @pytest.fixture
    def sample_chunks(self) -> list[ContextChunk]:
        """Crea chunks de ejemplo."""
        return [
            ContextChunk(
                chunk_id="chunk-1",
                content="First chunk content for testing",
                position=0,
                relevance_score=0.95,
                token_count=50,
            ),
            ContextChunk(
                chunk_id="chunk-2",
                content="Second chunk content for testing",
                position=1,
                relevance_score=0.85,
                token_count=45,
            ),
            ContextChunk(
                chunk_id="chunk-3",
                content="Third chunk content for testing",
                position=2,
                relevance_score=0.75,
                token_count=40,
            ),
        ]

    @pytest.fixture
    def sample_context_pack(self, sample_chunks) -> ContextPack:
        """Crea ContextPack de ejemplo."""
        return ContextPack(
            id=ContextPackId.generate(),
            article_id="article-test-123",
            query="test query for integration",
            chunks=sample_chunks,
            created_at=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            metadata={"test": True, "source": "integration_test"},
        )

    async def test_save_and_find_by_id(
        self,
        write_repository,
        read_repository,
        sample_context_pack,
    ):
        """Debería guardar y recuperar ContextPack por ID."""
        # Act - Guardar
        await write_repository.save(sample_context_pack)

        # Act - Recuperar
        found = await read_repository.find_by_id(sample_context_pack.id)

        # Assert
        assert found is not None
        assert str(found.id) == str(sample_context_pack.id)
        assert found.article_id == sample_context_pack.article_id
        assert found.query == sample_context_pack.query
        assert found.total_chunks == 3
        assert found.total_tokens == 135
        assert len(found.chunks) == 3

    async def test_save_preserves_chunks_order(
        self,
        write_repository,
        read_repository,
        sample_context_pack,
    ):
        """Debería preservar orden de chunks."""
        # Act
        await write_repository.save(sample_context_pack)
        found = await read_repository.find_by_id(sample_context_pack.id)

        # Assert
        assert found is not None
        assert found.chunks[0].chunk_id == "chunk-1"
        assert found.chunks[0].position == 0
        assert found.chunks[1].chunk_id == "chunk-2"
        assert found.chunks[1].position == 1
        assert found.chunks[2].chunk_id == "chunk-3"
        assert found.chunks[2].position == 2

    async def test_save_preserves_metadata(
        self,
        write_repository,
        read_repository,
        sample_context_pack,
    ):
        """Debería preservar metadata."""
        # Act
        await write_repository.save(sample_context_pack)
        found = await read_repository.find_by_id(sample_context_pack.id)

        # Assert
        assert found is not None
        assert found.metadata == {"test": True, "source": "integration_test"}

    async def test_update_existing_context_pack(
        self,
        write_repository,
        read_repository,
        sample_context_pack,
        sample_chunks,
    ):
        """Debería actualizar ContextPack existente."""
        # Arrange - Guardar original
        await write_repository.save(sample_context_pack)

        # Modificar
        updated_pack = ContextPack(
            id=sample_context_pack.id,
            article_id=sample_context_pack.article_id,
            query="updated query",
            chunks=sample_chunks[:2],  # Solo 2 chunks
            created_at=sample_context_pack.created_at,
            metadata={"updated": True},
        )

        # Act - Actualizar
        await write_repository.save(updated_pack)
        found = await read_repository.find_by_id(sample_context_pack.id)

        # Assert
        assert found is not None
        assert found.query == "updated query"
        assert found.total_chunks == 2
        assert found.total_tokens == 95
        assert len(found.chunks) == 2
        assert found.metadata == {"updated": True}

    async def test_find_by_id_returns_none_when_not_found(
        self,
        read_repository,
    ):
        """Debería retornar None cuando no existe."""
        # Act
        found = await read_repository.find_by_id(ContextPackId("non-existent-id"))

        # Assert
        assert found is None

    async def test_find_by_article_id(
        self,
        write_repository,
        read_repository,
        sample_chunks,
    ):
        """Debería encontrar ContextPacks por article_id."""
        # Arrange - Crear múltiples packs para el mismo artículo
        article_id = "article-multi-123"

        pack1 = ContextPack(
            id=ContextPackId.generate(),
            article_id=article_id,
            query="query 1",
            chunks=sample_chunks,
            created_at=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            metadata={},
        )

        pack2 = ContextPack(
            id=ContextPackId.generate(),
            article_id=article_id,
            query="query 2",
            chunks=sample_chunks[:2],
            created_at=datetime(2024, 1, 2, 12, 0, 0, tzinfo=timezone.utc),
            metadata={},
        )

        await write_repository.save(pack1)
        await write_repository.save(pack2)

        # Act
        found = await read_repository.find_by_article_id(article_id)

        # Assert
        assert len(found) == 2
        # Debería estar ordenado por fecha (más reciente primero)
        assert found[0].query == "query 2"
        assert found[1].query == "query 1"

    async def test_find_by_article_id_with_pagination(
        self,
        write_repository,
        read_repository,
        sample_chunks,
    ):
        """Debería paginar resultados por article_id."""
        # Arrange - Crear 3 packs
        article_id = "article-pagination-123"

        for i in range(3):
            pack = ContextPack(
                id=ContextPackId.generate(),
                article_id=article_id,
                query=f"query {i}",
                chunks=sample_chunks,
                created_at=datetime(2024, 1, i + 1, 12, 0, 0, tzinfo=timezone.utc),
                metadata={},
            )
            await write_repository.save(pack)

        # Act - Primera página (2 items)
        page1 = await read_repository.find_by_article_id(article_id, limit=2, offset=0)

        # Act - Segunda página (1 item)
        page2 = await read_repository.find_by_article_id(article_id, limit=2, offset=2)

        # Assert
        assert len(page1) == 2
        assert len(page2) == 1

    async def test_exists(
        self,
        write_repository,
        read_repository,
        sample_context_pack,
    ):
        """Debería verificar existencia correctamente."""
        # Arrange
        await write_repository.save(sample_context_pack)

        # Act & Assert - Existe
        assert await read_repository.exists(sample_context_pack.id) is True

        # Act & Assert - No existe
        assert await read_repository.exists(ContextPackId("non-existent")) is False

    async def test_count_by_article_id(
        self,
        write_repository,
        read_repository,
        sample_chunks,
    ):
        """Debería contar ContextPacks por article_id."""
        # Arrange
        article_id = "article-count-123"

        for i in range(5):
            pack = ContextPack(
                id=ContextPackId.generate(),
                article_id=article_id,
                query=f"query {i}",
                chunks=sample_chunks,
                created_at=datetime.utcnow(),
                metadata={},
            )
            await write_repository.save(pack)

        # Act
        count = await read_repository.count_by_article_id(article_id)

        # Assert
        assert count == 5

    async def test_count_by_article_id_returns_zero_when_none(
        self,
        read_repository,
    ):
        """Debería retornar 0 cuando no hay packs."""
        # Act
        count = await read_repository.count_by_article_id("non-existent")

        # Assert
        assert count == 0

    async def test_delete(
        self,
        write_repository,
        read_repository,
        sample_context_pack,
    ):
        """Debería eliminar ContextPack."""
        # Arrange
        await write_repository.save(sample_context_pack)
        assert await read_repository.exists(sample_context_pack.id) is True

        # Act
        await write_repository.delete(sample_context_pack.id)

        # Assert
        assert await read_repository.exists(sample_context_pack.id) is False

    async def test_delete_by_article_id(
        self,
        write_repository,
        read_repository,
        sample_chunks,
    ):
        """Debería eliminar todos los packs de un artículo."""
        # Arrange
        article_id = "article-delete-123"

        pack1 = ContextPack(
            id=ContextPackId.generate(),
            article_id=article_id,
            query="query 1",
            chunks=sample_chunks,
            created_at=datetime.utcnow(),
            metadata={},
        )

        pack2 = ContextPack(
            id=ContextPackId.generate(),
            article_id=article_id,
            query="query 2",
            chunks=sample_chunks,
            created_at=datetime.utcnow(),
            metadata={},
        )

        await write_repository.save(pack1)
        await write_repository.save(pack2)

        assert await read_repository.count_by_article_id(article_id) == 2

        # Act
        await write_repository.delete_by_article_id(article_id)

        # Assert
        assert await read_repository.count_by_article_id(article_id) == 0

    async def test_find_recent(
        self,
        write_repository,
        read_repository,
        sample_chunks,
    ):
        """Debería encontrar packs recientes."""
        # Arrange - Crear packs con diferentes fechas
        for i in range(5):
            pack = ContextPack(
                id=ContextPackId.generate(),
                article_id=f"article-{i}",
                query=f"query {i}",
                chunks=sample_chunks,
                created_at=datetime(2024, 1, i + 1, 12, 0, 0, tzinfo=timezone.utc),
                metadata={},
            )
            await write_repository.save(pack)

        # Act
        recent = await read_repository.find_recent(limit=3)

        # Assert
        assert len(recent) == 3
        # Debería estar ordenado por fecha (más reciente primero)
        assert recent[0].query == "query 4"
        assert recent[1].query == "query 3"
        assert recent[2].query == "query 2"

    async def test_cascade_delete_removes_chunks(
        self,
        write_repository,
        read_repository,
        sample_context_pack,
        db_session,
    ):
        """Debería eliminar chunks en cascada al eliminar pack."""
        # Arrange
        await write_repository.save(sample_context_pack)

        # Verificar que existen chunks
        from sqlalchemy import select

        from src.rag.infra.persistence.models.context_chunk_model import (
            ContextChunkModel,
        )

        stmt = select(ContextChunkModel).where(
            ContextChunkModel.context_pack_id == str(sample_context_pack.id)
        )
        result = await db_session.execute(stmt)
        chunks_before = result.scalars().all()
        assert len(chunks_before) == 3

        # Act - Eliminar pack
        await write_repository.delete(sample_context_pack.id)
        await db_session.flush()

        # Assert - Chunks también eliminados
        result = await db_session.execute(stmt)
        chunks_after = result.scalars().all()
        assert len(chunks_after) == 0
