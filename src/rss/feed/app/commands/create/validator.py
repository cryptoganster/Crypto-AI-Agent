"""Validator para CreateSourceCommand refactorizado para usar agregado Source."""

from src.rss.feed.domain.interfaces.repositories import ISourceReadRepository
from src.rss.feed.domain.value_objects.configuration import SourceConfiguration
from src.rss.feed.domain.value_objects.description import SourceDescription
from src.rss.feed.domain.value_objects.name import SourceName
from src.rss.feed.domain.value_objects.rss_feed_url import RssFeedUrl
from src.shared.kernel.logger import ILogger

from .command import CreateSourceCommand
from .exception import (
    CreateSourceValidationException,
    DuplicateSourceException,
)


class CreateRssFeedValidator:
    """
    Validator para CreateSourceCommand usando el agregado Source.

    Responsabilidad única: Validar comandos CreateSource usando Value Objects
    y verificar duplicados en el repositorio Source.
    """

    def __init__(
        self,
        source_read_repository: ISourceReadRepository,
        logger: ILogger,
    ):
        self._source_read_repository = source_read_repository
        self._logger = logger

    async def validate_command(self, command: CreateSourceCommand) -> None:
        """
        Valida completamente un CreateSourceCommand usando Value Objects.

        Args:
            command: Comando a validar

        Raises:
            CreateSourceValidationException: Si las validaciones fallan
            DuplicateSourceException: Si se detecta fuente duplicada
        """
        self._logger.info(
            "Iniciando validaciones para CreateSourceCommand con agregado Source",
            name=command.name,
            url=command.source_url,
        )

        # 1. Validar y construir Value Objects (esto incluye validaciones básicas)
        validation_errors = []
        source_url = None

        try:
            source_url = SourceUrl(command.source_url)
        except ValueError as e:
            validation_errors.append(f"URL inválida: {str(e)}")

        try:
            source_name = SourceName(command.name)
        except ValueError as e:
            validation_errors.append(f"Nombre inválido: {str(e)}")

        try:
            source_description = SourceDescription(command.description or "")
        except ValueError as e:
            validation_errors.append(f"Descripción inválida: {str(e)}")

        # Validar parámetros de configuración
        try:
            self._validate_configuration_parameters(command)
        except ValueError as e:
            validation_errors.append(str(e))

        # Si hay errores de Value Objects, fallar rápidamente
        if validation_errors:
            self._logger.error(
                "Errores de validación de Value Objects",
                name=command.name,
                errors=validation_errors,
            )
            raise CreateSourceValidationException(
                f"Errores de validación: {'; '.join(validation_errors)}"
            )

        # 2. Verificar duplicados en repositorio (solo si source_url es válido)
        if source_url is not None:
            await self._check_source_duplicates(source_url)

        self._logger.info(
            "Validaciones completadas exitosamente",
            name=command.name,
            url=command.source_url,
        )

    def _validate_configuration_parameters(self, command: CreateSourceCommand) -> None:
        """Valida parámetros de configuración del comando."""
        if command.fetch_interval_minutes is not None:
            if command.fetch_interval_minutes <= 0:
                raise ValueError("fetch_interval_minutes debe ser mayor a 0")
            if command.fetch_interval_minutes > 1440:  # 24 horas
                raise ValueError(
                    "fetch_interval_minutes no puede exceder 1440 (24 horas)"
                )

        if command.max_articles_per_fetch is not None:
            if command.max_articles_per_fetch <= 0:
                raise ValueError("max_articles_per_fetch debe ser mayor a 0")
            if command.max_articles_per_fetch > 1000:
                raise ValueError("max_articles_per_fetch no puede exceder 1000")

        if command.timeout_seconds is not None:
            if command.timeout_seconds <= 0:
                raise ValueError("timeout_seconds debe ser mayor a 0")
            if command.timeout_seconds > 300:  # 5 minutos
                raise ValueError("timeout_seconds no puede exceder 300 segundos")

    async def _check_source_duplicates(self, source_url: SourceUrl) -> None:
        """Verifica duplicados usando ISourceReadRepository."""
        duplicates = await self._source_read_repository.find_duplicates_by_url(
            str(source_url)
        )

        if duplicates:
            existing_source = duplicates[0]
            self._logger.error(
                "Source duplicado detectado",
                url=str(source_url),
                existing_id=str(existing_source.id),
                existing_name=str(existing_source.name),
            )
            raise DuplicateSourceException(
                source_url=str(source_url),
                existing_id=str(existing_source.id),
            )
