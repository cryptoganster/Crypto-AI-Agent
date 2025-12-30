"""Property-Based Tests para ContextPack aggregate.

Feature: ai-content-processing-bounded-context
"""

import pytest
from hypothesis import assume, given, settings
from hypothesis import strategies as st

from src.ai.domain.value_objects import ChunkId, VectorEmbedding
from src.chunking.domain.exceptions import (
    ChunkRelevanceOrderException,
    ContextPackFullException,
)
from src.rag.domain.aggregates import ContextPack

# ============================================================================
# Strategies (Generators)
# ============================================================================


@st.composite
def vector_embedding_strategy(draw):
    """Genera VectorEmbedding válido."""
    # Generar vector normalizado de 768 dimensiones
    vector = draw(
        st.lists(
            st.floats(
                min_value=-1.0, max_value=1.0, allow_nan=False, allow_infinity=False
            ),
            min_size=768,
            max_size=768,
        )
    )

    # Normalizar a magnitud unitaria
    import numpy as np

    vector_array = np.array(vector, dtype=np.float32)
    magnitude = np.linalg.norm(vector_array)

    if magnitude > 0:
        vector_array = vector_array / magnitude
    else:
        # Si el vector es cero, usar vector unitario en primera dimensión
        vector_array = np.zeros(768, dtype=np.float32)
        vector_array[0] = 1.0

    return VectorEmbedding.from_list(vector_array.tolist(), "nomic-embed-text")


@st.composite
def context_pack_strategy(draw, max_tokens=None):
    """Genera ContextPack válido."""
    query = draw(st.text(min_size=1, max_size=100))
    embedding = draw(vector_embedding_strategy())

    if max_tokens is None:
        max_tokens = draw(st.integers(min_value=100, max_value=10000))

    return ContextPack.create(
        query=query, query_embedding=embedding, max_tokens=max_tokens
    )


@st.composite
def chunk_data_strategy(draw, max_token_count=None):
    """Genera datos válidos para agregar un chunk."""
    chunk_id = ChunkId.generate()

    if max_token_count is None:
        token_count = draw(st.integers(min_value=1, max_value=2000))
    else:
        token_count = draw(st.integers(min_value=1, max_value=max_token_count))

    relevance_score = draw(st.floats(min_value=0.0, max_value=1.0))

    # Generar URL válida
    domain = draw(
        st.text(
            alphabet=st.characters(whitelist_categories=("Ll", "Nd")),
            min_size=3,
            max_size=20,
        )
    )
    path = draw(
        st.text(
            alphabet=st.characters(whitelist_categories=("Ll", "Nd", "Pd")),
            min_size=1,
            max_size=30,
        )
    )
    source_url = f"https://{domain}.com/{path}"

    return {
        "chunk_id": chunk_id,
        "token_count": token_count,
        "relevance_score": relevance_score,
        "source_url": source_url,
    }


def generate_descending_scores(size):
    """Genera lista simple de relevance scores en orden descendente."""
    # Generar scores descendentes con decremento fijo
    scores = []
    current_score = 1.0
    decrement = 0.05

    for _ in range(size):
        scores.append(max(0.0, current_score))
        current_score -= decrement

    return scores


# ============================================================================
# Property 9: Context Pack Token Limit
# **Feature: ai-content-processing-bounded-context, Property 9: Context Pack Token Limit**
# **Validates: Requirements 7.3, 7.4**
# ============================================================================


