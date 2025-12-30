"""Result para GenerateTLDRCommand."""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class GenerateTLDRResult:
    """
    Result para GenerateTLDRCommand.

    Attributes:
        success: Indica si el comando se ejecutó exitosamente
        article_id: ID del artículo procesado
        tldr: TLDR generado (si exitoso)
        bullet_count: Número de bullets en el TLDR
        chunks_used: Número de chunks usados para generar el TLDR
        error_message: Mensaje de error (si falló)
    """

    success: bool
    article_id: str
    tldr: Optional[str] = None
    bullet_count: Optional[int] = None
    chunks_used: Optional[int] = None
    error_message: Optional[str] = None

    @classmethod
    def success_result(
        cls,
        article_id: str,
        tldr: str,
        bullet_count: int,
        chunks_used: int,
    ) -> "GenerateTLDRResult":
        """Crea un result exitoso."""
        return cls(
            success=True,
            article_id=article_id,
            tldr=tldr,
            bullet_count=bullet_count,
            chunks_used=chunks_used,
        )

    @classmethod
    def failure(
        cls,
        article_id: str,
        error_message: str,
    ) -> "GenerateTLDRResult":
        """Crea un result de fallo."""
        return cls(
            success=False,
            article_id=article_id,
            error_message=error_message,
        )
