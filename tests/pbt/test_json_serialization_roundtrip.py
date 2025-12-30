"""Property-based tests para JSON serialization round-trip.

Tests que verifican que los VOs pueden ser serializados a JSON y deserializados sin pérdida de datos.
"""

import json
from datetime import datetime, timezone
from uuid import uuid4

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from src.rss.article.domain.value_objects.analysis import (
    RssArticleDuplicate as RssArticleDuplicate,
)
from src.rss.article.domain.value_objects.analysis import (
    RssArticleMetrics as RssArticleMetrics,
)
from src.rss.article.domain.value_objects.error_info import ErrorInfo
from src.rss.article.domain.value_objects.metadata import RssArticleMetadata
from src.rss.article.domain.value_objects.metadata.content import RssArticleContent
from src.rss.article.domain.value_objects.quality_assessment import QualityAssessment
from src.rss.article.domain.value_objects.rss_metadata import RssMetadata


# Estrategias para generar VOs
@st.composite
def article_content_vo(draw):
    """Genera ArticleContent VO válido."""
    markdown = draw(st.one_of(st.none(), st.text(min_size=1, max_size=500)))
    plaintext = draw(st.one_of(st.none(), st.text(min_size=1, max_size=500)))
    scrapped = draw(st.one_of(st.none(), st.text(min_size=1, max_size=500)))
    excerpt = draw(st.one_of(st.none(), st.text(min_size=1, max_size=200)))

    # Asegurar que al menos un campo no sea None
    if all(x is None for x in [markdown, plaintext, scrapped, excerpt]):
        markdown = "Default content"

    return RssArticleContent(
        markdown=markdown, plaintext=plaintext, scrapped=scrapped, excerpt=excerpt
    )


@st.composite
def content_metrics_vo(draw):
    """Genera ArticleMetrics VO válido."""
    word_count = draw(st.one_of(st.none(), st.integers(min_value=0, max_value=10000)))
    reading_time = draw(st.one_of(st.none(), st.integers(min_value=0, max_value=120)))

    return RssArticleMetrics.create(
        word_count=word_count, reading_time_minutes=reading_time
    )


@st.composite
def rss_metadata_vo(draw):
    """Genera RssMetadata VO válido."""
    guid = draw(st.one_of(st.none(), st.text(min_size=1, max_size=100)))
    pub_date_naive = draw(
        st.one_of(
            st.none(),
            st.datetimes(
                min_value=datetime(2020, 1, 1), max_value=datetime(2024, 12, 31)
            ),
        )
    )
    pub_date = pub_date_naive.replace(tzinfo=timezone.utc) if pub_date_naive else None
    description = draw(st.one_of(st.none(), st.text(min_size=1, max_size=500)))

    return RssMetadata.create(guid=guid, pub_date=pub_date, description=description)


@st.composite
def duplication_info_vo(draw):
    """Genera ArticleDuplicate VO válido."""
    is_duplicate = draw(st.booleans())

    if is_duplicate:
        from src.rss.article.domain.value_objects import RssArticleId

        return RssArticleDuplicate.duplicate_of(RssArticleId(str(uuid4())))
    else:
        return RssArticleDuplicate.not_duplicate()


@st.composite
def error_info_vo(draw):
    """Genera ErrorInfo VO válido."""
    has_error = draw(st.booleans())

    if has_error:
        error_type = draw(
            st.text(
                min_size=1,
                max_size=50,
                alphabet=st.characters(whitelist_categories=("Ll", "Lu")),
            )
        )
        error_message = draw(
            st.text(
                min_size=1,
                max_size=200,
                alphabet=st.characters(whitelist_categories=("Ll", "Lu", "Nd")),
            )
        )
        marked_by = draw(
            st.text(
                min_size=1,
                max_size=50,
                alphabet=st.characters(whitelist_categories=("Ll", "Lu")),
            )
        )
        marked_at_naive = draw(
            st.datetimes(
                min_value=datetime(2020, 1, 1), max_value=datetime(2024, 12, 31)
            )
        )
        marked_at = marked_at_naive.replace(tzinfo=timezone.utc)

        return ErrorInfo.create_error(
            error_type=error_type,
            error_message=error_message,
            marked_by=marked_by,
            marked_at=marked_at,
        )
    else:
        return ErrorInfo.no_error()


