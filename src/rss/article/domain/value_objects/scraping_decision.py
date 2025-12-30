"""
Value Object para decisión de estrategia de scraping.
Encapsula la lógica de decisión sobre qué scraper utilizar.
"""

from dataclasses import dataclass
from typing import Optional

from .scraper_type import ScraperStrategy


@dataclass(frozen=True)
class ScrapingDecision:
    """
    Value Object para la decisión de qué estrategia de scraping usar.

    Encapsula:
    - Estrategia seleccionada (Playwright, Trafilatura, etc.)
    - Razón de la decisión
    - Confianza en la decisión
    - Fallback strategy si la principal falla
    """

    strategy: ScraperStrategy
    reason: str
    confidence: float  # 0.0 a 1.0
    fallback_strategy: Optional[ScraperStrategy] = None

    def __post_init__(self):
        """Validación post-inicialización."""
        if not isinstance(self.strategy, ScraperStrategy):
            raise TypeError(
                f"strategy debe ser ScraperStrategy, recibido: {type(self.strategy)}"
            )

        if not isinstance(self.confidence, (int, float)):
            raise TypeError(
                f"confidence debe ser float, recibido: {type(self.confidence)}"
            )

        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(
                f"confidence debe estar entre 0.0 y 1.0: {self.confidence}"
            )

        if not self.reason or not self.reason.strip():
            raise ValueError("reason no puede estar vacío")

        if self.fallback_strategy and not isinstance(
            self.fallback_strategy, ScraperStrategy
        ):
            raise TypeError(
                f"fallback_strategy debe ser ScraperStrategy o None: {type(self.fallback_strategy)}"
            )

    @classmethod
    def use_playwright(
        cls,
        reason: str,
        confidence: float = 1.0,
        with_trafilatura_fallback: bool = False,
    ) -> "ScrapingDecision":
        """
        Decisión de usar Playwright.

        Args:
            reason: Razón de la decisión
            confidence: Nivel de confianza
            with_trafilatura_fallback: Si usar trafilatura como fallback

        Returns:
            ScrapingDecision configurada para Playwright
        """
        fallback = ScraperStrategy.TRAFILATURA if with_trafilatura_fallback else None
        return cls(
            strategy=ScraperStrategy.PLAYWRIGHT,
            reason=reason,
            confidence=confidence,
            fallback_strategy=fallback,
        )

    @classmethod
    def use_trafilatura(
        cls, reason: str, confidence: float = 0.8, with_playwright_fallback: bool = True
    ) -> "ScrapingDecision":
        """
        Decisión de usar Trafilatura.

        Args:
            reason: Razón de la decisión
            confidence: Nivel de confianza
            with_playwright_fallback: Si usar Playwright como fallback

        Returns:
            ScrapingDecision configurada para Trafilatura
        """
        fallback = ScraperStrategy.PLAYWRIGHT if with_playwright_fallback else None
        return cls(
            strategy=ScraperStrategy.TRAFILATURA,
            reason=reason,
            confidence=confidence,
            fallback_strategy=fallback,
        )

    @classmethod
    def use_smart(cls, reason: str = "Smart auto-selection") -> "ScrapingDecision":
        """
        Decisión de usar SmartScraper (auto-selección).

        Args:
            reason: Razón de la decisión

        Returns:
            ScrapingDecision configurada para SmartScraper
        """
        return cls(
            strategy=ScraperStrategy.SMART,
            reason=reason,
            confidence=1.0,
            fallback_strategy=None,
        )

    @classmethod
    def for_javascript_heavy_site(cls, domain: str) -> "ScrapingDecision":
        """
        Decisión para sitio JavaScript-heavy conocido.

        Args:
            domain: Dominio del sitio

        Returns:
            ScrapingDecision con Playwright directo
        """
        return cls.use_playwright(
            reason=f"JS-heavy domain detected: {domain}",
            confidence=1.0,
            with_trafilatura_fallback=False,
        )

    @classmethod
    def for_static_site(cls, domain: str) -> "ScrapingDecision":
        """
        Decisión para sitio HTML estático.

        Args:
            domain: Dominio del sitio

        Returns:
            ScrapingDecision con Trafilatura + fallback a Playwright
        """
        return cls.use_trafilatura(
            reason=f"Static HTML site detected: {domain}",
            confidence=0.8,
            with_playwright_fallback=True,
        )

    @classmethod
    def for_url_pattern_match(cls, pattern: str) -> "ScrapingDecision":
        """
        Decisión para URL con patrón JavaScript detectado.

        Args:
            pattern: Patrón detectado (e.g. '/app/', '/embed/')

        Returns:
            ScrapingDecision con Playwright directo
        """
        return cls.use_playwright(
            reason=f"JS pattern detected in URL: {pattern}",
            confidence=0.95,
            with_trafilatura_fallback=False,
        )

    def requires_javascript(self) -> bool:
        """Verifica si la estrategia requiere capacidad JavaScript."""
        return self.strategy in [ScraperStrategy.PLAYWRIGHT, ScraperStrategy.SMART]

    def is_high_confidence(self) -> bool:
        """Verifica si es una decisión de alta confianza (>= 0.9)."""
        return self.confidence >= 0.9

    def is_low_confidence(self) -> bool:
        """Verifica si es una decisión de baja confianza (< 0.5)."""
        return self.confidence < 0.5

    def has_fallback(self) -> bool:
        """Verifica si tiene estrategia de fallback configurada."""
        return self.fallback_strategy is not None

    def get_primary_strategy_name(self) -> str:
        """Retorna nombre de la estrategia principal."""
        return self.strategy.value

    def get_fallback_strategy_name(self) -> Optional[str]:
        """Retorna nombre de la estrategia de fallback."""
        return self.fallback_strategy.value if self.fallback_strategy else None

    def get_confidence_level(self) -> str:
        """Categoriza el nivel de confianza."""
        if self.confidence >= 0.9:
            return "high"
        elif self.confidence >= 0.7:
            return "medium"
        elif self.confidence >= 0.5:
            return "low"
        else:
            return "very_low"

    def should_try_fallback_on_failure(self) -> bool:
        """Determina si debería intentar fallback si falla la estrategia principal."""
        return self.has_fallback() and self.confidence < 1.0

    def __str__(self) -> str:
        strategy_name = self.strategy.value
        fallback = (
            f" (fallback: {self.fallback_strategy.value})"
            if self.fallback_strategy
            else ""
        )
        return f"{strategy_name}{fallback} - {self.reason} ({self.confidence:.0%} confidence)"

    def __repr__(self) -> str:
        return (
            f"ScrapingDecision(strategy={self.strategy}, "
            f"reason='{self.reason}', "
            f"confidence={self.confidence}, "
            f"fallback_strategy={self.fallback_strategy})"
        )
