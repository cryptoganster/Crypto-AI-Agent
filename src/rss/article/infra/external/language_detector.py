"""Language detector usando FastText - Article Bounded Context."""

from typing import Dict, Optional

from src.rss.article.domain.interfaces.external import (
    ILanguageDetector,
    LanguageDetectionResult,
)
from src.shared.kernel.logger import ILogger


class LanguageDetector(ILanguageDetector):
    """
    Detector de idioma usando fast-langdetect (Facebook's fastText).

    CARACTERÍSTICAS:
    - 176 idiomas soportados
    - 95% de precisión
    - 80x más rápido que langdetect
    """

    def __init__(
        self,
        model: str = "lite",
        reliability_threshold: float = 0.7,
        logger: Optional[ILogger] = None,
    ):
        """
        Inicializa el detector fastText.

        Args:
            model: 'lite' (offline, 1MB) o 'full' (126MB, más preciso)
            reliability_threshold: Umbral para considerar detección confiable
            logger: Logger opcional
        """
        self._model = model
        self._reliability_threshold = reliability_threshold
        self._logger = logger
        self._detector = None

    def _initialize_detector(self) -> None:
        """Lazy loading del detector fastText."""
        if self._detector is not None:
            return

        try:
            from fast_langdetect import LangDetectConfig, LangDetector

            config = LangDetectConfig(model=self._model)
            self._detector = LangDetector(config)

            if self._logger:
                self._logger.debug(
                    "FastText detector inicializado",
                    model=self._model,
                    reliability_threshold=self._reliability_threshold,
                )
        except ImportError as e:
            error_msg = (
                "fast-langdetect no está instalado. "
                "Instala con: pip install fast-langdetect"
            )
            if self._logger:
                self._logger.error(error_msg, error=str(e))
            raise ImportError(error_msg) from e

    def detect(self, text: str) -> LanguageDetectionResult:
        """Detecta el idioma principal del texto."""
        if not text or not text.strip():
            raise ValueError("Text no puede estar vacío")

        self._initialize_detector()
        text_sample = text[:1000].strip()

        try:
            results = self._detector.detect(text_sample, k=1)

            if not results:
                return LanguageDetectionResult.default_spanish()

            top_result = results[0]
            return LanguageDetectionResult.create(
                language_code=top_result["lang"],
                confidence=top_result["score"],
                reliability_threshold=self._reliability_threshold,
            )

        except Exception:
            return LanguageDetectionResult.default_spanish()

    def detect_with_probabilities(self, text: str, top_k: int = 3) -> Dict[str, float]:
        """Detecta idiomas con probabilidades para los top K."""
        if not text or not text.strip():
            return {"es": 1.0}

        self._initialize_detector()
        text_sample = text[:1000].strip()

        try:
            results = self._detector.detect(text_sample, k=top_k)
            if not results:
                return {"es": 1.0}
            return {result["lang"]: result["score"] for result in results}
        except Exception:
            return {"es": 1.0}
