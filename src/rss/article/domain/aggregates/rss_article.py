"""Article Aggregate Root.

Responsabilidades:
- Mantener identidad y metadata del artículo
- Coordinar actualizaciones de contenido
- Emitir eventos de dominio
- Garantizar invariantes

Creación: Usar ArticleFactory.create_article()
"""

from datetime import datetime, timezone

# Type hints para métodos (importados solo para type checking)
from typing import TYPE_CHECKING, List, Optional, Sequence

from src.rss.article.domain.strategies.validation import (
    NonEmptyStringValidationStrategy,
    ScoreValidationStrategy,
)
from src.rss.article.domain.value_objects.analysis import (
    ArticleDuplicate,
    ArticleError,
    ArticleMetrics,
    ArticleQuality,
    KeywordCollection,
)
from src.rss.article.domain.value_objects.metadata import ArticleMetadata
from src.rss.article.domain.value_objects.validation_info import ValidationInfo
from src.shared.domain.value_objects import Level
from src.shared.kernel import IAggregateRoot, IDomainEvent

if TYPE_CHECKING:
    from src.rss.article.domain.value_objects.metadata import (
        ArticleContent,
        ArticleId,
        ArticlePubDate,
        ArticleSummary,
        ArticleThumbnailUrl,
        ArticleTimestamps,
        ArticleTitle,
    )


