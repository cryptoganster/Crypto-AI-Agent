"""HuggingFace token encoder adapter."""

from typing import List, Optional

from transformers import AutoTokenizer

from src.chunking.domain.interfaces.external.token_encoder import ITokenEncoder


class HuggingFaceTokenEncoder(ITokenEncoder):
    """
    Token encoder usando tokenizers de HuggingFace.

    Soporta modelos que no están en tiktoken (como Qwen3-VL).
    Usa transformers.AutoTokenizer para cargar el tokenizer del modelo.

    Example:
        >>> encoder = HuggingFaceTokenEncoder.for_model("Qwen/Qwen2-VL-7B-Instruct")
        >>> tokens = encoder.encode("Hello world")
        >>> text = encoder.decode(tokens)
    """

    def __init__(self, tokenizer: AutoTokenizer):
        """
        Inicializa encoder con tokenizer de HuggingFace.

        Args:
            tokenizer: Tokenizer de transformers
        """
        self._tokenizer = tokenizer

    @classmethod
    def for_model(
        cls,
        model_name: str,
        trust_remote_code: bool = True,
        use_fast: bool = True,
    ) -> "HuggingFaceTokenEncoder":
        """
        Factory method para crear encoder desde nombre de modelo.

        Args:
            model_name: Nombre del modelo en HuggingFace Hub
                       (ej: "Qwen/Qwen2-VL-7B-Instruct")
            trust_remote_code: Si confiar en código remoto del modelo
            use_fast: Si usar tokenizer rápido (Rust) cuando esté disponible

        Returns:
            HuggingFaceTokenEncoder configurado para el modelo

        Raises:
            ValueError: Si el modelo no existe o no se puede cargar

        Example:
            >>> # Qwen3-VL
            >>> encoder = HuggingFaceTokenEncoder.for_model(
            ...     "Qwen/Qwen2-VL-7B-Instruct"
            ... )
            >>>
            >>> # Llama
            >>> encoder = HuggingFaceTokenEncoder.for_model(
            ...     "meta-llama/Llama-2-7b-hf"
            ... )
        """
        try:
            tokenizer = AutoTokenizer.from_pretrained(
                model_name,
                trust_remote_code=trust_remote_code,
                use_fast=use_fast,
            )
            return cls(tokenizer)
        except Exception as e:
            raise ValueError(
                f"No se pudo cargar tokenizer para modelo '{model_name}': {e}"
            )

    def encode(self, text: str) -> List[int]:
        """
        Codifica texto a tokens.

        Args:
            text: Texto a codificar

        Returns:
            Lista de IDs de tokens

        Example:
            >>> encoder = HuggingFaceTokenEncoder.for_model("Qwen/Qwen2-VL-7B-Instruct")
            >>> tokens = encoder.encode("Hello world")
            >>> len(tokens)
            3
        """
        return self._tokenizer.encode(text, add_special_tokens=False)

    def decode(self, tokens: List[int]) -> str:
        """
        Decodifica tokens a texto.

        Args:
            tokens: Lista de IDs de tokens

        Returns:
            Texto decodificado

        Example:
            >>> encoder = HuggingFaceTokenEncoder.for_model("Qwen/Qwen2-VL-7B-Instruct")
            >>> tokens = [9906, 1917]
            >>> text = encoder.decode(tokens)
            >>> text
            'Hello world'
        """
        return self._tokenizer.decode(tokens, skip_special_tokens=True)

    def count_tokens(self, text: str) -> int:
        """
        Cuenta tokens en texto sin codificar completamente.

        Args:
            text: Texto a contar

        Returns:
            Número de tokens

        Example:
            >>> encoder = HuggingFaceTokenEncoder.for_model("Qwen/Qwen2-VL-7B-Instruct")
            >>> count = encoder.count_tokens("Hello world")
            >>> count
            3
        """
        return len(self.encode(text))

    @property
    def model_name(self) -> Optional[str]:
        """
        Nombre del modelo del tokenizer.

        Returns:
            Nombre del modelo o None si no está disponible
        """
        return getattr(self._tokenizer, "name_or_path", None)
