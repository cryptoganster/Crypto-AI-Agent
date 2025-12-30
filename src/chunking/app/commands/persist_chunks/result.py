"""Result object para PersistChunksCommand."""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class PersistChunksResult:
    """
    Result object para PersistChunksCommand.

    Attributes:
        success: Indica si la operación fue exitosa
        article_id: ID del artículo procesado
        chunks_persisted: Número de chunks persistidos exitosamente
        chunks_skipped: Número de chunks omitidos (inválidos)
        error_message: Mensaje de error si la operación falló
    """

    success: bool
    article_id: str
    chunks_persisted: int = 0
    chunks_skipped: int = 0
    error_message: Optional[str] = None

    @classmethod
    def success_result(
        cls,
        article_id: str,
        chunks_persisted: int,
        chunks_skipped: int = 0,
    ) -> "PersistChunksResult":
        """
        Crea un result exitoso.

        Args:
            article_id: ID del artículo
            chunks_persisted: Número de chunks persistidos
            chunks_skipped: Número de chunks omitidos

        Returns:
            PersistChunksResult exitoso
        """
        return cls(
            success=True,
            article_id=article_id,
            chunks_persisted=chunks_persisted,
            chunks_skipped=chunks_skipped,
        )

    @classmethod
    def failure(
        cls,
        article_id: str,
        error_message: str,
    ) -> "PersistChunksResult":
        """
        Crea un result fallido.

        Args:
            article_id: ID del artículo
            error_message: Mensaje de error

        Returns:
            PersistChunksResult fallido
        """
        return cls(
            success=False,
            article_id=article_id,
            error_message=error_message,
        )
