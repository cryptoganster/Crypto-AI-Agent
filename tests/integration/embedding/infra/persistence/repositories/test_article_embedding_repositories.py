"""Integration tests para ArticleEmbedding repositories."""

from datetime import datetime, timezone
from uuid import uuid4

import numpy as np
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.embedding.domain.aggregates import ArticleEmbedding
from src.embedding.infra.persistence.models import ArticleEmbeddingModel
from src.embedding.infra.persistence.repositories import (
    SqlAlchemyArticleEmbeddingReadRepository,
    SqlAlchemyArticleEmbeddingWriteRepository,
)


@pytest.mark.integration
class TestRssArticleEmbeddingRepositories:
    """Integration tests para ArticleEmbedding repositories."""

    @pytest.fixture
    def write_repository(
        self, db_session: AsyncSession
    ) -> SqlAlchemyArticleEmbeddingWriteRepository:
        """Crea write repository con sesión de test."""
        return SqlAlchemyArticleEmbeddingWriteRepository(db_session)

    @pytest.fixture
    def read_repository(
        self, db_session: AsyncSession
    ) -> SqlAlchemyArticleEmbeddingReadRepository:
        """Crea read repository con sesión de test."""
        return SqlAlchemyArticleEmbeddingReadRepository(db_session)

    @pytest.fixture
    def sample_embedding(self) -> ArticleEmbedding:
        """Crea ArticleEmbedding de prueba."""
        # Crear vector normalizado
        vector = np.random.randn(768).astype(np.float32)
        vector = vector / np.linalg.norm(vector)

        return ArticleEmbedding(
            id=f"emb-{uuid4()}",
            article_id=f"art-{uuid4()}",
            embedding=vector,
            model="nomic-embed-text",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

    async def test_save_and_find_by_id(
        self,
        write_repository: SqlAlchemyArticleEmbeddingWriteRepository,
        read_repository: SqlAlchemyArticleEmbeddingReadRepository,
        sample_embedding: ArticleEmbedding,
        db_session: AsyncSession,
    ):
        """Debería guardar y recuperar embedding por ID."""
        # Act - Save
        await write_repository.save(sample_embedding)
        await db_session.commit()

        # Act - Find
        found = await read_repository.find_by_id(sample_embedding.id)

        # Assert
        assert found is not None
        assert found.id == sample_embedding.id
        assert found.article_id == sample_embedding.article_id
        assert found.model == sample_embedding.model
        np.testing.assert_array_almost_equal(
            found.embedding, sample_embedding.embedding
        )

    async def test_save_updates_existing_embedding(
        self,
        write_repository: SqlAlchemyArticleEmbeddingWriteRepository,
        read_repository: SqlAlchemyArticleEmbeddingReadRepository,
        sample_embedding: ArticleEmbedding,
        db_session: AsyncSession,
    ):
        """Debería actualizar embedding existente."""
        # Arrange - Save initial
        await write_repository.save(sample_embedding)
        await db_session.commit()

        # Crear nuevo vector
        new_vector = np.random.randn(768).astype(np.float32)
        new_vector = new_vector / np.linalg.norm(new_vector)

        updated_embedding = ArticleEmbedding(
            id=sample_embedding.id,  # Mismo ID
            article_id="art-updated",
            embedding=new_vector,
            model="new-model",
            created_at=sample_embedding.created_at,
            updated_at=datetime.now(timezone.utc),
        )

        # Act - Update
        await write_repository.save(updated_embedding)
        await db_session.commit()

        # Assert
        found = await read_repository.find_by_id(sample_embedding.id)
        assert found is not None
        assert found.article_id == "art-updated"
        assert found.model == "new-model"
        np.testing.assert_array_almost_equal(found.embedding, new_vector)

    async def test_find_by_article_id(
        self,
        write_repository: SqlAlchemyArticleEmbeddingWriteRepository,
        read_repository: SqlAlchemyArticleEmbeddingReadRepository,
        sample_embedding: ArticleEmbedding,
        db_session: AsyncSession,
    ):
        """Debería encontrar embedding por article_id."""
        # Arrange
        await write_repository.save(sample_embedding)
        await db_session.commit()

        # Act
        found = await read_repository.find_by_article_id(sample_embedding.article_id)

        # Assert
        assert found is not None
        assert found.id == sample_embedding.id
        assert found.article_id == sample_embedding.article_id

    async def test_find_by_article_id_returns_none_when_not_found(
        self,
        read_repository: SqlAlchemyArticleEmbeddingReadRepository,
    ):
        """Debería retornar None cuando article_id no existe."""
        # Act
        found = await read_repository.find_by_article_id("non-existent")

        # Assert
        assert found is None

    async def test_delete_removes_embedding(
        self,
        write_repository: SqlAlchemyArticleEmbeddingWriteRepository,
        read_repository: SqlAlchemyArticleEmbeddingReadRepository,
        sample_embedding: ArticleEmbedding,
        db_session: AsyncSession,
    ):
        """Debería eliminar embedding."""
        # Arrange
        await write_repository.save(sample_embedding)
        await db_session.commit()

        # Act
        await write_repository.delete(sample_embedding.id)
        await db_session.commit()

        # Assert
        found = await read_repository.find_by_id(sample_embedding.id)
        assert found is None

    async def test_delete_by_article_id_removes_all_embeddings(
        self,
        write_repository: SqlAlchemyArticleEmbeddingWriteRepository,
        read_repository: SqlAlchemyArticleEmbeddingReadRepository,
        db_session: AsyncSession,
    ):
        """Debería eliminar todos los embeddings de un artículo."""
        # Arrange - Crear múltiples embeddings para el mismo artículo
        article_id = f"art-{uuid4()}"

        embedding1 = ArticleEmbedding(
            id=f"emb-{uuid4()}",
            article_id=article_id,
            embedding=np.random.randn(768).astype(np.float32),
            model="test",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        embedding1.embedding = embedding1.embedding / np.linalg.norm(
            embedding1.embedding
        )

        await write_repository.save(embedding1)
        await db_session.commit()

        # Act
        await write_repository.delete_by_article_id(article_id)
        await db_session.commit()

        # Assert
        found = await read_repository.find_by_article_id(article_id)
        assert found is None

    async def test_exists_returns_true_when_embedding_exists(
        self,
        write_repository: SqlAlchemyArticleEmbeddingWriteRepository,
        read_repository: SqlAlchemyArticleEmbeddingReadRepository,
        sample_embedding: ArticleEmbedding,
        db_session: AsyncSession,
    ):
        """Debería retornar True cuando embedding existe."""
        # Arrange
        await write_repository.save(sample_embedding)
        await db_session.commit()

        # Act
        exists = await read_repository.exists(sample_embedding.id)

        # Assert
        assert exists is True

    async def test_exists_returns_false_when_embedding_not_found(
        self,
        read_repository: SqlAlchemyArticleEmbeddingReadRepository,
    ):
        """Debería retornar False cuando embedding no existe."""
        # Act
        exists = await read_repository.exists("non-existent")

        # Assert
        assert exists is False

    async def test_count_returns_total_embeddings(
        self,
        write_repository: SqlAlchemyArticleEmbeddingWriteRepository,
        read_repository: SqlAlchemyArticleEmbeddingReadRepository,
        db_session: AsyncSession,
    ):
        """Debería contar total de embeddings."""
        # Arrange - Crear múltiples embeddings
        for i in range(3):
            vector = np.random.randn(768).astype(np.float32)
            vector = vector / np.linalg.norm(vector)

            embedding = ArticleEmbedding(
                id=f"emb-{uuid4()}",
                article_id=f"art-{uuid4()}",
                embedding=vector,
                model="test",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            await write_repository.save(embedding)

        await db_session.commit()

        # Act
        count = await read_repository.count()

        # Assert
        assert count >= 3

    async def test_find_similar_returns_similar_embeddings(
        self,
        write_repository: SqlAlchemyArticleEmbeddingWriteRepository,
        read_repository: SqlAlchemyArticleEmbeddingReadRepository,
        db_session: AsyncSession,
    ):
        """Debería encontrar embeddings similares usando distancia coseno."""
        # Arrange - Crear embedding de referencia
        reference_vector = np.random.randn(768).astype(np.float32)
        reference_vector = reference_vector / np.linalg.norm(reference_vector)

        reference_embedding = ArticleEmbedding(
            id=f"emb-ref-{uuid4()}",
            article_id=f"art-ref-{uuid4()}",
            embedding=reference_vector,
            model="test",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        await write_repository.save(reference_embedding)

        # Crear embedding muy similar (pequeña perturbación)
        similar_vector = (
            reference_vector + np.random.randn(768).astype(np.float32) * 0.01
        )
        similar_vector = similar_vector / np.linalg.norm(similar_vector)

        similar_embedding = ArticleEmbedding(
            id=f"emb-sim-{uuid4()}",
            article_id=f"art-sim-{uuid4()}",
            embedding=similar_vector,
            model="test",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        await write_repository.save(similar_embedding)

        # Crear embedding diferente
        different_vector = np.random.randn(768).astype(np.float32)
        different_vector = different_vector / np.linalg.norm(different_vector)

        different_embedding = ArticleEmbedding(
            id=f"emb-diff-{uuid4()}",
            article_id=f"art-diff-{uuid4()}",
            embedding=different_vector,
            model="test",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        await write_repository.save(different_embedding)

        await db_session.commit()

        # Act - Buscar similares con threshold bajo para incluir todos
        similar_results = await read_repository.find_similar(
            reference_embedding,
            limit=10,
            threshold=0.0,  # Threshold bajo para incluir todos
        )

        # Assert
        assert len(similar_results) >= 2  # Al menos similar y different

        # Verificar que están ordenados por similitud descendente
        similarities = [score for _, score in similar_results]
        assert similarities == sorted(similarities, reverse=True)

        # Verificar que el más similar es el que creamos similar
        most_similar_embedding, most_similar_score = similar_results[0]
        assert most_similar_embedding.id == similar_embedding.id
        assert most_similar_score > 0.9  # Muy similar

    async def test_find_similar_respects_threshold(
        self,
        write_repository: SqlAlchemyArticleEmbeddingWriteRepository,
        read_repository: SqlAlchemyArticleEmbeddingReadRepository,
        db_session: AsyncSession,
    ):
        """Debería respetar threshold de similitud."""
        # Arrange
        reference_vector = np.random.randn(768).astype(np.float32)
        reference_vector = reference_vector / np.linalg.norm(reference_vector)

        reference_embedding = ArticleEmbedding(
            id=f"emb-ref-{uuid4()}",
            article_id=f"art-ref-{uuid4()}",
            embedding=reference_vector,
            model="test",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        await write_repository.save(reference_embedding)

        # Crear embedding diferente (baja similitud)
        different_vector = np.random.randn(768).astype(np.float32)
        different_vector = different_vector / np.linalg.norm(different_vector)

        different_embedding = ArticleEmbedding(
            id=f"emb-diff-{uuid4()}",
            article_id=f"art-diff-{uuid4()}",
            embedding=different_vector,
            model="test",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        await write_repository.save(different_embedding)

        await db_session.commit()

        # Act - Buscar con threshold alto
        similar_results = await read_repository.find_similar(
            reference_embedding,
            limit=10,
            threshold=0.95,  # Threshold muy alto
        )

        # Assert - No debería encontrar nada (vector aleatorio tiene baja similitud)
        assert len(similar_results) == 0

    async def test_find_similar_excludes_self(
        self,
        write_repository: SqlAlchemyArticleEmbeddingWriteRepository,
        read_repository: SqlAlchemyArticleEmbeddingReadRepository,
        sample_embedding: ArticleEmbedding,
        db_session: AsyncSession,
    ):
        """Debería excluir el mismo embedding de los resultados."""
        # Arrange
        await write_repository.save(sample_embedding)
        await db_session.commit()

        # Act
        similar_results = await read_repository.find_similar(
            sample_embedding,
            limit=10,
            threshold=0.0,
        )

        # Assert - No debería incluirse a sí mismo
        embedding_ids = [emb.id for emb, _ in similar_results]
        assert sample_embedding.id not in embedding_ids
