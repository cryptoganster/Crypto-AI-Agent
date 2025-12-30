"""Excepciones para DetectArticleLanguageCommand."""


class LanguageDetectionError(Exception):
    """Error base para detección de idioma."""

    pass


class ArticleNotFoundError(LanguageDetectionError):
    """Artículo no encontrado."""

    pass


class InsufficientContentError(LanguageDetectionError):
    """Contenido insuficiente para detectar idioma."""

    pass


class DetectionServiceError(LanguageDetectionError):
    """Error en servicio de detección."""

    pass


class LanguagePersistenceError(LanguageDetectionError):
    """Error al persistir idioma detectado."""

    pass
