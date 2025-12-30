"""Repository interface para ArticleProcessingStatus read model."""

from typing import Optional, Protocol

from src.chunking.app.read_models.article_processing_status import (
    ArticleProcessingStatus,
)


class IProcessingStatusRepository(Protocol):
    """
    Repository interface para leer estado de procesamiento.

    Este repository maneja el read model ArticleProcessingStatus,
    que es actualizado por event handlers y consultado por queries.

    Responsabilidades:
    - Buscar estado de procesamiento por article_id
    - Verificar si un artículo ha sido procesado
    """

    async def find_by_article_id(
        self,
        article_id: str,
    ) -> Optional[ArticleProcessingStatus]:
        """
        Busca estado de procesamiento por article_id.

        Args:
            article_id: ID del artículo

        Returns:
            ArticleProcessingStatus si existe, None si no
        """
        ...

    async def exists(self, article_id: str) -> bool:
        """
        Verifica si existe estado de procesamiento para un artículo.

        Args:
            article_id: ID del artículo

        Returns:
            True si existe, False si no
        """
        ...
