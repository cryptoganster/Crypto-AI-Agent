"""Unit tests para ArticleQuality Value Object."""

import pytest

from src.rss.article.domain.value_objects.analysis import RssArticleQuality
from src.rss.article.domain.value_objects.readability_score import ReadabilityScore
from src.shared.domain.value_objects import Level


class TestRssArticleQuality:
    """Unit tests para ArticleQuality VO."""

    def test_empty_creates_valid_instance(self):
        """Debería crear instancia vacía válida."""
        assessment = RssArticleQuality.empty()

        assert assessment.quality_level is None
        assert assessment.readability_score is None
        assert assessment.content_hash is None
        assert assessment.quality_score is None
        assert not assessment.has_quality_assessment
        assert not assessment.has_complete_assessment

    def test_create_with_all_fields(self):
        """Debería crear instancia con todos los campos."""
        quality_level = Level.high()
        readability_score = ReadabilityScore(value=0.8)
        content_hash = "abc123"

        assessment = RssArticleQuality(
            quality_level=quality_level,
            readability_score=readability_score,
            content_hash=content_hash,
        )

        assert assessment.quality_level == quality_level
        assert assessment.readability_score == readability_score
        assert assessment.content_hash == content_hash
        assert assessment.quality_score == 0.75  # Level.high() = 0.75
        assert assessment.has_quality_assessment
        assert assessment.has_complete_assessment

    def test_rejects_empty_content_hash(self):
        """Debería rechazar content_hash vacío."""
        with pytest.raises(ValueError) as exc_info:
            RssArticleQuality(quality_level=Level.medium(), content_hash="")

        assert "content_hash no puede estar vacío" in str(exc_info.value)

    def test_rejects_whitespace_only_content_hash(self):
        """Debería rechazar content_hash con solo espacios."""
        with pytest.raises(ValueError) as exc_info:
            RssArticleQuality(quality_level=Level.medium(), content_hash="   ")

        assert "content_hash no puede estar vacío" in str(exc_info.value)

    def test_accepts_none_content_hash(self):
        """Debería aceptar content_hash None."""
        assessment = RssArticleQuality(quality_level=Level.medium(), content_hash=None)

        assert assessment.content_hash is None

    def test_quality_score_property(self):
        """Debería retornar score desde quality_level."""
        assessment = RssArticleQuality(quality_level=Level.very_high())

        assert assessment.quality_score == 0.95

    def test_quality_score_none_when_no_quality_level(self):
        """Debería retornar None cuando no hay quality_level."""
        assessment = RssArticleQuality.empty()

        assert assessment.quality_score is None

    def test_is_high_quality_true_for_high(self):
        """Debería retornar True para HIGH quality."""
        assessment = RssArticleQuality(quality_level=Level.high())

        assert assessment.is_high_quality

    def test_is_high_quality_true_for_premium(self):
        """Debería retornar True para PREMIUM quality."""
        assessment = RssArticleQuality(quality_level=Level.very_high())

        assert assessment.is_high_quality

    def test_is_high_quality_false_for_medium(self):
        """Debería retornar False para MEDIUM quality."""
        assessment = RssArticleQuality(quality_level=Level.medium())

        assert not assessment.is_high_quality

    def test_is_publishable_true_for_medium(self):
        """Debería retornar True para MEDIUM quality."""
        assessment = RssArticleQuality(quality_level=Level.medium())

        assert assessment.is_publishable

    def test_is_publishable_false_for_low(self):
        """Debería retornar False para LOW quality."""
        assessment = RssArticleQuality(quality_level=Level.low())

        assert not assessment.is_publishable

    def test_with_quality_level_returns_new_instance(self):
        """Debería retornar nueva instancia con quality_level actualizado."""
        original = RssArticleQuality(
            quality_level=Level.low(),
            readability_score=ReadabilityScore(value=0.5),
            content_hash="original",
        )

        updated = original.with_quality_level(Level.high())

        # Verificar que son instancias diferentes
        assert original is not updated

        # Verificar que el original no cambió
        assert original.quality_level.is_low()

        # Verificar que el nuevo tiene el valor actualizado
        assert updated.quality_level.is_high()

        # Verificar que otros campos se preservaron
        assert updated.readability_score == original.readability_score
        assert updated.content_hash == original.content_hash

    def test_with_readability_score_returns_new_instance(self):
        """Debería retornar nueva instancia con readability_score actualizado."""
        original = RssArticleQuality(
            quality_level=Level.medium(),
            readability_score=ReadabilityScore(value=0.5),
        )

        new_score = ReadabilityScore(value=0.9)
        updated = original.with_readability_score(new_score)

        # Verificar que son instancias diferentes
        assert original is not updated

        # Verificar que el original no cambió
        assert original.readability_score.value == 0.5

        # Verificar que el nuevo tiene el valor actualizado
        assert updated.readability_score.value == 0.9

    def test_with_content_hash_returns_new_instance(self):
        """Debería retornar nueva instancia con content_hash actualizado."""
        original = RssArticleQuality(
            quality_level=Level.medium(), content_hash="original_hash"
        )

        updated = original.with_content_hash("new_hash")

        # Verificar que son instancias diferentes
        assert original is not updated

        # Verificar que el original no cambió
        assert original.content_hash == "original_hash"

        # Verificar que el nuevo tiene el valor actualizado
        assert updated.content_hash == "new_hash"

    def test_immutability(self):
        """Debería ser inmutable (frozen dataclass)."""
        assessment = RssArticleQuality(quality_level=Level.medium())

        with pytest.raises(AttributeError):
            assessment.quality_level = Level.high()  # type: ignore

    def test_has_quality_assessment_true_with_quality_level(self):
        """Debería retornar True cuando tiene quality_level."""
        assessment = RssArticleQuality(quality_level=Level.medium())

        assert assessment.has_quality_assessment

    def test_has_quality_assessment_true_with_readability_score(self):
        """Debería retornar True cuando tiene readability_score."""
        assessment = RssArticleQuality(readability_score=ReadabilityScore(value=0.5))

        assert assessment.has_quality_assessment

    def test_has_quality_assessment_false_when_empty(self):
        """Debería retornar False cuando está vacío."""
        assessment = RssArticleQuality.empty()

        assert not assessment.has_quality_assessment

    def test_has_complete_assessment_true_with_all_fields(self):
        """Debería retornar True cuando tiene todos los campos."""
        assessment = RssArticleQuality(
            quality_level=Level.medium(),
            readability_score=ReadabilityScore(value=0.5),
            content_hash="hash",
        )

        assert assessment.has_complete_assessment

    def test_has_complete_assessment_false_without_content_hash(self):
        """Debería retornar False sin content_hash."""
        assessment = RssArticleQuality(
            quality_level=Level.medium(),
            readability_score=ReadabilityScore(value=0.5),
        )

        assert not assessment.has_complete_assessment
