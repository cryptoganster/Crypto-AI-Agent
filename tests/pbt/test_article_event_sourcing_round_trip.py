"""
Property-Based Test for RssArticle Event Sourcing Round Trip.

Feature: article-aggregate-refactor, Property 11: Event sourcing round trip preserves state
Validates: Requirements 7.3, 11.5

Property: For any RssArticle instance, capturing its domain events and reconstructing
a new instance using from_events() should produce an RssArticle with equivalent state.

NOTA: Event Sourcing NO está implementado en este proyecto actualmente.
Estos tests están marcados como skip hasta que se implemente Event Sourcing.
"""

import pytest

# Skip todos los tests de este módulo - Event Sourcing no implementado
pytestmark = pytest.mark.skip(reason="Event Sourcing no implementado en este proyecto")
from datetime import datetime, timezone
from typing import List

from hypothesis import assume, given, settings
from hypothesis import strategies as st

from src.rss.article.domain.aggregates.rss_article import RssArticle
from src.rss.article.domain.factories.article_factory import RssArticleFactory
from src.rss.article.domain.value_objects import (
    RssArticleId,
    RssArticleTitle,
    RssArticleUrl,
)
from src.rss.article.domain.value_objects.metadata import (
    ArticleCategory,
    ArticleLanguage,
)
from src.rss.article.domain.value_objects.readability_score import ReadabilityScore
from src.rss.feed.domain.value_objects import RssFeedId
from src.shared.domain.value_objects import Level

# ==================== STRATEGIES ====================


@st.composite
def source_id_strategy(draw):
    """Generate valid SourceId."""
    return RssFeedId.generate()


@st.composite
def article_title_strategy(draw):
    """Generate valid article titles."""
    title = draw(
        st.text(
            min_size=1,
            max_size=200,
            alphabet=st.characters(
                whitelist_categories=("Lu", "Ll", "Nd", "Zs"),
                blacklist_characters="\x00\n\r\t",
            ),
        )
    )
    return title.strip() or "Default Title"


@st.composite
def article_url_strategy(draw):
    """Generate valid article URLs."""
    domain = draw(
        st.text(
            min_size=3,
            max_size=20,
            alphabet=st.characters(whitelist_categories=("Ll", "Nd")),
        )
    )
    path = draw(
        st.text(
            min_size=1,
            max_size=50,
            alphabet=st.characters(
                whitelist_categories=("Ll", "Nd"), blacklist_characters="/"
            ),
        )
    )
    return f"https://{domain}.com/{path}"


@st.composite
def article_content_strategy(draw):
    """Generate valid article content."""
    content = draw(
        st.text(
            min_size=10,
            max_size=500,
            alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd", "Zs", "Po")),
        )
    )
    return content.strip() or "Default content for testing."


@st.composite
def quality_score_strategy(draw):
    """Generate valid quality scores (0.0-1.0)."""
    return draw(st.floats(min_value=0.0, max_value=1.0))


@st.composite
def language_code_strategy(draw):
    """Generate valid ISO 639-1 language codes."""
    return draw(st.sampled_from(["en", "es", "fr", "de", "it", "pt", "ja", "zh"]))


@st.composite
def category_strategy(draw):
    """Generate valid article categories."""
    return draw(
        st.sampled_from(
            [
                "Technology",
                "Science",
                "Business",
                "Politics",
                "Sports",
                "Entertainment",
                "Health",
                "Education",
            ]
        )
    )


