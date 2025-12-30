"""Event handler para ArticleEmbeddingGenerated (cross-BC)."""

from src.chunking.domain.events import ArticleEmbeddingGenerated
from src.rss.article.app.commands.detect_duplicate import (
    DetectDuplicateArticleCommand,
)
from src.shared.kernel import IMediator
from src.shared.kernel.logger import ILogger


class OnArticleEmbeddingGeneratedHandler:
    """
    Handler para ArticleEmbeddingGenerated event (cross-BC).

    Responsabilidad: Cuando Embedding BC genera un embedding,
    emitir DetectDuplicateArticleCommand para verificar duplicados.

    Flujo:
    - ArticleEmbeddingGenerated (Embedding BC)
    - → OnArticleEmbeddingGeneratedHandler (Article BC)
    - → DetectDuplicateArticleCommand
    - → DetectDuplicateArticleHandler

    ARQUITECTURA: Event-Driven, Cross-BC Integration
    """

    def __init__(
        self,
        command_bus: IMediator,
        logger: ILogger,
    ):
        """
        Inicializa handler.

        Args:
            command_bus: Mediator para emitir comandos
            logger: Logger para tracking
        """
        self._command_bus = command_bus
        self._logger = logger.bind(
            layer="application",
            handler="OnArticleEmbeddingGeneratedHandler",
        )

    async def handle(self, event: ArticleEmbeddingGenerated) -> None:
        """
        Maneja ArticleEmbeddingGenerated event.

        Cuando se generan embeddings para un artículo → Emite DetectDuplicateArticleCommand

        Args:
            event: Evento ArticleEmbeddingGenerated
        """
        self._logger.info(
            "Embeddings generados, iniciando detección de duplicados",
            article_id=event.article_id,
            num_chunks=event.num_chunks,
            model=event.model,
            dimension=event.dimension,
        )

        # Emitir comando para detectar duplicados
        command = DetectDuplicateArticleCommand(
            article_id=event.article_id,
            max_results=10,
        )

        try:
            await self._command_bus.send(command)

            self._logger.info(
                "DetectDuplicateArticleCommand emitido",
                article_id=event.article_id,
            )
        except Exception as e:
            self._logger.error(
                "Error emitiendo DetectDuplicateArticleCommand",
                article_id=event.article_id,
                error=str(e),
            )
