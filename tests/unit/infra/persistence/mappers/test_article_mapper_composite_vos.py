"""Tests para RssArticleMapper con Value Objects compuestos.

Valida que el mapper correctamente:
- Crea RssArticleMetadata desde ArticleModel (Requirements 7.2)
- Crea RssArticleMetadata desde ArticleModel (Requirements 7.2)
- Extrae campos de RssArticleMetadata al crear ArticleModel (Requirements 7.3)
- Extrae campos de RssArticleMetadata al crear ArticleModel (Requirements 7.3)
- Preserva datos en round-trip (Requirements 7.4)
- Actualiza modelos correctamente (Requirements 7.5)
"""

import uuid
from datetime import datetime, timezone

import pytest

from src.rss.article.domain.aggregates.rss_article import RssArticle
from src.rss.article.domain.value_objects import (
    RssArticleId,
    RssArticleTitle,
    RssArticleUrl,
)
from src.rss.article.domain.value_objects.metadata import (
    RssArticleMetadata,
    RssArticleSummary,
    RssArticleThumbnailUrl,
)
from src.rss.article.infra.persistence.mappers import RssArticleMapper
from src.rss.article.infra.persistence.models import ArticleModel
from src.rss.feed.domain.value_objects import RssFeedId

# Test UUIDs - Valid UUIDs for testing
ART_123 = "046e66b2-2a08-46ef-9281-f2460bf5e252"
ART_MINIMAL = "3d4cfd97-a6a9-4ba6-afeb-5265ba27851f"
ART_789 = "d23e8025-fe26-4fc0-a19e-8c4b749e0e8d"
ART_ROUND_TRIP = "46ab2aee-52c8-41e1-89b1-6ddab3dd34a8"
ART_META_RT = "e0bdc69c-b4fc-4134-beb9-09e9543be7eb"
ART_FULL_RT = "f3b5cb03-949e-4fb1-95be-86c3d77efe68"
OLD_ID = "ad4d307c-5efd-4799-9b3e-5bf493158bd6"
NEW_ID = "c3134e30-2981-4977-858b-b2c19a67316c"
ART_UPDATE = "148e2ba8-0648-4f42-9cbc-244edd4c4f60"
ART_PRESERVE = "834d08c3-9970-4447-ae54-1840ab4cef83"

SRC_456 = "dd6eca55-c330-4ded-ba2c-d3b47ae05a18"
SRC_MINIMAL = "7971b31b-4ec6-4b00-86e1-bae2251863f1"
SRC_101 = "9420f7f7-1d17-4f50-a801-f078e5b6e298"
SRC_ROUND_TRIP = "17db0fbd-9ac4-4965-8719-cf9ba2ef79ac"
SRC_META_RT = "10d8b773-0626-4643-bb07-46c27b896ae7"
SRC_FULL_RT = "97e2da96-773d-4239-a4fe-79629fa15d61"
OLD_SOURCE = "af0b5e10-9ac4-46ef-b359-d63df83eea35"
NEW_SOURCE = "d0c9d7c9-d0ca-4839-bd6e-acfac0b25e0b"
SRC_UPDATE = "773328ed-4f95-4a83-85e3-7c5ac2286258"
SRC_PRESERVE = "2f0612a7-96bf-4afd-be29-6743bd35b552"


