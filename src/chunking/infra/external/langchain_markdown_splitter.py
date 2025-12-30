"""Adaptador de LangChain para splitting basado en estructura Markdown."""

from langchain_text_splitters import (
    MarkdownHeaderTextSplitter,
    RecursiveCharacterTextSplitter,
)

from src.chunking.domain.interfaces.external import ITextSplitter, ITokenEncoder


class LangChainMarkdownSplitter(ITextSplitter):
    """
    Adaptador de LangChain para splitting basado en estructura Markdown.

    Divide texto Markdown respetando su estructura jerárquica (headers).
    Esto es ideal para artículos que ya están en formato Markdown porque:

    - Preserva la organización lógica del documento
    - Mantiene contexto semántico dentro de cada chunk
    - Divide en límites naturales (secciones, subsecciones)
    - Más efectivo para retrieval y summarization

    Ventajas sobre RecursiveCharacterTextSplitter:
    - ✅ Respeta estructura semántica del documento
    - ✅ Chunks más coherentes (secciones completas)
    - ✅ Mejor para RAG (retrieval más preciso)
    - ✅ Preserva jerarquía de headers en metadata

    Flujo de splitting:
    1. MarkdownHeaderTextSplitter divide por headers (#, ##, ###)
    2. RecursiveCharacterTextSplitter subdivide chunks grandes
    """

    def __init__(
        self,
        token_encoder: ITokenEncoder,
        chunk_size: int = 1200,
        chunk_overlap: int = 150,
        encoding_name: str = "cl100k_base",
        headers_to_split_on: list[tuple[str, str]] | None = None,
    ):
        """
        Inicializa Markdown splitter.

        Args:
            token_encoder: Encoder para contar tokens
            chunk_size: Tamaño máximo del chunk en tokens
            chunk_overlap: Overlap entre chunks en tokens
            encoding_name: Nombre del encoding de tiktoken
            headers_to_split_on: Headers para dividir (default: H1, H2, H3)
                Formato: [("#", "Header 1"), ("##", "Header 2"), ...]
        """
        self._encoder = token_encoder
        self._chunk_size = chunk_size
        self._chunk_overlap = chunk_overlap
        self._encoding_name = encoding_name

        # Headers por defecto: H1, H2, H3
        self._headers_to_split_on = headers_to_split_on or [
            ("#", "Header 1"),
            ("##", "Header 2"),
            ("###", "Header 3"),
        ]

        # Paso 1: Splitter por headers de Markdown
        self._markdown_splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=self._headers_to_split_on,
            strip_headers=False,  # Mantener headers en el contenido
        )

        # Paso 2: Splitter recursivo para chunks grandes
        # (subdivide secciones que excedan chunk_size)
        try:
            self._recursive_splitter = (
                RecursiveCharacterTextSplitter.from_tiktoken_encoder(
                    encoding_name=encoding_name,
                    chunk_size=chunk_size,
                    chunk_overlap=chunk_overlap,
                )
            )
        except Exception:
            # Fallback
            self._recursive_splitter = RecursiveCharacterTextSplitter(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                length_function=lambda text: self._encoder.count_tokens(text),
            )

    def find_split_point(
        self,
        text: str,
        max_tokens: int,
        separators: list[str],
    ) -> int:
        """
        Encuentra el mejor punto de división en texto Markdown.

        Usa MarkdownHeaderTextSplitter para dividir por estructura,
        luego RecursiveCharacterTextSplitter para chunks grandes.

        Args:
            text: Texto Markdown a dividir
            max_tokens: Máximo de tokens permitidos
            separators: Lista de separadores (ignorado, usa headers de Markdown)

        Returns:
            Índice de carácter donde dividir (0 si no se puede dividir)
        """
        # Si el texto completo cabe, retornar su longitud
        if self._encoder.count_tokens(text) <= max_tokens:
            return len(text)

        try:
            # Paso 1: Dividir por headers de Markdown
            md_chunks = self._markdown_splitter.split_text(text)

            if not md_chunks:
                # Fallback: usar splitter recursivo directo
                return self._fallback_split(text)

            # Paso 2: Si el primer chunk es muy grande, subdividir
            first_chunk = (
                md_chunks[0].page_content
                if hasattr(md_chunks[0], "page_content")
                else md_chunks[0]
            )

            if self._encoder.count_tokens(first_chunk) > max_tokens:
                # Subdividir con recursive splitter
                sub_chunks = self._recursive_splitter.split_text(first_chunk)
                if sub_chunks:
                    return len(sub_chunks[0])

            # Retornar longitud del primer chunk
            return len(first_chunk)

        except Exception:
            # Fallback en caso de error
            return self._fallback_split(text)

    def _fallback_split(self, text: str) -> int:
        """
        Fallback: usar splitter recursivo directo.

        Args:
            text: Texto a dividir

        Returns:
            Índice de carácter donde dividir
        """
        chunks = self._recursive_splitter.split_text(text)
        if not chunks:
            return 0
        return len(chunks[0])
