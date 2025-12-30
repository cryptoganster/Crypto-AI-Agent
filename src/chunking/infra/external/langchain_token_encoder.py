"""Adaptador de tokenización usando utilidades de LangChain."""

from typing import Literal

try:
    # LangChain >= 0.1.0 tiene utilidades de tokenización
    from langchain_community.utils.tiktoken import get_token_ids

    LANGCHAIN_TIKTOKEN_AVAILABLE = True
except ImportError:
    LANGCHAIN_TIKTOKEN_AVAILABLE = False

from src.chunking.domain.interfaces.external import ITokenEncoder


class LangChainTokenEncoder(ITokenEncoder):
    """
    Encoder de tokens usando utilidades de LangChain.

    Usa las utilidades de tokenización de LangChain que abstraen tiktoken.
    Esto permite aprovechar optimizaciones y mejoras de LangChain.

    Soporta múltiples modelos de OpenAI y otros proveedores.

    Encodings soportados:
    - "cl100k_base": GPT-4, GPT-3.5-turbo, text-embedding-ada-002
    - "p50k_base": Codex, text-davinci-002, text-davinci-003
    - "r50k_base": GPT-3 (davinci, curie, babbage, ada)
    - "o200k_base": GPT-4o (más reciente)

    Nota: Si langchain_community no está disponible, usa tiktoken directamente.
    """

    def __init__(
        self,
        encoding_name: Literal[
            "cl100k_base",
            "p50k_base",
            "r50k_base",
            "o200k_base",
        ] = "cl100k_base",
    ):
        """
        Inicializa encoder.

        Args:
            encoding_name: Nombre del encoding de tiktoken
                - "cl100k_base": GPT-4, GPT-3.5-turbo (default)
                - "p50k_base": Codex, text-davinci-002/003
                - "r50k_base": GPT-3 (davinci, curie, etc.)
                - "o200k_base": GPT-4o (más reciente)
        """
        self._encoding_name = encoding_name

        # Usar tiktoken directamente (LangChain lo usa internamente)
        # LangChain no expone una API pública para encoding/decoding,
        # solo para conteo de tokens
        import tiktoken

        self._encoder = tiktoken.get_encoding(encoding_name)

    def count_tokens(self, text: str) -> int:
        """
        Cuenta tokens en el texto.

        Usa utilidades de LangChain si están disponibles,
        sino usa tiktoken directamente.

        Args:
            text: Texto a contar

        Returns:
            Número de tokens
        """
        if LANGCHAIN_TIKTOKEN_AVAILABLE:
            # Usar utilidad de LangChain (optimizada)
            return len(get_token_ids(text, encoding_name=self._encoding_name))
        else:
            # Fallback a tiktoken directo
            return len(self._encoder.encode(text))

    def encode(self, text: str) -> list[int]:
        """
        Codifica texto a lista de token IDs.

        Nota: LangChain no expone API pública para encoding,
        por lo que usamos tiktoken directamente.

        Args:
            text: Texto a codificar

        Returns:
            Lista de token IDs
        """
        return self._encoder.encode(text)

    def decode(self, tokens: list[int]) -> str:
        """
        Decodifica lista de token IDs a texto.

        Nota: LangChain no expone API pública para decoding,
        por lo que usamos tiktoken directamente.

        Args:
            tokens: Lista de token IDs

        Returns:
            Texto decodificado
        """
        return self._encoder.decode(tokens)

    @property
    def model_name(self) -> str:
        """
        Nombre del encoding usado.

        Returns:
            Nombre del encoding (ej: "cl100k_base")
        """
        return self._encoding_name

    @classmethod
    def for_model(cls, model_name: str) -> "LangChainTokenEncoder":
        """
        Crea encoder apropiado para un modelo específico.

        Args:
            model_name: Nombre del modelo (ej: "gpt-4", "gpt-3.5-turbo")

        Returns:
            LangChainTokenEncoder configurado para el modelo

        Example:
            >>> encoder = LangChainTokenEncoder.for_model("gpt-4")
            >>> encoder.count_tokens("Hello world")
            2
        """
        # Mapeo de modelos a encodings
        model_to_encoding = {
            "gpt-4": "cl100k_base",
            "gpt-4-turbo": "cl100k_base",
            "gpt-4o": "o200k_base",
            "gpt-3.5-turbo": "cl100k_base",
            "text-embedding-ada-002": "cl100k_base",
            "text-davinci-003": "p50k_base",
            "text-davinci-002": "p50k_base",
            "davinci": "r50k_base",
            "curie": "r50k_base",
            "babbage": "r50k_base",
            "ada": "r50k_base",
        }

        # Buscar encoding para el modelo
        encoding_name = model_to_encoding.get(model_name, "cl100k_base")

        return cls(encoding_name=encoding_name)
