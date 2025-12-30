"""Handler para UpdateSource command usando Source aggregate independiente."""

from uuid import UUID

from src.rss.feed.domain.aggregates import Source
from src.rss.feed.domain.interfaces.repositories import (
    ISourceReadRepository,
    ISourceWriteRepository,
)
from src.rss.feed.domain.value_objects.configuration import SourceConfiguration
from src.rss.feed.domain.value_objects.description import SourceDescription
from src.rss.feed.domain.value_objects.name import SourceName
from src.rss.feed.domain.value_objects.rss_feed_id import RssFeedId
from src.scraping.domain.interfaces.services.error_tracking import (
    IErrorTrackingService,
)
from src.shared.kernel.logger import ILogger

from .command import UpdateSourceCommand
from .exception import (
    InvalidSourceUpdateError,
    SourceConfigurationError,
    SourceNotFoundError,
)
from .mapper import UpdateSourceMapper
from .result import UpdateSourceResult
from .validator import UpdateSourceValidator


class UpdateRssFeedHandler:
    """Handler para UpdateSourceCommand usando Source aggregate independiente."""

    def __init__(
        self,
        source_read_repository: ISourceReadRepository,
        source_write_repository: ISourceWriteRepository,
        validator: UpdateSourceValidator,
        logger: ILogger,
        error_tracking_service: IErrorTrackingService,
    ):
        self._source_read_repo = source_read_repository
        self._source_write_repo = source_write_repository
        self._validator = validator
        self._logger = logger.bind(layer="application", component="UpdateSourceHandler")
        self._error_tracking_service = error_tracking_service

    async def handle(self, command: UpdateSourceCommand) -> UpdateSourceResult:
        """
        Maneja comando de actualización de Source.

        Args:
            command: Comando con nuevos detalles/configuración

        Returns:
            UpdateSourceResult: Resultado de la operación
        """
        self._logger.info(
            "Iniciando actualización de Source",
            source_id=command.source_id,
            correlation_id=command.correlation_id,
        )

        try:
            # 1. Validar comando
            try:
                self._validator.validate(command)
            except InvalidSourceUpdateError as e:
                self._logger.error("Validación fallida", error=str(e))
                return UpdateSourceResult.failure_result(
                    source_id=command.source_id,
                    message=f"Validación fallida: {str(e)}",
                    error_code="VALIDATION_ERROR",
                )

            # 2. Convertir str → UUID y SourceId
            source_id_uuid = UUID(command.source_id)
            source_id = SourceId.from_string(command.source_id)

            # 3. Recuperar Source aggregate usando read repository
            source = await self._source_read_repo.find_by_id(source_id_uuid)
            if not source:
                return UpdateSourceResult.source_not_found(command.source_id)

            # 4. Capturar detalles anteriores usando mapper local
            old_details = UpdateSourceMapper.source_to_summary(source)

            # 5. Actualizar detalles básicos si se proporcionan
            updated_name = None
            updated_description = None

            if command.name is not None:
                updated_name = SourceName(command.name.strip())

            if command.description is not None:
                updated_description = (
                    SourceDescription(command.description.strip())
                    if command.description.strip()
                    else None
                )

            if updated_name or updated_description is not None:
                source.update_details(
                    name=updated_name, description=updated_description
                )

            # 6. Actualizar configuración si se proporciona
            config_updated = False
            if command.source_config is not None:
                try:
                    new_config = SourceConfiguration(**command.source_config)
                    source.update_configuration(new_config)
                    config_updated = True
                except Exception as e:
                    return UpdateSourceResult.failure_result(
                        source_id=command.source_id,
                        message=f"Error en configuración: {str(e)}",
                        error_code="INVALID_CONFIG",
                    )

            # 7. Persistir aggregate con eventos generados
            await self._source_write_repo.save(source)

            # 8. Capturar detalles nuevos usando mapper local
            new_details = UpdateSourceMapper.source_to_summary(source)

            # 9. Log éxito
            self._logger.info(
                "Source actualizado exitosamente",
                source_id=command.source_id,
                config_updated=config_updated,
                correlation_id=command.correlation_id,
            )

            # 10. Construir resultado exitoso
            return UpdateSourceResult.success_result(
                source_id=command.source_id,
                old_details=old_details,
                new_details=new_details,
                config_updated=config_updated,
            )

        except SourceNotFoundError as e:
            self._logger.error("Source no encontrado", error=str(e))
            return UpdateSourceResult.source_not_found(command.source_id)

        except (InvalidSourceUpdateError, SourceConfigurationError) as e:
            # Crear error event para tracking
            error_event = self._error_tracking_service.create_error_event(
                message=f"Error de configuración en source: {str(e)}",
                source_id=command.source_id,
                context={
                    "operation": "update_source",
                    "source_id": command.source_id,
                    "correlation_id": command.correlation_id,
                    "error_type": "INVALID_CONFIG",
                },
            )

            self._logger.error(
                "Error de configuración",
                error=str(e),
                error_category=error_event.category,
                error_severity=error_event.severity,
            )
            return UpdateSourceResult.failure_result(
                source_id=command.source_id,
                message=str(e),
                error_code="INVALID_CONFIG",
            )

        except Exception as e:
            # Crear error event para tracking de errores inesperados
            error_event = self._error_tracking_service.create_error_event(
                message=f"Error inesperado al actualizar source: {str(e)}",
                source_id=command.source_id,
                context={
                    "operation": "update_source",
                    "source_id": command.source_id,
                    "correlation_id": command.correlation_id,
                    "error_type": "INTERNAL_ERROR",
                    "exception_type": type(e).__name__,
                },
            )

            self._logger.exception(
                "Error inesperado al actualizar source",
                error=str(e),
                error_category=error_event.category,
                error_severity=error_event.severity,
            )
            return UpdateSourceResult.failure_result(
                source_id=command.source_id,
                message=f"Error interno: {str(e)}",
                error_code="INTERNAL_ERROR",
            )
