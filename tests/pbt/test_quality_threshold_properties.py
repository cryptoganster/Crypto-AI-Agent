"""Property-based tests para ArticleQualityService con QualityThreshold usando Hypothesis.

Estos tests verifican propiedades universales que deben cumplirse
para el servicio de calidad con configuración de threshold.
"""

from datetime import datetime, timezone
from typing import Optional
from unittest.mock import Mock
from uuid import uuid4

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from src.domain.value_objects.classification import QualityLevel
from src.domain.value_objects.fetching import QualityThreshold
from src.rss.article.domain.aggregates.rss_article import RssArticle
from src.rss.article.domain.value_objects import (
    RssArticleId,
    RssArticleTitle,
    RssArticleUrl,
)

# Importar componentes del sistema
from src.rss.article.infra.services import ArticleQualityService
from src.rss.feed.domain.value_objects import RssFeedId

# ============================================================================
# ESTRATEGIAS DE GENERACIÓN DE DATOS
# ============================================================================


def valid_uuid_strategy():
    """Genera UUIDs válidos."""
    return st.uuids()


@st.composite
def valid_quality_threshold_strategy(draw):
    """Genera QualityThreshold válidos."""
    score = draw(st.floats(min_value=0.0, max_value=1.0))
    description = draw(st.one_of(st.none(), st.text(min_size=1, max_size=100)))
    return QualityThreshold(score=score, description=description)


@st.composite
def valid_article_strategy(draw):
    """Genera Article válidos para testing."""
    article_id = RssArticleId(str(draw(valid_uuid_strategy())))
    source_id = RssFeedId(str(draw(valid_uuid_strategy())))

    # Generar título no vacío
    title = draw(
        st.text(
            min_size=1,
            max_size=200,
            alphabet=st.characters(blacklist_categories=("Cs",)),
        )
    )
    if not title.strip():
        title = "Test RssArticle"

    # Generar URL válida
    url = f"https://example.com/article/{uuid4()}"

    # Generar contenido markdown no vacío
    content_markdown = draw(
        st.text(
            min_size=10,
            max_size=1000,
            alphabet=st.characters(blacklist_categories=("Cs",)),
        )
    )
    if not content_markdown.strip():
        content_markdown = "This is test content for the article."

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


# ============================================================================
# PROPERTY TEST: QUALITY THRESHOLD FROM CONFIGURATION
# ============================================================================


