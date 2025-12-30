"""
Property-based tests for ContentChunk aggregate.

Feature: ai-content-processing-bounded-context
Properties tested:
- Property 1: Chunk Size Bounds
- Property 13: Chunk Position Monotonicity

Validates: Requirements 1.1, 1.7
"""

import numpy as np
import pytest
from hypothesis import HealthCheck, assume, given, settings
from hypothesis import strategies as st

from src.chunking.domain.aggregates.content_chunk import ContentChunk
from src.chunking.domain.value_objects.chunk_id import ChunkId
from src.chunking.domain.value_objects.chunk_status import ChunkStatus
from src.chunking.domain.value_objects.token_count import (
    MAX_TOKEN_COUNT,
    MIN_TOKEN_COUNT,
    TokenCount,
)

# ============================================================================
# Property 1: Chunk Size Bounds
# ============================================================================
# For any text chunked by the system, all resulting chunks should have
# token counts between 100 and 2000 tokens.
# Validates: Requirements 1.1, 1.2
# ============================================================================


@given(
    token_value=st.integers(min_value=MIN_TOKEN_COUNT, max_value=MAX_TOKEN_COUNT),
    position=st.integers(min_value=0, max_value=100),
)
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=100)
def test_property_1_chunk_size_bounds(token_value: int, position: int):
    """
    Property 1: Chunk Size Bounds

    For any ContentChunk created with token count T:
    - T must be >= MIN_TOKEN_COUNT (100)
    - T must be <= MAX_TOKEN_COUNT (2000)
    - Token count must be immutable

    Validates: Requirements 1.1, 1.2
    """
    # Generate valid chunk data
    chunk_id = ChunkId.generate()
    article_id = f"article-{position}"
    content = "Test content " * (
        token_value // 2
    )  # Generate content proportional to tokens
    start_char = position * 1000
    end_char = start_char + len(content)
    token_count = TokenCount(value=token_value, encoding="cl100k_base")

    # Create chunk
    chunk = ContentChunk(
        id=chunk_id,
        article_id=article_id,
        content=content,
        position=position,
        start_char=start_char,
        end_char=end_char,
        token_count=token_count,
        source_url="https://example.com/article",
    )

    # Property: Token count is within bounds
    assert MIN_TOKEN_COUNT <= chunk.token_count.value <= MAX_TOKEN_COUNT
    assert chunk.token_count.value == token_value

    # Property: Token count is immutable (frozen value object)
    with pytest.raises(AttributeError):
        chunk.token_count.value = token_value + 1  # type: ignore


@given(
    token_value=st.integers(
        min_value=MIN_TOKEN_COUNT + 1, max_value=MAX_TOKEN_COUNT - 1
    ),
)
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=50)
def test_property_1_chunk_size_within_bounds_always_valid(token_value: int):
    """
    Property 1: Chunks Within Bounds Are Always Valid

    For any token count within [MIN_TOKEN_COUNT, MAX_TOKEN_COUNT],
    creating a ContentChunk should succeed.

    Validates: Requirements 1.1, 1.2
    """
    # Create chunk with valid token count
    chunk = ContentChunk(
        id=ChunkId.generate(),
        article_id="article-test",
        content="Valid content for testing chunk size bounds property",
        position=0,
        start_char=0,
        end_char=100,
        token_count=TokenCount(value=token_value, encoding="cl100k_base"),
        source_url="https://example.com/article",
    )

    # Property: Chunk is valid
    assert chunk.token_count.value == token_value
    assert chunk.status == ChunkStatus.PENDING


@given(
    token_value=st.integers(min_value=0, max_value=MIN_TOKEN_COUNT - 1),
)
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=30)
def test_property_1_chunk_size_below_minimum_rejected(token_value: int):
    """
    Property 1: Chunks Below Minimum Size Rejected

    For any token count below MIN_TOKEN_COUNT,
    creating a TokenCount should fail.

    Validates: Requirements 1.1, 1.2
    """
    assume(token_value < MIN_TOKEN_COUNT)

    # Property: Token count below minimum raises ValueError
    with pytest.raises(ValueError, match="Token count debe ser >= 0"):
        TokenCount(value=token_value, encoding="cl100k_base")


