"""Value Object para embeddings vectoriales normalizados."""

from dataclasses import dataclass
from typing import List

import numpy as np

# Constantes para validación
DEFAULT_DIMENSION = 768
"""Dimensión por defecto para nomic-embed-text."""

MIN_DIMENSION = 1
"""Dimensión mínima válida."""

MAX_DIMENSION = 10000
"""Dimensión máxima razonable."""

NORMALIZATION_TOLERANCE = 1e-5
"""Tolerancia para verificar normalización (magnitud ≈ 1.0)."""


@dataclass(frozen=True)
class VectorEmbedding:
    """
    Value Object para embedding vectorial normalizado.

    Representa un vector de embeddings normalizado (magnitud = 1.0) que captura
    el significado semántico de un texto. Compatible con modelos como nomic-embed-text.

    Attributes:
        vector: Array numpy con el vector (shape: (dimension,))
        model: Nombre del modelo usado (ej: "nomic-embed-text", "text-embedding-ada-002")
        dimension: Dimensión del vector (ej: 768, 1536)

    Examples:
        >>> import numpy as np
        >>> vec = np.array([0.1, 0.2, 0.3])
        >>> vec = vec / np.linalg.norm(vec)  # Normalizar
        >>> embedding = VectorEmbedding(vector=vec, model="test", dimension=3)
        >>> embedding.is_normalized()
        True
        >>> embedding.magnitude()
        1.0
    """

    vector: np.ndarray
    model: str
    dimension: int

    def __post_init__(self):
        """Valida que el embedding sea válido y esté normalizado."""
        # Validar tipo de vector
        if not isinstance(self.vector, np.ndarray):
            raise TypeError(
                f"Vector debe ser numpy.ndarray, recibido: {type(self.vector)}"
            )

        # Validar dimensión
        if not isinstance(self.dimension, int):
            raise TypeError(f"Dimension debe ser int, recibido: {type(self.dimension)}")

        if not MIN_DIMENSION <= self.dimension <= MAX_DIMENSION:
            raise ValueError(
                f"Dimension debe estar entre {MIN_DIMENSION} y {MAX_DIMENSION}, "
                f"recibido: {self.dimension}"
            )

        # Validar shape del vector
        if self.vector.shape != (self.dimension,):
            raise ValueError(
                f"Shape del vector inválido: {self.vector.shape}, "
                f"esperado: ({self.dimension},)"
            )

        # Validar dtype (debe ser float)
        if not np.issubdtype(self.vector.dtype, np.floating):
            raise TypeError(
                f"Vector debe ser de tipo float, recibido: {self.vector.dtype}"
            )

        # Validar que no haya NaN o Inf
        if np.any(np.isnan(self.vector)):
            raise ValueError("Vector contiene valores NaN")

        if np.any(np.isinf(self.vector)):
            raise ValueError("Vector contiene valores infinitos")

        # Validar normalización (magnitud ≈ 1.0)
        magnitude = np.linalg.norm(self.vector)
        if not np.isclose(magnitude, 1.0, atol=NORMALIZATION_TOLERANCE):
            raise ValueError(
                f"Vector no está normalizado: magnitud={magnitude:.6f}, "
                f"esperado: 1.0 ± {NORMALIZATION_TOLERANCE}"
            )

        # Validar modelo
        if not isinstance(self.model, str) or not self.model:
            raise ValueError(
                f"Model debe ser un string no vacío, recibido: {self.model}"
            )

    def cosine_similarity(self, other: "VectorEmbedding") -> float:
        """
        Calcula similitud coseno con otro embedding.

        Para vectores normalizados, la similitud coseno es simplemente el producto punto.
        Rango: [-1, 1] donde 1 = idénticos, 0 = ortogonales, -1 = opuestos.

        Args:
            other: Otro VectorEmbedding

        Returns:
            Similitud coseno (float entre -1 y 1)

        Raises:
            ValueError: Si las dimensiones no coinciden

        Examples:
            >>> vec1 = VectorEmbedding(...)
            >>> vec2 = VectorEmbedding(...)
            >>> similarity = vec1.cosine_similarity(vec2)
            >>> 0.0 <= similarity <= 1.0
            True
        """
        if self.dimension != other.dimension:
            raise ValueError(
                f"No se pueden comparar embeddings con dimensiones diferentes: "
                f"{self.dimension} != {other.dimension}"
            )

        # Para vectores normalizados: cos(θ) = dot(a, b)
        similarity = float(np.dot(self.vector, other.vector))

        # Asegurar que esté en rango [-1, 1] (por errores de precisión numérica)
        return np.clip(similarity, -1.0, 1.0)

    def cosine_distance(self, other: "VectorEmbedding") -> float:
        """
        Calcula distancia coseno con otro embedding.

        Distancia coseno = 1 - similitud coseno
        Rango: [0, 2] donde 0 = idénticos, 1 = ortogonales, 2 = opuestos.

        Args:
            other: Otro VectorEmbedding

        Returns:
            Distancia coseno (float entre 0 y 2)
        """
        return 1.0 - self.cosine_similarity(other)

    def euclidean_distance(self, other: "VectorEmbedding") -> float:
        """
        Calcula distancia euclidiana con otro embedding.

        Args:
            other: Otro VectorEmbedding

        Returns:
            Distancia euclidiana (float >= 0)

        Raises:
            ValueError: Si las dimensiones no coinciden
        """
        if self.dimension != other.dimension:
            raise ValueError(
                f"No se pueden comparar embeddings con dimensiones diferentes: "
                f"{self.dimension} != {other.dimension}"
            )

        return float(np.linalg.norm(self.vector - other.vector))

    def magnitude(self) -> float:
        """
        Calcula la magnitud (norma L2) del vector.

        Para vectores normalizados, debería ser ≈ 1.0.

        Returns:
            Magnitud del vector
        """
        return float(np.linalg.norm(self.vector))

    def is_normalized(self, tolerance: float = NORMALIZATION_TOLERANCE) -> bool:
        """
        Verifica si el vector está normalizado.

        Args:
            tolerance: Tolerancia para la verificación

        Returns:
            True si magnitud ≈ 1.0
        """
        return np.isclose(self.magnitude(), 1.0, atol=tolerance)

    def to_list(self) -> List[float]:
        """
        Convierte el vector a lista de floats para serialización.

        Returns:
            Lista de floats

        Examples:
            >>> embedding = VectorEmbedding(...)
            >>> vec_list = embedding.to_list()
            >>> len(vec_list) == embedding.dimension
            True
        """
        return self.vector.tolist()

    def to_bytes(self) -> bytes:
        """
        Convierte el vector a bytes para almacenamiento eficiente.

        Returns:
            Bytes del vector
        """
        return self.vector.tobytes()

    @classmethod
    def from_list(
        cls, vector_list: List[float], model: str, normalize: bool = True
    ) -> "VectorEmbedding":
        """
        Crea VectorEmbedding desde una lista de floats.

        Args:
            vector_list: Lista de floats
            model: Nombre del modelo
            normalize: Si True, normaliza el vector automáticamente

        Returns:
            VectorEmbedding

        Raises:
            ValueError: Si la lista está vacía o contiene valores inválidos

        Examples:
            >>> vec_list = [0.1, 0.2, 0.3]
            >>> embedding = VectorEmbedding.from_list(vec_list, "test", normalize=True)
            >>> embedding.is_normalized()
            True
        """
        if not vector_list:
            raise ValueError("Lista de vector no puede estar vacía")

        vector = np.array(vector_list, dtype=np.float32)
        dimension = len(vector_list)

        # Normalizar si se solicita
        if normalize:
            magnitude = np.linalg.norm(vector)
            if magnitude == 0:
                raise ValueError("No se puede normalizar un vector de magnitud cero")
            vector = vector / magnitude

        return cls(vector=vector, model=model, dimension=dimension)

    @classmethod
    def from_bytes(
        cls, vector_bytes: bytes, model: str, dimension: int
    ) -> "VectorEmbedding":
        """
        Crea VectorEmbedding desde bytes.

        Args:
            vector_bytes: Bytes del vector
            model: Nombre del modelo
            dimension: Dimensión del vector

        Returns:
            VectorEmbedding
        """
        vector = np.frombuffer(vector_bytes, dtype=np.float32)

        if len(vector) != dimension:
            raise ValueError(
                f"Dimensión incorrecta: esperado {dimension}, "
                f"recibido {len(vector)}"
            )

        return cls(vector=vector, model=model, dimension=dimension)

    @classmethod
    def zero_vector(
        cls, model: str, dimension: int = DEFAULT_DIMENSION
    ) -> "VectorEmbedding":
        """
        Crea un vector de ceros normalizado (útil para casos especiales).

        Nota: Un vector de ceros no puede ser normalizado, así que se crea
        un vector con un pequeño valor en la primera posición.

        Args:
            model: Nombre del modelo
            dimension: Dimensión del vector

        Returns:
            VectorEmbedding con valores muy pequeños
        """
        vector = np.zeros(dimension, dtype=np.float32)
        vector[0] = 1.0  # Poner 1 en primera posición para poder normalizar
        vector = vector / np.linalg.norm(vector)

        return cls(vector=vector, model=model, dimension=dimension)

    def __str__(self) -> str:
        """Representación en string del embedding."""
        return f"VectorEmbedding({self.dimension}D, model={self.model})"

    def __repr__(self) -> str:
        """Representación para debugging."""
        vec_preview = self.vector[:3] if self.dimension > 3 else self.vector
        return (
            f"VectorEmbedding(dimension={self.dimension}, model='{self.model}', "
            f"magnitude={self.magnitude():.6f}, preview={vec_preview})"
        )

    def __eq__(self, other: object) -> bool:
        """
        Compara dos embeddings por igualdad.

        Dos embeddings son iguales si tienen el mismo modelo, dimensión
        y vectores muy similares (dentro de tolerancia numérica).
        """
        if not isinstance(other, VectorEmbedding):
            return False

        return (
            self.model == other.model
            and self.dimension == other.dimension
            and np.allclose(self.vector, other.vector, atol=1e-6)
        )

    def __hash__(self) -> int:
        """Hash del embedding (basado en modelo y dimensión)."""
        # No incluir vector en hash porque es mutable en numpy
        return hash((self.model, self.dimension))
