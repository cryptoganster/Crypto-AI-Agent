"""
Value Object para colección de patrones de URL que indican JavaScript.
Encapsula reglas de detección de URLs dinámicas.
"""

from dataclasses import dataclass
from typing import FrozenSet


@dataclass(frozen=True)
class UrlPatternCollection:
    """
    Value Object para patrones de URL que indican contenido JavaScript.

    Provee:
    - Patrones inmutables de URL paths
    - Métodos de detección y matching
    - Categorización por tipo de patrón
    """

    patterns: FrozenSet[str]

    def __post_init__(self):
        """Validación post-inicialización."""
        if not isinstance(self.patterns, (frozenset, set)):
            raise TypeError(
                f"patterns debe ser set/frozenset, recibido: {type(self.patterns)}"
            )

        # Normalizar todos los patrones a lowercase
        normalized = frozenset(p.lower() for p in self.patterns)
        object.__setattr__(self, "patterns", normalized)

    @classmethod
    def default(cls) -> "UrlPatternCollection":
        """
        Crea colección con patrones conocidos por defecto.

        Patrones incluidos:
        - /app/ - Aplicaciones web SPA
        - /embed/ - Contenido embebido (videos, widgets)
        - /player/ - Reproductores de media
        - /widget/ - Widgets interactivos
        - /live/ - Contenido en vivo
        - /stream/ - Streaming de contenido
        - /interactive/ - Contenido interactivo
        - /dashboard/ - Dashboards dinámicos
        """
        default_patterns = {
            "/app/",
            "/embed/",
            "/player/",
            "/widget/",
            "/live/",
            "/stream/",
            "/interactive/",
            "/dashboard/",
            "/spa/",
            "/react/",
            "/angular/",
            "/vue/",
        }
        return cls(frozenset(default_patterns))

    @classmethod
    def create(cls, patterns: set) -> "UrlPatternCollection":
        """Factory method para crear colección personalizada."""
        return cls(frozenset(patterns))

    @classmethod
    def empty(cls) -> "UrlPatternCollection":
        """Crea colección vacía."""
        return cls(frozenset())

    def matches_any(self, url: str) -> bool:
        """
        Verifica si la URL contiene alguno de los patrones.

        Args:
            url: URL a verificar (se normaliza automáticamente)

        Returns:
            True si la URL contiene algún patrón
        """
        if not url:
            return False

        url_lower = url.lower()
        return any(pattern in url_lower for pattern in self.patterns)

    def find_matches(self, url: str) -> FrozenSet[str]:
        """
        Encuentra todos los patrones que coinciden en la URL.

        Args:
            url: URL a analizar

        Returns:
            Set de patrones que coinciden
        """
        if not url:
            return frozenset()

        # Convertir a string si es un Value Object
        url_str = str(url) if not isinstance(url, str) else url
        url_lower = url_str.lower()
        matches = {pattern for pattern in self.patterns if pattern in url_lower}
        return frozenset(matches)

    def add(self, pattern: str) -> "UrlPatternCollection":
        """
        Crea nueva colección agregando un patrón.

        Args:
            pattern: Patrón a agregar

        Returns:
            Nueva UrlPatternCollection con patrón agregado
        """
        normalized = pattern.lower()
        new_patterns = self.patterns | {normalized}
        return UrlPatternCollection(new_patterns)

    def remove(self, pattern: str) -> "UrlPatternCollection":
        """
        Crea nueva colección removiendo un patrón.

        Args:
            pattern: Patrón a remover

        Returns:
            Nueva UrlPatternCollection sin el patrón
        """
        normalized = pattern.lower()
        new_patterns = self.patterns - {normalized}
        return UrlPatternCollection(new_patterns)

    def merge(self, other: "UrlPatternCollection") -> "UrlPatternCollection":
        """
        Combina dos colecciones.

        Args:
            other: Otra colección a combinar

        Returns:
            Nueva colección con patrones combinados
        """
        merged_patterns = self.patterns | other.patterns
        return UrlPatternCollection(merged_patterns)

    def get_media_patterns(self) -> FrozenSet[str]:
        """Retorna solo patrones relacionados con media."""
        media = {"/embed/", "/player/", "/live/", "/stream/"}
        return self.patterns & media

    def get_app_patterns(self) -> FrozenSet[str]:
        """Retorna solo patrones relacionados con aplicaciones."""
        app = {"/app/", "/spa/", "/dashboard/", "/interactive/"}
        return self.patterns & app

    def get_framework_patterns(self) -> FrozenSet[str]:
        """Retorna solo patrones relacionados con frameworks."""
        framework = {"/react/", "/angular/", "/vue/"}
        return self.patterns & framework

    def count(self) -> int:
        """Retorna cantidad de patrones en la colección."""
        return len(self.patterns)

    def is_empty(self) -> bool:
        """Verifica si la colección está vacía."""
        return len(self.patterns) == 0

    def __len__(self) -> int:
        return len(self.patterns)

    def __contains__(self, pattern: str) -> bool:
        """Permite usar 'in' operator."""
        return pattern.lower() in self.patterns

    def __str__(self) -> str:
        return f"UrlPatternCollection({len(self.patterns)} patterns)"

    def __repr__(self) -> str:
        patterns_preview = list(self.patterns)[:3]
        preview = ", ".join(patterns_preview)
        suffix = "..." if len(self.patterns) > 3 else ""
        return f"UrlPatternCollection(patterns={{{preview}{suffix}}})"
