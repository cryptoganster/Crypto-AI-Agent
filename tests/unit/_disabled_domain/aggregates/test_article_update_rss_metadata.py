"""Tests para el método update_rss_metadata() de RssArticle aggregate.

Tests para Fase 2 del refactor: Consolidación de Setters Adicionales.
"""

from datetime import datetime, timezone

import pytest

from src.rss.article.domain.aggregates.rss_article import RssArticle
from src.rss.article.domain.factories.article_factory import RssArticleFactory
from src.rss.feed.domain.value_objects import RssFeedId


class TestRssArticleUpdateRssMetadata:
    """Tests para el método update_rss_metadata() del Article aggregate."""

    @pytest.fixture
    def article_factory(self):
        """Factory para crear artículos de prueba."""
        return RssArticleFactory()

    @pytest.fixture
    def sample_rss_article(self, article_factory):
        """Artículo de prueba."""
        return article_factory.create_article(
            title="Test RssArticle",
            url="https://example.com/test",
            source_id=RssFeedId("test-source-123"),
        )

    # Tests de actualización de campos individuales

    def test_update_rss_metadata_updates_guid_only(self, sample_article):
        """Debería actualizar solo el campo guid."""
        # Arrange
        initial_pub_date = sample_article.metadata.pub_date
        initial_description = sample_article.metadata.description

        # Act
        sample_article.update_metadata(guid="unique-guid-123")

        # Assert
        assert sample_article.metadata.guid.value == "unique-guid-123"
        assert sample_article.metadata.pub_date.value == initial_pub_date
        assert sample_article.metadata.description.value == initial_description

    def test_update_rss_metadata_updates_pub_date_only(self, sample_article):
        """Debería actualizar solo el campo pub_date."""
        # Arrange
        initial_guid = sample_article.metadata.guid
        initial_description = sample_article.metadata.description
        new_pub_date = datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc)

        # Act
        sample_article.update_metadata(pub_date=new_pub_date)

        # Assert
        assert sample_article.metadata.pub_date.value == new_pub_date
        assert sample_article.metadata.guid.value == initial_guid
        assert sample_article.metadata.description.value == initial_description

    def test_update_rss_metadata_updates_description_only(self, sample_article):
        """Debería actualizar solo el campo description."""
        # Arrange
        initial_guid = sample_article.metadata.guid
        initial_pub_date = sample_article.metadata.pub_date

        # Act
        sample_article.update_metadata(description="RSS feed description")

        # Assert
        assert sample_article.metadata.description.value == "RSS feed description"
        assert sample_article.metadata.guid.value == initial_guid
        assert sample_article.metadata.pub_date.value == initial_pub_date

    # Tests de actualización batch de múltiples campos

    def test_update_rss_metadata_updates_all_fields(self, sample_article):
        """Debería actualizar múltiples campos en batch."""
        # Arrange
        new_pub_date = datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc)

        # Act
        sample_article.update_metadata(
            guid="batch-guid-456",
            pub_date=new_pub_date,
            description="Batch update description",
        )

        # Assert
        assert sample_article.metadata.guid.value == "batch-guid-456"
        assert sample_article.metadata.pub_date.value == new_pub_date
        assert sample_article.metadata.description.value == "Batch update description"

    def test_update_rss_metadata_updates_guid_and_pub_date(self, sample_article):
        """Debería actualizar guid y pub_date juntos."""
        # Arrange
        new_pub_date = datetime(2024, 2, 20, 10, 30, 0, tzinfo=timezone.utc)

        # Act
        sample_article.update_metadata(guid="combined-guid-789", pub_date=new_pub_date)

        # Assert
        assert sample_article.metadata.guid.value == "combined-guid-789"
        assert sample_article.metadata.pub_date.value == new_pub_date

    def test_update_rss_metadata_updates_pub_date_and_description(self, sample_article):
        """Debería actualizar pub_date y description juntos."""
        # Arrange
        new_pub_date = datetime(2024, 3, 10, 8, 15, 0, tzinfo=timezone.utc)

        # Act
        sample_article.update_metadata(
            pub_date=new_pub_date, description="Combined description"
        )

        # Assert
        assert sample_article.metadata.pub_date.value == new_pub_date
        assert sample_article.metadata.description.value == "Combined description"

    # Tests que solo campos proporcionados cambian

    def test_update_rss_metadata_preserves_unprovided_fields(self, sample_article):
        """Debería preservar campos no proporcionados."""
        # Arrange - Establecer valores iniciales
        initial_pub_date = datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        sample_article.update_metadata(
            guid="initial-guid",
            pub_date=initial_pub_date,
            description="Initial description",
        )

        # Act - Actualizar solo guid
        sample_article.update_metadata(guid="updated-guid")

        # Assert - Otros campos deben permanecer sin cambios
        assert sample_article.metadata.guid.value == "updated-guid"
        assert sample_article.metadata.pub_date.value == initial_pub_date
        assert sample_article.metadata.description.value == "Initial description"

    def test_update_rss_metadata_with_no_parameters_does_nothing(self, sample_article):
        """Debería no hacer nada si no se proporcionan parámetros."""
        # Arrange
        initial_guid = sample_article.metadata.guid
        initial_pub_date = sample_article.metadata.pub_date
        initial_description = sample_article.metadata.description

        # Act
        sample_article.update_metadata()

        # Assert
        assert sample_article.metadata.guid.value == initial_guid
        assert sample_article.metadata.pub_date.value == initial_pub_date
        assert sample_article.metadata.description.value == initial_description

    # Tests de manejo de valores None

    def test_update_rss_metadata_sets_guid_to_none(self, sample_article):
        """Debería establecer guid a None cuando se pasa None."""
        # Arrange
        sample_article.update_metadata(guid="initial-guid")
        assert sample_article.metadata.guid is not None

        # Act
        sample_article.update_metadata(guid=None)

        # Assert
        assert sample_article.metadata.guid is None

    def test_update_rss_metadata_sets_pub_date_to_none(self, sample_article):
        """Debería establecer pub_date a None cuando se pasa None."""
        # Arrange
        sample_article.update_metadata(pub_date=datetime.now(timezone.utc))
        assert sample_article.metadata.pub_date is not None

        # Act
        sample_article.update_metadata(pub_date=None)

        # Assert
        assert sample_article.metadata.pub_date is None

    def test_update_rss_metadata_sets_description_to_none(self, sample_article):
        """Debería establecer description a None cuando se pasa None."""
        # Arrange
        sample_article.update_metadata(description="Initial description")
        assert sample_article.metadata.description is not None

        # Act
        sample_article.update_metadata(description=None)

        # Assert
        assert sample_article.metadata.description is None

    # Tests de actualización de timestamp

    def test_update_rss_metadata_updates_timestamp(self, sample_article):
        """Debería actualizar el timestamp updated_at."""
        # Arrange
        initial_updated_at = sample_article.updated_at

        # Act
        sample_article.update_metadata(guid="new-guid")

        # Assert
        assert sample_article.updated_at > initial_updated_at


