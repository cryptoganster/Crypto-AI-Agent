"""Interface para text splitting."""

from typing import Protocol


class ITextSplitter(Protocol):
    """
    Interface para servicios de text splitting.

    Abstracción sobre LangChain u otros text splitters.
    """

    def find_split_point(
        self,
        text: str,
        max_tokens: int,
        separators: list[str],
    ) -> int:
        """
        Encuentra el mejor punto de división en el texto.

        Args:
            text: Texto a dividir
            max_tokens: Máximo de tokens permitidos
            separators: Lista de separadores jerárquicos

        Returns:
            Índice de carácter donde dividir
        """
        ...
