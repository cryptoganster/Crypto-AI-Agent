# Patrón de Repository en Bounded Contexts

## Filosofía

Cada bounded context tiene sus propias interfaces de repositorio separadas en **Read** y **Write** siguiendo el principio CQRS.

## Ubicación

```
src/<bounded-context>/domain/interfaces/repositories/
├── __init__.py
├── <aggregate>_read_repository.py
└── <aggregate>_write_repository.py
```

## Diferencia: Repository vs CQRS Query

### Repository Queries (Operaciones Básicas de DB)

**Ubicación**: `src/<bounded-context>/domain/interfaces/repositories/`

**Características**:
- Operaciones CRUD básicas
- Sin lógica de negocio
- Retornan agregados de dominio
- No requieren handlers
- Métodos: `find_*()`, `count()`, `exists()`

**Ejemplo**:
```python
# src/source/domain/interfaces/repositories/source_read_repository.py

class ISourceReadRepository(ABC):
    """Repository para operaciones básicas de lectura."""
    
    @abstractmethod
    async def find_by_id(self, source_id: UUID) -> Optional[Source]:
        """Busca source por ID."""
        pass
    
    @abstractmethod
    async def find_all(self, limit, offset) -> List[Source]:
        """Obtiene todas las sources."""
        pass
    
    @abstractmethod
    async def count() -> int:
        """Cuenta total de sources."""
        pass
```

### CQRS Queries (Casos de Uso de Lectura)

**Ubicación**: `src/<bounded-context>/app/queries/`

**Características**:
- Casos de uso complejos
- Con lógica de negocio
- Retornan DTOs específicos
- Requieren handlers
- Pueden combinar múltiples agregados

**Ejemplo**:
```python
# src/source/app/queries/get_healthy_sources/query.py

@dataclass(frozen=True)
class GetHealthySourcesQuery:
    """Query para obtener sources saludables."""
    min_success_rate: float = 0.7
    min_fetch_count: int = 10
    order_by: str = "priority"
```

## Patrón Read/Write Repository

### Read Repository

**Propósito**: Operaciones de lectura (queries)

**Métodos típicos**:
```python
class ISourceReadRepository(ABC):
    # Búsqueda por ID
    async def find_by_id(id) -> Optional[Aggregate]
    async def exists(id) -> bool
    
    # Búsqueda por atributos
    async def find_by_url(url) -> Optional[Aggregate]
    async def find_by_name(name) -> List[Aggregate]
    
    # Listado y paginación
    async def find_all(limit, offset) -> List[Aggregate]
    async def find_active(limit, offset) -> List[Aggregate]
    async def find_by_status(status) -> List[Aggregate]
    
    # Conteo
    async def count() -> int
    async def count_active() -> int
    
    # Búsqueda de duplicados
    async def find_duplicates_by_url(url) -> List[Aggregate]
    async def find_similar_by_url(url, threshold) -> List[Aggregate]
```

### Write Repository

**Propósito**: Operaciones de escritura (commands)

**Métodos típicos**:
```python
class ISourceWriteRepository(ABC):
    # Persistencia
    async def save(aggregate: Aggregate) -> None
    
    # Eliminación
    async def delete(id: UUID) -> None
    async def delete_by_url(url: str) -> None
```

## Implementación en Infrastructure

**Ubicación**: `src/infra/persistence/repositories/`

```python
# src/infra/persistence/repositories/source_read_repository.py

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.source.domain.interfaces.repositories import ISourceReadRepository
from src.source.domain.aggregates.source import Source
from src.infra.persistence.models.source_model import SourceModel
from src.infra.persistence.mappers.source_mapper import SourceMapper


class SqlAlchemySourceReadRepository(ISourceReadRepository):
    """Implementación SQLAlchemy de ISourceReadRepository."""
    
    def __init__(self, session: AsyncSession):
        self._session = session
        self._mapper = SourceMapper()
    
    async def find_by_id(self, source_id: UUID) -> Optional[Source]:
        """Busca source por ID."""
        stmt = select(SourceModel).where(SourceModel.id == source_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        
        if model is None:
            return None
        
        return self._mapper.to_domain(model)
    
    async def find_all(
        self,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[Source]:
        """Obtiene todas las sources."""
        stmt = select(SourceModel)
        
        if offset:
            stmt = stmt.offset(offset)
        if limit:
            stmt = stmt.limit(limit)
        
        result = await self._session.execute(stmt)
        models = result.scalars().all()
        
        return [self._mapper.to_domain(m) for m in models]
    
    async def count(self) -> int:
        """Cuenta total de sources."""
        stmt = select(func.count()).select_from(SourceModel)
        result = await self._session.execute(stmt)
        return result.scalar()
```

## Uso en Handlers

### Command Handler (Escritura)

