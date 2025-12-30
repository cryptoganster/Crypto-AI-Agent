"""Factory moderno para Scraping aggregate con configuraciones avanzadas."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

from src.rss.feed.domain.aggregates import Source
from src.rss.feed.domain.value_objects import SourceId
from src.rss.feed.domain.value_objects.configuration import SourceConfiguration
from src.scraping.domain.aggregates import Scraping
from src.scraping.domain.events.started import ScrapingStarted
from src.scraping.domain.interfaces.factories import IScrapingFactory
from src.scraping.domain.value_objects import ScrapingConfig


class ValidationResult:
    """Resultado de validación con errores y warnings."""

    def __init__(
        self,
        is_valid: bool,
        error_messages: Tuple[str, ...] = (),
        warnings: Tuple[str, ...] = (),
    ):
        self.is_valid = is_valid
        self.error_messages = error_messages
        self.warnings = warnings


class ScrapingFactory(IScrapingFactory):
    """
    Factory moderno para Scraping aggregate.

    Proporciona capacidades avanzadas de configuración y validación:
    - Validaciones de configuración de scraping
    - Configuraciones optimizadas por tipo de fuente
    - Detección de configuraciones problemáticas
    - Creación desde fuentes existentes con inteligencia
    - Configuraciones de retry y timeout adaptativos

    Se integra con el Scraping aggregate preservando eventos de dominio.
    """

    def __init__(self):
        """Inicializa factory con configuraciones por defecto."""
        self._default_configurations = self._initialize_default_configurations()

    def create_for_source(
        self,
        source: Source,
        config: Optional[ScrapingConfig] = None,
        scraping_id: Optional[str] = None,
    ) -> Scraping:
        """
        Crea Scraping optimizada para una Source específica.

        Args:
            source: Source aggregate para la cual crear la sesión
            config: Configuración específica (usa inteligente si None)
            scraping_id: ID específico (genera uno si None)

        Returns:
            Nueva instancia de Scraping con configuración optimizada

        Raises:
            ValueError: Si los datos no pasan validaciones de dominio
        """
        # Validar source
        if not source.is_ready_for_basic_operations():
            raise ValueError(
                f"Source {source.id} no está lista para operaciones de scraping"
            )

        # Obtener configuración optimizada
        if config is None:
            config = self._derive_optimal_config_for_source(source)

        # Validar configuración
        validation = self.validate_scraping_config(config)
        if not validation.is_valid:
            error_msg = "; ".join(validation.error_messages)
            raise ValueError(f"Configuración inválida para Scraping: {error_msg}")

        # Convertir a SourceConfiguration
        source_configuration = self._convert_to_source_configuration(config)

        # Generar ID si no se proporciona
        session_id = scraping_id or str(uuid4())

        # Crear Scraping usando constructor directo
        scraping = Scraping(
            source_id=source.id,
            configuration=source_configuration,
            scraping_id=session_id,
            sources_to_scrape=[source.id],
            config=config,
        )

        # Emitir evento de inicio (responsabilidad de factory)
        event = ScrapingStarted(
            aggregate_id=session_id,
            source_id=str(source.id),
            scraping_id=session_id,
            sources_count=1,
            max_concurrent=config.max_concurrent_scrapes,
            timeout_seconds=config.timeout_seconds,
            started_at=datetime.now(timezone.utc),
        )
        scraping._add_domain_event(event)

        return scraping

    def reconstruct_from_persistence(
        self,
        sources_to_scrape: List[SourceId],
        scraping_id: str,
        max_concurrent_scrapes: int,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
        started_at: Optional[datetime] = None,
        completed_at: Optional[datetime] = None,
        status: Optional[str] = None,
        error_details: Optional[dict] = None,
        scraping_results: Optional[dict] = None,
        **kwargs,
    ) -> Scraping:
        """Reconstruye Scraping desde datos de persistencia."""

        # Crear Scraping usando constructor directo para evitar validaciones
        scraping = Scraping.__new__(Scraping)

        # Propiedades básicas
        scraping._sources_to_scrape = sources_to_scrape
        scraping._scraping_id = scraping_id
        scraping._max_concurrent_scrapes = max_concurrent_scrapes

        # Timestamps
        scraping._created_at = created_at or datetime.now(timezone.utc)
        scraping._updated_at = updated_at or datetime.now(timezone.utc)
        scraping._started_at = started_at
        scraping._completed_at = completed_at

        # Estado interno
        if status:
            from src.scraping.domain.value_objects.status import ScrapingStatus

            scraping._status = ScrapingStatus.from_string(status)
        else:
            from src.scraping.domain.value_objects.status import ScrapingStatus

            scraping._status = ScrapingStatus.CREATED

        # Datos adicionales
        scraping._error_details = error_details or {}
        scraping._scraping_results = scraping_results or {}

        # Inicializar listas de eventos vacías (no queremos eventos en reconstrucción)
        scraping._uncommitted_events = []

        # Inicializar scraping manager si no existe
        if not hasattr(scraping, "_scraping_manager"):
            from src.scraping.domain.entities.scraping_manager import ScrapingManager

            scraping._scraping_manager = ScrapingManager(
                max_concurrent_scrapes=max_concurrent_scrapes
            )

        return scraping

    def create_multi_source(
        self,
        sources: List[SourceId],
        config: Optional[ScrapingConfig] = None,
        scraping_id: Optional[str] = None,
        # Opciones de procesamiento (Application Layer → Domain Event)
        quality_threshold: Optional[float] = None,
        enable_quality_filter: bool = True,
        enable_deduplication: bool = True,
        force_refresh: bool = False,
        max_items_per_source: Optional[int] = None,
        session_name: Optional[str] = None,
        triggered_by: str = "manual",
    ) -> Scraping:
        """
        Crea Scraping para múltiples sources.

        Args:
            sources: Lista de source IDs a procesar
            config: Configuración técnica de la sesión
            scraping_id: ID opcional del scraping
            quality_threshold: Umbral de calidad para filtrar artículos
            enable_quality_filter: Si aplicar filtro de calidad
            enable_deduplication: Si detectar y filtrar duplicados
            force_refresh: Si forzar re-scraping de artículos existentes
            max_items_per_source: Límite de artículos por source
            session_name: Nombre descriptivo de la sesión
            triggered_by: Quién/qué inició el scraping

        Returns:
            Nueva instancia de Scraping configurada para multi-source

        Raises:
            ValueError: Si la lista de sources está vacía
        """
        if not sources:
            raise ValueError("La lista de sources no puede estar vacía")

        # Usar el primer source como source_id principal (compatibilidad)
        primary_source = sources[0]

        # Crear configuración por defecto si no se proporciona
        session_config = config or ScrapingConfig()

        # Validar configuración
        validation = self.validate_scraping_config(session_config)
        if not validation.is_valid:
            error_msg = "; ".join(validation.error_messages)
            raise ValueError(f"Configuración inválida: {error_msg}")

        # Crear configuración por defecto para compatibilidad
        default_source_config = SourceConfiguration()

        # Generar ID si no se proporciona
        session_id = scraping_id or str(uuid4())

        # Crear instancia usando constructor directo
        scraping = Scraping(
            source_id=primary_source,
            configuration=default_source_config,
            scraping_id=session_id,
            sources_to_scrape=sources,
            config=session_config,
        )

        # Emitir evento ScrapingStarted con todas las opciones
        # El evento transporta las opciones al ScrapingPipeline
        event = ScrapingStarted(
            aggregate_id=session_id,
            source_id=str(primary_source),
            scraping_id=session_id,
            sources_count=len(sources),
            source_ids=tuple(str(s) for s in sources),
            max_concurrent=session_config.max_concurrent_scrapes,
            timeout_seconds=session_config.timeout_seconds,
            # Opciones de procesamiento
            quality_threshold=quality_threshold,
            enable_quality_filter=enable_quality_filter,
            enable_deduplication=enable_deduplication,
            force_refresh=force_refresh,
            max_items_per_source=max_items_per_source,
            session_name=session_name,
            triggered_by=triggered_by,
            started_at=datetime.now(timezone.utc),
        )
        scraping._add_domain_event(event)

        return scraping

    def create_batch_session(
        self,
        sources: List[Source],
        config: Optional[ScrapingConfig] = None,
        session_name: Optional[str] = None,
    ) -> List[Scraping]:
        """
        Crea múltiples Scrapings para procesamiento en lote.

        Args:
            sources: Lista de Sources para procesar
            config: Configuración base (se optimiza por source)
            session_name: Nombre descriptivo para el lote

        Returns:
            Lista de Scrapings configuradas para cada source

        Raises:
            ValueError: Si alguna source no es válida
        """
        if not sources:
            raise ValueError("Lista de sources no puede estar vacía")

        sessions = []
        for i, source in enumerate(sources):
            # Crear configuración específica para cada source
            source_config = config or self._derive_optimal_config_for_source(source)

            # Añadir identificador de lote
            scraping_id = f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{i+1:03d}"

            try:
                session = self.create_for_source(
                    source=source,
                    config=source_config,
                    scraping_id=scraping_id,
                )
                sessions.append(session)
            except ValueError as e:
                # Log error pero continúa con las demás sources
                print(f"Error creando sesión para source {source.id}: {e}")
                continue

        if not sessions:
            raise ValueError("No se pudo crear ninguna sesión válida")

        return sessions

    def validate_scraping_config(self, config: ScrapingConfig) -> ValidationResult:
        """
        Valida configuración de Scraping con reglas de dominio.

        Args:
            config: Configuración a validar

        Returns:
            Resultado de validación con errores y warnings detallados
        """
        errors = []
        warnings = []

        # Validar timeout
        if config.timeout_seconds <= 0:
            errors.append("timeout_seconds debe ser mayor a 0")
        elif config.timeout_seconds < 5:
            warnings.append("Timeout muy bajo podría causar fallos prematuros")
        elif config.timeout_seconds > 300:  # 5 minutos
            warnings.append("Timeout muy alto podría bloquear el sistema")

        # Validar max_articles
        if config.max_articles is not None:
            if config.max_articles <= 0:
                errors.append("max_articles debe ser mayor a 0")
            elif config.max_articles > 1000:
                warnings.append(
                    "Límite muy alto de artículos podría consumir mucha memoria"
                )

        # Validar retry configuration
        if config.retry_attempts < 0:
            errors.append("retry_attempts no puede ser negativo")
        elif config.retry_attempts > 10:
            warnings.append(
                "Muchos reintentos podrían causar bloqueos por rate limiting"
            )

        if config.retry_delay_seconds <= 0:
            errors.append("retry_delay_seconds debe ser mayor a 0")

        # Validar user agent
        if config.user_agent and len(config.user_agent) > 200:
            warnings.append("User agent muy largo podría ser rechazado por servidores")

        # Validar scraping type
        valid_scraping_types = {"scheduled", "manual", "retry", "bulk", "priority"}
        if config.scraping_type not in valid_scraping_types:
            errors.append(
                f"scraping_type debe ser uno de: {', '.join(valid_scraping_types)}"
            )

        # Validar max_concurrent_scrapes
        if config.max_concurrent_scrapes <= 0:
            errors.append("max_concurrent_scrapes debe ser mayor a 0")
        elif config.max_concurrent_scrapes > 50:
            warnings.append(
                "Demasiados scrapes concurrentes podrían sobrecargar el sistema"
            )

        return ValidationResult(
            is_valid=len(errors) == 0,
            error_messages=tuple(errors),
            warnings=tuple(warnings),
        )

    def _derive_optimal_config_for_source(self, source: Source) -> ScrapingConfig:
        """
        Deriva configuración óptima basada en características de la Source.

        Args:
            source: Source para la cual optimizar

        Returns:
            ScrapingConfig optimizada para la source específica
        """
        from dataclasses import replace

        # Optimizar basado en URL de la source
        url_str = str(source.url)
        domain = self._extract_domain(url_str)

        # Valores por defecto
        timeout_seconds = 30
        retry_delay_seconds = 5
        max_articles = None
        user_agent = self._get_optimal_user_agent(domain)
        validate_ssl = True
        follow_redirects = True

        # Configuraciones específicas por dominio
        if domain in self._get_slow_domains():
            timeout_seconds = 60
            retry_delay_seconds = 10
        elif domain in self._get_fast_domains():
            timeout_seconds = 15
            retry_delay_seconds = 2

        # Configuraciones específicas por tipo de contenido detectado
        if "blog" in url_str.lower():
            max_articles = 20  # Blogs suelen tener menos contenido
        elif "news" in url_str.lower():
            max_articles = 50  # News sites tienen más contenido
        elif "podcast" in url_str.lower():
            max_articles = 10  # Podcasts tienen episodios menos frecuentes

        # Configuraciones de seguridad
        if domain in self._get_insecure_domains():
            validate_ssl = False
            follow_redirects = False

        # Crear configuración inmutable con todos los valores
        return ScrapingConfig(
            timeout_seconds=timeout_seconds,
            retry_delay_seconds=retry_delay_seconds,
            max_articles=max_articles,
            user_agent=user_agent,
            validate_ssl=validate_ssl,
            follow_redirects=follow_redirects,
        )

    def _convert_to_source_configuration(
        self, config: ScrapingConfig
    ) -> SourceConfiguration:
        """Convierte ScrapingConfig a SourceConfiguration."""
        # Solo usar campos que existen en SourceConfiguration
        # Usar defaults si los valores son None
        return SourceConfiguration(
            fetch_interval_minutes=30,  # Default interval
            timeout_seconds=config.timeout_seconds,
            max_articles_per_fetch=(
                config.max_articles if config.max_articles is not None else 50
            ),
            retry_attempts=config.retry_attempts,
            # custom_headers se puede usar para user_agent si es necesario
            custom_headers=(
                {"User-Agent": config.user_agent} if config.user_agent else None
            ),
            max_concurrent_fetches=config.max_concurrent_scrapes,
        )

    def _initialize_default_configurations(self) -> Dict[str, ScrapingConfig]:
        """Inicializa configuraciones por defecto para diferentes escenarios."""
        return {
            "fast": ScrapingConfig(
                timeout_seconds=15,
                retry_attempts=2,
                retry_delay_seconds=2,
                scraping_type="scheduled",
            ),
            "standard": ScrapingConfig(
                timeout_seconds=30,
                retry_attempts=3,
                retry_delay_seconds=5,
                scraping_type="scheduled",
            ),
            "slow": ScrapingConfig(
                timeout_seconds=60,
                retry_attempts=5,
                retry_delay_seconds=10,
                scraping_type="scheduled",
            ),
            "bulk": ScrapingConfig(
                timeout_seconds=45,
                retry_attempts=2,
                retry_delay_seconds=3,
                scraping_type="bulk",
                max_articles=100,
            ),
            "priority": ScrapingConfig(
                timeout_seconds=20,
                retry_attempts=5,
                retry_delay_seconds=2,
                scraping_type="priority",
            ),
        }

    def _extract_domain(self, url: str) -> str:
        """Extrae dominio de una URL."""
        try:
            from urllib.parse import urlparse

            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            if domain.startswith("www."):
                domain = domain[4:]
            return domain
        except Exception:
            return "unknown"

    def _get_slow_domains(self) -> set:
        """Retorna dominios conocidos por ser lentos."""
        return {
            "government.gov",
            "academic.edu",
            "oldsite.org",
            "legacy.com",
        }

    def _get_fast_domains(self) -> set:
        """Retorna dominios conocidos por ser rápidos."""
        return {
            "github.com",
            "medium.com",
            "dev.to",
            "stackoverflow.com",
        }

    def _get_insecure_domains(self) -> set:
        """Retorna dominios con problemas de SSL conocidos."""
        return {
            "insecure.com",
            "oldssl.org",
        }

    def _get_optimal_user_agent(self, domain: str) -> str:
        """Retorna User-Agent óptimo para el dominio."""
        # Algunos sitios requieren User-Agents específicos
        domain_user_agents = {
            "reddit.com": "FeedsAI/1.0 (Compatible with Reddit RSS)",
            "twitter.com": "FeedsAI/1.0 (RSS Reader)",
            "github.com": "FeedsAI/1.0 (GitHub RSS Crawler)",
        }

        return domain_user_agents.get(domain, "FeedsAI/1.0 (RSS Aggregator)")

    def get_configuration_preset(self, preset_name: str) -> ScrapingConfig:
        """
        Obtiene configuración predefinida por nombre.

        Args:
            preset_name: Nombre del preset (fast, standard, slow, bulk, priority)

        Returns:
            ScrapingConfig predefinida

        Raises:
            ValueError: Si el preset no existe
        """
        if preset_name not in self._default_configurations:
            available = ", ".join(self._default_configurations.keys())
            raise ValueError(
                f"Preset '{preset_name}' no existe. Disponibles: {available}"
            )

        return self._default_configurations[preset_name]

    def create_priority_session(
        self,
        source: Source,
        priority_level: str = "high",
        scraping_id: Optional[str] = None,
    ) -> Scraping:
        """
        Crea sesión de scraping con prioridad específica.

        Args:
            source: Source para scraping prioritario
            priority_level: Nivel de prioridad (high, medium, low)
            scraping_id: ID específico (opcional)

        Returns:
            Scraping configurada para prioridad específica
        """
        priority_configs = {
            "high": self.get_configuration_preset("priority"),
            "medium": self.get_configuration_preset("standard"),
            "low": self.get_configuration_preset("slow"),
        }

        if priority_level not in priority_configs:
            raise ValueError(
                f"priority_level debe ser: {', '.join(priority_configs.keys())}"
            )

        config = priority_configs[priority_level]
        config.scraping_type = f"priority_{priority_level}"

        return self.create_for_source(
            source=source,
            config=config,
            scraping_id=scraping_id,
        )
