"""Value Object: FetchLimit para límite máximo de items por fuente."""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class FetchLimit:
    """
    Value Object inmutable para límite de items por fuente durante fetch.

    Define cuántos items máximo obtener de cada fuente RSS.
    Reemplaza la validación primitiva de int en Commands.
    """

    max_items: int
    description: Optional[str] = None

    def __post_init__(self):
        """Validaciones del VO."""
        if not isinstance(self.max_items, int):
            raise ValueError("Fetch limit must be an integer")

        if self.max_items <= 0:
            raise ValueError("Fetch limit must be greater than 0")

        if self.max_items > 1000:  # Límite razonable para prevenir abuso
            raise ValueError("Fetch limit cannot exceed 1000 items per source")

    @classmethod
    def small(cls, description: Optional[str] = None) -> "FetchLimit":
        """Límite pequeño (10 items) - para pruebas o fuentes lentas."""
        return cls(
            max_items=10,
            description=description or "Límite pequeño para pruebas",
        )

    @classmethod
    def standard(cls, description: Optional[str] = None) -> "FetchLimit":
        """Límite estándar (50 items) - configuración por defecto."""
        return cls(
            max_items=50,
            description=description or "Límite estándar por defecto",
        )

    @classmethod
    def large(cls, description: Optional[str] = None) -> "FetchLimit":
        """Límite grande (100 items) - para fuentes activas."""
        return cls(
            max_items=100,
            description=description or "Límite grande para fuentes activas",
        )

    @classmethod
    def bulk(cls, description: Optional[str] = None) -> "FetchLimit":
        """Límite masivo (200 items) - para procesamiento batch."""
        return cls(
            max_items=200,
            description=description or "Límite masivo para batch",
        )

    @classmethod
    def unlimited(cls, description: Optional[str] = None) -> "FetchLimit":
        """Límite muy alto (500 items) - máximo práctico."""
        return cls(
            max_items=500,
            description=description or "Límite muy alto",
        )

    @classmethod
    def create(cls, max_items: int, description: Optional[str] = None) -> "FetchLimit":
        """Factory method para crear límite con cantidad específica."""
        return cls(max_items=max_items, description=description)

    def is_within_limit(self, item_count: int) -> bool:
        """Verifica si un conteo está dentro del límite."""
        return item_count <= self.max_items

    def get_remaining_capacity(self, current_items: int) -> int:
        """Calcula cuántos items más se pueden obtener."""
        remaining = self.max_items - current_items
        return max(0, remaining)  # No puede ser negativo

    def apply_limit(self, items: list) -> list:
        """Aplica el límite a una lista de items."""
        return items[: self.max_items]

    def calculate_batches(self, total_items: int, batch_size: int) -> int:
        """Calcula cuántos batches se necesitan respetando el límite."""
        effective_limit = min(self.max_items, total_items)
        return (effective_limit + batch_size - 1) // batch_size  # Ceiling division

    @property
    def size_category(self) -> str:
        """Categoría del tamaño del límite."""
        if self.max_items <= 20:
            return "small"
        elif self.max_items <= 75:
            return "medium"
        elif self.max_items <= 150:
            return "large"
        else:
            return "bulk"

    @property
    def is_conservative(self) -> bool:
        """Indica si es un límite conservador (<= 30)."""
        return self.max_items <= 30

    @property
    def is_aggressive(self) -> bool:
        """Indica si es un límite agresivo (>= 150)."""
        return self.max_items >= 150

    def get_performance_impact(self) -> str:
        """Impacto estimado en performance."""
        category = self.size_category
        impacts = {
            "small": "Bajo impacto - rápido y eficiente",
            "medium": "Impacto moderado - balance óptimo",
            "large": "Alto impacto - puede ser lento",
            "bulk": "Muy alto impacto - usar con precaución",
        }
        return impacts.get(category, "Impacto desconocido")

    def get_recommendation(self) -> str:
        """Recomendación basada en el tamaño del límite."""
        if self.is_conservative:
            return "Límite conservador, considera incrementar para mayor throughput"
        elif self.is_aggressive:
            return "Límite agresivo, monitorear performance y timeouts"
        else:
            return "Límite equilibrado para operaciones normales"

    def __int__(self) -> int:
        """Conversión a int."""
        return self.max_items

    def __str__(self) -> str:
        """Representación string del objeto."""
        return f"{self.max_items}"

    def __repr__(self) -> str:
        """Representación para debugging."""
        return f"FetchLimit({self.max_items}, '{self.description}')"
