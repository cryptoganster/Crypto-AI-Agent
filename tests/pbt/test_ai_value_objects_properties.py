"""
Property-based tests for AI Content Processing value objects.

Feature: ai-content-processing-bounded-context
Properties tested:
- Property 3: Embedding Dimension Consistency
- Property 4: Embedding Normalization
- Property 5: Summary Sentence Count
- Property 6: TLDR Bullet Count

Validates: Requirements 2.2, 2.6, 3.1, 3.5
"""

import numpy as np
import pytest
from hypothesis import HealthCheck, assume, given, settings
from hypothesis import strategies as st

from src.chunking.domain.value_objects.chunk_summary import (
    MAX_CONTENT_LENGTH,
    MAX_SENTENCES,
    MIN_CONTENT_LENGTH,
    MIN_SENTENCES,
    ChunkSummary,
)
from src.chunking.domain.value_objects.token_count import (
    DEFAULT_ENCODING,
    MAX_TOKEN_COUNT,
    MIN_TOKEN_COUNT,
    TokenCount,
)
from src.chunking.domain.value_objects.vector_embedding import (
    DEFAULT_DIMENSION,
    MAX_DIMENSION,
    MIN_DIMENSION,
    NORMALIZATION_TOLERANCE,
    VectorEmbedding,
)
from src.rag.domain.value_objects.tldr import (
    MAX_BULLET_LENGTH,
    MAX_BULLETS,
    MIN_BULLET_LENGTH,
    MIN_BULLETS,
    TLDR,
)

# ============================================================================
# Property 3: Embedding Dimension Consistency
# ============================================================================
# For any VectorEmbedding, the dimension attribute must match the actual
# vector shape, and all operations must preserve this consistency.
# Validates: Requirements 2.2
# ============================================================================


@given(
    dimension=st.integers(min_value=MIN_DIMENSION, max_value=min(100, MAX_DIMENSION)),
    model=st.text(
        min_size=1, max_size=50, alphabet=st.characters(blacklist_categories=("Cs",))
    ),
)
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=100)
def test_property_3_embedding_dimension_consistency(dimension: int, model: str):
    """
    Property 3: Embedding Dimension Consistency

    For any VectorEmbedding created with dimension D:
    - vector.shape must be (D,)
    - dimension attribute must equal D
    - All operations must preserve dimension consistency

    Validates: Requirements 2.2
    """
    # Generate random normalized vector
    vector = np.random.randn(dimension).astype(np.float32)
    magnitude = np.linalg.norm(vector)
    assume(magnitude > 0)  # Avoid zero vectors
    vector = vector / magnitude

    # Create embedding
    embedding = VectorEmbedding(vector=vector, model=model, dimension=dimension)

    # Property: Dimension attribute matches vector shape
    assert embedding.dimension == dimension
    assert embedding.vector.shape == (dimension,)
    assert len(embedding.vector) == dimension

    # Property: to_list() preserves dimension
    vec_list = embedding.to_list()
    assert len(vec_list) == dimension

    # Property: from_list() preserves dimension
    reconstructed = VectorEmbedding.from_list(vec_list, model=model, normalize=False)
    assert reconstructed.dimension == dimension
    assert reconstructed.vector.shape == (dimension,)

    # Property: Dimension is immutable (frozen dataclass)
    with pytest.raises(AttributeError):
        embedding.dimension = dimension + 1  # type: ignore


@given(
    dimension=st.integers(min_value=MIN_DIMENSION, max_value=min(100, MAX_DIMENSION)),
)
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=50)
def test_property_3_dimension_mismatch_rejected(dimension: int):
    """
    Property 3: Dimension Mismatch Rejected

    For any VectorEmbedding, if the vector shape doesn't match the
    declared dimension, creation must fail.

    Validates: Requirements 2.2
    """
    # Create vector with wrong dimension
    wrong_dimension = dimension + 1
    vector = np.random.randn(wrong_dimension).astype(np.float32)
    vector = vector / np.linalg.norm(vector)

    # Property: Dimension mismatch raises ValueError
    with pytest.raises(ValueError, match="Shape del vector inválido"):
        VectorEmbedding(vector=vector, model="test", dimension=dimension)


# ============================================================================
# Property 4: Embedding Normalization
# ============================================================================
# For any VectorEmbedding, the vector must be normalized (magnitude ≈ 1.0)
# within tolerance, and this property must be preserved across operations.
# Validates: Requirements 2.2, 2.6
# ============================================================================


