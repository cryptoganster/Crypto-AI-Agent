"""
Value Object para validación de longitud mínima de contenido scrapeado.
Encapsula reglas de validación de contenido suficiente.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class MinimumContentLength:
    """
    Value Object para longitud mínima de contenido válido.

    Garantiza:
    - Validación consistente de contenido mínimo
    - Diferentes umbrales según tipo de contenido
    - Métodos de validación expresivos
    """

    min_chars: int

    # Constantes de umbrales predefinidos
    VERY_SHORT = 100  # Snippet o preview corto
    SHORT = 300  # Noticia breve
    STANDARD = 500  # Artículo estándar
    LONG = 1000  # Artículo largo/análisis
    VERY_LONG = 2000  # Artículo profundo

    def __post_init__(self):
        """Validación post-inicialización."""
        if not isinstance(self.min_chars, int):
            raise TypeError(f"min_chars debe ser int, recibido: {type(self.min_chars)}")

        if self.min_chars < 0:
            raise ValueError(f"min_chars debe ser positivo: {self.min_chars}")

    @classmethod
    def create(cls, min_chars: int) -> "MinimumContentLength":
        """Factory method para crear longitud mínima."""
        return cls(min_chars)

    @classmethod
    def standard(cls) -> "MinimumContentLength":
        """Crea umbral estándar (500 caracteres)."""
        return cls(cls.STANDARD)

    @classmethod
    def short(cls) -> "MinimumContentLength":
        """Crea umbral para contenido breve (300 caracteres)."""
        return cls(cls.SHORT)

    @classmethod
    def long(cls) -> "MinimumContentLength":
        """Crea umbral para contenido largo (1000 caracteres)."""
        return cls(cls.LONG)

    @classmethod
    def very_short(cls) -> "MinimumContentLength":
        """Crea umbral muy corto (100 caracteres)."""
        return cls(cls.VERY_SHORT)

    @classmethod
    def very_long(cls) -> "MinimumContentLength":
        """Crea umbral muy largo (2000 caracteres)."""
        return cls(cls.VERY_LONG)

    def is_sufficient(self, content: str) -> bool:
        """
        Valida si el contenido tiene longitud suficiente.

        Args:
            content: Contenido a validar

        Returns:
            True si cumple longitud mínima
        """
        if not content:
            return False
        return len(content) >= self.min_chars

    def get_deficit(self, content: str) -> int:
        """
        Calcula cuántos caracteres faltan para cumplir el mínimo.

        Args:
            content: Contenido a evaluar

        Returns:
            Caracteres faltantes (0 si ya cumple)
        """
        if not content:
            return self.min_chars

        current_length = len(content)
        deficit = self.min_chars - current_length
        return max(0, deficit)

    def get_completion_percentage(self, content: str) -> float:
        """
        Calcula porcentaje de completitud respecto al mínimo.

        Args:
            content: Contenido a evaluar

        Returns:
            Porcentaje (0.0 a 100.0+)
        """
        if not content:
            return 0.0

        current_length = len(content)
        percentage = (current_length / self.min_chars) * 100.0
        return percentage

    def is_category(self) -> str:
        """Categoriza el umbral configurado."""
        if self.min_chars <= self.VERY_SHORT:
            return "very_short"
        elif self.min_chars <= self.SHORT:
            return "short"
        elif self.min_chars <= self.STANDARD:
            return "standard"
        elif self.min_chars <= self.LONG:
            return "long"
        else:
            return "very_long"

    def __str__(self) -> str:
        return f"MinimumContentLength({self.min_chars} chars)"

    def __repr__(self) -> str:
        return f"MinimumContentLength(min_chars={self.min_chars})"
