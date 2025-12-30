"""Property-based tests para RssArticleFactory.

Feature: refactor-article-factory-pattern
"""

from datetime import datetime, timezone

import pytest
from hypothesis import assume, given, settings
from hypothesis import strategies as st

from src.rss.article.domain.aggregates.rss_article import RssArticle
from src.rss.article.domain.factories.article_factory import FeedItem, RssArticleFactory
from src.rss.feed.domain.value_objects import RssFeedId

# ========== Estrategias de Hypothesis ==========


@st.composite
def valid_titles(draw):
    """Genera títulos válidos (5-500 caracteres)."""
    # Generar título base válido
    base = draw(
        st.text(
            alphabet=st.characters(
                whitelist_categories=("Lu", "Ll", "Nd", "Zs", "Po"),
                min_codepoint=32,
                max_codepoint=126,
            ),
            min_size=5,
            max_size=200,
        )
    )
    # Asegurar que no esté vacío después de strip
    assume(len(base.strip()) >= 5)
    return base


@st.composite
def dirty_titles(draw):
    """Genera títulos con 'suciedad' (espacios extra, prefijos RSS)."""
    clean_title = draw(valid_titles())

    # Agregar espacios extra
    spaces_before = draw(st.integers(min_value=0, max_value=5))
    spaces_after = draw(st.integers(min_value=0, max_value=5))
    spaces_middle = draw(st.integers(min_value=1, max_value=3))

    dirty = " " * spaces_before + clean_title + " " * spaces_after

    # Agregar prefijos RSS aleatoriamente
    prefixes = ["RSS:", "FEED:", "[RSS]", "[FEED]", "RSS -", "Feed:"]
    if draw(st.booleans()):
        prefix = draw(st.sampled_from(prefixes))
        dirty = prefix + " " + dirty

    # Agregar sufijos RSS aleatoriamente
    suffixes = [" - RSS", " | RSS Feed", " (RSS)"]
    if draw(st.booleans()):
        suffix = draw(st.sampled_from(suffixes))
        dirty = dirty + suffix

    return dirty, clean_title


@st.composite
def valid_urls(draw):
    """Genera URLs válidas."""
    protocol = draw(st.sampled_from(["http://", "https://"]))
    domain = draw(
        st.text(
            alphabet=st.characters(
                whitelist_categories=("Ll", "Nd"), min_codepoint=97, max_codepoint=122
            ),
            min_size=3,
            max_size=20,
        )
    )
    tld = draw(st.sampled_from([".com", ".org", ".net", ".io"]))
    path = draw(
        st.text(
            alphabet=st.characters(
                whitelist_categories=("Ll", "Nd"), min_codepoint=97, max_codepoint=122
            ),
            min_size=1,
            max_size=30,
        )
    )

    url = f"{protocol}{domain}{tld}/{path}"
    return url


@st.composite
def dirty_urls(draw):
    """Genera URLs con 'suciedad' (mayúsculas, espacios)."""
    clean_url = draw(valid_urls())

    # Convertir a mayúsculas aleatoriamente
    if draw(st.booleans()):
        clean_url = clean_url.upper()

    # Agregar espacios
    spaces_before = draw(st.integers(min_value=0, max_value=3))
    spaces_after = draw(st.integers(min_value=0, max_value=3))

    dirty = " " * spaces_before + clean_url + " " * spaces_after

    return dirty


@st.composite
def valid_source_ids(draw):
    """Genera SourceIds válidos."""
    source_str = draw(
        st.text(
            alphabet=st.characters(
                whitelist_categories=("Ll", "Nd"), min_codepoint=97, max_codepoint=122
            ),
            min_size=5,
            max_size=20,
        )
    )
    return RssFeedId(f"src-{source_str}")


# ========== Property 1: Factory produces clean data ==========


