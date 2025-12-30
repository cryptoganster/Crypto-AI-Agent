"""Implementación de IRssArticleWriteRepository."""

from typing import Optional

from sqlalchemy import delete, select, text
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from src.rss.article.domain.aggregates import RssArticle

# Alias para compatibilidad
Article = RssArticle
from src.rss.article.domain.interfaces.repositories import (
    IRssArticleWriteRepository,
)
from src.rss.article.domain.value_objects.metadata import RssArticleId
from src.rss.article.infra.persistence.mappers import RssArticleMapper
from src.rss.article.infra.persistence.models import RssArticleModel
from src.shared.kernel import IEventBus
from src.shared.kernel.logger import ILogger


class RssArticleRepositoryException(Exception):
    """Excepción base para errores del repositorio RssArticle."""

    pass


class RssArticleWriteRepository(IRssArticleWriteRepository):
    """
    Implementación del Write Repository para RssArticle aggregate.

    CQRS Command Side - Solo operaciones de escritura.

    Principios implementados:
    - Solo Commands (save, delete)
    - NO commit interno (delegado a Unit of Work si se usa)
    - Automatic event publishing
    - Clean Architecture + DDD + CQRS + SRP
    - NO contiene operaciones de lectura (usar IRssArticleQueries)
    """

    def __init__(
        self,
        session: AsyncSession,
        logger: Optional[ILogger] = None,
        event_publisher: Optional[IEventBus] = None,
    ):
        """
        Inicializa el Write Repository.

        Args:
            session: Sesión AsyncIO de SQLAlchemy
            logger: Logger opcional para observabilidad
            event_publisher: Publisher para eventos de dominio (opcional)
        """
        self._session = session
        self._logger = logger
        self._event_publisher = event_publisher
        self._mapper = RssArticleMapper()

    async def load(self, article_id: RssArticleId) -> Optional[Article]:
        """
        Carga Article aggregate para modificación.

        Usado por Command Handlers que modifican aggregates existentes.

        Args:
            article_id: ID del Article

        Returns:
            Article aggregate o None si no existe
        """
        try:
            # Manejar tanto UUID directo como Value Object con .value
            if hasattr(article_id, "value"):
                # Es un Value Object
                uuid_value = article_id.value
            else:
                # Es un UUID directo
                uuid_value = article_id

            stmt = select(RssArticleModel).where(RssArticleModel.id == uuid_value)

            self._log_info(
                "🔍 LOAD DEBUG",
                article_id_str=str(uuid_value),
                article_id_type=type(uuid_value).__name__,
                article_id_value=uuid_value,
                query=str(stmt),
                session_id=id(self._session),
            )

            result = await self._session.execute(stmt)
            model = result.scalar_one_or_none()

            if model is None:
                self._log_error(
                    "❌ Article no encontrado en load()",
                    article_id=str(uuid_value),
                    session_id=id(self._session),
                )
                return None

            self._log_debug(
                "✅ Article cargado exitosamente",
                article_id=str(uuid_value),
            )

            return self._mapper.to_domain(model)

        except SQLAlchemyError as e:
            self._log_error(
                "Error cargando Article",
                article_id=str(uuid_value),
                error=str(e),
            )
            raise RssArticleRepositoryException(
                f"Error cargando Article {uuid_value}"
            ) from e

    async def save(self, article: Article) -> None:
        """
        Persiste o actualiza Article aggregate.

        - Automatic event publishing si hay event_publisher
        - flush() para consistencia
        - Crea nuevo o actualiza existente automáticamente
        """
        # domain_events ya retorna tupla inmutable, no necesita .copy()
        pending_events = article.domain_events

        try:
            self._log_debug(
                "Guardando Article aggregate",
                article_id=str(article.id),
                title=(
                    str(article.metadata.title)
                    if article.metadata and article.metadata.title
                    else "N/A"
                ),
                events_count=len(pending_events),
            )

            # Verificar si ya existe (usar article.id.value directamente, NO str())
            stmt = select(RssArticleModel).where(RssArticleModel.id == article.id.value)
            result = await self._session.execute(stmt)
            existing_model = result.scalar_one_or_none()

            if existing_model:
                # Actualizar existente
                RssArticleMapper.update_model_from_domain(existing_model, article)
                self._log_debug(
                    "Article actualizado",
                    article_id=str(article.id),
                )
            else:
                # Crear nuevo
                new_model = RssArticleMapper.to_model(article)
                self._session.add(new_model)
                self._log_debug(
                    "Nuevo Article agregado",
                    article_id=str(article.id),
                )

            # Flush para ejecutar INSERT/UPDATE
            # NO commit aquí - delegado a Unit of Work
            await self._session.flush()

            # Publicar eventos de dominio
            if self._event_publisher and pending_events:
                for event in pending_events:
                    await self._event_publisher.publish(event)
                # Los eventos ya fueron copiados al inicio, no necesitamos limpiarlos aquí

                self._log_debug(
                    "Eventos de dominio publicados",
                    article_id=str(article.id),
                    events_count=len(pending_events),
                )

        except IntegrityError as e:
            self._log_error(
                "Error de integridad guardando Article",
                article_id=str(article.id),
                error=str(e),
            )
            raise RssArticleRepositoryException(
                f"Error de integridad al guardar Article {article.id}: {e}"
            ) from e

        except SQLAlchemyError as e:
            self._log_error(
                "Error SQLAlchemy guardando Article",
                article_id=str(article.id),
                error=str(e),
            )
            raise RssArticleRepositoryException(
                f"Error de base de datos al guardar Article {article.id}: {e}"
            ) from e

        except Exception as e:
            self._log_error(
                "Error inesperado guardando Article",
                article_id=str(article.id),
                error=str(e),
            )
            raise RssArticleRepositoryException(
                f"Error inesperado al guardar Article {article.id}: {e}"
            ) from e

    async def delete(self, article_id: RssArticleId) -> bool:
        """
        Elimina un Article por su ID.

        Args:
            article_id: ID del Article a eliminar

        Returns:
            True si se eliminó, False si no existía
        """
        try:
            self._log_debug(
                "Eliminando Article",
                article_id=str(article_id),
            )

            stmt = delete(RssArticleModel).where(RssArticleModel.id == article_id.value)
            result = await self._session.execute(stmt)
            await self._session.flush()

            deleted = result.rowcount > 0

            if deleted:
                self._log_info(
                    "Article eliminado",
                    article_id=str(article_id),
                )
            else:
                self._log_debug(
                    "Article no encontrado para eliminar",
                    article_id=str(article_id),
                )

            return deleted

        except SQLAlchemyError as e:
            self._log_error(
                "Error SQLAlchemy eliminando Article",
                article_id=str(article_id),
                error=str(e),
            )
            raise RssArticleRepositoryException(
                f"Error de base de datos al eliminar Article {article_id}: {e}"
            ) from e

        except Exception as e:
            self._log_error(
                "Error inesperado eliminando Article",
                article_id=str(article_id),
                error=str(e),
            )
            raise RssArticleRepositoryException(
                f"Error inesperado al eliminar Article {article_id}: {e}"
            ) from e

    # === HELPERS DE LOGGING ===

    def _log_debug(self, message: str, **context):
        """Log nivel debug con contexto."""
        if self._logger:
            self._logger.debug(message, repository="ArticleWriteRepository", **context)

    def _log_info(self, message: str, **context):
        """Log nivel info con contexto."""
        if self._logger:
            self._logger.info(message, repository="ArticleWriteRepository", **context)

    def _log_error(self, message: str, **context):
        """Log nivel error con contexto y traceback completo."""
        if self._logger:
            self._logger.error(
                message,
                repository="ArticleWriteRepository",
                exc_info=True,  # Mostrar traceback completo
                **context,
            )
