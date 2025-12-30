"""Handler para ArticleAIProcessedEvent event."""

from src.chunking.domain.events import ArticleAIProcessedEvent
from src.clustering.app.commands.cluster_articles.command import ClusterArticlesCommand
from src.shared.kernel.bus import IMediator
from src.shared.kernel.logger import ILogger


class OnArticleAIProcessedHandler:
    """
    Handler para ArticleAIProcessedEvent event.

    Responsabilidad: Cuando un artículo completa el procesamiento AI,
    considerar re-clustering si es necesario.

    Flujo:
    - ArticleAIProcessedEvent → (evaluar si re-clustering) → ClusterArticlesCommand

    Nota: Por ahora, este handler NO emite ClusterArticlesCommand automáticamente
    porque el clustering es una operación costosa que debe ser ejecutada
    manualmente o en batch programado.

    En el futuro, podríamos:
    - Acumular artículos nuevos y re-clusterizar cada N artículos
    - Re-clusterizar en horarios de baja carga
    - Usar clustering incremental

    Requirements: 10.3.4
    """

    def __init__(
        self,
        command_bus: IMediator,
        logger: ILogger,
    ):
        """
        Inicializa el handler.

        Args:
            command_bus: Mediator para enviar comandos
            logger: Logger para registrar operaciones
        """
        self._command_bus = command_bus
        self._logger = logger.bind(
            layer="application",
            component="OnArticleAIProcessedHandler",
        )

    async def handle(self, event: ArticleAIProcessedEvent) -> None:
        """
        Maneja ArticleAIProcessedEvent event.

        Por ahora, solo loggea el evento. El clustering debe ser
        ejecutado manualmente o programado.

        Args:
            event: Evento ArticleAIProcessedEvent
        """
        self._logger.info(
            "ArticleAIProcessedEvent recibido",
            article_id=event.article_id,
            chunks_created=event.chunks_created,
            total_tokens=event.total_tokens,
            has_global_summary=event.has_global_summary,
            has_tldr=event.has_tldr,
            success=event.success,
            note="Clustering debe ejecutarse manualmente o en batch programado",
        )

        # TODO: Implementar lógica de re-clustering automático
        # Opciones:
        # 1. Acumular artículos y re-clusterizar cada N artículos
        # 2. Re-clusterizar en horarios programados
        # 3. Usar clustering incremental (agregar a clusters existentes)
        #
        # Por ahora, el clustering se ejecuta manualmente vía:
        # - API endpoint: POST /api/v1/clustering/cluster-articles
        # - CLI command: python -m src.clustering.cli cluster-articles
        # - Scheduled job: APScheduler job que ejecuta ClusterArticlesCommand
