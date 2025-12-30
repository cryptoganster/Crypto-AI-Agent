"""Factory moderno para RssArticle aggregate con validaciones avanzadas."""

from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from src.rss.article.domain.aggregates import RssArticle
from src.rss.article.domain.interfaces.factories.article_factory import (
    IRssArticleFactory,
)
from src.rss.article.domain.value_objects.metadata import (
    ArticleThumbnailUrl,
    ArticleTitle,
    RssArticleId,
    RssArticleUrl,
)
from src.rss.article.domain.value_objects.metadata.content import (
    RssArticleContent,
)
from src.rss.feed.domain.value_objects import SourceId
from src.shared.domain.value_objects import Level


class FeedItem:
    """DTO para items de feed RSS."""

    def __init__(
        self,
        title: str,
        link: str,
        description: Optional[str] = None,
        content: Optional[str] = None,
        pub_date: Optional[datetime] = None,
        author: Optional[str] = None,
        categories: Optional[List[str]] = None,
        guid: Optional[str] = None,
    ):
        self.title = title
        self.link = link
        self.description = description
        self.content = content
        self.pub_date = pub_date
        self.author = author
        self.categories = categories or []
        self.guid = guid


class ValidationResult:
    """Resultado de validación con errores y warnings."""

    def __init__(
        self,
        is_valid: bool,
        error_messages: Tuple[str, ...] = (),
        warnings: Tuple[str, ...] = (),
    ):
        self.is_valid = is_valid
        self.error_messages = error_messages
        self.warnings = warnings


