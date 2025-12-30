"""Excepciones específicas para ExtractArticleKeywords command."""


class KeywordExtractionError(Exception):
    """Excepción base para errores de extracción de keywords."""

    pass


class ArticleNotFoundError(KeywordExtractionError):
    """Excepción cuando el artículo no se encuentra."""

    def __init__(self, article_id: str):
        self.article_id = article_id
        super().__init__(f"Artículo {article_id} no encontrado")


class InsufficientContentError(KeywordExtractionError):
    """Excepción cuando el contenido es insuficiente para extraer keywords."""

    def __init__(self, article_id: str, content_length: int):
        self.article_id = article_id
        self.content_length = content_length
        super().__init__(
            f"Contenido insuficiente para artículo {article_id}: "
            f"{content_length} caracteres (mínimo 100)"
        )


class KeywordExtractionServiceError(KeywordExtractionError):
    """Excepción cuando el servicio de extracción falla."""

    def __init__(self, article_id: str, original_error: Exception):
        self.article_id = article_id
        self.original_error = original_error
        super().__init__(
            f"Error en servicio de extracción para artículo {article_id}: "
            f"{str(original_error)}"
        )


class KeywordPersistenceError(KeywordExtractionError):
    """Excepción cuando falla el guardado de keywords en el artículo."""

    def __init__(self, article_id: str, original_error: Exception):
        self.article_id = article_id
        self.original_error = original_error
        super().__init__(
            f"Error guardando keywords en artículo {article_id}: "
            f"{str(original_error)}"
        )


class InvalidLanguageError(KeywordExtractionError):
    """Excepción cuando el idioma especificado no es soportado."""

    def __init__(self, language: str, supported_languages: list):
        self.language = language
        self.supported_languages = supported_languages
        super().__init__(
            f"Idioma '{language}' no soportado. "
            f"Idiomas válidos: {', '.join(supported_languages)}"
        )
