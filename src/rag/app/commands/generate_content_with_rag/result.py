"""Result object para GenerateContentWithRAG command."""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class GeneratedContent:
    """
    Contenido generado con RAG.

    Attributes:
        content: Contenido generado
        sources: URLs de fuentes usadas
        chunk_ids: IDs de chunks usados
        relevance_scores: Scores de relevancia de chunks
        tokens_used: Tokens usados en generación
        model: Modelo LLM usado
        generated_at: Timestamp de generación
    """

    content: str
    sources: List[str]
    chunk_ids: List[str]
    relevance_scores: List[float]
    tokens_used: int
    model: str
    generated_at: datetime


@dataclass
class GenerateContentWithRAGResult:
    """
    Result object para GenerateContentWithRAG command.

    Attributes:
        success: Si la generación fue exitosa
        generated_content: Contenido generado (si success=True)
        error: Mensaje de error (si success=False)
        context_pack_id: ID del context pack usado
        query: Query original
    """

    success: bool
    generated_content: Optional[GeneratedContent] = None
    error: Optional[str] = None
    context_pack_id: Optional[str] = None
    query: Optional[str] = None

    @classmethod
    def success_result(
        cls,
        generated_content: GeneratedContent,
        context_pack_id: str,
        query: str,
    ) -> "GenerateContentWithRAGResult":
        """
        Crea result exitoso.

        Args:
            generated_content: Contenido generado
            context_pack_id: ID del context pack
            query: Query original

        Returns:
            GenerateContentWithRAGResult exitoso
        """
        return cls(
            success=True,
            generated_content=generated_content,
            context_pack_id=context_pack_id,
            query=query,
        )

    @classmethod
    def failure(
        cls, error: str, query: Optional[str] = None
    ) -> "GenerateContentWithRAGResult":
        """
        Crea result fallido.

        Args:
            error: Mensaje de error
            query: Query original (opcional)

        Returns:
            GenerateContentWithRAGResult fallido
        """
        return cls(
            success=False,
            error=error,
            query=query,
        )
