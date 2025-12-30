"""Interface para servicio de summarization con LLM."""

from typing import List, Protocol

from src.chunking.domain.aggregates.content_chunk import ContentChunk


class ISummarizationService(Protocol):
    """
    Interface para servicio de summarization usando LLM.

    Responsabilidad: Generar summaries de chunks y artículos completos
    usando modelos de lenguaje (LLM).

    Implementaciones deben:
    - Generar chunk summaries (3-5 frases)
    - Generar global summary (artículo completo)
    - Fusionar summaries en TLDR (3-5 bullets)
    - Manejar rate limiting de LLM
    - Validar calidad de summaries
    """

    def summarize_chunk(
        self,
        chunk: ContentChunk,
        max_sentences: int = 5,
    ) -> str:
        """
        Genera summary de un chunk individual.

        Estrategia:
        1. Enviar chunk.content al LLM
        2. Prompt: "Summarize in 3-5 sentences"
        3. Validar longitud de respuesta
        4. Retornar summary limpio

        Args:
            chunk: ContentChunk a summarizar
            max_sentences: Máximo de frases en summary (default: 5)

        Returns:
            Summary del chunk (3-5 frases)

        Raises:
            ValueError: Si chunk.content está vacío
            LLMException: Si LLM falla o rate limit

        Example:
            >>> service = SummarizationService()
            >>> chunk = ContentChunk(
            ...     chunk_id="chunk-1",
            ...     content="Long chunk content...",
            ...     token_count=1200
            ... )
            >>> summary = service.summarize_chunk(chunk)
            >>> len(summary.split('. '))
            4  # 4 frases
        """
        ...

    def generate_global_summary(
        self,
        chunk_summaries: List[str],
        article_title: str,
        max_length: int = 500,
    ) -> str:
        """
        Genera summary global del artículo completo.

        Estrategia:
        1. Concatenar chunk_summaries
        2. Enviar al LLM con contexto del título
        3. Prompt: "Create comprehensive summary"
        4. Limitar a max_length caracteres
        5. Retornar summary global

        Args:
            chunk_summaries: Lista de summaries de chunks
            article_title: Título del artículo para contexto
            max_length: Longitud máxima del summary (default: 500 chars)

        Returns:
            Summary global del artículo completo

        Raises:
            ValueError: Si chunk_summaries está vacío
            LLMException: Si LLM falla

        Example:
            >>> service = SummarizationService()
            >>> chunk_summaries = [
            ...     "Chunk 1 summary...",
            ...     "Chunk 2 summary...",
            ...     "Chunk 3 summary..."
            ... ]
            >>> global_summary = service.generate_global_summary(
            ...     chunk_summaries=chunk_summaries,
            ...     article_title="Python Best Practices"
            ... )
            >>> len(global_summary)
            450  # Dentro del límite
        """
        ...

    def fuse_into_tldr(
        self,
        chunk_summaries: List[str],
        num_bullets: int = 5,
    ) -> List[str]:
        """
        Fusiona summaries en TLDR con bullets.

        Estrategia:
        1. Enviar chunk_summaries al LLM
        2. Prompt: "Create {num_bullets} bullet points"
        3. Extraer puntos clave
        4. Formatear como lista
        5. Retornar bullets

        Args:
            chunk_summaries: Lista de summaries de chunks
            num_bullets: Número de bullets en TLDR (default: 5)

        Returns:
            Lista de bullets (3-5 items)

        Raises:
            ValueError: Si chunk_summaries está vacío
            LLMException: Si LLM falla

        Example:
            >>> service = SummarizationService()
            >>> tldr = service.fuse_into_tldr(
            ...     chunk_summaries=chunk_summaries,
            ...     num_bullets=5
            ... )
            >>> len(tldr)
            5
            >>> tldr[0]
            'Python uses dynamic typing for flexibility'
        """
        ...

    def validate_summary_quality(
        self,
        summary: str,
        min_length: int = 50,
        max_length: int = 1000,
    ) -> bool:
        """
        Valida calidad de un summary generado.

        Validaciones:
        - Longitud dentro de límites
        - No contiene placeholders
        - No está truncado
        - Tiene puntuación correcta

        Args:
            summary: Summary a validar
            min_length: Longitud mínima (default: 50 chars)
            max_length: Longitud máxima (default: 1000 chars)

        Returns:
            True si summary es válido, False si hay problemas

        Example:
            >>> service = SummarizationService()
            >>> is_valid = service.validate_summary_quality(summary)
            >>> if not is_valid:
            ...     raise ValueError("Summary de baja calidad")
        """
        ...
