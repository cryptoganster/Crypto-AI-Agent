# Guías de Testing

## Filosofía de Testing

- **Test Pyramid**: Más unit tests, menos integration tests, pocos e2e tests
- **Test Behavior, Not Implementation**: Testear el "qué", no el "cómo"
- **Fast Feedback**: Tests rápidos que se ejecutan frecuentemente
- **Isolated Tests**: Cada test debe ser independiente

## Tipos de Tests

### 1. Unit Tests

**Propósito**: Testear componentes individuales aislados

**Ubicación**: `tests/unit/`

**Características**:
- Rápidos (< 100ms por test)
- Sin dependencias externas (DB, APIs, filesystem)
- Usan mocks/stubs para dependencies
- Testean lógica de dominio pura

**Ejemplo**:
```python
import pytest
from src.domain.aggregates.article import Article, ArticleStatus
from src.domain.value_objects.content_quality import ContentQuality

class TestArticle:
    """Unit tests for Article aggregate."""
    
    def test_publish_article_with_sufficient_quality(self):
        # Arrange
        article = Article(
            id="123",
            source_id="src-1",
            title="Test Article",
            url="https://example.com/article",
            content="Test content",
            published_at=datetime.utcnow(),
            quality_score=0.8,
            status=ArticleStatus.DRAFT
        )
        
        # Act
        article.publish()
        
        # Assert
        assert article.status == ArticleStatus.PUBLISHED
        assert len(article._events) == 1
        assert isinstance(article._events[0], ArticlePublished)
    
    def test_publish_article_with_low_quality_raises_exception(self):
        # Arrange
        article = Article(
            id="123",
            source_id="src-1",
            title="Test Article",
            url="https://example.com/article",
            content="Test content",
            published_at=datetime.utcnow(),
            quality_score=0.3,  # Low quality
            status=ArticleStatus.DRAFT
        )
        
        # Act & Assert
        with pytest.raises(InvalidOperationException) as exc_info:
            article.publish()
        
        assert "insufficient quality" in str(exc_info.value).lower()
```

**Testing Value Objects**:
```python
class TestContentQuality:
    """Unit tests for ContentQuality value object."""
    
    def test_create_valid_content_quality(self):
        # Act
        quality = ContentQuality(
            score=0.8,
            readability=0.75,
            uniqueness=0.85
        )
        
        # Assert
        assert quality.score == 0.8
        assert quality.is_high_quality is True
    
    def test_create_content_quality_with_invalid_score_raises_exception(self):
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            ContentQuality(score=1.5, readability=0.5, uniqueness=0.5)
        
        assert "between 0 and 1" in str(exc_info.value)
    
    def test_content_quality_is_immutable(self):
        # Arrange
        quality = ContentQuality(score=0.8, readability=0.75, uniqueness=0.85)
        
        # Act & Assert
        with pytest.raises(AttributeError):
            quality.score = 0.9
```

**Testing Domain Services**:
```python
class TestArticleDeduplicationService:
    """Unit tests for ArticleDeduplicationService."""
    
    def test_is_duplicate_returns_true_for_similar_articles(self):
        # Arrange
        service = ArticleDeduplicationService(similarity_threshold=0.85)
        article = Article(
            id="1",
            title="Python Best Practices",
            content="Content about Python best practices..."
        )
        existing = [
            Article(
                id="2",
                title="Python Best Practices Guide",
                content="Content about Python best practices and patterns..."
            )
        ]
        
        # Act
        result = service.is_duplicate(article, existing)
        
        # Assert
        assert result is True
    
    def test_is_duplicate_returns_false_for_different_articles(self):
        # Arrange
        service = ArticleDeduplicationService(similarity_threshold=0.85)
        article = Article(id="1", title="Python", content="Python content")
        existing = [Article(id="2", title="Java", content="Java content")]
        
        # Act
        result = service.is_duplicate(article, existing)
        
        # Assert
        assert result is False
```

### 2. Integration Tests

**Propósito**: Testear integración entre componentes

**Ubicación**: `tests/integration/`

**Características**:
- Más lentos que unit tests
- Usan dependencias reales (test DB, etc.)
- Testean repositories, external services
- Requieren setup/teardown

