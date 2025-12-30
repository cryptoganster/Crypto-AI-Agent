"""Value Object para métricas de contenido del artículo."""

from dataclasses import dataclass
from typing import Optional

from .reading_time import ReadingTime
from .word_count import WordCount


@dataclass(frozen=True)
class RssArticleMetrics:
    """
    Value Object para métricas calculadas del contenido.

    Encapsula métricas derivadas del análisis del contenido del artículo.

    Invariantes:
    - word_count debe ser no negativo (validado por WordCount VO)
    - reading_time debe ser no negativo (validado por ReadingTime VO)
    - Los campos son inmutables (frozen dataclass)

    Attributes:
        word_count: Conteo de palabras del artículo
        reading_time: Tiempo estimado de lectura
    """

    word_count: Optional[WordCount] = None
    reading_time: Optional[ReadingTime] = None

    @staticmethod
    def empty() -> "RssArticleMetrics":
        """
        Crea una instancia vacía sin métricas.

        Útil para inicialización de agregados sin métricas calculadas aún.

        Returns:
            RssArticleMetrics con todos los campos None

        Example:
            >>> metrics = RssArticleMetrics.empty()
            >>> metrics.word_count is None
            True
            >>> metrics.reading_time is None
            True
        """
        return RssArticleMetrics()

    @staticmethod
    def create(
        word_count: Optional[int], reading_time_minutes: Optional[int]
    ) -> "RssArticleMetrics":
        """
        Factory method para crear RssArticleMetrics con validaciones.

        Crea instancias de WordCount y ReadingTime VOs con validación automática.

        Args:
            word_count: Número de palabras (debe ser >= 0 si no es None)
            reading_time_minutes: Minutos de lectura (debe ser >= 0 si no es None)

        Returns:
            RssArticleMetrics con VOs creados

        Raises:
            ValueError: Si word_count o reading_time_minutes son negativos
            TypeError: Si los valores no son enteros

        Example:
            >>> metrics = RssArticleMetrics.create(word_count=500, reading_time_minutes=3)
            >>> metrics.word_count.value
            500
            >>> metrics.reading_time.minutes
            3
        """
        wc = WordCount(value=word_count) if word_count is not None else None
        rt = (
            ReadingTime(minutes=reading_time_minutes)
            if reading_time_minutes is not None
            else None
        )
        return RssArticleMetrics(word_count=wc, reading_time=rt)

    @property
    def has_metrics(self) -> bool:
        """
        Verifica si tiene al menos una métrica calculada.

        Returns:
            True si word_count o reading_time no son None
        """
        return self.word_count is not None or self.reading_time is not None

    @property
    def has_complete_metrics(self) -> bool:
        """
        Verifica si tiene todas las métricas calculadas.

        Returns:
            True si tanto word_count como reading_time no son None
        """
        return self.word_count is not None and self.reading_time is not None

    def with_word_count(self, word_count: WordCount) -> "RssArticleMetrics":
        """
        Retorna nueva instancia con word_count actualizado.

        Args:
            word_count: Nuevo WordCount VO

        Returns:
            Nueva instancia de RssArticleMetrics con word_count actualizado
        """
        return RssArticleMetrics(word_count=word_count, reading_time=self.reading_time)

    def with_reading_time(self, reading_time: ReadingTime) -> "RssArticleMetrics":
        """
        Retorna nueva instancia con reading_time actualizado.

        Args:
            reading_time: Nuevo ReadingTime VO

        Returns:
            Nueva instancia de RssArticleMetrics con reading_time actualizado
        """
        return RssArticleMetrics(word_count=self.word_count, reading_time=reading_time)


# Alias para compatibilidad
ArticleMetrics = RssArticleMetrics
