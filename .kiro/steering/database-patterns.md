# Patrones de Base de Datos

## ORM y Persistencia

Este proyecto usa **SQLAlchemy 2.0** con async support para persistencia.

## Estructura

### Modelos ORM

**Ubicación**: `src/infra/persistence/models/`

Los modelos ORM son representaciones de tablas de base de datos, separados del dominio.

**Ejemplo**:
```python
from sqlalchemy import Column, String, DateTime, Float, Enum
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

class ArticleModel(Base):
    """ORM model for articles table."""
    
    __tablename__ = "articles"
    
    id = Column(String, primary_key=True)
    source_id = Column(String, nullable=False, index=True)
    title = Column(String, nullable=False)
    url = Column(String, nullable=False, unique=True, index=True)
    content = Column(String, nullable=False)
    published_at = Column(DateTime, nullable=False)
    quality_score = Column(Float, nullable=True)
    status = Column(Enum(ArticleStatus), nullable=False, default=ArticleStatus.DRAFT)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
```

### Mappers

**Ubicación**: `src/infra/persistence/mappers/`

Los mappers convierten entre modelos ORM y agregados de dominio.

**Ejemplo**:
```python
from src.domain.aggregates.article import Article, ArticleStatus
from src.infra.persistence.models.article_model import ArticleModel

class ArticleMapper:
    """Mapper between Article domain model and ArticleModel ORM."""
    
    @staticmethod
    def to_domain(model: ArticleModel) -> Article:
        """Convert ORM model to domain aggregate."""
        return Article(
            id=model.id,
            source_id=model.source_id,
            title=model.title,
            url=model.url,
            content=model.content,
            published_at=model.published_at,
            quality_score=model.quality_score,
            status=ArticleStatus(model.status)
        )
    
    @staticmethod
    def to_model(article: Article) -> ArticleModel:
        """Convert domain aggregate to ORM model."""
        return ArticleModel(
            id=article.id,
            source_id=article.source_id,
            title=article.title,
            url=article.url,
            content=article.content,
            published_at=article.published_at,
            quality_score=article.quality_score,
            status=article.status.value
        )
    
    @staticmethod
    def update_model(model: ArticleModel, article: Article) -> None:
        """Update existing ORM model with domain aggregate data."""
        model.title = article.title
        model.content = article.content
        model.quality_score = article.quality_score
        model.status = article.status.value
        model.updated_at = datetime.utcnow()
```

### Repositories

**Ubicación**: `src/infra/persistence/repositories/`

Implementaciones concretas de las interfaces de repositorio del dominio.

**Ejemplo**:
```python
from typing import Optional
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.aggregates.article import Article
from src.domain.interfaces.repositories.article_write_repository import (
    IArticleRepository
)
from src.infra.persistence.models.article_model import ArticleModel
from src.infra.persistence.mappers.article_mapper import ArticleMapper

class SqlAlchemyArticleRepository(IArticleRepository):
    """SQLAlchemy implementation of article repository."""
    
    def __init__(self, session: AsyncSession):
        self._session = session
        self._mapper = ArticleMapper()
    
    async def save(self, article: Article) -> None:
        """Save an article."""
        # Check if exists
        stmt = select(ArticleModel).where(ArticleModel.id == article.id)
        result = await self._session.execute(stmt)
        existing = result.scalar_one_or_none()
        
        if existing:
            # Update existing
            self._mapper.update_model(existing, article)
        else:
            # Create new
            model = self._mapper.to_model(article)
            self._session.add(model)
        
        await self._session.flush()
    
    async def find_by_id(self, article_id: str) -> Optional[Article]:
        """Find article by ID."""
        stmt = select(ArticleModel).where(ArticleModel.id == article_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        
        if model is None:
            return None
        
        return self._mapper.to_domain(model)
    
    async def find_by_url(self, url: str) -> Optional[Article]:
        """Find article by URL."""
        stmt = select(ArticleModel).where(ArticleModel.url == url)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        
        if model is None:
            return None
        
        return self._mapper.to_domain(model)
    
    async def delete(self, article_id: str) -> None:
        """Delete an article."""
        stmt = delete(ArticleModel).where(ArticleModel.id == article_id)
        await self._session.execute(stmt)
        await self._session.flush()
```