**Ejemplo**:
```python
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from src.infra.persistence.repositories.article_repository import (
    SqlAlchemyArticleRepository
)
from src.domain.aggregates.article import Article

@pytest.mark.integration
class TestArticleRepository:
    """Integration tests for ArticleRepository."""
    
    @pytest.fixture
    async def repository(self, db_session: AsyncSession):
        """Create repository with test database session."""
        return SqlAlchemyArticleRepository(db_session)
    
    @pytest.fixture
    async def sample_article(self):
        """Create a sample article for testing."""
        return Article(
            id="test-123",
            source_id="src-1",
            title="Test Article",
            url="https://example.com/test",
            content="Test content",
            published_at=datetime.utcnow(),
            status=ArticleStatus.DRAFT
        )
    
    async def test_save_and_find_article(
        self,
        repository: SqlAlchemyArticleRepository,
        sample_article: Article
    ):
        # Act - Save
        await repository.save(sample_article)
        
        # Act - Find
        found = await repository.find_by_id(sample_article.id)
        
        # Assert
        assert found is not None
        assert found.id == sample_article.id
        assert found.title == sample_article.title
        assert found.content == sample_article.content
    
    async def test_find_by_url_returns_article(
        self,
        repository: SqlAlchemyArticleRepository,
        sample_article: Article
    ):
        # Arrange
        await repository.save(sample_article)
        
        # Act
        found = await repository.find_by_url(sample_article.url)
        
        # Assert
        assert found is not None
        assert found.id == sample_article.id
    
    async def test_delete_article(
        self,
        repository: SqlAlchemyArticleRepository,
        sample_article: Article
    ):
        # Arrange
        await repository.save(sample_article)
        
        # Act
        await repository.delete(sample_article.id)
        
        # Assert
        found = await repository.find_by_id(sample_article.id)
        assert found is None
```

**Testing External Services**:
```python
@pytest.mark.integration
@pytest.mark.external
class TestRssFetcherService:
    """Integration tests for RSS fetcher."""
    
    @pytest.fixture
    def fetcher(self):
        return RssFetcherService(timeout=30)
    
    async def test_fetch_valid_rss_feed(self, fetcher):
        # Arrange
        url = "https://example.com/feed.xml"
        
        # Act
        result = await fetcher.fetch(url)
        
        # Assert
        assert result.success is True
        assert len(result.entries) > 0
        assert result.entries[0].title is not None
    
    async def test_fetch_invalid_url_returns_error(self, fetcher):
        # Arrange
        url = "https://invalid-url-that-does-not-exist.com/feed.xml"
        
        # Act
        result = await fetcher.fetch(url)
        
        # Assert
        assert result.success is False
        assert result.error is not None
```

### 3. E2E Tests

**Propósito**: Testear flujos completos desde la API

**Ubicación**: `tests/e2e/`

**Características**:
- Más lentos
- Testean flujos de usuario completos
- Usan HTTP client para llamar API
- Verifican comportamiento end-to-end

**Ejemplo**:
```python
import pytest
from httpx import AsyncClient

@pytest.mark.e2e
class TestArticleWorkflow:
    """E2E tests for article workflow."""
    
    @pytest.fixture
    async def client(self):
        """Create HTTP client for API."""
        async with AsyncClient(base_url="http://localhost:8000") as client:
            yield client
    
    async def test_create_source_and_fetch_articles(self, client: AsyncClient):
        # Step 1: Create source
        source_data = {
            "name": "Test Source",
            "url": "https://example.com/feed.xml",
            "fetch_interval": 3600
        }
        response = await client.post("/api/v1/sources", json=source_data)
        assert response.status_code == 201
        source = response.json()
        source_id = source["id"]
        
        # Step 2: Start fetch session
        fetch_data = {"source_ids": [source_id]}
        response = await client.post("/api/v1/fetch-sessions", json=fetch_data)
        assert response.status_code == 201
        session = response.json()
        session_id = session["id"]
        
        # Step 3: Wait for completion (poll)
        await asyncio.sleep(5)
        
        # Step 4: Get articles
        response = await client.get(
            f"/api/v1/articles?source_id={source_id}"
        )
        assert response.status_code == 200
        articles = response.json()["items"]
        assert len(articles) > 0
        
        # Step 5: Verify article structure
        article = articles[0]
        assert "id" in article
        assert "title" in article
        assert "content" in article
        assert article["source_id"] == source_id
```