@given(
    max_tokens=st.integers(min_value=100, max_value=10000),
    num_chunks=st.integers(min_value=1, max_value=20),
)
@settings(max_examples=100)
def test_property_9_token_limit_never_exceeded(max_tokens, num_chunks):
    """
    Property 9: Context Pack Token Limit

    Para cualquier ContextPack con max_tokens M, y cualquier secuencia de
    operaciones add_chunk válidas, el total_tokens nunca debe exceder M.

    Invariante: total_tokens <= max_tokens (siempre)

    Validates: Requirements 7.3, 7.4
    """
    # Arrange - Crear ContextPack con max_tokens específico
    query = "test query"
    embedding = VectorEmbedding.from_list([1.0] + [0.0] * 767, "nomic-embed-text")
    pack = ContextPack.create(
        query=query, query_embedding=embedding, max_tokens=max_tokens
    )

    # Act - Intentar agregar chunks hasta llenar el pack
    tokens_per_chunk = max(
        1, max_tokens // (num_chunks * 2)
    )  # Asegurar que algunos quepan

    for i in range(num_chunks):
        # Generar relevance score descendente
        relevance_score = 1.0 - (i * 0.05)
        relevance_score = max(0.0, min(1.0, relevance_score))

        try:
            pack.add_chunk(
                chunk_id=ChunkId.generate(),
                token_count=tokens_per_chunk,
                relevance_score=relevance_score,
                source_url=f"https://example.com/article{i}",
            )
        except ContextPackFullException:
            # Es válido que se llene el pack
            break

    # Assert - INVARIANTE: total_tokens nunca excede max_tokens
    assert pack.total_tokens <= pack.max_tokens, (
        f"INVARIANTE VIOLADO: total_tokens ({pack.total_tokens}) "
        f"excede max_tokens ({pack.max_tokens})"
    )


@given(
    max_tokens=st.integers(min_value=100, max_value=5000),
    token_count=st.integers(min_value=1, max_value=10000),
)
@settings(max_examples=100)
def test_property_9_adding_chunk_that_exceeds_limit_fails(max_tokens, token_count):
    """
    Property 9: Context Pack Token Limit (Boundary Case)

    Para cualquier ContextPack con max_tokens M, intentar agregar un chunk
    que causaría que total_tokens > M debe lanzar ContextPackFullException.

    Validates: Requirements 7.3, 7.4
    """
    # Arrange
    query = "test query"
    embedding = VectorEmbedding.from_list([1.0] + [0.0] * 767, "nomic-embed-text")
    pack = ContextPack.create(
        query=query, query_embedding=embedding, max_tokens=max_tokens
    )

    # Assume: El chunk excedería el límite
    assume(token_count > max_tokens)

    # Act & Assert - Debe lanzar ContextPackFullException
    with pytest.raises(ContextPackFullException) as exc_info:
        pack.add_chunk(
            chunk_id=ChunkId.generate(),
            token_count=token_count,
            relevance_score=0.9,
            source_url="https://example.com/article",
        )

    # Verificar detalles de la excepción
    exception = exc_info.value
    assert exception.current_tokens == 0
    assert exception.max_tokens == max_tokens
    assert exception.attempted_tokens == token_count

    # Verificar que el pack no cambió
    assert pack.total_tokens == 0
    assert len(pack.chunk_ids) == 0


@given(
    max_tokens=st.integers(min_value=500, max_value=5000),
)
@settings(max_examples=100)
def test_property_9_filling_pack_exactly_to_limit(max_tokens):
    """
    Property 9: Context Pack Token Limit (Exact Fill)

    Para cualquier ContextPack con max_tokens M, es posible llenar el pack
    exactamente hasta M tokens, y después is_full() debe retornar True.

    Validates: Requirements 7.3, 7.4
    """
    # Arrange
    query = "test query"
    embedding = VectorEmbedding.from_list([1.0] + [0.0] * 767, "nomic-embed-text")
    pack = ContextPack.create(
        query=query, query_embedding=embedding, max_tokens=max_tokens
    )

    # Act - Llenar exactamente hasta el límite
    # Dividir en chunks que sumen exactamente max_tokens
    chunk_size = max_tokens // 3
    remaining = max_tokens
    chunk_num = 0

    while remaining > 0:
        tokens_to_add = min(chunk_size, remaining)

        pack.add_chunk(
            chunk_id=ChunkId.generate(),
            token_count=tokens_to_add,
            relevance_score=1.0 - (chunk_num * 0.1),
            source_url=f"https://example.com/article{chunk_num}",
        )

        remaining -= tokens_to_add
        chunk_num += 1

        if chunk_num > 100:  # Safety limit
            break

    # Assert
    assert (
        pack.total_tokens == max_tokens
    ), f"Expected total_tokens to be {max_tokens}, got {pack.total_tokens}"
    assert pack.is_full() is True, "Pack should be full when total_tokens == max_tokens"
    assert pack.get_remaining_tokens() == 0, "Remaining tokens should be 0"


