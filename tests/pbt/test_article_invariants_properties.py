"""Property-based tests para RssArticle Invariants.

Feature: article-enterprise-refactoring
"""

from datetime import datetime, timedelta, timezone
from unittest.mock import Mock

import pytest
from hypothesis import assume, given
from hypothesis import strategies as st

from src.domain.services.articles.article_validation_service import (
    ArticleValidationService,
)
from src.rss.article.domain.aggregates.rss_article import RssArticle


class TestRssArticleInvariantsProperties:
    """Property tests para validación de invariantes."""

    @given(
        score=st.floats(
            min_value=-10.0, max_value=10.0, allow_nan=False, allow_infinity=False
        )
    )
    def test_score_invariants_validated_consistently(self, score):
        """
        Property 3: Invariantes son validados en modificaciones.

        Feature: article-enterprise-refactoring, Property 3
        Validates: Requirements 12.1

        Para cualquier score, validate_scores debe detectar consistentemente
        si está fuera del rango [0.0, 1.0].
        """
        # Arrange
        service = ArticleValidationService()
        article = Mock(spec=Article)
        article.quality_vo = Mock()
        article.quality.quality_score = score
        article.quality.readability_score = None
        article.validation_info = None

        # Act
        violations = service.validate_scores(article)

        # Assert
        if 0.0 <= score <= 1.0:
            # Score válido - no debe haber violaciones
            assert (
                len(violations) == 0
            ), f"Score {score} es válido pero se reportó violación"
        else:
            # Score inválido - debe haber exactamente 1 violación
            assert (
                len(violations) == 1
            ), f"Score {score} es inválido pero no se reportó violación"
            assert violations[0].field == "quality_score"
            assert violations[0].error_code == "OUT_OF_RANGE"
            assert violations[0].current_value == score

    @given(hours_diff=st.integers(min_value=-100, max_value=100))
    def test_timestamp_invariants_validated_consistently(self, hours_diff):
        """
        Property: Timestamps son validados consistentemente.

        Feature: article-enterprise-refactoring, Property 3
        Validates: Requirements 12.3

        Para cualquier diferencia de tiempo entre created_at y updated_at,
        validate_timestamps debe detectar consistentemente si created_at > updated_at.
        """
        # Arrange
        service = ArticleValidationService()
        article = Mock(spec=Article)

        base_time = datetime.now(timezone.utc)
        article.created_at = base_time
        article.updated_at = base_time + timedelta(hours=hours_diff)
        article.published_at = None

        # Act
        violations = service.validate_timestamps(article)

        # Assert
        if hours_diff >= 0:
            # created_at <= updated_at - válido
            assert (
                len(violations) == 0
            ), f"Timestamps válidos pero se reportó violación (diff={hours_diff}h)"
        else:
            # created_at > updated_at - inválido
            assert (
                len(violations) == 1
            ), f"Timestamps inválidos pero no se reportó violación (diff={hours_diff}h)"
            assert violations[0].field == "timestamps"
            assert violations[0].error_code == "INVALID_TIMESTAMP_ORDER"

    @given(
        content_length=st.integers(min_value=1, max_value=500)  # Empezar desde 1, no 0
    )
    def test_content_length_invariants_validated_consistently(self, content_length):
        """
        Property: Longitud de contenido es validada consistentemente.

        Feature: article-enterprise-refactoring, Property 3
        Validates: Requirements 12.4

        Para cualquier longitud de contenido (>0), validate_content_invariants
        debe detectar consistentemente si es menor a MIN_CONTENT_LENGTH (100).

        Nota: content_length=0 (string vacío) no se valida porque el campo es opcional.
        """
        # Arrange
        service = ArticleValidationService()
        article = Mock(spec=Article)
        article.content_vo.markdown = "A" * content_length
        article.title = "Valid Title"
        article.url = "https://example.com"

        # Act
        violations = service.validate_content_invariants(article)

        # Assert
        content_violations = [v for v in violations if v.field == "content"]

        if content_length >= 100:
            # Contenido suficiente - no debe haber violación de contenido
            assert (
                len(content_violations) == 0
            ), f"Contenido de {content_length} chars es válido pero se reportó violación"
        else:
            # Contenido insuficiente - debe haber violación de contenido
            assert (
                len(content_violations) == 1
            ), f"Contenido de {content_length} chars es inválido pero no se reportó violación"
            assert content_violations[0].error_code == "INSUFFICIENT_CONTENT"

    @given(
        title_length=st.integers(min_value=1, max_value=600)  # Empezar desde 1, no 0
    )
    def test_title_length_invariants_validated_consistently(self, title_length):
        """
        Property: Longitud de título es validada consistentemente.

        Feature: article-enterprise-refactoring, Property 3
        Validates: Requirements 12.4

        Para cualquier longitud de título (>0), validate_content_invariants
        debe detectar consistentemente si excede MAX_TITLE_LENGTH (500).

        Nota: title_length=0 (string vacío) no se valida porque el campo es opcional.
        """
        # Arrange
        service = ArticleValidationService()
        article = Mock(spec=Article)
        article.content_vo.markdown = "A" * 150  # Contenido válido
        article.title = "A" * title_length
        article.url = "https://example.com"

        # Act
        violations = service.validate_content_invariants(article)

        # Assert
        title_violations = [v for v in violations if v.field == "title"]

        if title_length > 500:
            # Título demasiado largo - debe haber violación
            assert (
                len(title_violations) == 1
            ), f"Título de {title_length} chars es inválido pero no se reportó violación"
            assert title_violations[0].error_code == "TITLE_TOO_LONG"
        else:
            # Título válido - no debe haber violación
            assert (
                len(title_violations) == 0
            ), f"Título de {title_length} chars es válido pero se reportó violación"

    @given(
        has_id=st.booleans(),
        has_source_id=st.booleans(),
        quality_score=st.one_of(
            st.none(), st.floats(min_value=-1.0, max_value=2.0, allow_nan=False)
        ),
        content_length=st.integers(min_value=1, max_value=200),  # Empezar desde 1, no 0
    )
    def test_validate_all_invariants_detects_all_violations(
        self, has_id, has_source_id, quality_score, content_length
    ):
        """
        Property: validate_all_invariants detecta todas las violaciones.

        Feature: article-enterprise-refactoring, Property 3
        Validates: Requirements 12.1

        Para cualquier combinación de valores inválidos, validate_all_invariants
        debe detectar todas las violaciones, no solo la primera.

        Nota: content_length=0 no se prueba porque el campo es opcional.
        """
        # Arrange
        service = ArticleValidationService()
        article = Mock(spec=Article)
        article.id = "article-123" if has_id else None
        article.source_id = "source-456" if has_source_id else None
        article.quality.quality_score = quality_score
        article.quality.readability_score = None
        article.validation_score = None
        article.content_vo.markdown = "A" * content_length
        article.title = "Valid Title"
        article.url = "https://example.com"
        article.created_at = datetime.now(timezone.utc)
        article.updated_at = datetime.now(timezone.utc)
        article.published_at = None

        # Act
        violations = service.validate_all_invariants(article)

        # Assert - Contar violaciones esperadas
        expected_violations = 0

        if not has_id:
            expected_violations += 1
        if not has_source_id:
            expected_violations += 1
        if quality_score is not None and not (0.0 <= quality_score <= 1.0):
            expected_violations += 1
        if content_length > 0 and content_length < 100:  # Solo si content no está vacío
            expected_violations += 1

        assert len(violations) == expected_violations, (
            f"Esperadas {expected_violations} violaciones, "
            f"pero se encontraron {len(violations)}: {[v.field for v in violations]}"
        )
