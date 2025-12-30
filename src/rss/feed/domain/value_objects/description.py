"""
Value Object para descripciones de fuentes RSS.
Encapsula validación y normalización de descripciones de sources.
"""

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class RssFeedDescription:
    """Value Object para descripciones de fuentes RSS."""

    value: str

    def __post_init__(self):
        """Validación post-inicialización."""
        # Permitir descripciones vacías
        if self.value is None:
            object.__setattr__(self, "value", "")
            return

        if len(self.value) > 1000:
            raise ValueError(
                "Descripción de la fuente RSS no puede exceder 1000 caracteres"
            )

        # Normalizar descripción (eliminar espacios extra)
        normalized = re.sub(r"\s+", " ", self.value.strip()) if self.value else ""
        object.__setattr__(self, "value", normalized)

    @classmethod
    def create_from_url(cls, url: str) -> "RssFeedDescription":
        """Factory method para crear descripción desde URL."""
        try:
            from urllib.parse import urlparse

            parsed = urlparse(url)
            domain = parsed.netloc or parsed.path

            if domain:
                clean_domain = domain.replace("www.", "")
                return cls(f"RSS feed from {clean_domain}")
            else:
                return cls("RSS feed")
        except Exception:
            return cls("RSS feed")

    @classmethod
    def empty(cls) -> "RssFeedDescription":
        """Factory method para descripción vacía."""
        return cls("")

    @classmethod
    def create_default(cls, source_name: str) -> "RssFeedDescription":
        """Factory method para crear descripción por defecto."""
        if not source_name:
            return cls("RSS feed source")
        return cls(f"RSS feed from {source_name}")

    def is_empty(self) -> bool:
        """Verifica si la descripción está vacía."""
        return len(self.value.strip()) == 0

    def get_preview(self, max_length: int = 100) -> str:
        """Obtiene preview de la descripción."""
        if len(self.value) <= max_length:
            return self.value
        return self.value[: max_length - 3] + "..."

    def get_word_count(self) -> int:
        """Obtiene conteo de palabras."""
        if self.is_empty():
            return 0
        return len(self.value.split())

    def contains_keyword(self, keyword: str) -> bool:
        """Verifica si la descripción contiene una palabra clave."""
        if self.is_empty():
            return False
        return keyword.lower() in self.value.lower()

    def __str__(self) -> str:
        return self.value

    def __len__(self) -> int:
        return len(self.value)


# Alias para compatibilidad hacia atrás
SourceDescription = RssFeedDescription
