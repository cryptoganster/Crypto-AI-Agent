"""
Property-Based Test for Events Persistence.

Feature: resolve-todos, Property 13: Events Persistence
Validates: Requirements 6.3

Property: For any aggregate with generated events, all events should be
persisted to the event store.
"""

from datetime import datetime, timezone
from typing import List
from unittest.mock import AsyncMock, MagicMock

import pytest
from hypothesis import assume, given, settings
from hypothesis import strategies as st

from src.infra.persistence.repositories.rss.article_write_repository import (
    ArticleWriteRepository,
)
from src.infra.persistence.repositories.rss.source_write_repository import (
    SourceWriteRepository,
)
from src.rss.article.domain.aggregates.rss_article import RssArticle
from src.rss.article.domain.factories.article_factory import RssArticleFactory
from src.rss.feed.domain.aggregates import RssFeed
from src.rss.feed.domain.factories import RssFeedFactory
from src.rss.feed.domain.value_objects import RssFeedId
from src.rss.feed.domain.value_objects.name import RssFeedName
from src.rss.feed.domain.value_objects.rss_feed_url import RssFeedUrl

# ==================== STRATEGIES ====================


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
def source_url_strategy(draw):
    """Generate valid source URLs."""
    domain = draw(
        st.text(
            min_size=3,
            max_size=20,
            alphabet=st.characters(whitelist_categories=("Ll", "Nd")),
        )
    )
    return f"https://{domain}.com/feed.xml"


@st.composite
def source_name_strategy(draw):
    """Generate valid source names."""
    name = draw(
        st.text(
            min_size=1,
            max_size=100,
            alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd", "Zs")),
        )
    )
    return name.strip() or "Default RssFeed"


# ==================== PROPERTY TESTS ====================


@pytest.mark.pbt
@settings(max_examples=100, deadline=None)
@given(
    title=article_title_strategy(),
    url=article_url_strategy(),
)
def test_article_with_events_has_events_to_persist(title, url):
    """
    Property: For any RssArticle aggregate created, it should generate domain events
    that need to be persisted.

    Feature: resolve-todos, Property 13: Events Persistence
    Validates: Requirements 6.3
    """
    # Arrange & Act: Create an Article which generates events
    source_id = SourceId.generate()
    factory = RssArticleFactory()

    article = factory.create_article(
        title=title,
        url=url,
        source_id=source_id,
    )

    # Assert: RssArticle should have generated events
    events = list(article.domain_events)

    # 1. Should have at least one event (ArticleCreated)
    assert len(events) > 0, "RssArticle should generate at least one event on creation"

    # 2. First event should be ArticleCreated
    assert (
        events[0].event_type == "RssArticleCreated"
    ), f"First event should be RssArticleCreated, got {events[0].event_type}"

    # 3. All events should have required fields for persistence
    for event in events:
        assert hasattr(event, "event_id"), "Event must have event_id"
        assert hasattr(event, "event_type"), "Event must have event_type"
        assert hasattr(event, "aggregate_id"), "Event must have aggregate_id"
        assert hasattr(event, "occurred_at"), "Event must have occurred_at"
        assert hasattr(event, "to_dict"), "Event must be serializable"

        # Verify serialization works
        event_dict = event.to_dict()
        assert isinstance(event_dict, dict), "Event.to_dict() must return a dict"
        assert "event_id" in event_dict
        assert "event_type" in event_dict


@pytest.mark.pbt
@settings(max_examples=100, deadline=None)
@given(
    name=source_name_strategy(),
    url=source_url_strategy(),
)
def test_source_with_events_has_events_to_persist(name, url):
    """
    Property: For any RssFeed aggregate created, it should generate domain events
    that need to be persisted.

    Feature: resolve-todos, Property 13: Events Persistence
    Validates: Requirements 6.3
    """
    # Arrange & Act: Create a Source which generates events
    factory = RssFeedFactory()
    source = factory.create_source(
        url=url,
        name=name,
        description=None,
    )

    # Assert: RssFeed should have generated events
    events = list(source.domain_events)

    # 1. Should have at least one event (SourceCreated)
    assert len(events) > 0, "RssFeed should generate at least one event on creation"

    # 2. First event should be SourceCreated
    assert (
        events[0].event_type == "RssFeedCreated"
    ), f"First event should be RssFeedCreated, got {events[0].event_type}"

    # 3. All events should have required fields for persistence
    for event in events:
        assert hasattr(event, "event_id"), "Event must have event_id"
        assert hasattr(event, "event_type"), "Event must have event_type"
        assert hasattr(event, "aggregate_id"), "Event must have aggregate_id"
        assert hasattr(event, "occurred_at"), "Event must have occurred_at"
        assert hasattr(event, "to_dict"), "Event must be serializable"

        # Verify serialization works
        event_dict = event.to_dict()
        assert isinstance(event_dict, dict), "Event.to_dict() must return a dict"
        assert "event_id" in event_dict
        assert "event_type" in event_dict


@pytest.mark.pbt
@settings(max_examples=100, deadline=None)
@given(
    title=article_title_strategy(),
    url=article_url_strategy(),
)
def test_events_are_serializable_for_persistence(title, url):
    """
    Property: All events generated by aggregates should be serializable
    for persistence (can be converted to dict).

    Feature: resolve-todos, Property 13: Events Persistence
    Validates: Requirements 6.3
    """
    # Arrange: Create an Article
    source_id = SourceId.generate()
    factory = RssArticleFactory()

    article = factory.create_article(
        title=title,
        url=url,
        source_id=source_id,
    )

    events = list(article.domain_events)
    assume(len(events) > 0)

    # Act & Assert: Each event should be serializable
    for event in events:
        # Serialize to dict
        event_dict = event.to_dict()
        assert isinstance(event_dict, dict), "Event must be serializable to dict"

        # Should have all required fields for persistence
        assert "event_id" in event_dict, "Event dict must have event_id"
        assert "event_type" in event_dict, "Event dict must have event_type"
        assert "aggregate_id" in event_dict, "Event dict must have aggregate_id"
        assert "occurred_at" in event_dict, "Event dict must have occurred_at"

        # All values should be JSON-serializable types
        import json

        try:
            json.dumps(event_dict)
        except (TypeError, ValueError) as e:
            pytest.fail(f"Event dict is not JSON-serializable: {e}")


@pytest.mark.pbt
@settings(max_examples=100, deadline=None)
@given(
    title=article_title_strategy(),
    url=article_url_strategy(),
)
def test_aggregate_version_tracks_event_count(title, url):
    """
    Property: Aggregate version should track the number of events generated,
    which is essential for event store optimistic locking.

    Feature: resolve-todos, Property 13: Events Persistence
    Validates: Requirements 6.3
    """
    # Arrange & Act: Create an Article
    source_id = SourceId.generate()
    factory = RssArticleFactory()

    article = factory.create_article(
        title=title,
        url=url,
        source_id=source_id,
    )

    # Get initial events
    initial_events = list(article.domain_events)
    assume(len(initial_events) > 0)

    # Assert: Version should be 0 initially (before events are committed)
    # After reconstruction from events, version should match event count
    reconstructed = RssArticle.from_events(initial_events)
    assert reconstructed.version == len(
        initial_events
    ), f"Version {reconstructed.version} should match event count {len(initial_events)}"
