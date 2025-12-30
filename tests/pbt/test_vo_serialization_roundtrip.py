"""Property-based tests para VO serialization round-trip.

Tests que verifican que los VOs pueden ser serializados y deserializados sin pérdida de datos.
"""

from datetime import datetime, timezone
from uuid import uuid4

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from src.rss.article.domain.aggregates.rss_article import RssArticle
from src.rss.article.domain.factories.article_factory import RssArticleFactory
from src.rss.article.domain.value_objects import RssArticleId
from src.rss.article.infra.persistence.mappers import RssArticleMapper
from src.rss.feed.domain.value_objects import RssFeedId


# Estrategia para generar Articles válidos
@st.composite
def valid_article(draw):
    """Genera Article aggregate válido con VOs."""
    # Crear article básico
    article_id = RssArticleId(str(uuid4()))
    source_id = RssFeedId(str(uuid4()))
    title_words = draw(
        st.lists(
            st.text(
                min_size=1,
                max_size=20,
                alphabet=st.characters(whitelist_categories=("Ll", "Lu", "Nd")),
            ),
            min_size=1,
            max_size=10,
        )
    )
    title = " ".join(title_words)
    domain = draw(
        st.text(
            min_size=3,
            max_size=20,
            alphabet=st.characters(whitelist_categories=("Ll",)),
        )
    )
    path = draw(
        st.text(
            min_size=1,
            max_size=50,
            alphabet=st.characters(whitelist_categories=("Ll", "Nd")),
        )
    )
    url = f"https://{domain}.com/{path}"

    factory = RssArticleFactory()

    article = factory.create_article(
        title=title, url=url, source_id=source_id, article_id=article_id
    )

    # Poblar VOs con datos aleatorios
    from src.domain.value_objects.article.content_vo.markdown_metrics import (
        RssArticleMetrics,
    )
    from src.rss.article.domain.value_objects.analysis import (
        RssArticleDuplicate as RssArticleDuplicate,
    )
    from src.rss.article.domain.value_objects.error_info import ErrorInfo
    from src.rss.article.domain.value_objects.metadata import RssArticleMetadata
    from src.rss.article.domain.value_objects.metadata.content import RssArticleContent
    from src.rss.article.domain.value_objects.quality_assessment import (
        QualityAssessment,
    )
    from src.rss.article.domain.value_objects.rss_metadata import RssMetadata

    # ArticleContent
    content_markdown = draw(st.one_of(st.none(), st.text(min_size=1, max_size=1000)))
    content_plaintext = draw(st.one_of(st.none(), st.text(min_size=1, max_size=1000)))
    if content_markdown or content_plaintext:
        article._content = RssArticleContent(
            markdown=content_markdown,
            plaintext=content_plaintext,
            scrapped=None,
            excerpt=None,
        )

    # ArticleMetrics
    word_count = draw(st.one_of(st.none(), st.integers(min_value=0, max_value=10000)))
    reading_time = draw(st.one_of(st.none(), st.integers(min_value=0, max_value=120)))
    if word_count is not None or reading_time is not None:
        article._metrics = RssArticleMetrics.create(
            word_count=word_count, reading_time_minutes=reading_time
        )

    # RssMetadata
    rss_guid = draw(st.one_of(st.none(), st.text(min_size=1, max_size=100)))
    pub_date_naive = draw(
        st.one_of(
            st.none(),
            st.datetimes(
                min_value=datetime(2020, 1, 1), max_value=datetime(2024, 12, 31)
            ),
        )
    )
    pub_date = pub_date_naive.replace(tzinfo=timezone.utc) if pub_date_naive else None
    if rss_guid or pub_date:
        article._rss_metadata = RssMetadata.create(
            guid=rss_guid, pub_date=pub_date, description=None
        )

    # ArticleDuplicate
    is_duplicate = draw(st.booleans())
    if is_duplicate:
        article._duplication = RssArticleDuplicate.duplicate_of(
            RssArticleId(str(uuid4()))
        )

    return article


@given(article=valid_article())
@settings(suppress_health_check=[HealthCheck.too_slow], max_examples=50)
def test_vo_serialization_roundtrip_property(article):
    """
    Property 9: VO serialization round-trip

    For any Value Object instance, serializing it to a dictionary and then
    deserializing back must produce an equivalent Value Object.

    **Feature: refactor-article-aggregate, Property 9: VO serialization round-trip**
    **Validates: Requirements 7.2**
    """
    # Act - Serializar a modelo ORM y luego deserializar de vuelta
    model = RssArticleMapper.to_model(article)
    reconstructed = RssArticleMapper.to_domain(model)

    # Assert - Verificar que los VOs son equivalentes

    # ArticleContent VO
    assert reconstructed._content.markdown == article._content.markdown
    assert reconstructed._content.plaintext == article._content.plaintext
    assert reconstructed._content.scrapped == article._content.scrapped
    assert reconstructed._content.excerpt == article._content.excerpt

    # ArticleMetrics VO
    if article._metrics.word_count:
        assert reconstructed._metrics.word_count is not None
        assert (
            reconstructed._metrics.word_count.value == article._metrics.word_count.value
        )
    if article._metrics.reading_time:
        assert reconstructed._metrics.reading_time is not None
        assert (
            reconstructed._metrics.reading_time.minutes
            == article._metrics.reading_time.minutes
        )

    # RssMetadata VO
    assert reconstructed._rss_metadata.guid == article._rss_metadata.guid
    assert reconstructed._rss_metadata.pub_date == article._rss_metadata.pub_date
    assert reconstructed._rss_metadata.description == article._rss_metadata.description

    # ArticleDuplicate VO
    assert reconstructed._duplication.is_duplicate == article._duplication.is_duplicate
    if article._duplication.is_duplicate:
        assert str(reconstructed._duplication.duplicate_of_article_id) == str(
            article._duplication.duplicate_of_article_id
        )

    # ErrorInfo VO
    assert reconstructed._error.has_error == article._error.has_error


@given(article=valid_article())
def test_vo_serialization_preserves_identity(article):
    """
    Verificar que la serialización preserva la identidad del aggregate.

    El ID y otros campos core deben ser idénticos después del round-trip.
    """
    # Act
    model = RssArticleMapper.to_model(article)
    reconstructed = RssArticleMapper.to_domain(model)

    # Assert
    assert str(reconstructed.id) == str(article.id)
    assert str(reconstructed.source_id) == str(article.source_id)
    assert reconstructed.title == article.title
    assert reconstructed.url == article.url


@given(article=valid_article())
def test_vo_serialization_preserves_timestamps(article):
    """
    Verificar que la serialización preserva los timestamps.
    """
    # Act
    model = RssArticleMapper.to_model(article)
    reconstructed = RssArticleMapper.to_domain(model)

    # Assert
    assert reconstructed.created_at == article.created_at
    assert reconstructed.updated_at == article.updated_at
    assert reconstructed.version == article.version
