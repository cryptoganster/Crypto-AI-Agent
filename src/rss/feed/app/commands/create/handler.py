"""Handler para el comando CreateSourceCommand refactorizado para usar Source aggregate."""

from src.rss.feed.domain.aggregates import Source
from src.rss.feed.domain.interfaces.factories import ISourceFactory
from src.rss.feed.domain.interfaces.repositories import (
    ISourceReadRepository,
    ISourceWriteRepository,
)
from src.rss.feed.domain.value_objects.configuration import SourceConfiguration
from src.rss.feed.domain.value_objects.description import SourceDescription
from src.rss.feed.domain.value_objects.name import SourceName
from src.rss.feed.domain.value_objects.rss_feed_url import RssFeedUrl
from src.shared.kernel.logger import ILogger

from .command import CreateSourceCommand
from .exception import CreateSourceException
from .result import CreateSourceResult, CreateSourceResultBuilder


class CreateSourceCommandHandler:
    """
    Handler para procesar el comando CreateSourceCommand usando el agregado Source.

    Este handler refactorizado se encarga de:
    1. Validar la estructura del comando y construir Value Objects
    2. Verificar que no exista una fuente con la misma URL
    3. Crear el nuevo agregado Source con configuración
    4. Activar la fuente si se especifica
    5. Persistir el agregado usando ISourceRepository con automatic event publishing
    """

    def __init__(
        self,
        source_read_repo: ISourceReadRepository,
        source_write_repo: ISourceWriteRepository,
        source_factory: ISourceFactory,
        uow,  # IUnitOfWork
        logger: ILogger,
    ):
        self._read_repo = source_read_repo
        self._write_repo = source_write_repo
        self._source_factory = source_factory
        self._uow = uow
        self._logger = logger.bind(
            layer="application", handler="CreateSourceCommandHandler"
        )

    async def handle(self, command: CreateSourceCommand) -> CreateSourceResult:
        """
        Procesa el comando CreateSource usando el agregado Source.

        Args:
            command: Comando con datos para crear la fuente RSS

        Returns:
            CreateSourceResult: Resultado de la operación

        Raises:
            CreateSourceException: Si hay errores durante el procesamiento
        """
        self._logger.info(
            "Procesando CreateSourceCommand con agregado Source",
            name=command.name,
            url=command.source_url,
        )

        try:
            # 1. Validar datos usando factory con validaciones avanzadas
            validation_result = self._source_factory.validate_source_creation_data(
                url=command.source_url,
                name=command.name,
                description=command.description,
            )

            if not validation_result.is_valid:
                # Acceder a error_messages del ValidationResult del factory
                error_msgs = getattr(
                    validation_result,
                    "error_messages",
                    getattr(validation_result, "errors", []),
                )
                error_msg = "; ".join(error_msgs)
                self._logger.error(
                    "Validación de factory falló",
                    name=command.name,
                    url=command.source_url,
                    errors=error_msgs,
                    warnings=getattr(validation_result, "warnings", []),
                )
                raise CreateSourceException(
                    f"Datos de comando inválidos: {error_msg}",
                    "INVALID_COMMAND_DATA",
                )

            # Log warnings si existen
            warnings = getattr(validation_result, "warnings", [])
            if warnings:
                self._logger.warning(
                    "Warnings en validación de factory",
                    name=command.name,
                    url=command.source_url,
                    warnings=warnings,
                )

            # Construir Value Objects validados
            source_url = SourceUrl(command.source_url)
            source_configuration = self._build_source_configuration(command)

        except ValueError as e:
            self._logger.error(
                "Error validando Value Objects",
                name=command.name,
                url=command.source_url,
                error=str(e),
            )
            raise CreateSourceException(
                f"Datos de comando inválidos: {str(e)}",
                "INVALID_COMMAND_DATA",
            )

        try:
            # 2. Verificar que no exista una fuente con la misma URL usando repository
            duplicates = await self._read_repo.find_duplicates_by_url(
                url=str(source_url)
            )
            if duplicates:
                existing_source = duplicates[0]
                self._logger.warning(
                    "Fuente con URL ya existe",
                    url=command.source_url,
                    existing_id=str(existing_source.id),
                )
                raise CreateSourceException(
                    f"Ya existe una fuente con la URL: {command.source_url}",
                    "SOURCE_URL_ALREADY_EXISTS",
                )

            # 3. Crear el nuevo agregado Source usando factory con validaciones avanzadas
            source = self._source_factory.create_source(
                url=command.source_url,
                name=command.name,
                description=command.description,
                configuration=source_configuration,
            )

            self._logger.info(
                "Agregado Source creado exitosamente",
                source_id=str(source.id),
                name=command.name,
            )

            # 4. Activar la fuente si se especifica
            if command.is_active:
                source.activate()
                self._logger.info(
                    "Source activado automáticamente",
                    source_id=str(source.id),
                )

            # 5. Persistir usando UoW
            async with self._uow:
                await self._write_repo.save(source)
                await self._uow.commit()

            self._logger.info(
                "Source persistido exitosamente",
                source_id=str(source.id),
            )

            # 6. Construir resultado exitoso
            return CreateSourceResultBuilder.success(
                source_id=str(source.id),
                name=command.name,
                url=command.source_url,
                is_active=command.is_active,
            )

        except CreateSourceException:
            # Re-raise domain exceptions as-is
            raise
        except Exception as e:
            self._logger.exception(
                "Error inesperado procesando CreateSourceCommand - Stack trace completo",
                name=command.name,
                url=command.source_url,
                error=str(e),
                error_type=type(e).__name__,
            )
            raise CreateSourceException(
                f"Error interno del sistema: {str(e)}",
                "INTERNAL_ERROR",
            )

    def _build_source_configuration(
        self, command: CreateSourceCommand
    ) -> SourceConfiguration:
        """
        Construye la configuración del Source desde los parámetros del comando.

        Args:
            command: Comando con parámetros de configuración

        Returns:
            SourceConfiguration: Configuración construida con valores del comando o defaults
        """
        return SourceConfiguration(
            fetch_interval_minutes=command.fetch_interval_minutes or 5,
            max_articles_per_fetch=command.max_articles_per_fetch or 50,
            timeout_seconds=command.timeout_seconds or 30,
            retry_attempts=3,
        )
