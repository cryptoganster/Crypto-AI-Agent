"""Process Managers para Article Bounded Context.

Process Managers coordinan flujos event-driven complejos siguiendo CQRS estricto (Escuela 2).

Pipelines:
- ContentExtractionInitiator: ScrapingCompleted → Inicia procesamiento de artículos
- ArticleContentExtractionPipeline: Scraping → Plaintext → Markdown
- ArticleContentAnalysisPipeline: Metrics → Language → Summary → Keywords → Quality
"""

from src.rss.article.app.process_managers.content_analysis_pipeline import (
    ArticleContentAnalysisPipeline,
)
from src.rss.article.app.process_managers.content_extraction_initiator import (
    ContentExtractionInitiator,
)
from src.rss.article.app.process_managers.content_extraction_pipeline import (
    ArticleContentExtractionPipeline,
)

__all__ = [
    "ContentExtractionInitiator",
    "ArticleContentExtractionPipeline",
    "ArticleContentAnalysisPipeline",
]
