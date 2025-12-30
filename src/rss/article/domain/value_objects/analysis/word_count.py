"""Value Object para conteo de palabras de artículos."""

from dataclasses import dataclass


@dataclass(frozen=True)
class WordCount:
    """
    Value Object que representa el conteo de palabras de un artículo.

    Encapsula validaciones y comportamiento relacionado con la longitud del contenido.
    """

    value: int

    def __post_init__(self):
        """Valida que el conteo sea no negativo."""
        if not isinstance(self.value, int):
            raise TypeError("Word count debe ser un entero")

        if self.value < 0:
            raise ValueError(
                f"Word count no puede ser negativo, recibido: {self.value}"
            )

    def is_long_form(self) -> bool:
        """
        Determina si el artículo es de formato largo.

        Returns:
            True si tiene 1000+ palabras
        """
        return self.value >= 1000

    def is_short_form(self) -> bool:
        """
        Determina si el artículo es de formato corto.

        Returns:
            True si tiene menos de 300 palabras
        """
        return self.value < 300

    def is_medium_form(self) -> bool:
        """
        Determina si el artículo es de formato medio.

        Returns:
            True si tiene entre 300 y 999 palabras
        """
        return 300 <= self.value < 1000

    def is_empty(self) -> bool:
        """
        Determina si el conteo es cero.

        Returns:
            True si value es 0
        """
        return self.value == 0

    def has_minimum_length(self, minimum: int = 100) -> bool:
        """
        Verifica si cumple con un mínimo de palabras.

        Args:
            minimum: Número mínimo de palabras requerido

        Returns:
            True si cumple el mínimo
        """
        return self.value >= minimum

    def get_content_type(self) -> str:
        """
        Obtiene el tipo de contenido basado en longitud.

        Returns:
            Tipo: "empty", "snippet", "short", "medium", "long", "very_long"
        """
        if self.value == 0:
            return "empty"
        elif self.value < 100:
            return "snippet"
        elif self.value < 300:
            return "short"
        elif self.value < 1000:
            return "medium"
        elif self.value < 3000:
            return "long"
        else:
            return "very_long"

    def __str__(self) -> str:
        """Representación en string del conteo."""
        return str(self.value)

    def __repr__(self) -> str:
        """Representación para debugging."""
        return f"WordCount(value={self.value}, type={self.get_content_type()})"

    def __int__(self) -> int:
        """Permite conversión a int."""
        return self.value