class TestQualityThresholdFromConfiguration:
    """**Feature: resolve-todos, Property 10: Quality Threshold from Configuration**

    **Validates: Requirements 4.6**

    Para cualquier verificación de calidad, el threshold debe venir de un
    Configuration Value Object, no hardcodeado.
    """

    @settings(max_examples=100)
    @given(threshold=valid_quality_threshold_strategy())
    @pytest.mark.asyncio
    async def test_service_uses_configured_threshold(self, threshold):
        """Para cualquier threshold configurado, el servicio debe usarlo en lugar de un valor hardcodeado."""
        # Arrange - Crear servicio con threshold configurado
        service = ArticleQualityService(quality_threshold=threshold)

        # Verificar que el servicio tiene el threshold configurado
        assert (
            service._quality_threshold == threshold
        ), "El servicio debe usar el threshold configurado"
        assert (
            service._quality_threshold.score == threshold.score
        ), "El score del threshold debe coincidir con el configurado"

    @settings(max_examples=100)
    @given(
        threshold=valid_quality_threshold_strategy(), article=valid_article_strategy()
    )
    @pytest.mark.asyncio
    async def test_threshold_affects_quality_check(self, threshold, article):
        """Para cualquier threshold, debe afectar la verificación de calidad mínima."""
        # Arrange - Crear servicio con threshold
        service = ArticleQualityService(quality_threshold=threshold)

        # Crear quality level con score conocido
        quality_level = QualityLevel.from_score(0.6, confidence=1.0)

        # Act - Verificar si cumple el threshold
        meets_threshold = service._meets_minimum_quality_threshold(quality_level)

        # Assert - El resultado debe depender del threshold configurado, no hardcodeado
        expected = quality_level.score >= threshold.score
        assert (
            meets_threshold == expected
        ), f"El threshold configurado ({threshold.score}) debe determinar si cumple (score: {quality_level.score})"

    @settings(max_examples=100)
    @given(threshold=valid_quality_threshold_strategy())
    @pytest.mark.asyncio
    async def test_service_without_threshold_uses_default(self, threshold):
        """Para cualquier servicio sin threshold explícito, debe usar un default (no hardcodeado 0.5)."""
        # Arrange - Crear servicio sin threshold
        service = ArticleQualityService()

        # Assert - Debe tener un threshold por defecto (QualityThreshold.medium())
        assert (
            service._quality_threshold is not None
        ), "El servicio debe tener un threshold por defecto"
        assert isinstance(
            service._quality_threshold, QualityThreshold
        ), "El threshold por defecto debe ser un QualityThreshold VO"
        assert (
            service._quality_threshold.score == 0.5
        ), "El threshold por defecto debe ser medium (0.5)"

    @settings(max_examples=50)
    @given(
        low_threshold=st.floats(min_value=0.0, max_value=0.3),
        high_threshold=st.floats(min_value=0.7, max_value=1.0),
    )
    @pytest.mark.asyncio
    async def test_different_thresholds_produce_different_results(
        self, low_threshold, high_threshold
    ):
        """Para diferentes thresholds, el mismo quality level puede cumplir o no cumplir."""
        # Arrange - Crear servicios con diferentes thresholds
        service_low = ArticleQualityService(
            quality_threshold=QualityThreshold(score=low_threshold)
        )
        service_high = ArticleQualityService(
            quality_threshold=QualityThreshold(score=high_threshold)
        )

        # Quality level intermedio
        quality_level = QualityLevel.from_score(0.5, confidence=1.0)

        # Act
        meets_low = service_low._meets_minimum_quality_threshold(quality_level)
        meets_high = service_high._meets_minimum_quality_threshold(quality_level)

        # Assert - Diferentes thresholds deben producir diferentes resultados
        assert (
            meets_low is True
        ), f"Quality level 0.5 debe cumplir threshold bajo ({low_threshold})"
        assert (
            meets_high is False
        ), f"Quality level 0.5 no debe cumplir threshold alto ({high_threshold})"

    @settings(max_examples=100)
    @given(threshold=valid_quality_threshold_strategy())
    @pytest.mark.asyncio
    async def test_threshold_is_value_object_not_primitive(self, threshold):
        """Para cualquier threshold, debe ser un Value Object, no un float primitivo."""
        # Arrange - Crear servicio
        service = ArticleQualityService(quality_threshold=threshold)

        # Assert - El threshold debe ser un VO
        assert isinstance(
            service._quality_threshold, QualityThreshold
        ), "El threshold debe ser un QualityThreshold Value Object, no un float primitivo"
        assert hasattr(
            service._quality_threshold, "score"
        ), "El threshold VO debe tener un atributo 'score'"
        assert hasattr(
            service._quality_threshold, "description"
        ), "El threshold VO debe tener un atributo 'description'"

    @settings(max_examples=100)
    @given(
        threshold_score=st.floats(min_value=0.0, max_value=1.0),
        quality_score=st.floats(min_value=0.0, max_value=1.0),
    )
    @pytest.mark.asyncio
    async def test_threshold_comparison_is_consistent(
        self, threshold_score, quality_score
    ):
        """Para cualquier par de scores, la comparación debe ser consistente."""
        # Arrange
        threshold = QualityThreshold(score=threshold_score)
        service = ArticleQualityService(quality_threshold=threshold)
        quality_level = QualityLevel.from_score(quality_score, confidence=1.0)

        # Act
        meets_threshold = service._meets_minimum_quality_threshold(quality_level)

        # Assert - La comparación debe ser consistente con la lógica esperada
        expected = quality_score >= threshold_score
        assert (
            meets_threshold == expected
        ), f"La comparación debe ser consistente: {quality_score} >= {threshold_score} = {expected}"

    @settings(max_examples=50)
    @given(article=valid_article_strategy())
    @pytest.mark.asyncio
    async def test_predefined_thresholds_work_correctly(self, article):
        """Para cualquier artículo, los thresholds predefinidos deben funcionar correctamente."""
        # Arrange - Usar thresholds predefinidos
        service_low = ArticleQualityService(quality_threshold=QualityThreshold.low())
        service_medium = ArticleQualityService(
            quality_threshold=QualityThreshold.medium()
        )
        service_high = ArticleQualityService(quality_threshold=QualityThreshold.high())

        # Verificar que los thresholds predefinidos tienen los valores correctos
        assert (
            service_low._quality_threshold.score == 0.3
        ), "QualityThreshold.low() debe tener score 0.3"
        assert (
            service_medium._quality_threshold.score == 0.5
        ), "QualityThreshold.medium() debe tener score 0.5"
        assert (
            service_high._quality_threshold.score == 0.7
        ), "QualityThreshold.high() debe tener score 0.7"

    @settings(max_examples=100)
    @given(
        threshold=valid_quality_threshold_strategy(), article=valid_article_strategy()
    )
    @pytest.mark.asyncio
    async def test_calculate_quality_score_independent_of_threshold(
        self, threshold, article
    ):
        """Para cualquier threshold, el cálculo de quality score debe ser independiente del threshold."""
        # Arrange - Crear dos servicios con diferentes thresholds
        service1 = ArticleQualityService(quality_threshold=threshold)
        service2 = ArticleQualityService(
            quality_threshold=QualityThreshold(
                score=threshold.score + 0.1 if threshold.score < 0.9 else 0.9
            )
        )

        # Act - Calcular quality score con ambos servicios
        score1 = service1.calculate_content_quality_score(article)
        score2 = service2.calculate_content_quality_score(article)

        # Assert - El score calculado debe ser el mismo independientemente del threshold
        assert (
            score1 == score2
        ), "El cálculo de quality score debe ser independiente del threshold configurado"
        assert 0.0 <= score1 <= 1.0, "El quality score debe estar en el rango válido"
