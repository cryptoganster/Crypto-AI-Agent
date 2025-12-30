"""RssFeedConfiguration Value Object - Configuración específica de fetch para fuentes RSS."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from src.shared.kernel import IValueObject


@dataclass(frozen=True)
class RssFeedConfiguration(IValueObject):
    """
    Value Object para configuración específica de fetch de un RssFeed.

    Encapsula todas las reglas de negocio relacionadas con:
    - Intervalos de fetch
    - Límites de artículos por fetch
    - Configuración de timeouts y reintentos
    - Headers HTTP customizados
    """

    fetch_interval_minutes: int = 60
    max_articles_per_fetch: int = 50
    timeout_seconds: int = 30
    retry_attempts: int = 3
    custom_headers: Optional[Dict[str, str]] = None
    max_concurrent_fetches: int = 5
    next_fetch_at: Optional[str] = None
    content_filters: Optional[Dict[str, Any]] = field(
        default_factory=lambda: {
            "keywords": [],
            "categories": [],
            "filter_mode": "inclusive",
        }
    )

    # Constantes de validación
    MIN_FETCH_INTERVAL = 5  # 5 minutos mínimo
    MAX_FETCH_INTERVAL = 1440  # 24 horas máximo
    MIN_ARTICLES_PER_FETCH = 1
    MAX_ARTICLES_PER_FETCH = 500
    MIN_TIMEOUT = 5  # 5 segundos mínimo
    MAX_TIMEOUT = 300  # 5 minutos máximo
    MIN_RETRY_ATTEMPTS = 0
    MAX_RETRY_ATTEMPTS = 10

    def __post_init__(self):
        """Valida la configuración al crearla."""
        self._validate_fetch_interval()
        self._validate_max_articles()
        self._validate_timeout()
        self._validate_retry_attempts()
        self._validate_custom_headers()

    def _validate_fetch_interval(self) -> None:
        """Valida el intervalo de fetch."""
        if not (
            self.MIN_FETCH_INTERVAL
            <= self.fetch_interval_minutes
            <= self.MAX_FETCH_INTERVAL
        ):
            raise ValueError(
                f"fetch_interval_minutes debe estar entre {self.MIN_FETCH_INTERVAL} y {self.MAX_FETCH_INTERVAL} minutos"
            )

    def _validate_max_articles(self) -> None:
        """Valida el límite máximo de artículos."""
        if not (
            self.MIN_ARTICLES_PER_FETCH
            <= self.max_articles_per_fetch
            <= self.MAX_ARTICLES_PER_FETCH
        ):
            raise ValueError(
                f"max_articles_per_fetch debe estar entre {self.MIN_ARTICLES_PER_FETCH} y {self.MAX_ARTICLES_PER_FETCH}"
            )

    def _validate_timeout(self) -> None:
        """Valida el timeout."""
        if not (self.MIN_TIMEOUT <= self.timeout_seconds <= self.MAX_TIMEOUT):
            raise ValueError(
                f"timeout_seconds debe estar entre {self.MIN_TIMEOUT} y {self.MAX_TIMEOUT} segundos"
            )

    def _validate_retry_attempts(self) -> None:
        """Valida los reintentos."""
        if not (
            self.MIN_RETRY_ATTEMPTS <= self.retry_attempts <= self.MAX_RETRY_ATTEMPTS
        ):
            raise ValueError(
                f"retry_attempts debe estar entre {self.MIN_RETRY_ATTEMPTS} y {self.MAX_RETRY_ATTEMPTS}"
            )

    def _validate_custom_headers(self) -> None:
        """Valida los headers customizados."""
        if self.custom_headers is None:
            return

        # Validar que sean strings no vacíos
        for key, value in self.custom_headers.items():
            if not isinstance(key, str) or not isinstance(value, str):
                raise ValueError("Todos los headers deben ser strings")
            if not key.strip() or not value.strip():
                raise ValueError("Los headers no pueden estar vacíos")

    @classmethod
    def default(cls) -> "RssFeedConfiguration":
        """Crea configuración por defecto."""
        return cls()

    @classmethod
    def fast_fetch(cls) -> "RssFeedConfiguration":
        """
        Crea configuración para fetch frecuente.

        Returns:
            RssFeedConfiguration optimizada para fetch rápido
        """
        return cls(
            fetch_interval_minutes=15,  # Cada 15 minutos
            max_articles_per_fetch=25,  # Límite reducido
            timeout_seconds=15,  # Timeout más rápido
            retry_attempts=2,  # Menos reintentos
        )

    @classmethod
    def slow_fetch(cls) -> "RssFeedConfiguration":
        """
        Crea configuración para fetch lento/robusto.

        Returns:
            RssFeedConfiguration optimizada para confiabilidad
        """
        return cls(
            fetch_interval_minutes=180,  # Cada 3 horas
            max_articles_per_fetch=100,  # Más artículos por batch
            timeout_seconds=60,  # Timeout más generoso
            retry_attempts=5,  # Más reintentos
        )

    @classmethod
    def high_volume(cls) -> "RssFeedConfiguration":
        """
        Crea configuración para fuentes de alto volumen.

        Returns:
            RssFeedConfiguration para fuentes con muchos artículos
        """
        return cls(
            fetch_interval_minutes=30,
            max_articles_per_fetch=200,  # Más artículos por fetch
            timeout_seconds=45,
            retry_attempts=3,
        )

    @classmethod
    def with_auth_headers(cls, api_key: str, **kwargs) -> "RssFeedConfiguration":
        """
        Crea configuración con headers de autenticación.

        Args:
            api_key: Clave API para autenticación
            **kwargs: Otros parámetros de configuración

        Returns:
            RssFeedConfiguration con headers de autenticación
        """
        headers = {"Authorization": f"Bearer {api_key}"}

        # Permitir headers adicionales
        if "custom_headers" in kwargs:
            existing_headers = kwargs.pop("custom_headers") or {}
            headers.update(existing_headers)

        return cls(custom_headers=headers, **kwargs)

    def is_frequent_fetch(self) -> bool:
        """
        Determina si es configuración de fetch frecuente.

        Returns:
            True si el intervalo es menor a 30 minutos
        """
        return self.fetch_interval_minutes < 30

    def is_high_volume(self) -> bool:
        """
        Determina si es configuración de alto volumen.

        Returns:
            True si permite más de 100 artículos por fetch
        """
        return self.max_articles_per_fetch > 100

    def has_authentication(self) -> bool:
        """
        Verifica si tiene headers de autenticación.

        Returns:
            True si tiene headers que indican autenticación
        """
        if not self.custom_headers:
            return False

        auth_headers = ["authorization", "x-api-key", "api-key"]
        header_keys = [key.lower() for key in self.custom_headers.keys()]

        return any(auth_header in header_keys for auth_header in auth_headers)

    def get_total_timeout_with_retries(self) -> int:
        """
        Calcula el tiempo total máximo considerando reintentos.

        Returns:
            Tiempo máximo total en segundos
        """
        return self.timeout_seconds * (self.retry_attempts + 1)

    def with_fetch_interval(self, minutes: int) -> "RssFeedConfiguration":
        """
        Crea nueva configuración con intervalo de fetch diferente.

        Args:
            minutes: Nuevo intervalo en minutos

        Returns:
            Nueva instancia de RssFeedConfiguration
        """
        return RssFeedConfiguration(
            fetch_interval_minutes=minutes,
            max_articles_per_fetch=self.max_articles_per_fetch,
            timeout_seconds=self.timeout_seconds,
            retry_attempts=self.retry_attempts,
            custom_headers=self.custom_headers,
        )

    def with_timeout(self, seconds: int) -> "RssFeedConfiguration":
        """
        Crea nueva configuración con timeout diferente.

        Args:
            seconds: Nuevo timeout en segundos

        Returns:
            Nueva instancia de RssFeedConfiguration
        """
        return RssFeedConfiguration(
            fetch_interval_minutes=self.fetch_interval_minutes,
            max_articles_per_fetch=self.max_articles_per_fetch,
            timeout_seconds=seconds,
            retry_attempts=self.retry_attempts,
            custom_headers=self.custom_headers,
        )

    def with_custom_headers(self, headers: Dict[str, str]) -> "RssFeedConfiguration":
        """
        Crea nueva configuración con headers customizados.

        Args:
            headers: Nuevos headers HTTP

        Returns:
            Nueva instancia de RssFeedConfiguration
        """
        return RssFeedConfiguration(
            fetch_interval_minutes=self.fetch_interval_minutes,
            max_articles_per_fetch=self.max_articles_per_fetch,
            timeout_seconds=self.timeout_seconds,
            retry_attempts=self.retry_attempts,
            custom_headers=headers,
        )

    def __str__(self) -> str:
        return f"RssFeedConfiguration(interval={self.fetch_interval_minutes}min, max_articles={self.max_articles_per_fetch})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, RssFeedConfiguration):
            return False
        return (
            self.fetch_interval_minutes == other.fetch_interval_minutes
            and self.max_articles_per_fetch == other.max_articles_per_fetch
            and self.timeout_seconds == other.timeout_seconds
            and self.retry_attempts == other.retry_attempts
            and self.custom_headers == other.custom_headers
        )

    def __hash__(self) -> int:
        # Convertir custom_headers a tupla inmutable para hash
        headers_tuple = (
            tuple(sorted(self.custom_headers.items())) if self.custom_headers else None
        )
        return hash(
            (
                self.fetch_interval_minutes,
                self.max_articles_per_fetch,
                self.timeout_seconds,
                self.retry_attempts,
                headers_tuple,
            )
        )


# Alias para compatibilidad hacia atrás
SourceConfiguration = RssFeedConfiguration