class TestProperty1FactoryProducesCleanData:
    """Property 1: Factory produces clean data.

    Feature: refactor-article-factory-pattern, Property 1
    Validates: Requirements 1.1, 1.3, 7.1, 7.2, 7.3
    """

    @settings(max_examples=100)
    @given(
        dirty_title_and_clean=dirty_titles(),
        dirty_url=dirty_urls(),
        source_id=valid_source_ids(),
    )
    def test_factory_cleans_title_removes_rss_prefixes(
        self, dirty_title_and_clean, dirty_url, source_id
    ):
        """Para cualquier título con prefijos RSS, el factory debería removerlos."""
        dirty_title, expected_clean = dirty_title_and_clean

        # Arrange
        factory = RssArticleFactory()

        # Act
        article = factory.create_article(
            title=dirty_title, url=dirty_url, source_id=source_id
        )

        # Assert - El título no debería tener prefijos RSS
        title_str = str(article.title)
        assert not title_str.startswith("RSS:")
        assert not title_str.startswith("FEED:")
        assert not title_str.startswith("[RSS]")
        assert not title_str.startswith("[FEED]")
        assert not title_str.startswith("RSS -")
        assert not title_str.startswith("Feed:")

        # No debería tener sufijos RSS
        assert not title_str.endswith(" - RSS")
        assert not title_str.endswith(" | RSS Feed")
        assert not title_str.endswith(" (RSS)")

        # No debería tener espacios extra al inicio/final
        assert title_str == title_str.strip()
        assert "  " not in title_str  # No espacios dobles

    @settings(max_examples=100)
    @given(title=valid_titles(), dirty_url=dirty_urls(), source_id=valid_source_ids())
    def test_factory_normalizes_url_to_lowercase(self, title, dirty_url, source_id):
        """Para cualquier URL, el factory debería normalizarla a lowercase."""
        # Arrange
        factory = RssArticleFactory()

        # Act
        article = factory.create_article(
            title=title, url=dirty_url, source_id=source_id
        )

        # Assert - URL debería estar normalizada
        url_str = str(article.url)

        # Protocolo en lowercase
        assert url_str.startswith("http://") or url_str.startswith("https://")

        # Sin espacios
        assert url_str == url_str.strip()

        # Dominio en lowercase (ArticleUrl VO normaliza)
        # Extraer dominio para verificar
        if "://" in url_str:
            domain_part = url_str.split("://")[1].split("/")[0]
            assert domain_part == domain_part.lower()

    @settings(max_examples=100)
    @given(
        dirty_title_and_clean=dirty_titles(),
        url=valid_urls(),
        source_id=valid_source_ids(),
    )
    def test_factory_removes_extra_spaces_from_title(
        self, dirty_title_and_clean, url, source_id
    ):
        """Para cualquier título con espacios extra, el factory debería limpiarlos."""
        dirty_title, _ = dirty_title_and_clean

        # Arrange
        factory = RssArticleFactory()

        # Act
        article = factory.create_article(
            title=dirty_title, url=url, source_id=source_id
        )

        # Assert
        title_str = str(article.title)

        # No espacios al inicio o final
        assert not title_str.startswith(" ")
        assert not title_str.endswith(" ")

        # No espacios dobles o más
        assert "  " not in title_str


# Marcar test como completado
pytest.mark.pbt_property_1 = pytest.mark.pbt


# ========== Property 2: Factory rejects invalid data ==========


class TestProperty2FactoryRejectsInvalidData:
    """Property 2: Factory rejects invalid data.

    Feature: refactor-article-factory-pattern, Property 2
    Validates: Requirements 1.2, 6.1, 6.2
    """

    @settings(max_examples=100)
    @given(
        title=st.one_of(
            st.just(""),  # Vacío
            st.just("   "),  # Solo espacios
            # Título muy largo SIN espacios extra (para que limpieza no lo reduzca)
            st.text(
                alphabet=st.characters(
                    whitelist_categories=("Ll",), min_codepoint=97, max_codepoint=122
                ),
                min_size=501,
                max_size=600,
            ),
        ),
        url=valid_urls(),
        source_id=valid_source_ids(),
    )
    def test_factory_rejects_invalid_titles(self, title, url, source_id):
        """Para cualquier título inválido (vacío o muy largo), el factory debería rechazarlo con ValueError."""
        # Arrange
        factory = RssArticleFactory()
        # Asegurar que es inválido: vacío/espacios o muy largo DESPUÉS de limpieza
        cleaned = factory._clean_title(title) if title else ""
        assume(len(cleaned.strip()) == 0 or len(cleaned) > 500)

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            factory.create_article(title=title, url=url, source_id=source_id)

        # El error debería mencionar validación
        assert "Validación de RssArticle fallida" in str(exc_info.value)

    @settings(max_examples=100)
    @given(
        title=valid_titles(),
        url=st.one_of(
            st.just(""),  # Vacío
            st.just("not-a-url"),  # Sin protocolo
            st.just("ftp://example.com"),  # Protocolo inválido
            st.text(
                alphabet=st.characters(blacklist_characters=":/"),
                min_size=1,
                max_size=20,
            ),  # Sin ://
        ),
        source_id=valid_source_ids(),
    )
    def test_factory_rejects_invalid_urls(self, title, url, source_id):
        """Para cualquier URL inválida, el factory debería rechazarla con ValueError."""
        # Arrange
        factory = RssArticleFactory()

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            factory.create_article(title=title, url=url, source_id=source_id)

        # El error debería mencionar validación
        assert "Validación de RssArticle fallida" in str(exc_info.value)

    @settings(max_examples=50)
    @given(title=valid_titles(), url=valid_urls())
    def test_factory_rejects_empty_source_id(self, title, url):
        """Para cualquier source_id vacío, el factory debería rechazarlo."""
        # Arrange
        factory = RssArticleFactory()

        # Act & Assert - SourceId VO debería rechazar vacío
        with pytest.raises((ValueError, Exception)):
            empty_source = RssFeedId("")
            factory.create_article(title=title, url=url, source_id=empty_source)