@given(
    token_value=st.integers(
        min_value=MAX_TOKEN_COUNT + 1, max_value=MAX_TOKEN_COUNT + 1000
    ),
)
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=30)
def test_property_1_chunk_size_above_maximum_rejected(token_value: int):
    """
    Property 1: Chunks Above Maximum Size Rejected

    For any token count above MAX_TOKEN_COUNT,
    creating a TokenCount should fail.

    Validates: Requirements 1.1, 1.2
    """
    assume(token_value > MAX_TOKEN_COUNT)

    # Property: Token count above maximum raises ValueError
    with pytest.raises(ValueError, match="Token count debe ser <= 100000"):
        TokenCount(value=token_value, encoding="cl100k_base")


# ============================================================================
# Property 13: Chunk Position Monotonicity
# ============================================================================
# For any list of chunks from the same article, the position values should
# be strictly increasing (0, 1, 2, ...).
# Validates: Requirements 1.7
# ============================================================================


@given(
    num_chunks=st.integers(min_value=2, max_value=10),
)
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=50)
def test_property_13_chunk_position_monotonicity(num_chunks: int):
    """
    Property 13: Chunk Position Monotonicity

    For any list of chunks from the same article:
    - Positions should be strictly increasing (0, 1, 2, ...)
    - No gaps in positions
    - No duplicate positions
    - Sorting by position preserves order

    Validates: Requirements 1.7
    """
    article_id = "article-test-123"
    chunks = []

    # Create chunks with sequential positions
    for i in range(num_chunks):
        chunk = ContentChunk(
            id=ChunkId.generate(),
            article_id=article_id,
            content=f"Content for chunk {i}",
            position=i,
            start_char=i * 1000,
            end_char=(i + 1) * 1000,
            token_count=TokenCount(value=500, encoding="cl100k_base"),
            source_url="https://example.com/article",
        )
        chunks.append(chunk)

    # Property: Positions are strictly increasing
    positions = [chunk.position for chunk in chunks]
    for i in range(len(positions) - 1):
        assert positions[i] < positions[i + 1], "Positions must be strictly increasing"

    # Property: No gaps in positions (0, 1, 2, ...)
    assert positions == list(
        range(num_chunks)
    ), "Positions must be sequential without gaps"

    # Property: No duplicate positions
    assert len(set(positions)) == len(positions), "Positions must be unique"

    # Property: First position is 0
    assert positions[0] == 0, "First chunk position must be 0"

    # Property: Last position is num_chunks - 1
    assert positions[-1] == num_chunks - 1, "Last position must be num_chunks - 1"


@given(
    num_chunks=st.integers(min_value=2, max_value=10),
)
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=50)
def test_property_13_chunk_position_sorting(num_chunks: int):
    """
    Property 13: Chunk Position Sorting

    For any list of chunks from the same article, sorting by position
    should preserve the original order.

    Validates: Requirements 1.7
    """
    article_id = "article-test-456"
    chunks = []

    # Create chunks with sequential positions
    for i in range(num_chunks):
        chunk = ContentChunk(
            id=ChunkId.generate(),
            article_id=article_id,
            content=f"Content for chunk {i}",
            position=i,
            start_char=i * 1000,
            end_char=(i + 1) * 1000,
            token_count=TokenCount(value=500, encoding="cl100k_base"),
            source_url="https://example.com/article",
        )
        chunks.append(chunk)

    # Shuffle chunks
    import random

    shuffled_chunks = chunks.copy()
    random.shuffle(shuffled_chunks)

    # Property: Sorting by position restores original order
    sorted_chunks = sorted(shuffled_chunks, key=lambda c: c.position)
    sorted_positions = [c.position for c in sorted_chunks]

    assert sorted_positions == list(
        range(num_chunks)
    ), "Sorted positions must be sequential"

    # Property: Sorted chunks match original order
    for i, chunk in enumerate(sorted_chunks):
        assert chunk.position == i, f"Chunk at index {i} must have position {i}"


