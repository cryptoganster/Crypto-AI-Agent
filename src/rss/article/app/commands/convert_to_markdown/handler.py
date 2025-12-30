"""Handler para conversión de HTML a Markdown - Application Layer."""

from uuid import UUID

from src.rss.article.domain.events import ArticleMarkdownConverted
from src.rss.article.domain.interfaces.external import IHtmlToMarkdownConverter
from src.rss.article.domain.interfaces.repositories import (
    IArticleWriteRepository,
)
from src.shared.kernel.logger import ILogger
from src.shared.kernel.uow import IUnitOfWork

from .command import ConvertArticleToMarkdownCommand
from .interface import IConvertArticleToMarkdownHandler
from .result import ConvertArticleToMarkdownResult


class ConvertArticleToMarkdownHandler(IConvertArticleToMarkdownHandler):
    """
    Handler para convertir contenido HTML de artículo a formato Markdown.

    Application Layer - coordina operación usando:
    - IHtmlToMarkdownConverter (servicio externo)
    - IArticleWriteRepository (persistencia)
    - IEventBus (publicación de eventos)

    CQRS ESTRICTO:
    - NO usa ReadRepository (datos vienen del evento anterior)
    - Solo usa WriteRepository para persistir cambios
    - Confía en que el command tiene todos los datos necesarios

    UNIT OF WORK:
    - Usa UoW para manejar transacciones
    - Commit explícito después de save
    - Eventos publicados FUERA de transacción
    """

    def __init__(
        self,
        session_factory,  # Callable[[], AsyncSession]
        html_to_markdown_converter: IHtmlToMarkdownConverter,
        event_bus,  # IEventBus
        logger: ILogger,
    ):
        """
        Inicializa handler con dependencias inyectadas.

        CRÍTICO: Recibe session_factory para crear nueva sesión en cada invocación.

        Args:
            session_factory: Factory para crear nuevas sesiones
            html_to_markdown_converter: Converter de HTML a Markdown (INTERFACE)
            event_bus: Event bus para publicar eventos de dominio
            logger: Logger para observabilidad
        """
        self._session_factory = session_factory
        self._converter = html_to_markdown_converter
        self._event_bus = event_bus
        self._logger = logger

    async def handle(
        self, command: ConvertArticleToMarkdownCommand
    ) -> ConvertArticleToMarkdownResult:
        """
        Convierte contenido HTML procesado a Markdown.

        Args:
            command: Comando con article_id

        Returns:
            ConvertArticleToMarkdownResult con resultado de la operación
        """
        self._logger.info(
            "Iniciando conversión a Markdown",
            article_id=command.article_id,
        )

        try:
            # CQRS Estricto: Validar que el command tenga los datos requeridos
            if not command.html_content:
                error_msg = "html_content is required in command (debe venir del evento ArticlePlaintextExtracted)"
                self._logger.error(
                    error_msg,
                    article_id=command.article_id,
                )
                return ConvertArticleToMarkdownResult.failure(
                    article_id=command.article_id, error_message=error_msg
                )

            # 2. Convertir HTML a Markdown usando servicio externo (sin leer aggregate)
            try:
                # Generar markdown con links (contenido principal)
                markdown_content = self._converter.convert_with_links(
                    command.html_content
                )

                # Generar markdown sin links (para AI/ML processing)
                markdown_without_url = self._converter.convert_without_links(
                    command.html_content
                )

            except ValueError as ve:
                self._logger.warning(
                    "HTML malformado - no se pudo convertir a Markdown",
                    article_id=command.article_id,
                    article_title=command.article_title,
                    error=str(ve),
                    html_preview=command.html_content[:200],
                )
                return ConvertArticleToMarkdownResult.failure(
                    article_id=command.article_id,
                    error_message=f"Malformed HTML: {str(ve)}",
                )

            # Crear NUEVA sesión para esta invocación
            from src.rss.article.infra.persistence.repositories.rss_article_write_repository import (
                RssArticleWriteRepository,
            )
            from src.shared.kernel.uow import SqlAlchemyUnitOfWork

            session = self._session_factory()
            repository = RssArticleWriteRepository(
                session=session,
                logger=self._logger,
            )
            uow = SqlAlchemyUnitOfWork(
                session=session,
                logger=self._logger,
            )

            # Unit of Work: Transacción atómica
            async with uow:
                # 3. Cargar aggregate desde write side (WriteRepository.load)
                article_uuid = UUID(command.article_id)
                article = await repository.load(article_uuid)

                if not article:
                    return ConvertArticleToMarkdownResult.failure(
                        article_id=command.article_id, error_message="Article not found"
                    )

                # 4. Aplicar conversión al agregado (ambas versiones)
                try:
                    article.convert_to_markdown(
                        markdown_content=markdown_content,
                        markdown_without_url=markdown_without_url,
                    )
                except ValueError as ve:
                    self._logger.error(
                        "Error al aplicar markdown al agregado",
                        article_id=command.article_id,
                        error=str(ve),
                    )
                    return ConvertArticleToMarkdownResult.failure(
                        article_id=command.article_id, error_message=str(ve)
                    )

                # 5. Persistir cambios
                await repository.save(article)

                # Commit explícito
                await uow.commit()

            # 6. Emitir evento ENRIQUECIDO con datos para siguiente paso
            # IMPORTANTE: Eventos publicados FUERA de transacción
            await self._event_bus.publish(
                ArticleMarkdownConverted(
                    article_id=command.article_id,
                    markdown_length=len(markdown_content),
                    markdown_content=markdown_content,  # Para siguiente handler
                    plaintext=command.plaintext,  # Del evento anterior
                    article_url=command.article_url,
                    article_title=command.article_title,
                )
            )

            # 7. Marcar eventos del aggregate como committed
            article.mark_events_as_committed()

            self._logger.info(
                "✅ Conversión a Markdown exitosa",
                article_id=command.article_id,
                markdown_length=len(markdown_content),
            )

            # 8. Retornar resultado exitoso
            return ConvertArticleToMarkdownResult.success_result(
                article_id=command.article_id, markdown_length=len(markdown_content)
            )

        except Exception as e:
            # Solo capturar errores inesperados
            self._logger.exception(
                "❌ Error inesperado en ConvertArticleToMarkdownHandler",
                article_id=command.article_id,
                error=str(e),
                error_type=type(e).__name__,
            )
            return ConvertArticleToMarkdownResult.failure(
                article_id=command.article_id,
                error_message=f"Unexpected error: {str(e)}",
            )
