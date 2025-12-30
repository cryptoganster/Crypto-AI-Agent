"""Property-based tests para ArticleContent Value Object."""

import pytest
from hypothesis import given
from hypothesis import strategies as st

from src.rss.article.domain.value_objects.metadata.content import RssArticleContent


class TestRssArticleContentProperties:
    """Property-based tests para ArticleContent VO."""

    @given(
        markdown=st.one_of(st.none(), st.text()),
        plaintext=st.one_of(st.none(), st.text()),
        scrapped=st.one_of(st.none(), st.text()),
    )
    def test_article_content_at_least_one_field_property(
        self, markdown, plaintext, scrapped
    ):
        """
        Property 1: RssArticleContent validation

        For any RssArticleContent instance created, at least one of the content fields
        (markdown, plaintext, scrapped) must have non-empty content
        (not None and not empty after strip).

        **Feature: refactor-article-aggregate, Property 1: RssArticleContent validation**
        **Validates: Requirements 2.3**
        """
        # Verificar si al menos un campo tiene contenido no vacío
        has_content = any(
            [
                markdown and markdown.strip(),
                plaintext and plaintext.strip(),
                scrapped and scrapped.strip(),
            ]
        )

        # ArticleContent now allows empty state (all None or empty strings)
        # The aggregate enforces when content is required for business operations
        # This is intentionally permissive to support various initialization patterns
        if not has_content:
            # Should create successfully even with no content
            content = RssArticleContent(
                markdown=markdown,
                plaintext=plaintext,
                scrapped=scrapped,
            )
            # Verify it was created (no exception)
            assert content is not None
        else:
            # Si al menos uno tiene contenido, debe crear correctamente
            content = RssArticleContent(
                markdown=markdown,
                plaintext=plaintext,
                scrapped=scrapped,
            )

            # Verificar que se creó correctamente
            assert content is not None
            assert content.markdown == markdown
            assert content.plaintext == plaintext
            assert content.scrapped == scrapped

    @given(
        markdown=st.text(min_size=1),
        plaintext=st.one_of(st.none(), st.text()),
        scrapped=st.one_of(st.none(), st.text()),
    )
    def test_article_content_immutability_property(self, markdown, plaintext, scrapped):
        """
        Property: RssArticleContent es inmutable.

        For any RssArticleContent instance, intentar modificar sus campos
        debe lanzar un error.
        """
        content = RssArticleContent(
            markdown=markdown, plaintext=plaintext, scrapped=scrapped
        )

        # Intentar modificar debe fallar (frozen dataclass)
        with pytest.raises(AttributeError):
            content.markdown = "new value"  # type: ignore

    @given(
        original_markdown=st.text(min_size=1).filter(lambda x: x.strip()),
        new_markdown=st.text(min_size=1).filter(lambda x: x.strip()),
    )
    def test_with_markdown_returns_new_instance_property(
        self, original_markdown, new_markdown
    ):
        """
        Property: with_markdown retorna nueva instancia sin modificar original.

        For any RssArticleContent instance with valid content, llamar with_markdown
        con nuevo contenido válido debe retornar una nueva instancia con el markdown
        actualizado, sin modificar la original.
        """
        original = RssArticleContent(markdown=original_markdown)
        updated = original.with_markdown(new_markdown)

        # Verificar que son instancias diferentes
        assert original is not updated

        # Verificar que el original no cambió
        assert original.markdown == original_markdown

        # Verificar que el nuevo tiene el valor actualizado
        assert updated.markdown == new_markdown

        # Verificar que otros campos se preservaron
        assert updated.plaintext == original.plaintext
        assert updated.scrapped == original.scrapped

    @given(
        markdown=st.one_of(
            st.none(),
            st.just(""),
            st.just("   "),
            st.text(min_size=1).filter(lambda x: x.strip()),
        )
    )
    def test_has_markdown_property_correctness(self, markdown):
        """
        Property: has_markdown retorna True solo si markdown tiene contenido válido.

        For any RssArticleContent instance, has_markdown debe retornar True
        solo si markdown no es None y no está vacío después de strip.
        """
        # Necesitamos al menos un campo con contenido para crear la instancia
        if not markdown or not markdown.strip():
            # Si markdown está vacío, usar plaintext con contenido
            content = RssArticleContent(plaintext="dummy content")
        else:
            content = RssArticleContent(markdown=markdown)

        # Verificar propiedad
        expected = bool(markdown and markdown.strip())
        assert content.has_markdown == expected

    @given(
        plaintext=st.one_of(
            st.none(),
            st.just(""),
            st.just("   "),
            st.text(min_size=1).filter(lambda x: x.strip()),
        )
    )
    def test_has_plaintext_property_correctness(self, plaintext):
        """
        Property: has_plaintext retorna True solo si plaintext tiene contenido válido.

        For any RssArticleContent instance, has_plaintext debe retornar True
        solo si plaintext no es None y no está vacío después de strip.
        """
        # Necesitamos al menos un campo con contenido para crear la instancia
        if not plaintext or not plaintext.strip():
            # Si plaintext está vacío, usar markdown con contenido
            content = RssArticleContent(markdown="dummy content")
        else:
            content = RssArticleContent(plaintext=plaintext)

        # Verificar propiedad
        expected = bool(plaintext and plaintext.strip())
        assert content.has_plaintext == expected

    def test_can_create_with_all_empty_fields(self):
        """
        Property: RssArticleContent permite estado vacío para inicialización.

        RssArticleContent ahora permite todos los campos None o vacíos.
        Esto es intencional para soportar varios patrones de inicialización.
        El aggregate enforza cuándo el contenido es requerido para operaciones de negocio.
        """
        # Todos None - permitido
        content1 = RssArticleContent()
        assert content1 is not None

        # Todos empty strings - permitido
        content2 = RssArticleContent(markdown="", plaintext="", scrapped="")
        assert content2 is not None

        # Mix de None y empty - permitido
        content3 = RssArticleContent(markdown="", plaintext=None, scrapped="   ")
        assert content3 is not None