class RssArticleFactory(IRssArticleFactory):
    """
    Factory moderno para RssArticle aggregate.

    Migra funcionalidad valiosa del RssArticleFactory anterior:
    - Validaciones avanzadas de dominio
    - Limpieza y normalización de datos
    - Creación desde feed items RSS
    - Detección de duplicados potenciales

    Se integra con el nuevo RssArticle aggregate preservando eventos de dominio.
    """

    def create_article(
        self,
        title: str,
        url: str,
        source_id: SourceId,
        content: Optional[str] = None,
        article_id: Optional[RssArticleId] = None,
        thumbnail_url: Optional[str] = None,
        guid: Optional[str] = None,
        published_at: Optional[datetime] = None,
        description: Optional[str] = None,
        **metadata,
    ) -> RssArticle:
        """
        Crea nuevo RssArticle con validaciones y limpieza de dominio.

        Args:
            title: Título del artículo (string, será validado con ArticleTitle VO)
            url: URL del artículo (string, será validado con RssArticleUrl VO)
            source_id: ID de la source RSS
            content: Contenido opcional (string, será validado con RssArticleContent VO)
            article_id: ID opcional (genera determinístico si None)
            thumbnail_url: URL de thumbnail opcional
            guid: GUID único del RSS feed
            published_at: Fecha de publicación original del RSS
            description: Descripción original del RSS feed
            **metadata: Metadatos adicionales (author, language, etc.)

        Returns:
            RssArticle aggregate con validaciones y limpieza aplicadas

        Raises:
            ValueError: Si datos son inválidos según reglas de dominio
                (validados por VOs)
        """
        # PASO 1: Limpiar datos ANTES de validar con VOs
        # Esto garantiza que los datos estén normalizados antes de validación
        clean_title = self._clean_title(title)
        normalized_url = self._clean_url(url)
        clean_content = self._clean_content(content) if content else None
        clean_summary = self._clean_summary(description) if description else None

        # PASO 2: Validar usando Value Objects con datos ya limpios
        try:
            # VOs validan automáticamente en construcción
            title_vo = ArticleTitle(clean_title)
            url_vo = RssArticleUrl(normalized_url)
            # Validar content pero no lo usamos directamente
            if clean_content:
                RssArticleContent(markdown=clean_content)
        except ValueError as e:
            raise ValueError(f"Validación de RssArticle fallida: {e}") from e

        # PASO 3: Usar valores validados de los VOs
        # Los VOs pueden aplicar normalización adicional
        final_title = title_vo.value
        final_url = url_vo.value

        # Crear thumbnail VO si se proporciona
        thumbnail_vo = (
            ArticleThumbnailUrl.create(thumbnail_url) if thumbnail_url else None
        )

        # Crear summary VO si se proporciona
        from src.rss.article.domain.value_objects.metadata import ArticleSummary

        summary_vo = ArticleSummary(clean_summary) if clean_summary else None

        # Generar article_id si no se proporciona
        final_article_id = article_id or RssArticleId.from_source_and_url(
            str(source_id), url_vo.value
        )

        # Crear ArticleMetadata compuesto (ahora incluye source_id)
        # Este ArticleMetadata incluye: id, source_id, title, url, author, category, summary, thumbnail_url, language
        from src.rss.article.domain.value_objects.metadata import (
            ArticleMetadata as ArticleMetadataVO,
        )

        metadata_vo = ArticleMetadataVO.create(
            id=final_article_id,
            source_id=source_id,
            title=title_vo,
            url=url_vo,
            summary=summary_vo,
            thumbnail_url=thumbnail_vo,
        )

        # Crear RssArticle usando constructor con Value Objects compuestos
        article = RssArticle(
            metadata=metadata_vo,  # Contiene id, source_id, title, url, summary, thumbnail, author, language, category
        )

        # NOTA: El snippet HTML del RSS NO se guarda en content_scrapped
        # content_scrapped debe llenarse SOLO con scraping real desde la URL
        # El snippet del RSS ya está en 'description' para referencia

        # Emitir evento de creación manualmente (RssArticle.create() lo hacía)
        from src.rss.article.domain.events.article_created import ArticleCreated

        article._add_domain_event(
            ArticleCreated(
                aggregate_id=str(metadata_vo.id),
                article_id=str(metadata_vo.id),
                source_id=str(source_id),
                title=final_title,
                url=final_url,
                created_at=article.created_at,
            )
        )

        # Aplicar metadatos RSS nativos si se proporcionan
        if guid:
            article.update_guid(guid)
        if published_at:
            article.update_pub_date(published_at)
        if description:
            article.update_description(description)

        # Aplicar metadatos adicionales si se proporcionan
        if metadata.get("author"):
            article.update_author(metadata["author"])
        if metadata.get("language"):
            article.update_language(metadata["language"])
        if metadata.get("category"):
            article.update_category(metadata["category"], confidence=1.0)
        if metadata.get("tags"):
            for tag in metadata["tags"]:
                article.add_tag(tag)

        return article

    def create_from_feed_item(
        self,
        feed_item: FeedItem,
        source_id: SourceId,
        quality_assessment: bool = True,
    ) -> RssArticle:
        """
        Crea RssArticle desde item de feed RSS con inteligencia de dominio.

        Args:
            feed_item: Item del feed RSS con metadatos
            source_id: ID de la source RSS origen
            quality_assessment: True para evaluar calidad automáticamente

        Returns:
            Nueva instancia de RssArticle con metadatos aplicados y eventos
        """
        # Usar descripción como fallback para contenido
        summary = feed_item.description
        content = feed_item.content or feed_item.description

        # Crear artículo base con limpieza Y metadatos RSS
        # Ahora description se pasa para crear ArticleMetadata con summary
        article = self.create_article(
            title=feed_item.title,
            url=feed_item.link,
            source_id=source_id,
            content=content,
            # Metadatos RSS nativos (Bug Fix: ahora se pasan correctamente)
            guid=feed_item.guid,
            published_at=feed_item.pub_date,
            description=feed_item.description,  # Se usa para crear summary en metadata_vo
            # Metadatos adicionales
            author=feed_item.author,
            category=feed_item.categories[0] if feed_item.categories else None,
            tags=feed_item.categories,
        )

        # Establecer resumen adicional si es diferente del contenido
        # (ya se estableció en metadata_vo durante create_article)
        if summary and summary != content and not article.metadata.summary:
            from src.rss.article.domain.value_objects.metadata import ArticleSummary

            article.update_summary(ArticleSummary(summary))

        # Evaluación automática de calidad si se solicita
        if quality_assessment and content:
            quality_level = self._assess_content_quality(content)
            if quality_level:
                article.update_quality_level(quality_level)

        return article

    def validate_article_creation_data(
        self, title: str, url: str, source_id: str, **kwargs
    ) -> ValidationResult:
        """
        Valida datos para creación de artículo con reglas de dominio avanzadas.

        Args:
            title: Título del artículo a validar
            url: URL del artículo a validar
            source_id: ID de la source RSS a validar
            **kwargs: Argumentos adicionales a validar

        Returns:
            Resultado de validación con errores y warnings detallados
        """
        errors = []
        warnings = []

        # Validar título con reglas específicas
        title_validation = self._validate_title(title)
        errors.extend(title_validation["errors"])
        warnings.extend(title_validation["warnings"])

        # Validar URL con reglas específicas
        url_validation = self._validate_url(url)
        errors.extend(url_validation["errors"])
        warnings.extend(url_validation["warnings"])

        # Validar source_id
        if not source_id or not source_id.strip():
            errors.append("source_id es requerido")

        # Validar contenido opcional
        content = kwargs.get("content")
        if content:
            content_validation = self._validate_content(content)
            warnings.extend(content_validation["warnings"])

        # Validar metadatos opcionales
        metadata_validation = self._validate_metadata(kwargs)
        warnings.extend(metadata_validation["warnings"])

        # Validar duplicados potenciales
        if self._is_potentially_duplicate_url(url):
            warnings.append(
                "URL contiene parámetros de tracking que podrían " "causar duplicados"
            )

        return ValidationResult(
            is_valid=len(errors) == 0,
            error_messages=tuple(errors),
            warnings=tuple(warnings),
        )

    def _validate_title(self, title: str) -> Dict[str, List[str]]:
        """Valida título con reglas específicas de dominio."""
        errors = []
        warnings = []

        if not title or not title.strip():
            errors.append("Título es requerido")
            return {"errors": errors, "warnings": warnings}

        title = title.strip()

        if len(title) < 5:
            warnings.append("Título muy corto, recomendado mínimo 5 caracteres")
        elif len(title) > 200:
            errors.append("Título debe tener máximo 200 caracteres")

        # Detectar títulos potencialmente problemáticos
        if title.upper() == title and len(title) > 20:
            warnings.append(
                "Título en mayúsculas podría tener problemas de legibilidad"
            )

        if title.count("!") > 3:
            warnings.append("Exceso de signos de exclamación podría indicar clickbait")

        return {"errors": errors, "warnings": warnings}

    def _validate_url(self, url: str) -> Dict[str, List[str]]:
        """Valida URL con reglas específicas de dominio."""
        errors = []
        warnings = []

        try:
            # Usar RssArticleUrl VO que ya tiene validaciones de dominio
            article_url = RssArticleUrl.try_create(url)
            if not article_url:
                errors.append(
                    "URL debe incluir protocolo válido (http/https) y dominio"
                )
                return {"errors": errors, "warnings": warnings}

            # Validaciones de calidad usando VO
            if not article_url.is_secure():
                warnings.append("Se recomienda HTTPS en lugar de HTTP")

            domain = article_url.get_domain()
            if "bit.ly" in domain or "tinyurl.com" in domain:
                warnings.append("URL acortada podría ser problemática para archivado")

        except Exception:
            errors.append("URL no puede ser parseada correctamente")

        return {"errors": errors, "warnings": warnings}

    def _validate_content(self, content: str) -> Dict[str, List[str]]:
        """Valida contenido del artículo."""
        warnings = []

        if len(content) > 50000:  # 50KB límite
            warnings.append("Contenido muy largo, podría afectar performance")
        elif len(content) < 100:
            warnings.append("Contenido muy corto, podría no ser sustancial")

        # Detectar contenido potencialmente problemático
        if content.count("http") > 10:
            warnings.append("Exceso de enlaces podría indicar contenido spam")

        return {"warnings": warnings}

    def _validate_metadata(self, metadata: Dict[str, Any]) -> Dict[str, List[str]]:
        """Valida metadatos adicionales."""
        warnings = []

        summary = metadata.get("summary")
        if summary and len(summary) > 1000:
            warnings.append("Resumen muy largo, recomendado máximo 1000 caracteres")

        author = metadata.get("author")
        if author and len(author) > 100:
            warnings.append("Nombre de autor muy largo")

        return {"warnings": warnings}

    def _clean_title(self, title: str) -> str:
        """Limpia y normaliza el título del artículo."""
        # Remover espacios extra y caracteres de control
        clean = " ".join(title.split())

        # Remover prefijos comunes de RSS feeds
        prefixes_to_remove = ["RSS:", "FEED:", "[RSS]", "[FEED]", "RSS -", "Feed:"]
        for prefix in prefixes_to_remove:
            if clean.upper().startswith(prefix.upper()):
                clean = clean[len(prefix) :].strip()

        # Remover sufijos comunes
        suffixes_to_remove = [" - RSS", " | RSS Feed", " (RSS)"]
        for suffix in suffixes_to_remove:
            if clean.upper().endswith(suffix.upper()):
                clean = clean[: -len(suffix)].strip()

        return clean

    def _clean_url(self, url: str) -> str:
        """Limpia y normaliza la URL del artículo."""
        clean_url = url.strip()

        # RssArticleUrl VO ya normaliza la URL (scheme lowercase,
        # netloc lowercase, sin fragment)
        # Delegamos toda la normalización al Value Object
        try:
            article_url = RssArticleUrl.try_create(clean_url)
            if article_url:
                return str(article_url)
        except Exception:
            pass

        # Fallback si el VO falla
        return clean_url

    def _clean_content(self, content: str) -> str:
        """Limpia y normaliza contenido del artículo."""
        if not content:
            return content

        # Remover espacios extra pero preservar párrafos
        lines = [line.strip() for line in content.split("\n")]
        clean_lines = [line for line in lines if line]

        return "\n\n".join(clean_lines)

    def _clean_summary(self, summary: str) -> str:
        """Limpia y normaliza el resumen del artículo."""
        if not summary:
            return summary

        # Remover espacios extra
        clean = " ".join(summary.split())

        # Remover prefijos comunes de RSS
        prefixes_to_remove = ["Summary:", "SUMMARY:", "[Summary]"]
        for prefix in prefixes_to_remove:
            if clean.startswith(prefix):
                clean = clean[len(prefix) :].strip()

        return clean

    def _is_potentially_duplicate_url(self, url: str) -> bool:
        """Detecta URLs que podrían ser duplicadas por parámetros de tracking."""
        tracking_params = ["utm_", "fbclid", "gclid", "_ga", "ref=", "source="]
        url_lower = url.lower()

        return any(param in url_lower for param in tracking_params)

    def _assess_content_quality(self, content: str) -> Optional[Level]:
        """
        Evalúa automáticamente la calidad del contenido.

        Returns:
            Level basado en heurísticas simples
        """
        if not content or len(content) < 50:
            return Level.low()

        # Heurísticas simples de calidad
        word_count = len(content.split())

        if word_count < 100:
            return Level.low()
        elif word_count < 500:
            return Level.medium()
        else:
            return Level.high()
