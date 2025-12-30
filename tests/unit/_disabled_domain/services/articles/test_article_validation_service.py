"""Unit tests para ArticleValidationService con Specifications."""

from datetime import datetime, timedelta, timezone
from unittest.mock import Mock

import pytest

from src.domain.services.articles.article_validation_service import (
    ArticleValidationService,
)
from src.rss.article.domain.aggregates.rss_article import RssArticle
from src.rss.article.domain.value_objects.invariant_violation import InvariantViolation


class TestRssArticleValidationServiceInvariants:
    """Tests para validaciones de invariantes usando Specifications."""

    @pytest.fixture
    def service(self):
        """Crea instancia del servicio."""
        return ArticleValidationService()

    @pytest.fixture
    def valid_article(self):
        """Crea artículo válido para tests."""
        article = Mock(spec=Article)

        # Identity VO
        article.identity_vo = Mock()
        article.identity_vo.article_id = "article-123"
        article.identity_vo.source_id = "source-456"
        article.identity_vo.url = Mock()
        article.identity_vo.url.__str__ = Mock(
            return_value="https://example.com/article"
        )
        article.identity_vo.url.__bool__ = Mock(return_value=True)

        # Metadata VO
        article.metadata_vo = Mock()
        article.metadata.title = Mock()
        article.metadata.title.__str__ = Mock(return_value="Valid RssArticle Title")
        article.metadata.title.__bool__ = Mock(return_value=True)

        # Content VO
        article.content_vo = Mock()
        article.content_vo.markdown = "A" * 150  # Contenido suficiente
        article.content_vo.plaintext = None

        # Quality VO
        article.quality_vo = Mock()
        article.quality.quality_score = 0.8
        article.quality.readability_score = Mock(value=0.7)
        article.quality.quality_level = "high"

        # Validation info
        article.validation_info = Mock()
        article.validation_info.score = 0.9

        # Timestamps
        article.created_at = datetime.now(timezone.utc) - timedelta(hours=1)
        article.updated_at = datetime.now(timezone.utc)
        article.published_at = None

        return article

    # ========== Tests de validate_identity ==========

    def test_validate_identity_with_valid_article(self, service, valid_article):
        """Debería retornar lista vacía para artículo válido."""
        # Act
        violations = service.validate_identity(valid_article)

        # Assert
        assert violations == []

    def test_validate_identity_with_missing_id(self, service, valid_article):
        """Debería detectar ID faltante."""
        # Arrange
        valid_article.identity_vo.article_id = None

        # Act
        violations = service.validate_identity(valid_article)

        # Assert
        assert len(violations) == 1
        assert violations[0].field == "id"
        assert violations[0].error_code == "MISSING_ID"
        assert "ID no puede ser None" in violations[0].message

    def test_validate_identity_with_missing_source_id(self, service, valid_article):
        """Debería detectar source_id faltante."""
        # Arrange
        valid_article.identity_vo.source_id = None

        # Act
        violations = service.validate_identity(valid_article)

        # Assert
        assert len(violations) == 1
        assert violations[0].field == "source_id"
        assert violations[0].error_code == "MISSING_SOURCE_ID"
        assert "RssFeed ID no puede ser None" in violations[0].message

    def test_validate_identity_with_both_missing(self, service, valid_article):
        """Debería detectar múltiples violaciones."""
        # Arrange
        valid_article.identity_vo.article_id = None
        valid_article.identity_vo.source_id = None

        # Act
        violations = service.validate_identity(valid_article)

        # Assert
        assert len(violations) == 2
        assert any(v.field == "id" for v in violations)
        assert any(v.field == "source_id" for v in violations)

    # ========== Tests de validate_scores ==========

    def test_validate_scores_with_valid_scores(self, service, valid_article):
        """Debería retornar lista vacía para scores válidos."""
        # Act
        violations = service.validate_scores(valid_article)

        # Assert
        assert violations == []

    def test_validate_scores_with_invalid_quality_score(self, service, valid_article):
        """Debería detectar quality_score fuera de rango."""
        # Arrange
        valid_article.quality.quality_score = 1.5

        # Act
        violations = service.validate_scores(valid_article)

        # Assert
        assert len(violations) == 1
        assert violations[0].field == "quality_score"
        assert violations[0].error_code == "OUT_OF_RANGE"
        assert violations[0].current_value == 1.5

    def test_validate_scores_with_negative_score(self, service, valid_article):
        """Debería detectar score negativo."""
        # Arrange
        # Modificar el quality_vo con un score inválido (mock permite esto)
        valid_article.quality.quality_score = -0.1

        # Act
        violations = service.validate_scores(valid_article)

        # Assert
        assert len(violations) == 1
        assert violations[0].field == "quality_score"
        assert violations[0].error_code == "OUT_OF_RANGE"

    def test_validate_scores_with_multiple_invalid_scores(self, service, valid_article):
        """Debería detectar múltiples scores inválidos."""
        # Arrange
        # Modificar scores con valores inválidos (mock permite esto)
        valid_article.quality.quality_score = 1.5  # Inválido > 1.0
        valid_article.quality.readability_score = Mock(value=-0.1)  # Inválido < 0
        valid_article.validation_info.score = 2.0  # Inválido > 1.0

        # Act
        violations = service.validate_scores(valid_article)

        # Assert
        assert len(violations) == 3
        assert any(v.field == "quality_score" for v in violations)
        assert any(v.field == "readability_score" for v in violations)
        assert any(v.field == "validation_score" for v in violations)
        assert any(v.field == "readability_score" for v in violations)
        assert any(v.field == "validation_score" for v in violations)

    def test_validate_scores_with_none_scores(self, service, valid_article):
        """Debería ignorar scores None (opcionales)."""
        # Arrange
        valid_article.quality.quality_score = None
        valid_article.quality.readability_score = None
        valid_article.validation_score = None

        # Act
        violations = service.validate_scores(valid_article)

        # Assert
        assert violations == []

    # ========== Tests de validate_timestamps ==========

    def test_validate_timestamps_with_valid_order(self, service, valid_article):
        """Debería retornar lista vacía para timestamps válidos."""
        # Act
        violations = service.validate_timestamps(valid_article)

        # Assert
        assert violations == []

    def test_validate_timestamps_with_invalid_order(self, service, valid_article):
        """Debería detectar created_at > updated_at."""
        # Arrange
        valid_article.created_at = datetime.now(timezone.utc)
        valid_article.updated_at = datetime.now(timezone.utc) - timedelta(hours=1)

        # Act
        violations = service.validate_timestamps(valid_article)

        # Assert
        assert len(violations) == 1
        assert violations[0].field == "timestamps"
        assert violations[0].error_code == "INVALID_TIMESTAMP_ORDER"
        assert "created_at" in violations[0].message

    def test_validate_timestamps_with_none_timestamps(self, service, valid_article):
        """Debería ignorar timestamps None."""
        # Arrange
        valid_article.created_at = None
        valid_article.updated_at = None

        # Act
        violations = service.validate_timestamps(valid_article)

        # Assert
        assert violations == []

    # ========== Tests de validate_content_invariants ==========

    def test_validate_content_invariants_with_valid_content(
        self, service, valid_article
    ):
        """Debería retornar lista vacía para contenido válido."""
        # Act
        violations = service.validate_content_invariants(valid_article)

        # Assert
        assert violations == []

    def test_validate_content_invariants_with_insufficient_content(
        self, service, valid_article
    ):
        """Debería detectar contenido insuficiente."""
        # Arrange
        valid_article.content_vo.markdown = "Short"  # < 100 caracteres

        # Act
        violations = service.validate_content_invariants(valid_article)

        # Assert
        assert len(violations) == 1
        assert violations[0].field == "content"
        assert violations[0].error_code == "INSUFFICIENT_CONTENT"

    def test_validate_content_invariants_with_empty_title(self, service, valid_article):
        """Debería detectar título vacío."""
        # Arrange
        valid_article.metadata.title.__str__ = Mock(return_value="   ")  # Solo espacios

        # Act
        violations = service.validate_content_invariants(valid_article)

        # Assert
        assert len(violations) == 1
        assert violations[0].field == "title"
        assert violations[0].error_code == "EMPTY_TITLE"

    def test_validate_content_invariants_with_title_too_long(
        self, service, valid_article
    ):
        """Debería detectar título demasiado largo."""
        # Arrange
        valid_article.metadata.title.__str__ = Mock(
            return_value="A" * 600
        )  # > 500 caracteres

        # Act
        violations = service.validate_content_invariants(valid_article)

        # Assert
        assert len(violations) == 1
        assert violations[0].field == "title"
        assert violations[0].error_code == "TITLE_TOO_LONG"

    def test_validate_content_invariants_with_empty_url(self, service, valid_article):
        """Debería detectar URL vacía."""
        # Arrange
        valid_article.identity_vo.url.__str__ = Mock(return_value="   ")

        # Act
        violations = service.validate_content_invariants(valid_article)

        # Assert
        assert len(violations) == 1
        assert violations[0].field == "url"
        assert violations[0].error_code == "EMPTY_URL"

    # ========== Tests de validate_all_invariants ==========

    def test_validate_all_invariants_with_valid_article(self, service, valid_article):
        """Debería retornar lista vacía para artículo completamente válido."""
        # Act
        violations = service.validate_all_invariants(valid_article)

        # Assert
        assert violations == []

    def test_validate_all_invariants_with_multiple_violations(
        self, service, valid_article
    ):
        """Debería detectar violaciones en múltiples categorías."""
        # Arrange
        valid_article.identity_vo.article_id = None  # Violación de identidad
        valid_article.quality.quality_score = 1.5  # Violación de score
        valid_article.created_at = datetime.now(timezone.utc)
        valid_article.updated_at = datetime.now(timezone.utc) - timedelta(
            hours=1
        )  # Violación de timestamp
        valid_article.content_vo.markdown = "Short"  # Violación de contenido

        # Act
        violations = service.validate_all_invariants(valid_article)

        # Assert
        assert len(violations) >= 4  # Al menos 4 violaciones
        assert any(v.field == "id" for v in violations)
        assert any(v.field == "quality_score" for v in violations)
        assert any(v.field == "timestamps" for v in violations)
        assert any(v.field == "content" for v in violations)

    def test_validate_all_invariants_returns_all_violations(
        self, service, valid_article
    ):
        """Debería retornar todas las violaciones, no solo la primera."""
        # Arrange
        # Modificar identity_vo con valores None
        valid_article.identity_vo.article_id = None
        valid_article.identity_vo.source_id = None

        # Modificar quality_vo con scores inválidos (mock permite esto)
        valid_article.quality.quality_score = 1.5  # Inválido > 1.0
        valid_article.quality.readability_score = Mock(value=-0.1)  # Inválido < 0

        # Act
        violations = service.validate_all_invariants(valid_article)

        # Assert
        assert len(violations) == 4  # 2 identidad + 2 scores


