"""Handler para ArticleQualityCalculated event."""

from src.rss.article.domain.events import ArticleQualityCalculated
from src.shared.kernel.logger import ILogger


class OnArticleQualityCalculatedHandler:
    """
    Handler para ArticleQualityCalculated.

    Responsabilidad: Cuando calidad es calculada, el artículo está completamente procesado.

    Este es el último paso del flujo completo (extracción + análisis).
    No emite más comandos, solo log de éxito.
    """

    def __init__(self, logger: ILogger):
        self._logger = logger.bind(
            layer="application",
            component="OnArticleQualityCalculatedHandler",
        )

    async def handle(self, event: ArticleQualityCalculated) -> None:
        """
        Maneja ArticleQualityCalculated.

        Último paso: Log de éxito completo.

        Args:
            event: Evento ArticleQualityCalculated
        """
        if event.success:
            self._logger.success(
                "🎉 Artículo completamente procesado (extracción + análisis)",
                article_id=event.article_id,
                quality_score=(
                    event.quality_score if hasattr(event, "quality_score") else None
                ),
            )
        else:
            self._logger.warning(
                "Cálculo de calidad falló",
                article_id=event.article_id,
                error=event.error_message if hasattr(event, "error_message") else None,
            )
