"""Result para GenerateGlobalSummaryCommand."""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class GenerateGlobalSummaryResult:
    """
    Result para GenerateGlobalSummaryCommand.

    Attributes:
        success: Indica si el comando se ejecutó exitosamente
        article_id: ID del artículo procesado
        global_summary: Summary global generado (si exitoso)
        summary_length: Longitud del summary generado en caracteres
        chunks_used: Número de chunks usados para generar el summary
        error_message: Mensaje de error (si falló)
    """

    success: bool
    article_id: str
    global_summary: Optional[str] = None
    summary_length: Optional[int] = None
    chunks_used: Optional[int] = None
    error_message: Optional[str] = None

    @classmethod
    def success_result(
        cls,
        article_id: str,
        global_summary: str,
        chunks_used: int,
    ) -> "GenerateGlobalSummaryResult":
        """Crea un result exitoso."""
        return cls(
            success=True,
            article_id=article_id,
            global_summary=global_summary,
            summary_length=len(global_summary),
            chunks_used=chunks_used,
        )

    @classmethod
    def failure(
        cls,
        article_id: str,
        error_message: str,
    ) -> "GenerateGlobalSummaryResult":
        """Crea un result de fallo."""
        return cls(
            success=False,
            article_id=article_id,
            error_message=error_message,
        )