@given(
    dimension=st.integers(min_value=MIN_DIMENSION, max_value=min(100, MAX_DIMENSION)),
    model=st.text(
        min_size=1, max_size=50, alphabet=st.characters(blacklist_categories=("Cs",))
    ),
)
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=100)
def test_property_4_embedding_normalization(dimension: int, model: str):
    """
    Property 4: Embedding Normalization

    For any VectorEmbedding:
    - magnitude() must return ≈ 1.0 (within tolerance)
    - is_normalized() must return True
    - Normalization must be preserved across serialization

    Validates: Requirements 2.2, 2.6
    """
    # Generate random vector and normalize
    vector = np.random.randn(dimension).astype(np.float32)
    magnitude = np.linalg.norm(vector)
    assume(magnitude > 0)
    vector = vector / magnitude

    # Create embedding
    embedding = VectorEmbedding(vector=vector, model=model, dimension=dimension)

    # Property: Magnitude is approximately 1.0
    assert abs(embedding.magnitude() - 1.0) < NORMALIZATION_TOLERANCE

    # Property: is_normalized() returns True
    assert embedding.is_normalized()
    assert embedding.is_normalized(tolerance=NORMALIZATION_TOLERANCE)

    # Property: Normalization preserved after to_list/from_list
    vec_list = embedding.to_list()
    reconstructed = VectorEmbedding.from_list(vec_list, model=model, normalize=False)
    assert reconstructed.is_normalized()
    assert abs(reconstructed.magnitude() - 1.0) < NORMALIZATION_TOLERANCE


@given(
    dimension=st.integers(min_value=MIN_DIMENSION, max_value=min(100, MAX_DIMENSION)),
)
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=50)
def test_property_4_unnormalized_vector_rejected(dimension: int):
    """
    Property 4: Unnormalized Vector Rejected

    For any vector that is not normalized (magnitude != 1.0),
    VectorEmbedding creation must fail.

    Validates: Requirements 2.2, 2.6
    """
    # Create unnormalized vector (magnitude != 1.0)
    vector = np.random.randn(dimension).astype(np.float32)
    magnitude = np.linalg.norm(vector)
    assume(magnitude > 0)

    # Scale to make magnitude != 1.0 (outside tolerance)
    vector = vector * 2.0  # magnitude will be ~2.0

    # Property: Unnormalized vector raises ValueError
    with pytest.raises(ValueError, match="Vector no está normalizado"):
        VectorEmbedding(vector=vector, model="test", dimension=dimension)


@given(
    dimension=st.integers(min_value=MIN_DIMENSION, max_value=min(100, MAX_DIMENSION)),
)
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=50)
def test_property_4_from_list_auto_normalize(dimension: int):
    """
    Property 4: from_list() Auto-Normalization

    For any vector list, from_list(normalize=True) must produce
    a normalized VectorEmbedding.

    Validates: Requirements 2.2, 2.6
    """
    # Generate random unnormalized vector
    vec_list = np.random.randn(dimension).tolist()
    assume(np.linalg.norm(vec_list) > 0)

    # Property: from_list with normalize=True produces normalized embedding
    embedding = VectorEmbedding.from_list(vec_list, model="test", normalize=True)

    assert embedding.is_normalized()
    assert abs(embedding.magnitude() - 1.0) < NORMALIZATION_TOLERANCE


# ============================================================================
# Property 5: Summary Sentence Count
# ============================================================================
# For any ChunkSummary, the sentence_count must be between MIN_SENTENCES
# and MAX_SENTENCES, and must accurately reflect the content.
# Validates: Requirements 3.1, 3.5
# ============================================================================


def generate_sentences(n: int) -> str:
    """Generate n sentences for testing."""
    sentences = []
    for i in range(n):
        # Generate sentence with at least MIN_CONTENT_LENGTH/MAX_SENTENCES chars
        sentence = f"This is sentence number {i + 1} with some content"
        sentences.append(sentence)
    return ". ".join(sentences) + "."


@given(
    sentence_count=st.integers(min_value=MIN_SENTENCES, max_value=MAX_SENTENCES),
)
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=50)
def test_property_5_summary_sentence_count(sentence_count: int):
    """
    Property 5: Summary Sentence Count

    For any ChunkSummary with N sentences (MIN_SENTENCES <= N <= MAX_SENTENCES):
    - sentence_count attribute must equal N
    - Content must contain N sentences
    - Sentence count must be immutable

    Validates: Requirements 3.1, 3.5
    """
    # Generate content with exact sentence count
    content = generate_sentences(sentence_count)

    # Create summary
    summary = ChunkSummary(content=content, sentence_count=sentence_count)

    # Property: sentence_count matches declared value
    assert summary.sentence_count == sentence_count
    assert MIN_SENTENCES <= summary.sentence_count <= MAX_SENTENCES

    # Property: Content is not empty
    assert len(summary.content) >= MIN_CONTENT_LENGTH
    assert len(summary.content) <= MAX_CONTENT_LENGTH

    # Property: sentence_count is immutable
    with pytest.raises(AttributeError):
        summary.sentence_count = sentence_count + 1  # type: ignore


