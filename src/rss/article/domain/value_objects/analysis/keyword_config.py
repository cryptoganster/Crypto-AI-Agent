"""Value Object para configuración de extracción de keywords."""

from dataclasses import dataclass


@dataclass(frozen=True)
class KeywordExtractionConfig:
    """
    Configuración inmutable para extracción de keywords.

    Value Object que encapsula parámetros de extracción de keywords
    con validaciones de dominio y factory methods para presets.

    Específico del bounded context de Article para análisis de contenido.
    """

    max_keywords: int = 10
    min_score: float = 0.3
    min_word_length: int = 4

    def __post_init__(self):
        if self.max_keywords < 1:
            raise ValueError(
                f"max_keywords debe ser >= 1, recibido: {self.max_keywords}"
            )

        if not 0.0 <= self.min_score <= 1.0:
            raise ValueError(
                f"min_score debe estar entre 0.0 y 1.0, recibido: {self.min_score}"
            )

        if self.min_word_length < 1:
            raise ValueError(
                f"min_word_length debe ser >= 1, recibido: {self.min_word_length}"
            )

    @classmethod
    def default(cls) -> "KeywordExtractionConfig":
        """Configuración por defecto balanceada."""
        return cls(max_keywords=10, min_score=0.3, min_word_length=4)

    @classmethod
    def permissive(cls) -> "KeywordExtractionConfig":
        """Configuración permisiva - muchos keywords, umbral bajo."""
        return cls(max_keywords=20, min_score=0.1, min_word_length=3)

    @classmethod
    def strict(cls) -> "KeywordExtractionConfig":
        """Configuración estricta - pocos keywords, umbral alto."""
        return cls(max_keywords=5, min_score=0.5, min_word_length=5)

    @classmethod
    def extensive(cls) -> "KeywordExtractionConfig":
        """Configuración extensiva para análisis detallado."""
        return cls(max_keywords=30, min_score=0.2, min_word_length=3)

    def is_permissive(self) -> bool:
        """Verifica si es configuración permisiva."""
        return self.max_keywords >= 15 and self.min_score <= 0.2

    def is_strict(self) -> bool:
        """Verifica si es configuración estricta."""
        return self.max_keywords <= 5 and self.min_score >= 0.5

    def allows_short_words(self) -> bool:
        """Verifica si permite palabras cortas (< 4 caracteres)."""
        return self.min_word_length < 4

    def __str__(self) -> str:
        return f"KeywordConfig(max={self.max_keywords}, min_score={self.min_score}, min_len={self.min_word_length})"

    def __repr__(self) -> str:
        return f"KeywordExtractionConfig(max_keywords={self.max_keywords}, min_score={self.min_score}, min_word_length={self.min_word_length})"