## Fixtures y Helpers

### Pytest Fixtures

**Ubicación**: `tests/conftest.py`

```python
import pytest
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

@pytest.fixture(scope="session")
async def db_engine():
    """Create test database engine."""
    engine = create_async_engine(
        "postgresql+asyncpg://test:test@localhost/test_db",
        echo=False
    )
    yield engine
    await engine.dispose()

@pytest.fixture
async def db_session(db_engine):
    """Create test database session."""
    async_session = sessionmaker(
        db_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    
    async with async_session() as session:
        # Setup
        yield session
        # Teardown
        await session.rollback()

@pytest.fixture
def sample_article_data():
    """Sample article data for testing."""
    return {
        "title": "Test Article",
        "url": "https://example.com/article",
        "content": "Test content",
        "source_id": "src-1"
    }
```

### Factory Functions

```python
# tests/factories.py
from datetime import datetime
from src.domain.aggregates.article import Article, ArticleStatus

def create_article(
    id: str = "test-123",
    title: str = "Test Article",
    **kwargs
) -> Article:
    """Factory function to create test articles."""
    defaults = {
        "source_id": "src-1",
        "url": "https://example.com/article",
        "content": "Test content",
        "published_at": datetime.utcnow(),
        "status": ArticleStatus.DRAFT
    }
    defaults.update(kwargs)
    
    return Article(id=id, title=title, **defaults)

# Usage in tests
def test_something():
    article = create_article(quality_score=0.8)
    # ...
```

## Mocking

### Usando pytest-mock

```python
def test_fetch_articles_calls_repository(mocker):
    # Arrange
    mock_repo = mocker.Mock(spec=IArticleRepository)
    mock_repo.find_by_source.return_value = [create_article()]
    
    service = ArticleService(repository=mock_repo)
    
    # Act
    articles = await service.fetch_articles("src-1")
    
    # Assert
    mock_repo.find_by_source.assert_called_once_with("src-1")
    assert len(articles) == 1
```

### Mocking External Services

```python
@pytest.fixture
def mock_rss_fetcher(mocker):
    """Mock RSS fetcher service."""
    mock = mocker.Mock(spec=IRssFetcherService)
    mock.fetch.return_value = FetchResult(
        success=True,
        entries=[{"title": "Test", "link": "https://example.com"}]
    )
    return mock

def test_with_mocked_fetcher(mock_rss_fetcher):
    service = FetchService(fetcher=mock_rss_fetcher)
    result = await service.fetch_from_source("src-1")
    assert result.success is True
```

## Property-Based Testing

Usar `hypothesis` para property-based testing:

```python
from hypothesis import given, strategies as st

@given(
    score=st.floats(min_value=0.0, max_value=1.0),
    readability=st.floats(min_value=0.0, max_value=1.0),
    uniqueness=st.floats(min_value=0.0, max_value=1.0)
)
def test_content_quality_properties(score, readability, uniqueness):
    """Property test for ContentQuality."""
    quality = ContentQuality(
        score=score,
        readability=readability,
        uniqueness=uniqueness
    )
    
    # Properties that should always hold
    assert 0 <= quality.score <= 1
    assert quality.is_high_quality == (quality.score >= 0.7)
```

## Coverage

### Ejecutar con Coverage

```bash
# Run tests with coverage
pytest --cov=src --cov-report=html --cov-report=term

# View HTML report
open htmlcov/index.html
```

### Coverage Goals

- **Domain Layer**: 90%+ coverage
- **Application Layer**: 85%+ coverage
- **Infrastructure Layer**: 70%+ coverage
- **Overall**: 80%+ coverage

## Best Practices

1. **Arrange-Act-Assert**: Estructura clara en cada test
2. **One Assertion Per Test**: Preferiblemente un concepto por test
3. **Descriptive Names**: Nombres que describen el escenario
4. **Fast Tests**: Optimizar para velocidad
5. **Independent Tests**: Sin dependencias entre tests
6. **Clean Fixtures**: Setup/teardown limpio
7. **Test Edge Cases**: No solo happy path
8. **Mock External Dependencies**: Aislar unit tests
