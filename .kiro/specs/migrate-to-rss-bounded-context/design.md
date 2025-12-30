# Design Document

## Overview

Este documento describe el diseño técnico para migrar los bounded contexts `source/` y `article/` a una estructura más específica y escalable bajo `src/rss/`, con sub-bounded contexts `feed/` y `article/`. La migración mejora el Ubiquitous Language, prepara el sistema para múltiples tipos de contenido, y mantiene la separación clara de responsabilidades siguiendo principios de DDD.

## Architecture

### Current Structure (Before Migration)

```
src/
├── source/                    # Generic "Source" BC
│   ├── app/
│   ├── domain/
│   │   ├── aggregates/
│   │   │   └── source.py      # Source aggregate
│   │   ├── value_objects/
│   │   │   └── source_id.py
│   │   └── events/
│   ├── infra/
│   └── container.py
│
├── article/                   # Generic "Article" BC
│   ├── app/
│   ├── domain/
│   │   ├── aggregates/
│   │   │   └── article.py     # Article aggregate
│   │   ├── value_objects/
│   │   │   └── article_id.py
│   │   └── events/
│   ├── infra/
│   └── container.py
│
└── chunking/                  # To be renamed to "knowledge"
    └── ...
```

### Target Structure (After Migration)

```
src/
├── rss/                       # RSS Bounded Context
│   ├── feed/                  # Sub-BC for RSS Feeds
│   │   ├── app/
│   │   │   ├── commands/
│   │   │   │   ├── create_rss_feed/
│   │   │   │   ├── update_rss_feed/
│   │   │   │   └── ...
│   │   │   ├── queries/
│   │   │   │   ├── get_rss_feed_by_id/
│   │   │   │   ├── list_rss_feeds/
│   │   │   │   └── ...
│   │   │   └── event_handlers/
│   │   ├── domain/
│   │   │   ├── aggregates/
│   │   │   │   └── rss_feed.py        # RssFeed aggregate
│   │   │   ├── value_objects/
│   │   │   │   ├── rss_feed_id.py
│   │   │   │   ├── rss_feed_url.py
│   │   │   │   └── ...
│   │   │   ├── events/
│   │   │   │   ├── rss_feed_created.py
│   │   │   │   ├── rss_feed_updated.py
│   │   │   │   └── ...
│   │   │   ├── services/
│   │   │   ├── factories/
│   │   │   │   └── rss_feed_factory.py
│   │   │   └── interfaces/
│   │   │       ├── repositories/
│   │   │       │   ├── rss_feed_read_repository.py
│   │   │       │   └── rss_feed_write_repository.py
│   │   │       └── services/
│   │   ├── infra/
│   │   │   ├── persistence/
│   │   │   │   ├── models/
│   │   │   │   │   └── rss_feed_model.py
│   │   │   │   ├── mappers/
│   │   │   │   │   └── rss_feed_mapper.py
│   │   │   │   └── repositories/
│   │   │   │       ├── rss_feed_read_repository.py
│   │   │   │       └── rss_feed_write_repository.py
│   │   │   └── external/
│   │   └── container.py       # RssFeedContainer
│   │
│   ├── article/               # Sub-BC for RSS Articles
│   │   ├── app/
│   │   │   ├── commands/
│   │   │   │   ├── create_rss_article/
│   │   │   │   ├── scrape_rss_article_content/
│   │   │   │   └── ...
│   │   │   ├── queries/
│   │   │   │   ├── get_rss_article_by_id/
│   │   │   │   ├── list_rss_articles/
│   │   │   │   └── ...
│   │   │   ├── event_handlers/
│   │   │   └── process_managers/
│   │   ├── domain/
│   │   │   ├── aggregates/
│   │   │   │   └── rss_article.py     # RssArticle aggregate
│   │   │   ├── value_objects/
│   │   │   │   ├── rss_article_id.py
│   │   │   │   ├── rss_article_url.py
│   │   │   │   └── ...
│   │   │   ├── events/
│   │   │   │   ├── rss_article_created.py
│   │   │   │   ├── rss_article_content_scraped.py
│   │   │   │   └── ...
│   │   │   ├── services/
│   │   │   ├── factories/
│   │   │   │   └── rss_article_factory.py
│   │   │   └── interfaces/
│   │   │       ├── repositories/
│   │   │       │   ├── rss_article_read_repository.py
│   │   │       │   └── rss_article_write_repository.py
│   │   │       └── services/
│   │   ├── infra/
│   │   │   ├── persistence/
│   │   │   │   ├── models/
│   │   │   │   │   └── rss_article_model.py
│   │   │   │   ├── mappers/
│   │   │   │   │   └── rss_article_mapper.py
│   │   │   │   └── repositories/
│   │   │   │       ├── rss_article_read_repository.py
│   │   │   │       └── rss_article_write_repository.py
│   │   │   └── external/
│   │   └── container.py       # RssArticleContainer
│   │
│   └── shared/                # Shared kernel for RSS
│       ├── value_objects/
│       │   └── rss_metadata.py
│       └── exceptions/
│           └── rss_exceptions.py
│
├── knowledge/                 # Renamed from "chunking"
│   ├── domain/
│   │   ├── aggregates/
│   │   │   └── knowledge_chunk.py
│   │   └── value_objects/
│   │       └── source_reference.py  # Generic reference
│   └── ...
│
└── twitter/                   # Future BC (example)
    ├── tweet/
    │   ├── app/
    │   ├── domain/
    │   │   ├── aggregates/
    │   │   │   └── tweet.py
    │   │   └── value_objects/
    │   │       └── tweet_id.py
    │   ├── infra/
    │   └── container.py
    └── account/
        └── ...
```