## Query Adapters (CQRS Read Side)

**Ubicación**: `src/infra/persistence/query_adapters/`

Para queries de lectura optimizadas, separadas de los repositorios de escritura.

**Ejemplo**:
```python
from typing import Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.interfaces.queries.articles.get_article_query import (
    IGetArticleQuery
)
from src.presentation.schemas.rss.articles.article_response import ArticleResponse

class GetArticleQueryAdapter(IGetArticleQuery):
    """Query adapter for getting article details."""
    
    def __init__(self, session: AsyncSession):
        self._session = session
    
    async def execute(self, article_id: str) -> Optional[ArticleResponse]:
        """Execute query to get article."""
        stmt = select(ArticleModel).where(ArticleModel.id == article_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        
        if model is None:
            return None
        
        return ArticleResponse(
            id=model.id,
            source_id=model.source_id,
            title=model.title,
            url=model.url,
            content=model.content,
            published_at=model.published_at,
            quality_score=model.quality_score,
            status=model.status,
            created_at=model.created_at
        )

class ListArticlesQueryAdapter:
    """Query adapter for listing articles with pagination."""
    
    def __init__(self, session: AsyncSession):
        self._session = session
    
    async def execute(
        self,
        source_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 20,
        offset: int = 0
    ) -> tuple[list[ArticleResponse], int]:
        """Execute query to list articles."""
        # Build query
        stmt = select(ArticleModel)
        
        if source_id:
            stmt = stmt.where(ArticleModel.source_id == source_id)
        
        if status:
            stmt = stmt.where(ArticleModel.status == status)
        
        # Count total
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_result = await self._session.execute(count_stmt)
        total = total_result.scalar()
        
        # Apply pagination
        stmt = stmt.limit(limit).offset(offset)
        stmt = stmt.order_by(ArticleModel.created_at.desc())
        
        # Execute
        result = await self._session.execute(stmt)
        models = result.scalars().all()
        
        # Map to response
        articles = [
            ArticleResponse(
                id=m.id,
                source_id=m.source_id,
                title=m.title,
                url=m.url,
                content=m.content,
                published_at=m.published_at,
                quality_score=m.quality_score,
                status=m.status,
                created_at=m.created_at
            )
            for m in models
        ]
        
        return articles, total
```

## Session Management

**Ubicación**: `src/infra/persistence/session_manager.py`

```python
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker
)

class SessionManager:
    """Manages database sessions."""
    
    def __init__(self, database_url: str):
        self._engine = create_async_engine(
            database_url,
            echo=False,
            pool_pre_ping=True,
            pool_size=10,
            max_overflow=20
        )
        self._session_factory = async_sessionmaker(
            self._engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
    
    @asynccontextmanager
    async def session(self):
        """Create a new session."""
        async with self._session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
    
    async def close(self):
        """Close the engine."""
        await self._engine.dispose()
```

## Unit of Work Pattern

**Interface**: `src/shared/kernel/uow.py`
**Implementación**: `src/infra/persistence/uow.py`

```python
# Interface (Shared Kernel)
from src.shared.kernel.uow import IUnitOfWork

# Implementación (Infrastructure)
from src.infra.persistence.uow import SqlAlchemyUnitOfWork

# Uso en Command Handler
class PublishArticleHandler:
    def __init__(
        self,
        session_factory,
        article_repository,
        event_bus: IEventBus,
        logger: ILogger,
    ):
        self._session_factory = session_factory
        self._article_repository = article_repository
        self._event_bus = event_bus
        self._logger = logger
    
    async def handle(self, command):
        # Crear UoW
        session = self._session_factory()
        uow = SqlAlchemyUnitOfWork(session, self._logger)
        
        async with uow:
            # Cargar aggregate
            article = await self._article_repository.find_by_id(command.article_id)
            
            # Ejecutar lógica de negocio
            article.publish()
            
            # Persistir
            await self._article_repository.save(article)
            
            # Commit explícito
            await uow.commit()
        
        # Publicar eventos (fuera de transacción)
        events = article.get_uncommitted_events()
        await self._event_bus.publish_all(events)
        
        return PublishArticleResult.success(article)
```

