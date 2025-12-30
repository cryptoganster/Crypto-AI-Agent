"""Command para dividir artículo en chunks."""

from dataclasses import dataclass
from typing import List, Optional


@dataclass(frozen=True)
class ChunkArticleCommand:
    """
    Command para dividir artículo en chunks.

    Este comando toma el texto de un artículo y lo divide en chunks
    de tamaño configurable con overlap. Cada chunk se persiste como
    un KnowledgeChunk aggregate independiente.

    Attributes:
        article_id: ID del artículo a procesar
        text: Texto completo del artículo
        source_url: URL del artículo original
        source_type: Tipo de fuente (rss_article, web_scrape, etc.)
        published_at: Fecha de publicación (ISO format, opcional)
        topics: Lista de topics/categorías del artículo (opcional)
        correlation_id: ID para tracking (opcional)

    Examples:
        >>> command = ChunkArticleCommand(
        ...     article_id="article-123",
        ...     text="Bitcoin alcanzó $50,000...",
        ...     source_url="https://example.com/article",
        ...     source_type="rss_article",
        ...     published_at="2024-01-15T10:30:00Z",
        ...     topics=["crypto", "bitcoin"],
        ... )
    """

    article_id: str
    text: str
    source_url: str
    source_type: str = (
        "rss_article"  # Default to rss_article for backward compatibility
    )
    published_at: Optional[str] = None
    topics: Optional[List[str]] = None
    correlation_id: Optional[str] = None