## Components and Interfaces

### 1. RssFeed Aggregate (src/rss/feed/domain/aggregates/rss_feed.py)

```python
"""RssFeed aggregate root."""

from datetime import datetime, timezone
from typing import Optional

from src.shared.kernel import IAggregateRoot
from src.rss.feed.domain.value_objects.rss_feed_id import RssFeedId
from src.rss.feed.domain.value_objects.rss_feed_url import RssFeedUrl
from src.rss.feed.domain.events import RssFeedCreated, RssFeedUpdated


class RssFeed(IAggregateRoot[RssFeedId]):
    """
    Aggregate root para RSS Feed.
    
    Un RssFeed representa una fuente RSS que contiene múltiples artículos.
    Es responsable de mantener la configuración del feed, métricas de salud,
    y coordinar el proceso de fetching.
    
    Attributes:
        id: Identificador único del feed
        name: Nombre descriptivo del feed
        url: URL del feed RSS
        description: Descripción opcional del feed
        is_active: Si el feed está activo para fetching
        fetch_interval_minutes: Intervalo de fetching en minutos
        last_fetched_at: Última vez que se fetcheó el feed
        created_at: Timestamp de creación
        updated_at: Timestamp de última actualización
    """
    
    def __init__(
        self,
        id: RssFeedId,
        name: str,
        url: RssFeedUrl,
        description: Optional[str] = None,
        is_active: bool = True,
        fetch_interval_minutes: int = 60,
        last_fetched_at: Optional[datetime] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
    ):
        super().__init__()
        
        self._id = id
        self._name = name
        self._url = url
        self._description = description
        self._is_active = is_active
        self._fetch_interval_minutes = fetch_interval_minutes
        self._last_fetched_at = last_fetched_at
        self._created_at = created_at or datetime.now(timezone.utc)
        self._updated_at = updated_at or datetime.now(timezone.utc)
        
        self._validate_invariants()
    
    # Properties and business logic...
```

### 2. RssArticle Aggregate (src/rss/article/domain/aggregates/rss_article.py)

