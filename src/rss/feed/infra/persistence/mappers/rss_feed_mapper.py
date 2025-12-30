"""Source Mapper - Convierte entre Source aggregate y SourceModel."""

import json
from datetime import datetime, timezone
from typing import Optional

from loguru import logger

from src.rss.feed.domain.aggregates import Source
from src.rss.feed.domain.value_objects.configuration import SourceConfiguration
from src.rss.feed.domain.value_objects.description import SourceDescription
from src.rss.feed.domain.value_objects.name import SourceName
from src.rss.feed.domain.value_objects.rss_feed_id import RssFeedId, SourceId
from src.rss.feed.domain.value_objects.rss_feed_url import RssFeedUrl, SourceUrl
from src.rss.feed.domain.value_objects.status import SourceStatus
from src.rss.feed.infra.persistence.models import SourceModel
from src.shared.domain.value_objects import ScrapingConfiguration, TagCollection


class SourceMapper:
    """
    Mapper para convertir entre Source aggregate y SourceModel.

    Implementa el patrón Mapper de Infrastructure Layer,
    manteniendo separación entre domain y persistence.
    """

    @staticmethod
    def _scraping_config_to_dict(config: ScrapingConfiguration) -> dict:
        """
        Serializa ScrapingConfiguration a diccionario para JSONB.

        Args:
            config: ScrapingConfiguration del dominio

        Returns:
            Dict para persistencia en campo JSONB
        """
        return {
            "content_selectors": list(config.content_selectors),
            "excluded_selectors": list(config.excluded_selectors),
            "excluded_texts": list(config.excluded_texts),
            "excluded_text_patterns": list(config.excluded_text_patterns),
            "fallback_selectors": list(config.fallback_selectors),
            "wait_timeout_ms": config.wait_timeout_ms,
            "wait_strategy": config.wait_strategy,
            "scroll_needed": config.scroll_needed,
            "selector_timeout_ms": config.selector_timeout_ms,
        }

    @staticmethod
    def _scraping_config_from_dict(data: dict) -> ScrapingConfiguration:
        """
        Deserializa ScrapingConfiguration desde diccionario JSONB.

        Args:
            data: Dict desde campo JSONB de persistencia

        Returns:
            ScrapingConfiguration reconstruida
        """
        return ScrapingConfiguration(
            content_selectors=tuple(data["content_selectors"]),
            excluded_selectors=tuple(data.get("excluded_selectors", [])),
            excluded_texts=tuple(data.get("excluded_texts", [])),
            excluded_text_patterns=tuple(data.get("excluded_text_patterns", [])),
            fallback_selectors=tuple(
                data.get(
                    "fallback_selectors",
                    [
                        "article",
                        "main",
                        "[role='main']",
                        ".article-content",
                        ".post-content",
                        ".entry-content",
                        ".article-body",
                        ".post-body",
                        "#article",
                        "#content",
                        ".content",
                        "#main-content",
                        ".main-content",
                        "body",
                    ],
                )
            ),
            wait_timeout_ms=data["wait_timeout_ms"],
            wait_strategy=data["wait_strategy"],
            scroll_needed=data["scroll_needed"],
            selector_timeout_ms=data.get("selector_timeout_ms", 5000),
        )

    @staticmethod
    def to_domain(model: SourceModel) -> Source:
        """
        Convierte SourceModel a Source aggregate.

        Args:
            model: Modelo de persistencia

        Returns:
            Source aggregate reconstruido

        Raises:
            ValueError: Si los datos del modelo son inválidos
        """
        if not model:
            raise ValueError("SourceModel no puede ser None")

        try:
            # Crear VOs básicos
            url = SourceUrl(model.url)
            name = SourceName(model.name)
            description = (
                SourceDescription(model.description) if model.description else None
            )
            source_id = SourceId(str(model.id))

            # Configuración
            configuration = SourceConfiguration(
                fetch_interval_minutes=model.fetch_interval_minutes,  # type: ignore
                timeout_seconds=model.timeout_seconds,  # type: ignore
                retry_attempts=model.max_retries,  # type: ignore
                custom_headers=model.custom_headers or {},  # type: ignore
            )

            # Deserializar scraping_config JSONB si existe
            scraping_config = None
            if model.scraping_config:  # type: ignore
                try:
                    logger.debug(
                        f"[SourceMapper] Deserializando scraping_config | Type: {type(model.scraping_config)} | Content: {model.scraping_config}"
                    )

                    config_dict = model.scraping_config if isinstance(model.scraping_config, dict) else json.loads(model.scraping_config)  # type: ignore
                    scraping_config = SourceMapper._scraping_config_from_dict(
                        config_dict
                    )

                    logger.info(
                        f"[SourceMapper] ✅ scraping_config deserializado | Selectors: {scraping_config.content_selectors}"
                    )
                except Exception as e:
                    logger.error(
                        f"[SourceMapper] ❌ Error deserializando scraping_config | Error: {type(e).__name__}: {str(e)} | Data: {model.scraping_config}"
                    )
                    scraping_config = None
            else:
                logger.debug(
                    f"[SourceMapper] No scraping_config en DB para source: {model.name}"
                )

            # Crear Source usando constructor normal
            source = Source(
                url=url,
                name=name,
                description=description,
                source_id=source_id,
                configuration=configuration,
                scraping_config=scraping_config,
            )

            # Activar source si está activo en DB
            if model.status == "active":  # type: ignore
                source.activate()

            # Limpiar eventos generados por el constructor y activate()
            # (no queremos eventos al reconstruir desde DB)
            source._domain_events = []
            source._uncommitted_events = []

            return source

        except Exception as e:
            raise ValueError(
                f"Error convirtiendo SourceModel a Source: {str(e)}"
            ) from e

    @staticmethod
    def to_model(source: Source) -> SourceModel:
        """
        Convierte Source aggregate a SourceModel.

        Args:
            source: Source aggregate

        Returns:
            SourceModel para persistencia

        Raises:
            ValueError: Si el Source es inválido
        """
        if not source:
            raise ValueError("Source no puede ser None")

        try:
            # Extraer dominio de la URL
            domain = SourceModel._extract_domain(str(source.url))

            return SourceModel(
                # Identity - usar 'id' (nueva convención)
                id=source.id.value,
                # Core data
                name=str(source.name),
                url=str(source.url),
                domain=domain,
                description=str(source.description) if source.description else None,
                # Status
                status=str(source.status),
                # Configuration
                fetch_interval_minutes=source.configuration.fetch_interval_minutes,
                timeout_seconds=source.configuration.timeout_seconds,
                max_retries=source.configuration.retry_attempts,
                user_agent="feeds-ai/1.0",  # Valor por defecto ya que no existe en SourceConfiguration
                follow_redirects=True,  # Valor por defecto
                verify_ssl=True,  # Valor por defecto
                custom_headers=source.configuration.custom_headers or {},
                # Timestamps
                created_at=source.created_at,
                updated_at=source.updated_at,
                version=int(source.version),
                # Metrics - inicializados en 0 para nuevas sources
                total_fetch_attempts=0,
                successful_fetches=0,
                failed_fetches=0,
                last_fetch_at=None,
                last_successful_fetch_at=None,
                average_response_time_ms=0.0,
                consecutive_failures=0,
                last_error_message=None,
                last_error_at=None,
                total_articles_discovered=0,
                last_articles_count=0,
                # Scraping configuration (usar getattr para compatibilidad con objetos legacy)
                scraping_config=(
                    SourceMapper._scraping_config_to_dict(
                        getattr(source, "_scraping_config", None)
                    )
                    if getattr(source, "_scraping_config", None)
                    else None
                ),
            )

        except Exception as e:
            raise ValueError(
                f"Error convirtiendo Source a SourceModel: {str(e)}"
            ) from e

    @staticmethod
    def update_model_from_domain(model: SourceModel, source: Source) -> None:
        """
        Actualiza SourceModel existente con datos del Source aggregate.

        Útil para operaciones de actualización que preservan ciertos campos
        del modelo (como timestamps automáticos y métricas).

        Args:
            model: Modelo existente a actualizar
            source: Source aggregate con datos nuevos
        """
        if not model:
            raise ValueError("SourceModel no puede ser None")
        if not source:
            raise ValueError("Source no puede ser None")

        try:
            # Actualizar campos básicos usando setattr
            setattr(model, "name", str(source.name))
            setattr(model, "url", str(source.url))
            setattr(model, "domain", SourceModel._extract_domain(str(source.url)))
            setattr(
                model,
                "description",
                str(source.description) if source.description else None,
            )

            # Estado
            setattr(model, "status", str(source.status))

            # Configuración fetch
            setattr(
                model,
                "fetch_interval_minutes",
                source.configuration.fetch_interval_minutes,
            )
            setattr(model, "timeout_seconds", source.configuration.timeout_seconds)
            setattr(model, "max_retries", source.configuration.retry_attempts)
            setattr(
                model, "user_agent", "feeds-ai/1.0"
            )  # Valor por defecto ya que no existe en SourceConfiguration
            setattr(model, "follow_redirects", True)  # Valor por defecto
            setattr(model, "verify_ssl", True)  # Valor por defecto
            setattr(model, "custom_headers", source.configuration.custom_headers or {})

            # Versión
            setattr(model, "version", int(source.version))

            # Actualizar scraping_config SOLO si existe en el source (no sobrescribir con None)
            if source.scraping_config is not None:
                setattr(
                    model,
                    "scraping_config",
                    SourceMapper._scraping_config_to_dict(source.scraping_config),
                )
            else:
                setattr(model, "scraping_config", None)

            # Nota: Las métricas (total_fetch_attempts, etc.) se mantienen del modelo
            # ya que son gestionadas por los repositorios y servicios de fetching

            # updated_at se actualizará automáticamente por SQLAlchemy onupdate

        except Exception as e:
            raise ValueError(
                f"Error actualizando SourceModel desde Source: {str(e)}"
            ) from e
