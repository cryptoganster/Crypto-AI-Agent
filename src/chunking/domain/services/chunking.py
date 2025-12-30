"""Domain service para chunking de contenido con overlap exacto."""

from typing import TYPE_CHECKING, List, Tuple

from src.chunking.domain.aggregates import KnowledgeChunk
from src.chunking.domain.interfaces.external import ITextSplitter, ITokenEncoder
from src.chunking.domain.interfaces.services import IChunkingService
from src.chunking.domain.value_objects.token_count import TokenCount

if TYPE_CHECKING:
    from src.knowledge.domain.value_objects.source_reference import SourceReference

# Alias for backward compatibility
ContentChunk = KnowledgeChunk


class ChunkingService(IChunkingService):
    """
    Domain service para dividir contenido en chunks con overlap exacto.

    Implementación custom que garantiza:
    - Overlap exacto en caracteres entre chunks consecutivos
    - Posiciones de caracteres precisas (start_char, end_char)
    - Chunks dentro de límites de tamaño especificados
    - Separación en límites de oraciones cuando sea posible

    Usa Dependency Inversion Principle (DIP):
    - Depende de ITokenEncoder (abstracción) en lugar de tiktoken directamente
    - Depende de ITextSplitter (abstracción) para encontrar puntos de división

    Responsabilidades:
    - Dividir texto en chunks de tamaño apropiado
    - Garantizar overlap exacto entre chunks consecutivos
    - Calcular token counts usando ITokenEncoder
    - Crear ContentChunk aggregates

    Configuración:
    - chunk_size: 100-2000 tokens (default: 1400)
    - chunk_overlap: 0 a chunk_size-1 tokens (default: 150)
    - Separadores jerárquicos: \n\n, \n, . , espacio
    """

    def __init__(
        self,
        token_encoder: ITokenEncoder = None,
        text_splitter: ITextSplitter = None,
        chunk_size: int = 1400,
        chunk_overlap: int = 150,
    ):
        """
        Inicializa ChunkingService.

        Args:
            token_encoder: Encoder de tokens (ej: TiktokenEncoder). Si None, usa default.
            text_splitter: Splitter de texto (ej: RecursiveTextSplitter). Si None, usa default.
            chunk_size: Tamaño máximo del chunk en tokens (default: 1400)
            chunk_overlap: Overlap entre chunks en tokens (default: 150)

        Raises:
            ValueError: Si los parámetros son inválidos
        """
        # Validar chunk_size
        if chunk_size < 100:
            raise ValueError(f"chunk_size debe ser >= 100, recibido: {chunk_size}")
        if chunk_size > 2000:
            raise ValueError(f"chunk_size debe ser <= 2000, recibido: {chunk_size}")

        # Validar chunk_overlap
        if chunk_overlap < 0:
            raise ValueError(f"chunk_overlap debe ser >= 0, recibido: {chunk_overlap}")
        if chunk_overlap >= chunk_size:
            raise ValueError(
                f"chunk_overlap ({chunk_overlap}) debe ser < chunk_size ({chunk_size})"
            )

        # Inyección de dependencias con defaults
        if token_encoder is None:
            from src.chunking.infra.external import LangChainTokenEncoder

            token_encoder = LangChainTokenEncoder()

        if text_splitter is None:
            from src.chunking.infra.external import LangChainMarkdownSplitter

            text_splitter = LangChainMarkdownSplitter(token_encoder)

        self._token_encoder = token_encoder
        self._text_splitter = text_splitter

        self._chunk_size = chunk_size
        self._chunk_overlap = chunk_overlap

        # Separadores jerárquicos (de más a menos preferido)
        self._separators = ["\n\n", "\n", ". ", " "]

    def _count_tokens(self, text: str) -> int:
        """
        Cuenta tokens en texto usando el encoder inyectado.

        Args:
            text: Texto a contar

        Returns:
            Número de tokens
        """
        return self._token_encoder.count_tokens(text)

    def _find_split_point(
        self,
        text: str,
        max_tokens: int,
    ) -> int:
        """
        Encuentra el mejor punto de división en el texto.

        Delega al text_splitter inyectado para encontrar el punto óptimo.

        Args:
            text: Texto a dividir
            max_tokens: Máximo de tokens permitidos

        Returns:
            Índice de carácter donde dividir
        """
        # Delegar al text_splitter inyectado
        return self._text_splitter.find_split_point(
            text=text,
            max_tokens=max_tokens,
            separators=self._separators,
        )

    def _find_overlap_chars(self, text: str, overlap_tokens: int) -> int:
        """
        Encuentra cuántos caracteres corresponden a overlap_tokens.

        Args:
            text: Texto del chunk
            overlap_tokens: Número de tokens de overlap deseado

        Returns:
            Número de caracteres que corresponden al overlap
        """
        if overlap_tokens <= 0:
            return 0

        # Binary search para encontrar caracteres que corresponden a tokens
        left, right = 0, len(text)
        best_chars = 0

        while left <= right:
            mid = (left + right) // 2
            # Tomar los últimos 'mid' caracteres
            overlap_text = text[-mid:] if mid > 0 else ""
            token_count = self._count_tokens(overlap_text)

            if token_count <= overlap_tokens:
                best_chars = mid
                left = mid + 1
            else:
                right = mid - 1

        return best_chars

    def _split_with_overlap(
        self,
        content: str,
    ) -> List[Tuple[str, int, int]]:
        """
        Divide contenido en chunks con overlap exacto.

        Args:
            content: Contenido a dividir

        Returns:
            Lista de tuplas (chunk_text, start_char, end_char)
        """
        chunks: List[Tuple[str, int, int]] = []
        current_pos = 0

        while current_pos < len(content):
            # Texto restante desde posición actual
            remaining = content[current_pos:]

            # Encontrar punto de división
            split_point = self._find_split_point(remaining, self._chunk_size)

            # Extraer chunk
            chunk_text = remaining[:split_point]
            start_char = current_pos
            end_char = current_pos + len(chunk_text)

            chunks.append((chunk_text, start_char, end_char))

            # Si llegamos al final, terminar
            if end_char >= len(content):
                break

            # Calcular siguiente posición con overlap
            # El overlap debe ser en caracteres, no tokens
            # Encontramos cuántos caracteres corresponden a overlap tokens
            overlap_chars = self._find_overlap_chars(chunk_text, self._chunk_overlap)

            # Siguiente chunk empieza en: end_char - overlap_chars
            current_pos = max(0, end_char - overlap_chars)

            # Evitar loop infinito: si no avanzamos, forzar avance
            if current_pos == start_char:
                current_pos = end_char

        return chunks

    def chunk_text(
        self,
        text: str,
        source: "SourceReference",
    ) -> List[KnowledgeChunk]:
        """
        Divide texto en chunks con overlap exacto.

        Args:
            text: Texto a dividir
            source: SourceReference con información del contenido fuente

        Returns:
            Lista de KnowledgeChunk aggregates

        Raises:
            ValueError: Si text está vacío

        Example:
            >>> from src.knowledge.domain.value_objects.source_reference import SourceReference
            >>> source = SourceReference(article_id="art-123", source_url="https://example.com")
            >>> chunks = service.chunk_text(text="Long content...", source=source)
            >>> len(chunks)
            3
            >>> chunks[0].source.source_id
            'art-123'
        """
        if not text or not text.strip():
            raise ValueError("text no puede estar vacío")

        # Dividir con overlap exacto
        chunk_data = self._split_with_overlap(text)

        # Crear KnowledgeChunk aggregates
        chunks: List[KnowledgeChunk] = []

        for position, (chunk_text, start_char, end_char) in enumerate(chunk_data):
            # Calcular token count
            token_count = TokenCount(self._count_tokens(chunk_text))

            # Crear chunk usando SourceReference
            from src.chunking.domain.value_objects.chunk_id import ChunkId

            chunk = KnowledgeChunk(
                id=ChunkId.generate(),
                source=source,
                content=chunk_text,
                position=position,
                start_char=start_char,
                end_char=end_char,
                token_count=token_count,
            )

            chunks.append(chunk)

        return chunks

    def chunk_content(
        self,
        content: str,
        source: "SourceReference",
    ) -> List[KnowledgeChunk]:
        """
        Divide contenido en chunks con overlap exacto.

        Alias de chunk_text para compatibilidad.

        Args:
            content: Contenido a dividir
            source: SourceReference con información del contenido fuente

        Returns:
            Lista de KnowledgeChunk aggregates

        Raises:
            ValueError: Si content está vacío

        Example:
            >>> from src.knowledge.domain.value_objects.source_reference import SourceReference
            >>> source = SourceReference(article_id="art-123", source_url="https://example.com")
            >>> chunks = service.chunk_content(content="Long content...", source=source)
        """
        return self.chunk_text(
            text=content,
            source=source,
        )

    @property
    def chunk_size(self) -> int:
        """Tamaño máximo del chunk en tokens."""
        return self._chunk_size

    @property
    def chunk_overlap(self) -> int:
        """Overlap entre chunks en tokens."""
        return self._chunk_overlap