```python
"""RssArticle aggregate root."""

from datetime import datetime, timezone
from typing import Optional

from src.shared.kernel import IAggregateRoot
from src.rss.article.domain.value_objects.rss_article_id import RssArticleId
from src.rss.article.domain.value_objects.rss_article_url import RssArticleUrl
from src.rss.article.domain.events import RssArticleCreated, RssArticleContentScraped


class RssArticle(IAggregateRoot[RssArticleId]):
    """
    Aggregate root para RSS Article.
    
    Un RssArticle representa un artículo individual obtenido de un feed RSS.
    Es responsable de mantener el contenido del artículo, metadata,
    y coordinar el procesamiento (scraping, análisis, chunking).
    
    Attributes:
        id: Identificador único del artículo
        feed_id: ID del feed RSS al que pertenece
        title: Título del artículo
        url: URL del artículo
        content: Contenido completo del artículo
        published_at: Fecha de publicación
        created_at: Timestamp de creación
        updated_at: Timestamp de última actualización
    """
    
    def __init__(
        self,
        id: RssArticleId,
        feed_id: str,  # Reference to RssFeed
        title: str,
        url: RssArticleUrl,
        content: Optional[str] = None,
        published_at: Optional[datetime] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
    ):
        super().__init__()
        
        self._id = id
        self._feed_id = feed_id
        self._title = title
        self._url = url
        self._content = content
        self._published_at = published_at
        self._created_at = created_at or datetime.now(timezone.utc)
        self._updated_at = updated_at or datetime.now(timezone.utc)
        
        self._validate_invariants()
    
    # Properties and business logic...
```

### 3. SourceReference Value Object (src/knowledge/domain/value_objects/source_reference.py)

```python
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
        
        >>> # Tweet (FUTURO - no implementado aún)
        >>> ref = SourceReference(
        ...     source_type="tweet",
        ...     source_id="tweet-456",
        ...     source_url="https://twitter.com/user/status/456"
        ... )
    
    Notes:
        - Actualmente solo "rss_article" tiene bounded context implementado
        - Otros tipos están definidos para preparar extensibilidad futura
        - Al agregar nuevos tipos, crear su bounded context correspondiente
    """
    
    source_type: str
    source_id: str
    source_url: str
    
    def __post_init__(self):
        """Valida invariantes del VO."""
        if not self.source_type or not self.source_type.strip():
            raise ValueError("source_type no puede estar vacío")
        
        if not self.source_id or not self.source_id.strip():
            raise ValueError("source_id no puede estar vacío")
        
        if not self.source_url or not self.source_url.startswith(("http://", "https://", "file://")):
            raise ValueError("source_url debe ser una URL válida")
        
        # Validar source_types conocidos
        # NOTA: Solo "rss_article" está implementado actualmente
        valid_types = {
            "rss_article",      # ✅ IMPLEMENTADO
            "tweet",            # ⏳ FUTURO
            "pdf_document",     # ⏳ FUTURO
            "book",             # ⏳ FUTURO
            "instagram_post",   # ⏳ FUTURO
            "linkedin_post",    # ⏳ FUTURO
        }
        
        if self.source_type not in valid_types:
            raise ValueError(
                f"source_type '{self.source_type}' no es válido. "
                f"Tipos válidos: {', '.join(valid_types)}"
            )
    
    def is_rss_article(self) -> bool:
        """Verifica si la fuente es un artículo RSS (IMPLEMENTADO)."""
        return self.source_type == "rss_article"
    
    def is_tweet(self) -> bool:
        """Verifica si la fuente es un tweet (FUTURO - no implementado)."""
        return self.source_type == "tweet"
    
    def is_pdf(self) -> bool:
        """Verifica si la fuente es un PDF (FUTURO - no implementado)."""
        return self.source_type == "pdf_document"
    
    def is_book(self) -> bool:
        """Verifica si la fuente es un libro (FUTURO - no implementado)."""
        return self.source_type == "book"
    
    def is_instagram_post(self) -> bool:
        """Verifica si la fuente es un post de Instagram (FUTURO - no implementado)."""
        return self.source_type == "instagram_post"
    
    def is_linkedin_post(self) -> bool:
        """Verifica si la fuente es un post de LinkedIn (FUTURO - no implementado)."""
        return self.source_type == "linkedin_post"
```

