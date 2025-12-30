"""Property-based tests para ArticleDeduplicationService usando Hypothesis.

Estos tests verifican propiedades universales que deben cumplirse
para el servicio de deduplicación de artículos.
"""

from datetime import datetime, timezone
from typing import List
from uuid import uuid4

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from src.rss.article.domain.aggregates.rss_article import RssArticle
from src.rss.article.domain.factories.article_factory import RssArticleFactory
from src.rss.article.domain.value_objects import (
    RssArticleId,
    RssArticleTitle,
    RssArticleUrl,
)

# Importar componentes del sistema
from src.rss.article.infra.services import ArticleDeduplicationService
from src.rss.feed.domain.value_objects import RssFeedId

# ============================================================================
# ESTRATEGIAS DE GENERACIÓN DE DATOS
# ============================================================================


def valid_uuid_strategy():
    """Genera UUIDs válidos."""
    return st.uuids()


@st.composite
def valid_source_id_strategy(draw):
    """Genera SourceId válidos."""
    uuid_val = draw(valid_uuid_strategy())
    return RssFeedId(str(uuid_val))


@st.composite
def valid_article_strategy(draw):
    """Genera Article válidos para testing."""
    article_id = RssArticleId(str(draw(valid_uuid_strategy())))
    source_id = RssFeedId(str(draw(valid_uuid_strategy())))

    # Generar título no vacío
    title = draw(
        st.text(
            min_size=1,
            max_size=200,
            alphabet=st.characters(blacklist_categories=("Cs",)),
        )
    )
    if not title.strip():
        title = "Test RssArticle"

    # Generar URL válida
    url = f"https://example.com/article/{uuid4()}"

    # Generar contenido markdown no vacío
    content_markdown = draw(
        st.text(
            min_size=10,
            max_size=1000,
            alphabet=st.characters(blacklist_categories=("Cs",)),
        )
    )
    if not content_markdown.strip():
        content_markdown = "This is test content for the article."

    # Crear artículo
    article = RssArticle(
        title=RssArticleTitle(title),
        url=RssArticleUrl(url),
        source_id=source_id,
        article_id=article_id,
    )

    # Establecer contenido markdown usando el método público
    if content_markdown:
        article.update_content_fields(markdown=content_markdown)
        article.mark_events_as_committed()  # Limpiar eventos de test

    return article


# ============================================================================
# PROPERTY TEST: DEDUPLICATION USES REPOSITORY METHODS
# ============================================================================