class TestRssArticleRssSettersAsWrappers:
    """Tests para verificar que los setters son wrappers de update_rss_metadata()."""

    @pytest.fixture
    def article_factory(self):
        """Factory para crear artículos de prueba."""
        return RssArticleFactory()

    @pytest.fixture
    def sample_rss_article(self, article_factory):
        """Artículo de prueba."""
        return article_factory.create_article(
            title="Test RssArticle",
            url="https://example.com/test",
            source_id=RssFeedId("test-source-123"),
        )

    def test_set_rss_guid_is_equivalent_to_update_rss_metadata(self, sample_article):
        """set_rss_guid() debería ser equivalente a update_rss_metadata(guid=...)."""
        # Arrange
        article1 = sample_article
        article_factory = RssArticleFactory()
        article2 = article_factory.create_article(
            title="Test RssArticle",
            url="https://example.com/test2",
            source_id=RssFeedId("test-source-123"),
        )

        # Act
        article1.update_metadata(guid="test-guid-123")
        article2.update_metadata(guid="test-guid-123")

        # Assert
        assert article1.metadata.guid == article2.metadata.guid

    def test_set_pub_date_is_equivalent_to_update_rss_metadata(self, sample_article):
        """set_pub_date() debería ser equivalente a update_rss_metadata(pub_date=...)."""
        # Arrange
        article1 = sample_article
        article_factory = RssArticleFactory()
        article2 = article_factory.create_article(
            title="Test RssArticle",
            url="https://example.com/test2",
            source_id=RssFeedId("test-source-123"),
        )
        test_date = datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc)

        # Act
        article1.update_metadata(pub_date=test_date)
        article2.update_metadata(pub_date=test_date)

        # Assert
        assert article1.metadata.pub_date == article2.metadata.pub_date

    def test_set_description_is_equivalent_to_update_rss_metadata(self, sample_article):
        """set_description() debería ser equivalente a update_rss_metadata(description=...)."""
        # Arrange
        article1 = sample_article
        article_factory = RssArticleFactory()
        article2 = article_factory.create_article(
            title="Test RssArticle",
            url="https://example.com/test2",
            source_id=RssFeedId("test-source-123"),
        )

        # Act
        article1.update_metadata(description="Test description")
        article2.update_metadata(description="Test description")

        # Assert
        assert article1.metadata.description == article2.metadata.description

    def test_set_rss_guid_preserves_other_fields(self, sample_article):
        """set_rss_guid() debería preservar otros campos de RSS metadata."""
        # Arrange
        test_date = datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
        sample_article.update_metadata(
            pub_date=test_date, description="Initial description"
        )
        initial_pub_date = sample_article.metadata.pub_date
        initial_description = sample_article.metadata.description

        # Act
        sample_article.update_metadata(guid="new-guid")

        # Assert
        assert sample_article.metadata.guid.value == "new-guid"
        assert sample_article.metadata.pub_date.value == initial_pub_date
        assert sample_article.metadata.description.value == initial_description

    def test_set_pub_date_preserves_other_fields(self, sample_article):
        """set_pub_date() debería preservar otros campos de RSS metadata."""
        # Arrange
        sample_article.update_metadata(
            guid="initial-guid", description="Initial description"
        )
        initial_guid = sample_article.metadata.guid
        initial_description = sample_article.metadata.description
        new_date = datetime(2024, 2, 20, 10, 30, 0, tzinfo=timezone.utc)

        # Act
        sample_article.update_metadata(pub_date=new_date)

        # Assert
        assert sample_article.metadata.pub_date.value == new_date
        assert sample_article.metadata.guid.value == initial_guid
        assert sample_article.metadata.description.value == initial_description

    def test_set_description_preserves_other_fields(self, sample_article):
        """set_description() debería preservar otros campos de RSS metadata."""
        # Arrange
        test_date = datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
        sample_article.update_metadata(guid="initial-guid", pub_date=test_date)
        initial_guid = sample_article.metadata.guid
        initial_pub_date = sample_article.metadata.pub_date

        # Act
        sample_article.update_metadata(description="New description")

        # Assert
        assert sample_article.metadata.description.value == "New description"
        assert sample_article.metadata.guid.value == initial_guid
        assert sample_article.metadata.pub_date.value == initial_pub_date