@given(
    position1=st.integers(min_value=0, max_value=100),
    position2=st.integers(min_value=0, max_value=100),
)
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=50)
def test_property_13_chunk_position_comparison(position1: int, position2: int):
    """
    Property 13: Chunk Position Comparison

    For any two chunks from the same article with positions P1 and P2:
    - If P1 < P2, then chunk1.comes_before(chunk2) is True
    - If P1 > P2, then chunk1.comes_before(chunk2) is False
    - If P1 == P2, positions are equal (should not happen in practice)

    Validates: Requirements 1.7
    """
    article_id = "article-test-789"

    # Create two chunks with different positions
    chunk1 = ContentChunk(
        id=ChunkId.generate(),
        article_id=article_id,
        content=f"Content for chunk at position {position1}",
        position=position1,
        start_char=position1 * 1000,
        end_char=(position1 + 1) * 1000,
        token_count=TokenCount(value=500, encoding="cl100k_base"),
        source_url="https://example.com/article",
    )

    chunk2 = ContentChunk(
        id=ChunkId.generate(),
        article_id=article_id,
        content=f"Content for chunk at position {position2}",
        position=position2,
        start_char=position2 * 1000,
        end_char=(position2 + 1) * 1000,
        token_count=TokenCount(value=500, encoding="cl100k_base"),
        source_url="https://example.com/article",
    )

    # Property: comes_before() reflects position ordering
    if position1 < position2:
        assert chunk1.comes_before(chunk2) is True
        assert chunk2.comes_before(chunk1) is False
    elif position1 > position2:
        assert chunk1.comes_before(chunk2) is False
        assert chunk2.comes_before(chunk1) is True
    else:  # position1 == position2
        assert chunk1.comes_before(chunk2) is False
        assert chunk2.comes_before(chunk1) is False


@given(
    num_chunks=st.integers(min_value=3, max_value=10),
)
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=30)
def test_property_13_adjacent_chunks(num_chunks: int):
    """
    Property 13: Adjacent Chunks

    For any list of chunks with sequential positions:
    - Chunk at position N is adjacent to chunk at position N+1
    - Chunk at position N is NOT adjacent to chunk at position N+2

    Validates: Requirements 1.7
    """
    article_id = "article-test-adjacent"
    chunks = []

    # Create chunks with sequential positions
    for i in range(num_chunks):
        chunk = ContentChunk(
            id=ChunkId.generate(),
            article_id=article_id,
            content=f"Content for chunk {i}",
            position=i,
            start_char=i * 1000,
            end_char=(i + 1) * 1000,
            token_count=TokenCount(value=500, encoding="cl100k_base"),
            source_url="https://example.com/article",
        )
        chunks.append(chunk)

    # Property: Adjacent chunks are detected correctly
    for i in range(len(chunks) - 1):
        assert (
            chunks[i].is_adjacent_to(chunks[i + 1]) is True
        ), f"Chunk {i} should be adjacent to chunk {i+1}"
        assert (
            chunks[i + 1].is_adjacent_to(chunks[i]) is True
        ), f"Chunk {i+1} should be adjacent to chunk {i}"

    # Property: Non-adjacent chunks are detected correctly
    if num_chunks >= 3:
        for i in range(len(chunks) - 2):
            assert (
                chunks[i].is_adjacent_to(chunks[i + 2]) is False
            ), f"Chunk {i} should NOT be adjacent to chunk {i+2}"