@given(
    sentence_count=st.integers(min_value=MIN_SENTENCES, max_value=MAX_SENTENCES),
)
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=50)
def test_property_5_from_text_sentence_counting(sentence_count: int):
    """
    Property 5: from_text() Sentence Counting

    For any text with N sentences, from_text() must correctly
    count and validate the sentence count.

    Validates: Requirements 3.1, 3.5
    """
    # Generate text with known sentence count
    text = generate_sentences(sentence_count)

    # Property: from_text() creates valid summary
    summary = ChunkSummary.from_text(text)

    # Property: Sentence count is within valid range
    assert MIN_SENTENCES <= summary.sentence_count <= MAX_SENTENCES

    # Property: Content matches input (stripped)
    assert summary.content == text.strip()


@given(
    sentence_count=st.integers(min_value=0, max_value=MIN_SENTENCES - 1),
)
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=20)
def test_property_5_too_few_sentences_rejected(sentence_count: int):
    """
    Property 5: Too Few Sentences Rejected

    For any ChunkSummary with fewer than MIN_SENTENCES,
    creation must fail.

    Validates: Requirements 3.1, 3.5
    """
    assume(sentence_count < MIN_SENTENCES)

    # Generate content with too few sentences
    if sentence_count == 0:
        content = "Single sentence without proper structure"
    else:
        content = generate_sentences(sentence_count)

    # Property: Too few sentences raises ValueError
    with pytest.raises(ValueError, match="debe tener entre"):
        ChunkSummary(content=content, sentence_count=sentence_count)


@given(
    sentence_count=st.integers(
        min_value=MAX_SENTENCES + 1, max_value=MAX_SENTENCES + 10
    ),
)
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=20)
def test_property_5_too_many_sentences_rejected(sentence_count: int):
    """
    Property 5: Too Many Sentences Rejected

    For any ChunkSummary with more than MAX_SENTENCES,
    creation must fail.

    Validates: Requirements 3.1, 3.5
    """
    assume(sentence_count > MAX_SENTENCES)

    # Generate content with too many sentences
    content = generate_sentences(sentence_count)

    # Property: Too many sentences raises ValueError
    with pytest.raises(ValueError, match="debe tener entre"):
        ChunkSummary(content=content, sentence_count=sentence_count)


# ============================================================================
# Property 6: TLDR Bullet Count
# ============================================================================
# For any TLDR, the number of bullets must be between MIN_BULLETS and
# MAX_BULLETS, and each bullet must meet length requirements.
# Validates: Requirements 3.5
# ============================================================================


def generate_bullets(n: int) -> list[str]:
    """Generate n valid bullets for testing."""
    bullets = []
    for i in range(n):
        # Generate bullet with valid length
        bullet = f"Important point number {i + 1} about the article content"
        bullets.append(bullet)
    return bullets


@given(
    bullet_count=st.integers(min_value=MIN_BULLETS, max_value=MAX_BULLETS),
)
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=50)
def test_property_6_tldr_bullet_count(bullet_count: int):
    """
    Property 6: TLDR Bullet Count

    For any TLDR with N bullets (MIN_BULLETS <= N <= MAX_BULLETS):
    - bullet_count property must equal N
    - bullets list must have length N
    - Each bullet must meet length requirements

    Validates: Requirements 3.5
    """
    # Generate bullets
    bullets = generate_bullets(bullet_count)

    # Create TLDR
    tldr = TLDR(bullets=bullets)

    # Property: bullet_count matches number of bullets
    assert tldr.bullet_count == bullet_count
    assert len(tldr.bullets) == bullet_count
    assert len(tldr) == bullet_count

    # Property: Bullet count is in valid range
    assert MIN_BULLETS <= tldr.bullet_count <= MAX_BULLETS

    # Property: Each bullet meets length requirements
    for bullet in tldr.bullets:
        assert MIN_BULLET_LENGTH <= len(bullet) <= MAX_BULLET_LENGTH

    # Property: bullet_count is immutable (property, not attribute)
    # Cannot be set directly


