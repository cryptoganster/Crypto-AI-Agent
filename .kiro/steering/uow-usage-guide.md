# Guía de Uso del Unit of Work (UoW)

## Ubicación

**UoW Compartido**: `src/shared/kernel/uow.py`

Este UoW es compartido por todos los bounded contexts. NO crear UoWs específicos por bounded context.

## Principio Fundamental

### ❌ NUNCA hacer commit en el Repository

```python
# ❌ INCORRECTO - Repository hace commit
class ArticleWriteRepository:
    async def save(self, article: Article) -> None:
        # ... guardar
        await self._session.commit()  # ❌ NUNCA
```

### ✅ SIEMPRE hacer commit en el Handler usando UoW

```python
# ✅ CORRECTO - Handler hace commit via UoW
class PublishArticleHandler:
    async def handle(self, command):
        async with self._uow:
            article = await self._repo.find_by_id(command.article_id)
            article.publish()
            await self._repo.save(article)
            await self._uow.commit()  # ✅ Commit explícito
```

## Interfaces Disponibles

### IUnitOfWork (Base)

Interface básica para Unit of Work:

```python
from src.shared.kernel.uow import IUnitOfWork

class IUnitOfWork(ABC):
    async def commit(self) -> None:
        """Commit the transaction."""
        pass
    
    async def rollback(self) -> None:
        """Rollback the transaction."""
        pass
    
    async def __aenter__(self) -> "IUnitOfWork":
        """Enter context."""
        pass
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit context."""
        pass
```

### SqlAlchemyUnitOfWork (Implementación)

Implementación concreta para SQLAlchemy:

```python
from src.shared.kernel.uow import SqlAlchemyUnitOfWork

uow = SqlAlchemyUnitOfWork(session, logger)
```

### IUnitOfWorkFactory (Factory)

Factory para crear UoWs:

```python
from src.shared.kernel.uow import IUnitOfWorkFactory, SqlAlchemyUnitOfWorkFactory

factory = SqlAlchemyUnitOfWorkFactory(session_factory, logger)
uow = factory.create()
```

## Uso en Command Handlers

### Patrón Básico

```python
from src.shared.kernel.uow import IUnitOfWork

class PublishArticleHandler:
    def __init__(
        self,
        article_repo: IArticleWriteRepository,
        uow: IUnitOfWork,
        event_bus: IEventBus,
        logger: ILogger,
    ):
        self._repo = article_repo
        self._uow = uow
        self._event_bus = event_bus
        self._logger = logger
    
    async def handle(self, command: PublishArticleCommand) -> PublishArticleResult:
        """Publica un artículo."""
        
        # 1. Usar UoW como context manager
        async with self._uow:
            # 2. Cargar aggregate
            article = await self._repo.find_by_id(command.article_id)
            if not article:
                return PublishArticleResult.failure("Article not found")
            
            # 3. Ejecutar lógica de negocio
            try:
                article.publish()
            except InvalidOperationException as e:
                return PublishArticleResult.failure(str(e))
            
            # 4. Persistir cambios
            await self._repo.save(article)
            
            # 5. Commit explícito
            await self._uow.commit()
        
        # 6. Publicar eventos (FUERA de transacción)
        events = article.get_uncommitted_events()
        await self._event_bus.publish_all(events)
        article.mark_events_as_committed()
        
        return PublishArticleResult.success(article)
```

### Múltiples Agregados en una Transacción

```python
class TransferArticleHandler:
    async def handle(self, command: TransferArticleCommand):
        async with self._uow:
            # Cargar múltiples agregados
            article = await self._article_repo.find_by_id(command.article_id)
            old_source = await self._source_repo.find_by_id(article.source_id)
            new_source = await self._source_repo.find_by_id(command.new_source_id)
            
            # Lógica de negocio
            article.transfer_to_source(command.new_source_id)
            old_source.decrement_article_count()
            new_source.increment_article_count()
            
            # Persistir todos los cambios
            await self._article_repo.save(article)
            await self._source_repo.save(old_source)
            await self._source_repo.save(new_source)
            
            # Commit atómico de todos los cambios
            await self._uow.commit()
        
        # Publicar eventos
        events = article.get_uncommitted_events()
        await self._event_bus.publish_all(events)
        article.mark_events_as_committed()
        
        return TransferArticleResult.success(article)
```

### Manejo de Errores

