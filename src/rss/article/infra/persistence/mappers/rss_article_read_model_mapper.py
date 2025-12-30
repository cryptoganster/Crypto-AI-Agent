"""Mapper de RssArticleModel a ArticleReadModel (Read Side).

CQRS ESTRICTO: Este mapper convierte modelos ORM a Read Models planos.
NO reconstruye Aggregates, solo extrae datos.
"""

from uuid import UUID

from src.rss.article.domain.read_models import ArticleReadModel
from src.rss.article.infra.persistence.models import RssArticleModel


class RssArticleReadModelMapper:
    """
    Mapper para convertir RssArticleModel a ArticleReadModel.

    CQRS Read Side: Convierte ORM a Read Model (solo datos).

    Para Write Side, usar RssArticleMapper.to_domain() que devuelve Aggregate.
    """

    @staticmethod
    def _determine_status(model: RssArticleModel) -> str:
        """
        Determina el status del artículo basándose en timestamps.

        Args:
            model: Modelo ORM de Article

        Returns:
            Status del artículo: "ARCHIVED", "PUBLISHED", o "DRAFT"
        """
        if model.archived_at is not None:
            return "ARCHIVED"
        elif model.published_at is not None:
            return "PUBLISHED"
        else:
            return "DRAFT"

    @staticmethod
    def to_read_model(model: RssArticleModel) -> ArticleReadModel:
        """
        Convierte RssArticleModel a ArticleReadModel (read side).

        Args:
            model: Modelo ORM de SQLAlchemy

        Returns:
            ArticleReadModel con datos planos (sin comportamiento)
        """
        if not model:
            raise ValueError("RssArticleModel no puede ser None")

        return ArticleReadModel(
            # Identificación
            id=UUID(str(model.id)),
            source_id=UUID(str(model.source_id)),
            # Metadata
            title=model.title,
            url=model.url,
            summary=model.summary,
            author=model.author,
            language=model.language,
            thumbnail_url=model.thumbnail_url,
            # RSS Metadata
            rss_guid=model.rss_guid,
            pub_date=model.pub_date,
            # Content
            content_scraped=model.content_scraped,
            content_plaintext=model.content_plaintext,
            content_markdown=model.content_markdown,
            markdown_without_url=model.markdown_without_url,
            # Analysis
            keywords=model.keywords if model.keywords else None,
            categories=model.categories if model.categories else None,
            # Metrics
            word_count=model.word_count,
            reading_time_minutes=model.reading_time_minutes,
            # Quality
            quality_score=model.quality_score,
            validation_score=model.validation_score,
            validated_by=model.validated_by,
            # Timestamps
            published_at=model.published_at,
            created_at=model.created_at,
            updated_at=model.updated_at,
            version=int(model.version) if model.version else 0,
            # Status (calculado desde timestamps)
            status=RssArticleReadModelMapper._determine_status(model),
        )

    @staticmethod
    def to_read_model_list(models: list[RssArticleModel]) -> list[ArticleReadModel]:
        """
        Convierte lista de RssArticleModel a lista de ArticleReadModel.

        Args:
            models: Lista de modelos ORM

        Returns:
            Lista de Read Models
        """
        return [ArticleReadModelMapper.to_read_model(model) for model in models]
