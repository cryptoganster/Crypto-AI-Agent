"""
Value Object para URLs de artículos RSS.
Encapsula validación y normalización de URLs.
"""

import re
from dataclasses import dataclass
from urllib.parse import urlparse, urlunparse

from src.shared.kernel.value_object import IValueObject


@dataclass(frozen=True)
class RssArticleUrl(IValueObject):
    """Value Object para URLs de artículos RSS con validaciones."""

    value: str

    def __post_init__(self):
        """Validación post-inicialización."""
        if not self.value:
            raise ValueError("URL del artículo no puede estar vacía")

        if len(self.value.strip()) == 0:
            raise ValueError("URL del artículo no puede ser solo espacios")

        # Validación básica de formato URL
        if not self._is_valid_url(self.value):
            raise ValueError(f"URL inválida: {self.value}")

        # Normalizar URL (eliminar espacios, convertir a minúsculas dominio)
        normalized = self._normalize_url(self.value.strip())
        object.__setattr__(self, "value", normalized)

    def _is_valid_url(self, url: str) -> bool:
        """Valida formato básico de URL."""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc]) and result.scheme in [
                "http",
                "https",
            ]
        except Exception:
            return False

    def _normalize_url(self, url: str) -> str:
        """Normaliza URL para consistencia."""
        try:
            parsed = urlparse(url)
            # Normalizar: scheme y netloc en minúsculas, path sin cambios
            normalized = urlunparse(
                (
                    parsed.scheme.lower(),
                    parsed.netloc.lower(),
                    parsed.path,
                    parsed.params,
                    parsed.query,
                    "",  # Eliminar fragment (#) para canonicalización
                )
            )
            return normalized
        except Exception:
            return url

    @classmethod
    def create(cls, url: str) -> "RssArticleUrl":
        """Factory method para crear URL."""
        return cls(url)

    @classmethod
    def try_create(cls, url: str) -> "RssArticleUrl | None":
        """Intenta crear URL, retorna None si es inválida."""
        try:
            return cls(url)
        except ValueError:
            return None

    def get_domain(self) -> str:
        """Extrae el dominio de la URL."""
        parsed = urlparse(self.value)
        return parsed.netloc

    def get_scheme(self) -> str:
        """Obtiene el esquema (http/https)."""
        parsed = urlparse(self.value)
        return parsed.scheme

    def is_secure(self) -> bool:
        """Verifica si usa HTTPS."""
        return self.get_scheme() == "https"

    def get_path(self) -> str:
        """Obtiene el path de la URL."""
        parsed = urlparse(self.value)
        return parsed.path

    def matches_domain(self, domain: str) -> bool:
        """Verifica si la URL pertenece al dominio especificado."""
        return self.get_domain().lower() == domain.lower()

    def __str__(self) -> str:
        return self.value

    def __len__(self) -> int:
        return len(self.value)


# Alias para compatibilidad
ArticleUrl = RssArticleUrl
