"""ArticleContentExtractionPipeline - Process Manager para extracción de contenido.

Este Process Manager coordina el flujo de extracción de contenido de artículos:

Pipeline:
1. ArticleContentScraped → ExtractArticlePlaintextCommand
2. ArticlePlaintextExtracted → ConvertArticleToMarkdownCommand
3. ArticleMarkdownConverted → Delega a ArticleContentAnalysisPipeline

Sigue CQRS estricto (Escuela 2):
- Event Handlers solo delegan al Process Manager
- Process Manager coordina el flujo completo
- NO hace queries directas
- SÍ escucha eventos
- SÍ emite comandos
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, Optional

from src.rss.article.domain.events import (
    ArticleContentScraped,
    ArticleMarkdownConverted,
    ArticlePlaintextExtracted,
)
from src.shared.kernel import IMediator
from src.shared.kernel.logger import ILogger


@dataclass
class ExtractionState:
    """Estado del pipeline de extracción para un artículo."""

    article_id: str
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    # Datos del flujo (event-driven)
    html_content: Optional[str] = None
    plaintext: Optional[str] = None
    markdown_content: Optional[str] = None

    # Metadata
    article_url: Optional[str] = None
    article_title: Optional[str] = None

    # Estado de pasos
    content_scraped: bool = False
    plaintext_extracted: bool = False
    markdown_converted: bool = False

    @property
    def is_complete(self) -> bool:
        """Pipeline completo cuando markdown está convertido."""
        return self.markdown_converted


class RssArticleContentExtractionPipeline:
    """
    Process Manager para el pipeline de extracción de contenido.

    Coordina el flujo de extracción de forma event-driven:

    1. on_content_scraped() - Inicia extracción, emite ExtractArticlePlaintextCommand
    2. on_plaintext_extracted() - Emite ConvertArticleToMarkdownCommand
    3. on_markdown_converted() - Marca como completo, limpia estado

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
            component="ArticleContentExtractionPipeline",
        )

        # Estado de pipelines activos (en memoria)
        self._active_pipelines: Dict[str, ExtractionState] = {}

    async def on_content_scraped(self, event: ArticleContentScraped) -> None:
        """
        Maneja ArticleContentScraped e inicia el pipeline de extracción.

        Si scraping exitoso → Emite ExtractArticlePlaintextCommand con html_content
        Si scraping falló → Log error, no continúa

        Args:
            event: Evento de contenido scrapeado
        """
        if not event.success:
            self._logger.warning(
                "Content scraping falló, no se iniciará extracción",
                article_id=event.article_id,
                error=event.error_message if hasattr(event, "error_message") else None,
            )
            return

        self._logger.info(
            "Iniciando pipeline de extracción de contenido",
            article_id=event.article_id,
            html_length=len(event.html_content) if event.html_content else 0,
        )

        # Crear estado del pipeline
        state = ExtractionState(
            article_id=event.article_id,
            html_content=event.html_content,
            article_url=event.article_url,
            article_title=event.article_title,
        )
        state.content_scraped = True
        self._active_pipelines[event.article_id] = state

        # Emitir comando para extraer plaintext (con datos del evento)
        from src.rss.article.app.commands.extract_plaintext.command import (
            ExtractArticlePlaintextCommand,
        )

        command = ExtractArticlePlaintextCommand(
            article_id=event.article_id,
            html_content=event.html_content,  # ← Del evento
            article_url=event.article_url,
            article_title=event.article_title,
        )

        try:
            await self._command_bus.send(command)

            self._logger.debug(
                "ExtractArticlePlaintextCommand emitido",
                article_id=event.article_id,
            )
        except Exception as e:
            self._logger.error(
                "Error emitiendo ExtractArticlePlaintextCommand",
                article_id=event.article_id,
                error=str(e),
            )
            # Limpiar estado
            del self._active_pipelines[event.article_id]

    async def on_plaintext_extracted(self, event: ArticlePlaintextExtracted) -> None:
        """
        Maneja ArticlePlaintextExtracted.

        Si extracción exitosa → Emite ConvertArticleToMarkdownCommand con plaintext
        Si extracción falló → Log error, limpia estado

        Args:
            event: Evento de plaintext extraído
        """
        if not event.success:
            self._logger.warning(
                "Plaintext extraction falló, no se convertirá a markdown",
                article_id=event.article_id,
                error=event.error_message if hasattr(event, "error_message") else None,
            )
            # Limpiar estado
            if event.article_id in self._active_pipelines:
                del self._active_pipelines[event.article_id]
            return

        state = self._active_pipelines.get(event.article_id)

        if not state:
            self._logger.warning(
                "Pipeline no encontrado para ArticlePlaintextExtracted",
                article_id=event.article_id,
            )
            return

        # Actualizar estado
        state.plaintext = event.plaintext
        state.plaintext_extracted = True

        # Emitir comando para convertir a markdown (con datos del evento)
        from src.rss.article.app.commands.convert_to_markdown.command import (
            ConvertArticleToMarkdownCommand,
        )

        command = ConvertArticleToMarkdownCommand(
            article_id=event.article_id,
            html_content=event.html_content
            or state.html_content,  # ← Del evento o estado
            plaintext=event.plaintext,  # ← Del evento
            article_url=event.article_url or state.article_url,
            article_title=event.article_title or state.article_title,
        )

        try:
            await self._command_bus.send(command)

            self._logger.debug(
                "ConvertArticleToMarkdownCommand emitido",
                article_id=event.article_id,
            )
        except Exception as e:
            self._logger.error(
                "Error emitiendo ConvertArticleToMarkdownCommand",
                article_id=event.article_id,
                error=str(e),
            )
            # Limpiar estado
            del self._active_pipelines[event.article_id]

    async def on_markdown_converted(self, event: ArticleMarkdownConverted) -> None:
        """
        Maneja ArticleMarkdownConverted.

        Marca el pipeline de extracción como completo y limpia estado.
        El siguiente pipeline (análisis) será iniciado por ArticleContentAnalysisPipeline.

        Args:
            event: Evento de markdown convertido
        """
        state = self._active_pipelines.get(event.article_id)

        if not state:
            self._logger.debug(
                "Pipeline no encontrado para ArticleMarkdownConverted (puede ser normal)",
                article_id=event.article_id,
            )
            return

        # Actualizar estado
        state.markdown_content = (
            event.markdown_content if hasattr(event, "markdown_content") else None
        )
        state.markdown_converted = True

        duration = (datetime.now(timezone.utc) - state.started_at).total_seconds()

        self._logger.success(
            "✅ Pipeline de extracción de contenido completado",
            article_id=event.article_id,
            duration_seconds=duration,
            markdown_length=event.markdown_length,
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
            "content_scraped": state.content_scraped,
            "plaintext_extracted": state.plaintext_extracted,
            "markdown_converted": state.markdown_converted,
            "is_complete": state.is_complete,
            "started_at": state.started_at.isoformat(),
        }


# Alias para compatibilidad
ArticleContentExtractionPipeline = RssArticleContentExtractionPipeline
