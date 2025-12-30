"""Excepciones para CalculateArticleMetrics command."""


class CalculateArticleMetricsError(Exception):
    """Excepción base para errores de cálculo de métricas."""

    pass


class ArticleNotFoundError(CalculateArticleMetricsError):
    """Artículo no encontrado."""

    def __init__(self, article_id: str):
        super().__init__(f"Artículo no encontrado: {article_id}")
        self.article_id = article_id


class ArticleHasNoContentError(CalculateArticleMetricsError):
    """Artículo sin contenido para calcular métricas."""

    def __init__(self, article_id: str):
        super().__init__(f"Artículo sin contenido: {article_id}")
        self.article_id = article_id


class MetricsCalculationError(CalculateArticleMetricsError):
    """Error durante el cálculo de métricas."""

    def __init__(self, article_id: str, reason: str):
        super().__init__(f"Error calculando métricas para {article_id}: {reason}")
        self.article_id = article_id
        self.reason = reason