@given(vo=article_content_vo())
@settings(max_examples=100)
def test_article_content_json_roundtrip(vo):
    """
    Property 11: JSON serialization round-trip (RssArticleContent)

    For any RssArticleContent VO, serializing to JSON and deserializing back
    must produce an equivalent VO.

    **Feature: refactor-article-aggregate, Property 11: JSON serialization round-trip**
    **Validates: Requirements 7.5**
    """
    # Act - Serializar a dict (JSON-compatible)
    vo_dict = {
        "markdown": vo.markdown,
        "plaintext": vo.plaintext,
        "scrapped": vo.scrapped,
        "excerpt": vo.excerpt,
    }

    # Serializar a JSON y deserializar
    json_str = json.dumps(vo_dict)
    deserialized_dict = json.loads(json_str)

    # Reconstruir VO
    reconstructed = RssArticleContent(
        markdown=deserialized_dict["markdown"],
        plaintext=deserialized_dict["plaintext"],
        scrapped=deserialized_dict["scrapped"],
        excerpt=deserialized_dict["excerpt"],
    )

    # Assert - Verificar equivalencia
    assert reconstructed.markdown == vo.markdown
    assert reconstructed.plaintext == vo.plaintext
    assert reconstructed.scrapped == vo.scrapped
    assert reconstructed.excerpt == vo.excerpt


@given(vo=content_metrics_vo())
@settings(max_examples=100)
def test_content_metrics_json_roundtrip(vo):
    """
    Property 11: JSON serialization round-trip (RssArticleMetrics)

    For any RssArticleMetrics VO, serializing to JSON and deserializing back
    must produce an equivalent VO.

    **Feature: refactor-article-aggregate, Property 11: JSON serialization round-trip**
    **Validates: Requirements 7.5**
    """
    # Act - Serializar a dict (JSON-compatible)
    vo_dict = {
        "word_count": vo.word_count.value if vo.word_count else None,
        "reading_time_minutes": vo.reading_time.minutes if vo.reading_time else None,
    }

    # Serializar a JSON y deserializar
    json_str = json.dumps(vo_dict)
    deserialized_dict = json.loads(json_str)

    # Reconstruir VO
    reconstructed = RssArticleMetrics.create(
        word_count=deserialized_dict["word_count"],
        reading_time_minutes=deserialized_dict["reading_time_minutes"],
    )

    # Assert - Verificar equivalencia
    if vo.word_count:
        assert reconstructed.word_count is not None
        assert reconstructed.word_count.value == vo.word_count.value
    else:
        assert reconstructed.word_count is None

    if vo.reading_time:
        assert reconstructed.reading_time is not None
        assert reconstructed.reading_time.minutes == vo.reading_time.minutes
    else:
        assert reconstructed.reading_time is None


@given(vo=rss_metadata_vo())
@settings(max_examples=100)
def test_rss_metadata_json_roundtrip(vo):
    """
    Property 11: JSON serialization round-trip (RssMetadata)

    For any RssMetadata VO, serializing to JSON and deserializing back
    must produce an equivalent VO.

    **Feature: refactor-article-aggregate, Property 11: JSON serialization round-trip**
    **Validates: Requirements 7.5**
    """
    # Act - Serializar a dict (JSON-compatible)
    vo_dict = {
        "guid": vo.guid,
        "pub_date": vo.pub_date.isoformat() if vo.pub_date else None,
        "description": vo.description,
    }

    # Serializar a JSON y deserializar
    json_str = json.dumps(vo_dict)
    deserialized_dict = json.loads(json_str)

    # Reconstruir VO
    pub_date = (
        datetime.fromisoformat(deserialized_dict["pub_date"])
        if deserialized_dict["pub_date"]
        else None
    )
    reconstructed = RssMetadata.create(
        guid=deserialized_dict["guid"],
        pub_date=pub_date,
        description=deserialized_dict["description"],
    )

    # Assert - Verificar equivalencia
    assert reconstructed.guid == vo.guid
    assert reconstructed.pub_date == vo.pub_date
    assert reconstructed.description == vo.description


