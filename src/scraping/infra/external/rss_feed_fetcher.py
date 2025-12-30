"""Servicio RSS Fetcher para Scraping bounded context.

Implementación concreta de IRssFeedFetcherService usando aiohttp y feedparser.
"""

import asyncio
import re
from datetime import datetime, timezone
from typing import Dict, List, Optional
from urllib.parse import urlparse

import aiohttp
import feedparser

from src.rss.feed.domain.aggregates import Source
from src.rss.feed.domain.value_objects import SourceId
from src.rss.feed.domain.value_objects.rss_feed_url import SourceUrl
from src.scraping.domain.aggregates import Scraping
from src.scraping.domain.entities.scraping_record import ScrapingId
from src.scraping.domain.interfaces.external import (
    ArticleData,
    FetchResult,
    IRssFeedFetcherService,
)
from src.shared.kernel.logger import ILogger


class RssFeedFetcherService(IRssFeedFetcherService):
    """
    Servicio RSS Fetcher para Scraping bounded context.

    Implementa IRssFeedFetcherService usando Source, Scraping aggregates.

    Características:
    - Opera con agregados del dominio (Source, Scraping)
    - Coordina entre bounded contexts sin violar boundaries
    - Retorna ArticleData para crear Article aggregates
    - Logging estructurado con contexto
    - Rate limiting por dominio
    - Manejo robusto de errores HTTP y parsing
    """

    def __init__(
        self,
        logger: Optional[ILogger] = None,
        timeout: int = 30,
        max_concurrent: int = 10,
        rate_limit_delay: float = 1.0,
        user_agent: str = "FeedsAI-RSS/1.0 (+https://github.com/feedsai)",
    ):
        """
        Inicializar el fetcher RSS.

        Args:
            logger: Logger opcional para observabilidad
            timeout: Timeout en segundos para requests RSS
            max_concurrent: Máximo requests RSS concurrentes
            rate_limit_delay: Delay entre requests al mismo dominio RSS
            user_agent: User agent string especializado RSS
        """
        self._logger = (
            logger.bind(component="RssFeedFetcherService") if logger else None
        )
        self.timeout = timeout
        self.max_concurrent = max_concurrent
        self.rate_limit_delay = rate_limit_delay
        self.user_agent = user_agent

        # Rate limiting por dominio RSS
        self._domain_last_request: Dict[str, datetime] = {}
        self._semaphore = asyncio.Semaphore(max_concurrent)

        # Estadísticas RSS
        self._total_fetches = 0
        self._successful_fetches = 0
        self._failed_fetches = 0

        if self._logger:
            self._logger.info(
                "RSS Feed Fetcher Service inicializado",
                timeout=timeout,
                max_concurrent=max_concurrent,
                rate_limit_delay=rate_limit_delay,
            )

    async def fetch_from_source(
        self,
        source: Source,
        scraping: Scraping,
        scraping_id: ScrapingId,
    ) -> FetchResult:
        """
        Fetch RSS desde un Source aggregate con Scraping tracking.

        Args:
            source: Source aggregate con configuración
            scraping: Scraping aggregate para tracking
            scraping_id: ID del scraping record

        Returns:
            FetchResult con datos para crear Article aggregates
        """
        start_time = datetime.now(timezone.utc)

        try:
            # Validar que source esté activo
            if not source.is_active:
                raise ValueError(f"Source {source.id} no está activo")

            # Rate limiting usando Source aggregate
            await self._apply_rate_limit_for_source(source)

            # Fetch con semáforo para limitar concurrencia
            async with self._semaphore:
                article_data_list = await self._fetch_and_parse_from_source(
                    source, scraping
                )

            # Calcular duración
            duration_ms = (
                datetime.now(timezone.utc) - start_time
            ).total_seconds() * 1000

            # Actualizar estadísticas
            self._total_fetches += 1
            self._successful_fetches += 1

            if self._logger:
                self._logger.debug(
                    "RSS fetch completado exitosamente",
                    source_id=str(source.id),
                    source_name=str(source.name),
                    articles_found=len(article_data_list),
                    duration_ms=duration_ms,
                    scraping_id=scraping.id,
                )

            return FetchResult(
                success=True,
                source_id=source.id,
                source_url=source.url,
                scraping_id=scraping.id,
                articles_found=len(article_data_list),
                articles_new=len(article_data_list),
                fetch_duration_ms=duration_ms,
                article_data_list=article_data_list,
            )

        except Exception as e:
            duration_ms = (
                datetime.now(timezone.utc) - start_time
            ).total_seconds() * 1000
            self._total_fetches += 1
            self._failed_fetches += 1

            if self._logger:
                self._logger.error(
                    "RSS fetch falló",
                    source_id=str(source.id),
                    source_name=str(source.name),
                    error=str(e),
                    error_type=type(e).__name__,
                    scraping_id=str(scraping.id),
                    exc_info=True,
                )

            return FetchResult(
                success=False,
                source_id=source.id,
                source_url=source.url,
                scraping_id=scraping.id,
                articles_found=0,
                articles_new=0,
                fetch_duration_ms=duration_ms,
                error_message=str(e),
                error_type=type(e).__name__,
                article_data_list=[],
            )

    async def fetch_by_url(
        self,
        source_url: SourceUrl,
        scraping_id: str,
    ) -> FetchResult:
        """
        Fetch directo por URL (para casos simples sin aggregates).

        Args:
            source_url: URL RSS como Value Object
            scraping_id: ID de scraping para tracking

        Returns:
            FetchResult con datos de artículos
        """
        start_time = datetime.now(timezone.utc)

        # Crear SourceId temporal para el resultado
        temp_source_id = SourceId.generate()

        try:
            await self._apply_rate_limit_for_url(source_url)

            async with self._semaphore:
                article_data_list = await self._fetch_and_parse_by_url(source_url)

            duration_ms = (
                datetime.now(timezone.utc) - start_time
            ).total_seconds() * 1000

            self._total_fetches += 1
            self._successful_fetches += 1

            return FetchResult(
                success=True,
                source_id=temp_source_id,
                source_url=source_url,
                scraping_id=scraping_id,
                articles_found=len(article_data_list),
                articles_new=len(article_data_list),
                fetch_duration_ms=duration_ms,
                response_time_ms=duration_ms,
                article_data_list=article_data_list,
            )

        except Exception as e:
            duration_ms = (
                datetime.now(timezone.utc) - start_time
            ).total_seconds() * 1000
            self._total_fetches += 1
            self._failed_fetches += 1

            if self._logger:
                self._logger.error(
                    "RSS fetch by URL failed",
                    url=str(source_url),
                    error=str(e),
                    scraping_id=scraping_id,
                )

            return FetchResult(
                success=False,
                source_id=temp_source_id,
                source_url=source_url,
                scraping_id=scraping_id,
                articles_found=0,
                articles_new=0,
                fetch_duration_ms=duration_ms,
                error_message=str(e),
                error_type=type(e).__name__,
                article_data_list=[],
            )

    async def fetch_multiple_sources(
        self,
        sources: List[Source],
        scraping: Scraping,
    ) -> List[FetchResult]:
        """
        Fetch múltiples Source aggregates usando un Scraping.

        Args:
            sources: Lista de Source aggregates a procesar
            scraping: Scraping aggregate común para tracking

        Returns:
            Lista de FetchResult para crear Article aggregates
        """
        if not sources:
            return []

        if self._logger:
            self._logger.info(
                "Iniciando batch fetch RSS",
                sources_count=len(sources),
                scraping_id=scraping.id,
            )

        # Crear tasks para todos los fetches RSS
        tasks = [
            asyncio.create_task(self.fetch_from_source(source, scraping, scraping.id))
            for source in sources
        ]

        # Ejecutar todos los tasks
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Procesar resultados
        output = []
        for source, result in zip(sources, results):
            if isinstance(result, Exception):
                # Manejar excepciones no capturadas
                fetch_result = FetchResult(
                    success=False,
                    source_id=source.id,
                    source_url=source.url,
                    scraping_id=scraping.id,
                    articles_found=0,
                    articles_new=0,
                    fetch_duration_ms=0.0,
                    error_message=str(result),
                    error_type="TASK_EXCEPTION",
                    article_data_list=[],
                )
            else:
                fetch_result = result

            output.append(fetch_result)

        # Log estadísticas del lote
        successful = sum(1 for r in output if r.success)
        failed = len(output) - successful
        total_articles = sum(r.articles_found for r in output)

        if self._logger:
            self._logger.info(
                "Batch fetch RSS completado",
                successful_sources=successful,
                failed_sources=failed,
                total_articles=total_articles,
                scraping_id=scraping.id,
            )

        return output

    async def _fetch_and_parse_from_source(
        self, source: Source, scraping: Scraping
    ) -> List[ArticleData]:
        """Fetch y parseo especializado para Source aggregate."""
        try:
            # Headers HTTP personalizados para RSS
            headers = {
                "User-Agent": self.user_agent,
                "Accept": "application/rss+xml, application/xml, text/xml, */*",
                "Accept-Encoding": "gzip, deflate",
            }

            # Timeout más generoso: 10s para conectar, 60s para leer
            timeout = aiohttp.ClientTimeout(
                total=self.timeout * 2,  # Total: 60s
                connect=10,  # Conectar: 10s
                sock_read=60,  # Leer socket: 60s
            )

            async with aiohttp.ClientSession(
                timeout=timeout, headers=headers
            ) as session:
                async with session.get(source.url.value) as response:
                    response.raise_for_status()
                    # Leer contenido con timeout explícito
                    content = await asyncio.wait_for(response.text(), timeout=60.0)

            # Parseo usando feedparser
            return await self._parse_content_for_articles(content, source, scraping)

        except aiohttp.ClientError as e:
            if self._logger:
                self._logger.warning(
                    "Error HTTP durante fetch",
                    source_id=source.id.value,
                    source_url=source.url.value,
                    scraping_id=str(scraping.id),
                    error=str(e),
                    error_type="HTTP_ERROR",
                )
            raise

        except Exception as e:
            if self._logger:
                self._logger.error(
                    "Error durante fetch y parseo",
                    source_id=source.id.value,
                    source_url=source.url.value,
                    scraping_id=str(scraping.id),
                    error=str(e),
                    error_type="FETCH_PARSE_ERROR",
                )
            raise

    async def _fetch_and_parse_by_url(self, source_url: SourceUrl) -> List[ArticleData]:
        """Fetch y parseo por URL simple."""
        try:
            headers = {
                "User-Agent": self.user_agent,
                "Accept": "application/rss+xml, application/xml, text/xml, */*",
                "Accept-Encoding": "gzip, deflate",
            }

            # Timeout más generoso: 10s para conectar, 60s para leer
            timeout = aiohttp.ClientTimeout(
                total=self.timeout * 2,  # Total: 60s
                connect=10,  # Conectar: 10s
                sock_read=60,  # Leer socket: 60s
            )

            async with aiohttp.ClientSession(
                timeout=timeout, headers=headers
            ) as session:
                async with session.get(source_url.value) as response:
                    response.raise_for_status()
                    # Leer contenido con timeout explícito
                    content = await asyncio.wait_for(response.text(), timeout=60.0)

            return await self._parse_content_for_simple_articles(content, source_url)

        except Exception as e:
            if self._logger:
                self._logger.error(
                    "Error durante fetch by URL",
                    url=source_url.value,
                    error=str(e),
                )
            raise

    async def _parse_content_for_articles(
        self, content: str, source: Source, scraping: Scraping
    ) -> List[ArticleData]:
        """Parsea contenido RSS y retorna ArticleData."""
        try:
            feed = feedparser.parse(content)

            # Validar feed RSS
            if hasattr(feed, "bozo") and feed.bozo:
                error_msg = (
                    str(feed.bozo_exception)
                    if hasattr(feed, "bozo_exception")
                    else "Feed RSS malformado"
                )

                if "entries" in feed and len(feed.entries) > 0:
                    if self._logger:
                        self._logger.warning(
                            "Feed RSS con errores menores pero procesable",
                            source_id=source.id.value,
                            error_message=error_msg,
                            entries_count=len(feed.entries),
                        )
                else:
                    raise ValueError(f"Invalid RSS feed: {error_msg}")

            # Procesar entradas
            articles_data = []
            if hasattr(feed, "entries"):
                for entry in feed.entries:
                    try:
                        article_data = self._convert_entry_to_article_data(entry)
                        articles_data.append(article_data)
                    except Exception as e:
                        if self._logger:
                            self._logger.warning(
                                "Error procesando entrada RSS",
                                source_id=source.id.value,
                                error=str(e),
                            )
                        continue

            return articles_data

        except Exception as e:
            if self._logger:
                self._logger.error(
                    "Error durante parseo RSS",
                    source_id=source.id.value,
                    error=str(e),
                )
            raise

    async def _parse_content_for_simple_articles(
        self, content: str, source_url: SourceUrl
    ) -> List[ArticleData]:
        """Parsea contenido RSS desde URL simple."""
        try:
            feed = feedparser.parse(content)

            if hasattr(feed, "bozo") and feed.bozo:
                error_msg = (
                    str(feed.bozo_exception)
                    if hasattr(feed, "bozo_exception")
                    else "Feed RSS malformado"
                )

                if not ("entries" in feed and len(feed.entries) > 0):
                    raise ValueError(f"Invalid RSS feed: {error_msg}")

            articles_data = []
            if hasattr(feed, "entries"):
                for entry in feed.entries:
                    try:
                        article_data = self._convert_entry_to_article_data(entry)
                        articles_data.append(article_data)
                    except Exception as e:
                        if self._logger:
                            self._logger.warning(
                                "Error procesando entrada RSS", error=str(e)
                            )
                        continue

            return articles_data

        except Exception as e:
            if self._logger:
                self._logger.error("Error durante parseo RSS", error=str(e))
            raise

    def _convert_entry_to_article_data(self, entry) -> ArticleData:
        """Convierte entrada de feedparser a ArticleData."""
        # Extraer fecha de publicación
        published_at = None
        if hasattr(entry, "published_parsed") and entry.published_parsed:
            try:
                pub_date = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
                published_at = pub_date
            except (TypeError, ValueError):
                pass

        # Extraer categorías
        categories = []
        if hasattr(entry, "tags") and entry.tags:
            categories = [tag.term for tag in entry.tags if hasattr(tag, "term")]

        # Extraer contenido
        content = None
        if hasattr(entry, "content") and entry.content:
            content = entry.content[0].value if entry.content else None
        elif hasattr(entry, "description"):
            content = entry.description

        # Extraer thumbnail
        thumbnail_url = self._extract_thumbnail_from_entry(entry)

        # Limpiar description
        raw_description = getattr(entry, "description", None)
        clean_description = (
            self._strip_html_tags(raw_description) if raw_description else None
        )

        return ArticleData(
            title=getattr(entry, "title", "Sin título"),
            url=getattr(entry, "link", ""),
            description=clean_description,
            content=content,
            summary=getattr(entry, "summary", getattr(entry, "description", None)),
            author=getattr(entry, "author", None),
            published_at=published_at,
            guid=getattr(entry, "id", getattr(entry, "guid", None)),
            tags=categories,
            category=categories[0] if categories else None,
            thumbnail_url=thumbnail_url,
        )

    def _strip_html_tags(self, html_text: Optional[str]) -> Optional[str]:
        """Limpia HTML tags de texto."""
        if not html_text:
            return None

        # Remover tags HTML
        text = re.sub(r"<[^>]+>", "", html_text)
        # Decodificar entidades HTML
        text = text.replace("&nbsp;", " ")
        text = text.replace("&lt;", "<")
        text = text.replace("&gt;", ">")
        text = text.replace("&amp;", "&")
        text = text.replace("&quot;", '"')
        text = text.replace("&#39;", "'")
        # Limpiar espacios
        text = re.sub(r"\s+", " ", text)
        return text.strip() if text else None

    def _extract_thumbnail_from_entry(self, entry) -> Optional[str]:
        """Extrae thumbnail URL de entrada feedparser."""
        try:
            # 1. Media RSS thumbnail
            if hasattr(entry, "media_thumbnail") and entry.media_thumbnail:
                if (
                    isinstance(entry.media_thumbnail, list)
                    and len(entry.media_thumbnail) > 0
                ):
                    thumbnail = entry.media_thumbnail[0]
                    if isinstance(thumbnail, dict) and "url" in thumbnail:
                        return thumbnail["url"]

            # 2. Enclosures de tipo imagen
            if hasattr(entry, "enclosures") and entry.enclosures:
                for enclosure in entry.enclosures:
                    if isinstance(enclosure, dict):
                        enc_type = enclosure.get("type", "")
                        if enc_type.startswith("image/"):
                            url = enclosure.get("href") or enclosure.get("url")
                            if url:
                                return url

            # 3. Media content de tipo imagen
            if hasattr(entry, "media_content") and entry.media_content:
                for media in entry.media_content:
                    if isinstance(media, dict):
                        medium = media.get("medium")
                        media_type = media.get("type", "")
                        if medium == "image" or media_type.startswith("image/"):
                            url = media.get("url")
                            if url:
                                return url

            # 4. Parsear img tags del summary/description
            if hasattr(entry, "summary_detail") and entry.summary_detail:
                html = entry.summary_detail.get("value", "")
                if html:
                    img_match = re.search(r'<img[^>]+src=["\']([^"\' >]+)["\']', html)
                    if img_match:
                        return img_match.group(1)

            if hasattr(entry, "description"):
                html = entry.description
                if html and isinstance(html, str):
                    img_match = re.search(r'<img[^>]+src=["\']([^"\' >]+)["\']', html)
                    if img_match:
                        return img_match.group(1)

            return None

        except Exception as e:
            if self._logger:
                self._logger.debug("Error extrayendo thumbnail", error=str(e))
            return None

    async def _apply_rate_limit_for_source(self, source: Source) -> None:
        """Aplicar rate limiting por dominio del Source."""
        try:
            domain = urlparse(source.url.value).netloc

            if domain in self._domain_last_request:
                time_since_last = (
                    datetime.now(timezone.utc) - self._domain_last_request[domain]
                )
                if time_since_last.total_seconds() < self.rate_limit_delay:
                    sleep_time = self.rate_limit_delay - time_since_last.total_seconds()
                    await asyncio.sleep(sleep_time)

            self._domain_last_request[domain] = datetime.now(timezone.utc)

        except Exception as e:
            if self._logger:
                self._logger.warning(
                    "Error aplicando rate limit",
                    source_id=source.id.value,
                    error=str(e),
                )

    async def _apply_rate_limit_for_url(self, source_url: SourceUrl) -> None:
        """Aplicar rate limiting por dominio desde SourceUrl."""
        try:
            domain = urlparse(source_url.value).netloc

            if domain in self._domain_last_request:
                time_since_last = (
                    datetime.now(timezone.utc) - self._domain_last_request[domain]
                )
                if time_since_last.total_seconds() < self.rate_limit_delay:
                    sleep_time = self.rate_limit_delay - time_since_last.total_seconds()
                    await asyncio.sleep(sleep_time)

            self._domain_last_request[domain] = datetime.now(timezone.utc)

        except Exception as e:
            if self._logger:
                self._logger.warning(
                    "Error aplicando rate limit", url=source_url.value, error=str(e)
                )

    def get_fetcher_statistics(self) -> dict:
        """Obtiene estadísticas del fetcher RSS."""
        total = self._total_fetches
        success_rate = self._successful_fetches / total if total > 0 else 0.0

        return {
            "total_fetches": self._total_fetches,
            "successful_fetches": self._successful_fetches,
            "failed_fetches": self._failed_fetches,
            "success_rate": round(success_rate, 4),
            "domains_tracked": len(self._domain_last_request),
            "max_concurrent": self.max_concurrent,
            "timeout": self.timeout,
            "rate_limit_delay": self.rate_limit_delay,
        }

    def reset_fetcher_statistics(self) -> None:
        """Resetea estadísticas del fetcher RSS."""
        self._total_fetches = 0
        self._successful_fetches = 0
        self._failed_fetches = 0
