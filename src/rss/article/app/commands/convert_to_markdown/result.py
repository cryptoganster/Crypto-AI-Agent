"""Result para ConvertArticleToMarkdown command."""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class ConvertArticleToMarkdownResult:
    """
    Result para ConvertArticleToMarkdown command.

    Attributes:
        success: Si la conversión fue exitosa
        article_id: ID del artículo procesado
        markdown_length: Longitud del markdown generado (si exitoso)
        error_message: Mensaje de error (si falló)
    """

    success: bool
    article_id: str
    markdown_length: Optional[int] = None
    error_message: Optional[str] = None

    @classmethod
    def success_result(
        cls, article_id: str, markdown_length: int
    ) -> "ConvertArticleToMarkdownResult":
        """
        Crea resultado exitoso.

        Args:
            article_id: ID del artículo
            markdown_length: Longitud del markdown generado

        Returns:
            Result exitoso
        """
        return cls(success=True, article_id=article_id, markdown_length=markdown_length)

    @classmethod
    def failure(
        cls, article_id: str, error_message: str
    ) -> "ConvertArticleToMarkdownResult":
        """
        Crea resultado fallido.

        Args:
            article_id: ID del artículo
            error_message: Mensaje de error

        Returns:
            Result fallido
        """
        return cls(success=False, article_id=article_id, error_message=error_message)
