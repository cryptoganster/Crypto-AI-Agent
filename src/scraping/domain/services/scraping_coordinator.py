"""
Scraping Coordinator Service - Coordina operaciones de scraping RSS.

Este servicio coordina el proceso completo de scraping:
- Fetch de contenido RSS
- Creación de artículos
- Deduplicación
- Evaluación de calidad

MIGRACIÓN COMPLETADA:
- Migrado desde: src/domain/services/sources/source_fetching_service.py
- Renombrado: SourceFetchingService → ScrapingCoordinatorService
- Interface: IScrapingCoordinator (antes ISourceFetchingService)
- Ubicación: src/scraping/domain/services/scraping_coordinator.py
- Interface ubicación: src/scraping/domain/interfaces/services/scraping_orchestrator.py

BOUNDED CONTEXT:
Este servicio pertenece al bounded context Scraping porque coordina
el proceso completo de scraping, conectando Source (input) con Article (output).
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID

from src.rss.article.domain.aggregates import RssArticle
from src.rss.article.domain.interfaces.factories import IArticleFactory
from src.rss.article.domain.interfaces.repositories import (
    IArticleWriteRepository,
)
from src.rss.article.domain.interfaces.services.deduplication import (
    IArticleDeduplicationService,
)
from src.rss.article.domain.interfaces.services.quality import (
    IArticleQualityService,
)
from src.rss.article.domain.value_objects import ArticleId

# Domain aggregates
from src.rss.feed.domain.aggregates import Source
from src.rss.feed.domain.interfaces.repositories import (
    ISourceWriteRepository,
)
from src.rss.feed.domain.interfaces.services.health import (
    ISourceHealthService,
)

# Value objects
from src.rss.feed.domain.value_objects import SourceId
from src.scraping.domain.aggregates import Scraping
from src.scraping.domain.entities import ScrapingId

# External services (infrastructure)
from src.scraping.domain.interfaces.external import (
    ArticleData,
    IRssFeedFetcherService,
)
from src.scraping.domain.interfaces.repositories import (
    IScrapingWriteRepository,
)

# Interfaces
from src.scraping.domain.interfaces.services import (
    FetchResult,
    IScrapingCoordinator,
)

# RSS domain value objects
from src.scraping.domain.value_objects import FetchLimit
from src.scraping.domain.value_objects import ScrapingIdentity as ScrapingId

# Shared domain
from src.shared.domain.value_objects import Level, QualityThreshold


class ScrapingCoordinatorService(IScrapingCoordinator):
    """
    Servicio de dominio que coordina operaciones de scraping RSS.

    Responsabilidades:
    - Coordinar scraping entre agregados Source, Scraping y Article
    - Orquestar operaciones de fetch manteniendo consistencia
    - Aplicar reglas de negocio del dominio (calidad, deduplicación)
    - Delegar persistencia a repositories especializados

    Este servicio pertenece al bounded context Scraping porque coordina
    el proceso completo de scraping, conectando Source (input) con
    Article (output).
    """

    def __init__(
        self,
        rss_fetcher: Optional[IRssFeedFetcherService],
        article_repository: Optional[IArticleWriteRepository],
        source_repository: Optional[ISourceWriteRepository],
        scraping_repository: Optional[IScrapingWriteRepository],
        source_health_service: Optional[ISourceHealthService],
        article_deduplication_service: Optional[IArticleDeduplicationService],
        article_quality_service: Optional[IArticleQualityService],
        article_factory: Optional[IArticleFactory],
        logger: Optional[Any] = None,
    ):
        """
        Inicializa el coordinador con dependencias inyectadas.

        Args:
            rss_fetcher: Servicio de infraestructura para fetch HTTP/RSS
            article_repository: Repository para agregados Article
            source_repository: Repository para agregados Source
            scraping_repository: Repository para agregados Scraping
            source_health_service: Servicio de dominio para validaciones de salud
            article_deduplication_service: Servicio de dominio para deduplicación
            article_quality_service: Servicio de dominio para evaluación de calidad
            article_factory: Factory para creación de Articles con validaciones
            logger: Logger estructurado
        """
        self._rss_fetcher = rss_fetcher
        self._article_repository = article_repository
        self._source_repository = source_repository
        self._scraping_repository = scraping_repository
        self._source_health_service = source_health_service
        self._article_deduplication_service = article_deduplication_service
        self._article_quality_service = article_quality_service
        self._article_factory = article_factory

        # Logger
        if logger:
            self._logger = logger.bind(
                layer="domain",
                component="ScrapingCoordinatorService",
            )
        else:
            # Fallback logger
            from loguru import logger as loguru_logger

            self._logger = loguru_logger.bind(
                layer="domain",
                component="ScrapingCoordinatorService",
            )

    async def fetch_sources(
        self,
        sources: List[Source],
        scraping: Scraping,
        fetch_limit: Optional[FetchLimit] = None,
        quality_threshold: Optional[QualityThreshold] = None,
    ) -> FetchResult:
        """
        Coordina scraping para múltiples fuentes usando agregados DDD.

        Args:
            sources: Lista de agregados Source activos para scraping
            scraping: Agregado Scraping que coordina la sesión
            fetch_limit: Límite de artículos por fuente
            quality_threshold: Umbral de calidad para filtrado

        Returns:
            FetchResult con métricas agregadas de la operación
        """
        # Validar sources antes de procesar
        valid_sources = [s for s in sources if self.validate_source_for_fetch(s)]

        if not valid_sources:
            return FetchResult(
                success=True,
                total_sources_processed=0,
                successful_sources=0,
                failed_sources=0,
                total_articles_discovered=0,
                total_articles_created=0,
                scraping_id=str(scraping.id),
            )

        # Contadores para métricas
        successful_sources = 0
        failed_sources = 0
        total_articles_discovered = 0
        total_articles_created = 0
        all_article_ids = []

        # Procesar cada source individualmente
        for source in valid_sources:
            try:
                self._logger.info(
                    f"Procesando source: {source.name}",
                    source_id=str(source.id),
                    source_url=str(source.url),
                )

                result = await self.fetch_single_source(
                    source=source,
                    scraping=scraping,
                    fetch_limit=fetch_limit,
                    quality_threshold=quality_threshold,
                )

                if result["success"]:
                    successful_sources += 1
                    total_articles_discovered += result.get("articles_discovered", 0)
                    total_articles_created += result.get("articles_created", 0)
                    all_article_ids.extend(result.get("article_ids", []))

                    self._logger.success(
                        f"✅ Source procesada exitosamente: {source.name}",
                        source_id=str(source.id),
                        articles_created=result.get("articles_created", 0),
                        articles_discovered=result.get("articles_discovered", 0),
                    )
                else:
                    failed_sources += 1
                    error_msg = result.get("error", "Unknown error")
                    self._logger.error(
                        f"❌ Error procesando source: {source.name} | Error: {error_msg}"
                    )

            except Exception as e:
                failed_sources += 1
                self._logger.exception(
                    f"❌ Excepción procesando source: {source.name}",
                    source_id=str(source.id),
                    error=str(e),
                )

        return FetchResult(
            success=True,
            total_sources_processed=len(valid_sources),
            successful_sources=successful_sources,
            failed_sources=failed_sources,
            total_articles_discovered=total_articles_discovered,
            total_articles_created=total_articles_created,
            scraping_id=str(scraping.id),
            article_ids=all_article_ids,
        )

    async def fetch_single_source(
        self,
        source: Source,
        scraping: Scraping,
        fetch_limit: Optional[FetchLimit] = None,
        quality_threshold: Optional[QualityThreshold] = None,
    ) -> Dict[str, Any]:
        """
        Procesa una fuente específica usando agregados Source y Scraping.

        Args:
            source: Agregado Source a procesar
            scraping: Agregado Scraping para tracking
            fetch_limit: Límite de artículos a procesar
            quality_threshold: Umbral de calidad opcional

        Returns:
            Dict con métricas de resultado para la fuente específica
        """
        # 1. Validar que la source esté lista
        if not self.validate_source_for_fetch(source):
            return {
                "success": False,
                "articles_created": 0,
                "articles_discovered": 0,
                "error": f"Source {source.name} no está válida para fetch",
            }

        # 2. Usar el Scraping aggregate que ya fue creado por el handler
        scraping_id = str(scraping.id)

        # 3. Ejecutar fetch HTTP usando infraestructura
        if self._rss_fetcher is None:
            return {
                "success": False,
                "articles_created": 0,
                "articles_discovered": 0,
                "error": "RssFetcherService not configured",
            }

        try:
            fetch_result = await self._rss_fetcher.fetch_from_source(
                source=source,
                scraping=scraping,
                scraping_id=scraping_id,
            )
        except Exception as e:
            self._logger.exception(
                "Error en fetch HTTP",
                source_id=str(source.id),
                error=str(e),
            )
            return {
                "success": False,
                "articles_created": 0,
                "articles_discovered": 0,
                "error": f"Error en fetch HTTP: {str(e)}",
            }

        if not fetch_result.success:
            return {
                "success": False,
                "articles_created": 0,
                "articles_discovered": 0,
                "error": fetch_result.error_message or "Fetch failed",
            }

        # 4. Aplicar límites de dominio
        articles_data = fetch_result.articles_data or []
        if fetch_limit and articles_data:
            articles_data = articles_data[: fetch_limit.max_items]

        # 5. Persistir Source (para actualizar métricas)
        if self._source_repository:
            try:
                await self._source_repository.save(source)
            except Exception as e:
                self._logger.error(
                    "Error persistiendo source",
                    source_id=str(source.id),
                    error=str(e),
                )

        # 6. Crear agregados Article
        try:
            articles_created = await self.create_articles_from_fetch(
                articles_data=articles_data,
                source=source,
                scraping=scraping,
                quality_threshold=quality_threshold,
            )
        except Exception as e:
            self._logger.exception(
                "Error creando artículos",
                source_id=str(source.id),
                error=str(e),
            )
            return {
                "success": False,
                "articles_created": 0,
                "articles_discovered": len(articles_data) if articles_data else 0,
                "error": f"Error creando artículos: {str(e)}",
            }

        result = {
            "success": True,
            "articles_created": len(articles_created),
            "articles_discovered": len(articles_data) if articles_data else 0,
            "article_ids": [str(article.id) for article in articles_created],
        }

        self._logger.info(
            f"🔍 DEBUG: fetch_single_source completado | "
            f"source={str(source.name)} | "
            f"articles_created={result['articles_created']} | "
            f"articles_discovered={result['articles_discovered']} | "
            f"article_ids_count={len(result['article_ids'])}"
        )

        return result

    async def create_articles_from_fetch(
        self,
        articles_data: List[ArticleData],
        source: Source,
        scraping: Scraping,
        quality_threshold: Optional[QualityThreshold] = None,
    ) -> List[RssArticle]:
        """
        Crea agregados RssArticle desde datos de fetch RSS.

        Args:
            articles_data: Lista de datos de artículos extraídos
            source: Agregado Source de origen
            scraping: Agregado Scraping para contexto
            quality_threshold: Umbral de calidad para filtrado

        Returns:
            Lista de agregados RssArticle creados
        """
        created_articles = []

        for idx, article_data in enumerate(articles_data, 1):
            try:
                # Aplicar filtro de calidad
                if quality_threshold and self._article_quality_service:
                    if not self._article_quality_service.meets_quality_threshold(
                        article_data, quality_threshold
                    ):
                        continue

                # Verificar duplicados
                if self._article_deduplication_service:
                    is_dup = await self._article_deduplication_service.check_duplicate_by_url(
                        article_data, source
                    )
                    if is_dup:
                        continue

                # Verificar factory
                if not self._article_factory:
                    continue

                # Crear Article usando factory
                article = self._article_factory.create_article(
                    title=article_data.title,
                    url=article_data.url,
                    source_id=source.id,
                    content=article_data.content or article_data.summary,
                    thumbnail_url=article_data.thumbnail_url,
                    guid=article_data.guid,
                    published_at=article_data.published_at,
                    description=article_data.description,
                    author=article_data.author,
                    tags=article_data.tags,
                )

                # Verificar repository
                if not self._article_repository:
                    continue

                # Persistir agregado (sin commit, manejado por UoW)
                await self._article_repository.save(article)
                created_articles.append(article)

            except Exception as save_error:
                # Duplicados en BD - skip silenciosamente
                error_msg = str(save_error).lower()
                if "unique constraint" in error_msg or "duplicate key" in error_msg:
                    continue

                # Otro error - log y continuar
                self._logger.exception(
                    f"Error guardando artículo {idx}/{len(articles_data)}",
                    url=article_data.url,
                    error=str(save_error),
                )
                continue

        return created_articles

    def validate_source_for_fetch(self, source: Source) -> bool:
        """
        Valida si Source aggregate está listo para fetch.

        Delegado a SourceHealthService para centralizar lógica de validación.

        Args:
            source: Agregado Source a validar

        Returns:
            True si el agregado puede ser procesado
        """
        if not self._source_health_service:
            return False
        return self._source_health_service.validate_source_for_scraping(source)