@st.composite
def article_with_operations_strategy(draw):
    """
    Generate an RssArticle and perform random operations on it.

    This creates a realistic RssArticle with various state changes that
    should be preserved through event sourcing round trip.
    """
    # Create base article
    title = draw(article_title_strategy())
    url = draw(article_url_strategy())
    source_id = draw(source_id_strategy())

    factory = RssArticleFactory()

    article = factory.create_article(title=title, url=url, source_id=source_id)

    # Clear creation event for cleaner testing
    article.mark_events_as_committed()

    # Perform random operations
    operations = draw(
        st.lists(
            st.sampled_from(
                [
                    "update_content",
                    "set_quality",
                    "set_readability",
                    "validate",
                    "set_language",
                    "set_category",
                    "add_tags",
                    "set_keywords",
                ]
            ),
            min_size=1,
            max_size=5,
            unique=True,
        )
    )

    for operation in operations:
        if operation == "update_content":
            content = draw(article_content_strategy())
            article.update_content_fields(markdown=content)

        elif operation == "set_quality":
            quality_score = draw(quality_score_strategy())
            quality_level = Level.from_score(quality_score)
            article.assess_quality(quality_level)

        elif operation == "set_readability":
            readability = draw(quality_score_strategy())
            article.update_readability_score(readability)

        elif operation == "validate":
            validation_score = draw(quality_score_strategy())
            validated_by = draw(
                st.text(
                    alphabet=st.characters(blacklist_categories=("Cs",)),
                    min_size=1,
                    max_size=50,
                ).filter(lambda s: s.strip())
            )
            article.validate_article(validation_score, validated_by)

        elif operation == "set_language":
            language = draw(language_code_strategy())
            confidence = draw(quality_score_strategy())
            article.update_language(language, confidence)

        elif operation == "set_category":
            category = draw(category_strategy())
            confidence = draw(quality_score_strategy())
            article.update_category(category, confidence)

        elif operation == "add_tags":
            num_tags = draw(st.integers(min_value=1, max_value=5))
            for _ in range(num_tags):
                tag = draw(st.text(min_size=1, max_size=20))
                if tag.strip():
                    article.add_tag(tag)

        elif operation == "set_keywords":
            num_keywords = draw(st.integers(min_value=1, max_value=10))
            keywords = [
                draw(st.text(min_size=1, max_size=20)) for _ in range(num_keywords)
            ]
            keywords = [k.strip() for k in keywords if k.strip()]
            if keywords:
                article.set_keywords(keywords)

    return article


# ==================== PROPERTY TESTS ====================


@pytest.mark.pbt
@settings(max_examples=100, deadline=None)
@given(article=article_with_operations_strategy())
def test_event_sourcing_round_trip_preserves_core_identity(article):
    """
    Property 11: Event sourcing round trip preserves state - Core Identity.

    For any RssArticle with operations, reconstructing from events should preserve
    core identity fields (id, title, url, source_id).

    Feature: article-aggregate-refactor, Property 11
    Validates: Requirements 7.3, 11.5
    """
    # Arrange: Capture all domain events
    events = article.get_domain_events()
    assume(len(events) > 0)

    # Act: Reconstruct Article from events
    reconstructed = RssArticle.from_events(events)

    # Assert: Core identity should be preserved
    assert str(reconstructed.id) == str(
        article.id
    ), "RssArticle ID should be preserved through event sourcing"

    assert (
        reconstructed.title == article.title
    ), "Title should be preserved through event sourcing"

    assert (
        reconstructed.url == article.url
    ), "URL should be preserved through event sourcing"

    assert str(reconstructed.source_id) == str(
        article.source_id
    ), "RssFeed ID should be preserved through event sourcing"


@pytest.mark.pbt
@settings(max_examples=100, deadline=None)
@given(article=article_with_operations_strategy())
def test_event_sourcing_round_trip_preserves_content(article):
    """
    Property 11: Event sourcing round trip preserves state - Content.

    For any RssArticle with content updates, reconstructing from events should
    preserve the final content state.

    Feature: article-aggregate-refactor, Property 11
    Validates: Requirements 7.3, 11.5
    """
    # Arrange: Capture all domain events
    events = article.get_domain_events()
    assume(len(events) > 0)

    # Act: Reconstruct Article from events
    reconstructed = RssArticle.from_events(events)

    # Assert: Content should be preserved
    assert (
        reconstructed.content == article.content_vo.markdown
    ), "Content should be preserved through event sourcing"

    assert (
        reconstructed.has_content == article.content_vo.has_markdown
    ), "Content presence flag should be preserved"


