"""Result para GenerateChunkSummariesCommand."""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class GenerateChunkSummariesResult:
    """
    Result de generar summaries de chunks.

    Attributes:
        success: Si la operación fue exitosa
        article_id: ID del artículo procesado
        chunks_summarized: Número de chunks que se summarizaron exitosamente
        total_chunks: Número total de chunks procesados
        error_message: Mensaje de error si falló (opcional)
    """

    success: bool
    article_id: str
    chunks_summarized: int
    total_chunks: int
    error_message: Optional[str] = None

    @classmethod
    def success_result(
        cls,
        article_id: str,
        chunks_summarized: int,
        total_chunks: int,
    ) -> "GenerateChunkSummariesResult":
        """
        Crea result exitoso.

        Args:
            article_id: ID del artículo
            chunks_summarized: Número de chunks summarizados
            total_chunks: Número total de chunks

        Returns:
            Result exitoso
        """
        return cls(
            success=True,
            article_id=article_id,
            chunks_summarized=chunks_summarized,
            total_chunks=total_chunks,
        )

    @classmethod
    def failure(
        cls,
        article_id: str,
        error_message: str,
        chunks_summarized: int = 0,
        total_chunks: int = 0,
    ) -> "GenerateChunkSummariesResult":
        """
        Crea result fallido.

        Args:
            article_id: ID del artículo
            error_message: Mensaje de error
            chunks_summarized: Número de chunks summarizados antes del error
            total_chunks: Número total de chunks

        Returns:
            Result fallido
        """
        return cls(
            success=False,
            article_id=article_id,
            chunks_summarized=chunks_summarized,
            total_chunks=total_chunks,
            error_message=error_message,
        )
