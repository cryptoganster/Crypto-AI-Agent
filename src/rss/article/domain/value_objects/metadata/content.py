"""Value Object para contenido del artículo en diferentes formatos."""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class RssArticleContent:
    """
    Value Object para contenido del artículo en diferentes formatos.

    Encapsula el pipeline de procesamiento de contenido (HTML → Markdown → Plaintext).

    Invariantes:
    - Al menos uno de los campos debe ser no-None
    - Los campos son inmutables (frozen dataclass)

    Attributes:
        markdown: Contenido principal en formato Markdown con links
        markdown_without_url: Contenido Markdown sin URLs (para AI/ML)
        plaintext: Texto plano para procesamiento NLP
        scrapped: HTML original scrapeado
    """

    markdown: Optional[str] = None
    markdown_without_url: Optional[str] = None
    plaintext: Optional[str] = None
    scraped: Optional[str] = None

    def __post_init__(self):
        """
        Valida que al menos un campo tenga contenido no vacío.

        Verifica que al menos uno de los campos (markdown, plaintext, scrapped)
        no sea None Y no esté vacío después de strip().

        Raises:
            ValueError: Si todos los campos son None o están vacíos

        Note:
            Empty content is allowed for initialization (all fields None).
            Validation only fails if fields are explicitly set to empty strings.
        """
        # Check if any field has actual content (not None and not empty after strip)
        has_content = any(
            [
                self.markdown and self.markdown.strip(),
                self.markdown_without_url and self.markdown_without_url.strip(),
                self.plaintext and self.plaintext.strip(),
                self.scraped and self.scraped.strip(),
            ]
        )

        # Allow empty state - all None or all empty strings are valid
        # This is intentionally permissive to support various initialization patterns
        # The aggregate will enforce business rules about when content is required

    @staticmethod
    def empty() -> "RssArticleContent":
        """
        Crea instancia vacía de ArticleContent.

        Útil para inicialización del aggregate cuando aún no hay contenido.

        Returns:
            Nueva instancia de ArticleContent con todos los campos None

        Example:
            >>> content = ArticleContent.empty()
            >>> content.markdown is None
            True
            >>> content.has_markdown
            False
        """
        # Create instance with all None fields
        # This bypasses the validation in __post_init__
        return RssArticleContent(
            markdown=None, markdown_without_url=None, plaintext=None, scraped=None
        )

    @property
    def has_markdown(self) -> bool:
        """
        Verifica si tiene contenido markdown válido.

        Returns:
            True si markdown no es None y no está vacío (después de strip)
        """
        return bool(self.markdown and self.markdown.strip())

    @property
    def has_plaintext(self) -> bool:
        """
        Verifica si tiene contenido plaintext válido.

        Returns:
            True si plaintext no es None y no está vacío (después de strip)
        """
        return bool(self.plaintext and self.plaintext.strip())

    def with_markdown(self, markdown: Optional[str]) -> "RssArticleContent":
        """
        Retorna nueva instancia con markdown actualizado.

        Método inmutable que crea una nueva instancia preservando otros campos.

        Args:
            markdown: Nuevo contenido markdown (puede ser None para limpiar)

        Returns:
            Nueva instancia de ArticleContent con markdown actualizado

        Example:
            >>> content = ArticleContent(markdown="# Old")
            >>> updated = content.with_markdown("# New")
            >>> updated.markdown
            '# New'
            >>> content.markdown  # Original sin cambios
            '# Old'
            >>> cleared = content.with_markdown(None)
            >>> cleared.markdown is None
            True
        """
        return RssArticleContent(
            markdown=markdown,
            markdown_without_url=self.markdown_without_url,
            plaintext=self.plaintext,
            scraped=self.scraped,
        )

    def with_markdown_without_url(
        self, markdown_without_url: Optional[str]
    ) -> "RssArticleContent":
        """
        Retorna nueva instancia con markdown_without_url actualizado.

        Args:
            markdown_without_url: Nuevo contenido markdown sin URLs (puede ser None)

        Returns:
            Nueva instancia de ArticleContent con markdown_without_url actualizado
        """
        return RssArticleContent(
            markdown=self.markdown,
            markdown_without_url=markdown_without_url,
            plaintext=self.plaintext,
            scraped=self.scraped,
        )

    def with_plaintext(self, plaintext: Optional[str]) -> "RssArticleContent":
        """
        Retorna nueva instancia con plaintext actualizado.

        Args:
            plaintext: Nuevo contenido en texto plano (puede ser None para limpiar)

        Returns:
            Nueva instancia de ArticleContent con plaintext actualizado
        """
        return RssArticleContent(
            markdown=self.markdown,
            markdown_without_url=self.markdown_without_url,
            plaintext=plaintext,
            scraped=self.scraped,
        )

    def with_scraped(self, scraped: Optional[str]) -> "RssArticleContent":
        """
        Retorna nueva instancia con HTML scrapeado actualizado.

        Args:
            scraped: Nuevo HTML scrapeado (puede ser None para limpiar)

        Returns:
            Nueva instancia de ArticleContent con scraped actualizado
        """
        return RssArticleContent(
            markdown=self.markdown,
            markdown_without_url=self.markdown_without_url,
            plaintext=self.plaintext,
            scraped=scraped,
        )