class TestRssArticleMapperToDomain:
    """Tests para RssArticleMapper.to_domain() con composite VOs."""

    def test_to_domain_creates_article_identity_correctly(self):
        """Debería crear RssArticleMetadata correctamente desde ArticleModel.

        Validates: Requirements 7.2
        """
        # Arrange
        model = RssArticleModel(
            id=ART_123,
            source_id=SRC_456,
            title="Test RssArticle",
            url="https://example.com/article",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        # Act
        article = RssArticleMapper.to_domain(model)

        # Assert
        assert article.identity_vo is not None
        assert isinstance(article.identity_vo, RssArticleMetadata)
        assert str(article.identity_vo.article_id) == ART_123
        assert str(article.identity_vo.source_id) == SRC_456
        assert article.identity_vo.url.value == "https://example.com/article"

    def test_to_domain_creates_article_metadata_correctly(self):
        """Debería crear RssArticleMetadata correctamente desde ArticleModel.

        Validates: Requirements 7.2
        """
        # Arrange
        model = RssArticleModel(
            id=ART_123,
            source_id=SRC_456,
            title="Test RssArticle",
            url="https://example.com/article",
            summary="Test summary",
            thumbnail_url="https://example.com/thumb.jpg",
            author="John Doe",
            language="en",
            tags=["tech", "python"],
            keywords=["testing", "ddd"],
            categories=["Technology"],
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        # Act
        article = RssArticleMapper.to_domain(model)

        # Assert
        assert article.metadata_vo is not None
        assert isinstance(article.metadata_vo, RssArticleMetadata)
        assert article.metadata.title.value == "Test RssArticle"
        assert str(article.metadata.summary) == "Test summary"
        assert str(article.metadata.thumbnail_url) == "https://example.com/thumb.jpg"
        assert str(article.metadata.author) == "John Doe"
        assert article.metadata.language.code == "en"
        assert "tech" in article.metadata.tags.sorted_tags
        assert "testing" in article.metadata.keywords.keywords

    def test_to_domain_handles_minimal_article_model(self):
        """Debería manejar ArticleModel con campos mínimos.

        Validates: Requirements 7.2
        """
        # Arrange
        model = RssArticleModel(
            id=ART_MINIMAL,
            source_id=SRC_MINIMAL,
            title="Minimal RssArticle",
            url="https://example.com/minimal",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        # Act
        article = RssArticleMapper.to_domain(model)

        # Assert
        assert article.identity_vo.article_id is not None
        assert article.identity_vo.source_id is not None
        assert article.identity_vo.url is not None
        assert article.metadata.title is not None
        assert article.metadata.summary is None
        assert article.metadata.thumbnail_url is None
        assert article.metadata.author is None


class TestRssArticleMapperToModel:
    """Tests para RssArticleMapper.to_model() con composite VOs."""

    def test_to_model_extracts_article_id_from_identity_vo(self):
        """Debería extraer article_id desde identity_vo.

        Validates: Requirements 7.3
        """
        # Arrange
        identity = RssArticleMetadata.create(
            id=RssArticleId(ART_789),
            source_id=RssFeedId(SRC_101),
            url=RssArticleUrl("https://example.com/test"),
        )
        metadata = RssArticleMetadata.create(
            title=RssArticleTitle("Test Title"),
        )
        article = RssArticle(identity=identity, metadata=metadata)

        # Act
        model = RssArticleMapper.to_model(article)

        # Assert
        assert model.id == ART_789

    def test_to_model_extracts_source_id_from_identity_vo(self):
        """Debería extraer source_id desde identity_vo.

        Validates: Requirements 7.3
        """
        # Arrange
        identity = RssArticleMetadata.create(
            id=RssArticleId(ART_789),
            source_id=RssFeedId(SRC_101),
            url=RssArticleUrl("https://example.com/test"),
        )
        metadata = RssArticleMetadata.create(
            title=RssArticleTitle("Test Title"),
        )
        article = RssArticle(identity=identity, metadata=metadata)

        # Act
        model = RssArticleMapper.to_model(article)

        # Assert
        assert model.source_id == SRC_101

    def test_to_model_extracts_url_from_identity_vo(self):
        """Debería extraer url desde identity_vo.

        Validates: Requirements 7.3
        """
        # Arrange
        identity = RssArticleMetadata.create(
            id=RssArticleId(ART_789),
            source_id=RssFeedId(SRC_101),
            url=RssArticleUrl("https://example.com/test"),
        )
        metadata = RssArticleMetadata.create(
            title=RssArticleTitle("Test Title"),
        )
        article = RssArticle(identity=identity, metadata=metadata)

        # Act
        model = RssArticleMapper.to_model(article)

        # Assert
        assert model.url == "https://example.com/test"

    def test_to_model_extracts_title_from_metadata_vo(self):
        """Debería extraer title desde metadata_vo.

        Validates: Requirements 7.3
        """
        # Arrange
        identity = RssArticleMetadata.create(
            id=RssArticleId(ART_789),
            source_id=RssFeedId(SRC_101),
            url=RssArticleUrl("https://example.com/test"),
        )
        metadata = RssArticleMetadata.create(
            title=RssArticleTitle("My Test RssArticle"),
        )
        article = RssArticle(identity=identity, metadata=metadata)

        # Act
        model = RssArticleMapper.to_model(article)

        # Assert
        assert model.title == "My Test RssArticle"

    def test_to_model_extracts_summary_from_metadata_vo(self):
        """Debería extraer summary desde metadata_vo.

        Validates: Requirements 7.3
        """
        # Arrange
        identity = RssArticleMetadata.create(
            id=RssArticleId(ART_789),
            source_id=RssFeedId(SRC_101),
            url=RssArticleUrl("https://example.com/test"),
        )
        metadata = RssArticleMetadata.create(
            title=RssArticleTitle("Test Title"),
            summary=RssArticleSummary("Test summary content"),
        )
        article = RssArticle(identity=identity, metadata=metadata)

        # Act
        model = RssArticleMapper.to_model(article)

        # Assert
        assert model.summary == "Test summary content"

    def test_to_model_extracts_thumbnail_url_from_metadata_vo(self):
        """Debería extraer thumbnail_url desde metadata_vo.

        Validates: Requirements 7.3
        """
        # Arrange
        identity = RssArticleMetadata.create(
            id=RssArticleId(ART_789),
            source_id=RssFeedId(SRC_101),
            url=RssArticleUrl("https://example.com/test"),
        )
        metadata = RssArticleMetadata.create(
            title=RssArticleTitle("Test Title"),
            thumbnail_url=RssArticleThumbnailUrl("https://example.com/image.jpg"),
        )
        article = RssArticle(identity=identity, metadata=metadata)

        # Act
        model = RssArticleMapper.to_model(article)

        # Assert
        assert model.thumbnail_url == "https://example.com/image.jpg"

    def test_to_model_handles_none_values_in_metadata(self):
        """Debería manejar valores None en metadata_vo correctamente.

        Validates: Requirements 7.3
        """
        # Arrange
        identity = RssArticleMetadata.create(
            id=RssArticleId(ART_789),
            source_id=RssFeedId(SRC_101),
            url=RssArticleUrl("https://example.com/test"),
        )
        metadata = RssArticleMetadata.create(
            title=RssArticleTitle("Test Title"),
            summary=None,
            thumbnail_url=None,
            author=None,
        )
        article = RssArticle(identity=identity, metadata=metadata)

        # Act
        model = RssArticleMapper.to_model(article)

        # Assert
        assert model.summary is None
        assert model.thumbnail_url is None
        assert model.author is None


class TestRssArticleMapperRoundTrip:
    """Tests para round-trip (to_model → to_domain) preserva datos."""

    def test_round_trip_preserves_identity_data(self):
        """Debería preservar datos de identity en round-trip.

        Validates: Requirements 7.4
        """
        # Arrange
        identity = RssArticleMetadata.create(
            id=RssArticleId(ART_ROUND_TRIP),
            source_id=RssFeedId(SRC_ROUND_TRIP),
            url=RssArticleUrl("https://example.com/roundtrip"),
        )
        metadata = RssArticleMetadata.create(
            title=RssArticleTitle("Round Trip Test"),
        )
        original_article = RssArticle(identity=identity, metadata=metadata)

        # Act
        model = RssArticleMapper.to_model(original_article)
        reconstructed_article = RssArticleMapper.to_domain(model)

        # Assert
        assert str(reconstructed_article.identity_vo.article_id) == ART_ROUND_TRIP
        assert str(reconstructed_article.identity_vo.source_id) == SRC_ROUND_TRIP
        assert (
            reconstructed_article.identity_vo.url.value
            == "https://example.com/roundtrip"
        )

    def test_round_trip_preserves_metadata_data(self):
        """Debería preservar datos de metadata en round-trip.

        Validates: Requirements 7.4
        """
        # Arrange
        identity = RssArticleMetadata.create(
            id=RssArticleId(ART_META_RT),
            source_id=RssFeedId(SRC_META_RT),
            url=RssArticleUrl("https://example.com/meta-rt"),
        )
        metadata = RssArticleMetadata.create(
            title=RssArticleTitle("Metadata Round Trip"),
            summary=RssArticleSummary("Summary for round trip"),
            thumbnail_url=RssArticleThumbnailUrl("https://example.com/thumb-rt.jpg"),
        )
        original_article = RssArticle(identity=identity, metadata=metadata)

        # Act
        model = RssArticleMapper.to_model(original_article)
        reconstructed_article = RssArticleMapper.to_domain(model)

        # Assert
        assert reconstructed_article.metadata.title.value == "Metadata Round Trip"
        assert str(reconstructed_article.metadata.summary) == "Summary for round trip"
        assert (
            str(reconstructed_article.metadata.thumbnail_url)
            == "https://example.com/thumb-rt.jpg"
        )

    def test_round_trip_preserves_all_composite_vos(self):
        """Debería preservar todos los Value Objects compuestos en round-trip.

        Validates: Requirements 7.4
        """
        # Arrange
        identity = RssArticleMetadata.create(
            id=RssArticleId(ART_FULL_RT),
            source_id=RssFeedId(SRC_FULL_RT),
            url=RssArticleUrl("https://example.com/full-rt"),
        )
        metadata = RssArticleMetadata.create(
            title=RssArticleTitle("Full Round Trip"),
            summary=RssArticleSummary("Complete summary"),
            thumbnail_url=RssArticleThumbnailUrl("https://example.com/full-thumb.jpg"),
        )
        original_article = RssArticle(identity=identity, metadata=metadata)

        # Act
        model = RssArticleMapper.to_model(original_article)
        reconstructed_article = RssArticleMapper.to_domain(model)

        # Assert - Identity
        assert str(reconstructed_article.identity_vo.article_id) == str(
            original_article.identity_vo.article_id
        )
        assert str(reconstructed_article.identity_vo.source_id) == str(
            original_article.identity_vo.source_id
        )
        assert (
            reconstructed_article.identity_vo.url.value
            == original_article.identity_vo.url.value
        )

        # Assert - Metadata
        assert (
            reconstructed_article.metadata.title.value
            == original_article.metadata.title.value
        )
        assert str(reconstructed_article.metadata.summary) == str(
            original_article.metadata.summary
        )
        assert str(reconstructed_article.metadata.thumbnail_url) == str(
            original_article.metadata.thumbnail_url
        )


class TestRssArticleMapperUpdateModel:
    """Tests para RssArticleMapper.update_model_from_domain()."""

    def test_update_model_updates_identity_fields(self):
        """Debería actualizar campos de identity correctamente.

        Validates: Requirements 7.5
        """
        # Arrange
        model = RssArticleModel(
            id=OLD_ID,
            source_id=OLD_SOURCE,
            title="Old Title",
            url="https://old.com/article",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        identity = RssArticleMetadata.create(
            id=RssArticleId(NEW_ID),
            source_id=RssFeedId(NEW_SOURCE),
            url=RssArticleUrl("https://new.com/article"),
        )
        metadata = RssArticleMetadata.create(
            title=RssArticleTitle("New Title"),
        )
        article = RssArticle(identity=identity, metadata=metadata)

        # Act
        RssArticleMapper.update_model_from_domain(model, article)

        # Assert
        assert model.id == NEW_ID
        assert model.source_id == NEW_SOURCE
        assert model.url == "https://new.com/article"

    def test_update_model_updates_metadata_fields(self):
        """Debería actualizar campos de metadata correctamente.

        Validates: Requirements 7.5
        """
        # Arrange
        model = RssArticleModel(
            id=ART_UPDATE,
            source_id=SRC_UPDATE,
            title="Old Title",
            url="https://example.com/update",
            summary="Old summary",
            thumbnail_url="https://old.com/thumb.jpg",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        identity = RssArticleMetadata.create(
            id=RssArticleId(ART_UPDATE),
            source_id=RssFeedId(SRC_UPDATE),
            url=RssArticleUrl("https://example.com/update"),
        )
        metadata = RssArticleMetadata.create(
            title=RssArticleTitle("Updated Title"),
            summary=RssArticleSummary("Updated summary"),
            thumbnail_url=RssArticleThumbnailUrl("https://new.com/thumb.jpg"),
        )
        article = RssArticle(identity=identity, metadata=metadata)

        # Act
        RssArticleMapper.update_model_from_domain(model, article)

        # Assert
        assert model.title == "Updated Title"
        assert model.summary == "Updated summary"
        assert model.thumbnail_url == "https://new.com/thumb.jpg"

    def test_update_model_preserves_none_values(self):
        """Debería preservar valores None cuando se actualizan campos opcionales.

        Validates: Requirements 7.5
        """
        # Arrange
        model = RssArticleModel(
            id=ART_PRESERVE,
            source_id=SRC_PRESERVE,
            title="Title",
            url="https://example.com/preserve",
            summary=None,
            thumbnail_url=None,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        identity = RssArticleMetadata.create(
            id=RssArticleId(ART_PRESERVE),
            source_id=RssFeedId(SRC_PRESERVE),
            url=RssArticleUrl("https://example.com/preserve"),
        )
        metadata = RssArticleMetadata.create(
            title=RssArticleTitle("Updated Title"),
            summary=None,
            thumbnail_url=None,
        )
        article = RssArticle(identity=identity, metadata=metadata)

        # Act
        RssArticleMapper.update_model_from_domain(model, article)

        # Assert
        assert model.title == "Updated Title"
        assert model.summary is None
        assert model.thumbnail_url is None
