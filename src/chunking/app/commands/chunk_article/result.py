"""Result object para ChunkArticleCommand."""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class ChunkArticleResult:
    """
    Result object para ChunkArticleCommand.

    Attributes:
        success: Indica si el comando fue exitoso
        article_id: ID del artículo procesado
        source_type: Tipo de fuente del artículo
        chunks_created: Número de chunks creados
        error_message: Mensaje de error si falló (opcional)

    Examples:
        >>> result = ChunkArticleResult.success(
        ...     article_id="article-123",
        ...     source_type="rss_article",
        ...     chunks_created=5,
        ... )
        >>> result.success
        True
        >>> result.chunks_created
        5
        >>> result.source_type
        'rss_article'
    """

    article_id: str
    source_type: str
    success: bool
    chunks_created: int = 0
    error_message: Optional[str] = None

    @classmethod
    def success(
        cls,
        article_id: str,
        source_type: str,
        chunks_created: int,
    ) -> "ChunkArticleResult":
        """
        Crea result exitoso.

        Args:
            article_id: ID del artículo procesado
            source_type: Tipo de fuente del artículo
            chunks_created: Número de chunks creados

        Returns:
            ChunkArticleResult exitoso
        """
        return cls(
            success=True,
            article_id=article_id,
            source_type=source_type,
            chunks_created=chunks_created,
            error_message=None,
        )

    @classmethod
    def failure(
        cls,
        article_id: str,
        source_type: str,
        error_message: str,
    ) -> "ChunkArticleResult":
        """
        Crea result fallido.

        Args:
            article_id: ID del artículo que falló
            source_type: Tipo de fuente del artículo
            error_message: Mensaje de error

        Returns:
            ChunkArticleResult fallido
        """
        return cls(
            success=False,
            article_id=article_id,
            source_type=source_type,
            chunks_created=0,
            error_message=error_message,
        )