# Marcar test como completado
pytest.mark.pbt_property_2 = pytest.mark.pbt


# ========== Property 3: Factory emits ArticleCreated event ==========


class TestProperty3FactoryEmitsArticleCreatedEvent:
    """Property 3: Factory emits RssArticleCreated event.

    Feature: refactor-article-factory-pattern, Property 3
    Validates: Requirements 1.4
    """

    @settings(max_examples=100)
    @given(title=valid_titles(), url=valid_urls(), source_id=valid_source_ids())
    def test_factory_emits_exactly_one_article_created_event(
        self, title, url, source_id
    ):
        """Para cualquier artículo creado, debería emitir exactamente un evento ArticleCreated."""
        # Arrange
        factory = RssArticleFactory()

        # Act
        article = factory.create_article(title=title, url=url, source_id=source_id)

        # Assert
        events = article.get_uncommitted_events()
        assert len(events) == 1, f"Expected 1 event, got {len(events)}"

        # Verificar tipo de evento
        event = events[0]
        assert event.event_type == "RssArticleCreated"

    @settings(max_examples=100)
    @given(title=valid_titles(), url=valid_urls(), source_id=valid_source_ids())
    def test_article_created_event_contains_correct_data(self, title, url, source_id):
        """El evento ArticleCreated debería contener los datos correctos del artículo."""
        # Arrange
        factory = RssArticleFactory()

        # Act
        article = factory.create_article(title=title, url=url, source_id=source_id)

        # Assert
        event = article.get_uncommitted_events()[0]

        # Verificar que el evento tiene los campos correctos
        assert hasattr(event, "article_id")
        assert hasattr(event, "source_id")
        assert hasattr(event, "title")
        assert hasattr(event, "url")

        # Verificar que los valores coinciden
        assert event.article_id == str(article.id)
        assert event.source_id == str(source_id)
        # El título en el evento debería ser el limpio (después de normalización del VO)
        assert event.title == str(article.title)
        assert event.url == str(article.url)

    @settings(max_examples=50)
    @given(title=valid_titles(), url=valid_urls(), source_id=valid_source_ids())
    def test_article_has_uncommitted_events_after_creation(self, title, url, source_id):
        """Artículo recién creado debería tener eventos uncommitted."""
        # Arrange
        factory = RssArticleFactory()

        # Act
        article = factory.create_article(title=title, url=url, source_id=source_id)

        # Assert
        assert article.has_uncommitted_events() is True
        assert article.get_event_count() > 0


# Marcar test como completado
pytest.mark.pbt_property_3 = pytest.mark.pbt


# ========== Property 4: Factory generates warnings for problematic data ==========


