"""
Value Object para HTML scrapeado de artículos.
Encapsula validación y operaciones sobre contenido HTML obtenido por scraping.
"""

import re
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class ScrappedHtml:
    """
    Value Object para HTML scrapeado de artículos RSS.

    Diferencias con ArticleContent:
    - ArticleContent: contenido procesado/limpio para el usuario
    - ScrappedHtml: HTML raw desde scraping, puede contener tags, scripts, etc.
    """

    value: str

    def __post_init__(self):
        """Validación post-inicialización."""
        if self.value is None:
            raise ValueError(
                "HTML scrapeado no puede ser None (usar empty string si vacío)"
            )

        # Permitir contenido vacío pero normalizar
        if isinstance(self.value, str):
            # No normalizar espacios en HTML (puede romper estructura)
            object.__setattr__(self, "value", self.value)
        else:
            raise TypeError(
                f"HTML scrapeado debe ser string, recibido: {type(self.value)}"
            )

    @classmethod
    def create(cls, html: Optional[str]) -> "ScrappedHtml":
        """Factory method para crear HTML scrapeado."""
        if html is None:
            return cls("")
        return cls(html)

    @classmethod
    def empty(cls) -> "ScrappedHtml":
        """Crea HTML scrapeado vacío."""
        return cls("")

    def is_empty(self) -> bool:
        """Verifica si el HTML está vacío."""
        return len(self.value.strip()) == 0

    def is_sufficient(self, min_length: int = 500) -> bool:
        """
        Valida si tiene contenido suficiente.

        Default: 500 chars (alineado con SmartScraperService threshold)

        Args:
            min_length: Longitud mínima en caracteres

        Returns:
            True si cumple con longitud mínima
        """
        return len(self.value.strip()) >= min_length

    def get_length(self) -> int:
        """Obtiene longitud del HTML."""
        return len(self.value)

    def extract_text_preview(self, max_chars: int = 200) -> str:
        """
        Extrae preview de texto sin tags HTML.

        Args:
            max_chars: Máximo de caracteres para preview

        Returns:
            Preview de texto limpio sin HTML
        """
        if self.is_empty():
            return ""

        # Limpieza básica de HTML
        text = re.sub(
            r"<script[^>]*>.*?</script>",
            "",
            self.value,
            flags=re.DOTALL | re.IGNORECASE,
        )
        text = re.sub(
            r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL | re.IGNORECASE
        )
        text = re.sub(r"<[^>]+>", "", text)  # Remover todos los tags
        text = re.sub(r"\s+", " ", text).strip()  # Normalizar espacios

        if len(text) <= max_chars:
            return text

        return text[: max_chars - 3] + "..."

    def contains_tag(self, tag: str) -> bool:
        """Verifica si contiene un tag HTML específico."""
        pattern = f"<{tag}[^>]*>"
        return bool(re.search(pattern, self.value, re.IGNORECASE))

    def count_tags(self) -> int:
        """Cuenta número de tags HTML."""
        return len(re.findall(r"<[^>]+>", self.value))

    def has_minimum_quality(self) -> bool:
        """
        Verifica calidad mínima del HTML scrapeado.

        Criterios:
        - Al menos 500 caracteres
        - Contiene al menos un tag HTML
        """
        return self.is_sufficient(500) and self.count_tags() > 0

    def truncate(self, max_length: int = 1000) -> str:
        """
        Trunca HTML para preview.

        Args:
            max_length: Longitud máxima

        Returns:
            HTML truncado
        """
        if len(self.value) <= max_length:
            return self.value
        return self.value[: max_length - 3] + "..."

    def __str__(self) -> str:
        return self.value

    def __len__(self) -> int:
        return len(self.value)

    def __bool__(self) -> bool:
        """Permite usar en contextos booleanos."""
        return not self.is_empty()