### 4. Dependency Injection Containers

#### RssFeedContainer (src/rss/feed/container.py)

```python
"""Dependency injection container for RSS Feed sub-BC."""

from dependency_injector import containers, providers

from src.rss.feed.domain.factories import RssFeedFactory
from src.rss.feed.infra.persistence.repositories import (
    SqlAlchemyRssFeedReadRepository,
    SqlAlchemyRssFeedWriteRepository,
)


class RssFeedContainer(containers.DeclarativeContainer):
    """Container para RSS Feed bounded context."""
    
    # Infrastructure dependencies (injected from parent)
    infra = providers.DependenciesContainer()
    
    # Factories
    rss_feed_factory = providers.Singleton(RssFeedFactory)
    
    # Repositories
    rss_feed_read_repository = providers.Factory(
        SqlAlchemyRssFeedReadRepository,
        session=infra.db_session,
    )
    
    rss_feed_write_repository = providers.Factory(
        SqlAlchemyRssFeedWriteRepository,
        session=infra.db_session,
    )
    
    # Command Handlers
    def get_create_rss_feed_handler(self):
        from src.rss.feed.app.commands.create_rss_feed.handler import (
            CreateRssFeedHandler,
        )
        return CreateRssFeedHandler(
            rss_feed_factory=self.rss_feed_factory(),
            rss_feed_write_repository=self.rss_feed_write_repository(),
            event_bus=self.infra.event_bus,
            logger=self.infra.logger,
        )
    
    # Query Handlers
    def get_get_rss_feed_by_id_handler(self):
        from src.rss.feed.app.queries.get_rss_feed_by_id.handler import (
            GetRssFeedByIdHandler,
        )
        return GetRssFeedByIdHandler(
            rss_feed_read_repository=self.rss_feed_read_repository(),
            logger=self.infra.logger,
        )
```

#### RssArticleContainer (src/rss/article/container.py)

```python
"""Dependency injection container for RSS Article sub-BC."""

from dependency_injector import containers, providers

from src.rss.article.domain.factories import RssArticleFactory
from src.rss.article.infra.persistence.repositories import (
    SqlAlchemyRssArticleReadRepository,
    SqlAlchemyRssArticleWriteRepository,
)


class RssArticleContainer(containers.DeclarativeContainer):
    """Container para RSS Article bounded context."""
    
    # Infrastructure dependencies (injected from parent)
    infra = providers.DependenciesContainer()
    
    # Factories
    rss_article_factory = providers.Singleton(RssArticleFactory)
    
    # Repositories
    rss_article_read_repository = providers.Factory(
        SqlAlchemyRssArticleReadRepository,
        session=infra.db_session,
    )
    
    rss_article_write_repository = providers.Factory(
        SqlAlchemyRssArticleWriteRepository,
        session=infra.db_session,
    )
    
    # Command Handlers
    def get_create_rss_article_handler(self):
        from src.rss.article.app.commands.create_rss_article.handler import (
            CreateRssArticleHandler,
        )
        return CreateRssArticleHandler(
            rss_article_factory=self.rss_article_factory(),
            rss_article_write_repository=self.rss_article_write_repository(),
            event_bus=self.infra.event_bus,
            logger=self.infra.logger,
        )
```

## Data Models

### RssFeedModel (ORM)

```python
"""ORM model for rss_feeds table."""

from sqlalchemy import Column, String, Boolean, Integer, DateTime
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class RssFeedModel(Base):
    """ORM model for RSS feeds."""
    
    __tablename__ = "rss_feeds"
    
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    url = Column(String, nullable=False, unique=True, index=True)
    description = Column(String, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    fetch_interval_minutes = Column(Integer, nullable=False, default=60)
    last_fetched_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)
```

### RssArticleModel (ORM)

