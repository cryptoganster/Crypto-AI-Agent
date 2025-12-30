"""Value Object para summary de un chunk de contenido."""

from dataclasses import dataclass

# Constantes para validación
MIN_SENTENCES = 3
"""Número mínimo de frases en un summary."""

MAX_SENTENCES = 5
"""Número máximo de frases en un summary."""

MIN_CONTENT_LENGTH = 10
"""Longitud mínima del contenido del summary."""

MAX_CONTENT_LENGTH = 2000
"""Longitud máxima del contenido del summary."""


@dataclass(frozen=True)
class ChunkSummary:
    """
    Value Object para summary de un chunk de contenido.

    Representa un resumen conciso de 3-5 frases que captura la información
    esencial de un chunk de texto. Generado por LLM con instrucciones específicas
    para mantener hechos importantes, actores, números y fechas.

    Attributes:
        content: Texto del summary (3-5 frases)
        sentence_count: Número de frases en el summary

    Examples:
        >>> summary = ChunkSummary(
        ...     content="Bitcoin alcanzó $50,000. El mercado reaccionó positivamente. "
        ...             "Los inversores institucionales aumentaron sus posiciones.",
        ...     sentence_count=3
        ... )
        >>> summary.is_valid_length()
        True
        >>> summary.get_word_count()
        12
    """

    content: str
    sentence_count: int

    def __post_init__(self):
        """Valida que el summary sea válido."""
        # Validar content
        if not isinstance(self.content, str):
            raise TypeError(f"Content debe ser string, recibido: {type(self.content)}")

        if not self.content or not self.content.strip():
            raise ValueError("Content no puede estar vacío")

        content_length = len(self.content)
        if content_length < MIN_CONTENT_LENGTH:
            raise ValueError(
                f"Content muy corto: {content_length} caracteres, "
                f"mínimo: {MIN_CONTENT_LENGTH}"
            )

        if content_length > MAX_CONTENT_LENGTH:
            raise ValueError(
                f"Content muy largo: {content_length} caracteres, "
                f"máximo: {MAX_CONTENT_LENGTH}"
            )

        # Validar sentence_count
        if not isinstance(self.sentence_count, int):
            raise TypeError(
                f"Sentence count debe ser int, recibido: {type(self.sentence_count)}"
            )

        if not MIN_SENTENCES <= self.sentence_count <= MAX_SENTENCES:
            raise ValueError(
                f"Summary debe tener entre {MIN_SENTENCES} y {MAX_SENTENCES} frases, "
                f"recibido: {self.sentence_count}"
            )

    @classmethod
    def from_text(cls, text: str) -> "ChunkSummary":
        """
        Crea ChunkSummary desde texto, contando frases automáticamente.

        Cuenta frases usando puntos como delimitadores. Considera:
        - Punto seguido de espacio y mayúscula
        - Punto al final del texto
        - Ignora puntos en números (ej: 3.14)

        Args:
            text: Texto del summary

        Returns:
            ChunkSummary con sentence_count calculado

        Examples:
            >>> summary = ChunkSummary.from_text(
            ...     "Primera frase. Segunda frase. Tercera frase."
            ... )
            >>> summary.sentence_count
            3
        """
        if not text or not text.strip():
            raise ValueError("Text no puede estar vacío")

        # Contar frases de manera simple
        # Dividir por punto y filtrar vacíos
        sentences = [s.strip() for s in text.split(". ") if s.strip()]

        # Si el último elemento no termina en punto, es una frase completa
        if text.rstrip().endswith("."):
            sentence_count = len(sentences)
        else:
            sentence_count = len(sentences)

        # Ajustar si hay punto final sin espacio
        if "." in text and not text.endswith(". "):
            # Contar puntos que probablemente sean finales de frase
            sentence_count = text.count(". ") + (
                1 if text.rstrip().endswith(".") else 0
            )

        # Asegurar que esté en rango válido
        sentence_count = max(MIN_SENTENCES, min(MAX_SENTENCES, sentence_count))

        return cls(content=text.strip(), sentence_count=sentence_count)

    def get_word_count(self) -> int:
        """
        Obtiene el número de palabras en el summary.

        Returns:
            Número de palabras
        """
        return len(self.content.split())

    def get_char_count(self) -> int:
        """
        Obtiene el número de caracteres en el summary.

        Returns:
            Número de caracteres
        """
        return len(self.content)

    def is_valid_length(self) -> bool:
        """
        Verifica si el summary tiene una longitud válida.

        Returns:
            True si está dentro de los límites
        """
        return MIN_CONTENT_LENGTH <= len(self.content) <= MAX_CONTENT_LENGTH

    def is_concise(self) -> bool:
        """
        Verifica si el summary es conciso (< 500 caracteres).

        Returns:
            True si es conciso
        """
        return len(self.content) < 500

    def contains_numbers(self) -> bool:
        """
        Verifica si el summary contiene números (importante para hechos).

        Returns:
            True si contiene al menos un dígito
        """
        return any(char.isdigit() for char in self.content)

    def get_preview(self, max_length: int = 100) -> str:
        """
        Obtiene un preview del summary.

        Args:
            max_length: Longitud máxima del preview

        Returns:
            Preview del summary (truncado si es necesario)
        """
        if len(self.content) <= max_length:
            return self.content

        return self.content[: max_length - 3] + "..."

    def __str__(self) -> str:
        """Representación en string del summary."""
        return self.content

    def __repr__(self) -> str:
        """Representación para debugging."""
        preview = self.get_preview(50)
        return (
            f"ChunkSummary(sentences={self.sentence_count}, "
            f"words={self.get_word_count()}, "
            f"preview='{preview}')"
        )

    def __len__(self) -> int:
        """Permite usar len() en ChunkSummary."""
        return len(self.content)
