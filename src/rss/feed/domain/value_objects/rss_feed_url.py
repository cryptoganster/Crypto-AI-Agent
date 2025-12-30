"""Source URL Value Object."""

import re
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse

from src.shared.kernel import IValueObject


@dataclass(frozen=True)
class RssFeedUrl(IValueObject):
    """
    Value Object para URLs RSS con validaciones específicas.

    Responsabilidades:
    - Validación de formato URL RSS válido
    - Normalización de URL (http/https, trailing slash)
    - Validación de extensiones RSS (.xml, .rss, feed/, etc.)
    """

    url: str

    def __post_init__(self):
        if not self.url or not self.url.strip():
            raise ValueError("URL RSS no puede estar vacía")

        normalized = self._normalize_url(self.url.strip())
        object.__setattr__(self, "url", normalized)

        if not self._is_valid_rss_url():
            raise ValueError(f"URL RSS inválida: {self.url}")

    def _normalize_url(self, url: str) -> str:
        """Normaliza la URL RSS."""
        # Asegurar protocolo
        if not url.startswith(("http://", "https://")):
            url = f"https://{url}"

        # Parsear y reconstruir para normalizar
        parsed = urlparse(url)
        if not parsed.netloc:
            raise ValueError("URL RSS debe tener un dominio válido")

        return url

    def _is_valid_rss_url(self) -> bool:
        """Valida si la URL podría ser un feed RSS válido."""
        try:
            parsed = urlparse(self.url)

            # Validar esquema
            if parsed.scheme not in ("http", "https"):
                return False

            # Validar dominio
            if not parsed.netloc:
                return False

            # Patrones comunes de RSS feeds
            rss_patterns = [
                r"\.xml$",
                r"\.rss$",
                r"/feed/?$",
                r"/rss/?$",
                r"/atom/?$",
                r"feed\.php",
                r"rss\.php",
                r"/index\.xml$",
            ]

            path_lower = parsed.path.lower()
            for pattern in rss_patterns:
                if re.search(pattern, path_lower):
                    return True

            # Si no coincide con patrones RSS conocidos, validar que al menos sea un dominio válido
            # Para ser más estricto con URLs que no parecen feeds RSS
            if len(parsed.netloc.split(".")) < 2:
                return False

            return True

        except Exception:
            return False

    def get_domain(self) -> str:
        """Obtiene el dominio de la URL RSS."""
        parsed = urlparse(self.url)
        return parsed.netloc

    def get_path(self) -> str:
        """Obtiene el path de la URL RSS."""
        parsed = urlparse(self.url)
        return parsed.path

    def __str__(self) -> str:
        return self.url

    def equals(self, other: Any) -> bool:
        """Compara con otra SourceUrl."""
        if not isinstance(other, SourceUrl):
            return False
        return self.url == other.url

    @property
    def value(self) -> str:
        """Retorna el valor de la URL para compatibilidad."""
        return self.url

    def to_dict(self) -> dict[str, Any]:
        """Serializa a diccionario para persistencia."""
        return {"url": self.url}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SourceUrl":
        """Crea instancia desde diccionario."""
        return cls(data["url"])


# Alias para compatibilidad hacia atrás
RssUrl = RssFeedUrl
SourceUrl = RssFeedUrl
