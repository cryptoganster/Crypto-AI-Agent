"""Property-based tests para RssContentCleanupService usando Hypothesis.

Estos tests verifican propiedades universales que deben cumplirse
para el servicio de limpieza de contenido RSS.
"""

from datetime import datetime, timezone
from typing import List
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

# Importar componentes del sistema
from src.domain.services.rss_content_cleanup_service import RssContentCleanupService
from src.rss.article.domain.aggregates.rss_article import RssArticle
from src.rss.article.domain.value_objects import (
    RssArticleId,
    RssArticleTitle,
    RssArticleUrl,
)
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
def valid_article_strategy(draw, source_id: SourceId):
    """Genera Article válidos para testing."""
    article_id = RssArticleId(str(draw(valid_uuid_strategy())))

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
# PROPERTY TEST: CLEANUP SERVICE USES REPOSITORY
# ============================================================================


class TestCleanupServiceUsesRepository:
    """**Feature: resolve-todos, Property 8: Cleanup Service Uses Repository**

    **Validates: Requirements 4.1, 4.2, 4.3**

    Para cualquier operación de limpieza, el servicio debe consultar el repositorio
    en lugar de retornar valores hardcodeados.
    """

    @settings(max_examples=100)
    @given(source_id=valid_source_id_strategy())
    @pytest.mark.asyncio
    async def test_cleanup_articles_queries_repository(self, source_id):
        """Para cualquier source_id, cleanup_articles_by_source debe consultar el repositorio."""
        # Arrange - Crear artículos mock
        mock_articles = [
            await self._create_mock_article(source_id),
            await self._create_mock_article(source_id),
        ]

        # Mock repository que retorna artículos
        mock_repository = AsyncMock()
        mock_repository.find_all = AsyncMock(return_value=mock_articles)
        mock_repository.delete = AsyncMock(return_value=True)

        # Crear servicio
        service = RssContentCleanupService(article_repository=mock_repository)

        # Act
        deleted_ids = await service.cleanup_articles_by_source(source_id)

        # Assert - El repositorio debe ser consultado
        mock_repository.find_all.assert_called_once_with(source_id=source_id)
        assert len(deleted_ids) == len(
            mock_articles
        ), "El número de IDs eliminados debe coincidir con el número de artículos"

    @settings(max_examples=100)
    @given(source_id=valid_source_id_strategy())
    @pytest.mark.asyncio
    async def test_cleanup_impact_queries_repository(self, source_id):
        """Para cualquier source_id, get_cleanup_impact_summary debe consultar el repositorio."""
        # Arrange - Crear artículos mock
        mock_articles = [
            await self._create_mock_article(source_id),
            await self._create_mock_article(source_id),
            await self._create_mock_article(source_id),
        ]

        # Mock repository
        mock_repository = AsyncMock()
        mock_repository.find_all = AsyncMock(return_value=mock_articles)

        # Crear servicio
        service = RssContentCleanupService(article_repository=mock_repository)

        # Act
        summary = await service.get_cleanup_impact_summary(source_id)

        # Assert - El repositorio debe ser consultado
        mock_repository.find_all.assert_called_once_with(source_id=source_id)
        assert summary.articles_to_remove == len(
            mock_articles
        ), "El resumen debe reflejar el número real de artículos"
        assert (
            summary.articles_to_remove > 0
        ), "El resumen no debe retornar 0 cuando hay artículos"

    @settings(max_examples=100)
    @given(
        source_id=valid_source_id_strategy(),
        article_count=st.integers(min_value=0, max_value=10),
    )
    @pytest.mark.asyncio
    async def test_cleanup_returns_actual_count_not_hardcoded(
        self, source_id, article_count
    ):
        """Para cualquier número de artículos, el servicio debe retornar el conteo real, no hardcodeado."""
        # Arrange - Crear número variable de artículos
        mock_articles = []
        for _ in range(article_count):
            article = await self._create_mock_article(source_id)
            mock_articles.append(article)

        # Mock repository
        mock_repository = AsyncMock()
        mock_repository.find_all = AsyncMock(return_value=mock_articles)
        mock_repository.delete = AsyncMock(return_value=True)

        # Crear servicio
        service = RssContentCleanupService(article_repository=mock_repository)

        # Act
        deleted_ids = await service.cleanup_articles_by_source(source_id)

        # Assert - El conteo debe ser real, no hardcodeado a 0
        assert (
            len(deleted_ids) == article_count
        ), f"El servicio debe retornar {article_count} IDs eliminados, no un valor hardcodeado"

    @settings(max_examples=100)
    @given(source_id=valid_source_id_strategy())
    @pytest.mark.asyncio
    async def test_cleanup_calls_delete_for_each_article(self, source_id):
        """Para cualquier conjunto de artículos, el servicio debe llamar delete para cada uno."""
        # Arrange
        mock_articles = [
            await self._create_mock_article(source_id),
            await self._create_mock_article(source_id),
            await self._create_mock_article(source_id),
        ]

        # Mock repository
        mock_repository = AsyncMock()
        mock_repository.find_all = AsyncMock(return_value=mock_articles)
        mock_repository.delete = AsyncMock(return_value=True)

        # Crear servicio
        service = RssContentCleanupService(article_repository=mock_repository)

        # Act
        deleted_ids = await service.cleanup_articles_by_source(source_id)

        # Assert - delete debe ser llamado para cada artículo
        assert mock_repository.delete.call_count == len(
            mock_articles
        ), "El repositorio debe ser llamado para eliminar cada artículo"

        # Verificar que se llamó con los IDs correctos
        for article in mock_articles:
            mock_repository.delete.assert_any_call(article.id)

    @settings(max_examples=100)
    @given(source_id=valid_source_id_strategy())
    @pytest.mark.asyncio
    async def test_impact_summary_calculates_real_data_size(self, source_id):
        """Para cualquier conjunto de artículos, el resumen debe calcular el tamaño real de datos."""
        # Arrange - Crear artículos con contenido de tamaño conocido
        mock_articles = [
            await self._create_mock_article_with_content(source_id, "A" * 1000),
            await self._create_mock_article_with_content(source_id, "B" * 2000),
        ]

        # Mock repository
        mock_repository = AsyncMock()
        mock_repository.find_all = AsyncMock(return_value=mock_articles)

        # Crear servicio
        service = RssContentCleanupService(article_repository=mock_repository)

        # Act
        summary = await service.get_cleanup_impact_summary(source_id)

        # Assert - El tamaño debe ser calculado, no hardcodeado a 0.0
        assert (
            summary.estimated_data_size_mb > 0.0
        ), "El tamaño estimado debe ser calculado basado en datos reales, no hardcodeado a 0.0"

    @settings(max_examples=100)
    @given(source_id=valid_source_id_strategy())
    @pytest.mark.asyncio
    async def test_cleanup_with_empty_repository_returns_empty_list(self, source_id):
        """Para cualquier source sin artículos, el servicio debe retornar lista vacía."""
        # Arrange - Repository vacío
        mock_repository = AsyncMock()
        mock_repository.find_all = AsyncMock(return_value=[])

        # Crear servicio
        service = RssContentCleanupService(article_repository=mock_repository)

        # Act
        deleted_ids = await service.cleanup_articles_by_source(source_id)

        # Assert
        assert (
            len(deleted_ids) == 0
        ), "El servicio debe retornar lista vacía cuando no hay artículos"
        mock_repository.find_all.assert_called_once()

    @settings(max_examples=50)
    @given(
        source_id=valid_source_id_strategy(),
        article_count=st.integers(min_value=1, max_value=5),
    )
    @pytest.mark.asyncio
    async def test_cleanup_impact_includes_affected_categories(
        self, source_id, article_count
    ):
        """Para cualquier conjunto de artículos con categorías, el resumen debe incluirlas."""
        # Arrange - Crear artículos con categorías
        mock_articles = []
        categories = ["Tech", "Science", "Business"]
        for i in range(article_count):
            article = await self._create_mock_article(source_id)
            article._category = categories[i % len(categories)]
            mock_articles.append(article)

        # Mock repository
        mock_repository = AsyncMock()
        mock_repository.find_all = AsyncMock(return_value=mock_articles)

        # Crear servicio
        service = RssContentCleanupService(article_repository=mock_repository)

        # Act
        summary = await service.get_cleanup_impact_summary(source_id)

        # Assert - Las categorías deben estar presentes
        assert (
            len(summary.affected_categories) > 0
        ), "El resumen debe incluir categorías afectadas cuando existen"

        # Verificar que las categorías son de los artículos
        for category in summary.affected_categories:
            assert (
                category in categories
            ), f"La categoría {category} debe ser una de las categorías de los artículos"

    # Helper methods
    async def _create_mock_article(self, source_id: SourceId) -> RssArticle:
        """Crea un Article mock para testing."""
        article_id = RssArticleId(str(uuid4()))
        title = RssArticleTitle("Test RssArticle")
        url = RssArticleUrl(f"https://example.com/article/{uuid4()}")

        article = RssArticle(
            title=title,
            url=url,
            source_id=source_id,
            article_id=article_id,
        )

        article.update_content_fields(markdown="This is test content for the article.")
        article.mark_events_as_committed()  # Limpiar eventos de test

        return article

    async def _create_mock_article_with_content(
        self, source_id: RssFeedId, content: str
    ) -> RssArticle:
        """Crea un Article mock con contenido específico."""
        article_id = RssArticleId(str(uuid4()))
        title = RssArticleTitle("Test RssArticle")
        url = RssArticleUrl(f"https://example.com/article/{uuid4()}")

        article = RssArticle(
            title=title,
            url=url,
            source_id=source_id,
            article_id=article_id,
        )

        article.update_content_fields(markdown=content)
        article.mark_events_as_committed()  # Limpiar eventos de test

        return article