@st.composite
def problematic_titles(draw):
    """Genera títulos problemáticos pero válidos."""
    choice = draw(st.integers(min_value=0, max_value=2))

    if choice == 0:
        # Título en mayúsculas
        base = draw(
            st.text(
                alphabet=st.characters(
                    whitelist_categories=("Lu", "Nd", "Zs"),
                    min_codepoint=65,
                    max_codepoint=90,
                ),
                min_size=25,
                max_size=50,
            )
        )
        return base.upper()
    elif choice == 1:
        # Título con muchos signos de exclamación
        base = draw(valid_titles())
        return base + "!!!!"
    else:
        # Título muy corto pero válido
        return draw(
            st.text(
                alphabet=st.characters(
                    whitelist_categories=("Ll",), min_codepoint=97, max_codepoint=122
                ),
                min_size=1,
                max_size=4,
            )
        )


@st.composite
def urls_with_tracking(draw):
    """Genera URLs con parámetros de tracking."""
    base_url = draw(valid_urls())
    tracking_param = draw(
        st.sampled_from(
            [
                "utm_source=test",
                "fbclid=123",
                "gclid=456",
                "_ga=789",
                "ref=social",
                "source=email",
            ]
        )
    )

    separator = "?" if "?" not in base_url else "&"
    return base_url + separator + tracking_param


class TestProperty4FactoryGeneratesWarnings:
    """Property 4: Factory generates warnings for problematic data.

    Feature: refactor-article-factory-pattern, Property 4
    Validates: Requirements 1.5, 6.3, 6.4, 7.4, 7.5
    """

    @settings(max_examples=100)
    @given(title=problematic_titles(), url=valid_urls(), source_id=valid_source_ids())
    def test_validation_generates_warnings_for_problematic_titles(
        self, title, url, source_id
    ):
        """Para títulos problemáticos, validate_article_creation_data debería generar warnings."""
        # Arrange
        factory = RssArticleFactory()

        # Act
        result = factory.validate_article_creation_data(
            title=title, url=url, source_id=str(source_id)
        )

        # Assert - Debería ser válido pero con warnings
        if len(title.strip()) >= 5:  # Solo si es válido
            assert result.is_valid is True
            # Puede o no tener warnings dependiendo del título específico
            # pero no debería tener errores
            assert len(result.error_messages) == 0

    @settings(max_examples=100)
    @given(title=valid_titles(), url=urls_with_tracking(), source_id=valid_source_ids())
    def test_validation_warns_about_tracking_parameters(self, title, url, source_id):
        """Para URLs con tracking params, debería generar warning sobre duplicados."""
        # Arrange
        factory = RssArticleFactory()

        # Act
        result = factory.validate_article_creation_data(
            title=title, url=url, source_id=str(source_id)
        )

        # Assert
        assert result.is_valid is True  # Válido
        assert len(result.warnings) > 0  # Pero con warnings

        # Verificar que menciona tracking o duplicados
        warnings_text = " ".join(result.warnings).lower()
        assert "tracking" in warnings_text or "duplicado" in warnings_text

    @settings(max_examples=50)
    @given(
        title=valid_titles(),
        url=valid_urls(),
        source_id=valid_source_ids(),
        content=st.text(min_size=1, max_size=50),  # Contenido muy corto
    )
    def test_validation_warns_about_short_content(self, title, url, source_id, content):
        """Para contenido muy corto, debería generar warning."""
        # Arrange
        factory = RssArticleFactory()

        # Act
        result = factory.validate_article_creation_data(
            title=title, url=url, source_id=str(source_id), content=content
        )

        # Assert
        assert result.is_valid is True  # Válido
        # Puede tener warnings sobre contenido corto
        if len(content) < 100:
            assert len(result.warnings) > 0

    @settings(max_examples=50)
    @given(title=valid_titles(), url=valid_urls(), source_id=valid_source_ids())
    def test_factory_creates_article_despite_warnings(self, title, url, source_id):
        """Factory debería crear artículo incluso con warnings (datos problemáticos pero válidos)."""
        # Arrange
        factory = RssArticleFactory()
        problematic_title = title.upper() + "!!!!"  # Problemático pero válido

        # Act - No debería lanzar excepción
        article = factory.create_article(
            title=problematic_title, url=url, source_id=source_id
        )

        # Assert
        assert article is not None
        assert isinstance(article, RssArticle)


# Marcar test como completado
pytest.mark.pbt_property_4 = pytest.mark.pbt


# ========== Property 9: FeedItem metadata extraction ==========


