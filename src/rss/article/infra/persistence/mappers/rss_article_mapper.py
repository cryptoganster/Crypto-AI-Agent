"""RssArticle Mapper - Convierte entre RssArticle aggregate y RssArticleModel."""

from src.rss.article.domain.aggregates import RssArticle
from src.rss.article.domain.value_objects.analysis import (
    ArticleDuplicate,
    ArticleError,
    ArticleMetrics,
    ArticleQuality,
)

# New Value Objects for refactoring
from src.rss.article.domain.value_objects.metadata import (
    ArticleContent,
    ArticleMetadata,
    RssArticleId,
)

# Alias para compatibilidad
ArticleId = RssArticleId
Article = RssArticle
from src.rss.article.domain.value_objects.readability_score import ReadabilityScore
from src.rss.article.domain.value_objects.validation_info import ValidationInfo
from src.rss.article.infra.persistence.models import RssArticleModel
from src.rss.feed.domain.value_objects import SourceId
from src.shared.domain.value_objects import Level


class RssArticleMapper:
    """
    Mapper para convertir entre RssArticle aggregate y RssArticleModel.

    Implementa el patrón Mapper de Infrastructure Layer,
    manteniendo separación entre domain y persistence.
    """

    @staticmethod
    def to_domain(model: RssArticleModel) -> RssArticle:
        """
        Convierte RssArticleModel a RssArticle aggregate.

        Args:
            model: Modelo de persistencia

        Returns:
            Article aggregate reconstruido

        Raises:
            ValueError: Si los datos del modelo son inválidos
        """
        if not model:
            raise ValueError("ArticleModel no puede ser None")

        try:
            # Imports necesarios
            from src.rss.article.domain.value_objects.analysis import KeywordCollection
            from src.rss.article.domain.value_objects.metadata import (
                ArticleAuthor,
                ArticleCategory,
                ArticleLanguage,
                ArticleMetadata,
                ArticleSummary,
                ArticleThumbnailUrl,
                ArticleTitle,
                ArticleUrl,
            )

            # 1. Crear ArticleMetadata (Requirements 7.2)
            # Nota: ArticleMetadata contiene id, source_id, title, url y otros metadatos
            from src.rss.feed.domain.value_objects import SourceId
            from src.shared.domain.value_objects import TagCollection

            metadata = ArticleMetadata.create(
                id=ArticleId(str(model.id)),  # type: ignore
                source_id=SourceId(str(model.source_id)),  # type: ignore
                title=ArticleTitle(model.title),  # type: ignore
                url=ArticleUrl(model.url),  # type: ignore
                summary=ArticleSummary.create(model.summary) if model.summary else None,  # type: ignore
                thumbnail_url=ArticleThumbnailUrl.create(model.thumbnail_url) if model.thumbnail_url else None,  # type: ignore
                author=ArticleAuthor.create(model.author) if model.author else None,  # type: ignore
                language=ArticleLanguage(code=model.language, confidence=1.0) if model.language else None,  # type: ignore
                category=ArticleCategory.create(model.categories[0], confidence=1.0) if model.categories else None,  # type: ignore
            )

            # 3. Crear Article usando constructor directo (no factory para evitar eventos)
            article = Article.__new__(Article)  # Crear sin llamar __init__

            # 4. Asignar Value Objects compuestos
            article._metadata = metadata  # type: ignore

            # 5. Timestamps VO (Requirements 7.2)
            from src.rss.article.domain.value_objects.metadata import (
                ArticleTimestamps,
            )

            article._timestamps = ArticleTimestamps(
                created_at=model.created_at,
                updated_at=model.updated_at,
                version=int(model.version) if model.version else 0,
            )  # type: ignore

            # 6. Pub date VO (Requirements 7.2)
            from src.rss.article.domain.value_objects.metadata import ArticlePubDate

            article._pub_date = (
                ArticlePubDate(model.published_at) if model.published_at else None
            )  # type: ignore

            # 7. Validation info
            article._validation_info = (  # type: ignore
                ValidationInfo.create(
                    score=model.validation_score,
                    validated_by=model.validated_by,
                    validated_at=model.validated_at,
                )
                if model.validation_score is not None and model.validated_by is not None
                else None
            )

            # 8. Inicializar eventos vacíos (no debe emitir eventos al reconstruir)
            article._domain_events = []
            article._uncommitted_events = []

            # 9. Llamar super().__init__() para inicializar IAggregateRoot
            super(Article, article).__init__()

            # 10. Reconstruir otros Value Objects compuestos
            # ArticleContent VO
            article._content = (
                ArticleContent(
                    markdown=model.content_markdown,  # type: ignore
                    markdown_without_url=model.markdown_without_url,  # type: ignore
                    plaintext=model.content_plaintext,  # type: ignore
                    scraped=model.content_scraped,  # type: ignore
                )
                if any(
                    [
                        model.content_markdown,
                        model.markdown_without_url,
                        model.content_plaintext,
                        model.content_scraped,
                    ]
                )
                else ArticleContent.empty()
            )  # type: ignore

            # ArticleMetrics VO
            article._metrics = ArticleMetrics.create(
                word_count=model.word_count,  # type: ignore
                reading_time_minutes=model.reading_time_minutes,  # type: ignore
            )

            # Feed metadata (guid, pub_date, description) - reconstruir en metadata
            # Estos campos ya están en ArticleMetadata, necesitamos reconstruir el metadata con ellos
            if model.rss_guid or model.pub_date or model.description:
                from src.rss.article.domain.value_objects.metadata import (
                    ArticleDescription,
                    ArticleGuid,
                    ArticlePubDate,
                )

                # Reconstruir metadata con campos RSS
                article._metadata = ArticleMetadata.create(
                    id=metadata.id,
                    source_id=metadata.source_id,
                    title=metadata.title,
                    url=metadata.url,
                    summary=metadata.summary,
                    thumbnail_url=metadata.thumbnail_url,
                    author=metadata.author,
                    language=metadata.language,
                    category=metadata.category,
                    guid=ArticleGuid(model.rss_guid) if model.rss_guid else None,  # type: ignore
                    pub_date=ArticlePubDate(model.pub_date) if model.pub_date else None,  # type: ignore
                    description=ArticleDescription(model.description) if model.description else None,  # type: ignore
                )

            # QualityAssessment VO
            # Convertir quality_score de BD (0-100) a aggregate (0.0-1.0)
            article._quality = (
                ArticleQuality(
                    quality_level=Level.from_string(model.quality_level) if model.quality_level else None,  # type: ignore
                    readability_score=ReadabilityScore(value=model.readability_score) if model.readability_score is not None else None,  # type: ignore
                    content_hash=model.content_hash,  # type: ignore
                )
                if any(
                    [
                        model.quality_level,
                        model.readability_score is not None,
                        model.content_hash,
                    ]
                )
                else ArticleQuality.empty()
            )  # type: ignore

            # ArticleDuplicate VO
            article._duplication = (
                ArticleDuplicate.duplicate_of(
                    ArticleId(str(model.duplicate_of_id))  # type: ignore
                )
                if model.is_duplicate and model.duplicate_of_id
                else ArticleDuplicate.not_duplicate()
            )  # type: ignore

            # ArticleError VO
            # Solo crear error si has_error es True Y todos los campos requeridos están presentes y no vacíos
            has_valid_error_fields = (
                model.has_error  # type: ignore
                and model.error_type
                and str(model.error_type).strip()  # type: ignore
                and model.error_message
                and str(model.error_message).strip()  # type: ignore
                and model.error_marked_by
                and str(model.error_marked_by).strip()  # type: ignore
            )
            if has_valid_error_fields:
                article._error = ArticleError.create_error(
                    error_type=model.error_type,  # type: ignore
                    error_message=model.error_message,  # type: ignore
                    marked_by=model.error_marked_by,  # type: ignore
                    marked_at=model.error_marked_at,  # type: ignore
                )
            else:
                article._error = ArticleError.no_error()  # type: ignore

            return article

        except Exception as e:
            raise ValueError(
                f"Error convirtiendo ArticleModel a Article: {str(e)}"
            ) from e

    @staticmethod
    def to_model(article: Article) -> RssArticleModel:
        """
        Convierte Article aggregate a ArticleModel.

        Args:
            article: Article aggregate

        Returns:
            ArticleModel para persistencia

        Raises:
            ValueError: Si el Article es inválido
        """
        if not article:
            raise ValueError("Article no puede ser None")

        try:
            # Extraer campos desde metadata (nuevo aggregate)
            article_id = str(article.id)  # article.id retorna ArticleId
            source_id = str(article.metadata.source_id)  # source_id está en metadata
            url = article.metadata.url.value

            # Extraer campos desde metadata_vo (Requirements 7.3)
            title = article.metadata.title.value
            summary = (
                str(article.metadata.summary) if article.metadata.summary else None
            )
            thumbnail_url = (
                str(article.metadata.thumbnail_url)
                if article.metadata.thumbnail_url
                else None
            )
            author = str(article.metadata.author) if article.metadata.author else None
            language = (
                article.metadata.language.code if article.metadata.language else None
            )
            category = (
                str(article.metadata.category) if article.metadata.category else None
            )
            tags = (
                list(article.metadata.tags.sorted_tags) if article.metadata.tags else []
            )
            keywords = (
                list(article.metadata.keywords.keywords)
                if article.metadata.keywords
                else []
            )

            # Extraer campos de contenido desde article.content
            content_markdown = article.content.markdown
            markdown_without_url = article.content.markdown_without_url
            content_plaintext = article.content.plaintext
            content_scraped = article.content.scraped

            # Extraer métricas desde article.metrics
            word_count = (
                article.metrics.word_count.value if article.metrics.word_count else None
            )
            reading_time_minutes = (
                article.metrics.reading_time.minutes
                if article.metrics.reading_time
                else None
            )

            # Extraer feed metadata desde article.metadata
            rss_guid = str(article.metadata.guid) if article.metadata.guid else None
            pub_date = (
                article.metadata.pub_date.value if article.metadata.pub_date else None
            )
            description = (
                str(article.metadata.description)
                if article.metadata.description
                else None
            )

            # Extraer calidad desde article.quality
            quality_level = (
                str(article.quality.quality_level)
                if article.quality.quality_level
                else None
            )
            # Convertir quality_score de aggregate (0.0-1.0) a BD (0-100)
            quality_score = (
                int(article.quality.quality_score * 100)
                if article.quality.quality_score is not None
                else None
            )
            readability_score = (
                article.quality.readability_score.value
                if article.quality.readability_score
                else None
            )
            content_hash = article.quality.content_hash

            # Extraer duplicación desde article.duplication
            is_duplicate = article.duplication.is_duplicate
            duplicate_of_id = (
                str(article.duplication.duplicate_of_article_id)
                if article.duplication.duplicate_of_article_id
                else None
            )

            # Extraer error desde article.error
            has_error = article.error.has_error
            error_type = article.error.error_type
            error_message = article.error.error_message
            error_marked_by = article.error.error_marked_by
            error_marked_at = article.error.error_marked_at

            return RssArticleModel(
                id=article_id,
                title=title,
                url=url,
                source_id=source_id,
                # Campos extraídos desde metadata_vo
                summary=summary,
                thumbnail_url=thumbnail_url,
                author=author,
                language=language,
                tags=tags,
                keywords=keywords,
                categories=[category] if category else [],
                # Campos extraídos desde quality_vo
                content_hash=content_hash,
                quality_level=quality_level,
                quality_score=quality_score,
                readability_score=readability_score,
                # Campos de procesamiento desde ArticleContent VO
                content_scraped=content_scraped,
                content_plaintext=content_plaintext,
                content_markdown=content_markdown,
                markdown_without_url=markdown_without_url,
                # Métricas desde ArticleMetrics VO
                word_count=word_count,
                reading_time_minutes=reading_time_minutes,
                # Metadatos de feed desde ArticleMetadata
                rss_guid=rss_guid,
                pub_date=pub_date,
                description=description,
                # Metadatos tipados desde ArticleDuplicate VO
                is_duplicate=is_duplicate,
                duplicate_of_id=duplicate_of_id,
                # Validación
                validation_score=(
                    article.validation_info.score.value
                    if article.validation_info
                    else None
                ),
                validated_by=(
                    article.validation_info.validated_by
                    if article.validation_info
                    else None
                ),
                validated_at=(
                    article.validation_info.validated_at
                    if article.validation_info
                    else None
                ),
                # Error desde ArticleError VO
                has_error=has_error,
                error_type=error_type,
                error_message=error_message,
                error_marked_by=error_marked_by,
                error_marked_at=error_marked_at,
                coin_mentions=None,
                is_coin_checked=False,
                published_at=article.published_at,
                archived_at=None,
                created_at=article.created_at,
                updated_at=article.updated_at,
                version=article.timestamps.version,
            )

        except Exception as e:
            raise ValueError(
                f"Error convirtiendo Article a ArticleModel: {str(e)}"
            ) from e

    @staticmethod
    def update_model_from_domain(model: RssArticleModel, article: Article) -> None:
        """
        Actualiza ArticleModel existente con datos del Article aggregate.

        Útil para operaciones de actualización que preservan ciertos campos
        del modelo (como timestamps automáticos).

        Args:
            model: Modelo existente a actualizar
            article: Article aggregate con datos nuevos
        """
        if not model:
            raise ValueError("ArticleModel no puede ser None")
        if not article:
            raise ValueError("Article no puede ser None")

        try:
            # Actualizar campos desde metadata (Requirements 7.5)
            model.id = str(article.id)  # type: ignore
            model.source_id = str(article.metadata.source_id)  # type: ignore
            model.url = article.metadata.url.value  # type: ignore

            # Actualizar campos desde metadata_vo (Requirements 7.5)
            model.title = article.metadata.title.value  # type: ignore

            summary = (
                str(article.metadata.summary) if article.metadata.summary else None
            )
            model.summary = summary  # type: ignore

            thumbnail_url = (
                str(article.metadata.thumbnail_url)
                if article.metadata.thumbnail_url
                else None
            )
            if thumbnail_url is not None:
                model.thumbnail_url = thumbnail_url  # type: ignore

            author = str(article.metadata.author) if article.metadata.author else None
            model.author = author  # type: ignore

            language = (
                article.metadata.language.code if article.metadata.language else None
            )
            model.language = language  # type: ignore

            tags = (
                list(article.metadata.tags.sorted_tags) if article.metadata.tags else []
            )
            model.tags = tags  # type: ignore

            # Keywords solo si article tiene valores (no sobrescribir keywords generadas)
            keywords = (
                list(article.metadata.keywords.keywords)
                if article.metadata.keywords
                else []
            )
            if keywords:
                model.keywords = keywords  # type: ignore

            category = (
                str(article.metadata.category) if article.metadata.category else None
            )
            model.categories = [category] if category else []  # type: ignore

            # Extraer content_hash desde quality_vo
            model.content_hash = article.quality.content_hash  # type: ignore

            # Actualizar calidad desde quality_vo
            quality_level = (
                str(article.quality.quality_level)
                if article.quality.quality_level
                else None
            )
            model.quality_level = quality_level  # type: ignore

            # Convertir quality_score de aggregate (0.0-1.0) a BD (0-100)
            quality_score = (
                int(article.quality.quality_score * 100)
                if article.quality.quality_score is not None
                else None
            )
            model.quality_score = quality_score  # type: ignore

            # Actualizar campos de procesamiento desde content_vo - SOLO si article tiene valores (no sobrescribir con None)
            # Esto preserva campos procesados cuando se actualiza article desde RSS fetch
            if article.content.scraped is not None:
                model.content_scraped = article.content.scraped  # type: ignore
            if article.content.plaintext is not None:
                model.content_plaintext = article.content.plaintext  # type: ignore
            if article.content.markdown is not None:
                model.content_markdown = article.content.markdown  # type: ignore
            if article.content.markdown_without_url is not None:
                model.markdown_without_url = article.content.markdown_without_url  # type: ignore

            # Actualizar métricas desde metrics_vo
            word_count = (
                article.metrics.word_count.value if article.metrics.word_count else None
            )
            if word_count is not None:
                model.word_count = word_count  # type: ignore

            reading_time_minutes = (
                article.metrics.reading_time.minutes
                if article.metrics.reading_time
                else None
            )
            if reading_time_minutes is not None:
                model.reading_time_minutes = reading_time_minutes  # type: ignore

            # Actualizar metadatos RSS nativos desde metadata - solo si article tiene valores
            if article.metadata.guid is not None:
                model.rss_guid = str(article.metadata.guid) if hasattr(article.metadata.guid, "value") else str(article.metadata.guid)  # type: ignore
            if article.metadata.pub_date is not None:
                model.pub_date = article.metadata.pub_date.value if hasattr(article.metadata.pub_date, "value") else article.metadata.pub_date  # type: ignore
            if article.metadata.description is not None:
                model.description = str(article.metadata.description) if hasattr(article.metadata.description, "value") else str(article.metadata.description)  # type: ignore

            # Actualizar metadatos tipados desde duplication_vo
            model.is_duplicate = article.duplication.is_duplicate  # type: ignore
            duplicate_of_id = (
                str(article.duplication.duplicate_of_article_id)
                if article.duplication.duplicate_of_article_id
                else None
            )
            model.duplicate_of_id = duplicate_of_id  # type: ignore

            # Actualizar validación desde validation_info
            model.validation_score = article.validation_info.score.value if article.validation_info else None  # type: ignore
            model.validated_by = article.validation_info.validated_by if article.validation_info else None  # type: ignore
            model.validated_at = article.validation_info.validated_at if article.validation_info else None  # type: ignore

            # Actualizar error desde error_vo
            model.has_error = article.error.has_error  # type: ignore
            model.error_type = article.error.error_type  # type: ignore
            model.error_message = article.error.error_message  # type: ignore
            model.error_marked_by = article.error.error_marked_by  # type: ignore
            model.error_marked_at = article.error.error_marked_at  # type: ignore

            # Actualizar readability desde quality_vo
            readability_score = (
                article.quality.readability_score.value
                if article.quality.readability_score
                else None
            )
            model.readability_score = readability_score  # type: ignore

            model.coin_mentions = None  # type: ignore
            model.is_coin_checked = False  # type: ignore

            # Actualizar timestamps de workflow
            model.published_at = article.published_at  # type: ignore
            model.archived_at = None

            # Actualizar versión desde timestamps
            model.version = article.timestamps.version  # type: ignore

            # updated_at se actualizará automáticamente por SQLAlchemy onupdate

        except Exception as e:
            raise ValueError(
                f"Error actualizando ArticleModel desde Article: {str(e)}"
            ) from e
