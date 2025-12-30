"""Excepciones específicas del AI Content Processing bounded context."""

from src.shared.kernel.errors import DomainException


class ContextPackFullException(DomainException):
    """
    Excepción cuando un ContextPack alcanza su límite de tokens.

    Se lanza cuando se intenta agregar un chunk a un ContextPack
    que ya alcanzó su max_tokens configurado.

    Attributes:
        current_tokens: Tokens actuales en el pack
        max_tokens: Límite máximo de tokens
        attempted_tokens: Tokens que se intentaron agregar

    Example:
        >>> if self.total_tokens + token_count > self.max_tokens:
        ...     raise ContextPackFullException(
        ...         current_tokens=self.total_tokens,
        ...         max_tokens=self.max_tokens,
        ...         attempted_tokens=token_count
        ...     )
    """

    def __init__(
        self,
        current_tokens: int,
        max_tokens: int,
        attempted_tokens: int,
    ):
        """
        Inicializa la excepción.

        Args:
            current_tokens: Tokens actuales en el pack
            max_tokens: Límite máximo de tokens
            attempted_tokens: Tokens que se intentaron agregar
        """
        message = (
            f"Cannot add chunk: would exceed max_tokens "
            f"({current_tokens} + {attempted_tokens} > {max_tokens})"
        )
        super().__init__(message)
        self.current_tokens = current_tokens
        self.max_tokens = max_tokens
        self.attempted_tokens = attempted_tokens


class ChunkRelevanceOrderException(DomainException):
    """
    Excepción cuando se intenta agregar chunks fuera de orden de relevancia.

    Se lanza cuando se intenta agregar un chunk con relevance score
    mayor que el último chunk agregado, violando el invariante de
    orden descendente.

    Attributes:
        new_score: Score del chunk que se intenta agregar
        last_score: Score del último chunk agregado

    Example:
        >>> if self.relevance_scores and relevance_score > self.relevance_scores[-1]:
        ...     raise ChunkRelevanceOrderException(
        ...         new_score=relevance_score,
        ...         last_score=self.relevance_scores[-1]
        ...     )
    """

    def __init__(self, new_score: float, last_score: float):
        """
        Inicializa la excepción.

        Args:
            new_score: Score del chunk que se intenta agregar
            last_score: Score del último chunk agregado
        """
        message = (
            f"Chunks must be added in descending relevance order: "
            f"new score {new_score} > last score {last_score}"
        )
        super().__init__(message)
        self.new_score = new_score
        self.last_score = last_score
