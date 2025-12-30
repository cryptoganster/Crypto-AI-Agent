"""Value Object para conteo de tokens usando tiktoken."""

from dataclasses import dataclass
from typing import ClassVar

# Constantes para validación
MIN_TOKEN_COUNT = 0
"""Conteo mínimo de tokens."""

MAX_TOKEN_COUNT = 1_000_000
"""Conteo máximo de tokens (límite razonable para un artículo)."""

DEFAULT_ENCODING = "cl100k_base"
"""Encoding por defecto (usado por GPT-4, GPT-3.5-turbo)."""


@dataclass(frozen=True)
class TokenCount:
    """
    Value Object para conteo preciso de tokens.

    Usa tiktoken para conteo preciso compatible con modelos de OpenAI.
    El encoding por defecto es cl100k_base (GPT-4, GPT-3.5-turbo).

    Attributes:
        value: Número de tokens
        encoding: Nombre del encoding usado (ej: "cl100k_base", "p50k_base")

    Examples:
        >>> token_count = TokenCount.from_text("Hello world", encoding="cl100k_base")
        >>> token_count.value
        2
        >>> token_count.is_within_limit(100)
        True
    """

    value: int
    encoding: str = DEFAULT_ENCODING

    # Cache de encoders para evitar recrearlos
    _encoder_cache: ClassVar[dict] = {}

    def __post_init__(self):
        """Valida que el conteo de tokens sea válido."""
        if not isinstance(self.value, int):
            raise TypeError(
                f"Token count debe ser un entero, recibido: {type(self.value)}"
            )

        if self.value < MIN_TOKEN_COUNT:
            raise ValueError(
                f"Token count no puede ser negativo, recibido: {self.value}"
            )

        if self.value > MAX_TOKEN_COUNT:
            raise ValueError(
                f"Token count excede el máximo permitido ({MAX_TOKEN_COUNT}), "
                f"recibido: {self.value}"
            )

        if not isinstance(self.encoding, str) or not self.encoding:
            raise ValueError(
                f"Encoding debe ser un string no vacío, recibido: {self.encoding}"
            )

    @classmethod
    def from_text(cls, text: str, encoding: str = DEFAULT_ENCODING) -> "TokenCount":
        """
        Crea TokenCount contando tokens en el texto usando tiktoken.

        Args:
            text: Texto a contar
            encoding: Encoding a usar (default: cl100k_base)

        Returns:
            TokenCount con el conteo de tokens

        Raises:
            ValueError: Si el texto está vacío o el encoding es inválido
            ImportError: Si tiktoken no está instalado

        Examples:
            >>> count = TokenCount.from_text("Hello world")
            >>> count.value
            2
        """
        if not text:
            return cls(value=0, encoding=encoding)

        try:
            import tiktoken
        except ImportError:
            raise ImportError(
                "tiktoken es requerido para conteo de tokens. "
                "Instalar con: pip install tiktoken"
            )

        # Usar cache de encoders
        if encoding not in cls._encoder_cache:
            try:
                cls._encoder_cache[encoding] = tiktoken.get_encoding(encoding)
            except Exception as e:
                raise ValueError(f"Encoding inválido '{encoding}': {str(e)}")

        encoder = cls._encoder_cache[encoding]
        tokens = encoder.encode(text)

        return cls(value=len(tokens), encoding=encoding)

    def is_within_limit(self, limit: int) -> bool:
        """
        Verifica si el conteo está dentro de un límite.

        Args:
            limit: Límite máximo de tokens

        Returns:
            True si value <= limit

        Examples:
            >>> count = TokenCount(value=100, encoding="cl100k_base")
            >>> count.is_within_limit(150)
            True
            >>> count.is_within_limit(50)
            False
        """
        return self.value <= limit

    def exceeds_limit(self, limit: int) -> bool:
        """
        Verifica si el conteo excede un límite.

        Args:
            limit: Límite máximo de tokens

        Returns:
            True si value > limit
        """
        return self.value > limit

    def is_empty(self) -> bool:
        """
        Verifica si el conteo es cero.

        Returns:
            True si value == 0
        """
        return self.value == 0

    def add(self, other: "TokenCount") -> "TokenCount":
        """
        Suma dos conteos de tokens.

        Args:
            other: Otro TokenCount a sumar

        Returns:
            Nuevo TokenCount con la suma

        Raises:
            ValueError: Si los encodings no coinciden

        Examples:
            >>> count1 = TokenCount(value=100, encoding="cl100k_base")
            >>> count2 = TokenCount(value=50, encoding="cl100k_base")
            >>> total = count1.add(count2)
            >>> total.value
            150
        """
        if self.encoding != other.encoding:
            raise ValueError(
                f"No se pueden sumar TokenCounts con encodings diferentes: "
                f"{self.encoding} != {other.encoding}"
            )

        return TokenCount(value=self.value + other.value, encoding=self.encoding)

    def subtract(self, other: "TokenCount") -> "TokenCount":
        """
        Resta dos conteos de tokens.

        Args:
            other: Otro TokenCount a restar

        Returns:
            Nuevo TokenCount con la resta (mínimo 0)

        Raises:
            ValueError: Si los encodings no coinciden
        """
        if self.encoding != other.encoding:
            raise ValueError(
                f"No se pueden restar TokenCounts con encodings diferentes: "
                f"{self.encoding} != {other.encoding}"
            )

        # No permitir valores negativos
        result_value = max(0, self.value - other.value)
        return TokenCount(value=result_value, encoding=self.encoding)

    def percentage_of(self, total: "TokenCount") -> float:
        """
        Calcula el porcentaje que representa este conteo del total.

        Args:
            total: TokenCount total

        Returns:
            Porcentaje (0.0 - 100.0)

        Raises:
            ValueError: Si los encodings no coinciden o total es cero
        """
        if self.encoding != total.encoding:
            raise ValueError(
                f"No se pueden comparar TokenCounts con encodings diferentes: "
                f"{self.encoding} != {total.encoding}"
            )

        if total.value == 0:
            raise ValueError(
                "No se puede calcular porcentaje de un total de cero tokens"
            )

        return (self.value / total.value) * 100.0

    def __str__(self) -> str:
        """Representación en string del conteo."""
        return f"{self.value} tokens"

    def __repr__(self) -> str:
        """Representación para debugging."""
        return f"TokenCount(value={self.value}, encoding='{self.encoding}')"

    def __int__(self) -> int:
        """Permite usar TokenCount como int."""
        return self.value

    def __lt__(self, other: "TokenCount") -> bool:
        """Comparación menor que."""
        if self.encoding != other.encoding:
            raise ValueError(
                "No se pueden comparar TokenCounts con encodings diferentes"
            )
        return self.value < other.value

    def __le__(self, other: "TokenCount") -> bool:
        """Comparación menor o igual que."""
        if self.encoding != other.encoding:
            raise ValueError(
                "No se pueden comparar TokenCounts con encodings diferentes"
            )
        return self.value <= other.value

    def __gt__(self, other: "TokenCount") -> bool:
        """Comparación mayor que."""
        if self.encoding != other.encoding:
            raise ValueError(
                "No se pueden comparar TokenCounts con encodings diferentes"
            )
        return self.value > other.value

    def __ge__(self, other: "TokenCount") -> bool:
        """Comparación mayor o igual que."""
        if self.encoding != other.encoding:
            raise ValueError(
                "No se pueden comparar TokenCounts con encodings diferentes"
            )
        return self.value >= other.value
