"""
Value Object para hash de contenido en detección de duplicados.

Encapsula operaciones de hashing de contenido con diferentes algoritmos.
"""

import hashlib
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional

from src.shared.kernel import IValueObject


class ContentHashAlgorithm(Enum):
    """Algoritmos disponibles para generar hashes de contenido."""

    MD5 = "md5"
    SHA256 = "sha256"
    SHA1 = "sha1"


@dataclass(frozen=True)
class ContentHash:
    """
    Value Object para hash de contenido usado en detección de duplicados.

    Reglas de negocio:
    - Hash inmutable generado desde contenido
    - Soporte múltiples algoritmos de hash
    - Validación de formato de hash
    - Comparación eficiente para detección de duplicados
    """

    hash_value: str
    algorithm: ContentHashAlgorithm
    source_length: Optional[int] = None  # Longitud del contenido original

    def __post_init__(self):
        """Validación en construcción."""
        if not isinstance(self.hash_value, str) or not self.hash_value.strip():
            raise ValueError("Hash value no puede estar vacío")

        if not isinstance(self.algorithm, ContentHashAlgorithm):
            raise ValueError("Algorithm debe ser ContentHashAlgorithm válido")

        # Validar formato del hash según algoritmo
        self._validate_hash_format()

        if self.source_length is not None and self.source_length < 0:
            raise ValueError("Source length no puede ser negativo")

    def _validate_hash_format(self) -> None:
        """Valida formato del hash según el algoritmo."""
        expected_lengths = {
            ContentHashAlgorithm.MD5: 32,
            ContentHashAlgorithm.SHA1: 40,
            ContentHashAlgorithm.SHA256: 64,
        }

        expected_length = expected_lengths[self.algorithm]
        if len(self.hash_value) != expected_length:
            raise ValueError(
                f"Hash {self.algorithm.value} debe tener {expected_length} caracteres, "
                f"recibido: {len(self.hash_value)}"
            )

        # Validar que solo contenga caracteres hexadecimales
        try:
            int(self.hash_value, 16)
        except ValueError:
            raise ValueError(
                f"Hash debe contener solo caracteres hexadecimales: {self.hash_value}"
            )

    @classmethod
    def from_content(
        cls,
        content: str,
        algorithm: ContentHashAlgorithm = ContentHashAlgorithm.SHA256,
        include_length: bool = True,
    ) -> "ContentHash":
        """Crea hash desde contenido de texto."""
        if not isinstance(content, str):
            raise ValueError("Content debe ser string")

        # Normalizar contenido (remover espacios extra, convertir a lowercase)
        normalized_content = " ".join(content.lower().split())

        # Generar hash
        content_bytes = normalized_content.encode("utf-8")

        if algorithm == ContentHashAlgorithm.MD5:
            hash_obj = hashlib.md5(content_bytes)
        elif algorithm == ContentHashAlgorithm.SHA1:
            hash_obj = hashlib.sha1(content_bytes)
        elif algorithm == ContentHashAlgorithm.SHA256:
            hash_obj = hashlib.sha256(content_bytes)
        else:
            raise ValueError(f"Algoritmo no soportado: {algorithm}")

        hash_value = hash_obj.hexdigest()
        source_length = len(content) if include_length else None

        return cls(hash_value, algorithm, source_length)

    @classmethod
    def from_url_and_title(
        cls,
        url: str,
        title: str,
        algorithm: ContentHashAlgorithm = ContentHashAlgorithm.SHA256,
    ) -> "ContentHash":
        """Crea hash combinando URL y título (útil para artículos RSS)."""
        if not url or not title:
            raise ValueError("URL y title son requeridos")

        # Combinar URL y título normalizado
        combined_content = f"{url.strip().lower()}|{title.strip().lower()}"
        return cls.from_content(combined_content, algorithm, include_length=False)

    @classmethod
    def from_multiple_fields(
        cls,
        fields: dict[str, str],
        algorithm: ContentHashAlgorithm = ContentHashAlgorithm.SHA256,
    ) -> "ContentHash":
        """Crea hash desde múltiples campos (estrategia MULTI_FIELD)."""
        if not fields:
            raise ValueError("Fields dict no puede estar vacío")

        # Ordenar campos por clave para consistencia
        sorted_fields = sorted(fields.items())
        combined_content = "|".join(
            f"{k}:{v.strip().lower()}" for k, v in sorted_fields if v
        )

        return cls.from_content(combined_content, algorithm, include_length=False)

    def matches(self, other: "ContentHash") -> bool:
        """Verifica si coincide con otro hash."""
        if not isinstance(other, ContentHash):
            return False

        # Deben tener mismo algoritmo para comparar
        if self.algorithm != other.algorithm:
            return False

        return self.hash_value == other.hash_value

    def is_same_algorithm(self, other: "ContentHash") -> bool:
        """Verifica si usa el mismo algoritmo."""
        return isinstance(other, ContentHash) and self.algorithm == other.algorithm

    @property
    def short_hash(self) -> str:
        """Versión corta del hash (primeros 8 caracteres)."""
        return self.hash_value[:8]

    @property
    def is_md5(self) -> bool:
        """Indica si es hash MD5."""
        return self.algorithm == ContentHashAlgorithm.MD5

    @property
    def is_sha256(self) -> bool:
        """Indica si es hash SHA256."""
        return self.algorithm == ContentHashAlgorithm.SHA256

    @property
    def is_secure_algorithm(self) -> bool:
        """Indica si usa algoritmo seguro (no MD5)."""
        return self.algorithm != ContentHashAlgorithm.MD5

    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario."""
        result: Dict[str, Any] = {
            "hash_value": self.hash_value,
            "algorithm": self.algorithm.value,
            "short_hash": self.short_hash,
        }
        if self.source_length is not None:
            result["source_length"] = self.source_length
        return result

    def __str__(self) -> str:
        """Representación string."""
        length_info = f" ({self.source_length} chars)" if self.source_length else ""
        return f"ContentHash({self.algorithm.value}:{self.short_hash}...{length_info})"

    def __eq__(self, other) -> bool:
        """Igualdad basada en hash y algoritmo."""
        return (
            isinstance(other, ContentHash)
            and self.hash_value == other.hash_value
            and self.algorithm == other.algorithm
        )

    def __hash__(self) -> int:
        """Hash para usar en sets/dicts."""
        return hash((self.hash_value, self.algorithm))
