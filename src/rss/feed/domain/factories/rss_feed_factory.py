"""Factory moderno para Source aggregate con validaciones avanzadas."""

from typing import Any, Dict, List, Optional, Set, Tuple
from urllib.parse import urlparse

from src.rss.feed.domain.aggregates import Source
from src.rss.feed.domain.interfaces.factories.rss_feed_factory import ISourceFactory
from src.rss.feed.domain.value_objects.configuration import SourceConfiguration
from src.rss.feed.domain.value_objects.description import SourceDescription
from src.rss.feed.domain.value_objects.name import SourceName
from src.rss.feed.domain.value_objects.rss_feed_id import RssFeedId
from src.rss.feed.domain.value_objects.rss_feed_url import RssFeedUrl


class FeedMetadata:
    """DTO para metadatos de feed RSS."""

    def __init__(
        self,
        title: Optional[str] = None,
        description: Optional[str] = None,
        language: Optional[str] = None,
        category: Optional[str] = None,
        last_build_date: Optional[str] = None,
        generator: Optional[str] = None,
        webmaster: Optional[str] = None,
    ):
        self.title = title
        self.description = description
        self.language = language
        self.category = category
        self.last_build_date = last_build_date
        self.generator = generator
        self.webmaster = webmaster


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


class RssFeedFactory(ISourceFactory):
    """
    Factory moderno para Source aggregate.

    Migra funcionalidad valiosa del RssSourceFactory anterior:
    - Validaciones avanzadas de URLs y dominios
    - Derivación inteligente de nombres desde URLs
    - Blacklist de dominios bloqueados
    - Creación desde metadatos de feeds RSS
    - Detección de configuraciones problemáticas

    Se integra con el nuevo Source aggregate preservando eventos de dominio.
    """

    def __init__(self):
        """Inicializa factory con configuraciones por defecto."""
        self._blocked_domains = self._initialize_blocked_domains()
        self._suspicious_patterns = self._initialize_suspicious_patterns()

    def create_source(
        self,
        url: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        configuration: Optional[SourceConfiguration] = None,
        source_id: Optional[SourceId] = None,
    ) -> Source:
        """
        Crea nueva Source con validaciones y limpieza de dominio.

        Args:
            url: URL del feed RSS (string raw)
            name: Nombre opcional para la source
            description: Descripción opcional
            configuration: Configuración específica (usa default si None)
            source_id: ID específico (genera uno si None)

        Returns:
            Nueva instancia de Source con eventos de dominio

        Raises:
            ValueError: Si los datos no pasan validaciones de dominio
        """
        # Validar datos de entrada
        validation = self.validate_source_creation_data(url, name, description)
        if not validation.is_valid:
            error_msg = "; ".join(validation.error_messages)
            raise ValueError(f"Datos inválidos para creación de source: {error_msg}")

        # Crear Value Objects con limpieza
        source_url = SourceUrl(self._clean_url(url))
        source_name = SourceName(name or self._derive_name_from_url(url))
        source_description = SourceDescription(
            description or self._derive_description_from_url(url)
        )

        # Generar ID si no se proporciona
        final_source_id = source_id or SourceId.generate()

        # Crear Source usando constructor simple
        source = Source(
            url=source_url,
            name=source_name,
            description=source_description,
            configuration=configuration or SourceConfiguration.default(),
            source_id=final_source_id,
        )

        # Emitir evento de creación (responsabilidad de la Factory)
        from src.rss.feed.domain.events import SourceCreated

        source._add_domain_event(
            SourceCreated(
                source_id=str(final_source_id),
                name=str(source_name),
                url=str(source_url),
            )
        )

        return source

    def create_from_feed_metadata(
        self,
        url: str,
        metadata: FeedMetadata,
        configuration: Optional[SourceConfiguration] = None,
    ) -> Source:
        """
        Crea Source desde metadatos de feed RSS con inteligencia de dominio.

        Args:
            url: URL del feed RSS
            metadata: Metadatos extraídos del feed RSS
            configuration: Configuración específica (opcional)

        Returns:
            Nueva instancia de Source con metadatos aplicados y eventos
        """
        # Usar metadatos para información más rica
        name = self._clean_feed_title(metadata.title) if metadata.title else None
        description = self._clean_feed_description(metadata.description)

        # Crear source base con metadatos
        source = self.create_source(
            url=url,
            name=name,
            description=description,
            configuration=configuration,
        )

        # Aplicar configuración inteligente basada en metadatos
        if metadata.language:
            enhanced_config = self._enhance_configuration_with_metadata(
                source.configuration, metadata
            )
            if enhanced_config != source.configuration:
                source.update_configuration(enhanced_config)

        return source

    def validate_source_creation_data(
        self,
        url: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> ValidationResult:
        """
        Valida datos para creación de source con reglas de dominio avanzadas.

        Args:
            url: URL del feed RSS a validar
            name: Nombre opcional a validar
            description: Descripción opcional a validar

        Returns:
            Resultado de validación con errores y warnings detallados
        """
        errors = []
        warnings = []

        # Validar URL con reglas específicas
        url_validation = self._validate_url(url)
        errors.extend(url_validation["errors"])
        warnings.extend(url_validation["warnings"])

        # Validar dominio específicamente
        domain_validation = self._validate_domain(url)
        errors.extend(domain_validation["errors"])
        warnings.extend(domain_validation["warnings"])

        # Validar nombre si se proporciona
        if name is not None:
            name_validation = self._validate_name(name)
            errors.extend(name_validation["errors"])
            warnings.extend(name_validation["warnings"])

        # Validar descripción si se proporciona
        if description is not None:
            desc_validation = self._validate_description(description)
            warnings.extend(desc_validation["warnings"])

        return ValidationResult(
            is_valid=len(errors) == 0,
            error_messages=tuple(errors),
            warnings=tuple(warnings),
        )

    def _validate_url(self, url: str) -> Dict[str, List[str]]:
        """Valida URL con reglas específicas de dominio."""
        errors = []
        warnings = []

        try:
            # Crear SourceUrl para validación inicial
            SourceUrl(url)
        except ValueError as e:
            errors.append(f"URL inválida: {str(e)}")
            return {"errors": errors, "warnings": warnings}

        try:
            parsed = urlparse(url)

            # Validaciones de protocolo
            if parsed.scheme == "http":
                warnings.append("Se recomienda HTTPS en lugar de HTTP")
            elif parsed.scheme not in ["http", "https"]:
                errors.append("Solo se soportan protocolos HTTP y HTTPS")

            # Validaciones de estructura
            if not parsed.path or parsed.path == "/":
                warnings.append("URL sin ruta específica podría no ser un feed RSS")

            # Validaciones de calidad
            if parsed.port and parsed.port not in [80, 443, 8080]:
                warnings.append(
                    f"Puerto no estándar ({parsed.port}) podría causar problemas"
                )

            # Detectar patrones sospechosos
            if any(pattern in url.lower() for pattern in self._suspicious_patterns):
                warnings.append("URL contiene patrones potencialmente problemáticos")

        except Exception:
            errors.append("URL no puede ser parseada correctamente")

        return {"errors": errors, "warnings": warnings}

    def _validate_domain(self, url: str) -> Dict[str, List[str]]:
        """Valida dominio con blacklist y reglas específicas."""
        errors = []
        warnings = []

        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()

            # Verificar dominio bloqueado
            if domain in self._blocked_domains:
                errors.append(f"Dominio bloqueado: {domain}")

            # Verificar dominios sospechosos
            if self._is_suspicious_domain(domain):
                warnings.append(f"Dominio {domain} podría ser temporal o no confiable")

            # Verificar TLD válido
            if not self._has_valid_tld(domain):
                warnings.append("TLD no estándar podría causar problemas")

        except Exception:
            errors.append("No se pudo validar el dominio")

        return {"errors": errors, "warnings": warnings}

    def _validate_name(self, name: str) -> Dict[str, List[str]]:
        """Valida nombre de la source."""
        errors = []
        warnings = []

        if not name.strip():
            errors.append("Nombre no puede estar vacío")
            return {"errors": errors, "warnings": warnings}

        name = name.strip()

        if len(name) > 100:
            errors.append("Nombre debe tener máximo 100 caracteres")
        elif len(name) < 3:
            warnings.append("Nombre muy corto, recomendado mínimo 3 caracteres")

        # Detectar nombres problemáticos
        if name.upper() == name:
            warnings.append(
                "Nombre en mayúsculas podría tener problemas de legibilidad"
            )

        return {"errors": errors, "warnings": warnings}

    def _validate_description(self, description: str) -> Dict[str, List[str]]:
        """Valida descripción de la source."""
        warnings = []

        if description and len(description) > 500:
            warnings.append("Descripción muy larga, recomendado máximo 500 caracteres")
        elif description and len(description) < 10:
            warnings.append("Descripción muy corta, poco informativa")

        return {"warnings": warnings}

    def _clean_url(self, url: str) -> str:
        """Limpia y normaliza la URL."""
        clean_url = url.strip()

        # Remover fragmentos innecesarios
        if "#" in clean_url:
            clean_url = clean_url.split("#")[0]

        return clean_url

    def _derive_name_from_url(self, url: str) -> str:
        """Deriva un nombre descriptivo desde la URL con inteligencia mejorada."""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()

            # Remover prefijos comunes
            if domain.startswith("www."):
                domain = domain[4:]
            if domain.startswith("feeds."):
                domain = domain[6:]
            if domain.startswith("rss."):
                domain = domain[4:]

            # Casos especiales para dominios conocidos
            domain_mappings = {
                "github.com": "GitHub",
                "stackoverflow.com": "Stack Overflow",
                "medium.com": "Medium",
                "dev.to": "DEV Community",
                "hackernews.com": "Hacker News",
            }

            if domain in domain_mappings:
                return domain_mappings[domain]

            # Derivación general
            if "." in domain:
                parts = domain.split(".")
                main_part = parts[0] if len(parts) > 1 else domain
                return main_part.replace("-", " ").replace("_", " ").title()

            return domain.replace("-", " ").replace("_", " ").title()

        except Exception:
            return "RSS Feed"

    def _derive_description_from_url(self, url: str) -> str:
        """Deriva una descripción básica desde la URL."""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()

            if "blog" in domain or "blog" in parsed.path:
                return f"Blog RSS feed from {domain}"
            elif "news" in domain or "news" in parsed.path:
                return f"News RSS feed from {domain}"
            elif "podcast" in domain or "podcast" in parsed.path:
                return f"Podcast RSS feed from {domain}"
            else:
                return f"RSS feed from {domain}"

        except Exception:
            return "RSS feed source"

    def _clean_feed_title(self, title: str) -> str:
        """Limpia título del feed RSS."""
        if not title:
            return title

        clean = title.strip()

        # Remover sufijos comunes de feeds
        suffixes_to_remove = [
            " RSS",
            " Feed",
            " RSS Feed",
            " - RSS",
            " | RSS",
            " Blog",
            " News",
            " Updates",
        ]

        for suffix in suffixes_to_remove:
            if clean.upper().endswith(suffix.upper()):
                clean = clean[: -len(suffix)].strip()

        return clean

    def _clean_feed_description(self, description: Optional[str]) -> Optional[str]:
        """Limpia descripción del feed RSS."""
        if not description:
            return description

        clean = description.strip()

        # Truncar si es muy larga
        if len(clean) > 400:
            clean = clean[:397] + "..."

        return clean

    def _enhance_configuration_with_metadata(
        self,
        base_config: SourceConfiguration,
        metadata: FeedMetadata,
    ) -> SourceConfiguration:
        """Mejora configuración basada en metadatos del feed."""
        # Por ahora retorna la configuración base
        # Se puede expandir para ajustar timeouts, user-agent, etc.
        # basado en el tipo de feed detectado
        return base_config

    def _initialize_blocked_domains(self) -> Set[str]:
        """Inicializa conjunto de dominios bloqueados."""
        return {
            "localhost",
            "127.0.0.1",
            "0.0.0.0",
            "example.com",
            "test.com",
            "invalid.invalid",
            "malware.com",
            "spam.com",
        }

    def _initialize_suspicious_patterns(self) -> List[str]:
        """Inicializa patrones sospechosos en URLs."""
        return [
            "bit.ly",
            "tinyurl",
            "shortened",
            "redirect",
            "proxy",
            "mirror",
        ]

    def _is_suspicious_domain(self, domain: str) -> bool:
        """Detecta dominios potencialmente sospechosos."""
        suspicious_indicators = [
            len(domain) > 50,  # Dominios muy largos
            domain.count("-") > 3,  # Muchos guiones
            domain.count(".") > 3,  # Muchos subdominios
            any(char.isdigit() for char in domain.replace(".", "")),  # Contiene números
        ]

        return sum(suspicious_indicators) >= 2

    def _has_valid_tld(self, domain: str) -> bool:
        """Verifica si el dominio tiene un TLD válido."""
        common_tlds = {
            "com",
            "org",
            "net",
            "edu",
            "gov",
            "mil",
            "int",
            "co",
            "io",
            "ai",
            "dev",
            "app",
            "blog",
            "news",
            "es",
            "mx",
            "ar",
            "cl",
            "pe",
            "co.uk",
            "com.mx",
        }

        parts = domain.split(".")
        if len(parts) < 2:
            return False

        tld = parts[-1]
        two_part_tld = ".".join(parts[-2:]) if len(parts) >= 2 else ""

        return tld in common_tlds or two_part_tld in common_tlds

    def reconstruct_from_persistence(
        self,
        source_id: SourceId,
        url: str,
        name: str,
        description: Optional[str] = None,
        configuration: Optional[SourceConfiguration] = None,
        status: Optional[str] = None,
        created_at: Optional[object] = None,
        updated_at: Optional[object] = None,
        last_fetch_at: Optional[object] = None,
        health_metrics: Optional[dict] = None,
        **kwargs,
    ) -> Source:
        """Reconstruye Source desde datos de persistencia sin emitir eventos."""
        from datetime import datetime, timezone

        from src.rss.feed.domain.value_objects import (
            SourceHealth,
            SourceIdentity,
            SourceMetadata,
        )
        from src.rss.feed.domain.value_objects.description import SourceDescription
        from src.rss.feed.domain.value_objects.name import SourceName
        from src.rss.feed.domain.value_objects.rss_feed_url import RssFeedUrl
        from src.rss.feed.domain.value_objects.status import SourceStatus
        from src.shared.domain.value_objects import TagCollection

        # Crear Source usando constructor directo para evitar validaciones
        source = Source.__new__(Source)

        # IMPORTANTE: Inicializar eventos PRIMERO (requerido por IAggregateRoot)
        source._domain_events = []
        source._uncommitted_events = []

        # Crear Value Objects compuestos
        source._identity = SourceIdentity.create(
            source_id=source_id,
            url=SourceUrl(url),
            created_at=created_at or datetime.now(timezone.utc),
            updated_at=updated_at or datetime.now(timezone.utc),
            version=kwargs.get("version", 0),
        )

        source._metadata = SourceMetadata.create(
            name=SourceName(name) if isinstance(name, str) else name,
            description=SourceDescription(description) if description else None,
            category=kwargs.get("category", None),
            tags=kwargs.get("tags", TagCollection(tags=frozenset())),
            source_type=kwargs.get("source_type", "rss"),
        )

        # Estado de salud
        health_status = (
            SourceStatus.from_string(status) if status else SourceStatus.inactive()
        )
        source._health = SourceHealth(
            status=health_status,
            metrics=None,  # Se cargan por separado si es necesario
        )

        # Configuración
        source._configuration = configuration or SourceConfiguration.default()
        source._scraping_config = kwargs.get("scraping_config", None)

        # Llamar super().__init__() para completar inicialización de IAggregateRoot
        super(Source, source).__init__()

        return source
