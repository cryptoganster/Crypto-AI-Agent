"""Value Object para tiempo de lectura de artículos."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ReadingTime:
    """
    Value Object que representa el tiempo estimado de lectura de un artículo.

    Calculado basándose en el conteo de palabras y velocidad promedio de lectura.
    Velocidad estándar: 200 palabras por minuto (WPM).
    """

    minutes: int

    def __post_init__(self):
        """Valida que el tiempo sea no negativo."""
        if not isinstance(self.minutes, int):
            raise TypeError("Reading time debe ser un entero")

        if self.minutes < 0:
            raise ValueError(
                f"Reading time no puede ser negativo, recibido: {self.minutes}"
            )

    @classmethod
    def from_word_count(cls, word_count: int, wpm: int = 200) -> "ReadingTime":
        """
        Calcula el tiempo de lectura desde un conteo de palabras.

        Args:
            word_count: Número de palabras del artículo
            wpm: Palabras por minuto (default: 200)

        Returns:
            ReadingTime calculado (mínimo 1 minuto)

        Raises:
            ValueError: Si word_count o wpm son negativos
        """
        if word_count < 0:
            raise ValueError("Word count no puede ser negativo")

        if wpm <= 0:
            raise ValueError("WPM debe ser positivo")

        # Calcular minutos, mínimo 1
        minutes = max(1, word_count // wpm)
        return cls(minutes=minutes)

    def is_quick_read(self) -> bool:
        """
        Determina si es una lectura rápida.

        Returns:
            True si toma 5 minutos o menos
        """
        return self.minutes <= 5

    def is_long_read(self) -> bool:
        """
        Determina si es una lectura larga.

        Returns:
            True si toma más de 15 minutos
        """
        return self.minutes > 15

    def is_medium_read(self) -> bool:
        """
        Determina si es una lectura de duración media.

        Returns:
            True si toma entre 6 y 15 minutos
        """
        return 6 <= self.minutes <= 15

    def get_reading_category(self) -> str:
        """
        Obtiene la categoría de lectura basada en duración.

        Returns:
            Categoría: "quick", "medium", "long", "very_long"
        """
        if self.minutes <= 5:
            return "quick"
        elif self.minutes <= 15:
            return "medium"
        elif self.minutes <= 30:
            return "long"
        else:
            return "very_long"

    def to_display_string(self) -> str:
        """
        Convierte a string legible para mostrar al usuario.

        Returns:
            String formateado: "5 min read", "1 min read", etc.
        """
        if self.minutes == 1:
            return "1 min read"
        else:
            return f"{self.minutes} min read"

    def __str__(self) -> str:
        """Representación en string del tiempo."""
        return str(self.minutes)

    def __repr__(self) -> str:
        """Representación para debugging."""
        return f"ReadingTime(minutes={self.minutes}, category={self.get_reading_category()})"

    def __int__(self) -> int:
        """Permite conversión a int."""
        return self.minutes
