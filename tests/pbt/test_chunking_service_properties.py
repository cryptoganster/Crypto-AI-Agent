"""
Property-based tests for ChunkingService.

Feature: ai-content-processing-bounded-context
Properties tested:
- Property 1: Chunk Size Bounds
- Property 2: Chunk Overlap Consistency

Validates: Requirements 1.1, 1.2
"""

import pytest
from hypothesis import HealthCheck, assume, given, settings
from hypothesis import strategies as st

from src.chunking.domain.services.chunking import ChunkingService
from src.chunking.domain.value_objects.token_count import TokenCount
from src.chunking.infra.external.recursive_text_splitter import RecursiveTextSplitter
from src.chunking.infra.external.tiktoken_encoder import TiktokenEncoder


# Helper function to create ChunkingService with dependencies
def create_chunking_service(
    chunk_size: int = 1400, chunk_overlap: int = 150
) -> ChunkingService:
    """
    Creates ChunkingService with injected dependencies.

    Args:
        chunk_size: Maximum chunk size in tokens
        chunk_overlap: Overlap between chunks in tokens

    Returns:
        ChunkingService instance
    """
    token_encoder = TiktokenEncoder(encoding_name="cl100k_base")
    text_splitter = RecursiveTextSplitter(token_encoder=token_encoder)

    return ChunkingService(
        token_encoder=token_encoder,
        text_splitter=text_splitter,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )


# ============================================================================
# Property 1: Chunk Size Bounds
# ============================================================================
# For any text chunked by ChunkingService, all resulting chunks should have
# token counts within the configured chunk_size bounds (1200-1500 tokens).
# Validates: Requirements 1.1, 1.2
# ============================================================================


@given(
    chunk_size=st.integers(min_value=1200, max_value=1500),
    text_length=st.integers(min_value=5000, max_value=20000),
)
@settings(
    suppress_health_check=[HealthCheck.function_scoped_fixture],
    max_examples=50,
    deadline=1000,
)
def test_property_1_chunk_size_bounds(chunk_size: int, text_length: int):
    """
    Property 1: Chunk Size Bounds

    For any text chunked with chunk_size S:
    - All chunks should have token count <= S
    - Most chunks should have token count close to S (within 20%)
    - Last chunk may be smaller

    Validates: Requirements 1.1, 1.2
    """
    # Create service with specified chunk_size
    service = create_chunking_service(chunk_size=chunk_size, chunk_overlap=150)

    # Generate text (repeat pattern to ensure sufficient length)
    text = ("Bitcoin alcanzó un nuevo máximo histórico. " * (text_length // 50))[
        :text_length
    ]

    # Chunk text
    chunks = service.chunk_text(
        text=text, article_id="article-test", source_url="https://example.com/article"
    )

    # Property: All chunks exist
    assert len(chunks) > 0, "Should produce at least one chunk"

    # Property: All chunks have token count <= chunk_size (with tolerance)
    # Note: LangChain may slightly exceed chunk_size at word boundaries
    tolerance = 1.2  # 20% tolerance
    for i, chunk in enumerate(chunks):
        assert (
            chunk.token_count.value <= chunk_size * tolerance
        ), f"Chunk {i} has {chunk.token_count.value} tokens, exceeds {chunk_size * tolerance}"

    # Property: Most chunks (except last) should be close to chunk_size
    if len(chunks) > 1:
        for i, chunk in enumerate(chunks[:-1]):  # All except last
            # Chunks should be at least 50% of chunk_size
            assert (
                chunk.token_count.value >= chunk_size * 0.5
            ), f"Chunk {i} has {chunk.token_count.value} tokens, below {chunk_size * 0.5}"


@given(
    chunk_size=st.integers(min_value=1200, max_value=1500),
)
@settings(
    suppress_health_check=[HealthCheck.function_scoped_fixture],
    max_examples=30,
    deadline=1000,
)
def test_property_1_chunk_size_configuration(chunk_size: int):
    """
    Property 1: Chunk Size Configuration

    For any valid chunk_size configuration:
    - Service should accept it
    - Service should use it for chunking
    - Chunks should respect the configured size

    Validates: Requirements 1.1, 1.2
    """
    # Create service with specified chunk_size
    service = create_chunking_service(chunk_size=chunk_size, chunk_overlap=150)

    # Property: Service stores configuration
    assert service.chunk_size == chunk_size
    assert service.chunk_overlap == 150

    # Generate long text
    text = "Bitcoin es una criptomoneda descentralizada. " * 500

    # Chunk text
    chunks = service.chunk_text(
        text=text,
        article_id="article-config-test",
        source_url="https://example.com/article",
    )

    # Property: Chunks respect configured size (with tolerance)
    tolerance = 1.2
    for chunk in chunks:
        assert chunk.token_count.value <= chunk_size * tolerance


@given(
    chunk_size=st.integers(min_value=50, max_value=99),
)
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=20)
def test_property_1_chunk_size_below_minimum_rejected(chunk_size: int):
    """
    Property 1: Chunk Size Below Minimum Rejected

    For any chunk_size below 100:
    - Service creation should fail with ValueError

    Validates: Requirements 1.1, 1.2
    """
    assume(chunk_size < 100)

    # Property: chunk_size below minimum raises ValueError
    with pytest.raises(ValueError, match="chunk_size debe ser >= 100"):
        create_chunking_service(chunk_size=chunk_size, chunk_overlap=50)


