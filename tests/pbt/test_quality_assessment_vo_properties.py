"""Property-based tests para QualityAssessment Value Object."""

import pytest
from hypothesis import given
from hypothesis import strategies as st

from src.rss.article.domain.value_objects import (
    Level,
    LevelEnum,
)
from src.rss.article.domain.value_objects.quality_assessment import QualityAssessment
from src.rss.article.domain.value_objects.readability_score import ReadabilityScore


class TestQualityAssessmentProperties:
    """Property-based tests para QualityAssessment VO."""

    @given(
        quality_score=st.floats(min_value=0.0, max_value=1.0),
        readability_value=st.floats(min_value=0.0, max_value=1.0),
    )
    def test_quality_assessment_score_ranges_property(
        self, quality_score, readability_value
    ):
        """
        Property 5: QualityAssessment score ranges

        For any QualityAssessment instance created with quality_level or readability_score,
        those scores must be in the range [0.0, 1.0].

        **Feature: refactor-article-aggregate, Property 5: QualityAssessment score ranges**
        **Validates: Requirements 4.2**
        """
        # Crear quality_level desde score (esto valida el rango internamente)
        quality_level = Level.from_score(quality_score)

        # Crear readability_score (esto valida el rango internamente)
        readability_score = ReadabilityScore(value=readability_value)

        # Crear QualityAssessment
        assessment = QualityAssessment(
            quality_level=quality_level,
            readability_score=readability_score,
            content_hash="test_hash",
        )

        # Verificar que los scores están en rango válido
        assert assessment.quality_score is not None
        assert 0.0 <= assessment.quality_score <= 1.0

        assert assessment.readability_score is not None
        assert 0.0 <= assessment.readability_score.value <= 1.0

    @given(
        quality_score=st.floats(min_value=-10.0, max_value=-0.01).filter(
            lambda x: x < 0.0
        )
    )
    def test_quality_level_rejects_negative_scores(self, quality_score):
        """
        Property: Level rechaza scores negativos.

        For any negative score, Level.from_score debe lanzar ValueError.
        """
        with pytest.raises(ValueError) as exc_info:
            Level.from_score(quality_score)

        assert "entre 0.0 y 1.0" in str(exc_info.value)

    @given(
        quality_score=st.floats(min_value=1.01, max_value=10.0).filter(
            lambda x: x > 1.0
        )
    )
    def test_quality_level_rejects_scores_above_one(self, quality_score):
        """
        Property: Level rechaza scores mayores a 1.0.

        For any score > 1.0, Level.from_score debe lanzar ValueError.
        """
        with pytest.raises(ValueError) as exc_info:
            Level.from_score(quality_score)

        assert "entre 0.0 y 1.0" in str(exc_info.value)

    @given(
        readability_value=st.floats(min_value=-10.0, max_value=-0.01).filter(
            lambda x: x < 0.0
        )
    )
    def test_readability_score_rejects_negative_values(self, readability_value):
        """
        Property: ReadabilityScore rechaza valores negativos.

        For any negative value, ReadabilityScore debe lanzar ValueError.
        """
        with pytest.raises(ValueError) as exc_info:
            ReadabilityScore(value=readability_value)

        assert "entre" in str(exc_info.value).lower()

    @given(
        readability_value=st.floats(min_value=1.01, max_value=10.0).filter(
            lambda x: x > 1.0
        )
    )
    def test_readability_score_rejects_values_above_one(self, readability_value):
        """
        Property: ReadabilityScore rechaza valores mayores a 1.0.

        For any value > 1.0, ReadabilityScore debe lanzar ValueError.
        """
        with pytest.raises(ValueError) as exc_info:
            ReadabilityScore(value=readability_value)

        assert "entre" in str(exc_info.value).lower()

    @given(content_hash=st.text(min_size=0, max_size=0))
    def test_quality_assessment_rejects_empty_content_hash(self, content_hash):
        """
        Property: QualityAssessment rechaza content_hash vacío.

        For any empty string (after strip), QualityAssessment debe lanzar ValueError
        si content_hash no es None.
        """
        # content_hash vacío debe lanzar error
        with pytest.raises(ValueError) as exc_info:
            QualityAssessment(
                quality_level=Level.medium(),
                readability_score=ReadabilityScore(value=0.5),
                content_hash=content_hash,
            )

        assert "content_hash no puede estar vacío" in str(exc_info.value)

    @given(content_hash=st.text(min_size=1, max_size=100))
    def test_quality_assessment_accepts_non_empty_content_hash(self, content_hash):
        """
        Property: QualityAssessment acepta content_hash no vacío.

        For any non-empty string, QualityAssessment debe aceptar el content_hash.
        """
        # Filtrar strings que son solo whitespace
        if not content_hash.strip():
            with pytest.raises(ValueError):
                QualityAssessment(
                    quality_level=Level.medium(),
                    readability_score=ReadabilityScore(value=0.5),
                    content_hash=content_hash,
                )
        else:
            assessment = QualityAssessment(
                quality_level=Level.medium(),
                readability_score=ReadabilityScore(value=0.5),
                content_hash=content_hash,
            )

            assert assessment.content_hash == content_hash

    def test_empty_factory_creates_valid_instance(self):
        """
        Property: empty() factory method crea instancia válida.

        El factory method empty() debe crear una instancia válida
        con todos los campos None.
        """
        assessment = QualityAssessment.empty()

        assert assessment is not None
        assert assessment.quality_level is None
        assert assessment.readability_score is None
        assert assessment.content_hash is None
        assert assessment.quality_score is None
        assert assessment.has_quality_assessment is False
        assert assessment.has_complete_assessment is False

    @given(
        quality_enum=st.sampled_from(
            [
                LevelEnum.LOW,
                LevelEnum.MEDIUM,
                LevelEnum.HIGH,
                LevelEnum.PREMIUM,
            ]
        )
    )
    def test_quality_assessment_immutability_property(self, quality_enum):
        """
        Property: QualityAssessment es inmutable.

        For any QualityAssessment instance, intentar modificar sus campos
        debe lanzar un error.
        """
        quality_level = Level(quality_enum)
        assessment = QualityAssessment(
            quality_level=quality_level,
            readability_score=ReadabilityScore(value=0.5),
            content_hash="test_hash",
        )

        # Intentar modificar debe fallar (frozen dataclass)
        with pytest.raises(AttributeError):
            assessment.quality_level = Level.high()  # type: ignore

    @given(
        original_quality=st.sampled_from(
            [
                LevelEnum.LOW,
                LevelEnum.MEDIUM,
                LevelEnum.HIGH,
                LevelEnum.PREMIUM,
            ]
        ),
        new_quality=st.sampled_from(
            [
                LevelEnum.LOW,
                LevelEnum.MEDIUM,
                LevelEnum.HIGH,
                LevelEnum.PREMIUM,
            ]
        ),
    )
    def test_with_quality_level_returns_new_instance_property(
        self, original_quality, new_quality
    ):
        """
        Property: with_quality_level retorna nueva instancia sin modificar original.

        For any QualityAssessment instance, llamar with_quality_level debe retornar
        una nueva instancia con el quality_level actualizado, sin modificar la original.
        """
        original_level = Level(original_quality)
        original = QualityAssessment(
            quality_level=original_level,
            readability_score=ReadabilityScore(value=0.5),
            content_hash="original_hash",
        )

        new_level = Level(new_quality)
        updated = original.with_quality_level(new_level)

        # Verificar que son instancias diferentes
        assert original is not updated

        # Verificar que el original no cambió
        assert original.quality_level == original_level

        # Verificar que el nuevo tiene el valor actualizado
        assert updated.quality_level == new_level

        # Verificar que otros campos se preservaron
        assert updated.readability_score == original.readability_score
        assert updated.content_hash == original.content_hash

    @given(
        quality_score=st.floats(min_value=0.0, max_value=1.0),
        readability_value=st.floats(min_value=0.0, max_value=1.0),
        content_hash=st.one_of(st.none(), st.text(min_size=1, max_size=100)),
    )
    def test_has_quality_assessment_property_correctness(
        self, quality_score, readability_value, content_hash
    ):
        """
        Property: has_quality_assessment retorna True si al menos una evaluación está presente.

        For any QualityAssessment instance, has_quality_assessment debe retornar True
        si quality_level o readability_score no son None.
        """
        # Filtrar content_hash que son solo whitespace
        if content_hash is not None and not content_hash.strip():
            content_hash = None

        quality_level = Level.from_score(quality_score)
        readability_score = ReadabilityScore(value=readability_value)

        assessment = QualityAssessment(
            quality_level=quality_level,
            readability_score=readability_score,
            content_hash=content_hash,
        )

        # Siempre debe ser True porque ambos están presentes
        assert assessment.has_quality_assessment is True

    @given(
        quality_score=st.floats(min_value=0.0, max_value=1.0),
        readability_value=st.floats(min_value=0.0, max_value=1.0),
        content_hash=st.text(min_size=1, max_size=100),
    )
    def test_has_complete_assessment_property_correctness(
        self, quality_score, readability_value, content_hash
    ):
        """
        Property: has_complete_assessment retorna True si todas las evaluaciones están presentes.

        For any QualityAssessment instance, has_complete_assessment debe retornar True
        solo si quality_level, readability_score y content_hash no son None.
        """
        # Filtrar content_hash que son solo whitespace
        if not content_hash.strip():
            return  # Skip este caso

        quality_level = Level.from_score(quality_score)
        readability_score = ReadabilityScore(value=readability_value)

        assessment = QualityAssessment(
            quality_level=quality_level,
            readability_score=readability_score,
            content_hash=content_hash,
        )

        # Debe ser True porque todos los campos están presentes
        assert assessment.has_complete_assessment is True

    @given(quality_score=st.floats(min_value=0.0, max_value=1.0))
    def test_is_high_quality_property_correctness(self, quality_score):
        """
        Property: is_high_quality retorna True para HIGH y PREMIUM.

        For any QualityAssessment instance, is_high_quality debe retornar True
        si quality_level es HIGH o PREMIUM.
        """
        quality_level = Level.from_score(quality_score)
        assessment = QualityAssessment(quality_level=quality_level)

        expected = quality_level.is_high() or quality_level.is_very_high()
        assert assessment.is_high_quality == expected

    @given(quality_score=st.floats(min_value=0.0, max_value=1.0))
    def test_is_publishable_property_correctness(self, quality_score):
        """
        Property: is_publishable retorna True para calidad suficiente.

        For any QualityAssessment instance, is_publishable debe retornar True
        si quality_level indica que es publicable (MEDIUM, HIGH, PREMIUM).
        """
        quality_level = Level.from_score(quality_score)
        assessment = QualityAssessment(quality_level=quality_level)

        expected = quality_level.is_acceptable()
        assert assessment.is_publishable == expected

    def test_quality_assessment_accepts_none_content_hash(self):
        """
        Property: QualityAssessment acepta content_hash None.

        content_hash puede ser None sin lanzar error.
        """
        assessment = QualityAssessment(
            quality_level=Level.medium(),
            readability_score=ReadabilityScore(value=0.5),
            content_hash=None,
        )

        assert assessment.content_hash is None
        assert assessment.has_complete_assessment is False