class RssArticle(IAggregateRoot):
    """Aggregate Root para artículos RSS.

    Value Objects compuestos:
    - metadata: ArticleMetadata (identidad y metadata del artículo)
    - content: ArticleContent (markdown, plaintext, scraped)
    - quality: ArticleQuality (quality_level, readability, hash)
    - timestamps: ArticleTimestamps (created_at, updated_at, version)
    - metrics: ArticleMetrics (word_count, reading_time)
    - duplication: ArticleDuplicate (is_duplicate, duplicate_of)
    - error: ArticleError (has_error, error_type, error_message)
    """

    # Validation strategies (class-level)
    _score_validator = ScoreValidationStrategy()
    _string_validator = NonEmptyStringValidationStrategy()

    def __init__(
        self,
        metadata: ArticleMetadata,
    ) -> None:
        """Inicializa aggregate. Usar ArticleFactory.create_article()."""
        # ✅ CORRECTO - super().__init__() primero
        super().__init__()

        # Value Objects compuestos principales
        self._metadata: ArticleMetadata = metadata

        # Importar VOs solo cuando se necesitan instanciar
        from src.rss.article.domain.value_objects.metadata import (
            ArticleContent,
            ArticlePubDate,
            ArticleTimestamps,
        )

        self._timestamps: "ArticleTimestamps" = ArticleTimestamps.create()
        self._pub_date: Optional["ArticlePubDate"] = None  # None = draft

        # Otros atributos
        self._validation_info: Optional[ValidationInfo] = None

        # Otros Value Objects compuestos
        self._content: "ArticleContent" = ArticleContent.empty()
        self._metrics: ArticleMetrics = ArticleMetrics.empty()
        self._quality: ArticleQuality = ArticleQuality.empty()
        self._duplication: ArticleDuplicate = ArticleDuplicate.not_duplicate()
        self._error: ArticleError = ArticleError.no_error()

        # Eventos de dominio ya inicializados por IAggregateRoot
        # (no necesitamos inicializarlos aquí)

    # ===== Core Properties =====

    @property
    def id(self) -> "ArticleId":
        """ID único del artículo."""
        return self._metadata.id

    @property
    def metadata(self) -> ArticleMetadata:
        """Metadata completo del artículo."""
        return self._metadata

    @property
    def timestamps(self) -> "ArticleTimestamps":
        """Timestamps del artículo."""
        return self._timestamps

    @property
    def content(self) -> "ArticleContent":
        """Contenido del artículo."""
        return self._content

    @property
    def quality(self) -> ArticleQuality:
        """Calidad del artículo."""
        return self._quality

    @property
    def metrics(self) -> ArticleMetrics:
        """Métricas del artículo."""
        return self._metrics

    @property
    def duplication(self) -> ArticleDuplicate:
        """Estado de duplicación."""
        return self._duplication

    @property
    def error(self) -> ArticleError:
        """Estado de error."""
        return self._error

    @property
    def validation_info(self) -> Optional[ValidationInfo]:
        """Información de validación."""
        return self._validation_info

    # ===== Convenience Properties =====

    @property
    def created_at(self) -> datetime:
        """Fecha de creación."""
        return self._timestamps.created_at

    @property
    def updated_at(self) -> datetime:
        """Fecha de última actualización."""
        return self._timestamps.updated_at

    @property
    def published_at(self) -> Optional[datetime]:
        """Fecha de publicación."""
        return self._pub_date.value if self._pub_date else None

    @property
    def domain_events(self) -> Sequence[IDomainEvent]:
        """Eventos de dominio."""
        return tuple(self._domain_events)

    # ===== Content Update Methods =====

    def update_markdown(self, markdown: Optional[str]) -> None:
        """Actualiza contenido markdown."""
        self._content = self._content.with_markdown(markdown)
        self._timestamps = self._timestamps.touch()

    def update_markdown_without_url(self, markdown_without_url: Optional[str]) -> None:
        """Actualiza contenido markdown sin URLs (para AI/ML processing)."""
        self._content = self._content.with_markdown_without_url(markdown_without_url)
        self._timestamps = self._timestamps.touch()

    def update_plaintext(self, plaintext: Optional[str]) -> None:
        """Actualiza contenido plaintext."""
        self._content = self._content.with_plaintext(plaintext)
        self._timestamps = self._timestamps.touch()

    def update_scraped(self, scraped: Optional[str]) -> None:
        """Actualiza contenido scrapeado."""
        self._content = self._content.with_scraped(scraped)
        self._timestamps = self._timestamps.touch()

    def set_keywords(self, keywords: List[str]) -> None:
        """Establece keywords (calculados por ArticleKeywordExtractionService)."""
        from dataclasses import replace

        new_keywords = (
            KeywordCollection.from_list(keywords)
            if keywords
            else KeywordCollection.empty()
        )
        self._metadata = replace(self._metadata, keywords=new_keywords)
        self._timestamps = self._timestamps.touch()

    # ===== Quality Update Methods =====

    def update_quality_level(self, quality_level: Level) -> None:
        """Actualiza nivel de calidad."""
        self._quality = self._quality.with_quality_level(quality_level)
        self._timestamps = self._timestamps.touch()

    def update_readability_score(self, score: float) -> None:
        """Actualiza readability score. Valida que esté entre 0 y 1."""
        self._score_validator.validate(score, "readability_score")

        from src.rss.article.domain.value_objects import ReadabilityScore

        readability_vo = ReadabilityScore(value=score)
        self._quality = self._quality.with_readability_score(readability_vo)
        self._timestamps = self._timestamps.touch()

    def update_content_hash(self, content_hash: str) -> None:
        """Actualiza content hash."""
        if not content_hash or not content_hash.strip():
            raise ValueError("content_hash no puede estar vacío")

        self._quality = self._quality.with_content_hash(content_hash.strip())
        self._timestamps = self._timestamps.touch()

    def clear_quality_level(self) -> None:
        """Limpia quality level."""
        self._quality = ArticleQuality(
            quality_level=None,
            readability_score=self._quality.readability_score,
            content_hash=self._quality.content_hash,
        )
        self._timestamps = self._timestamps.touch()

    def clear_readability_score(self) -> None:
        """Limpia readability score."""
        self._quality = ArticleQuality(
            quality_level=self._quality.quality_level,
            readability_score=None,
            content_hash=self._quality.content_hash,
        )
        self._timestamps = self._timestamps.touch()

    # ===== Duplication Methods =====

    def mark_as_duplicate(self, duplicate_of: "ArticleId") -> None:
        """Marca como duplicado. Detección previa por ArticleDeduplicationService."""
        if not duplicate_of:
            raise ValueError("duplicate_of es requerido")

        from src.rss.article.domain.value_objects.metadata import ArticleId

        if not isinstance(duplicate_of, ArticleId):
            raise ValueError("duplicate_of debe ser ArticleId Value Object")

        self._duplication = ArticleDuplicate.duplicate_of(duplicate_of)
        self._timestamps = self._timestamps.touch()

    # ===== Validation Methods =====

    def validate_article(self, validation_score: float, validated_by: str) -> None:
        """Valida artículo. Emite ArticleValidated."""
        self._validation_info = ValidationInfo.create(
            score=validation_score, validated_by=validated_by
        )
        self._timestamps = self._timestamps.touch()

        from src.rss.article.domain.events import ArticleValidated

        self._add_domain_event(
            ArticleValidated(
                aggregate_id=str(self.id),
                article_id=str(self.id),
                source_id=str(self.metadata.source_id),
                validation_status="validated",
                validated_at=self._validation_info.validated_at,
                validation_score=validation_score,
            )
        )

    # ===== Error Handling Methods =====

    def mark_error(self, error_type: str, error_message: str, marked_by: str) -> None:
        """Marca con error. Emite ArticleErrorMarked."""
        error_marked_at = datetime.now(timezone.utc)

        self._error = ArticleError.create_error(
            error_type=error_type,
            error_message=error_message,
            marked_by=marked_by,
            marked_at=error_marked_at,
        )
        self._timestamps = self._timestamps.touch()

        from src.rss.article.domain.events import ArticleErrorMarked

        self._add_domain_event(
            ArticleErrorMarked(
                aggregate_id=str(self.id),
                article_id=str(self.id),
                source_id=str(self.metadata.source_id),
                error_type=error_type,
                error_message=error_message,
            )
        )

    # ===== Tag Methods =====

    def add_tag(self, tag: str) -> None:
        """Agrega tag. Emite ArticleTagAdded."""
        if not tag or not tag.strip():
            return

        self._metadata = self._metadata.add_tag(tag)
        self._timestamps = self._timestamps.touch()

        from src.rss.article.domain.events import ArticleTagAdded

        self._add_domain_event(
            ArticleTagAdded(
                aggregate_id=str(self.id),
                article_id=str(self.id),
                source_id=str(self.metadata.source_id),
                tag=tag.strip(),
                added_at=self.updated_at,
            )
        )

    # ===== Metadata Update Methods =====

    def update_title(self, title: "ArticleTitle") -> None:
        """Actualiza título."""
        self._metadata = self._metadata.with_title(title)
        self._timestamps = self._timestamps.touch()

    def update_summary(self, summary: "ArticleSummary") -> None:
        """Actualiza resumen."""
        self._metadata = self._metadata.with_summary(summary)
        self._timestamps = self._timestamps.touch()

    def update_thumbnail_url(self, thumbnail_url: "ArticleThumbnailUrl") -> None:
        """Actualiza URL de thumbnail."""
        self._metadata = self._metadata.with_thumbnail_url(thumbnail_url)
        self._timestamps = self._timestamps.touch()

    def update_author(self, author: str) -> None:
        """Actualiza autor."""
        self._metadata = self._metadata.with_author(author)
        self._timestamps = self._timestamps.touch()

    def clear_author(self) -> None:
        """Limpia autor."""
        from dataclasses import replace

        self._metadata = replace(self._metadata, author=None)
        self._timestamps = self._timestamps.touch()

    def update_language(self, language_code: str, confidence: float = 1.0) -> None:
        """Actualiza idioma. Emite ArticleLanguageDetected."""
        self._string_validator.validate(language_code, "language")
        self._score_validator.validate(confidence, "language_confidence")

        self._metadata = self._metadata.with_language(
            language_code=language_code.strip().lower(), confidence=confidence
        )
        self._timestamps = self._timestamps.touch()

        from src.rss.article.domain.events import ArticleLanguageDetected

        self._add_domain_event(
            ArticleLanguageDetected(
                aggregate_id=str(self.id),
                article_id=str(self.id),
                source_id=str(self.metadata.source_id),
                language_code=language_code.strip().lower(),
                confidence=confidence,
                detected_at=datetime.now(timezone.utc),
            )
        )

    def update_category(self, category: str, confidence: float = 1.0) -> None:
        """Actualiza categoría. Emite ArticleCategorized."""
        self._string_validator.validate(category, "category")
        self._score_validator.validate(confidence, "category_confidence")

        self._metadata = self._metadata.with_category(category.strip())
        self._timestamps = self._timestamps.touch()

        from src.rss.article.domain.events import ArticleCategorized

        self._add_domain_event(
            ArticleCategorized(
                aggregate_id=str(self.id),
                article_id=str(self.id),
                source_id=str(self.metadata.source_id),
                category=category.strip(),
                confidence=confidence,
                categorized_at=datetime.now(timezone.utc),
            )
        )

    def clear_language(self) -> None:
        """Limpia idioma."""
        from dataclasses import replace

        self._metadata = replace(self._metadata, language=None)
        self._timestamps = self._timestamps.touch()

    def clear_category(self) -> None:
        """Limpia categoría."""
        from dataclasses import replace

        self._metadata = replace(self._metadata, category=None)
        self._timestamps = self._timestamps.touch()

    # ===== Metrics Methods =====

    def update_metrics(self, word_count: int, reading_time: int) -> None:
        """Actualiza métricas. Valores calculados por ArticleMetricsCalculationService."""
        self._metrics = ArticleMetrics.create(
            word_count=word_count,
            reading_time_minutes=reading_time,
        )
        self._timestamps = self._timestamps.touch()

    # ===== Additional Metadata Methods =====

    def update_guid(self, guid: str) -> None:
        """Actualiza GUID."""
        from src.rss.article.domain.value_objects.metadata import ArticleGuid

        self._metadata = ArticleMetadata.create(
            id=self._metadata.id,
            source_id=self._metadata.source_id,
            title=self._metadata.title,
            url=self._metadata.url,
            author=self._metadata.author,
            category=self._metadata.category,
            summary=self._metadata.summary,
            thumbnail_url=self._metadata.thumbnail_url,
            language=self._metadata.language,
            tags=self._metadata.tags,
            keywords=self._metadata.keywords,
            guid=ArticleGuid(guid),
            pub_date=self._metadata.pub_date,
            description=self._metadata.description,
        )
        self._timestamps = self._timestamps.touch()

    def update_pub_date(self, pub_date: datetime) -> None:
        """Actualiza fecha de publicación."""
        from src.rss.article.domain.value_objects.metadata import ArticlePubDate

        self._metadata = ArticleMetadata.create(
            id=self._metadata.id,
            source_id=self._metadata.source_id,
            title=self._metadata.title,
            url=self._metadata.url,
            author=self._metadata.author,
            category=self._metadata.category,
            summary=self._metadata.summary,
            thumbnail_url=self._metadata.thumbnail_url,
            language=self._metadata.language,
            tags=self._metadata.tags,
            keywords=self._metadata.keywords,
            guid=self._metadata.guid,
            pub_date=ArticlePubDate(pub_date),
            description=self._metadata.description,
        )
        self._timestamps = self._timestamps.touch()

    def update_description(self, description: str) -> None:
        """Actualiza descripción."""
        from src.rss.article.domain.value_objects.metadata import ArticleDescription

        self._metadata = ArticleMetadata.create(
            id=self._metadata.id,
            source_id=self._metadata.source_id,
            title=self._metadata.title,
            url=self._metadata.url,
            author=self._metadata.author,
            category=self._metadata.category,
            summary=self._metadata.summary,
            thumbnail_url=self._metadata.thumbnail_url,
            language=self._metadata.language,
            tags=self._metadata.tags,
            keywords=self._metadata.keywords,
            guid=self._metadata.guid,
            pub_date=self._metadata.pub_date,
            description=ArticleDescription(description),
        )
        self._timestamps = self._timestamps.touch()

    # ===== Markdown Conversion Methods =====

    def can_convert_to_markdown(self) -> bool:
        """Verifica si el artículo puede ser convertido a markdown."""
        return bool(self._content.scraped or self._content.markdown)

    def get_html_for_conversion(self) -> str:
        """
        Obtiene el HTML apropiado para conversión a markdown.

        Prioriza content.scraped sobre content.markdown para preservar
        URLs de imágenes y estructura original.
        """
        if not self.can_convert_to_markdown():
            from src.rss.article.domain.exceptions import InvalidOperationException

            raise InvalidOperationException(
                "No HTML content available for markdown conversion"
            )

        return self._content.scraped or self._content.markdown

    def convert_to_markdown(
        self, markdown_content: str, markdown_without_url: Optional[str] = None
    ) -> None:
        """
        Convierte contenido a markdown y emite evento de dominio.

        Args:
            markdown_content: Contenido en formato markdown con links
            markdown_without_url: Contenido en formato markdown sin links (opcional)
        """
        if not markdown_content or not markdown_content.strip():
            raise ValueError("markdown_content no puede estar vacío")

        self.update_markdown(markdown_content)

        # Si se proporciona markdown sin URLs, también actualizarlo
        if markdown_without_url:
            self.update_markdown_without_url(markdown_without_url)

        from src.rss.article.domain.events import ArticleMarkdownConverted

        self._add_domain_event(
            ArticleMarkdownConverted(
                article_id=str(self.id),
                markdown_length=len(markdown_content),
            )
        )

    # ===== Event Management =====
    # (get_uncommitted_events, mark_events_as_committed, _add_domain_event)
    # ya están implementados en la clase base IAggregateRoot

    # ===== Magic Methods =====

    def __str__(self) -> str:
        title_str = str(self._metadata.title) if self._metadata.title else "Untitled"
        return f"RssArticle({title_str[:50]}...)"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, RssArticle):
            return False
        return str(self._metadata.id) == str(other._metadata.id)

    def __hash__(self) -> int:
        return hash(str(self._metadata.id))


# Alias para compatibilidad
Article = RssArticle