```python
from src.source.domain.interfaces.repositories import (
    ISourceReadRepository,
    ISourceWriteRepository,
)
from src.source.domain.factories import SourceFactory


class CreateSourceHandler:
    def __init__(
        self,
        source_read_repo: ISourceReadRepository,
        source_write_repo: ISourceWriteRepository,
        source_factory: SourceFactory,
        logger: ILogger,
    ):
        self._read_repo = source_read_repo
        self._write_repo = source_write_repo
        self._factory = source_factory
        self._logger = logger
    
    async def handle(self, command: CreateSourceCommand) -> CreateSourceResult:
        # 1. Verificar duplicados (read)
        duplicates = await self._read_repo.find_duplicates_by_url(command.url)
        if duplicates:
            return CreateSourceResult.failure("Source already exists")
        
        # 2. Crear source usando factory
        source = self._factory.create_source(
            name=command.name,
            url=command.url,
        )
        
        # 3. Guardar (write)
        await self._write_repo.save(source)
        
        return CreateSourceResult.success(source)
```

### Query Handler (Lectura Compleja)

```python
from src.source.domain.interfaces.repositories import ISourceReadRepository
from src.source.domain.services.health import SourceHealthService


class GetHealthySourcesHandler:
    def __init__(
        self,
        source_repository: ISourceReadRepository,
        health_service: SourceHealthService,
        logger: ILogger,
    ):
        self._repository = source_repository
        self._health_service = health_service
        self._logger = logger
    
    async def handle(
        self,
        query: GetHealthySourcesQuery
    ) -> GetHealthySourcesResult:
        # 1. Obtener sources activas (repository)
        sources = await self._repository.find_active()
        
        # 2. Filtrar por salud (domain service)
        healthy_sources = []
        for source in sources:
            health = self._health_service.evaluate_health(source)
            if health.success_rate >= query.min_success_rate:
                healthy_sources.append(source)
        
        # 3. Ordenar y paginar
        healthy_sources.sort(key=lambda s: s.priority, reverse=True)
        
        return GetHealthySourcesResult.success(healthy_sources)
```

## Dependency Injection

```python
# src/bootstrap/containers/source_container.py

class SourceContainer(containers.DeclarativeContainer):
    
    # Repositories
    def get_source_read_repository(self) -> ISourceReadRepository:
        return SqlAlchemySourceReadRepository(
            session=self.infra.db_session,
        )
    
    def get_source_write_repository(self) -> ISourceWriteRepository:
        return SqlAlchemySourceWriteRepository(
            session=self.infra.db_session,
        )
    
    # Handlers
    def get_create_source_handler(self) -> CreateSourceHandler:
        return CreateSourceHandler(
            source_read_repo=self.get_source_read_repository(),
            source_write_repo=self.get_source_write_repository(),
            source_factory=self.get_source_factory(),
            logger=self.infra.logger,
        )
```

## Comparación

| Aspecto | Repository Query | CQRS Query |
|---------|-----------------|------------|
| **Ubicación** | `src/<bc>/domain/interfaces/repositories/` | `src/<bc>/app/queries/` |
| **Propósito** | Operaciones básicas de DB | Casos de uso de lectura |
| **Complejidad** | Simple (CRUD) | Compleja (lógica de negocio) |
| **Lógica** | Sin lógica de negocio | Con lógica de negocio |
| **Handler** | No requiere | Requiere handler |
| **Retorno** | Agregados | DTOs específicos |

## Beneficios

✅ **Separación clara**: Read vs Write
✅ **CQRS**: Optimización independiente de lectura y escritura
✅ **Cohesión**: Repositories en bounded context
✅ **Testabilidad**: Fácil de mockear
✅ **Mantenibilidad**: Código organizado y predecible

## Anti-Patrones

### ❌ Repository con Lógica de Negocio

```python
# ❌ INCORRECTO
class SourceReadRepository:
    async def find_healthy_sources(self, min_rate: float):
        sources = await self.find_all()
        # Lógica de negocio en repository
        return [s for s in sources if s.calculate_health() > min_rate]
```

**Problema**: Repository tiene lógica de negocio.

**Solución**: Mover a CQRS Query Handler.

### ❌ Queries Básicas en app/queries/

```python
# ❌ INCORRECTO - Query básica en app/queries/
class GetSourceByIdQuery:
    source_id: UUID

class GetSourceByIdHandler:
    async def handle(self, query):
        return await self._repository.find_by_id(query.source_id)
```

**Problema**: Query trivial que solo delega al repository.

**Solución**: Usar repository directamente.

## Referencias

- **Architecture**: `.kiro/steering/architecture.md`
- **Domain Patterns**: `.kiro/steering/domain-patterns.md`
- **Database Patterns**: `.kiro/steering/database-patterns.md`
- **CQRS**: Command Query Responsibility Segregation pattern

---

**Última actualización**: 2024-12-03
