"""Interface para detectores de idioma externos - Article Bounded Context."""

from dataclasses import dataclass
from typing import Dict, Protocol


@dataclass(frozen=True)
class LanguageDetectionResult:
    """
    Resultado de detección de idioma.

    Value Object inmutable que encapsula el resultado de detección.
    """

    language_code: str  # ISO 639-1 code (e.g., "en", "es", "fr")
    confidence: float  # 0.0-1.0
    is_reliable: bool  # True si confidence > threshold

    @classmethod
    def create(
        cls,
        language_code: str,
        confidence: float,
        reliability_threshold: float = 0.8,
    ) -> "LanguageDetectionResult":
        """
        Factory method con validación.

        Args:
            language_code: Código ISO 639-1
            confidence: Confianza 0.0-1.0
            reliability_threshold: Umbral para considerar confiable

        Returns:
            LanguageDetectionResult validado
        """
        normalized_code = language_code.lower().strip()
        clamped_confidence = max(0.0, min(1.0, confidence))

        return cls(
            language_code=normalized_code,
            confidence=clamped_confidence,
            is_reliable=clamped_confidence >= reliability_threshold,
        )

    @classmethod
    def default_spanish(cls) -> "LanguageDetectionResult":
        """Resultado por defecto cuando la detección falla."""
        return cls(
            language_code="es",
            confidence=0.0,
            is_reliable=False,
        )


class ILanguageDetector(Protocol):
    """
    Interface para detectores de idioma externos.

    DEPENDENCY INVERSION PRINCIPLE:
    - Domain layer define la interface
    - Infrastructure layer implementa el adapter concreto

    Implementaciones concretas:
    - FastTextAdapter (fast-langdetect - 176 idiomas, 95% precisión)
    """

    def detect(self, text: str) -> LanguageDetectionResult:
        """
        Detecta el idioma principal del texto.

        Args:
            text: Texto a analizar (UTF-8)

        Returns:
            LanguageDetectionResult con idioma detectado
        """
        ...

    def detect_with_probabilities(self, text: str, top_k: int = 3) -> Dict[str, float]:
        """
        Detecta idiomas con probabilidades para los top K.

        Args:
            text: Texto a analizar
            top_k: Número de idiomas principales a retornar

        Returns:
            Dict con {language_code: probability} ordenado por probabilidad
        """
        ...
