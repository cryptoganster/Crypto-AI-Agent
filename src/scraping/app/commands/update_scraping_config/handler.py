"""Handler para UpdateScrapingConfigCommand."""

from uuid import UUID

from src.rss.feed.domain.value_objects.configuration import SourceConfiguration
from src.scraping.app.commands.update_scraping_config.command import (
    UpdateScrapingConfigCommand,
)
from src.scraping.app.commands.update_scraping_config.exception import (
    InvalidScrapingConfigError,
    ScrapingNotFoundError,
)
from src.scraping.app.commands.update_scraping_config.result import (
    UpdateScrapingConfigResult,
)
from src.scraping.app.commands.update_scraping_config.validator import (
    UpdateScrapingConfigValidator,
)
from src.scraping.domain.aggregates import Scraping
from src.scraping.domain.interfaces.repositories import (
    IScrapingReadRepository,
    IScrapingWriteRepository,
)
from src.scraping.domain.interfaces.services.error_tracking import (
    IErrorTrackingService,
)
from src.shared.kernel import IEventBus
from src.shared.kernel.logger import ILogger


class UpdateScrapingConfigHandler:
    """
    Handler para actualización de configuración de scraping.

    Responsabilidades:
    - Validar comando
    - Obtener sesión de scraping asociada a la fuente
    - Actualizar configuración
    - Persistir cambios
    - Publicar eventos de dominio
    """

    def __init__(
        self,
        scraping_read_repository: IScrapingReadRepository,
        scraping_write_repository: IScrapingWriteRepository,
        validator: UpdateScrapingConfigValidator,
        logger: ILogger,
        error_tracking_service: IErrorTrackingService,
        event_publisher: IEventBus,
    ):
        self._scraping_read_repo = scraping_read_repository
        self._scraping_write_repo = scraping_write_repository
        self._validator = validator
        self._logger = logger.bind(
            layer="application",
            component="UpdateScrapingConfigHandler",
        )
        self._error_tracking_service = error_tracking_service
        self._event_publisher = event_publisher

    async def handle(
        self, command: UpdateScrapingConfigCommand
    ) -> UpdateScrapingConfigResult:
        """
        Ejecuta el comando de actualización de configuración.

        Args:
            command: Comando con nueva configuración

        Returns:
            UpdateScrapingConfigResult: Resultado de la operación
        """
        self._logger.info(
            "Iniciando actualización de configuración de scraping",
            source_id=command.source_id,
            correlation_id=command.correlation_id,
            updated_by=command.updated_by,
        )

        try:
            # 1. Validar comando
            if command.validate_config:
                self._validator.validate(command)

            # 2. Convertir str → UUID para repository
            source_id_uuid = UUID(command.source_id)

            # 3. Obtener sesión de scraping por source_id usando read repository
            scrapings = await self._scraping_read_repo.find_by_source(
                source_id_uuid, limit=1
            )

            if not scrapings:
                raise ScrapingNotFoundError(command.source_id)

            scraping = scrapings[0]

            # 4. Capturar configuración anterior
            stats = scraping.get_fetch_statistics()
            old_config = {
                "interval_seconds": command.scraping_config.get(
                    "interval_seconds", 300
                ),
                "max_concurrency": command.scraping_config.get("max_concurrency", 5),
                "request_timeout": command.scraping_config.get("request_timeout", 30),
                "max_articles_per_fetch": command.scraping_config.get(
                    "max_articles_per_fetch", 50
                ),
                "retry_attempts": command.scraping_config.get("retry_attempts", 3),
            }

            # 5. Mapear configuración a SourceConfiguration
            new_source_config = self._map_scraping_config_to_source_configuration(
                command.scraping_config
            )

            # 6. Actualizar configuración en el aggregate
            reason = f"Configuración actualizada por {command.updated_by or 'system'}"
            scraping.update_configuration(new_source_config, reason=reason)

            # 7. Persistir aggregate con eventos generados
            await self._scraping_write_repo.save(scraping)

            # 8. Publicar eventos de dominio
            events_published = await self._publish_scraping_domain_events(scraping)

            self._logger.info(
                "Configuración de scraping actualizada exitosamente",
                source_id=command.source_id,
                events_published=events_published,
                correlation_id=command.correlation_id,
            )

            return UpdateScrapingConfigResult.success_result(
                source_id=command.source_id,
                old_config=old_config,
                new_config=command.scraping_config.copy(),
                changes_applied=command.apply_immediately,
            )

        except ScrapingNotFoundError as e:
            self._logger.error(
                "Scraping no encontrado",
                source_id=command.source_id,
                error=str(e),
            )
            return UpdateScrapingConfigResult.scraping_not_found(command.source_id)

        except (InvalidScrapingConfigError, ValueError) as e:
            # Crear error event para tracking
            error_event = self._error_tracking_service.create_error_event(
                message=f"Error de configuración de scraping: {str(e)}",
                source_id=command.source_id,
                context={
                    "operation": "update_scraping_config",
                    "source_id": command.source_id,
                    "correlation_id": command.correlation_id,
                    "error_type": "INVALID_CONFIG",
                },
            )

            self._logger.error(
                "Error de configuración de scraping",
                source_id=command.source_id,
                error=str(e),
                error_category=getattr(
                    error_event.category, "value", str(error_event.category)
                ),
            )

            return UpdateScrapingConfigResult.failure_result(
                source_id=command.source_id,
                message=str(e),
                error_code="INVALID_CONFIG",
            )

        except Exception as e:
            # Crear error event para tracking de errores inesperados
            error_event = self._error_tracking_service.create_error_event(
                message=f"Error inesperado al actualizar configuración: {str(e)}",
                source_id=command.source_id,
                context={
                    "operation": "update_scraping_config",
                    "source_id": command.source_id,
                    "correlation_id": command.correlation_id,
                    "error_type": "INTERNAL_ERROR",
                    "exception_type": type(e).__name__,
                },
            )

            self._logger.exception(
                "Error inesperado al actualizar configuración",
                source_id=command.source_id,
                error=str(e),
                error_category=getattr(
                    error_event.category, "value", str(error_event.category)
                ),
            )

            return UpdateScrapingConfigResult.failure_result(
                source_id=command.source_id,
                message=f"Error interno: {str(e)}",
                error_code="INTERNAL_ERROR",
            )

    def _map_scraping_config_to_source_configuration(
        self, scraping_config: dict
    ) -> SourceConfiguration:
        """
        Mapea la configuración del comando a SourceConfiguration.

        Args:
            scraping_config: Diccionario de configuración del comando

        Returns:
            SourceConfiguration con los valores mapeados
        """
        config_params = {}

        # Mapear interval_seconds a fetch_interval_minutes
        if "interval_seconds" in scraping_config:
            config_params["fetch_interval_minutes"] = (
                scraping_config["interval_seconds"] // 60
            )

        # Mapear request_timeout a timeout_seconds
        if "request_timeout" in scraping_config:
            config_params["timeout_seconds"] = scraping_config["request_timeout"]

        # Campos que tienen el mismo nombre
        if "max_articles_per_fetch" in scraping_config:
            config_params["max_articles_per_fetch"] = scraping_config[
                "max_articles_per_fetch"
            ]

        if "retry_attempts" in scraping_config:
            config_params["retry_attempts"] = scraping_config["retry_attempts"]

        # Si no hay parámetros, usar configuración por defecto
        if not config_params:
            return SourceConfiguration.default()

        return SourceConfiguration(**config_params)

    async def _publish_scraping_domain_events(self, scraping: Scraping) -> int:
        """
        Publica los eventos de dominio generados por el agregado Scraping.

        Args:
            scraping: Agregado Scraping con eventos pendientes

        Returns:
            Número de eventos publicados
        """
        events = scraping.domain_events
        events_count = len(events)

        for event in events:
            await self._event_publisher.publish(event)
            self._logger.debug(
                "Evento ScrapingSession publicado",
                event_type=type(event).__name__,
                scraping_id=str(scraping.id),
            )

        scraping.mark_events_as_committed()

        self._logger.info(
            "Publicados eventos de dominio del ScrapingSession",
            events_count=events_count,
            scraping_id=str(scraping.id),
        )

        return events_count