class TestRssArticleValidationServiceBackwardCompatibility:
    """Tests para verificar backward compatibility con código existente."""

    @pytest.fixture
    def service(self):
        """Crea instancia del servicio."""
        return ArticleValidationService()

    @pytest.fixture
    def rss_article(self):
        """Crea artículo para tests."""
        article = Mock(spec=Article)

        # Identity VO
        article.identity_vo = Mock()
        article.identity_vo.article_id = "article-123"
        article.identity_vo.source_id = "source-456"
        article.identity_vo.url = Mock()
        article.identity_vo.url.__str__ = Mock(
            return_value="https://example.com/article"
        )
        article.identity_vo.url.__bool__ = Mock(return_value=True)

        # Metadata VO
        article.metadata_vo = Mock()
        article.metadata.title = Mock()
        article.metadata.title.__str__ = Mock(return_value="Valid RssArticle Title")
        article.metadata.title.__bool__ = Mock(return_value=True)

        # Content VO
        article.content_vo = Mock()
        article.content_vo.markdown = "A" * 150
        article.content_vo.plaintext = None

        # Quality VO
        article.quality_vo = Mock()
        article.quality.quality_score = 0.8
        article.quality.readability_score = None
        article.quality.quality_level = "HIGH"

        # Validation info
        article.validation_info = Mock()
        article.validation_info.score = None

        # Timestamps
        article.created_at = datetime.now(timezone.utc)
        article.updated_at = datetime.now(timezone.utc)

        return article

    def test_validate_article_content_still_works(self, service, article):
        """Debería mantener compatibilidad con validate_article_content."""
        # Act
        result = service.validate_article_content(article)

        # Assert
        assert result is not None
        assert result.content_length_valid is True
        assert result.title_valid is True
        assert result.url_valid is True

    def test_has_sufficient_content_still_works(self, service, article):
        """Debería mantener compatibilidad con has_sufficient_content."""
        # Act
        result = service.has_sufficient_content(article)

        # Assert
        assert result is True

    def test_has_valid_title_still_works(self, service, article):
        """Debería mantener compatibilidad con has_valid_title."""
        # Act
        result = service.has_valid_title(article)

        # Assert
        assert result is True

    def test_has_valid_url_still_works(self, service, article):
        """Debería mantener compatibilidad con has_valid_url."""
        # Act
        result = service.has_valid_url(article)

        # Assert
        assert result is True

    def test_validate_multiple_articles_still_works(self, service, article):
        """Debería mantener compatibilidad con validate_multiple_articles."""
        # Arrange
        articles = [article, article]

        # Act
        results = service.validate_multiple_articles(articles)

        # Assert
        assert len(results) == 2
        assert all(r.content_length_valid for r in results)
