"""Unit tests para ArticleWriteRepository.

Estos tests verifican que el write repository implementa correctamente
las operaciones de escritura (save, delete) y que NO contiene operaciones
de lectura, siguiendo el patrón CQRS.
"""

from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from src.infra.persistence.repositories.rss.article_write_repository import (
    ArticleRepositoryException,
    ArticleWriteRepository,
)
from src.rss.article.domain.aggregates.rss_article import RssArticle
from src.rss.article.domain.factories.article_factory import RssArticleFactory
from src.rss.article.domain.value_objects import RssArticleId
from src.rss.article.infra.persistence.models import ArticleModel
from src.rss.feed.domain.value_objects import RssFeedId


class TestRssArticleWriteRepository:
    """Tests para ArticleWriteRepository - CQRS Write Side."""

    @pytest.fixture
    def mock_session(self):
        """Crea una sesión mock para testing."""
        return AsyncMock(spec=AsyncSession)

    @pytest.fixture
    def mock_event_publisher(self):
        """Crea un event publisher mock."""
        publisher = AsyncMock()
        publisher.publish = AsyncMock()
        return publisher

    @pytest.fixture
    def repository(self, mock_session, mock_event_publisher):
        """Crea un ArticleWriteRepository con mocks."""
        return ArticleWriteRepository(
            session=mock_session,
            logger=None,
            event_publisher=mock_event_publisher,
        )

    @pytest.fixture
    def sample_rss_article(self):
        """Crea un Article de ejemplo para testing."""
        article_id = RssArticleId(str(uuid4()))
        source_id = RssFeedId(str(uuid4()))

        factory = RssArticleFactory()

        article = factory.create_article(
            title="Test RssArticle",
            url="https://example.com/test",
            source_id=source_id,
            article_id=article_id,
        )

        article.update_content_fields(markdown="Test content")
        article.mark_events_as_committed()  # Limpiar eventos de test
        article._coin_mentions = None
        article._is_coin_checked = False

        return article

    # ========================================================================
    # TESTS: Repository solo tiene operaciones de escritura
    # ========================================================================

    def test_repository_only_has_write_operations(self, repository):
        """Debería tener solo operaciones de escritura (save, delete)."""
        # Assert - Verificar que tiene save y delete
        assert hasattr(repository, "save"), "Debe tener método save"
        assert hasattr(repository, "delete"), "Debe tener método delete"

        # Assert - Verificar que NO tiene operaciones de lectura
        assert not hasattr(
            repository, "find_all"
        ), "NO debe tener método find_all (usar IArticleQueries)"
        assert not hasattr(
            repository, "find_by_id"
        ), "NO debe tener método find_by_id (usar IArticleQueries)"
        assert not hasattr(
            repository, "exists"
        ), "NO debe tener método exists (usar IArticleQueries)"
        assert not hasattr(
            repository, "count"
        ), "NO debe tener método count (usar IArticleQueries)"

    # ========================================================================
    # TESTS: save() - Crear nuevo artículo
    # ========================================================================

    @pytest.mark.asyncio
    async def test_save_new_article_success(
        self, repository, mock_session, sample_article
    ):
        """Debería guardar un nuevo artículo correctamente."""
        # Arrange
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none = Mock(return_value=None)  # No existe
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.add = Mock()
        mock_session.flush = AsyncMock()
        mock_session.commit = AsyncMock()

        # Act
        await repository.save(sample_article)

        # Assert
        mock_session.execute.assert_called_once()  # Verificar existencia
        mock_session.add.assert_called_once()  # Agregar nuevo
        mock_session.flush.assert_called_once()  # Flush
        mock_session.commit.assert_called_once()  # Commit

    @pytest.mark.asyncio
    async def test_save_existing_article_updates(
        self, repository, mock_session, sample_article
    ):
        """Debería actualizar un artículo existente."""
        # Arrange
        existing_model = RssArticleModel(
            article_id=str(sample_article.identity_vo.article_id),
            source_id=str(sample_article.identity_vo.source_id),
            title="Old Title",
            url=sample_article.identity_vo.url.value,  # URL is already a string in the model
            content_markdown="Old content",
            summary="Old summary",
            content_hash="old_hash",
            quality_level="low",
            quality_score=50,
            is_duplicate=False,
            has_error=False,
            is_coin_checked=False,
        )

        mock_result = AsyncMock()
        mock_result.scalar_one_or_none = Mock(return_value=existing_model)
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.add = Mock()
        mock_session.flush = AsyncMock()
        mock_session.commit = AsyncMock()

        # Act
        await repository.save(sample_article)

        # Assert
        mock_session.execute.assert_called_once()  # Verificar existencia
        mock_session.add.assert_not_called()  # NO agregar (ya existe)
        mock_session.flush.assert_called_once()  # Flush
        mock_session.commit.assert_called_once()  # Commit

    # ========================================================================
    # TESTS: save() - Event Publishing
    # ========================================================================

    @pytest.mark.asyncio
    async def test_save_publishes_domain_events(
        self, repository, mock_session, mock_event_publisher, sample_article
    ):
        """Debería publicar eventos de dominio al guardar."""
        # Arrange
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none = Mock(return_value=None)
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.add = Mock()
        mock_session.flush = AsyncMock()
        mock_session.commit = AsyncMock()

        expected_event_count = len(sample_article.domain_events)

        # Act
        await repository.save(sample_article)

        # Assert
        assert (
            mock_event_publisher.publish.call_count == expected_event_count
        ), f"Debe publicar {expected_event_count} eventos"

    @pytest.mark.asyncio
    async def test_save_without_event_publisher_does_not_fail(
        self, mock_session, sample_article
    ):
        """Debería funcionar sin event publisher."""
        # Arrange
        repository = ArticleWriteRepository(
            session=mock_session,
            logger=None,
            event_publisher=None,  # Sin publisher
        )

        mock_result = AsyncMock()
        mock_result.scalar_one_or_none = Mock(return_value=None)
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.add = Mock()
        mock_session.flush = AsyncMock()
        mock_session.commit = AsyncMock()

        # Act & Assert - No debe fallar
        await repository.save(sample_article)

        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_save_publishes_events_after_commit(
        self, repository, mock_session, mock_event_publisher, sample_article
    ):
        """Debería publicar eventos después de commit."""
        # Arrange
        call_order = []

        async def track_commit():
            call_order.append("commit")

        async def track_publish(event):
            call_order.append("publish")

        mock_result = AsyncMock()
        mock_result.scalar_one_or_none = Mock(return_value=None)
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.add = Mock()
        mock_session.flush = AsyncMock()
        mock_session.commit = AsyncMock(side_effect=track_commit)
        mock_event_publisher.publish = AsyncMock(side_effect=track_publish)

        # Act
        await repository.save(sample_article)

        # Assert
        if len(sample_article.domain_events) > 0:
            commit_index = call_order.index("commit")
            publish_index = call_order.index("publish")
            assert commit_index < publish_index, "commit debe ocurrir antes de publish"

    # ========================================================================
    # TESTS: save() - Error Handling
    # ========================================================================

    @pytest.mark.asyncio
    async def test_save_raises_exception_on_integrity_error(
        self, repository, mock_session, sample_article
    ):
        """Debería lanzar ArticleRepositoryException en error de integridad."""
        # Arrange
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none = Mock(return_value=None)
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.add = Mock()
        mock_session.flush = AsyncMock(
            side_effect=IntegrityError("Duplicate", {}, None)
        )

        # Act & Assert
        with pytest.raises(ArticleRepositoryException) as exc_info:
            await repository.save(sample_article)

        assert "integridad" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_save_raises_exception_on_sqlalchemy_error(
        self, repository, mock_session, sample_article
    ):
        """Debería lanzar ArticleRepositoryException en error de SQLAlchemy."""
        # Arrange
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none = Mock(return_value=None)
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.add = Mock()
        mock_session.flush = AsyncMock(side_effect=SQLAlchemyError("Database error"))

        # Act & Assert
        with pytest.raises(ArticleRepositoryException) as exc_info:
            await repository.save(sample_article)

        assert "base de datos" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_save_raises_exception_on_unexpected_error(
        self, repository, mock_session, sample_article
    ):
        """Debería lanzar ArticleRepositoryException en error inesperado."""
        # Arrange
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none = Mock(return_value=None)
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.add = Mock()
        mock_session.flush = AsyncMock(side_effect=Exception("Unexpected error"))

        # Act & Assert
        with pytest.raises(ArticleRepositoryException) as exc_info:
            await repository.save(sample_article)

        assert "inesperado" in str(exc_info.value).lower()

    # ========================================================================
    # TESTS: delete()
    # ========================================================================

    @pytest.mark.asyncio
    async def test_delete_existing_article_returns_true(self, repository, mock_session):
        """Debería retornar True al eliminar un artículo existente."""
        # Arrange
        article_id = RssArticleId(str(uuid4()))

        mock_result = AsyncMock()
        mock_result.rowcount = 1  # Se eliminó 1 fila
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.flush = AsyncMock()

        # Act
        result = await repository.delete(article_id)

        # Assert
        assert result is True, "Debe retornar True cuando se elimina"
        mock_session.execute.assert_called_once()
        mock_session.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_nonexistent_article_returns_false(
        self, repository, mock_session
    ):
        """Debería retornar False al intentar eliminar un artículo inexistente."""
        # Arrange
        article_id = RssArticleId(str(uuid4()))

        mock_result = AsyncMock()
        mock_result.rowcount = 0  # No se eliminó nada
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.flush = AsyncMock()

        # Act
        result = await repository.delete(article_id)

        # Assert
        assert result is False, "Debe retornar False cuando no existe"
        mock_session.execute.assert_called_once()
        mock_session.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_raises_exception_on_sqlalchemy_error(
        self, repository, mock_session
    ):
        """Debería lanzar ArticleRepositoryException en error de SQLAlchemy."""
        # Arrange
        article_id = RssArticleId(str(uuid4()))

        mock_session.execute = AsyncMock(side_effect=SQLAlchemyError("Database error"))

        # Act & Assert
        with pytest.raises(ArticleRepositoryException) as exc_info:
            await repository.delete(article_id)

        assert "base de datos" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_delete_raises_exception_on_unexpected_error(
        self, repository, mock_session
    ):
        """Debería lanzar ArticleRepositoryException en error inesperado."""
        # Arrange
        article_id = RssArticleId(str(uuid4()))

        mock_session.execute = AsyncMock(side_effect=Exception("Unexpected error"))

        # Act & Assert
        with pytest.raises(ArticleRepositoryException) as exc_info:
            await repository.delete(article_id)

        assert "inesperado" in str(exc_info.value).lower()

    # ========================================================================
    # TESTS: CQRS Compliance
    # ========================================================================

    def test_repository_interface_compliance(self, repository):
        """Debería cumplir con la interface IRssArticleWriteRepository."""
        # Assert - Verificar que implementa los métodos requeridos
        assert callable(getattr(repository, "save", None)), "Debe implementar save()"
        assert callable(
            getattr(repository, "delete", None)
        ), "Debe implementar delete()"

        # Assert - Verificar que NO implementa métodos de lectura
        read_methods = ["find_all", "find_by_id", "exists", "count"]
        for method in read_methods:
            assert not hasattr(
                repository, method
            ), f"NO debe implementar {method}() - usar IArticleQueries"

    def test_repository_docstring_mentions_cqrs(self, repository):
        """Debería mencionar CQRS en la documentación."""
        # Assert
        docstring = repository.__class__.__doc__
        assert docstring is not None, "Debe tener docstring"
        assert "CQRS" in docstring, "Debe mencionar CQRS"
        assert (
            "Command Side" in docstring or "escritura" in docstring
        ), "Debe indicar que es Command Side"
