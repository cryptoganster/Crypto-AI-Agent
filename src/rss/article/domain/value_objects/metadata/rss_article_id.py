"""RssArticleId Value Object."""

import uuid
from typing import Optional

from src.shared.kernel.value_object import IValueObject


class RssArticleId(IValueObject):
    """
    Value Object para ID único de RssArticle.

    Genera IDs determinísticos basados en source_id + url para evitar duplicados.
    """

    def __init__(self, value: str):
        """
        Inicializa RssArticleId con validación.

        Args:
            value: UUID string válido o UUID object

        Raises:
            ValueError: Si el ID no es válido
        """
        # Convertir UUID a string si es necesario
        if isinstance(value, uuid.UUID):
            value = str(value)

        if not value or not isinstance(value, str):
            raise ValueError("RssArticleId value debe ser string no vacío")

        # Validar que es UUID válido
        try:
            uuid.UUID(value)
        except ValueError:
            raise ValueError(f"RssArticleId debe ser UUID válido: {value}")

        self._value: str = value

    @property
    def value(self) -> str:
        """Valor del ID."""
        return self._value

    @classmethod
    def from_string(cls, value: str) -> "RssArticleId":
        """Crea RssArticleId desde string UUID."""
        return cls(value)

    @staticmethod
    def generate() -> "RssArticleId":
        """Genera nuevo RssArticleId aleatorio."""
        return RssArticleId(str(uuid.uuid4()))

    @staticmethod
    def from_source_and_url(source_id: str, url: str) -> "RssArticleId":
        """
        Genera RssArticleId determinístico basado en source + url.

        Esto previene duplicados ya que la misma URL de la misma source
        siempre genera el mismo RssArticleId.

        Args:
            source_id: ID de la source RSS
            url: URL del artículo

        Returns:
            RssArticleId determinístico

        Raises:
            ValueError: Si source_id o url son inválidos
        """
        if not source_id or not isinstance(source_id, str):
            raise ValueError("source_id debe ser string no vacío")
        if not url or not isinstance(url, str):
            raise ValueError("url debe ser string no vacía")

        # Crear hash determinístico usando namespace UUID
        hash_input = f"{source_id}:{url.strip()}"
        article_uuid = str(uuid.uuid5(uuid.NAMESPACE_URL, hash_input))
        return RssArticleId(article_uuid)

    def __str__(self) -> str:
        return self._value

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, RssArticleId):
            return False
        return self._value == other._value

    def __hash__(self) -> int:
        return hash(self._value)

    @classmethod
    def from_dict(cls, data: dict) -> "RssArticleId":
        """Crea RssArticleId desde diccionario."""
        if not isinstance(data, dict) or "value" not in data:
            raise ValueError("Data debe ser dict con key 'value'")
        return cls(data["value"])

    def to_dict(self) -> dict:
        """Convierte RssArticleId a diccionario."""
        return {"value": self._value}


# Alias para compatibilidad
ArticleId = RssArticleId