```python
"""ORM model for rss_articles table."""

from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class RssArticleModel(Base):
    """ORM model for RSS articles."""
    
    __tablename__ = "rss_articles"
    
    id = Column(String, primary_key=True)
    feed_id = Column(String, ForeignKey("rss_feeds.id"), nullable=False, index=True)
    title = Column(String, nullable=False)
    url = Column(String, nullable=False, unique=True, index=True)
    content = Column(Text, nullable=True)
    published_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)
```

## Migration Strategy

### Phase 1: Create New Structure

1. Create `src/rss/` directory
2. Create `src/rss/feed/` sub-BC with full structure
3. Create `src/rss/article/` sub-BC with full structure
4. Create `src/rss/shared/` for shared concepts

### Phase 2: Copy and Rename Files

1. Copy `src/source/` → `src/rss/feed/`
2. Copy `src/article/` → `src/rss/article/`
3. Rename all files with "source" → "rss_feed"
4. Rename all files with "article" → "rss_article"

### Phase 3: Rename Classes and Imports

1. Rename `Source` → `RssFeed` in all files
2. Rename `Article` → `RssArticle` in all files
3. Rename `SourceId` → `RssFeedId` in all files
4. Rename `ArticleId` → `RssArticleId` in all files
5. Update all imports to use new paths

### Phase 4: Update Dependencies

1. Update `src/knowledge/` to use `SourceReference`
2. Update `src/rag/` to use new imports
3. Update all tests to use new imports
4. Update containers to use new class names

### Phase 5: Deprecate Old Files

1. Mark old files as DEPRECATED
2. Add migration comments
3. Keep old files temporarily for reference

### Phase 6: Cleanup

1. Run all tests to verify migration
2. Remove deprecated files
3. Update documentation

## Error Handling

### Migration Errors

- **Import errors**: Use `grep` to find all imports and update systematically
- **Test failures**: Fix tests incrementally, one bounded context at a time
- **Container errors**: Verify all factory methods use new class names

### Rollback Strategy

- Keep old files until migration is complete and validated
- Use git branches for safe migration
- Test each phase before proceeding to next

## Testing Strategy

### Unit Tests

- Rename test files to match new class names
- Update test classes to use new names (TestRssFeed, TestRssArticle)
- Update all imports in tests
- Verify all tests pass after each phase

### Integration Tests

- Update integration tests to use new bounded context paths
- Verify database operations work with new table names
- Test cross-BC communication (RssFeed → RssArticle → KnowledgeChunk)

### Property-Based Tests

- Update PBT tests to use new class names
- Verify properties still hold after migration
- Add new properties for SourceReference validation

## Performance Considerations

- Migration should not affect runtime performance
- New structure may improve compile times (better organization)
- Tests should run in same time or faster (better isolation)

## Security Considerations

- No security changes in this migration
- Maintain existing access controls
- Verify no sensitive data exposed in new structure

## Deployment Strategy

- Migration can be done in development first
- No database migration needed (only table renames)
- Deploy to staging for validation
- Deploy to production after full validation

## Monitoring and Observability

- Add logging for migration steps
- Monitor test execution times
- Track import errors during migration
- Verify all bounded contexts compile correctly

## Future Extensibility

### Adding Twitter BC

```
src/twitter/
├── tweet/
│   ├── domain/
│   │   ├── aggregates/
│   │   │   └── tweet.py
│   │   └── value_objects/
│   │       └── tweet_id.py
│   └── container.py
└── account/
    └── ...
```

### Adding PDF BC

```
src/pdf/
├── document/
│   ├── domain/
│   │   ├── aggregates/
│   │   │   └── pdf_document.py
│   │   └── value_objects/
│   │       └── pdf_document_id.py
│   └── container.py
└── library/
    └── ...
```

## References

- **DDD Patterns**: `.kiro/steering/domain-patterns.md`
- **Architecture**: `.kiro/steering/architecture.md`
- **Repository Pattern**: `.kiro/steering/repository-pattern.md`
- **Bounded Contexts**: Eric Evans, Domain-Driven Design
- **Ubiquitous Language**: Vaughn Vernon, Implementing Domain-Driven Design
