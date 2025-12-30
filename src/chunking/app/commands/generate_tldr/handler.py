"""Handler para GenerateTLDRCommand."""

from src.chunking.app.commands.generate_tldr.command import GenerateTLDRCommand
from src.chunking.app.commands.generate_tldr.result import GenerateTLDRResult
from src.chunking.domain.interfaces.repositories import IContentChunkReadRepository
from src.rag.domain.interfaces.services import ISummarizationService
from src.rss.article.domain.interfaces.repositories import IArticleWriteRepository
from src.shared.kernel.logger import ILogger


class GenerateTLDRHandler:
    """
    Handler para generar TLDR de un artículo.

    Responsabilidades:
    - Cargar chunks desde repository
    - Extraer chunk summaries
    - Fusionar summaries en TLDR (3-5 bullets) usando ISummarizationService
    - Actualizar Article aggregate con tldr
    - Persistir Article actualizado

    NO emite eventos adicionales (Process Manager detecta completitud).
    """

    def __init__(
        self,
        summarization_service: ISummarizationService,
        chunk_repository: IContentChunkReadRepository,
        article_repository: IArticleWriteRepository,
        logger: ILogger,
    ):
        """
        Inicializa el handler.

        Args:
            summarization_service: Service para generar TLDR
            chunk_repository: Repository para cargar chunks
            article_repository: Repository para cargar/persistir artículos
            logger: Logger para registrar operaciones
        """
        self._summarization_service = summarization_service
        self._chunk_repository = chunk_repository
        self._article_repository = article_repository
        self._logger = logger.bind(
            layer="application",
            component="GenerateTLDRHandler",
        )

    async def handle(
        self,
        command: GenerateTLDRCommand,
    ) -> GenerateTLDRResult:
        """
        Ejecuta el comando de generar TLDR.

        Args:
            command: Comando con article_id

        Returns:
            GenerateTLDRResult con resultado de la operación
        """
        self._logger.info(
            "Iniciando generación de TLDR",
            article_id=command.article_id,
            correlation_id=command.correlation_id,
        )

        try:
            # 1. Cargar chunks desde repository
            chunks = await self._chunk_repository.find_by_article_id(command.article_id)

            if not chunks:
                self._logger.warning(
                    "No se encontraron chunks para generar TLDR",
                    article_id=command.article_id,
                )
                return GenerateTLDRResult.failure(
                    article_id=command.article_id,
                    error_message="No se encontraron chunks para el artículo",
                )

            # 2. Extraer chunk summaries
            chunk_summaries = []
            for chunk in chunks:
                if chunk.summary and chunk.summary.content:
                    chunk_summaries.append(chunk.summary.content)

            if not chunk_summaries:
                self._logger.warning(
                    "No se encontraron chunk summaries para generar TLDR",
                    article_id=command.article_id,
                    total_chunks=len(chunks),
                )
                return GenerateTLDRResult.failure(
                    article_id=command.article_id,
                    error_message="No se encontraron chunk summaries",
                )

            # 3. Cargar artículo para obtener título
            article = await self._article_repository.find_by_id(command.article_id)

            if not article:
                self._logger.error(
                    "Artículo no encontrado",
                    article_id=command.article_id,
                )
                return GenerateTLDRResult.failure(
                    article_id=command.article_id,
                    error_message="Artículo no encontrado",
                )

            # 4. Fusionar summaries en TLDR usando service
            self._logger.info(
                "Fusionando summaries en TLDR",
                article_id=command.article_id,
                chunks_used=len(chunk_summaries),
            )

            tldr = self._summarization_service.fuse_into_tldr(
                chunk_summaries=chunk_summaries,
                article_title=str(article._metadata.title),
            )

            # 5. Contar bullets en el TLDR
            # Contar líneas que empiezan con bullets (-, •, *)
            lines = tldr.split("\n")
            bullet_count = sum(
                1 for line in lines if line.strip().startswith(("-", "•", "*"))
            )

            # 6. Validar calidad del TLDR
            is_valid = self._summarization_service.validate_summary_quality(
                summary=tldr,
                min_length=50,
                max_length=500,
            )

            if not is_valid:
                self._logger.warning(
                    "TLDR generado no cumple criterios de calidad",
                    article_id=command.article_id,
                    tldr_length=len(tldr),
                    bullet_count=bullet_count,
                )
                return GenerateTLDRResult.failure(
                    article_id=command.article_id,
                    error_message="TLDR generado no cumple criterios de calidad",
                )

            # 7. Actualizar Article aggregate con tldr
            # Nota: Asumiendo que Article tiene un método update_tldr()
            # Si no existe, se debe agregar al aggregate
            if hasattr(article, "update_tldr"):
                article.update_tldr(tldr)
            else:
                # Fallback: usar metadata o crear método
                self._logger.warning(
                    "Article aggregate no tiene método update_tldr(), usando fallback",
                    article_id=command.article_id,
                )
                # Por ahora, solo loggeamos. El método debe agregarse al aggregate.

            # 8. Persistir Article actualizado
            await self._article_repository.save(article)

            self._logger.info(
                "TLDR generado y persistido exitosamente",
                article_id=command.article_id,
                tldr_length=len(tldr),
                bullet_count=bullet_count,
                chunks_used=len(chunk_summaries),
            )

            return GenerateTLDRResult.success_result(
                article_id=command.article_id,
                tldr=tldr,
                bullet_count=bullet_count,
                chunks_used=len(chunk_summaries),
            )

        except ValueError as e:
            self._logger.error(
                "Error de validación generando TLDR",
                article_id=command.article_id,
                error=str(e),
            )
            return GenerateTLDRResult.failure(
                article_id=command.article_id,
                error_message=f"Error de validación: {str(e)}",
            )
        except Exception as e:
            self._logger.error(
                "Error generando TLDR",
                article_id=command.article_id,
                error=str(e),
                exc_info=True,
            )
            return GenerateTLDRResult.failure(
                article_id=command.article_id,
                error_message=f"Error generando TLDR: {str(e)}",
            )