# ============================================================================
# Property 10: Context Pack Ordering
# **Feature: ai-content-processing-bounded-context, Property 10: Context Pack Ordering**
# **Validates: Requirements 7.3, 7.4**
# ============================================================================


@given(
    num_chunks=st.integers(min_value=2, max_value=20),
)
@settings(max_examples=100)
def test_property_10_relevance_scores_always_descending(num_chunks):
    """
    Property 10: Context Pack Ordering

    Para cualquier ContextPack, los relevance_scores deben estar siempre
    en orden descendente (no estrictamente, permite iguales).

    Invariante: Para todo i < j: relevance_scores[i] >= relevance_scores[j]

    Validates: Requirements 7.3, 7.4
    """
    # Arrange
    query = "test query"
    embedding = VectorEmbedding.from_list([1.0] + [0.0] * 767, "nomic-embed-text")
    pack = ContextPack.create(
        query=query,
        query_embedding=embedding,
        max_tokens=10000,  # Suficiente para todos los chunks
    )

    # Act - Agregar chunks con scores descendentes
    for i in range(num_chunks):
        # Generar score descendente (permite iguales)
        relevance_score = 1.0 - (i * 0.04)  # Decremento pequeño
        relevance_score = max(0.0, min(1.0, relevance_score))

        pack.add_chunk(
            chunk_id=ChunkId.generate(),
            token_count=100,
            relevance_score=relevance_score,
            source_url=f"https://example.com/article{i}",
        )

    # Assert - INVARIANTE: Orden descendente
    scores = pack.relevance_scores

    for i in range(len(scores) - 1):
        assert scores[i] >= scores[i + 1], (
            f"INVARIANTE VIOLADO: relevance_scores no está en orden descendente. "
            f"scores[{i}] = {scores[i]}, scores[{i+1}] = {scores[i+1]}"
        )


@given(
    first_score=st.floats(min_value=0.0, max_value=1.0),
    second_score=st.floats(min_value=0.0, max_value=1.0),
)
@settings(max_examples=100)
def test_property_10_adding_higher_score_after_lower_fails(first_score, second_score):
    """
    Property 10: Context Pack Ordering (Violation Detection)

    Para cualquier ContextPack, intentar agregar un chunk con relevance_score
    mayor que el último chunk debe lanzar ChunkRelevanceOrderException.

    Validates: Requirements 7.3, 7.4
    """
    # Assume: El segundo score es estrictamente mayor que el primero
    assume(second_score > first_score)

    # Arrange
    query = "test query"
    embedding = VectorEmbedding.from_list([1.0] + [0.0] * 767, "nomic-embed-text")
    pack = ContextPack.create(query=query, query_embedding=embedding, max_tokens=10000)

    # Act - Agregar primer chunk
    pack.add_chunk(
        chunk_id=ChunkId.generate(),
        token_count=100,
        relevance_score=first_score,
        source_url="https://example.com/article1",
    )

    # Act & Assert - Intentar agregar chunk con score mayor debe fallar
    with pytest.raises(ChunkRelevanceOrderException) as exc_info:
        pack.add_chunk(
            chunk_id=ChunkId.generate(),
            token_count=100,
            relevance_score=second_score,
            source_url="https://example.com/article2",
        )

    # Verificar detalles de la excepción
    exception = exc_info.value
    assert exception.new_score == second_score
    assert exception.last_score == first_score

    # Verificar que el pack no cambió
    assert len(pack.chunk_ids) == 1
    assert pack.relevance_scores == [first_score]