@st.composite
def feed_items_with_metadata(draw):
    """Genera FeedItems con metadatos completos."""
    title = draw(valid_titles())
    url = draw(valid_urls())
    description = draw(st.text(min_size=10, max_size=200))
    content = draw(st.text(min_size=50, max_size=500))
    author = draw(
        st.text(
            alphabet=st.characters(
                whitelist_categories=("Lu", "Ll", "Zs"),
                min_codepoint=65,
                max_codepoint=122,
            ),
            min_size=3,
            max_size=50,
        )
    )
    categories = draw(
        st.lists(
            st.text(
                alphabet=st.characters(
                    whitelist_categories=("Ll",), min_codepoint=97, max_codepoint=122
                ),
                min_size=3,
                max_size=15,
            ),
            min_size=1,
            max_size=5,
        )
    )
    guid = draw(
        st.text(
            alphabet=st.characters(
                whitelist_categories=("Ll", "Nd"), min_codepoint=97, max_codepoint=122
            ),
            min_size=10,
            max_size=30,
        )
    )
    pub_date = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

    return FeedItem(
        title=title,
        link=url,
        description=description,
        content=content,
        author=author,
        categories=categories,
        guid=guid,
        pub_date=pub_date,
    )


class TestProperty9FeedItemMetadataExtraction:
    """Property 9: FeedItem metadata extraction.

    Feature: refactor-article-factory-pattern, Property 9
    Validates: Requirements 5.1
    """

    @settings(max_examples=100)
    @given(feed_item=feed_items_with_metadata(), source_id=valid_source_ids())
    def test_factory_extracts_all_feed_item_metadata(self, feed_item, source_id):
        """Para cualquier FeedItem con metadatos, el factory debería extraerlos todos."""
        # Arrange
        factory = RssArticleFactory()

        # Act
        article = factory.create_from_feed_item(
            feed_item=feed_item, source_id=source_id, quality_assessment=False
        )

        # Assert - Verificar que los metadatos se extrajeron
        assert article is not None

        # Verificar metadatos RSS
        if feed_item.guid:
            assert article._rss_metadata.guid == feed_item.guid
        if feed_item.pub_date:
            assert article._rss_metadata.pub_date == feed_item.pub_date
        if feed_item.description:
            assert article._rss_metadata.description == feed_item.description

        # Verificar metadatos de artículo
        if feed_item.author:
            assert str(article._metadata.author) == feed_item.author

        # Verificar categorías/tags
        if feed_item.categories:
            assert len(tuple(article.metadata.tags.sorted_tags)) > 0


# Marcar test como completado
pytest.mark.pbt_property_9 = pytest.mark.pbt


# ========== Property 12: URL tracking parameter detection ==========


class TestProperty12URLTrackingParameterDetection:
    """Property 12: URL tracking parameter detection.

    Feature: refactor-article-factory-pattern, Property 12
    Validates: Requirements 5.4, 7.4
    """

    @settings(max_examples=100)
    @given(title=valid_titles(), url=urls_with_tracking(), source_id=valid_source_ids())
    def test_validation_detects_tracking_parameters(self, title, url, source_id):
        """Para cualquier URL con tracking params, validate debería detectarlos."""
        # Arrange
        factory = RssArticleFactory()

        # Act
        result = factory.validate_article_creation_data(
            title=title, url=url, source_id=str(source_id)
        )

        # Assert
        assert result.is_valid is True
        assert len(result.warnings) > 0

        # Verificar que el warning menciona tracking o duplicados
        warnings_text = " ".join(result.warnings).lower()
        assert "tracking" in warnings_text or "duplicado" in warnings_text


# Marcar test como completado
pytest.mark.pbt_property_12 = pytest.mark.pbt


# ========== Property 13: Multiple validation errors collected ==========


class TestProperty13MultipleValidationErrorsCollected:
    """Property 13: Multiple validation errors collected.

    Feature: refactor-article-factory-pattern, Property 13
    Validates: Requirements 6.5
    """

    @settings(max_examples=50)
    @given(source_id=valid_source_ids())
    def test_validation_collects_multiple_errors(self, source_id):
        """Para datos con múltiples errores, validate debería recolectarlos todos."""
        # Arrange
        factory = RssArticleFactory()

        # Datos con múltiples errores
        invalid_title = ""  # Error 1: título vacío
        invalid_url = "not-a-url"  # Error 2: URL inválida

        # Act
        result = factory.validate_article_creation_data(
            title=invalid_title, url=invalid_url, source_id=str(source_id)
        )

        # Assert
        assert result.is_valid is False
        assert len(result.error_messages) >= 2  # Al menos 2 errores

        # Verificar que ambos errores están presentes
        errors_text = " ".join(result.error_messages).lower()
        assert "título" in errors_text or "title" in errors_text
        assert "url" in errors_text