```python
class UpdateArticleHandler:
    async def handle(self, command: UpdateArticleCommand):
        try:
            async with self._uow:
                article = await self._repo.find_by_id(command.article_id)
                
                # Lógica que puede fallar
                article.update_content(command.content)
                await self._repo.save(article)
                
                # Commit explícito
                await self._uow.commit()
            
            # Publicar eventos
            events = article.get_uncommitted_events()
            await self._event_bus.publish_all(events)
            
            return UpdateArticleResult.success(article)
            
        except InvalidOperationException as e:
            # Rollback automático (no commit)
            self._logger.warning("Invalid operation", error=str(e))
            return UpdateArticleResult.failure(str(e))
        
        except Exception as e:
            # Rollback automático (no commit)
            self._logger.error("Unexpected error", error=str(e))
            return UpdateArticleResult.failure("Internal error")
```

## Dependency Injection

### Registrar en Container

```python
# src/bootstrap/containers/article_container.py

from src.shared.kernel.uow import SqlAlchemyUnitOfWork

class ArticleContainer(containers.DeclarativeContainer):
    
    def get_uow(self) -> IUnitOfWork:
        """Factory para Unit of Work."""
        return SqlAlchemyUnitOfWork(
            session=self.infra.db_session(),
            logger=self.infra.logger,
        )
    
    def get_publish_article_handler(self) -> PublishArticleHandler:
        """Factory para PublishArticleHandler."""
        return PublishArticleHandler(
            article_repo=self.get_article_write_repository(),
            uow=self.get_uow(),  # ← Inyectar UoW
            event_bus=self.infra.event_bus,
            logger=self.infra.logger,
        )
```

### Usar Factory Pattern

```python
# Si necesitas crear múltiples UoWs
from src.shared.kernel.uow import SqlAlchemyUnitOfWorkFactory

class ArticleContainer(containers.DeclarativeContainer):
    
    def get_uow_factory(self) -> IUnitOfWorkFactory:
        """Factory para crear UoWs."""
        return SqlAlchemyUnitOfWorkFactory(
            session_factory=self.infra.db_session_factory,
            logger=self.infra.logger,
        )
    
    def get_handler(self):
        return MyHandler(
            uow_factory=self.get_uow_factory(),
            # ...
        )
```

## Comportamiento del UoW

### Commit Explícito Requerido

```python
# ✅ CORRECTO - Commit explícito
async with uow:
    await repo.save(article)
    await uow.commit()  # ✅ Commit explícito

# ❌ INCORRECTO - Sin commit (rollback automático)
async with uow:
    await repo.save(article)
    # ❌ No commit → rollback automático
```

### Rollback Automático en Excepción

```python
# Rollback automático si hay excepción
async with uow:
    await repo.save(article)
    raise ValueError("Error!")  # Rollback automático
    await uow.commit()  # Nunca se ejecuta
```

### Rollback Automático sin Commit

```python
# Rollback automático si no hay commit
async with uow:
    await repo.save(article)
    # Salir sin commit → rollback automático
```

## Write Repositories (Sin Commit)

Los Write Repositories NUNCA deben hacer commit:

```python
# ✅ CORRECTO - Repository sin commit
class ArticleWriteRepository(IArticleWriteRepository):
    def __init__(self, session: AsyncSession):
        self._session = session
    
    async def save(self, article: Article) -> None:
        """Guarda article sin hacer commit."""
        model = self._mapper.to_model(article)
        self._session.add(model)
        await self._session.flush()  # ✅ Flush, NO commit
    
    async def delete(self, article_id: str) -> None:
        """Elimina article sin hacer commit."""
        stmt = delete(ArticleModel).where(ArticleModel.id == article_id)
        await self._session.execute(stmt)
        await self._session.flush()  # ✅ Flush, NO commit
```

## Testing

### Mock UoW en Tests

```python
import pytest
from unittest.mock import AsyncMock

@pytest.fixture
def mock_uow():
    """Mock para Unit of Work."""
    uow = AsyncMock(spec=IUnitOfWork)
    uow.__aenter__.return_value = uow
    uow.__aexit__.return_value = None
    return uow

async def test_publish_article_commits_transaction(mock_uow):
    """Debería hacer commit de la transacción."""
    # Arrange
    handler = PublishArticleHandler(
        article_repo=mock_repo,
        uow=mock_uow,
        event_bus=mock_event_bus,
        logger=mock_logger,
    )
    
    # Act
    result = await handler.handle(command)
    
    # Assert
    assert result.success
    mock_uow.commit.assert_called_once()
```

### Test de Integración con UoW Real

```python
@pytest.mark.integration
async def test_publish_article_with_real_uow(db_session, logger):
    """Test de integración con UoW real."""
    # Arrange
    uow = SqlAlchemyUnitOfWork(db_session, logger)
    repo = ArticleWriteRepository(db_session)
    handler = PublishArticleHandler(repo, uow, event_bus, logger)
    
    # Act
    result = await handler.handle(command)
    
    # Assert
    assert result.success
    
    # Verificar que se persistió
    article = await repo.find_by_id(command.article_id)
    assert article.status == ArticleStatus.PUBLISHED
```

