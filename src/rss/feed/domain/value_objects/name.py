"""
Value Object para nombres de fuentes RSS.
Encapsula validación y normalización de nombres de sources.
"""

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class RssFeedName:
    """Value Object para nombres de fuentes RSS."""

    value: str

    def __post_init__(self):
        """Validación post-inicialización."""
        if not self.value:
            raise ValueError("Nombre de la fuente RSS no puede estar vacío")

        if len(self.value.strip()) == 0:
            raise ValueError("Nombre de la fuente RSS no puede ser solo espacios")

        if len(self.value) > 200:
            raise ValueError("Nombre de la fuente RSS no puede exceder 200 caracteres")

        # Normalizar nombre (eliminar espacios extra, capitalizar apropiadamente)
        normalized = re.sub(r"\s+", " ", self.value.strip())
        object.__setattr__(self, "value", normalized)

    @classmethod
    def create_from_url(cls, url: str) -> "RssFeedName":
        """Factory method para crear nombre desde URL."""
        try:
            from urllib.parse import urlparse

            parsed = urlparse(url)
            domain = parsed.netloc or parsed.path

            # Limpiar dominio
            domain = (
                domain.replace("www.", "")
                .replace(".com", "")
                .replace(".org", "")
                .replace(".net", "")
            )

            # Capitalizar primera letra
            if domain:
                return cls(domain.capitalize() + " RSS Feed")
            else:
                return cls("RSS Feed")
        except Exception:
            return cls("RSS Feed")

    @classmethod
    def create_default(cls, fallback_text: str = "Unnamed RSS Source") -> "RssFeedName":
        """Factory method para crear nombre por defecto."""
        return cls(fallback_text)

    def get_short_name(self, max_length: int = 50) -> str:
        """Obtiene versión corta del nombre."""
        if len(self.value) <= max_length:
            return self.value
        return self.value[: max_length - 3] + "..."

    def contains_keyword(self, keyword: str) -> bool:
        """Verifica si el nombre contiene una palabra clave."""
        return keyword.lower() in self.value.lower()

    def is_generic(self) -> bool:
        """Detecta nombres genéricos."""
        generic_patterns = [
            r"^rss\s+feed$",
            r"^feed\s*\d*$",
            r"^source\s*\d*$",
            r"^unnamed",
            r"^untitled",
        ]

        name_lower = self.value.lower()
        return any(re.search(pattern, name_lower) for pattern in generic_patterns)

    def __str__(self) -> str:
        return self.value

    def __len__(self) -> int:
        return len(self.value)


# Alias para compatibilidad hacia atrás
SourceName = RssFeedName