@given(vo=duplication_info_vo())
@settings(max_examples=100)
def test_duplication_info_json_roundtrip(vo):
    """
    Property 11: JSON serialization round-trip (RssArticleDuplicate)

    For any RssArticleDuplicate VO, serializing to JSON and deserializing back
    must produce an equivalent VO.

    **Feature: refactor-article-aggregate, Property 11: JSON serialization round-trip**
    **Validates: Requirements 7.5**
    """
    # Act - Serializar a dict (JSON-compatible)
    vo_dict = {
        "is_duplicate": vo.is_duplicate,
        "duplicate_of_article_id": (
            str(vo.duplicate_of_article_id) if vo.duplicate_of_article_id else None
        ),
    }

    # Serializar a JSON y deserializar
    json_str = json.dumps(vo_dict)
    deserialized_dict = json.loads(json_str)

    # Reconstruir VO
    from src.rss.article.domain.value_objects import RssArticleId

    if (
        deserialized_dict["is_duplicate"]
        and deserialized_dict["duplicate_of_article_id"]
    ):
        reconstructed = RssArticleDuplicate.duplicate_of(
            RssArticleId(deserialized_dict["duplicate_of_article_id"])
        )
    else:
        reconstructed = RssArticleDuplicate.not_duplicate()

    # Assert - Verificar equivalencia
    assert reconstructed.is_duplicate == vo.is_duplicate
    if vo.is_duplicate:
        assert str(reconstructed.duplicate_of_article_id) == str(
            vo.duplicate_of_article_id
        )


@given(vo=error_info_vo())
@settings(max_examples=100)
def test_error_info_json_roundtrip(vo):
    """
    Property 11: JSON serialization round-trip (ErrorInfo)

    For any ErrorInfo VO, serializing to JSON and deserializing back
    must produce an equivalent VO.

    **Feature: refactor-article-aggregate, Property 11: JSON serialization round-trip**
    **Validates: Requirements 7.5**
    """
    # Act - Serializar a dict (JSON-compatible)
    vo_dict = {
        "has_error": vo.has_error,
        "error_type": vo.error_type,
        "error_message": vo.error_message,
        "error_marked_by": vo.error_marked_by,
        "error_marked_at": (
            vo.error_marked_at.isoformat() if vo.error_marked_at else None
        ),
    }

    # Serializar a JSON y deserializar
    json_str = json.dumps(vo_dict)
    deserialized_dict = json.loads(json_str)

    # Reconstruir VO
    if deserialized_dict["has_error"]:
        marked_at = (
            datetime.fromisoformat(deserialized_dict["error_marked_at"])
            if deserialized_dict["error_marked_at"]
            else None
        )
        reconstructed = ErrorInfo.create_error(
            error_type=deserialized_dict["error_type"],
            error_message=deserialized_dict["error_message"],
            marked_by=deserialized_dict["error_marked_by"],
            marked_at=marked_at,
        )
    else:
        reconstructed = ErrorInfo.no_error()

    # Assert - Verificar equivalencia
    assert reconstructed.has_error == vo.has_error
    if vo.has_error:
        assert reconstructed.error_type == vo.error_type
        assert reconstructed.error_message == vo.error_message
        assert reconstructed.error_marked_by == vo.error_marked_by
        assert reconstructed.error_marked_at == vo.error_marked_at