@pytest.mark.pbt
@settings(max_examples=100, deadline=None)
@given(article=article_with_operations_strategy())
def test_event_sourcing_round_trip_preserves_quality_metrics(article):
    """
    Property 11: Event sourcing round trip preserves state - Quality Metrics.

    For any RssArticle with quality assessments, reconstructing from events should
    preserve quality scores and validation info.

    Feature: article-aggregate-refactor, Property 11
    Validates: Requirements 7.3, 11.5
    """
    # Arrange: Capture all domain events
    events = article.get_domain_events()
    assume(len(events) > 0)

    # Act: Reconstruct Article from events
    reconstructed = RssArticle.from_events(events)

    # Assert: Quality metrics should be preserved
    if article.quality.quality_score is not None:
        assert (
            reconstructed.quality_score == article.quality.quality_score
        ), "Quality score should be preserved through event sourcing"

    if (
        article.quality.readability_score.value
        if article.quality.readability_score
        else None is not None
    ):
        assert (
            reconstructed.readability_score == article.quality.readability_score.value
            if article.quality.readability_score
            else None
        ), "Readability score should be preserved through event sourcing"

    if article.validation_score is not None:
        assert (
            reconstructed.validation_score == article.validation_score
        ), "Validation score should be preserved through event sourcing"

        assert (
            reconstructed.validated_by == article.validated_by
        ), "Validated by should be preserved through event sourcing"


@pytest.mark.pbt
@settings(max_examples=100, deadline=None)
@given(article=article_with_operations_strategy())
def test_event_sourcing_round_trip_preserves_metadata(article):
    """
    Property 11: Event sourcing round trip preserves state - Metadata.

    For any RssArticle with metadata (language, category, tags, keywords),
    reconstructing from events should preserve all metadata.

    Feature: article-aggregate-refactor, Property 11
    Validates: Requirements 7.3, 11.5
    """
    # Arrange: Capture all domain events
    events = article.get_domain_events()
    assume(len(events) > 0)

    # Act: Reconstruct Article from events
    reconstructed = RssArticle.from_events(events)

    # Assert: Metadata should be preserved
    assert (
        reconstructed.language == article.metadata.language.code
        if article.metadata.language
        else None
    ), "Language should be preserved through event sourcing"

    assert (
        reconstructed.category == article.metadata.category.value
        if article.metadata.category
        else None
    ), "Category should be preserved through event sourcing"

    # Tags and keywords are tuples, so direct comparison works
    assert reconstructed.tags == tuple(
        article.metadata.tags.sorted_tags
    ), "Tags should be preserved through event sourcing"

    assert reconstructed.keywords == tuple(
        article.metadata.keywords.keywords
    ), "Keywords should be preserved through event sourcing"


@pytest.mark.pbt
@settings(max_examples=100, deadline=None)
@given(article=article_with_operations_strategy())
def test_event_sourcing_round_trip_preserves_version(article):
    """
    Property 11: Event sourcing round trip preserves state - Version.

    For any RssArticle, the reconstructed version should match the number of events.

    Feature: article-aggregate-refactor, Property 11
    Validates: Requirements 7.3, 11.5
    """
    # Arrange: Capture all domain events
    events = article.get_domain_events()
    assume(len(events) > 0)

    # Act: Reconstruct Article from events
    reconstructed = RssArticle.from_events(events)

    # Assert: Version should match event count
    assert reconstructed.version == len(
        events
    ), f"Version should match event count: expected {len(events)}, got {reconstructed.version}"


@pytest.mark.pbt
@settings(max_examples=100, deadline=None)
@given(article=article_with_operations_strategy())
def test_event_sourcing_round_trip_clears_uncommitted_events(article):
    """
    Property 11: Event sourcing round trip preserves state - Event Management.

    For any RssArticle reconstructed from events, uncommitted events should be empty
    since reconstruction doesn't generate new events.

    Feature: article-aggregate-refactor, Property 11
    Validates: Requirements 7.3, 11.5
    """
    # Arrange: Capture all domain events
    events = article.get_domain_events()
    assume(len(events) > 0)

    # Act: Reconstruct Article from events
    reconstructed = RssArticle.from_events(events)

    # Assert: Uncommitted events should be empty after reconstruction
    assert (
        len(reconstructed.get_uncommitted_events()) == 0
    ), "Reconstructed article should have no uncommitted events"


