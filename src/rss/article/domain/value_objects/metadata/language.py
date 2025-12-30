"""Value Object para idioma del artículo."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ArticleLanguage:
    """
    Idioma del artículo.

    Value Object inmutable que representa el idioma detectado del contenido.
    Usa códigos ISO 639-1 de 2 letras (es, en, fr, etc.)
    """

    code: str  # "es", "en", "fr", etc.
    confidence: float = 1.0  # 0.0-1.0

    def __post_init__(self):
        """Validación post-inicialización."""
        if not self.code or len(self.code) != 2:
            raise ValueError(
                f"code debe ser código ISO 639-1 de 2 letras, recibido: {self.code}"
            )

        # Validar que sea código ISO 639-1 válido (2 letras minúsculas)
        if not self.code.isalpha():
            raise ValueError(
                f"code debe contener solo letras (ISO 639-1), recibido: {self.code}"
            )

        if not self.code.islower():
            raise ValueError(
                f"code debe estar en minúsculas (ISO 639-1), recibido: {self.code}"
            )

        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(
                f"confidence debe estar entre 0.0 y 1.0, recibido: {self.confidence}"
            )

    @classmethod
    def spanish(cls, confidence: float = 1.0) -> "ArticleLanguage":
        """Factory method para español."""
        return cls(code="es", confidence=confidence)

    @classmethod
    def english(cls, confidence: float = 1.0) -> "ArticleLanguage":
        """Factory method para inglés."""
        return cls(code="en", confidence=confidence)

    @classmethod
    def french(cls, confidence: float = 1.0) -> "ArticleLanguage":
        """Factory method para francés."""
        return cls(code="fr", confidence=confidence)

    def is_spanish(self) -> bool:
        """Verifica si es español."""
        return self.code == "es"

    def is_english(self) -> bool:
        """Verifica si es inglés."""
        return self.code == "en"

    def is_french(self) -> bool:
        """Verifica si es francés."""
        return self.code == "fr"

    def is_high_confidence(self) -> bool:
        """Confianza > 0.7 es alta."""
        return self.confidence > 0.7

    def is_low_confidence(self) -> bool:
        """Confianza < 0.3 es baja."""
        return self.confidence < 0.3

    def __str__(self) -> str:
        if self.confidence < 1.0:
            return f"{self.code.upper()} ({self.confidence:.1%})"
        return self.code.upper()

    def __repr__(self) -> str:
        return f"ArticleLanguage(code='{self.code}', confidence={self.confidence:.2f})"
