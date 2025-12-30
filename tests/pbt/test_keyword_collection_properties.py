"""Property-based tests para KeywordCollection Value Object."""

import pytest
from hypothesis import given
from hypothesis import strategies as st

from src.rss.article.domain.value_objects.analysis import KeywordCollection


class TestKeywordCollectionProperties:
    """Property-based tests para KeywordCollection."""

    @given(keywords=st.lists(st.text(min_size=2, max_size=20), min_size=0, max_size=50))
    def test_property_collection_maintains_uniqueness(self, keywords: list):
        """
        Property 4: Collection maintains uniqueness.

        Feature: article-aggregate-refactor, Property 4
        Validates: Requirements 4.2

        Para cualquier lista de keywords (incluso con duplicados),
        KeywordCollection debe mantener solo keywords únicas.
        """
        # Act
        collection = KeywordCollection.from_list(keywords)

        # Assert
        # No debe haber duplicados (case-insensitive)
        keywords_list = collection.to_list()
        assert len(keywords_list) == len(set(keywords_list))

        # Todas las keywords deben estar en lowercase
        assert all(kw == kw.lower() for kw in keywords_list)

    @given(
        keywords1=st.lists(st.text(min_size=2, max_size=10), min_size=1, max_size=10),
        keywords2=st.lists(st.text(min_size=2, max_size=10), min_size=1, max_size=10),
    )
    def test_property_merge_combines_collections(
        self, keywords1: list, keywords2: list
    ):
        """
        Property 4: Collection maintains uniqueness.

        Feature: article-aggregate-refactor, Property 4
        Validates: Requirements 4.2

        Para cualesquiera dos colecciones,
        merge() debe combinarlas manteniendo uniqueness.
        """
        # Arrange
        collection1 = KeywordCollection.from_list(keywords1)
        collection2 = KeywordCollection.from_list(keywords2)

        # Act
        merged = collection1.merge(collection2)

        # Assert
        # El merge debe contener keywords de ambas colecciones
        assert merged.count >= collection1.count
        assert merged.count >= collection2.count
        # Pero no más que la suma (por duplicados)
        assert merged.count <= collection1.count + collection2.count

    @given(keyword=st.text(min_size=2, max_size=20))
    def test_property_add_increases_count(self, keyword: str):
        """
        Property 4: Collection maintains uniqueness.

        Feature: article-aggregate-refactor, Property 4
        Validates: Requirements 4.2

        Para cualquier keyword válida,
        add() debe incrementar el count (si no existía).
        """
        # Arrange
        collection = KeywordCollection.empty()
        initial_count = collection.count

        # Act
        new_collection = collection.add(keyword)

        # Assert
        if len(keyword.strip()) >= 2:
            assert new_collection.count >= initial_count
            assert new_collection.contains(keyword)
