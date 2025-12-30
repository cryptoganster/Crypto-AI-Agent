"""Excepciones para extracción de texto plano."""


class PlaintextExtractionError(Exception):
    """Excepción base para errores de extracción de plaintext."""

    pass


class ArticleNotFoundError(PlaintextExtractionError):
    """Artículo no encontrado en BD."""

    def __init__(self, article_id: str):
        self.article_id = article_id
        super().__init__(f"Article not found: {article_id}")


class NoScrapedContentError(PlaintextExtractionError):
    """Artículo no tiene content_scrapped disponible."""

    def __init__(self, article_id: str):
        self.article_id = article_id
        super().__init__(
            f"Article {article_id} has no content_scrapped. "
            "Run scraping phase first."
        )


class PlaintextConversionError(PlaintextExtractionError):
    """Error durante conversión HTML → plaintext."""

    def __init__(self, article_id: str, original_error: Exception):
        self.article_id = article_id
        self.original_error = original_error
        super().__init__(
            f"Failed to convert HTML to plaintext for article {article_id}: "
            f"{str(original_error)}"
        )
