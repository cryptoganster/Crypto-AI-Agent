"""Event handlers livianos para Article bounded context.

Event Handlers siguiendo Escuela 2 (Process Manager):
- Livianos: Solo delegan a Process Managers
- NO coordinan: Process Managers coordinan
- NO emiten comandos directamente: Process Managers emiten

Event Handlers activos (solo 2):
- OnScrapingCompletedHandler: Cross-BC, delega a ContentExtractionInitiator
- OnArticleQualityCalculatedHandler: Fin del pipeline (solo log)

NOTA: Los eventos internos del pipeline (ArticleContentScraped,
ArticlePlaintextExtracted, ArticleMarkdownConverted, etc.) son manejados
DIRECTAMENTE por los Process Managers registrados en el Event Bus.
No necesitan Event Handlers intermedios.

Event Handlers deprecados (redundantes - Process Managers escuchan directamente):
- on_article_content_scraped.py.bak (redundante)
- on_article_plaintext_extracted.py.bak (redundante)
- on_article_markdown_converted.py.bak (coordinación en PM)
- on_article_metrics_calculated.py.bak (coordinación en PM)
- on_article_language_detected.py.bak (coordinación en PM)
- on_article_summary_generated.py.bak (coordinación en PM)
- on_article_keywords_extracted.py.bak (coordinación en PM)
"""

from .on_article_quality_calculated import OnArticleQualityCalculatedHandler
from .on_scraping_completed import OnScrapingCompletedHandler

__all__ = [
    "OnScrapingCompletedHandler",
    "OnArticleQualityCalculatedHandler",
]
