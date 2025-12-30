"""Excepciones para RemoveSource command."""


class RemoveSourceError(Exception):
    """Error base para RemoveSource command."""

    pass


class SourceNotFoundByIdError(RemoveSourceError):
    """Error cuando la fuente RSS no existe por ID."""

    def __init__(self, source_id: str):
        self.source_id = source_id
        super().__init__(f"Fuente RSS con ID {source_id} no encontrada")


class SourceNotFoundError(RemoveSourceError):
    """Error cuando la fuente RSS no existe en el contexto."""

    def __init__(self, source_id: str, context_id: str = ""):
        self.source_id = source_id
        self.context_id = context_id
        context_msg = f" en contexto {context_id}" if context_id else ""
        super().__init__(f"Fuente RSS con ID {source_id} no encontrada{context_msg}")


class SourceRemovalBlockedError(RemoveSourceError):
    """Error cuando la eliminación está bloqueada por artículos asociados."""

    def __init__(self, source_id: str, articles_count: int):
        self.source_id = source_id
        self.articles_count = articles_count
        super().__init__(
            f"Eliminación de fuente {source_id} bloqueada: tiene {articles_count} artículos asociados"
        )


class ContentCleanupError(RemoveSourceError):
    """Error durante la limpieza de contenido asociado."""

    def __init__(self, source_id: str, cleanup_error: str):
        self.source_id = source_id
        self.cleanup_error = cleanup_error
        super().__init__(
            f"Error limpiando contenido de fuente {source_id}: {cleanup_error}"
        )


class SourceArchivalError(RemoveSourceError):
    """Error durante el archivado de la fuente antes de eliminación."""

    def __init__(self, source_id: str, archival_error: str):
        self.source_id = source_id
        self.archival_error = archival_error
        super().__init__(f"Error archivando fuente {source_id}: {archival_error}")


class SourceRemovalConflictError(RemoveSourceError):
    """Error cuando hay conflicto durante la eliminación."""

    def __init__(self, source_id: str, conflict_details: str):
        self.source_id = source_id
        self.conflict_details = conflict_details
        super().__init__(f"Conflicto eliminando fuente {source_id}: {conflict_details}")
