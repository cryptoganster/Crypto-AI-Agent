"""
Servicio de dominio para detección de idioma de artículos.

RESPONSABILIDAD ÚNICA: Detección de idioma.
Extraído desde ArticleKeywordService para seguir Single Responsibility Principle.

"""

from typing import Optional

from src.rss.article.domain.aggregates.rss_article import RssArticle as Article
from src.rss.article.domain.interfaces.external import (
    ILanguageDetector,
    LanguageDetectionResult,
)
from src.rss.article.domain.interfaces.services.language_detection import (
    IArticleLanguageDetectionService,
)
from src.rss.article.domain.value_objects.metadata import ArticleLanguage


class ArticleLanguageDetectionService(IArticleLanguageDetectionService):
    """
    Servicio de dominio para detección de idioma.

    ARQUITECTURA CLEAN + DDD:
    - Inyecta ILanguageDetector (Dependency Inversion Principle)
    - NO conoce implementaciones concretas (fastText, langdetect, etc.)
    - Domain Service puro con lógica de dominio
    - Facilita testing con mocks

    RESPONSABILIDAD ÚNICA: Detecta idioma del artículo
    - NO extrae keywords (ArticleKeywordService)
    - NO hace análisis de sentimiento (ArticleAnalysisService)
    - NO valida calidad (ArticleQualityService)
    """

    def __init__(self, language_detector: Optional[ILanguageDetector]):
        """
        Inicializa el servicio con un detector de idioma inyectado.

        Args:
            language_detector: Implementación de ILanguageDetector (FastTextAdapter, LangdetectAdapter, etc.)
        """
        self._language_detector = language_detector

    def detect_language(self, article: Article) -> ArticleLanguage:
        """
        Detecta el idioma del artículo usando detector externo.

        Args:
            article: Artículo a analizar (usa content_plaintext para mejor precisión NLP)

        Returns:
            ArticleLanguage con código de idioma y confianza detectada

        Raises:
            ValueError: Si el artículo no tiene contenido
        """
        # Usar content_vo.plaintext (texto puro sin HTML/Markdown para mejor detección NLP)
        # Fallback: content_vo.markdown → content_vo.markdown si plaintext no disponible
        text_to_analyze = (
            article.content.plaintext
            or article.content.markdown
            or article.content.markdown
        )

        if not text_to_analyze or len(text_to_analyze.strip()) < 10:
            # Default a español con confianza 0 si no hay contenido suficiente
            return ArticleLanguage.spanish(confidence=0.0)

        # Usar detector inyectado (puede ser fastText, langdetect, Lingua, etc.)
        # Truncar a primeros 1000 caracteres para eficiencia
        text_sample = text_to_analyze[:1000]

        try:
            # Verificar que el detector esté disponible
            if self._language_detector is None:
                # Fallback seguro a español si no hay detector
                return ArticleLanguage.spanish(confidence=0.0)

            # Delegar detección al adapter externo
            detection_result: LanguageDetectionResult = self._language_detector.detect(
                text_sample
            )

            # Convertir resultado externo a ArticleLanguage (Value Object de dominio)
            return ArticleLanguage(
                code=detection_result.language_code,
                confidence=detection_result.confidence,
            )

        except Exception:
            # Fallback seguro a español si falla detección
            return ArticleLanguage.spanish(confidence=0.0)
