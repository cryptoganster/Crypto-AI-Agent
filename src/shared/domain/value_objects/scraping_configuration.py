"""
Value Object: ScrapingConfiguration
Configuración especializada de scraping por fuente RSS.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class ScrapingConfiguration:
    """
    Configuración de scraping especializada para una fuente específica.

    Permite definir selectores CSS específicos, timeouts y estrategias
    de carga optimizadas para cada sitio web.
    """

    # Selectores CSS en orden de prioridad
    content_selectors: tuple[str, ...]

    # Selectores CSS de elementos a EXCLUIR (ads, widgets, banners)
    excluded_selectors: tuple[str, ...] = ()

    # Textos específicos a EXCLUIR (busca y elimina elementos que contengan estos textos)
    excluded_texts: tuple[str, ...] = ()

    # Patrones de texto a EXCLUIR (busca párrafos que empiecen con estos patrones)
    # Ejemplo: ("Related:", "Magazine:") eliminará párrafos que empiecen con estos textos
    excluded_text_patterns: tuple[str, ...] = ()

    # Selectores genéricos de fallback (usados si content_selectors fallan)
    # Se intentan en orden de prioridad
    fallback_selectors: tuple[str, ...] = (
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
    )

    # Tiempo de espera para carga de JavaScript (milisegundos)
    wait_timeout_ms: int = 3000

    # Estrategia de espera: 'domcontentloaded', 'load', 'networkidle'
    wait_strategy: str = "domcontentloaded"

    # Si necesita scroll para lazy loading
    scroll_needed: bool = False

    # Timeout adicional para selectores (milisegundos)
    selector_timeout_ms: int = 5000

    def __post_init__(self):
        """Validaciones."""
        if not self.content_selectors:
            raise ValueError("content_selectors no puede estar vacío")

        if self.wait_timeout_ms < 0:
            raise ValueError("wait_timeout_ms debe ser positivo")

        if self.wait_strategy not in ["domcontentloaded", "load", "networkidle"]:
            raise ValueError(f"wait_strategy inválida: {self.wait_strategy}")

    @staticmethod
    def cointelegraph() -> "ScrapingConfiguration":
        """
        Configuración optimizada para Cointelegraph.

        Basada en inspección real de estructura HTML:
        - Selectores principales: .post-content, article, main
        - Excluye: banners, widgets de precios, ads, newsletters
        - Necesita 3s para JavaScript
        - Scroll para lazy images
        """
        return ScrapingConfiguration(
            content_selectors=(".post-content", "article", "main"),
            excluded_selectors=(
                # Publicidad y widgets
                ".text-banner",  # Banners de publicidad
                '[data-testid="live-data-ticker"]',  # Widgets de precios en vivo
                "#buzzsprout-player",  # Reproductores de podcast
                ".newsletter-subscription-form",  # Formularios de newsletter
                '[data-testid="close-ad-button"]',  # Botones de ads
                ".m-auto.relative",  # Contenedores de ads
                "iframe",  # iframes (generalmente ads)
                # Formularios y newsletters
                "form",  # Todos los formularios
                'form[class*="newsletter"]',
                '[class*="newsletter-subscription"]',
                "fieldset",
                'button[type="submit"]',
                'input[type="email"]',
                '[class*="-tos"]',
                # Widgets Cointelegraph
                "[data-ct-widget]",  # Widgets específicos
                '[class*="widget"]',
                # Estructura
                "nav",
                "header",
                "footer",
                '[role="complementary"]',
                # Media decorativa
                "svg",  # SVGs inline
                '[aria-label*="advertisement"]',
                # Elementos sociales y secundarios
                '[class*="social"]',  # Botones sociales (share, follow, etc)
                '[class*="share"]',  # Botones de compartir
                '[class*="comment"]',  # Secciones de comentarios
                '[class*="related"]',  # Artículos relacionados
                "aside",  # Sidebars con contenido secundario
                # Disclaimers legales
                ".post-content__disclaimer",  # Disclaimers de inversión
            ),
            excluded_texts=(),
            excluded_text_patterns=(),
            fallback_selectors=(
                "article",
                "main",
                "[role='main']",
                ".article-content",
                ".post-content",
                ".entry-content",
                "body",
            ),
            wait_timeout_ms=3000,
            wait_strategy="domcontentloaded",
            scroll_needed=True,
            selector_timeout_ms=5000,
        )

    @staticmethod
    def default() -> "ScrapingConfiguration":
        """
        Configuración genérica para sitios con estructura estándar.

        Usa selectores HTML semánticos comunes.
        """
        return ScrapingConfiguration(
            content_selectors=(
                "article",
                "main",
                '[role="main"]',
                ".content",
                ".post-content",
            ),
            excluded_selectors=(),
            excluded_texts=(),
            excluded_text_patterns=(),
            fallback_selectors=(
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
            ),
            wait_timeout_ms=2000,
            wait_strategy="domcontentloaded",
            scroll_needed=False,
            selector_timeout_ms=5000,
        )

    @staticmethod
    def fast() -> "ScrapingConfiguration":
        """
        Configuración rápida para sitios HTML estáticos simples.
        """
        return ScrapingConfiguration(
            content_selectors=("article", "main"),
            excluded_selectors=(),
            excluded_texts=(),
            excluded_text_patterns=(),
            fallback_selectors=("article", "main", "body"),
            wait_timeout_ms=1000,
            wait_strategy="domcontentloaded",
            scroll_needed=False,
            selector_timeout_ms=3000,
        )

    def with_additional_selectors(self, *selectors: str) -> "ScrapingConfiguration":
        """
        Crea nueva configuración agregando selectores adicionales.
        """
        new_selectors = self.content_selectors + tuple(selectors)
        return ScrapingConfiguration(
            content_selectors=new_selectors,
            excluded_selectors=self.excluded_selectors,
            excluded_texts=self.excluded_texts,
            excluded_text_patterns=self.excluded_text_patterns,
            fallback_selectors=self.fallback_selectors,
            wait_timeout_ms=self.wait_timeout_ms,
            wait_strategy=self.wait_strategy,
            scroll_needed=self.scroll_needed,
            selector_timeout_ms=self.selector_timeout_ms,
        )

    def with_excluded_selectors(self, *selectors: str) -> "ScrapingConfiguration":
        """
        Crea nueva configuración agregando selectores a excluir.
        """
        new_excluded = self.excluded_selectors + tuple(selectors)
        return ScrapingConfiguration(
            content_selectors=self.content_selectors,
            excluded_selectors=new_excluded,
            excluded_texts=self.excluded_texts,
            excluded_text_patterns=self.excluded_text_patterns,
            fallback_selectors=self.fallback_selectors,
            wait_timeout_ms=self.wait_timeout_ms,
            wait_strategy=self.wait_strategy,
            scroll_needed=self.scroll_needed,
            selector_timeout_ms=self.selector_timeout_ms,
        )

    def get_wait_timeout_seconds(self) -> float:
        """Retorna timeout en segundos."""
        return self.wait_timeout_ms / 1000.0

    def get_selector_timeout_seconds(self) -> float:
        """Retorna timeout de selectores en segundos."""
        return self.selector_timeout_ms / 1000.0

    def __str__(self) -> str:
        return (
            f"ScrapingConfig(selectors={len(self.content_selectors)}, "
            f"wait={self.wait_timeout_ms}ms, "
            f"strategy={self.wait_strategy}, "
            f"scroll={self.scroll_needed})"
        )