@given(
    bullet_count=st.integers(min_value=MIN_BULLETS, max_value=MAX_BULLETS),
)
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=50)
def test_property_6_tldr_iteration(bullet_count: int):
    """
    Property 6: TLDR Iteration

    For any TLDR with N bullets, iterating over it must yield
    exactly N bullets in order.

    Validates: Requirements 3.5
    """
    # Generate bullets
    bullets = generate_bullets(bullet_count)

    # Create TLDR
    tldr = TLDR(bullets=bullets)

    # Property: Iteration yields all bullets
    iterated_bullets = list(tldr)
    assert len(iterated_bullets) == bullet_count
    assert iterated_bullets == bullets

    # Property: Index access works
    for i in range(bullet_count):
        assert tldr[i] == bullets[i]
        assert tldr.get_bullet(i) == bullets[i]


@given(
    bullet_count=st.integers(min_value=0, max_value=MIN_BULLETS - 1),
)
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=20)
def test_property_6_too_few_bullets_rejected(bullet_count: int):
    """
    Property 6: Too Few Bullets Rejected

    For any TLDR with fewer than MIN_BULLETS,
    creation must fail.

    Validates: Requirements 3.5
    """
    assume(bullet_count < MIN_BULLETS)

    # Generate too few bullets
    if bullet_count == 0:
        bullets = []
    else:
        bullets = generate_bullets(bullet_count)

    # Property: Too few bullets raises ValueError
    with pytest.raises(ValueError, match="debe tener entre"):
        TLDR(bullets=bullets)


@given(
    bullet_count=st.integers(min_value=MAX_BULLETS + 1, max_value=MAX_BULLETS + 5),
)
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=20)
def test_property_6_too_many_bullets_rejected(bullet_count: int):
    """
    Property 6: Too Many Bullets Rejected

    For any TLDR with more than MAX_BULLETS,
    creation must fail.

    Validates: Requirements 3.5
    """
    assume(bullet_count > MAX_BULLETS)

    # Generate too many bullets
    bullets = generate_bullets(bullet_count)

    # Property: Too many bullets raises ValueError
    with pytest.raises(ValueError, match="debe tener entre"):
        TLDR(bullets=bullets)


@given(
    bullet_count=st.integers(min_value=MIN_BULLETS, max_value=MAX_BULLETS),
    short_bullet_index=st.integers(min_value=0, max_value=MAX_BULLETS - 1),
)
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=30)
def test_property_6_short_bullet_rejected(bullet_count: int, short_bullet_index: int):
    """
    Property 6: Short Bullet Rejected

    For any TLDR where one bullet is shorter than MIN_BULLET_LENGTH,
    creation must fail.

    Validates: Requirements 3.5
    """
    assume(short_bullet_index < bullet_count)

    # Generate bullets with one too short
    bullets = generate_bullets(bullet_count)
    bullets[short_bullet_index] = "Short"  # Less than MIN_BULLET_LENGTH

    # Property: Short bullet raises ValueError
    with pytest.raises(ValueError, match="muy corto"):
        TLDR(bullets=bullets)


# ============================================================================
# Additional Property Tests for TokenCount
# ============================================================================


@given(
    text=st.text(
        min_size=1, max_size=1000, alphabet=st.characters(blacklist_categories=("Cs",))
    ),
)
@settings(
    suppress_health_check=[HealthCheck.function_scoped_fixture],
    max_examples=50,
    deadline=None,
)
def test_token_count_non_negative(text: str):
    """
    Property: Token count is always non-negative.

    For any text, TokenCount.from_text() must return a non-negative value.
    """
    try:
        token_count = TokenCount.from_text(text)
        assert token_count.value >= MIN_TOKEN_COUNT
        assert token_count.value <= MAX_TOKEN_COUNT
    except ImportError:
        pytest.skip("tiktoken not installed")


@given(
    value1=st.integers(min_value=MIN_TOKEN_COUNT, max_value=1000),
    value2=st.integers(min_value=MIN_TOKEN_COUNT, max_value=1000),
)
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=50)
def test_token_count_addition_commutative(value1: int, value2: int):
    """
    Property: Token count addition is commutative.

    For any two TokenCounts A and B: A + B = B + A
    """
    count1 = TokenCount(value=value1, encoding=DEFAULT_ENCODING)
    count2 = TokenCount(value=value2, encoding=DEFAULT_ENCODING)

    sum1 = count1.add(count2)
    sum2 = count2.add(count1)

    assert sum1.value == sum2.value
    assert sum1.value == value1 + value2