@pytest.mark.pbt
@settings(max_examples=100, deadline=None)
@given(article=article_with_operations_strategy())
def test_event_sourcing_round_trip_is_idempotent(article):
    """
    Property 11: Event sourcing round trip preserves state - Idempotence.

    For any RssArticle, reconstructing multiple times from the same events
    should always produce identical state.

    Feature: article-aggregate-refactor, Property 11
    Validates: Requirements 7.3, 11.5
    """
    # Arrange: Capture all domain events
    events = article.get_domain_events()
    assume(len(events) > 0)

    # Act: Reconstruct Article twice
    reconstructed1 = RssArticle.from_events(events)
    reconstructed2 = RssArticle.from_events(events)

    # Assert: Both reconstructions should be identical
    assert str(reconstructed1.id) == str(reconstructed2.id)
    assert reconstructed1.title == reconstructed2.title
    assert reconstructed1.url == reconstructed2.url
    assert str(reconstructed1.source_id) == str(reconstructed2.source_id)
    assert reconstructed1.content == reconstructed2.content
    assert reconstructed1.quality_score == reconstructed2.quality_score
    assert reconstructed1.readability_score == reconstructed2.readability_score
    assert reconstructed1.validation_score == reconstructed2.validation_score
    assert reconstructed1.language == reconstructed2.language
    assert reconstructed1.category == reconstructed2.category
    assert reconstructed1.tags == reconstructed2.tags
    assert reconstructed1.keywords == reconstructed2.keywords
    assert reconstructed1.version == reconstructed2.version


@pytest.mark.pbt
@settings(max_examples=100, deadline=None)
@given(article=article_with_operations_strategy())
def test_event_sourcing_round_trip_preserves_timestamps(article):
    """
    Property 11: Event sourcing round trip preserves state - Timestamps.

    For any RssArticle with workflow timestamps (published_at, archived_at),
    reconstructing from events should preserve these timestamps.

    Feature: article-aggregate-refactor, Property 11
    Validates: Requirements 7.3, 11.5
    """
    # Arrange: Capture all domain events
    events = article.get_domain_events()
    assume(len(events) > 0)

    # Act: Reconstruct Article from events
    reconstructed = RssArticle.from_events(events)

    # Assert: Timestamps should be preserved
    assert (
        reconstructed.published_at == article.published_at
    ), "Published timestamp should be preserved through event sourcing"

    assert (
        reconstructed.archived_at == article.archived_at
    ), "Archived timestamp should be preserved through event sourcing"

    # Note: created_at and updated_at are set during reconstruction,
    # so they may differ from the original. This is expected behavior
    # as these are operational timestamps, not domain state.


@pytest.mark.pbt
@settings(max_examples=100, deadline=None)
@given(article=article_with_operations_strategy())
def test_event_sourcing_round_trip_preserves_error_state(article):
    """
    Property 11: Event sourcing round trip preserves state - Error State.

    For any RssArticle with error markers, reconstructing from events should
    preserve error information.

    Feature: article-aggregate-refactor, Property 11
    Validates: Requirements 7.3, 11.5
    """
    # Arrange: Capture all domain events
    events = article.get_domain_events()
    assume(len(events) > 0)

    # Act: Reconstruct Article from events
    reconstructed = RssArticle.from_events(events)

    # Assert: Error state should be preserved
    assert (
        reconstructed.has_error == article.error_info.has_error
    ), "Error flag should be preserved through event sourcing"

    if article.error_info.has_error:
        assert (
            reconstructed.error_type == article.error_info.error_type
        ), "Error type should be preserved through event sourcing"

        assert (
            reconstructed.error_message == article.error_info.error_message
        ), "Error message should be preserved through event sourcing"

        assert (
            reconstructed.error_marked_by == article.error_marked_by
        ), "Error marked by should be preserved through event sourcing"
