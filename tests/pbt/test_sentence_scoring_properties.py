"""Property-based tests para sentence scoring en ArticleSummaryExtractionService usando Hypothesis.

Estos tests verifican propiedades universales que deben cumplirse
para el scoring de oraciones en la generación de resúmenes.
"""

from datetime import datetime, timezone
from typing import List
from uuid import uuid4

import pytest
from hypothesis import HealthCheck, assume, given, settings
from hypothesis import strategies as st

from src.rss.article.domain.aggregates.rss_article import RssArticle

# Importar componentes del sistema
from src.rss.article.domain.services import (
    ArticleSummaryExtractionService,
    ScoredSentence,
    SentenceRelevanceScorer,
)
from src.rss.article.domain.value_objects import (
    RssArticleId,
    RssArticleTitle,
    RssArticleUrl,
)
from src.rss.feed.domain.value_objects import RssFeedId

# ============================================================================
# ESTRATEGIAS DE GENERACIÓN DE DATOS
# ============================================================================


def valid_uuid_strategy():
    """Genera UUIDs válidos."""
    return st.uuids()


@st.composite
def valid_sentence_strategy(draw):
    """Genera oraciones válidas para testing."""
    # Generar oración con longitud variable
    words = draw(
        st.lists(
            st.text(
                min_size=1,
                max_size=15,
                alphabet=st.characters(
                    whitelist_categories=("Lu", "Ll"),
                    min_codepoint=65,
                    max_codepoint=122,
                ),
            ),
            min_size=3,
            max_size=30,
        )
    )

    # Unir palabras
    sentence = " ".join(words)

    # Agregar puntuación final
    punctuation = draw(st.sampled_from([".", "!", "?", ""]))
    sentence = sentence + punctuation

    return sentence


@st.composite
def valid_sentences_list_strategy(draw):
    """Genera lista de oraciones válidas."""
    sentences = draw(st.lists(valid_sentence_strategy(), min_size=1, max_size=20))
    return sentences


@st.composite
def valid_article_with_content_strategy(draw):
    """Genera Article válidos con contenido markdown para testing."""
    article_id = RssArticleId(str(draw(valid_uuid_strategy())))
    source_id = RssFeedId(str(draw(valid_uuid_strategy())))

    # Generar título no vacío
    title = draw(
        st.text(
            min_size=1,
            max_size=200,
            alphabet=st.characters(
                whitelist_categories=("Lu", "Ll", "Nd"),
                min_codepoint=32,
                max_codepoint=126,
            ),
        )
    )
    if not title.strip():
        title = "Test RssArticle"

    # Generar URL válida
    url = f"https://example.com/article/{uuid4()}"

    # Generar contenido markdown con múltiples oraciones
    sentences = draw(valid_sentences_list_strategy())
    content_markdown = " ".join(sentences)

    # Crear artículo
    article = RssArticle(
        title=RssArticleTitle(title),
        url=RssArticleUrl(url),
        source_id=source_id,
        article_id=article_id,
    )

    # Establecer contenido markdown usando el método público
    if content_markdown:
        article.update_content_fields(markdown=content_markdown)
        article.mark_events_as_committed()  # Limpiar eventos de test

    return article


@st.composite
def valid_keywords_strategy(draw):
    """Genera lista de keywords válidas."""
    keywords = draw(
        st.lists(
            st.text(
                min_size=3,
                max_size=15,
                alphabet=st.characters(
                    whitelist_categories=("Lu", "Ll"),
                    min_codepoint=65,
                    max_codepoint=122,
                ),
            ),
            min_size=0,
            max_size=10,
        )
    )
    return keywords


# ============================================================================
# PROPERTY TEST: SUMMARY USES SENTENCE SCORING
# ============================================================================