**Ver ejemplos completos en**: `src/infra/persistence/sqlalchemy_uow_example.py`

## Migrations con Alembic

### Crear Migración

```bash
# Auto-generate migration from models
alembic revision --autogenerate -m "Add articles table"

# Create empty migration
alembic revision -m "Custom migration"
```

### Estructura de Migración

```python
"""Add articles table

Revision ID: abc123
Revises: 
Create Date: 2024-01-01 12:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = 'abc123'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    """Upgrade database schema."""
    op.create_table(
        'articles',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('source_id', sa.String(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('url', sa.String(), nullable=False),
        sa.Column('content', sa.String(), nullable=False),
        sa.Column('published_at', sa.DateTime(), nullable=False),
        sa.Column('quality_score', sa.Float(), nullable=True),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_articles_source_id', 'articles', ['source_id'])
    op.create_index('ix_articles_url', 'articles', ['url'], unique=True)

def downgrade() -> None:
    """Downgrade database schema."""
    op.drop_index('ix_articles_url', table_name='articles')
    op.drop_index('ix_articles_source_id', table_name='articles')
    op.drop_table('articles')
```

## Best Practices

### 1. Separación de Concerns
- Modelos ORM != Agregados de Dominio
- Usar mappers para conversión
- Mantener lógica de negocio en el dominio

### 2. Async/Await
```python
# ✅ Correcto
async def save_article(article: Article):
    async with session_manager.session() as session:
        repo = SqlAlchemyArticleRepository(session)
        await repo.save(article)

# ❌ Incorrecto - Bloquear event loop
def save_article(article: Article):
    session = Session()
    repo.save(article)
    session.commit()
```

### 3. Transacciones
```python
# ✅ Correcto - Usar context manager
async with session_manager.session() as session:
    repo = SqlAlchemyArticleRepository(session)
    await repo.save(article)
    # Auto-commit on success, rollback on exception

# ❌ Incorrecto - Manual commit sin error handling
session = await session_factory()
await repo.save(article)
await session.commit()
```

### 4. Queries Eficientes
```python
# ✅ Correcto - Eager loading
stmt = select(ArticleModel).options(
    selectinload(ArticleModel.source)
)

# ✅ Correcto - Projection para queries de lectura
stmt = select(
    ArticleModel.id,
    ArticleModel.title,
    ArticleModel.published_at
)

# ❌ Incorrecto - N+1 queries
articles = await session.execute(select(ArticleModel))
for article in articles:
    source = await session.execute(
        select(SourceModel).where(SourceModel.id == article.source_id)
    )
```

### 5. Indexes
```python
# Crear índices para queries frecuentes
class ArticleModel(Base):
    __tablename__ = "articles"
    
    id = Column(String, primary_key=True)
    source_id = Column(String, nullable=False, index=True)  # Index
    url = Column(String, nullable=False, unique=True, index=True)  # Unique index
    status = Column(String, nullable=False, index=True)  # Index
    
    # Composite index
    __table_args__ = (
        Index('ix_articles_source_status', 'source_id', 'status'),
    )
```

### 6. Connection Pooling
```python
# Configurar pool apropiadamente
engine = create_async_engine(
    database_url,
    pool_size=10,        # Connections en el pool
    max_overflow=20,     # Connections adicionales
    pool_pre_ping=True,  # Verificar conexiones
    pool_recycle=3600    # Reciclar cada hora
)
```