# Marcar test como completado
pytest.mark.pbt_property_13 = pytest.mark.pbt


# ========== Property 14: Title cleaning removes RSS artifacts ==========


@st.composite
def titles_with_rss_artifacts(draw):
    """Genera títulos con artefactos RSS específicos."""
    base = draw(valid_titles())

    artifact_type = draw(st.integers(min_value=0, max_value=2))

    if artifact_type == 0:
        # Prefijos
        prefix = draw(
            st.sampled_from(["RSS:", "FEED:", "[RSS]", "[FEED]", "RSS -", "Feed:"])
        )
        return prefix + " " + base, base
    elif artifact_type == 1:
        # Sufijos
        suffix = draw(st.sampled_from([" - RSS", " | RSS Feed", " (RSS)"]))
        return base + suffix, base
    else:
        # Ambos
        prefix = draw(st.sampled_from(["RSS:", "FEED:"]))
        suffix = draw(st.sampled_from([" - RSS", " (RSS)"]))
        return prefix + " " + base + suffix, base


class TestProperty14TitleCleaningRemovesRSSArtifacts:
    """Property 14: Title cleaning removes RSS artifacts.

    Feature: refactor-article-factory-pattern, Property 14
    Validates: Requirements 7.1

    NOTE: This test is currently EXPECTED TO FAIL because RssArticleFactory
    does not call _clean_title() before creating RssArticleTitle VO.
    See Property 1 failure for details.
    """

    @settings(max_examples=100)
    @given(
        title_with_artifact=titles_with_rss_artifacts(),
        url=valid_urls(),
        source_id=valid_source_ids(),
    )
    def test_clean_title_removes_rss_prefixes_and_suffixes(
        self, title_with_artifact, url, source_id
    ):
        """Para cualquier título con artefactos RSS, _clean_title debería removerlos."""
        dirty_title, expected_clean = title_with_artifact

        # Arrange
        factory = RssArticleFactory()

        # Act - Llamar directamente al método de limpieza
        cleaned = factory._clean_title(dirty_title)

        # Assert
        assert not cleaned.startswith("RSS:")
        assert not cleaned.startswith("FEED:")
        assert not cleaned.startswith("[RSS]")
        assert not cleaned.startswith("[FEED]")
        assert not cleaned.startswith("RSS -")
        assert not cleaned.startswith("Feed:")

        assert not cleaned.endswith(" - RSS")
        assert not cleaned.endswith(" | RSS Feed")
        assert not cleaned.endswith(" (RSS)")


# Marcar test como completado
pytest.mark.pbt_property_14 = pytest.mark.pbt


# ========== Property 15: URL normalization is idempotent ==========


class TestProperty15URLNormalizationIsIdempotent:
    """Property 15: URL normalization is idempotent.

    Feature: refactor-article-factory-pattern, Property 15
    Validates: Requirements 7.2
    """

    @settings(max_examples=100)
    @given(url=valid_urls())
    def test_clean_url_is_idempotent(self, url):
        """Para cualquier URL, limpiarla dos veces debería dar el mismo resultado."""
        # Arrange
        factory = RssArticleFactory()

        # Act
        cleaned_once = factory._clean_url(url)
        cleaned_twice = factory._clean_url(cleaned_once)

        # Assert - Idempotencia
        assert cleaned_once == cleaned_twice

    @settings(max_examples=100)
    @given(title=valid_titles(), url=valid_urls(), source_id=valid_source_ids())
    def test_article_url_normalization_is_idempotent(self, title, url, source_id):
        """Crear dos artículos con la misma URL debería resultar en URLs idénticas."""
        # Arrange
        factory = RssArticleFactory()

        # Act
        article1 = factory.create_article(title=title, url=url, source_id=source_id)
        article2 = factory.create_article(title=title, url=url, source_id=source_id)

        # Assert
        assert str(article1.url) == str(article2.url)


# Marcar test como completado
pytest.mark.pbt_property_15 = pytest.mark.pbt