@given(
    num_chunks=st.integers(min_value=3, max_value=15),
)
@settings(max_examples=100)
def test_property_10_adding_chunks_in_descending_order_succeeds(num_chunks):
    """
    Property 10: Context Pack Ordering (Valid Sequence)

    Para cualquier secuencia de relevance_scores en orden descendente,
    agregar chunks con esos scores debe tener éxito y mantener el orden.

    Validates: Requirements 7.3, 7.4
    """
    # Arrange
    query = "test query"
    embedding = VectorEmbedding.from_list([1.0] + [0.0] * 767, "nomic-embed-text")
    pack = ContextPack.create(
        query=query,
        query_embedding=embedding,
        max_tokens=100000,  # Suficiente para todos
    )

    # Generate descending scores
    scores = generate_descending_scores(num_chunks)

    # Act - Agregar chunks con scores descendentes
    for i, score in enumerate(scores):
        pack.add_chunk(
            chunk_id=ChunkId.generate(),
            token_count=100,
            relevance_score=score,
            source_url=f"https://example.com/article{i}",
        )

    # Assert - Verificar que se agregaron todos
    assert len(pack.chunk_ids) == len(scores)
    assert pack.relevance_scores == scores

    # Assert - Verificar orden descendente
    for i in range(len(pack.relevance_scores) - 1):
        assert pack.relevance_scores[i] >= pack.relevance_scores[i + 1]


@given(
    num_chunks=st.integers(min_value=2, max_value=10),
)
@settings(max_examples=100)
def test_property_10_equal_scores_allowed(num_chunks):
    """
    Property 10: Context Pack Ordering (Equal Scores)

    Para cualquier ContextPack, agregar chunks con relevance_scores iguales
    debe estar permitido (orden no estrictamente descendente).

    Validates: Requirements 7.3, 7.4
    """
    # Arrange
    query = "test query"
    embedding = VectorEmbedding.from_list([1.0] + [0.0] * 767, "nomic-embed-text")
    pack = ContextPack.create(query=query, query_embedding=embedding, max_tokens=10000)

    # Act - Agregar chunks con el mismo score
    same_score = 0.85

    for i in range(num_chunks):
        pack.add_chunk(
            chunk_id=ChunkId.generate(),
            token_count=100,
            relevance_score=same_score,
            source_url=f"https://example.com/article{i}",
        )

    # Assert - Todos los chunks deben haberse agregado
    assert len(pack.chunk_ids) == num_chunks
    assert all(score == same_score for score in pack.relevance_scores)

    # Assert - Orden descendente (no estricto) se mantiene
    for i in range(len(pack.relevance_scores) - 1):
        assert pack.relevance_scores[i] >= pack.relevance_scores[i + 1]


# ============================================================================
# Combined Properties: Token Limit + Ordering
# ============================================================================


@given(
    max_tokens=st.integers(min_value=500, max_value=5000),
    num_attempts=st.integers(min_value=5, max_value=30),
)
@settings(max_examples=50)
def test_combined_token_limit_and_ordering_maintained(max_tokens, num_attempts):
    """
    Combined Property: Token Limit + Ordering

    Para cualquier ContextPack, al agregar múltiples chunks:
    1. El total_tokens nunca excede max_tokens
    2. Los relevance_scores siempre están en orden descendente

    Validates: Requirements 7.3, 7.4
    """
    # Arrange
    query = "test query"
    embedding = VectorEmbedding.from_list([1.0] + [0.0] * 767, "nomic-embed-text")
    pack = ContextPack.create(
        query=query, query_embedding=embedding, max_tokens=max_tokens
    )

    # Act - Intentar agregar múltiples chunks
    token_count = max(10, max_tokens // (num_attempts * 2))

    for i in range(num_attempts):
        relevance_score = 1.0 - (i * 0.03)
        relevance_score = max(0.0, min(1.0, relevance_score))

        try:
            pack.add_chunk(
                chunk_id=ChunkId.generate(),
                token_count=token_count,
                relevance_score=relevance_score,
                source_url=f"https://example.com/article{i}",
            )
        except ContextPackFullException:
            # Es válido que se llene
            break

    # Assert - Invariante 1: Token Limit
    assert (
        pack.total_tokens <= pack.max_tokens
    ), f"Token limit violated: {pack.total_tokens} > {pack.max_tokens}"

    # Assert - Invariante 2: Ordering
    scores = pack.relevance_scores
    for i in range(len(scores) - 1):
        assert (
            scores[i] >= scores[i + 1]
        ), f"Ordering violated at index {i}: {scores[i]} < {scores[i + 1]}"
