"""RssFeedMetadata Value Object - Metadatos descriptivos del RssFeed."""

from dataclasses import dataclass
from typing import Optional

from src.rss.feed.domain.value_objects.description import RssFeedDescription
from src.rss.feed.domain.value_objects.name import RssFeedName
from src.shared.domain.value_objects import TagCollection


@dataclass(frozen=True)
class RssFeedMetadata:
    """
    Value Object compuesto para metadatos del RssFeed.

    Agrupa todos los campos descriptivos y de clasificación
    del RssFeed aggregate.

    Attributes:
        name: Nombre descriptivo de la fuente
        description: Descripción opcional de la fuente
        category: Categoría opcional de la fuente
        tags: Colección de tags para clasificación
        source_type: Tipo de fuente (rss, atom, etc.)
    """

    name: RssFeedName
    description: Optional[RssFeedDescription]
    category: Optional[str]
    tags: TagCollection
    source_type: str

    @classmethod
    def create(
        cls,
        name: RssFeedName,
        description: Optional[RssFeedDescription] = None,
        category: Optional[str] = None,
        tags: Optional[TagCollection] = None,
        source_type: str = "rss",
    ) -> "RssFeedMetadata":
        """
        Crea nueva instancia de RssFeedMetadata.

        Args:
            name: Nombre descriptivo de la fuente
            description: Descripción opcional
            category: Categoría opcional
            tags: Colección de tags (default: vacía)
            source_type: Tipo de fuente (default: "rss")

        Returns:
            Nueva instancia de RssFeedMetadata
        """
        return cls(
            name=name,
            description=description,
            category=category,
            tags=tags or TagCollection(tags=frozenset()),
            source_type=source_type,
        )

    def with_name(self, name: RssFeedName) -> "RssFeedMetadata":
        """
        Crea nueva instancia con nombre actualizado.

        Args:
            name: Nuevo nombre

        Returns:
            Nueva instancia con nombre actualizado
        """
        return RssFeedMetadata(
            name=name,
            description=self.description,
            category=self.category,
            tags=self.tags,
            source_type=self.source_type,
        )

    def with_description(
        self, description: Optional[RssFeedDescription]
    ) -> "RssFeedMetadata":
        """
        Crea nueva instancia con descripción actualizada.

        Args:
            description: Nueva descripción

        Returns:
            Nueva instancia con descripción actualizada
        """
        return RssFeedMetadata(
            name=self.name,
            description=description,
            category=self.category,
            tags=self.tags,
            source_type=self.source_type,
        )

    def with_category(self, category: Optional[str]) -> "RssFeedMetadata":
        """
        Crea nueva instancia con categoría actualizada.

        Args:
            category: Nueva categoría

        Returns:
            Nueva instancia con categoría actualizada
        """
        return RssFeedMetadata(
            name=self.name,
            description=self.description,
            category=category,
            tags=self.tags,
            source_type=self.source_type,
        )

    def with_tags(self, tags: TagCollection) -> "RssFeedMetadata":
        """
        Crea nueva instancia con tags actualizados.

        Args:
            tags: Nueva colección de tags

        Returns:
            Nueva instancia con tags actualizados
        """
        return RssFeedMetadata(
            name=self.name,
            description=self.description,
            category=self.category,
            tags=tags,
            source_type=self.source_type,
        )


# Alias para compatibilidad hacia atrás
SourceMetadata = RssFeedMetadata
