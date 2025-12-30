"""Value Object para colección de keywords de artículos."""

from dataclasses import dataclass
from typing import FrozenSet, Iterator, List


@dataclass(frozen=True)
class KeywordCollection:
    """
    Value Object que representa una colección inmutable de keywords.

    Encapsula validación, normalización y operaciones sobre keywords.
    Las keywords se almacenan en lowercase y sin duplicados.

    Específico del bounded context de Article para análisis de contenido.
    """

    keywords: FrozenSet[str]

    def __post_init__(self):
        """Valida y normaliza las keywords."""
        # Validar y normalizar keywords
        validated = set()

        for kw in self.keywords:
            if not isinstance(kw, str):
                raise TypeError(f"Keyword debe ser string, recibido: {type(kw)}")

            # Normalizar: strip, lowercase, validar longitud
            normalized = kw.strip().lower()

            if len(normalized) >= 2:  # Mínimo 2 caracteres
                validated.add(normalized)

        # Reemplazar con keywords validadas
        object.__setattr__(self, "keywords", frozenset(validated))

    @classmethod
    def from_list(cls, keywords: List[str]) -> "KeywordCollection":
        """
        Crea una colección desde una lista de keywords.

        Args:
            keywords: Lista de keywords (pueden tener duplicados)

        Returns:
            KeywordCollection con keywords únicas y normalizadas
        """
        return cls(frozenset(keywords))

    @classmethod
    def empty(cls) -> "KeywordCollection":
        """
        Crea una colección vacía.

        Returns:
            KeywordCollection sin keywords
        """
        return cls(frozenset())

    @property
    def count(self) -> int:
        """
        Obtiene el número de keywords.

        Returns:
            Cantidad de keywords en la colección
        """
        return len(self.keywords)

    def is_empty(self) -> bool:
        """
        Verifica si la colección está vacía.

        Returns:
            True si no hay keywords
        """
        return len(self.keywords) == 0

    def contains(self, keyword: str) -> bool:
        """
        Verifica si contiene una keyword específica.

        Args:
            keyword: Keyword a buscar (case-insensitive)

        Returns:
            True si la keyword está en la colección
        """
        return keyword.strip().lower() in self.keywords

    def to_list(self) -> List[str]:
        """
        Convierte a lista ordenada alfabéticamente.

        Returns:
            Lista de keywords ordenadas
        """
        return sorted(list(self.keywords))

    def to_csv(self) -> str:
        """
        Convierte a string CSV.

        Returns:
            Keywords separadas por comas
        """
        return ", ".join(self.to_list())

    def add(self, keyword: str) -> "KeywordCollection":
        """
        Agrega una keyword (retorna nueva colección).

        Args:
            keyword: Keyword a agregar

        Returns:
            Nueva KeywordCollection con la keyword agregada
        """
        normalized = keyword.strip().lower()
        if len(normalized) < 2:
            return self

        new_keywords = set(self.keywords)
        new_keywords.add(normalized)
        return KeywordCollection(frozenset(new_keywords))

    def remove(self, keyword: str) -> "KeywordCollection":
        """
        Remueve una keyword (retorna nueva colección).

        Args:
            keyword: Keyword a remover

        Returns:
            Nueva KeywordCollection sin la keyword
        """
        normalized = keyword.strip().lower()
        new_keywords = set(self.keywords)
        new_keywords.discard(normalized)
        return KeywordCollection(frozenset(new_keywords))

    def merge(self, other: "KeywordCollection") -> "KeywordCollection":
        """
        Combina con otra colección (unión).

        Args:
            other: Otra KeywordCollection

        Returns:
            Nueva KeywordCollection con keywords de ambas
        """
        merged = self.keywords | other.keywords
        return KeywordCollection(merged)

    def intersect(self, other: "KeywordCollection") -> "KeywordCollection":
        """
        Obtiene keywords comunes (intersección).

        Args:
            other: Otra KeywordCollection

        Returns:
            Nueva KeywordCollection con keywords comunes
        """
        common = self.keywords & other.keywords
        return KeywordCollection(common)

    def filter_by_prefix(self, prefix: str) -> "KeywordCollection":
        """
        Filtra keywords que empiezan con un prefijo.

        Args:
            prefix: Prefijo a buscar (case-insensitive)

        Returns:
            Nueva KeywordCollection con keywords filtradas
        """
        prefix_lower = prefix.lower()
        filtered = {kw for kw in self.keywords if kw.startswith(prefix_lower)}
        return KeywordCollection(frozenset(filtered))

    def __iter__(self) -> Iterator[str]:
        """Permite iterar sobre las keywords."""
        return iter(sorted(self.keywords))

    def __len__(self) -> int:
        """Permite usar len() sobre la colección."""
        return len(self.keywords)

    def __contains__(self, keyword: str) -> bool:
        """Permite usar 'in' operator."""
        return self.contains(keyword)

    def __str__(self) -> str:
        """Representación en string."""
        return self.to_csv()

    def __repr__(self) -> str:
        """Representación para debugging."""
        return (
            f"KeywordCollection(count={self.count}, keywords={self.to_list()[:5]}...)"
        )
