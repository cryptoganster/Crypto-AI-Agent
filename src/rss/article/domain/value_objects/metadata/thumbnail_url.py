"""Value Object para URL de thumbnail de artículo."""

from dataclasses import dataclass
from typing import Optional
from urllib.parse import urlparse


@dataclass(frozen=True)
class ArticleThumbnailUrl:
    """
    Value Object para URL de imagen thumbnail de artículo.

    Encapsula validaciones y reglas de negocio para thumbnails.
    Thumbnails son extraídos durante fetch RSS de campos estándar:
    - media:thumbnail (Media RSS)
    - enclosures tipo imagen (RSS 2.0)
    - media:content (Media RSS)

    Características:
    - Inmutable (frozen=True)
    - Validación de formato URL
    - Opcional (puede ser None)
    """

    value: Optional[str]

    def __post_init__(self):
        """Validar thumbnail URL al crear instancia."""
        if self.value is not None:
            # Validar que no esté vacío
            if not isinstance(self.value, str) or not self.value.strip():
                object.__setattr__(self, "value", None)
                return

            # Validar formato URL básico
            value_stripped = self.value.strip()
            if not value_stripped.startswith(("http://", "https://")):
                raise ValueError(
                    f"Thumbnail URL debe comenzar con http:// o https://: {value_stripped}"
                )

            # Validar que sea parseable
            try:
                parsed = urlparse(value_stripped)
                if not parsed.netloc:
                    raise ValueError(
                        f"Thumbnail URL sin dominio válido: {value_stripped}"
                    )
            except Exception as e:
                raise ValueError(f"Thumbnail URL malformada: {value_stripped}") from e

            # Normalizar: guardar URL limpia
            object.__setattr__(self, "value", value_stripped)

    @classmethod
    def create(cls, url: Optional[str]) -> "ArticleThumbnailUrl":
        """
        Factory method para crear ArticleThumbnailUrl con validación.

        Args:
            url: URL del thumbnail (puede ser None o string vacío)

        Returns:
            ArticleThumbnailUrl con value=None si URL inválida o vacía
        """
        if url is None or (isinstance(url, str) and not url.strip()):
            return cls(value=None)

        try:
            return cls(value=url)
        except ValueError:
            # Si validación falla, retornar con value=None (thumbnail opcional)
            return cls(value=None)

    @property
    def is_present(self) -> bool:
        """Indica si hay thumbnail disponible."""
        return self.value is not None and len(self.value) > 0

    @property
    def domain(self) -> Optional[str]:
        """Extrae dominio de la URL del thumbnail."""
        if not self.is_present:
            return None

        try:
            parsed = urlparse(self.value)
            return parsed.netloc
        except Exception:
            return None

    def __str__(self) -> str:
        """Representación string del thumbnail URL."""
        return self.value if self.value else ""

    def __repr__(self) -> str:
        """Representación para debugging."""
        if self.is_present:
            return f"ArticleThumbnailUrl('{self.value}')"
        return "ArticleThumbnailUrl(None)"
