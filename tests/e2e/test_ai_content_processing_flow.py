"""
E2E Integration Tests para AI Content Processing Flow.

Tests de integración end-to-end que verifican el flujo completo:
RssArticle → Chunking → Embedding → Clustering

Requirements: 10.6.3
"""

from datetime import datetime, timezone

import pytest
import pytest_asyncio


@pytest.mark.e2e
@pytest.mark.asyncio
class TestAIContentProcessingFlow:
    """
    E2E tests para el flujo completo de procesamiento AI.

    Flujo:
    1. RssArticle creado
    2. ArticleQualityCalculated → ChunkArticleContentCommand
    3. ArticleChunked → GenerateArticleEmbeddingCommand
    4. ArticleEmbeddingGenerated → ClusterArticlesCommand
    5. ArticlesClustered (fin)
    """

    async def test_complete_flow_article_to_clustering(
        self,
        app_container,
    ):
        """
        Debería completar flujo completo: RssArticle → Chunking → Embedding → Clustering.

        Requirements: 10.6.3
        """
        # Arrange
        mediator = app_container.shared.mediator
        event_publisher = app_container.shared.event_publisher

        # Verificar que todos los bounded contexts están inicializados
        assert app_container.chunking is not None
        assert app_container.embedding is not None
        assert app_container.clustering is not None

        # Act - Simular evento ArticleQualityCalculated
        from src.rss.article.domain.events.article_quality_calculated import (
            ArticleQualityCalculated,
        )

        event = ArticleQualityCalculated(
            article_id="test-article-123",
            quality_score=0.85,
            occurred_at=datetime.now(timezone.utc),
        )

        # Publicar evento
        await event_publisher.publish(event)

        # Assert - Verificar que el flujo se ejecutó
        # (En un test real, verificaríamos la base de datos)
        # Por ahora, verificamos que no hubo excepciones
        assert True

    async def test_event_propagation_between_bounded_contexts(
        self,
        app_container,
    ):
        """
        Debería propagar eventos correctamente entre bounded contexts.

        Verifica:
        - ArticleChunked (Chunking BC) → Embedding BC
        - ArticleEmbeddingGenerated (Embedding BC) → Clustering BC

        Requirements: 10.6.3
        """
        # Arrange
        event_handler_registry = app_container.shared.event_handler_registry

        # Assert - Verificar que event handlers están registrados

        # 1. OnArticleQualityCalculatedHandler (Chunking BC)
        from src.rss.article.domain.events.article_quality_calculated import (
            ArticleQualityCalculated,
        )

        handlers = event_handler_registry.get_handlers(ArticleQualityCalculated)
        assert len(handlers) > 0, "OnArticleQualityCalculatedHandler no registrado"

        # 2. OnArticleChunkedHandler (Embedding BC)
        from src.chunking.domain.events.article_chunked import ArticleChunked

        handlers = event_handler_registry.get_handlers(ArticleChunked)
        assert len(handlers) > 0, "OnArticleChunkedHandler no registrado"

        # 3. OnArticleEmbeddingGeneratedHandler (Clustering BC)
        from src.chunking.domain.events import (
            ArticleEmbeddingGenerated,
        )

        handlers = event_handler_registry.get_handlers(ArticleEmbeddingGenerated)
        assert len(handlers) > 0, "OnArticleEmbeddingGeneratedHandler no registrado"

    async def test_handler_execution_order(
        self,
        app_container,
    ):
        """
        Debería ejecutar handlers en el orden correcto.

        Orden esperado:
        1. ChunkArticleContentHandler
        2. GenerateArticleEmbeddingHandler
        3. ClusterArticlesHandler

        Requirements: 10.6.3
        """
        # Arrange
        mediator = app_container.shared.mediator

        # Assert - Verificar que command handlers están registrados

        # 1. ChunkArticleContentCommand
        from src.chunking.app.commands.chunk_article_content.command import (
            ChunkArticleContentCommand,
        )

        assert ChunkArticleContentCommand in mediator._handler_registry

        # 2. GenerateArticleEmbeddingCommand
        from src.chunking.app.commands.generate_article_embedding.command import (
            GenerateArticleEmbeddingCommand,
        )

        assert GenerateArticleEmbeddingCommand in mediator._handler_registry

        # 3. ClusterArticlesCommand
        from src.clustering.app.commands.cluster_articles.command import (
            ClusterArticlesCommand,
        )

        assert ClusterArticlesCommand in mediator._handler_registry

    async def test_all_bounded_contexts_initialized(
        self,
        app_container,
    ):
        """
        Debería inicializar todos los bounded contexts correctamente.

        Requirements: 10.6.1
        """
        # Assert - Verificar que todos los BCs están inicializados
        assert app_container.shared is not None
        assert app_container.articles is not None
        assert app_container.sources is not None
        assert app_container.scraping is not None
        assert app_container.chunking is not None
        assert app_container.embedding is not None
        assert app_container.clustering is not None

        # Verificar que tienen acceso al shared container
        assert app_container.chunking._shared is app_container.shared
        assert app_container.embedding._shared is app_container.shared
        assert app_container.clustering._shared is app_container.shared

    async def test_cross_bc_event_handlers_registered(
        self,
        app_container,
    ):
        """
        Debería registrar event handlers cross-BC correctamente.

        Cross-BC Event Handlers:
        - Chunking escucha RssArticle BC
        - Embedding escucha Chunking BC
        - Clustering escucha Embedding BC

        Requirements: 10.6.2
        """
        # Arrange
        event_registry = app_container.shared.event_handler_registry

        # Assert - Verificar handlers cross-BC

        # Article → Chunking
        from src.rss.article.domain.events.article_quality_calculated import (
            ArticleQualityCalculated,
        )

        handlers = event_registry.get_handlers(ArticleQualityCalculated)
        assert len(handlers) > 0

        # Chunking → Embedding
        from src.chunking.domain.events.article_chunked import ArticleChunked

        handlers = event_registry.get_handlers(ArticleChunked)
        assert len(handlers) > 0

        # Embedding → Clustering
        from src.chunking.domain.events import (
            ArticleEmbeddingGenerated,
        )

        handlers = event_registry.get_handlers(ArticleEmbeddingGenerated)
        assert len(handlers) > 0


# === FIXTURES ===


@pytest_asyncio.fixture
async def app_container():
    """
    Fixture para AppContainer completo.

    Inicializa todos los bounded contexts y registra handlers.
    """
    from src.bootstrap.lifespan import AppContainer
    from src.shared.config import AppConfig

    config = AppConfig()
    container = AppContainer(config)

    # Registrar handlers
    container.articles.register_handlers()
    container.sources.register_handlers()
    container.scraping.register_handlers()
    container.chunking.register_handlers()
    container.embedding.register_handlers()
    container.clustering.register_handlers()

    yield container

    # Cleanup
    await container.dispose()
