"""Fixtures para integration tests."""

import asyncio
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.chunking.container import ChunkingContainer
from src.chunking.infra.persistence.models import ContentChunkModel
from src.clustering.container import ClusteringContainer
from src.rag.container import RAGContainer
from src.shared.config import AppConfig
from src.shared.container import SharedContainer

# Database URL para tests (usar base de datos de test)
TEST_DATABASE_URL = (
    "postgresql+asyncpg://postgres:postgres@localhost:5432/rss_scraper_test"
)


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Crea sesión de base de datos para tests.

    Cada test obtiene una sesión limpia con rollback automático.
    """
    # Crear engine
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        pool_pre_ping=True,
    )

    # Crear tablas si no existen
    async with engine.begin() as conn:
        # Importar Base de los modelos
        await conn.run_sync(ContentChunkModel.metadata.create_all)

    # Crear session factory
    async_session = sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    # Crear sesión para el test
    async with async_session() as session:
        # Iniciar transacción
        async with session.begin():
            yield session
            # Rollback automático al salir
            await session.rollback()

    # Cleanup
    await engine.dispose()


@pytest.fixture
def app_config():
    """
    Crea AppConfig para tests.

    Usa configuración de test con base de datos de test.
    """
    return AppConfig()


@pytest.fixture
def shared_container(app_config):
    """
    Crea SharedContainer para tests.

    Contiene infraestructura compartida (logger, mediator, event bus).
    """
    return SharedContainer(app_config)


@pytest.fixture
def chunking_container(shared_container):
    """
    Crea ChunkingContainer para tests.

    Contiene servicios y handlers del bounded context Chunking.
    """
    return ChunkingContainer(shared_container)


# EmbeddingContainer eliminado - funcionalidad migrada a ChunkingContainer


@pytest.fixture
def clustering_container(shared_container):
    """
    Crea ClusteringContainer para tests.

    Contiene servicios y handlers del bounded context Clustering.
    """
    return ClusteringContainer(shared_container)


@pytest.fixture
def rag_container(shared_container, monkeypatch):
    """
    Crea RAGContainer para tests.

    Contiene servicios y handlers del bounded context RAG.
    Configura variables de entorno necesarias para RAG.
    """
    # Configurar variables de entorno para RAG
    monkeypatch.setenv("LLM_API_KEY", "test-api-key-for-testing")
    monkeypatch.setenv("LLM_MODEL", "gpt-4")
    monkeypatch.setenv("MAX_CONTEXT_TOKENS", "4000")
    monkeypatch.setenv("DEFAULT_TEMPERATURE", "0.3")
    monkeypatch.setenv("DEFAULT_MAX_TOKENS", "1000")

    return RAGContainer(shared_container)