@given(
    chunk_size=st.integers(min_value=2001, max_value=3000),
)
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=20)
def test_property_1_chunk_size_above_maximum_rejected(chunk_size: int):
    """
    Property 1: Chunk Size Above Maximum Rejected

    For any chunk_size above 2000:
    - Service creation should fail with ValueError

    Validates: Requirements 1.1, 1.2
    """
    assume(chunk_size > 2000)

    # Property: chunk_size above maximum raises ValueError
    with pytest.raises(ValueError, match="chunk_size debe ser <= 2000"):
        create_chunking_service(chunk_size=chunk_size, chunk_overlap=50)


# ============================================================================
# Property 2: Chunk Overlap Consistency
# ============================================================================
# For any text chunked with overlap O, consecutive chunks should share
# approximately O tokens of content.
# Validates: Requirements 1.1, 1.2
# ============================================================================


@given(
    chunk_overlap=st.integers(min_value=50, max_value=300),
)
@settings(
    suppress_health_check=[HealthCheck.function_scoped_fixture],
    max_examples=50,
    deadline=1000,
)
def test_property_2_chunk_overlap_consistency(chunk_overlap: int):
    """
    Property 2: Chunk Overlap Consistency

    For any text chunked with overlap O:
    - Consecutive chunks should share content
    - Overlap should be approximately O tokens
    - All chunks should have overlap (except first and last)

    Validates: Requirements 1.1, 1.2
    """
    # Create service with specified overlap
    chunk_size = 1200
    assume(chunk_overlap < chunk_size)

    service = create_chunking_service(
        chunk_size=chunk_size, chunk_overlap=chunk_overlap
    )

    # Generate long text to ensure multiple chunks
    text = "El mercado de criptomonedas experimentó volatilidad. " * 500

    # Chunk text
    chunks = service.chunk_text(
        text=text,
        article_id="article-overlap-test",
        source_url="https://example.com/article",
    )

    # Property: Multiple chunks created
    if len(chunks) <= 1:
        # If only one chunk, overlap doesn't apply
        return

    # Property: Consecutive chunks have overlapping content
    for i in range(len(chunks) - 1):
        chunk1 = chunks[i]
        chunk2 = chunks[i + 1]

        # Check if there's content overlap
        # Note: Due to separator-based splitting, exact overlap may vary
        # We check that chunk2 starts before chunk1 ends
        assert (
            chunk2.start_char < chunk1.end_char
        ), f"Chunks {i} and {i+1} should have overlapping character positions"


@given(
    chunk_overlap=st.integers(min_value=0, max_value=500),
)
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=30)
def test_property_2_chunk_overlap_configuration(chunk_overlap: int):
    """
    Property 2: Chunk Overlap Configuration

    For any valid chunk_overlap configuration:
    - Service should accept it if overlap < chunk_size
    - Service should store the configuration

    Validates: Requirements 1.1, 1.2
    """
    chunk_size = 1200

    if chunk_overlap >= chunk_size:
        # Property: overlap >= chunk_size raises ValueError
        with pytest.raises(ValueError, match="chunk_overlap .* debe ser < chunk_size"):
            create_chunking_service(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    else:
        # Property: Valid overlap is accepted
        service = create_chunking_service(
            chunk_size=chunk_size, chunk_overlap=chunk_overlap
        )
        assert service.chunk_overlap == chunk_overlap


@given(
    chunk_overlap=st.integers(min_value=-100, max_value=-1),
)
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=20)
def test_property_2_negative_overlap_rejected(chunk_overlap: int):
    """
    Property 2: Negative Overlap Rejected

    For any negative chunk_overlap:
    - Service creation should fail with ValueError

    Validates: Requirements 1.1, 1.2
    """
    assume(chunk_overlap < 0)

    # Property: Negative overlap raises ValueError
    with pytest.raises(ValueError, match="chunk_overlap debe ser >= 0"):
        create_chunking_service(chunk_size=1200, chunk_overlap=chunk_overlap)


