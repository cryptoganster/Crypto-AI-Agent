"""Handler para ActivateSource command."""

from uuid import UUID

from src.rss.feed.domain.aggregates import Source
from src.rss.feed.domain.interfaces.repositories import (
    ISourceReadRepository,
    ISourceWriteRepository,
)
from src.rss.feed.domain.services import SourceHealthService
from src.rss.feed.domain.value_objects.rss_feed_id import RssFeedId
from src.shared.kernel.logger import ILogger

from .command import ActivateSourceCommand
from .exception import (
    SourceAlreadyActiveError,
    SourceHealthCheckFailedError,
    SourceNotFoundError,
)
from .interface import IActivateSourceHandler
from .result import ActivateSourceResult
from .validator import ActivateSourceValidator


class ActivateRssFeedHandler(IActivateSourceHandler):
    """Handler CQRS para ActivateSourceCommand usando Source aggregate."""

    def __init__(
        self,
        source_read_repo: ISourceReadRepository,
        source_write_repo: ISourceWriteRepository,
        source_health_service: SourceHealthService,
        validator: ActivateSourceValidator,
        logger: ILogger,
    ):
        self._read_repo = source_read_repo
        self._write_repo = source_write_repo
        self._source_health_service = source_health_service
        self._validator = validator
        self._logger = logger.bind(
            layer="application", component="ActivateSourceHandler"
        )

    async def handle(self, command: ActivateSourceCommand) -> ActivateSourceResult:
        """
        Maneja activación de fuente RSS usando nuevo aggregate Source.

        Args:
            command: Comando con información de activación

        Returns:
            ActivateSourceResult: Resultado de la operación
        """
        self._logger.info(
            "Iniciando activación de fuente RSS",
            source_id=command.source_id,
            correlation_id=command.correlation_id,
        )

        try:
            # 1. Validar parámetros
            validation_result = self._validator.validate(command)
            if not validation_result.is_valid:
                return ActivateSourceResult.failure_result(
                    source_id=command.source_id,
                    message=f"Validación fallida: {'; '.join(validation_result.errors)}",
                    error_code="VALIDATION_ERROR",
                )

            # 2. Convertir str → UUID para repository
            source_id_uuid = UUID(command.source_id)

            # 3. Recuperar Source aggregate usando read repository
            source = await self._read_repo.find_by_id(source_id_uuid)
            if not source:
                return ActivateSourceResult.source_not_found(command.source_id)

            # 4. Verificar si ya está activa
            if source.is_active and not command.force_activation:
                return ActivateSourceResult.source_already_active(command.source_id)

            # 5. Probar conexión si se requiere
            if command.test_connection:
                connection_test = (
                    await self._source_health_service.test_source_connection(source)
                )
                if not connection_test.is_healthy and not command.force_activation:
                    # Construir error_details desde issues
                    error_details = (
                        "; ".join(connection_test.issues)
                        if connection_test.issues
                        else "Health check failed"
                    )
                    return ActivateSourceResult.connection_test_failed(
                        command.source_id,
                        error_details,
                    )

            # 6. Resetear métricas de salud si se requiere
            if command.reset_health_metrics:
                source.reset_health_metrics()
                self._logger.info(
                    "Métricas de salud reseteadas",
                    source_id=command.source_id,
                )

            # 7. Activar fuente a través del aggregate
            source.activate()

            # 8. Persistir aggregate con eventos generados
            await self._write_repo.save(source)

            # 9. Log éxito
            self._logger.info(
                "Fuente RSS activada exitosamente",
                source_id=command.source_id,
                source_name=str(source.name),
                correlation_id=command.correlation_id,
            )

            # 10. Construir resultado exitoso
            return ActivateSourceResult.success_result(
                source_id=command.source_id,
                source_name=str(source.name),
                source_url=str(source.url),
                health_metrics_reset=command.reset_health_metrics,
                connection_tested=command.test_connection,
            )

        except SourceNotFoundError as e:
            self._logger.warning("Fuente no encontrada", error=str(e))
            return ActivateSourceResult.source_not_found(command.source_id)
        except ValueError as e:
            self._logger.warning("Error de validación en activación", error=str(e))
            return ActivateSourceResult.failure_result(
                source_id=command.source_id,
                message=str(e),
                error_code="ACTIVATION_ERROR",
            )
        except Exception as e:
            self._logger.exception(
                "Error inesperado al activar fuente RSS", error=str(e)
            )
            return ActivateSourceResult.failure_result(
                source_id=command.source_id,
                message=f"Error interno: {str(e)}",
                error_code="INTERNAL_ERROR",
            )
