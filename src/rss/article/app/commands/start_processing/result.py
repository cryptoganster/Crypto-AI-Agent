"""Result Object para StartArticleProcessingCommand."""

from dataclasses import dataclass
from typing import List, Optional


@dataclass(frozen=True)
class StartArticleProcessingResult:
    """
    Resultado de iniciar el pipeline de procesamiento.

    Attributes:
        success: Si el comando se ejecutó exitosamente
        pipeline_id: ID del pipeline iniciado
        article_ids: IDs de artículos que serán procesados
        error: Mensaje de error si falló
    """

    success: bool
    pipeline_id: Optional[str] = None
    article_ids: Optional[List[str]] = None
    error: Optional[str] = None

    @classmethod
    def success_result(
        cls,
        pipeline_id: str,
        article_ids: List[str],
    ) -> "StartArticleProcessingResult":
        """Crea resultado exitoso."""
        return cls(
            success=True,
            pipeline_id=pipeline_id,
            article_ids=article_ids,
        )

    @classmethod
    def failure(cls, error: str) -> "StartArticleProcessingResult":
        """Crea resultado fallido."""
        return cls(success=False, error=error)
