"""Command para generar contenido usando RAG."""

from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class GenerateContentWithRAGCommand:
    """
    Command para generar contenido nuevo basado en RAG.

    Este comando ensambla un context pack con chunks relevantes
    y genera contenido nuevo usando un LLM.

    Attributes:
        query: Query de búsqueda para recuperar contexto relevante
        top_k: Número de chunks a recuperar (default: 20)
        filters: Filtros opcionales (fecha, source, topics, etc.)
        content_type: Tipo de contenido a generar (article, analysis, newsletter, etc.)
        max_tokens: Máximo de tokens para el contenido generado (default: 1000)
        temperature: Temperature para generación LLM (default: 0.7)

    Example:
        >>> command = GenerateContentWithRAGCommand(
        ...     query="Bitcoin ETF regulation impact",
        ...     top_k=15,
        ...     filters={"date_from": "2024-01-01", "topics": ["regulation"]},
        ...     content_type="analysis"
        ... )
    """

    query: str
    top_k: int = 20
    filters: Optional[Dict[str, Any]] = None
    content_type: str = "article"
    max_tokens: int = 1000
    temperature: float = 0.7

    def __post_init__(self):
        """Validaciones básicas del comando."""
        if not self.query or not self.query.strip():
            raise ValueError("query no puede estar vacío")

        if self.top_k <= 0:
            raise ValueError("top_k debe ser mayor a 0")

        if self.top_k > 50:
            raise ValueError("top_k no puede exceder 50")

        if self.max_tokens <= 0:
            raise ValueError("max_tokens debe ser mayor a 0")

        if not (0.0 <= self.temperature <= 1.0):
            raise ValueError("temperature debe estar entre 0.0 y 1.0")

        valid_content_types = ["article", "analysis", "newsletter", "summary", "report"]
        if self.content_type not in valid_content_types:
            raise ValueError(
                f"content_type debe ser uno de: {', '.join(valid_content_types)}"
            )