## Beneficios del UoW Compartido

✅ **Consistencia**: Todas las transacciones se manejan igual
✅ **Sin Duplicación**: Un solo UoW para todo el sistema
✅ **Transacciones Atómicas**: Múltiples agregados en una transacción
✅ **Rollback Seguro**: Rollback automático en caso de error
✅ **Testeable**: Fácil de mockear en tests
✅ **Logging**: Logging consistente de transacciones

## Anti-Patrones a Evitar

### ❌ Commit en Repository

```python
# ❌ NUNCA hacer esto
class ArticleWriteRepository:
    async def save(self, article: Article) -> None:
        self._session.add(model)
        await self._session.commit()  # ❌ NUNCA
```

### ❌ Múltiples UoWs por Bounded Context

```python
# ❌ NO crear UoWs específicos
src/article/infra/persistence/article_uow.py  # ❌
src/source/infra/persistence/source_uow.py    # ❌
src/scraping/infra/persistence/scraping_uow.py # ❌
```

### ❌ Publicar Eventos Dentro de Transacción

```python
# ❌ INCORRECTO - Eventos dentro de transacción
async with uow:
    await repo.save(article)
    await event_bus.publish(events)  # ❌ Dentro de transacción
    await uow.commit()

# ✅ CORRECTO - Eventos fuera de transacción
async with uow:
    await repo.save(article)
    await uow.commit()

# Publicar eventos DESPUÉS del commit
await event_bus.publish(events)  # ✅ Fuera de transacción
```

### ❌ No Hacer Commit

```python
# ❌ INCORRECTO - Sin commit (rollback automático)
async with uow:
    await repo.save(article)
    # ❌ No commit → cambios se pierden
```

## CQRS: Queries vs Commands

### ❌ Queries (Read Side) - NO necesitan UoW

Los Query Handlers son **solo lectura**, NO necesitan UoW:

```python
# ✅ CORRECTO - Query sin UoW
class GetArticleByIdHandler:
    def __init__(
        self,
        read_repo: IArticleReadRepository,  # Solo read repo
        logger: ILogger,
    ):
        self._read_repo = read_repo
        self._logger = logger
    
    async def handle(self, query: GetArticleByIdQuery):
        """Query pura - solo lectura, sin UoW."""
        article_dto = await self._read_repo.find_by_id(query.article_id)
        
        if not article_dto:
            return GetArticleByIdResult.not_found()
        
        return GetArticleByIdResult.success(article_dto)
```

**Razones:**
- ✅ Solo lectura (SELECT)
- ✅ No modifican estado
- ✅ No necesitan commit
- ✅ No necesitan transacciones
- ✅ Mejor performance (sin overhead transaccional)

### ✅ Commands (Write Side) - SÍ necesitan UoW

Los Command Handlers **modifican estado**, SÍ necesitan UoW:

```python
# ✅ CORRECTO - Command con UoW
class ScrapeArticleContentHandler:
    def __init__(
        self,
        read_repo: IArticleReadRepository,
        write_repo: IArticleWriteRepository,
        uow: IUnitOfWork,  # ← UoW necesario
        event_bus: IEventBus,
        logger: ILogger,
    ):
        self._read_repo = read_repo
        self._write_repo = write_repo
        self._uow = uow
        self._event_bus = event_bus
        self._logger = logger
    
    async def handle(self, command: ScrapeArticleContentCommand):
        """Command - modifica estado, necesita UoW."""
        
        async with self._uow:
            article = await self._read_repo.find_by_id(command.article_id)
            article.scrape_content(content)
            await self._write_repo.save(article)
            await self._uow.commit()
        
        events = article.get_uncommitted_events()
        await self._event_bus.publish_all(events)
```

**Razones:**
- ✅ Modifican estado (INSERT/UPDATE/DELETE)
- ✅ Necesitan commit
- ✅ Necesitan transacciones atómicas
- ✅ Necesitan rollback en caso de error
- ✅ Pueden modificar múltiples agregados

## Resumen

- 🎯 Usa el UoW compartido de `src/shared/kernel/uow.py`
- 🔒 Repositories NUNCA hacen commit
- ✅ **Commands** hacen commit explícito via UoW
- ❌ **Queries** NO usan UoW (solo lectura)
- 🔄 Rollback automático si no hay commit o hay excepción
- 📝 Publicar eventos FUERA de transacción
- 🧪 Fácil de mockear en tests

## Referencias

- **Architecture**: `.kiro/steering/architecture.md`
- **Repository Pattern**: `.kiro/steering/repository-pattern.md`
- **Domain Patterns**: `.kiro/steering/domain-patterns.md`
- **Testing Guidelines**: `.kiro/steering/testing-guidelines.md`

---

**Última actualización**: 2024-12-07
