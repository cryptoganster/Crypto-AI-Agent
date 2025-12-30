"""Excepciones para GenerateArticleSummary command."""


class GenerateArticleSummaryError(Exception):
    """Excepción base para errores de generación de resúmenes."""

    pass


class ArticleNotFoundError(GenerateArticleSummaryError):
    """Artículo no encontrado."""

    def __init__(self, article_id: str):
        super().__init__(f"Artículo no encontrado: {article_id}")
        self.article_id = article_id


class ArticleHasNoContentError(GenerateArticleSummaryError):
    """Artículo sin contenido para generar resumen."""

    def __init__(self, article_id: str):
        super().__init__(f"Artículo sin contenido: {article_id}")
        self.article_id = article_id


class SummaryGenerationError(GenerateArticleSummaryError):
    """Error durante la generación de resúmenes."""

    def __init__(self, article_id: str, reason: str):
        super().__init__(f"Error generando resúmenes para {article_id}: {reason}")
        self.article_id = article_id
        self.reason = reason
