"""Handler para RemoveSource command."""

from uuid import UUID

from src.rss.article.domain.interfaces.repositories import (
    IArticleReadRepository,
    IArticleWriteRepository,
)
from src.rss.feed.domain.aggregates import Source
from src.rss.feed.domain.interfaces.repositories import (
    ISourceReadRepository,
    ISourceWriteRepository,
)
from src.rss.feed.domain.interfaces.services import IRssContentCleanupService
from src.rss.feed.domain.value_objects.rss_feed_id import RssFeedId
from src.shared.kernel import IEventBus
from src.shared.kernel.logger import ILogger

from .command import RemoveSourceCommand
from .exception import (
    SourceNotFoundError,
    SourceRemovalBlockedError,
)
from .result import RemoveSourceResult
from .validator import RemoveSourceValidator


class RemoveRssFeedHandler:
    """Handler para RemoveSourceCommand usando Source aggregate."""

    def __init__(
        self,
        source_read_repo: ISourceReadRepository,
        source_write_repo: ISourceWriteRepository,
        article_read_repository: IArticleReadRepository,
        article_write_repository: IArticleWriteRepository,
        content_cleanup_service: IRssContentCleanupService,
        event_publisher: IEventBus,
        validator: RemoveSourceValidator,
        logger: ILogger,
    ):
        self._read_repo = source_read_repo
        self._write_repo = source_write_repo
        self._article_read_repo = article_read_repository
        self._article_write_repo = article_write_repository
        self._content_cleanup_service = content_cleanup_service
        self._event_publisher = event_publisher
        self._validator = validator
        self._logger = logger.bind(layer="application", component="RemoveSourceHandler")

    async def handle(self, command: RemoveSourceCommand) -> RemoveSourceResult:
        """
        Maneja comando de eliminación de fuente RSS.

        Args:
            command: Comando con información de eliminación

        Returns:
            RemoveSourceResult: Resultado de la operación
        """
        self._logger.info(
            "Iniciando eliminación de fuente RSS",
            source_id=command.source_id,
            correlation_id=command.correlation_id,
        )

        try:
            # 1. Validar comando
            validation_result = self._validator.validate(command)
            if not validation_result.is_valid:
                return RemoveSourceResult.failure_result(
                    source_id=command.source_id,
                    message=f"Validación fallida: {'; '.join(validation_result.errors)}",
                    error_code="VALIDATION_ERROR",
                )

            # 2. Convertir str → UUID para repository
            source_id_uuid = UUID(command.source_id)
            source_id = SourceId.from_string(command.source_id)

            # 3. Recuperar Source aggregate usando read repository
            source = await self._read_repo.find_by_id(source_id_uuid)
            if not source:
                return RemoveSourceResult.source_not_found(command.source_id)

            # 4. Verificar si hay artículos asociados usando ArticleReadRepository
            articles_count = await self._article_read_repo.count(source_id=source_id)
            removed_articles_count = 0

            if command.cleanup_articles:
                # Usar domain service para cleanup coordinado
                removed_article_ids = (
                    self._content_cleanup_service.cleanup_articles_by_source(source_id)
                )

                removed_articles_count = len(removed_article_ids)

                self._logger.info(
                    "Cleanup de artículos completado",
                    source_id=command.source_id,
                    articles_found=articles_count,
                    articles_removed=removed_articles_count,
                )
            else:
                # Verificar si hay artículos y no se permite force_removal
                if articles_count > 0 and not command.force_removal:
                    return RemoveSourceResult.removal_blocked_by_articles(
                        command.source_id, articles_count
                    )

            # 5. Archivar fuente antes de eliminar si se requiere
            if command.archive_before_removal and source.is_active:
                source.deactivate()
                self._logger.info(
                    "Fuente archivada antes de eliminación",
                    source_id=command.source_id,
                )

            # 6. Eliminar la fuente directamente del write repository
            await self._write_repo.delete(source_id_uuid)

            # 7. Publicar eventos de dominio del source
            await self._publish_domain_events(source)

            # 8. Log éxito
            self._logger.info(
                "Fuente RSS eliminada exitosamente",
                source_id=command.source_id,
                articles_removed=removed_articles_count,
                correlation_id=command.correlation_id,
            )

            # 10. Construir resultado exitoso
            return RemoveSourceResult.success_result(
                source_id=command.source_id,
                source_name=str(source.name),
                source_url=str(source.url),
                articles_removed=removed_articles_count,
                was_archived=command.archive_before_removal,
            )

        except SourceRemovalBlockedError as e:
            self._logger.warning("Eliminación de fuente bloqueada", error=str(e))
            return RemoveSourceResult.failure_result(
                source_id=command.source_id,
                message=str(e),
                error_code="REMOVAL_BLOCKED",
            )
        except Exception as e:
            self._logger.exception(
                "Error inesperado al eliminar fuente RSS",
                error=str(e),
            )
            return RemoveSourceResult.failure_result(
                source_id=command.source_id,
                message=f"Error interno: {str(e)}",
                error_code="INTERNAL_ERROR",
            )

    async def _publish_domain_events(self, source: Source) -> int:
        """Publica eventos de dominio generados por el agregado Source."""
        events = source.domain_events
        events_count = len(events)

        for event in events:
            await self._event_publisher.publish(event)
            self._logger.debug(
                "Evento Source publicado",
                event_type=type(event).__name__,
                source_id=str(source.id),
            )

        # Limpiar eventos procesados
        source.mark_events_as_committed()

        return events_count
