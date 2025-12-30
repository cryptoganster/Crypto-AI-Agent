"""ScrapingConfig Value Object para configuración de sesiones de scraping."""

from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass(frozen=True)
class ScrapingConfig:
    """
    Value Object para configuración completa de sesiones de scraping.

    Encapsula toda la configuración de cómo se ejecutará una sesión de scraping,
    incluyendo límites de concurrencia, timeouts, opciones de retry, y configuración
    avanzada de HTTP.

    Attributes:
        max_concurrent_scrapes: Número máximo de scrapes concurrentes (1-50)
        timeout_seconds: Timeout general en segundos (5-300)
        timeout_config: Configuración de timeouts específicos por operación
        retry_failed: Si se deben reintentar sources fallidos
        max_articles: Límite máximo de artículos por scraping (opcional)
        retry_attempts: Número de reintentos en caso de fallo (0-10)
        retry_delay_seconds: Segundos de espera entre reintentos
        user_agent: User-Agent personalizado para requests HTTP
        follow_redirects: Si seguir redirects HTTP
        validate_ssl: Si validar certificados SSL
        scraping_type: Tipo de scraping (scheduled, manual, retry, bulk, priority)

    Example:
        >>> config = ScrapingConfig(
        ...     max_concurrent_scrapes=10,
        ...     timeout_seconds=60,
        ...     timeout_config={"connect": 10, "read": 30},
        ...     retry_failed=True,
        ...     max_articles=100,
        ...     user_agent="CustomBot/1.0"
        ... )
        >>> config.max_concurrent_scrapes
        10
    """

    # Configuración básica
    max_concurrent_scrapes: int = 5
    timeout_seconds: int = 30
    timeout_config: Dict[str, int] = field(default_factory=dict)
    retry_failed: bool = False

    # Configuración avanzada
    max_articles: Optional[int] = None
    retry_attempts: int = 3
    retry_delay_seconds: int = 5
    user_agent: Optional[str] = None
    follow_redirects: bool = True
    validate_ssl: bool = True
    scraping_type: str = "scheduled"

    def __post_init__(self):
        """Valida los valores de configuración."""
        # Validar max_concurrent_scrapes
        if not 1 <= self.max_concurrent_scrapes <= 50:
            raise ValueError(
                f"max_concurrent_scrapes debe estar entre 1 y 50, "
                f"recibido: {self.max_concurrent_scrapes}"
            )

        # Validar timeout_seconds
        if not 5 <= self.timeout_seconds <= 300:
            raise ValueError(
                f"timeout_seconds debe estar entre 5 y 300, "
                f"recibido: {self.timeout_seconds}"
            )

        # Validar timeout_config si existe
        if self.timeout_config:
            for key, value in self.timeout_config.items():
                if not isinstance(value, int) or value < 1:
                    raise ValueError(
                        f"timeout_config['{key}'] debe ser un entero positivo, "
                        f"recibido: {value}"
                    )

        # Validar max_articles
        if self.max_articles is not None and self.max_articles <= 0:
            raise ValueError(
                f"max_articles debe ser mayor a 0, recibido: {self.max_articles}"
            )

        # Validar retry_attempts
        if not 0 <= self.retry_attempts <= 10:
            raise ValueError(
                f"retry_attempts debe estar entre 0 y 10, "
                f"recibido: {self.retry_attempts}"
            )

        # Validar retry_delay_seconds
        if self.retry_delay_seconds <= 0:
            raise ValueError(
                f"retry_delay_seconds debe ser mayor a 0, "
                f"recibido: {self.retry_delay_seconds}"
            )

        # Validar user_agent
        if self.user_agent and len(self.user_agent) > 200:
            raise ValueError(
                f"user_agent no puede exceder 200 caracteres, "
                f"recibido: {len(self.user_agent)}"
            )

        # Validar scraping_type
        valid_types = {"scheduled", "manual", "retry", "bulk", "priority"}
        if self.scraping_type not in valid_types:
            raise ValueError(
                f"scraping_type debe ser uno de {valid_types}, "
                f"recibido: {self.scraping_type}"
            )

    def to_dict(self) -> Dict:
        """
        Serializa la configuración a diccionario.

        Returns:
            Diccionario con los valores de configuración
        """
        return {
            "max_concurrent_scrapes": self.max_concurrent_scrapes,
            "timeout_seconds": self.timeout_seconds,
            "timeout_config": dict(self.timeout_config),
            "retry_failed": self.retry_failed,
            "max_articles": self.max_articles,
            "retry_attempts": self.retry_attempts,
            "retry_delay_seconds": self.retry_delay_seconds,
            "user_agent": self.user_agent,
            "follow_redirects": self.follow_redirects,
            "validate_ssl": self.validate_ssl,
            "scraping_type": self.scraping_type,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "ScrapingConfig":
        """
        Crea una instancia desde un diccionario.

        Args:
            data: Diccionario con los valores de configuración

        Returns:
            Nueva instancia de ScrapingConfig

        Example:
            >>> data = {
            ...     "max_concurrent_scrapes": 10,
            ...     "timeout_seconds": 60,
            ...     "timeout_config": {"connect": 10},
            ...     "retry_failed": True,
            ...     "max_articles": 100
            ... }
            >>> config = ScrapingConfig.from_dict(data)
            >>> config.max_concurrent_scrapes
            10
        """
        return cls(
            max_concurrent_scrapes=data.get("max_concurrent_scrapes", 5),
            timeout_seconds=data.get("timeout_seconds", 30),
            timeout_config=data.get("timeout_config", {}),
            retry_failed=data.get("retry_failed", False),
            max_articles=data.get("max_articles"),
            retry_attempts=data.get("retry_attempts", 3),
            retry_delay_seconds=data.get("retry_delay_seconds", 5),
            user_agent=data.get("user_agent"),
            follow_redirects=data.get("follow_redirects", True),
            validate_ssl=data.get("validate_ssl", True),
            scraping_type=data.get("scraping_type", "scheduled"),
        )

    @classmethod
    def default(cls) -> "ScrapingConfig":
        """
        Crea una configuración con valores por defecto.

        Returns:
            Configuración con valores por defecto
        """
        return cls()
