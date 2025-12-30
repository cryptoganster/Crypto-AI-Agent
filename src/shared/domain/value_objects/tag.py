"""Tag Value Objects - Transversal para clasificación."""

import re
from dataclasses import dataclass
from typing import FrozenSet, Iterator, List, Optional

from src.shared.kernel import IValueObject


@dataclass(frozen=True)
class Tag(IValueObject):
    """
    Value Object para un tag individual.

    Representa una etiqueta de clasificación normalizada.
    Usado transversalmente en múltiples bounded contexts.
    """

    value: str

    def __post_init__(self):
        """Valida y normaliza el tag."""
        if not self.value or not isinstance(self.value, str):
            raise ValueError("Tag value debe ser string no vacío")

        normalized = self.value.strip().lower()

        if len(normalized) < 2 or len(normalized) > 50:
            raise ValueError("Tag debe tener entre 2 y 50 caracteres")

        # Validar caracteres permitidos (letras, números, guiones, espacios)
        if not re.match(r"^[a-zA-Z0-9\s\-_]+$", normalized):
            raise ValueError("Tag contiene caracteres no permitidos")

        # Normalizar espacios múltiples
        normalized = re.sub(r"\s+", " ", normalized)

        object.__setattr__(self, "value", normalized)

    def __str__(self) -> str:
        return self.value

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Tag):
            return False
        return self.value == other.value

    def __hash__(self) -> int:
        return hash(self.value)


@dataclass(frozen=True)
class TagCollection(IValueObject):
    """
    Colección inmutable de tags para clasificación transversal.

    Value Object usado en múltiples bounded contexts (Source, Article)
    para clasificación y organización mediante etiquetas.
    """

    tags: FrozenSet[str]

    def __post_init__(self):
        """Validar y normalizar tags."""
        if not isinstance(self.tags, (set, frozenset, list)):
            raise ValueError("Tags must be a collection")

        validated_tags = set()
        for tag in self.tags:
            normalized_tag = self._normalize_tag(tag)
            if normalized_tag:
                validated_tags.add(normalized_tag)

        # Actualizar con tags validados
        object.__setattr__(self, "tags", frozenset(validated_tags))

    @classmethod
    def create(cls, tags: List[str]) -> "TagCollection":
        """Factory method para crear TagCollection con validación."""
        return cls.from_list(tags)

    @classmethod
    def empty(cls) -> "TagCollection":
        """Crea colección vacía."""
        return cls(frozenset())

    @classmethod
    def from_list(cls, tag_list: List[str]) -> "TagCollection":
        """Crea colección desde lista de strings."""
        return cls(frozenset(tag_list))

    @classmethod
    def from_text(cls, text: str, separator: str = ",") -> "TagCollection":
        """Extrae tags de texto separado."""
        if not text or not text.strip():
            return cls.empty()

        tags = [tag.strip() for tag in text.split(separator)]
        return cls.from_list(tags)

    def _normalize_tag(self, tag: str) -> Optional[str]:
        """Normaliza un tag individual."""
        if not isinstance(tag, str):
            return None

        # Limpiar y normalizar
        cleaned = tag.strip().lower()

        # Validar longitud
        if len(cleaned) < 2 or len(cleaned) > 50:
            return None

        # Validar caracteres (solo letras, números, guiones y espacios)
        if not re.match(r"^[a-zA-Z0-9\s\-_]+$", cleaned):
            return None

        # Normalizar espacios múltiples
        normalized = re.sub(r"\s+", " ", cleaned)

        return normalized

    def add(self, *tags: str) -> "TagCollection":
        """Añade tags y retorna nueva colección."""
        new_tags = set(self.tags)

        for tag in tags:
            normalized = self._normalize_tag(tag)
            if normalized:
                new_tags.add(normalized)

        return TagCollection(frozenset(new_tags))

    def remove(self, *tags: str) -> "TagCollection":
        """Remueve tags y retorna nueva colección."""
        tags_to_remove = {
            normalized_tag
            for tag in tags
            if (normalized_tag := self._normalize_tag(tag)) is not None
        }
        new_tags = self.tags - tags_to_remove
        return TagCollection(new_tags)

    def filter_by_pattern(self, pattern: str) -> "TagCollection":
        """Filtra tags que coinciden con patrón regex."""
        try:
            regex = re.compile(pattern, re.IGNORECASE)
            filtered_tags = {tag for tag in self.tags if regex.search(tag)}
            return TagCollection(frozenset(filtered_tags))
        except re.error:
            return TagCollection(frozenset())

    def merge(self, other: "TagCollection") -> "TagCollection":
        """Fusiona con otra colección."""
        if not isinstance(other, TagCollection):
            raise ValueError("Can only merge with another TagCollection")

        merged_tags = self.tags | other.tags
        return TagCollection(merged_tags)

    def intersect(self, other: "TagCollection") -> "TagCollection":
        """Intersección con otra colección."""
        if not isinstance(other, TagCollection):
            raise ValueError("Can only intersect with another TagCollection")

        intersected_tags = self.tags & other.tags
        return TagCollection(intersected_tags)

    @property
    def is_empty(self) -> bool:
        """Indica si la colección está vacía."""
        return len(self.tags) == 0

    @property
    def count(self) -> int:
        """Número de tags."""
        return len(self.tags)

    @property
    def sorted_tags(self) -> List[str]:
        """Tags ordenados alfabéticamente."""
        return sorted(self.tags)

    def contains(self, tag: str) -> bool:
        """Verifica si contiene un tag específico."""
        normalized = self._normalize_tag(tag)
        return normalized in self.tags if normalized else False

    def get_most_common_words(self, limit: int = 10) -> List[str]:
        """Extrae palabras más comunes de los tags."""
        word_count = {}

        for tag in self.tags:
            words = tag.split()
            for word in words:
                if len(word) > 2:  # Ignorar palabras muy cortas
                    word_count[word] = word_count.get(word, 0) + 1

        # Ordenar por frecuencia
        sorted_words = sorted(word_count.items(), key=lambda x: x[1], reverse=True)
        return [word for word, _ in sorted_words[:limit]]

    def to_hashtags(self) -> List[str]:
        """Convierte tags a hashtags para redes sociales."""
        hashtags = []
        for tag in self.tags:
            # Remover espacios y caracteres especiales para hashtags
            hashtag = re.sub(r"[^\w]", "", tag)
            if len(hashtag) >= 2:
                hashtags.append(f"#{hashtag}")

        return sorted(hashtags)

    def to_csv(self, separator: str = ", ") -> str:
        """Convierte a string separado por comas."""
        return separator.join(self.sorted_tags)

    def __iter__(self) -> Iterator[str]:
        """Permite iteración."""
        return iter(self.sorted_tags)

    def __len__(self) -> int:
        """Longitud de la colección."""
        return len(self.tags)

    def __contains__(self, tag: str) -> bool:
        """Operador 'in'."""
        return self.contains(tag)

    def __bool__(self) -> bool:
        """Evaluación booleana."""
        return not self.is_empty

    def __str__(self) -> str:
        return f"TagCollection({self.count} tags)"

    def __repr__(self) -> str:
        tags_preview = ", ".join(list(self.tags)[:3])
        if len(self.tags) > 3:
            tags_preview += f"... (+{len(self.tags) - 3} more)"
        return f"TagCollection([{tags_preview}])"
