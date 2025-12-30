"""Property-based tests para ArticleMetrics Value Object."""

import pytest
from hypothesis import given
from hypothesis import strategies as st

from src.rss.article.domain.value_objects.analysis import (
    ReadingTime,
)
from src.rss.article.domain.value_objects.analysis import (
    RssArticleMetrics as RssArticleMetrics,
)
from src.rss.article.domain.value_objects.analysis import (
    WordCount,
)


class TestContentMetricsProperties:
    """Property-based tests para ArticleMetrics VO."""

    @given(
        word_count=st.one_of(st.none(), st.integers()),
        reading_time_minutes=st.one_of(st.none(), st.integers()),
    )
    def test_content_metrics_non_negative_values_property(
        self, word_count, reading_time_minutes
    ):
        """
        Property 2: RssArticleMetrics non-negative values

        For any RssArticleMetrics instance created with word_count or reading_time,
        those values must be non-negative (>= 0).

        **Feature: refactor-article-aggregate, Property 2: RssArticleMetrics non-negative values**
        **Validates: Requirements 2.4**
        """
        # Si algún valor es negativo, debe lanzar error
        if (word_count is not None and word_count < 0) or (
            reading_time_minutes is not None and reading_time_minutes < 0
        ):
            with pytest.raises(ValueError) as exc_info:
                RssArticleMetrics.create(
                    word_count=word_count, reading_time_minutes=reading_time_minutes
                )

            # Verificar mensaje de error
            assert "no puede ser negativo" in str(exc_info.value).lower()
        else:
            # Si ambos son None o no negativos, debe crear correctamente
            metrics = RssArticleMetrics.create(
                word_count=word_count, reading_time_minutes=reading_time_minutes
            )

            # Verificar que se creó correctamente
            assert metrics is not None

            # Verificar valores
            if word_count is not None:
                assert metrics.word_count is not None
                assert metrics.word_count.value == word_count
                assert metrics.word_count.value >= 0
            else:
                assert metrics.word_count is None

            if reading_time_minutes is not None:
                assert metrics.reading_time is not None
                assert metrics.reading_time.minutes == reading_time_minutes
                assert metrics.reading_time.minutes >= 0
            else:
                assert metrics.reading_time is None

    @given(
        word_count=st.integers(min_value=0, max_value=10000),
        reading_time_minutes=st.integers(min_value=0, max_value=1000),
    )
    def test_content_metrics_immutability_property(
        self, word_count, reading_time_minutes
    ):
        """
        Property: RssArticleMetrics es inmutable.

        For any RssArticleMetrics instance, intentar modificar sus campos
        debe lanzar un error.
        """
        metrics = RssArticleMetrics.create(
            word_count=word_count, reading_time_minutes=reading_time_minutes
        )

        # Intentar modificar debe fallar (frozen dataclass)
        with pytest.raises(AttributeError):
            metrics.word_count = WordCount(value=999)  # type: ignore

    @given(
        original_wc=st.integers(min_value=0, max_value=10000),
        new_wc=st.integers(min_value=0, max_value=10000),
    )
    def test_with_word_count_returns_new_instance_property(self, original_wc, new_wc):
        """
        Property: with_word_count retorna nueva instancia sin modificar original.

        For any RssArticleMetrics instance, llamar with_word_count debe retornar
        una nueva instancia con el word_count actualizado, sin modificar la original.
        """
        original = RssArticleMetrics.create(
            word_count=original_wc, reading_time_minutes=5
        )
        new_word_count = WordCount(value=new_wc)
        updated = original.with_word_count(new_word_count)

        # Verificar que son instancias diferentes
        assert original is not updated

        # Verificar que el original no cambió
        assert original.word_count.value == original_wc

        # Verificar que el nuevo tiene el valor actualizado
        assert updated.word_count.value == new_wc

        # Verificar que reading_time se preservó
        assert updated.reading_time == original.reading_time

    def test_empty_factory_creates_valid_instance(self):
        """
        Property: empty() factory method crea instancia válida.

        El factory method empty() debe crear una instancia válida
        con todos los campos None.
        """
        metrics = RssArticleMetrics.empty()

        assert metrics is not None
        assert metrics.word_count is None
        assert metrics.reading_time is None
        assert metrics.has_metrics is False
        assert metrics.has_complete_metrics is False

    @given(
        word_count=st.one_of(st.none(), st.integers(min_value=0, max_value=10000)),
        reading_time=st.one_of(st.none(), st.integers(min_value=0, max_value=1000)),
    )
    def test_has_metrics_property_correctness(self, word_count, reading_time):
        """
        Property: has_metrics retorna True si al menos una métrica está presente.

        For any RssArticleMetrics instance, has_metrics debe retornar True
        si word_count o reading_time no son None.
        """
        metrics = RssArticleMetrics.create(
            word_count=word_count, reading_time_minutes=reading_time
        )

        expected = word_count is not None or reading_time is not None
        assert metrics.has_metrics == expected

    @given(
        word_count=st.one_of(st.none(), st.integers(min_value=0, max_value=10000)),
        reading_time=st.one_of(st.none(), st.integers(min_value=0, max_value=1000)),
    )
    def test_has_complete_metrics_property_correctness(self, word_count, reading_time):
        """
        Property: has_complete_metrics retorna True si todas las métricas están presentes.

        For any RssArticleMetrics instance, has_complete_metrics debe retornar True
        solo si tanto word_count como reading_time no son None.
        """
        metrics = RssArticleMetrics.create(
            word_count=word_count, reading_time_minutes=reading_time
        )

        expected = word_count is not None and reading_time is not None
        assert metrics.has_complete_metrics == expected

    @given(word_count=st.integers(min_value=0, max_value=10000))
    def test_create_with_only_word_count(self, word_count):
        """
        Property: Se puede crear RssArticleMetrics solo con word_count.

        For any non-negative word_count, se debe poder crear RssArticleMetrics
        con solo ese valor.
        """
        metrics = RssArticleMetrics.create(
            word_count=word_count, reading_time_minutes=None
        )

        assert metrics.word_count is not None
        assert metrics.word_count.value == word_count
        assert metrics.reading_time is None
        assert metrics.has_metrics is True
        assert metrics.has_complete_metrics is False

    @given(reading_time=st.integers(min_value=0, max_value=1000))
    def test_create_with_only_reading_time(self, reading_time):
        """
        Property: Se puede crear RssArticleMetrics solo con reading_time.

        For any non-negative reading_time, se debe poder crear RssArticleMetrics
        con solo ese valor.
        """
        metrics = RssArticleMetrics.create(
            word_count=None, reading_time_minutes=reading_time
        )

        assert metrics.word_count is None
        assert metrics.reading_time is not None
        assert metrics.reading_time.minutes == reading_time
        assert metrics.has_metrics is True
        assert metrics.has_complete_metrics is False
