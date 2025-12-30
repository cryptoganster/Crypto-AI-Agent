"""
Article Metadata Value Objects.

Este módulo contiene los Value Objects granulares para metadata de artículos
y el ArticleMetadata compuesto que los agrupa.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from src.rss.article.domain.value_objects.analysis import KeywordCollection

from .author import RssArticleAuthor
from .category import ArticleCategory
from .content import RssArticleContent
from .description import RssArticleDescription
from .guid import RssArticleGuid
from .language import ArticleLanguage
from .pub_date import RssArticlePubDate
from .rss_article_id import RssArticleId
from .rss_article_url import RssArticleUrl
from .summary import RssArticleSummary
from .thumbnail_url import ArticleThumbnailUrl
from .timestamps import RssArticleTimestamps
from .title import ArticleTitle

# Aliases para compatibilidad
ArticleId = RssArticleId
ArticleUrl = RssArticleUrl
ArticleAuthor = RssArticleAuthor
ArticleContent = RssArticleContent
ArticleDescription = RssArticleDescription
ArticleGuid = RssArticleGuid
ArticlePubDate = RssArticlePubDate
ArticleSummary = RssArticleSummary
ArticleTimestamps = RssArticleTimestamps
from src.rss.feed.domain.value_objects import SourceId
from src.shared.domain.value_objects import TagCollection

__all__ = [
    "RssArticleId",
    "RssArticleUrl",
    "RssArticleAuthor",
    "RssArticleContent",
    "RssArticleDescription",
    "RssArticleGuid",
    "RssArticlePubDate",
    "RssArticleSummary",
    "RssArticleTimestamps",
    "ArticleId",  # Alias para compatibilidad
    "ArticleUrl",  # Alias para compatibilidad
    "ArticleAuthor",  # Alias para compatibilidad
    "ArticleContent",  # Alias para compatibilidad
    "ArticleDescription",  # Alias para compatibilidad
    "ArticleGuid",  # Alias para compatibilidad
    "ArticlePubDate",  # Alias para compatibilidad
    "ArticleSummary",  # Alias para compatibilidad
    "ArticleTimestamps",  # Alias para compatibilidad
    "ArticleTitle",
    "ArticleCategory",
    "ArticleThumbnailUrl",
    "ArticleLanguage",
    "ArticleMetadata",
]


@dataclass(frozen=True)
class ArticleMetadata:
    """
    Value Object compuesto que agrupa metadata del artículo.

    Compone los Value Objects granulares de metadata en una estructura cohesiva.
    Cada campo es un VO con su propia validación y lógica de negocio.

    Attributes:
        id: Identificador único del artículo
        source_id: Identificador de la fuente
        title: Título del artículo
        url: URL del artículo
        author: Autor del artículo (opcional)
        category: Categoría del artículo (opcional)
        summary: Resumen del artículo (opcional)
        thumbnail_url: URL de imagen thumbnail (opcional)
        language: Idioma del artículo (opcional)
        tags: Etiquetas del artículo (opcional)
        keywords: Palabras clave del artículo (opcional)
        guid: GUID del feed (opcional)
        pub_date: Fecha de publicación del feed (opcional)
        description: Descripción del feed (opcional)
    """

    id: RssArticleId
    source_id: SourceId
    title: ArticleTitle
    url: RssArticleUrl
    author: Optional[RssArticleAuthor] = None
    category: Optional[ArticleCategory] = None
    summary: Optional[RssArticleSummary] = None
    thumbnail_url: Optional[ArticleThumbnailUrl] = None
    language: Optional[ArticleLanguage] = None
    tags: Optional[TagCollection] = None
    keywords: Optional[KeywordCollection] = None
    # Campos RSS
    guid: Optional[RssArticleGuid] = None
    pub_date: Optional[RssArticlePubDate] = None
    description: Optional[RssArticleDescription] = None

    @staticmethod
    def create(
        id: RssArticleId,
        source_id: SourceId,
        title: ArticleTitle,
        url: RssArticleUrl,
        author: Optional[ArticleAuthor] = None,
        category: Optional[ArticleCategory] = None,
        summary: Optional[ArticleSummary] = None,
        thumbnail_url: Optional[ArticleThumbnailUrl] = None,
        language: Optional[ArticleLanguage] = None,
        tags: Optional[TagCollection] = None,
        keywords: Optional[KeywordCollection] = None,
        guid: Optional[ArticleGuid] = None,
        pub_date: Optional[ArticlePubDate] = None,
        description: Optional[ArticleDescription] = None,
    ) -> "ArticleMetadata":
        """
        Factory method para crear ArticleMetadata.

        Args:
            id: RssArticleId VO
            source_id: SourceId VO
            title: ArticleTitle VO
            url: RssArticleUrl VO
            author: ArticleAuthor VO opcional
            category: ArticleCategory VO opcional
            summary: ArticleSummary VO opcional
            thumbnail_url: ArticleThumbnailUrl VO opcional
            language: ArticleLanguage VO opcional
            tags: TagCollection VO opcional
            keywords: KeywordCollection VO opcional
            guid: ArticleGuid VO opcional (feed)
            pub_date: ArticlePubDate VO opcional (feed)
            description: ArticleDescription VO opcional (feed)

        Returns:
            Nueva instancia de ArticleMetadata
        """
        return ArticleMetadata(
            id=id,
            source_id=source_id,
            title=title,
            url=url,
            author=author,
            category=category,
            summary=summary,
            thumbnail_url=thumbnail_url,
            language=language,
            tags=tags,
            keywords=keywords,
            guid=guid,
            pub_date=pub_date,
            description=description,
        )

    def with_author(self, author: Optional[ArticleAuthor]) -> "ArticleMetadata":
        """Retorna nueva instancia con author actualizado."""
        return ArticleMetadata(
            id=self.id,
            source_id=self.source_id,
            title=self.title,
            url=self.url,
            author=author,
            category=self.category,
            summary=self.summary,
            thumbnail_url=self.thumbnail_url,
            language=self.language,
            tags=self.tags,
            keywords=self.keywords,
            guid=self.guid,
            pub_date=self.pub_date,
            description=self.description,
        )

    def with_category(self, category: Optional[ArticleCategory]) -> "ArticleMetadata":
        """Retorna nueva instancia con category actualizado."""
        return ArticleMetadata(
            id=self.id,
            source_id=self.source_id,
            title=self.title,
            url=self.url,
            author=self.author,
            category=category,
            summary=self.summary,
            thumbnail_url=self.thumbnail_url,
            language=self.language,
            tags=self.tags,
            keywords=self.keywords,
            guid=self.guid,
            pub_date=self.pub_date,
            description=self.description,
        )

    def with_summary(self, summary: Optional[ArticleSummary]) -> "ArticleMetadata":
        """Retorna nueva instancia con summary actualizado."""
        return ArticleMetadata(
            id=self.id,
            source_id=self.source_id,
            title=self.title,
            url=self.url,
            author=self.author,
            category=self.category,
            summary=summary,
            thumbnail_url=self.thumbnail_url,
            language=self.language,
            tags=self.tags,
            keywords=self.keywords,
            guid=self.guid,
            pub_date=self.pub_date,
            description=self.description,
        )

    def with_thumbnail_url(
        self, thumbnail_url: Optional[ArticleThumbnailUrl]
    ) -> "ArticleMetadata":
        """Retorna nueva instancia con thumbnail_url actualizado."""
        return ArticleMetadata(
            id=self.id,
            source_id=self.source_id,
            title=self.title,
            url=self.url,
            author=self.author,
            category=self.category,
            summary=self.summary,
            thumbnail_url=thumbnail_url,
            language=self.language,
            tags=self.tags,
            keywords=self.keywords,
            guid=self.guid,
            pub_date=self.pub_date,
            description=self.description,
        )

    def with_language(
        self,
        language: Optional[ArticleLanguage] = None,
        language_code: Optional[str] = None,
        confidence: float = 1.0,
    ) -> "ArticleMetadata":
        """
        Retorna nueva instancia con language actualizado.

        Args:
            language: ArticleLanguage VO (si se provee, ignora language_code y confidence)
            language_code: Código de idioma como string (alternativa a language)
            confidence: Confianza de detección (solo si se usa language_code)

        Returns:
            Nueva instancia de ArticleMetadata con language actualizado
        """
        # Si se provee el VO directamente, usarlo
        if language is not None:
            language_vo = language
        # Si se provee código, crear el VO
        elif language_code is not None:
            language_vo = ArticleLanguage(code=language_code, confidence=confidence)
        else:
            language_vo = None

        return ArticleMetadata(
            id=self.id,
            source_id=self.source_id,
            title=self.title,
            url=self.url,
            author=self.author,
            category=self.category,
            summary=self.summary,
            thumbnail_url=self.thumbnail_url,
            language=language_vo,
            tags=self.tags,
            keywords=self.keywords,
            guid=self.guid,
            pub_date=self.pub_date,
            description=self.description,
        )

    def with_tags(self, tags: Optional[TagCollection]) -> "ArticleMetadata":
        """Retorna nueva instancia con tags actualizado."""
        return ArticleMetadata(
            id=self.id,
            source_id=self.source_id,
            title=self.title,
            url=self.url,
            author=self.author,
            category=self.category,
            summary=self.summary,
            thumbnail_url=self.thumbnail_url,
            language=self.language,
            tags=tags,
            keywords=self.keywords,
            guid=self.guid,
            pub_date=self.pub_date,
            description=self.description,
        )

    def add_tag(self, tag: str) -> "ArticleMetadata":
        """Retorna nueva instancia con tag agregado a la colección."""
        if self.tags is None:
            new_tags = TagCollection.create([tag])
        else:
            new_tags = self.tags.add(tag)

        return self.with_tags(new_tags)

    def with_keywords(self, keywords: Optional[KeywordCollection]) -> ArticleMetadata:
        """Retorna nueva instancia con keywords actualizado."""
        return ArticleMetadata(
            id=self.id,
            source_id=self.source_id,
            title=self.title,
            url=self.url,
            author=self.author,
            category=self.category,
            summary=self.summary,
            thumbnail_url=self.thumbnail_url,
            language=self.language,
            tags=self.tags,
            keywords=keywords,
            guid=self.guid,
            pub_date=self.pub_date,
            description=self.description,
        )

    def with_guid(self, guid: Optional[ArticleGuid]) -> "ArticleMetadata":
        """Retorna nueva instancia con guid actualizado."""
        return ArticleMetadata(
            id=self.id,
            source_id=self.source_id,
            title=self.title,
            url=self.url,
            author=self.author,
            category=self.category,
            summary=self.summary,
            thumbnail_url=self.thumbnail_url,
            language=self.language,
            tags=self.tags,
            keywords=self.keywords,
            guid=guid,
            pub_date=self.pub_date,
            description=self.description,
        )

    def with_pub_date(self, pub_date: Optional[ArticlePubDate]) -> "ArticleMetadata":
        """Retorna nueva instancia con pub_date actualizado."""
        return ArticleMetadata(
            id=self.id,
            source_id=self.source_id,
            title=self.title,
            url=self.url,
            author=self.author,
            category=self.category,
            summary=self.summary,
            thumbnail_url=self.thumbnail_url,
            language=self.language,
            tags=self.tags,
            keywords=self.keywords,
            guid=self.guid,
            pub_date=pub_date,
            description=self.description,
        )

    def with_description(
        self, description: Optional[ArticleDescription]
    ) -> "ArticleMetadata":
        """Retorna nueva instancia con description actualizado."""
        return ArticleMetadata(
            id=self.id,
            source_id=self.source_id,
            title=self.title,
            url=self.url,
            author=self.author,
            category=self.category,
            summary=self.summary,
            thumbnail_url=self.thumbnail_url,
            language=self.language,
            tags=self.tags,
            keywords=self.keywords,
            guid=self.guid,
            pub_date=self.pub_date,
            description=description,
        )

    @property
    def has_author(self) -> bool:
        """Verifica si tiene autor."""
        return self.author is not None

    @property
    def has_category(self) -> bool:
        """Verifica si tiene categoría."""
        return self.category is not None

    @property
    def has_summary(self) -> bool:
        """Verifica si tiene resumen."""
        return self.summary is not None and not self.summary.is_empty()

    @property
    def has_thumbnail(self) -> bool:
        """Verifica si tiene thumbnail."""
        return self.thumbnail_url is not None and self.thumbnail_url.is_present

    @property
    def has_language(self) -> bool:
        """Verifica si tiene idioma detectado."""
        return self.language is not None

    @property
    def has_guid(self) -> bool:
        """Verifica si tiene GUID."""
        return self.guid is not None

    @property
    def has_pub_date(self) -> bool:
        """Verifica si tiene fecha de publicación."""
        return self.pub_date is not None

    @property
    def has_description(self) -> bool:
        """Verifica si tiene descripción."""
        return self.description is not None

    @property
    def has_feed_metadata(self) -> bool:
        """Verifica si tiene al menos un campo de feed (guid, pub_date, description)."""
        return self.has_guid or self.has_pub_date or self.has_description

    @property
    def is_complete(self) -> bool:
        """Verifica si tiene toda la metadata opcional."""
        return all(
            [
                self.has_author,
                self.has_category,
                self.has_summary,
                self.has_thumbnail,
                self.has_language,
            ]
        )
