"""Result para GenerateChunkEmbeddingsCommand."""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class GenerateChunkEmbeddingsResult:
    """
    Result object para GenerateChunkEmbeddingsCommand.

    Attributes:
        success: Indica si la generación de embeddings fue exitosa
        article_id: ID del artículo procesado
        chunks_processed: Número de chunks que recibieron embeddings
        error_message: Mensaje de error si success=False
    """

    success: bool
    article_id: str
    chunks_processed: int = 0
    error_message: Optional[str] = None

    @classmethod
    def success_result(
        cls,
        article_id: str,
        chunks_processed: int,
    ) -> "GenerateChunkEmbeddingsResult":
        """
        Crea un result exitoso.

        Args:
            article_id: ID del artículo procesado
            chunks_processed: Número de chunks procesados

        Returns:
            GenerateChunkEmbeddingsResult con success=True
        """
        return cls(
            success=True,
            article_id=article_id,
            chunks_processed=chunks_processed,
        )

    @classmethod
    def failure(
        cls,
        article_id: str,
        error_message: str,
    ) -> "GenerateChunkEmbeddingsResult":
        """
        Crea un result fallido.

        Args:
            article_id: ID del artículo que falló
            error_message: Descripción del error

        Returns:
            GenerateChunkEmbeddingsResult con success=False
        """
        return cls(
            success=False,
            article_id=article_id,
            error_message=error_message,
        )
