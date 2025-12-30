"""Value Object para evaluación de calidad del artículo."""

from dataclasses import dataclass
from typing import Optional

from src.rss.article.domain.value_objects.readability_score import ReadabilityScore
from src.shared.domain.value_objects import Level


@dataclass(frozen=True)
class RssArticleQuality:
    """
    Value Object para evaluación de calidad del contenido de un artículo.

    Encapsula la evaluación completa de calidad de un artículo, incluyendo
    nivel de calidad, legibilidad y hash del contenido.

    Invariantes:
    - quality_level.score debe estar en [0.0, 1.0] (validado por Level VO)
    - readability_score.value debe estar en [0.0, 1.0] (validado por ReadabilityScore VO)
    - content_hash no puede estar vacío si está presente
    - Los campos son inmutables (frozen dataclass)

    Attributes:
        quality_level: Nivel de calidad del artículo (LOW, MEDIUM, HIGH, PREMIUM)
        readability_score: Score de legibilidad del contenido
        content_hash: Hash del contenido para detección de cambios
    """

    quality_level: Optional[Level] = None
    readability_score: Optional[ReadabilityScore] = None
    content_hash: Optional[str] = None

    def __post_init__(self):
        """
        Valida que content_hash no esté vacío si está presente.

        Raises:
            ValueError: Si content_hash está presente pero es una cadena vacía
        """
        if self.content_hash is not None and not self.content_hash.strip():
            raise ValueError(
                "content_hash no puede estar vacío. "
                "Debe ser None o una cadena no vacía."
            )

    @staticmethod
    def empty() -> "RssArticleQuality":
        """
        Crea una instancia vacía sin evaluación de calidad.

        Útil para inicialización de agregados sin calidad evaluada aún.

        Returns:
            RssArticleQuality con todos los campos None

        Example:
            >>> assessment = RssArticleQuality.empty()
            >>> assessment.quality_level is None
            True
            >>> assessment.readability_score is None
            True
            >>> assessment.content_hash is None
            True
        """
        return RssArticleQuality()

    @property
    def quality_score(self) -> Optional[float]:
        """
        Retorna score normalizado desde quality_level si existe.

        Convierte el nivel de calidad a un score numérico entre 0.0 y 1.0
        para facilitar comparaciones y cálculos.

        Returns:
            Score entre 0.0 y 1.0 si quality_level existe, None en caso contrario

        Example:
            >>> assessment = ArticleQuality(quality_level=Level.high())
            >>> assessment.quality_score
            0.8
        """
        return self.quality_level.score if self.quality_level else None

    @property
    def has_quality_assessment(self) -> bool:
        """
        Verifica si tiene al menos una evaluación de calidad.

        Returns:
            True si quality_level o readability_score no son None
        """
        return self.quality_level is not None or self.readability_score is not None

    @property
    def has_complete_assessment(self) -> bool:
        """
        Verifica si tiene evaluación completa de calidad.

        Returns:
            True si quality_level, readability_score y content_hash no son None
        """
        return (
            self.quality_level is not None
            and self.readability_score is not None
            and self.content_hash is not None
        )

    @property
    def is_high_quality(self) -> bool:
        """
        Verifica si el artículo es de alta calidad.

        Returns:
            True si quality_level es HIGH o PREMIUM, False en caso contrario
        """
        if self.quality_level is None:
            return False
        return self.quality_level.is_high() or self.quality_level.is_very_high()

    @property
    def is_publishable(self) -> bool:
        """
        Verifica si el artículo tiene calidad suficiente para publicar.

        Returns:
            True si quality_level indica que es publicable, False en caso contrario
        """
        if self.quality_level is None:
            return False
        return self.quality_level.is_acceptable()

    def with_quality_level(self, quality_level: Level) -> "RssArticleQuality":
        """
        Retorna nueva instancia con quality_level actualizado.

        Método inmutable que crea una nueva instancia preservando otros campos.

        Args:
            quality_level: Nuevo Level

        Returns:
            Nueva instancia de RssArticleQuality con quality_level actualizado

        Example:
            >>> assessment = RssArticleQuality.empty()
            >>> updated = assessment.with_quality_level(Level.high())
            >>> updated.quality_level.is_high()
            True
            >>> assessment.quality_level is None  # Original sin cambios
            True
        """
        return RssArticleQuality(
            quality_level=quality_level,
            readability_score=self.readability_score,
            content_hash=self.content_hash,
        )

    def with_readability_score(
        self, readability_score: ReadabilityScore
    ) -> "RssArticleQuality":
        """
        Retorna nueva instancia con readability_score actualizado.

        Args:
            readability_score: Nuevo ReadabilityScore

        Returns:
            Nueva instancia de RssArticleQuality con readability_score actualizado
        """
        return RssArticleQuality(
            quality_level=self.quality_level,
            readability_score=readability_score,
            content_hash=self.content_hash,
        )

    def with_content_hash(self, content_hash: str) -> "RssArticleQuality":
        """
        Retorna nueva instancia con content_hash actualizado.

        Args:
            content_hash: Nuevo hash del contenido

        Returns:
            Nueva instancia de RssArticleQuality con content_hash actualizado

        Raises:
            ValueError: Si content_hash es una cadena vacía
        """
        return RssArticleQuality(
            quality_level=self.quality_level,
            readability_score=self.readability_score,
            content_hash=content_hash,
        )


# Alias para compatibilidad
ArticleQuality = RssArticleQuality