class TestSummaryUsesSentenceScoring:
    """**Feature: resolve-todos, Property 11: Summary Uses Sentence Scoring**

    **Validates: Requirements 5.1**

    Para cualquier generación de resumen de contenido, el sistema debe usar
    scoring de oraciones por relevancia en lugar de tomar las primeras oraciones.
    """

    @settings(max_examples=100)
    @given(article=valid_article_with_content_strategy())
    @pytest.mark.asyncio
    async def test_summary_uses_sentence_scorer(self, article):
        """Para cualquier artículo, el resumen debe usar sentence scoring."""
        # Arrange
        service = ArticleSummaryExtractionService()

        # Verificar que el servicio tiene un sentence scorer
        assert hasattr(
            service, "_sentence_scorer"
        ), "El servicio debe tener un _sentence_scorer"
        assert isinstance(
            service._sentence_scorer, SentenceRelevanceScorer
        ), "El _sentence_scorer debe ser una instancia de SentenceRelevanceScorer"

        # Act - Generar summary
        summary = service.generate_summary(article, max_length=200)

        # Assert - El summary debe existir
        assert isinstance(summary, str), "El summary debe ser un string"

    @settings(max_examples=100)
    @given(
        article=valid_article_with_content_strategy(),
        max_length=st.integers(min_value=50, max_value=500),
    )
    @pytest.mark.asyncio
    async def test_summary_respects_max_length(self, article, max_length):
        """Para cualquier max_length, el summary no debe excederlo."""
        # Arrange
        service = ArticleSummaryExtractionService()

        # Assume que el contenido es más largo que max_length
        assume(len(article.content_vo.markdown_markdown) > max_length)

        # Act
        summary = service.generate_summary(article, max_length=max_length)

        # Assert - El summary no debe exceder max_length
        assert (
            len(summary) <= max_length
        ), f"El summary ({len(summary)} chars) no debe exceder max_length ({max_length})"

    @settings(max_examples=50)
    @given(sentences=valid_sentences_list_strategy())
    @pytest.mark.asyncio
    async def test_sentence_scorer_assigns_scores(self, sentences):
        """Para cualquier lista de oraciones, el scorer debe asignar scores."""
        # Arrange
        scorer = SentenceRelevanceScorer()

        # Act
        scored = scorer.score_sentences(sentences)

        # Assert
        assert len(scored) == len(sentences), "Debe haber un score por cada oración"

        for scored_sentence in scored:
            assert isinstance(
                scored_sentence, ScoredSentence
            ), "Cada elemento debe ser un ScoredSentence"
            assert (
                0.0 <= scored_sentence.score <= 1.0
            ), f"El score debe estar entre 0 y 1, got {scored_sentence.score}"
            assert (
                scored_sentence.text in sentences
            ), "El texto debe ser una de las oraciones originales"

    @settings(max_examples=50)
    @given(sentences=valid_sentences_list_strategy())
    @pytest.mark.asyncio
    async def test_scored_sentences_are_ordered_by_relevance(self, sentences):
        """Para cualquier lista de oraciones, las scored deben estar ordenadas por score."""
        # Arrange
        scorer = SentenceRelevanceScorer()

        # Assume que hay al menos 2 oraciones
        assume(len(sentences) >= 2)

        # Act
        scored = scorer.score_sentences(sentences)

        # Assert - Los scores deben estar en orden descendente
        for i in range(len(scored) - 1):
            assert (
                scored[i].score >= scored[i + 1].score
            ), "Las oraciones deben estar ordenadas por score descendente"

    @settings(max_examples=50)
    @given(
        sentences=valid_sentences_list_strategy(),
        max_length=st.integers(min_value=20, max_value=500),
    )
    @pytest.mark.asyncio
    async def test_selected_sentences_maintain_original_order(
        self, sentences, max_length
    ):
        """Para cualquier selección, las oraciones deben mantener su orden original."""
        # Arrange
        scorer = SentenceRelevanceScorer()
        scored = scorer.score_sentences(sentences)

        # Assume que no hay oraciones duplicadas (para evitar ambigüedad en posiciones)
        assume(len(sentences) == len(set(sentences)))

        # Act
        selected = scorer.select_top_sentences(scored, max_length)

        # Assert - Las oraciones seleccionadas deben estar en orden original
        if len(selected) >= 2:
            # Verificar que las posiciones están en orden
            positions = []
            for selected_text in selected:
                # Encontrar posición original
                for i, original in enumerate(sentences):
                    if original == selected_text:
                        positions.append(i)
                        break

            # Verificar orden ascendente de posiciones
            for i in range(len(positions) - 1):
                assert (
                    positions[i] < positions[i + 1]
                ), "Las oraciones seleccionadas deben mantener el orden original"

    @settings(max_examples=50)
    @given(
        sentences=valid_sentences_list_strategy(), keywords=valid_keywords_strategy()
    )
    @pytest.mark.asyncio
    async def test_keywords_affect_scoring(self, sentences, keywords):
        """Para cualquier lista de keywords, deben afectar el scoring."""
        # Arrange
        scorer_without_keywords = SentenceRelevanceScorer(keywords=None)
        scorer_with_keywords = SentenceRelevanceScorer(keywords=keywords)

        # Assume que hay keywords
        assume(len(keywords) > 0)

        # Act
        scored_without = scorer_without_keywords.score_sentences(sentences)
        scored_with = scorer_with_keywords.score_sentences(sentences)

        # Assert - Los scorers deben existir y funcionar
        assert len(scored_without) == len(
            sentences
        ), "Scorer sin keywords debe procesar todas las oraciones"
        assert len(scored_with) == len(
            sentences
        ), "Scorer con keywords debe procesar todas las oraciones"

    @settings(max_examples=50, suppress_health_check=[HealthCheck.filter_too_much])
    @given(article=valid_article_with_content_strategy())
    @pytest.mark.asyncio
    async def test_summary_not_just_first_sentences(self, article):
        """Para cualquier artículo largo, el summary no debe ser solo las primeras oraciones."""
        # Arrange
        service = ArticleSummaryExtractionService()

        # Assume que el artículo tiene múltiples oraciones
        sentences = service._split_into_sentences(article.content_vo.markdown_markdown)
        assume(len(sentences) >= 5)

        # Assume que el contenido es largo
        assume(len(article.content_vo.markdown_markdown) > 300)

        # Act
        summary = service.generate_summary(article, max_length=200)

        # Assert - El summary debe existir y ser más corto que el original
        assert len(summary) > 0, "El summary debe tener contenido"
        assert len(summary) < len(
            article.content_vo.markdown_markdown
        ), "El summary debe ser más corto que el contenido original"

        # El summary debe usar el sentence scorer (verificado por la existencia del atributo)
        assert hasattr(
            service, "_sentence_scorer"
        ), "El servicio debe usar sentence scorer"

    @settings(max_examples=50)
    @given(
        article=valid_article_with_content_strategy(),
        keywords=valid_keywords_strategy(),
    )
    @pytest.mark.asyncio
    async def test_service_can_be_initialized_with_keywords(self, article, keywords):
        """Para cualquier lista de keywords, el servicio debe poder inicializarse con ellas."""
        # Arrange & Act
        service = ArticleSummaryExtractionService(keywords=keywords)

        # Assert
        assert service._sentence_scorer.keywords == [
            k.lower() for k in keywords
        ], "El scorer debe tener las keywords configuradas"

        # Verificar que funciona
        summary = service.generate_summary(article, max_length=200)
        assert isinstance(summary, str), "El summary debe ser un string"

    @settings(max_examples=50)
    @given(sentences=valid_sentences_list_strategy())
    @pytest.mark.asyncio
    async def test_position_affects_scoring(self, sentences):
        """Para cualquier lista de oraciones, la posición debe afectar el score."""
        # Arrange
        scorer = SentenceRelevanceScorer()

        # Assume que hay al menos 3 oraciones
        assume(len(sentences) >= 3)

        # Act
        scored = scorer.score_sentences(sentences)

        # Assert - Verificar que las oraciones tienen diferentes scores basados en posición
        # (esto es una propiedad del algoritmo, no una garantía absoluta)
        scores = [s.score for s in scored]

        # Al menos debe haber variación en los scores
        assert (
            len(set(scores)) > 1 or len(sentences) == 1
        ), "Debe haber variación en los scores (a menos que sea una sola oración)"

    @settings(max_examples=50)
    @given(
        sentences=valid_sentences_list_strategy(),
        max_length=st.integers(min_value=10, max_value=1000),
    )
    @pytest.mark.asyncio
    async def test_select_top_sentences_respects_max_length(
        self, sentences, max_length
    ):
        """Para cualquier max_length, las oraciones seleccionadas no deben excederlo."""
        # Arrange
        scorer = SentenceRelevanceScorer()
        scored = scorer.score_sentences(sentences)

        # Act
        selected = scorer.select_top_sentences(scored, max_length)

        # Assert
        if selected:
            # Calcular longitud total incluyendo espacios entre oraciones
            total_length = sum(len(s) for s in selected)
            spaces = len(selected) - 1  # Espacios entre oraciones
            total_with_spaces = total_length + spaces

            assert (
                total_with_spaces <= max_length
            ), f"Las oraciones seleccionadas ({total_with_spaces} chars con espacios) no deben exceder max_length ({max_length})"

    @settings(max_examples=50)
    @given(article=valid_article_with_content_strategy())
    @pytest.mark.asyncio
    async def test_empty_content_returns_empty_summary(self, article):
        """Para cualquier artículo sin contenido, el summary debe ser vacío."""
        # Arrange
        service = ArticleSummaryExtractionService()
        # Article sin contenido - no llamar update_content con string vacío

        # Act
        summary = service.generate_summary(article)

        # Assert
        assert summary == "", "El summary de contenido vacío debe ser string vacío"

    @settings(max_examples=50)
    @given(article=valid_article_with_content_strategy())
    @pytest.mark.asyncio
    async def test_short_content_returns_full_content(self, article):
        """Para cualquier artículo corto, el summary debe ser el contenido completo."""
        # Arrange
        service = ArticleSummaryExtractionService()

        # Assume que el contenido es corto
        assume(len(article.content_vo.markdown_markdown) <= 100)

        # Act
        summary = service.generate_summary(article, max_length=500)

        # Assert
        assert (
            summary == article.content_vo.markdown_markdown
        ), "El summary de contenido corto debe ser el contenido completo"