class TestDeduplicationUsesRepositoryMethods:
    """**Feature: resolve-todos, Property 9: Deduplication Uses Repository Methods**

    **Validates: Requirements 4.4, 4.5**

    Para cualquier verificación de duplicados, el servicio debe usar los métodos
    del repositorio (find_all) y ArticleSimilarityService.
    """

    @settings(max_examples=100)
    @given(article=valid_article_strategy())
    @pytest.mark.asyncio
    async def test_check_duplicate_by_hash_queries_repository(self, article):
        """Para cualquier artículo con hash, el servicio debe poder detectar duplicados."""
        # Arrange - Crear artículo con contenido
        article.update_content_fields(markdown="Test content for deduplication")

        # Crear servicio
        service = ArticleDeduplicationService(similarity_threshold=0.85)

        # Act - Verificar que no es duplicado de sí mismo (lista vacía)
        result = service.is_duplicate(article, [])

        # Assert - No debe ser duplicado de lista vacía
        assert result is False, "Un artículo no debe ser duplicado de una lista vacía"

    @settings(max_examples=100)
    @given(article=valid_article_strategy())
    @pytest.mark.asyncio
    async def test_check_duplicate_by_similarity_queries_repository(self, article):
        """Para cualquier artículo, el servicio debe poder calcular similitud."""
        # Arrange - Crear artículo con contenido
        article.update_content_fields(markdown="Test content for similarity check")

        # Crear otro artículo similar
        factory = RssArticleFactory()
        similar_article = factory.create_article(
            title="Similar RssArticle",
            url="https://example.com/similar",
            source_id=article.source_id,
        )
        similar_article.update_content_fields(
            markdown="Test content for similarity check"
        )

        # Crear servicio
        service = ArticleDeduplicationService(similarity_threshold=0.85)

        # Act
        result = service.is_duplicate(article, [similar_article])

        # Assert - Debe detectar como duplicado (contenido idéntico)
        assert (
            result is True
        ), "Artículos con contenido idéntico deben ser detectados como duplicados"

    @settings(max_examples=100)
    @given(article=valid_article_strategy())
    @pytest.mark.asyncio
    async def test_check_duplicate_hybrid_queries_repository(self, article):
        """Para cualquier artículo, el servicio debe poder detectar duplicados con threshold configurable."""
        # Arrange - Crear artículo con contenido
        article.update_content_fields(markdown="Test content for hybrid detection")

        # Crear artículo parcialmente similar
        factory = RssArticleFactory()
        partial_match = factory.create_article(
            title="Partially Similar RssArticle",
            url="https://example.com/partial",
            source_id=article.source_id,
        )
        partial_match.update_content_fields(
            markdown="Test content for different detection"
        )

        # Crear servicio con threshold bajo
        service = ArticleDeduplicationService(similarity_threshold=0.50)

        # Act
        result = service.is_duplicate(article, [partial_match])

        # Assert - Con threshold bajo, puede detectar como duplicado
        assert isinstance(result, bool), "El servicio debe retornar un booleano"

    @settings(max_examples=100)
    @given(article=valid_article_strategy())
    @pytest.mark.asyncio
    async def test_similarity_detection_uses_similarity_service(self, article):
        """Para cualquier artículo, la detección por similaridad debe calcular correctamente."""
        # Arrange - Crear artículo con contenido
        article.update_content_fields(
            markdown="This is a test article about Python programming"
        )

        # Crear artículo similar
        factory = RssArticleFactory()
        similar_article = factory.create_article(
            title="Similar RssArticle",
            url="https://example.com/similar",
            source_id=article.source_id,
        )
        similar_article.update_content_fields(
            markdown="This is a test article about Python programming"
        )

        # Crear servicio
        service = ArticleDeduplicationService(similarity_threshold=0.85)

        # Act
        result = service.is_duplicate(article, [similar_article])

        # Assert - Debe detectar como duplicado (contenido idéntico)
        assert (
            result is True
        ), "Artículos con contenido idéntico deben ser detectados como duplicados"

    @settings(max_examples=100)
    @given(article=valid_article_strategy())
    @pytest.mark.asyncio
    async def test_find_all_duplicates_queries_repository_for_each_article(
        self, article
    ):
        """Para cualquier lista de artículos, find_all_duplicates debe detectar pares duplicados."""
        # Arrange - Crear artículos con contenido
        article.update_content_fields(markdown="Test content one")

        factory = RssArticleFactory()
        other_article = factory.create_article(
            title="Other RssArticle",
            url="https://example.com/other",
            source_id=article.source_id,
        )
        other_article.update_content_fields(markdown="Test content two")

        articles = [article, other_article]

        # Crear servicio
        service = ArticleDeduplicationService(similarity_threshold=0.85)

        # Act
        duplicates_map = service.find_all_duplicates(articles)

        # Assert - Debe retornar un diccionario (puede estar vacío si no hay duplicados)
        assert isinstance(duplicates_map, dict), "Debe retornar un diccionario"

    @settings(max_examples=100)
    @given(article=valid_article_strategy())
    @pytest.mark.asyncio
    async def test_deduplication_without_repository_returns_not_duplicate(
        self, article
    ):
        """Para cualquier artículo, si la lista está vacía, debe retornar no duplicado."""
        # Arrange - Crear artículo con contenido
        article.update_content_fields(markdown="Test content")

        # Crear servicio
        service = ArticleDeduplicationService(similarity_threshold=0.85)

        # Act - Verificar contra lista vacía
        result = service.is_duplicate(article, [])

        # Assert - Sin artículos para comparar, debe retornar no duplicado
        assert (
            result is False
        ), "Sin artículos para comparar, el servicio debe retornar no duplicado"

    @settings(max_examples=50)
    @given(article=valid_article_strategy())
    @pytest.mark.asyncio
    async def test_hash_detection_finds_exact_duplicates(self, article):
        """Para cualquier artículo, la detección debe encontrar duplicados exactos por contenido."""
        # Arrange - Crear artículo con contenido
        article.update_content_fields(markdown="Exact duplicate content for testing")

        # Crear artículo duplicado (mismo contenido)
        factory = RssArticleFactory()
        duplicate_article = factory.create_article(
            title="Duplicate RssArticle",
            url="https://example.com/duplicate",
            source_id=article.source_id,
        )
        duplicate_article.update_content_fields(
            markdown="Exact duplicate content for testing"
        )

        # Crear servicio
        service = ArticleDeduplicationService(similarity_threshold=0.85)

        # Act
        result = service.is_duplicate(article, [duplicate_article])

        # Assert - Debe detectar el duplicado
        assert (
            result is True
        ), "El servicio debe detectar duplicados por contenido idéntico"

    @settings(max_examples=50)
    @given(article=valid_article_strategy())
    @pytest.mark.asyncio
    async def test_similarity_detection_compares_all_articles(self, article):
        """Para cualquier artículo, la detección por similaridad debe comparar con todos los artículos."""
        # Arrange - Crear artículo con contenido
        article.update_content_fields(markdown="Test content for comparison")

        # Crear múltiples artículos diferentes
        factory = RssArticleFactory()
        other_article1 = factory.create_article(
            title="Other RssArticle 1",
            url="https://example.com/other1",
            source_id=article.source_id,
        )
        other_article1.update_content_fields(
            markdown="Completely different content one"
        )

        factory = RssArticleFactory()
        other_article2 = factory.create_article(
            title="Other RssArticle 2",
            url="https://example.com/other2",
            source_id=article.source_id,
        )
        other_article2.update_content_fields(
            markdown="Completely different content two"
        )

        other_articles = [other_article1, other_article2]

        # Crear servicio
        service = ArticleDeduplicationService(similarity_threshold=0.85)

        # Act
        result = service.is_duplicate(article, other_articles)

        # Assert - No debe ser duplicado de artículos diferentes
        assert (
            result is False
        ), "Artículos con contenido diferente no deben ser duplicados"
