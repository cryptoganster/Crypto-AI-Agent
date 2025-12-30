"""Handler para StartScrapingCommand.

Handler simple que sigue Clean Architecture + CQRS + Event-Driven estricto:

1. Valida comando
2. Resuelve sources (por IDs, URLs, o todas activas)
3. Crea sesión de scraping via Factory (Factory emite evento ScrapingStarted)
4. Guarda aggregate via Repository (Repository publica eventos automáticamente)
5. Retorna resultado

El evento ScrapingStarted se emite desde el Aggregate (via Factory),
NO desde el Handler. Esto sigue el principio DDD de que los eventos
de dominio deben originarse en el Aggregate.

El ScrapingPipeline escucha el evento y coordina el resto.
"""

from typing import List, Tuple
from uuid import UUID

from src.rss.feed.domain.interfaces.repositories import ISourceReadRepository
from src.scraping.app.commands.start_scraping.command import StartScrapingCommand
from src.scraping.app.commands.start_scraping.exception import (
    NoSourcesAvailableError,
    StartScrapingValidationError,
)
from src.scraping.app.commands.start_scraping.result import StartScrapingResult
from src.scraping.app.commands.start_scraping.validator import StartScrapingValidator
from src.scraping.domain.interfaces.factories import IScrapingFactory
from src.scraping.domain.interfaces.repositories import IScrapingWriteRepository
from src.shared.kernel.logger import ILogger


