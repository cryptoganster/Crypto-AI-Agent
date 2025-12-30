"""
Value Object para tipo de scraper utilizado.
Encapsula información sobre qué scraper procesó el contenido.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class ScraperStrategy(Enum):
    """Estrategias de scraping disponibles."""

    PLAYWRIGHT = "playwright"
    TRAFILATURA = "trafilatura"
    SMART = "smart"
    CACHED = "cached"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class ScraperType:
    """
    Value Object para tipo de scraper usado.

    Provee:
    - Identificación del scraper utilizado
    - Metadata sobre la estrategia
    - Display names amigables
    """

    name: str
    strategy: Optional[ScraperStrategy] = None

    # Constantes de nombres de scrapers
    PLAYWRIGHT_SERVICE = "PlaywrightScraperService"
    TRAFILATURA_SERVICE = "TrafilaturaScraperService"
    SMART_SERVICE = "SmartScraperService"
    CACHED = "cached"

    def __post_init__(self):
        """Validación y normalización post-inicialización."""
        if not self.name:
            raise ValueError("Scraper name no puede estar vacío")

        # Auto-detectar estrategia si no fue especificada
        if self.strategy is None:
            detected_strategy = self._detect_strategy(self.name)
            object.__setattr__(self, "strategy", detected_strategy)

    @classmethod
    def from_service(cls, service_class_name: str) -> "ScraperType":
        """
        Factory method desde nombre de clase del servicio.

        Args:
            service_class_name: Nombre de la clase (e.g. "PlaywrightScraperService")

        Returns:
            ScraperType con estrategia detectada
        """
        return cls(name=service_class_name)

    @classmethod
    def playwright(cls) -> "ScraperType":
        """Crea ScraperType para Playwright."""
        return cls(name=cls.PLAYWRIGHT_SERVICE, strategy=ScraperStrategy.PLAYWRIGHT)

    @classmethod
    def trafilatura(cls) -> "ScraperType":
        """Crea ScraperType para Trafilatura."""
        return cls(name=cls.TRAFILATURA_SERVICE, strategy=ScraperStrategy.TRAFILATURA)

    @classmethod
    def smart(cls) -> "ScraperType":
        """Crea ScraperType para SmartScraper."""
        return cls(name=cls.SMART_SERVICE, strategy=ScraperStrategy.SMART)

    @classmethod
    def cached(cls) -> "ScraperType":
        """Crea ScraperType para contenido cacheado."""
        return cls(name=cls.CACHED, strategy=ScraperStrategy.CACHED)

    def _detect_strategy(self, name: str) -> ScraperStrategy:
        """Detecta estrategia basada en nombre."""
        name_lower = name.lower()

        if "playwright" in name_lower:
            return ScraperStrategy.PLAYWRIGHT
        elif "trafilatura" in name_lower:
            return ScraperStrategy.TRAFILATURA
        elif "smart" in name_lower:
            return ScraperStrategy.SMART
        elif "cached" in name_lower or "cache" in name_lower:
            return ScraperStrategy.CACHED
        else:
            return ScraperStrategy.UNKNOWN

    def display_name(self) -> str:
        """
        Nombre amigable para mostrar.

        Returns:
            Nombre simplificado sin sufijo "Service"
        """
        return self.name.replace("ScraperService", "").replace("Service", "")

    def is_javascript_capable(self) -> bool:
        """Verifica si el scraper puede ejecutar JavaScript."""
        return self.strategy in [ScraperStrategy.PLAYWRIGHT, ScraperStrategy.SMART]

    def is_cached(self) -> bool:
        """Verifica si es contenido cacheado."""
        return self.strategy == ScraperStrategy.CACHED

    def is_static_only(self) -> bool:
        """Verifica si solo maneja HTML estático."""
        return self.strategy == ScraperStrategy.TRAFILATURA

    def get_emoji(self) -> str:
        """Retorna emoji representativo del scraper."""
        emoji_map = {
            ScraperStrategy.PLAYWRIGHT: "🎭",
            ScraperStrategy.TRAFILATURA: "📄",
            ScraperStrategy.SMART: "🧠",
            ScraperStrategy.CACHED: "💾",
            ScraperStrategy.UNKNOWN: "❓",
        }
        return emoji_map.get(self.strategy, "❓")

    def __str__(self) -> str:
        return f"{self.get_emoji()} {self.display_name()}"

    def __repr__(self) -> str:
        return f"ScraperType(name='{self.name}', strategy={self.strategy})"