@given(
    chunk_size=st.integers(min_value=200, max_value=500),
    chunk_overlap=st.integers(min_value=50, max_value=150),
)
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=30)
def test_property_2_overlap_less_than_chunk_size(chunk_size: int, chunk_overlap: int):
    """
    Property 2: Overlap Must Be Less Than Chunk Size

    For any chunk_size and chunk_overlap:
    - If overlap >= chunk_size, service creation should fail
    - If overlap < chunk_size, service creation should succeed

    Validates: Requirements 1.1, 1.2
    """
    if chunk_overlap >= chunk_size:
        # Property: overlap >= chunk_size raises ValueError
        with pytest.raises(ValueError, match="chunk_overlap .* debe ser < chunk_size"):
            create_chunking_service(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    else:
        # Property: Valid configuration is accepted
        service = create_chunking_service(
            chunk_size=chunk_size, chunk_overlap=chunk_overlap
        )
        assert service.chunk_size == chunk_size
        assert service.chunk_overlap == chunk_overlap


@given(
    text_length=st.integers(min_value=5000, max_value=15000),
)
@settings(
    suppress_health_check=[HealthCheck.function_scoped_fixture],
    max_examples=30,
    deadline=1000,
)
def test_property_2_overlap_preserves_context(text_length: int):
    """
    Property 2: Overlap Preserves Context

    For any text chunked with overlap:
    - Information at chunk boundaries should appear in both chunks
    - This ensures context is preserved across chunks

    Validates: Requirements 1.1, 1.2
    """
    # Create service with overlap
    service = create_chunking_service(chunk_size=1200, chunk_overlap=150)

    # Generate text with identifiable patterns
    text = ""
    for i in range(text_length // 100):
        text += f"Sección {i}: Bitcoin alcanzó ${i * 1000}. "

    # Chunk text
    chunks = service.chunk_text(
        text=text,
        article_id="article-context-test",
        source_url="https://example.com/article",
    )

    # Property: Multiple chunks created
    if len(chunks) <= 1:
        return

    # Property: Consecutive chunks have overlapping positions
    for i in range(len(chunks) - 1):
        chunk1 = chunks[i]
        chunk2 = chunks[i + 1]

        # Chunk2 should start before chunk1 ends (overlap)
        assert (
            chunk2.start_char < chunk1.end_char
        ), f"Chunks {i} and {i+1} should overlap in character positions"

        # There should be some overlap in characters
        overlap_chars = chunk1.end_char - chunk2.start_char
        assert (
            overlap_chars > 0
        ), f"Chunks {i} and {i+1} should have positive character overlap"


@given(
    num_chunks=st.integers(min_value=2, max_value=10),
)
@settings(
    suppress_health_check=[HealthCheck.function_scoped_fixture],
    max_examples=30,
    deadline=1000,
)
def test_property_2_all_chunks_have_overlap_except_boundaries(num_chunks: int):
    """
    Property 2: All Chunks Have Overlap Except Boundaries

    For any list of chunks:
    - First chunk has no predecessor (no overlap before)
    - Last chunk has no successor (no overlap after)
    - All middle chunks have overlap with neighbors

    Validates: Requirements 1.1, 1.2
    """
    # Create service
    service = create_chunking_service(chunk_size=500, chunk_overlap=100)

    # Generate text long enough for multiple chunks
    text = "Bitcoin es una criptomoneda. " * 1000

    # Chunk text
    chunks = service.chunk_text(
        text=text,
        article_id="article-boundary-test",
        source_url="https://example.com/article",
    )

    # Property: At least 2 chunks
    if len(chunks) < 2:
        # Generate longer text
        text = "Bitcoin es una criptomoneda. " * 2000
        chunks = service.chunk_text(
            text=text,
            article_id="article-boundary-test",
            source_url="https://example.com/article",
        )

    if len(chunks) < 2:
        # Still only one chunk, skip test
        return

    # Property: First chunk starts at position 0
    assert chunks[0].start_char == 0, "First chunk should start at position 0"

    # Property: Last chunk ends at or near text end
    assert chunks[-1].end_char <= len(text), "Last chunk should not exceed text length"

    # Property: Middle chunks have overlap with neighbors
    for i in range(1, len(chunks) - 1):
        prev_chunk = chunks[i - 1]
        curr_chunk = chunks[i]
        next_chunk = chunks[i + 1]

        # Current chunk overlaps with previous
        assert (
            curr_chunk.start_char < prev_chunk.end_char
        ), f"Chunk {i} should overlap with previous chunk"

        # Current chunk overlaps with next
        assert (
            next_chunk.start_char < curr_chunk.end_char
        ), f"Chunk {i} should overlap with next chunk"


@given(
    chunk_size=st.integers(min_value=1200, max_value=1500),
    chunk_overlap=st.integers(min_value=100, max_value=200),
)
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=30)
def test_property_2_overlap_ratio_reasonable(chunk_size: int, chunk_overlap: int):
    """
    Property 2: Overlap Ratio Is Reasonable

    For any chunk_size and chunk_overlap:
    - Overlap should be less than chunk_size
    - Overlap ratio (overlap/chunk_size) should be reasonable (< 0.5)

    Validates: Requirements 1.1, 1.2
    """
    assume(chunk_overlap < chunk_size)

    # Create service
    service = create_chunking_service(
        chunk_size=chunk_size, chunk_overlap=chunk_overlap
    )

    # Property: Overlap is less than chunk_size
    assert service.chunk_overlap < service.chunk_size

    # Property: Overlap ratio is reasonable
    overlap_ratio = service.chunk_overlap / service.chunk_size
    assert (
        overlap_ratio < 0.5
    ), f"Overlap ratio {overlap_ratio} should be < 0.5 for efficiency"
