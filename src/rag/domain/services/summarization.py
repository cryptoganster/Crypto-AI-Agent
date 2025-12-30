"""Domain service para summarización jerárquica."""

from typing import Any, Dict, List, Optional

from src.chunking.domain.aggregates.content_chunk import ContentChunk
from src.chunking.domain.value_objects.chunk_summary import ChunkSummary
from src.chunking.domain.value_objects.tldr import TLDR
from src.rag.domain.interfaces.llm_service import ILLMService
from src.rag.domain.interfaces.services import ISummarizationService


class SummarizationService(ISummarizationService):
    """
    Domain service para summarización jerárquica.

    Responsabilidades:
    - Generar chunk summaries (3-5 frases)
    - Generar global summary (artículo completo)
    - Fusionar summaries en TLDR
    """

    def __init__(self, llm_service: ILLMService):
        """
        Inicializa SummarizationService.

        Args:
            llm_service: Servicio de LLM para generación de texto
        """
        self._llm = llm_service

    async def summarize_chunk(self, chunk: ContentChunk) -> ChunkSummary:
        """
        Genera summary de 3-5 frases para un chunk.

        Args:
            chunk: Chunk a resumir

        Returns:
            ChunkSummary
        """
        prompt = f"""Resume el siguiente texto en 3-5 frases claras y concisas, 
        manteniendo hechos importantes, actores, números y fechas. 
        No agregues información nueva.

        Texto: {chunk.content}


        Resumen:"""

        summary_text = await self._llm.generate(
            prompt=prompt,
            max_tokens=200,
            temperature=0.3,
        )

        # Contar frases
        sentences = summary_text.split(". ")
        sentence_count = len([s for s in sentences if s.strip()])

        return ChunkSummary(
            content=summary_text,
            sentence_count=sentence_count,
        )

    async def generate_global_summary(
        self,
        full_text: str,
        existing_summary: Optional[str] = None,
    ) -> str:
        """
        Genera summary global del artículo completo.

        Args:
            full_text: Texto completo del artículo
            existing_summary: Summary extractivo existente (opcional)

        Returns:
            Global summary
        """
        prompt = f"""Genera un resumen global de este artículo manteniendo 
        la información crítica.

        {f"Resumen extractivo existente: {existing_summary}" if existing_summary else ""}

        Artículo: {full_text[:4000]}

        Resumen global:"""

        return await self._llm.generate(
            prompt=prompt,
            max_tokens=300,
            temperature=0.3,
        )

    async def fuse_into_tldr(
        self,
        global_summary: str,
        chunk_summaries: List[ChunkSummary],
        metadata: Dict[str, Any],
    ) -> TLDR:
        """
        Fusiona summaries en TLDR de 3-5 bullets.

        Args:
            global_summary: Summary global
            chunk_summaries: Summaries de chunks
            metadata: Metadata del artículo (fecha, fuente, etc.)

        Returns:
            TLDR
        """
        chunk_summaries_text = "\n".join(f"- {cs.content}" for cs in chunk_summaries)

        prompt = f"""Usa los siguientes datos:

        1) Summary global: {global_summary}

        2) Summaries por chunk: {chunk_summaries_text}

        3) Metadata:
        - Fuente: {metadata.get('source', 'Unknown')}
        - Fecha: {metadata.get('date', 'Unknown')}
        - Tokens mencionados: {metadata.get('tokens', [])}

        Genera un TLDR final de 3-5 bullets con:
        - Qué pasó
        - Impacto en el mercado cripto
        - Tokens afectados
        - Actores involucrados
        - Riesgo regulatorio o técnico

        No agregues información nueva.

        TLDR:"""

        tldr_text = await self._llm.generate(
            prompt=prompt,
            max_tokens=250,
            temperature=0.3,
        )

        # Parsear bullets
        bullets = [
            line.strip("- ").strip()
            for line in tldr_text.split("\n")
            if line.strip().startswith("-")
        ]

        return TLDR(bullets=bullets)
