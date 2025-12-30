"""Interface para token encoding."""

from typing import Protocol


class ITokenEncoder(Protocol):
    """
    Interface para servicios de token encoding.

    Abstracción sobre tiktoken u otros encoders de tokens.
    """

    def encode(self, text: str) -> list[int]:
        """
        Codifica texto a lista de token IDs.

        Args:
            text: Texto a codificar

        Returns:
            Lista de token IDs
        """
        ...

    def count_tokens(self, text: str) -> int:
        """
        Cuenta tokens en texto.

        Args:
            text: Texto a contar

        Returns:
            Número de tokens
        """
        ...