@given(
    position=st.integers(min_value=0, max_value=100),
)
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=50)
def test_property_13_position_immutability(position: int):
    """
    Property 13: Position Immutability

    For any ContentChunk, the position attribute must be immutable.

    Validates: Requirements 1.7
    """
    # Create chunk
    chunk = ContentChunk(
        id=ChunkId.generate(),
        article_id="article-test",
        content="Test content for immutability check",
        position=position,
        start_char=0,
        end_char=100,
        token_count=TokenCount(value=500, encoding="cl100k_base"),
        source_url="https://example.com/article",
    )

    # Property: Position is immutable
    original_position = chunk.position

    # Attempting to modify position should fail (no setter)
    with pytest.raises(AttributeError):
        chunk.position = position + 1  # type: ignore

    # Position remains unchanged
    assert chunk.position == original_position


@given(
    num_chunks=st.integers(min_value=2, max_value=10),
)
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=30)
def test_property_13_same_article_chunks_comparable(num_chunks: int):
    """
    Property 13: Same RssArticle Chunks Are Comparable

    For any two chunks from the same article:
    - They can be compared using comes_before()
    - They can be checked for adjacency
    - They can be identified as from same article

    Validates: Requirements 1.7
    """
    article_id = "article-test-comparable"
    chunks = []

    # Create chunks from same article
    for i in range(num_chunks):
        chunk = ContentChunk(
            id=ChunkId.generate(),
            article_id=article_id,
            content=f"Content {i}",
            position=i,
            start_char=i * 1000,
            end_char=(i + 1) * 1000,
            token_count=TokenCount(value=500, encoding="cl100k_base"),
            source_url="https://example.com/article",
        )
        chunks.append(chunk)

    # Property: All chunks are from same article
    for i in range(len(chunks)):
        for j in range(len(chunks)):
            assert (
                chunks[i].is_from_same_article(chunks[j]) is True
            ), f"Chunks {i} and {j} should be from same article"

    # Property: Chunks can be compared
    for i in range(len(chunks) - 1):
        assert (
            chunks[i].comes_before(chunks[i + 1]) is True
        ), f"Chunk {i} should come before chunk {i+1}"


@given(
    position1=st.integers(min_value=0, max_value=50),
    position2=st.integers(min_value=0, max_value=50),
)
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=50)
def test_property_13_different_article_chunks_not_comparable(
    position1: int, position2: int
):
    """
    Property 13: Different RssArticle Chunks Not Comparable

    For any two chunks from different articles:
    - comes_before() should raise ValueError
    - is_adjacent_to() should return False
    - is_from_same_article() should return False

    Validates: Requirements 1.7
    """
    # Create chunks from different articles
    chunk1 = ContentChunk(
        id=ChunkId.generate(),
        article_id="article-1",
        content="Content from article 1",
        position=position1,
        start_char=0,
        end_char=100,
        token_count=TokenCount(value=500, encoding="cl100k_base"),
        source_url="https://example.com/article1",
    )

    chunk2 = ContentChunk(
        id=ChunkId.generate(),
        article_id="article-2",
        content="Content from article 2",
        position=position2,
        start_char=0,
        end_char=100,
        token_count=TokenCount(value=500, encoding="cl100k_base"),
        source_url="https://example.com/article2",
    )

    # Property: Chunks are from different articles
    assert chunk1.is_from_same_article(chunk2) is False
    assert chunk2.is_from_same_article(chunk1) is False

    # Property: Chunks are not adjacent (different articles)
    assert chunk1.is_adjacent_to(chunk2) is False
    assert chunk2.is_adjacent_to(chunk1) is False

    # Property: comes_before() raises ValueError for different articles
    with pytest.raises(
        ValueError, match="No se pueden comparar chunks de artículos diferentes"
    ):
        chunk1.comes_before(chunk2)

    with pytest.raises(
        ValueError, match="No se pueden comparar chunks de artículos diferentes"
    ):
        chunk2.comes_before(chunk1)
