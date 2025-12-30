"""Command para persistir chunks en vector store."""

from dataclasses import dataclass


@dataclass(frozen=True)
class PersistChunksCommand:
    """
    Command para persistir chunks en vector store.

    Este comando persiste chunks validados en el vector store
    y marca los chunks como completados.

    Attributes:
        article_id: ID del artículo cuyos chunks se van a persistir
        correlation_id: ID de correlación para tracking (opcional)
        triggered_by: Identificador de quién/qué disparó el comando (opcional)
    """

    article_id: str
    correlation_id: str | None = None
    triggered_by: str | None = None
