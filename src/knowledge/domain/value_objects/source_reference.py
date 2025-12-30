"""SourceReference value object for generic content source."""

from dataclasses import dataclass


@dataclass(frozen=True)
class SourceReference:
    """
    Value Object que representa la fuente de un chunk de conocimiento.

    Este VO es genérico y puede representar cualquier tipo de fuente.

    **Estado Actual (v1.0)**:
    - Solo "rss_article" está implementado
    - Otros tipos (tweet, pdf, etc.) son placeholders para futuro

    **Tipos de Fuente**:
    - RSS Article: source_type="rss_article", source_id="rss-article-123" ✅ IMPLEMENTADO
    - Tweet: source_type="tweet", source_id="tweet-456" ⏳ FUTURO
    - PDF: source_type="pdf_document", source_id="pdf-789" ⏳ FUTURO
    - Book: source_type="book", source_id="book-012" ⏳ FUTURO

    Attributes:
        source_type: Tipo de fuente ("rss_article" actualmente, otros en futuro)
        source_id: ID de la fuente en su bounded context
        source_url: URL de la fuente (si aplica)

    Examples:
        >>> # RSS Article (IMPLEMENTADO)
        >>> ref = SourceReference(
        ...     source_type="rss_article",
        ...     source_id="rss-article-123",
        ...     source_url="https://example.com/article"
        ... )
        >>> ref.is_rss_article()
        True

        >>> # Tweet (FUTURO - no implementado aún)
        >>> ref = SourceReference(
        ...     source_type="tweet",
        ...     source_id="tweet-456",
        ...     source_url="https://twitter.com/user/status/456"
        ... )
        >>> ref.is_tweet()
        True

    Notes:
        - Actualmente solo "rss_article" tiene bounded context implementado
        - Otros tipos están definidos para preparar extensibilidad futura
        - Al agregar nuevos tipos, crear su bounded context correspondiente

    Raises:
        ValueError: Si source_type, source_id o source_url son inválidos
    """

    source_type: str
    source_id: str
    source_url: str

    def __post_init__(self):
        """
        Valida invariantes del VO.

        Raises:
            ValueError: Si algún campo es inválido
        """
        # Validar source_type
        if not self.source_type or not self.source_type.strip():
            raise ValueError("source_type no puede estar vacío")

        # Validar source_id
        if not self.source_id or not self.source_id.strip():
            raise ValueError("source_id no puede estar vacío")

        # Validar source_url
        if not self.source_url or not self.source_url.startswith(
            ("http://", "https://", "file://")
        ):
            raise ValueError(
                "source_url debe ser una URL válida (http://, https://, o file://)"
            )

        # Validar source_types conocidos
        # NOTA: Solo "rss_article" está implementado actualmente
        valid_types = {
            "rss_article",  # ✅ IMPLEMENTADO
            "tweet",  # ⏳ FUTURO
            "pdf_document",  # ⏳ FUTURO
            "book",  # ⏳ FUTURO
            "instagram_post",  # ⏳ FUTURO
            "linkedin_post",  # ⏳ FUTURO
        }

        if self.source_type not in valid_types:
            raise ValueError(
                f"source_type '{self.source_type}' no es válido. "
                f"Tipos válidos: {', '.join(sorted(valid_types))}"
            )

    # Helper methods para verificar tipo de fuente

    def is_rss_article(self) -> bool:
        """
        Verifica si la fuente es un artículo RSS.

        Returns:
            True si source_type es "rss_article"

        Note:
            Este es el único tipo implementado actualmente.
        """
        return self.source_type == "rss_article"

    def is_tweet(self) -> bool:
        """
        Verifica si la fuente es un tweet.

        Returns:
            True si source_type es "tweet"

        Note:
            FUTURO - No implementado aún. Requiere bounded context twitter/.
        """
        return self.source_type == "tweet"

    def is_pdf(self) -> bool:
        """
        Verifica si la fuente es un documento PDF.

        Returns:
            True si source_type es "pdf_document"

        Note:
            FUTURO - No implementado aún. Requiere bounded context pdf/.
        """
        return self.source_type == "pdf_document"

    def is_book(self) -> bool:
        """
        Verifica si la fuente es un libro.

        Returns:
            True si source_type es "book"

        Note:
            FUTURO - No implementado aún. Requiere bounded context book/.
        """
        return self.source_type == "book"

    def is_instagram_post(self) -> bool:
        """
        Verifica si la fuente es un post de Instagram.

        Returns:
            True si source_type es "instagram_post"

        Note:
            FUTURO - No implementado aún. Requiere bounded context instagram/.
        """
        return self.source_type == "instagram_post"

    def is_linkedin_post(self) -> bool:
        """
        Verifica si la fuente es un post de LinkedIn.

        Returns:
            True si source_type es "linkedin_post"

        Note:
            FUTURO - No implementado aún. Requiere bounded context linkedin/.
        """
        return self.source_type == "linkedin_post"

    def get_bounded_context(self) -> str:
        """
        Obtiene el nombre del bounded context al que pertenece esta fuente.

        Returns:
            Nombre del bounded context (ej: "rss", "twitter", "pdf")

        Examples:
            >>> ref = SourceReference("rss_article", "123", "https://example.com")
            >>> ref.get_bounded_context()
            'rss'

        Note:
            Solo "rss" está implementado actualmente.
        """
        context_map = {
            "rss_article": "rss",
            "tweet": "twitter",
            "pdf_document": "pdf",
            "book": "book",
            "instagram_post": "instagram",
            "linkedin_post": "linkedin",
        }
        return context_map.get(self.source_type, "unknown")
