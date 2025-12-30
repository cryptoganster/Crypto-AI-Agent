"""ArticleContentAnalysisPipeline - Process Manager para análisis de contenido.

Este Process Manager coordina el flujo de análisis NLP de artículos:

Pipeline:
1. ArticleMarkdownConverted → CalculateArticleMetricsCommand
2. ArticleMetricsCalculated → DetectArticleLanguageCommand
3. ArticleLanguageDetected → GenerateArticleSummaryCommand
4. ArticleSummaryGenerated → ExtractArticleKeywordsCommand
5. ArticleKeywordsExtracted → CalculateArticleQualityCommand
6. ArticleQualityCalculated → Pipeline completo

Sigue CQRS estricto (Escuela 2):
- Event Handlers solo delegan al Process Manager
- Process Manager coordina el flujo completo
- NO hace queries directas
- SÍ escucha eventos
- SÍ emite comandos
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional

from src.rss.article.domain.events import (
    ArticleKeywordsExtracted,
    ArticleLanguageDetected,
    ArticleMarkdownConverted,
    ArticleMetricsCalculated,
    ArticleQualityCalculated,
    ArticleSummaryGenerated,
)
from src.shared.kernel import IMediator
from src.shared.kernel.logger import ILogger


@dataclass
class AnalysisState:
    """Estado del pipeline de análisis para un artículo."""

    article_id: str
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    # Datos del flujo (event-driven)
    plaintext: Optional[str] = None
    markdown_content: Optional[str] = None
    word_count: Optional[int] = None
    reading_time_minutes: Optional[int] = None
    language_code: Optional[str] = None
    summary: Optional[str] = None
    keywords: Optional[List[str]] = None
    quality_score: Optional[float] = None

    # Metadata
    article_url: Optional[str] = None
    article_title: Optional[str] = None

    # Estado de pasos
    metrics_calculated: bool = False
    language_detected: bool = False
    summary_generated: bool = False
    keywords_extracted: bool = False
    quality_calculated: bool = False

    @property
    def is_complete(self) -> bool:
        """Pipeline completo cuando calidad está calculada."""
        return self.quality_calculated


class RssArticleContentAnalysisPipeline:
    """
    Process Manager para el pipeline de análisis de contenido.

    Coordina el flujo de análisis NLP de forma event-driven:

    1. on_markdown_converted() - Inicia análisis, emite CalculateArticleMetricsCommand
    2. on_metrics_calculated() - Emite DetectArticleLanguageCommand
    3. on_language_detected() - Emite GenerateArticleSummaryCommand
    4. on_summary_generated() - Emite ExtractArticleKeywordsCommand
    5. on_keywords_extracted() - Emite CalculateArticleQualityCommand
    6. on_quality_calculated() - Marca como completo, limpia estado

    Responsabilidades:
    - Escuchar eventos de dominio
    - Emitir comandos al bus (con datos del evento anterior)
    - Trackear estado del pipeline por artículo
    - Pasar datos entre pasos (event-driven)

    NO hace:
    - Queries directas a repositorios
    - Llamadas directas a handlers
    - Lógica de negocio
    """

    def __init__(
        self,
        command_bus: IMediator,
        logger: ILogger,
    ):
        self._command_bus = command_bus
        self._logger = logger.bind(
            layer="application",
            component="ArticleContentAnalysisPipeline",
        )

        # Estado de pipelines activos (en memoria)
        self._active_pipelines: Dict[str, AnalysisState] = {}

    async def on_markdown_converted(self, event: ArticleMarkdownConverted) -> None:
        """
        Maneja ArticleMarkdownConverted e inicia el pipeline de análisis.

        Emite CalculateArticleMetricsCommand con plaintext

        Args:
            event: Evento de markdown convertido
        """
        self._logger.success(
            "✅ Extracción completada, iniciando análisis NLP",
            article_id=event.article_id,
            markdown_length=event.markdown_length,
        )

        # Crear estado del pipeline
        state = AnalysisState(
            article_id=event.article_id,
            plaintext=event.plaintext,
            markdown_content=event.markdown_content,
            article_url=event.article_url,
            article_title=event.article_title,
        )
        self._active_pipelines[event.article_id] = state

        # Emitir comando para calcular métricas (con datos del evento)
        from src.rss.article.app.commands.calculate_metrics.command import (
            CalculateArticleMetricsCommand,
        )

        command = CalculateArticleMetricsCommand(
            article_id=event.article_id,
            plaintext=event.plaintext,  # ← Del evento
            markdown_content=event.markdown_content,
            article_url=event.article_url,
            article_title=event.article_title,
        )

        try:
            await self._command_bus.send(command)

            self._logger.debug(
                "CalculateArticleMetricsCommand emitido",
                article_id=event.article_id,
            )
        except Exception as e:
            self._logger.error(
                "Error emitiendo CalculateArticleMetricsCommand",
                article_id=event.article_id,
                error=str(e),
            )
            # Limpiar estado
            del self._active_pipelines[event.article_id]

    async def on_metrics_calculated(self, event: ArticleMetricsCalculated) -> None:
        """
        Maneja ArticleMetricsCalculated.

        Si cálculo exitoso → Emite DetectArticleLanguageCommand con plaintext
        Si cálculo falló → Log error, limpia estado

        Args:
            event: Evento de métricas calculadas
        """
        if not event.success:
            self._logger.warning(
                "Metrics calculation falló, no se continuará pipeline",
                article_id=event.article_id,
                error=event.error_message,
            )
            # Limpiar estado
            if event.article_id in self._active_pipelines:
                del self._active_pipelines[event.article_id]
            return

        state = self._active_pipelines.get(event.article_id)

        if not state:
            self._logger.warning(
                "Pipeline no encontrado para ArticleMetricsCalculated",
                article_id=event.article_id,
            )
            return

        # Actualizar estado
        state.word_count = event.word_count
        state.reading_time_minutes = event.reading_time_minutes
        state.metrics_calculated = True

        # Emitir comando para detectar idioma (con datos del evento)
        from uuid import UUID

        from src.rss.article.app.commands.detect_language.command import (
            DetectArticleLanguageCommand,
        )

        command = DetectArticleLanguageCommand(
            article_id=UUID(event.article_id),
            plaintext=event.plaintext or state.plaintext,  # ← Del evento o estado
            article_url=event.article_url or state.article_url,
            article_title=event.article_title or state.article_title,
        )

        try:
            await self._command_bus.send(command)

            self._logger.debug(
                "DetectArticleLanguageCommand emitido",
                article_id=event.article_id,
            )
        except Exception as e:
            self._logger.error(
                "Error emitiendo DetectArticleLanguageCommand",
                article_id=event.article_id,
                error=str(e),
            )
            # Limpiar estado
            del self._active_pipelines[event.article_id]

    async def on_language_detected(self, event: ArticleLanguageDetected) -> None:
        """
        Maneja ArticleLanguageDetected.

        Emite GenerateArticleSummaryCommand con plaintext

        Args:
            event: Evento de idioma detectado
        """
        state = self._active_pipelines.get(event.article_id)

        if not state:
            self._logger.warning(
                "Pipeline no encontrado para ArticleLanguageDetected",
                article_id=event.article_id,
            )
            return

        # Actualizar estado
        state.language_code = event.language_code
        state.language_detected = True

        # Emitir comando para generar resumen (con datos del evento)
        from src.rss.article.app.commands.generate_summary.command import (
            GenerateArticleSummaryCommand,
        )

        command = GenerateArticleSummaryCommand(
            article_id=event.article_id,
            plaintext=(
                event.plaintext if hasattr(event, "plaintext") else state.plaintext
            ),  # ← Del evento o estado
            article_url=(
                event.article_url
                if hasattr(event, "article_url")
                else state.article_url
            ),
            article_title=(
                event.article_title
                if hasattr(event, "article_title")
                else state.article_title
            ),
        )

        try:
            await self._command_bus.send(command)

            self._logger.debug(
                "GenerateArticleSummaryCommand emitido",
                article_id=event.article_id,
            )
        except Exception as e:
            self._logger.error(
                "Error emitiendo GenerateArticleSummaryCommand",
                article_id=event.article_id,
                error=str(e),
            )
            # Limpiar estado
            del self._active_pipelines[event.article_id]

    async def on_summary_generated(self, event: ArticleSummaryGenerated) -> None:
        """
        Maneja ArticleSummaryGenerated.

        Si generación exitosa → Emite ExtractArticleKeywordsCommand con plaintext y summary
        Si generación falló → Log error, limpia estado

        Args:
            event: Evento de resumen generado
        """
        if not event.success:
            self._logger.warning(
                "Summary generation falló, no se continuará pipeline",
                article_id=event.article_id,
                error=event.error_message,
            )
            # Limpiar estado
            if event.article_id in self._active_pipelines:
                del self._active_pipelines[event.article_id]
            return

        state = self._active_pipelines.get(event.article_id)

        if not state:
            self._logger.warning(
                "Pipeline no encontrado para ArticleSummaryGenerated",
                article_id=event.article_id,
            )
            return

        # Actualizar estado
        state.summary = event.summary if hasattr(event, "summary") else None
        state.summary_generated = True

        # Emitir comando para extraer keywords (con datos del evento)
        from src.rss.article.app.commands.extract_keywords.command import (
            ExtractArticleKeywordsCommand,
        )

        command = ExtractArticleKeywordsCommand(
            article_id=event.article_id,
            plaintext=(
                event.plaintext if hasattr(event, "plaintext") else state.plaintext
            ),  # ← Del evento o estado
            summary=event.summary if hasattr(event, "summary") else state.summary,
            article_url=(
                event.article_url
                if hasattr(event, "article_url")
                else state.article_url
            ),
            article_title=(
                event.article_title
                if hasattr(event, "article_title")
                else state.article_title
            ),
        )

        try:
            await self._command_bus.send(command)

            self._logger.debug(
                "ExtractArticleKeywordsCommand emitido",
                article_id=event.article_id,
            )
        except Exception as e:
            self._logger.error(
                "Error emitiendo ExtractArticleKeywordsCommand",
                article_id=event.article_id,
                error=str(e),
            )
            # Limpiar estado
            del self._active_pipelines[event.article_id]

    async def on_keywords_extracted(self, event: ArticleKeywordsExtracted) -> None:
        """
        Maneja ArticleKeywordsExtracted.

        Emite CalculateArticleQualityCommand (último paso del análisis)

        Args:
            event: Evento de keywords extraídos
        """
        state = self._active_pipelines.get(event.article_id)

        if not state:
            self._logger.warning(
                "Pipeline no encontrado para ArticleKeywordsExtracted",
                article_id=event.article_id,
            )
            return

        # Actualizar estado
        state.keywords = list(event.keywords) if hasattr(event, "keywords") else None
        state.keywords_extracted = True

        # Emitir comando para calcular calidad (último paso, con datos acumulados)
        from src.rss.article.app.commands.calculate_quality.command import (
            CalculateArticleQualityCommand,
        )

        command = CalculateArticleQualityCommand(
            article_id=event.article_id,
            keywords=(
                list(event.keywords) if hasattr(event, "keywords") else None
            ),  # ← Del evento
            plaintext=state.plaintext,  # ← Del estado
            word_count=state.word_count,  # ← Del estado
        )

        try:
            await self._command_bus.send(command)

            self._logger.debug(
                "CalculateArticleQualityCommand emitido (último paso)",
                article_id=event.article_id,
            )
        except Exception as e:
            self._logger.error(
                "Error emitiendo CalculateArticleQualityCommand",
                article_id=event.article_id,
                error=str(e),
            )
            # Limpiar estado
            del self._active_pipelines[event.article_id]

    async def on_quality_calculated(self, event: ArticleQualityCalculated) -> None:
        """
        Maneja ArticleQualityCalculated.

        Marca el pipeline de análisis como completo y limpia estado.
        Este es el último paso del procesamiento completo del artículo.

        Args:
            event: Evento de calidad calculada
        """
        state = self._active_pipelines.get(event.article_id)

        if not state:
            self._logger.debug(
                "Pipeline no encontrado para ArticleQualityCalculated (puede ser normal)",
                article_id=event.article_id,
            )
            return

        # Actualizar estado
        state.quality_score = event.quality_score
        state.quality_calculated = True

        duration = (datetime.now(timezone.utc) - state.started_at).total_seconds()

        self._logger.success(
            "🎉 Pipeline de análisis de contenido completado - Artículo procesado completamente",
            article_id=event.article_id,
            duration_seconds=duration,
            quality_score=event.quality_score,
            word_count=state.word_count,
            language=state.language_code,
        )

        # Limpiar estado
        del self._active_pipelines[event.article_id]

    def get_pipeline_status(self, article_id: str) -> Optional[Dict]:
        """
        Obtiene el estado actual del pipeline para un artículo.

        Args:
            article_id: ID del artículo

        Returns:
            Dict con estado o None si no existe
        """
        state = self._active_pipelines.get(article_id)

        if not state:
            return None

        return {
            "article_id": state.article_id,
            "metrics_calculated": state.metrics_calculated,
            "language_detected": state.language_detected,
            "summary_generated": state.summary_generated,
            "keywords_extracted": state.keywords_extracted,
            "quality_calculated": state.quality_calculated,
            "is_complete": state.is_complete,
            "started_at": state.started_at.isoformat(),
            "word_count": state.word_count,
            "language_code": state.language_code,
            "quality_score": state.quality_score,
        }


# Alias para compatibilidad
ArticleContentAnalysisPipeline = RssArticleContentAnalysisPipeline