class StartScrapingHandler:
    """
    Handler para iniciar scraping de sources.

    Sigue Clean Architecture + CQRS + Event-Driven estricto:
    - Valida el comando
    - Resuelve sources a procesar (por IDs, URLs, o todas activas)
    - Crea sesión de scraping via Factory (emite evento ScrapingStarted)
    - Guarda aggregate via Repository (publica eventos automáticamente)
    - Retorna resultado

    El evento ScrapingStarted se emite desde el Aggregate (via Factory),
    siguiendo el principio DDD. El Repository publica los eventos
    automáticamente al guardar.

    NO hace el scraping real. El ScrapingPipeline escucha
    el evento ScrapingStarted y coordina el resto.

    Las opciones de scraping (quality_threshold, enable_deduplication, etc.)
    se pasan al Factory y se transportan en el evento ScrapingStarted.
    """

    def __init__(
        self,
        source_read_repository: ISourceReadRepository,
        scraping_repository: IScrapingWriteRepository,
        scraping_factory: IScrapingFactory,
        session_factory,  # async_sessionmaker para crear sesiones nuevas
        logger: ILogger,
        validator: StartScrapingValidator,
        event_bus=None,  # Deprecated: eventos se publican via Repository
    ):
        self._source_repo = source_read_repository
        self._scraping_repo = scraping_repository
        self._scraping_factory = scraping_factory
        self._session_factory = session_factory
        self._validator = validator
        self._logger = logger.bind(
            layer="application",
            component="StartScrapingHandler",
        )

    async def handle(self, command: StartScrapingCommand) -> StartScrapingResult:
        """
        Ejecuta el comando de inicio de scraping.

        Args:
            command: Comando con configuración y opciones

        Returns:
            StartScrapingResult indicando si se inició correctamente
        """
        try:
            # 1. Validar comando
            self._validator.validate(command)

            self._logger.info(
                "Iniciando scraping",
                source_ids=command.source_ids,
                source_urls=command.source_urls,
                is_all_sources=command.is_all_sources,
                quality_threshold=command.quality_threshold,
                correlation_id=command.correlation_id,
            )

            # 2. Resolver sources (por IDs, URLs, o todas activas)
            source_ids, invalid_urls = await self._resolve_sources(command)

            if not source_ids:
                self._logger.warning(
                    "No hay sources para scrapear",
                    invalid_urls=invalid_urls,
                )
                return StartScrapingResult.no_sources(invalid_urls=invalid_urls)

            self._logger.info(
                "Sources resueltas",
                sources_count=len(source_ids),
                invalid_urls_count=len(invalid_urls),
            )

            # 3. Crear sesión de scraping (Factory emite evento ScrapingStarted)
            from src.rss.feed.domain.value_objects import SourceId

            scraping = self._scraping_factory.create_multi_source(
                sources=[SourceId(UUID(sid)) for sid in source_ids],
                config=None,  # Usar config por defecto
                # Opciones de procesamiento → transportadas en el evento
                quality_threshold=command.quality_threshold,
                enable_quality_filter=command.enable_quality_filter,
                enable_deduplication=command.enable_deduplication,
                force_refresh=command.force_refresh,
                max_items_per_source=command.max_items_per_source,
                session_name=command.session_name,
                triggered_by=command.triggered_by,
            )

            # 4. Guardar aggregate con UoW
            # ARQUITECTURA: Crear UoW con sesión nueva para esta transacción
            from src.shared.kernel.uow import SqlAlchemyUnitOfWork

            session = self._session_factory()
            uow = SqlAlchemyUnitOfWork(
                session=session,
                logger=self._logger,
            )

            async with uow:
                await self._scraping_repo.save(scraping)
                await uow.commit()

            self._logger.info(
                "Sesión de scraping creada y evento ScrapingStarted emitido",
                scraping_id=str(scraping.id),
                sources_count=len(source_ids),
                quality_threshold=command.quality_threshold,
            )

            # 5. Retornar resultado
            return StartScrapingResult.started(
                scraping_id=str(scraping.id),
                source_ids=source_ids,
                invalid_urls=invalid_urls,
            )

        except StartScrapingValidationError as e:
            self._logger.error("Error de validación", error=str(e))
            return StartScrapingResult.failure(
                error=str(e),
                error_code="VALIDATION_ERROR",
            )

        except Exception as e:
            self._logger.exception("Error iniciando scraping", error=str(e))
            return StartScrapingResult.failure(
                error=f"Error interno: {str(e)}",
                error_code="INTERNAL_ERROR",
            )

    async def _resolve_sources(
        self, command: StartScrapingCommand
    ) -> Tuple[List[str], List[str]]:
        """
        Resuelve las sources a procesar.

        Soporta tres modos:
        1. Por source_ids: Buscar fuentes por IDs
        2. Por source_urls: Buscar fuentes por URLs
        3. Sin especificar: Obtener todas las fuentes activas

        Args:
            command: Comando con source_ids, source_urls, o None para todas

        Returns:
            Tupla de (source_ids válidos, urls inválidas)
        """
        invalid_urls: List[str] = []

        # Modo 1: Por source_ids
        if command.source_ids:
            valid_ids = []
            for source_id_str in command.source_ids:
                try:
                    source_id = UUID(source_id_str)
                    source = await self._source_repo.find_by_id(source_id)

                    if source and source.is_active:
                        valid_ids.append(source_id_str)
                    else:
                        self._logger.warning(
                            "Source no encontrada o inactiva",
                            source_id=source_id_str,
                        )
                except ValueError:
                    self._logger.warning(
                        "ID de source inválido",
                        source_id=source_id_str,
                    )

            return valid_ids, invalid_urls

        # Modo 2: Por source_urls
        if command.source_urls:
            valid_ids = []
            for url in command.source_urls:
                try:
                    source = await self._source_repo.find_by_url(url)

                    if source and source.is_active:
                        valid_ids.append(str(source.id))
                    else:
                        invalid_urls.append(url)
                        self._logger.warning(
                            "Source no encontrada o inactiva por URL",
                            url=url,
                        )
                except Exception as e:
                    invalid_urls.append(url)
                    self._logger.warning(
                        "Error buscando source por URL",
                        url=url,
                        error=str(e),
                    )

            return valid_ids, invalid_urls

        # Modo 3: Todas las sources activas
        self._logger.info("Buscando todas las sources activas...")
        try:
            sources = await self._source_repo.find_active()
            self._logger.info(f"Sources activas encontradas: {len(sources)}")
            return [str(s.id) for s in sources], invalid_urls
        except Exception as e:
            self._logger.exception("Error buscando sources activas", error=str(e))
            raise
