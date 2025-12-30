# Arquitectura del Proyecto

## Principios Arquitectónicos

Este proyecto implementa **Clean Architecture** con **Domain-Driven Design (DDD)** y **CQRS** (Command Query Responsibility Segregation).

## Estructura de Capas

### 1. Domain Layer (`src/domain/`)
- **Propósito**: Lógica de negocio pura, independiente de frameworks
- **Contenido**:
  - `aggregates/`: Raíces de agregados (Article, Source, FetchSession)
  - `entities/`: Entidades del dominio
  - `value_objects/`: Objetos de valor inmutables
  - `events/`: Eventos de dominio
  - `services/`: Servicios de dominio
  - `factories/`: Factories para crear agregados
  - `interfaces/`: Interfaces para repositorios y servicios externos

**Reglas**:
- No debe tener dependencias de infraestructura
- Solo lógica de negocio pura
- Inmutabilidad en value objects
- Eventos de dominio para comunicación

### 2. Application Layer (`src/<bounded-context>/app/`)
- **Propósito**: Casos de uso y orquestación
- **Contenido**:
  - `commands/`: Command Handlers CQRS (escritura, simples)
  - `queries/`: Query Handlers CQRS (lectura pura)
  - `process_managers/`: Process Managers (orquestación event-driven)
  - `event_handlers/`: Manejadores de eventos

**Reglas**:
- Implementa patrón Command/Handler
- Cada comando tiene su handler (simple: 1 agregado, 1 operación)
- Usa mediator para desacoplar
- **Process Managers** para orquestación compleja (NO en handlers)
- **Mappers locales**: Cada comando/query que necesite serialización tiene su propio `mapper.py`

### 3. Infrastructure Layer (`src/infra/`)
- **Propósito**: Implementaciones técnicas
- **Contenido**:
  - `persistence/`: Repositorios, mappers, modelos ORM
  - `external/`: Adaptadores para servicios externos
  - `events/`: Event bus implementation
  - `scheduling/`: Jobs y schedulers
  - `logging/`: Logging service

**Reglas**:
- Implementa interfaces del dominio
- Maneja detalles técnicos (DB, HTTP, etc.)
- Usa mappers para convertir entre domain y persistence

### 4. Presentation Layer (`src/presentation/`)
- **Propósito**: API REST con FastAPI
- **Contenido**:
  - `routers/`: Endpoints REST
  - `schemas/`: Pydantic schemas para request/response
  - `middleware/`: Middleware HTTP

**Reglas**:
- Solo validación y serialización
- Delega lógica a application layer
- Usa dependency injection

## Patrones de Diseño

### Command Pattern
```python
# Estructura de comando
class MyCommand:
    def __init__(self, param: str):
        self.param = param

class MyCommandHandler:
    async def handle(self, command: MyCommand) -> MyResult:
        # Lógica del caso de uso
        pass
```

### Repository Pattern
```python
# Interface en domain
class IArticleRepository(Protocol):
    async def save(self, article: Article) -> None:
        pass
    
    async def find_by_id(self, id: str) -> Optional[Article]:
        pass

# Implementación en infrastructure
class SqlAlchemyArticleRepository(IArticleRepository):
    # Implementación con SQLAlchemy
    pass
```

### Aggregate Root Pattern

Los Aggregate Roots son la raíz de un cluster de objetos de dominio que se tratan como una unidad.

**Interface Base**: `IAggregateRoot`

**Responsabilidades**:
- Mantener lista de eventos de dominio pendientes
- Proporcionar acceso a eventos no confirmados
- Marcar eventos como confirmados después de publicación

**Métodos Esenciales**:
```python
from abc import ABC, abstractmethod
from typing import Sequence
from src.domain.shared.interfaces.core.domain_event import IDomainEvent

class IAggregateRoot(ABC):
    """Interface base para Aggregate Roots."""
    
    @property
    @abstractmethod
    def domain_events(self) -> Sequence[IDomainEvent]:
        """Lista de eventos de dominio pendientes."""
        pass
    
    @abstractmethod
    def get_uncommitted_events(self) -> Sequence[IDomainEvent]:
        """Obtiene eventos no confirmados."""
        pass
    
    @abstractmethod
    def mark_events_as_committed(self) -> None:
        """Marca eventos como confirmados."""
        pass
    
    # Métodos de conveniencia con implementación por defecto
    def has_uncommitted_events(self) -> bool:
        """Indica si hay eventos pendientes."""
        return len(self.get_uncommitted_events()) > 0
    
    def get_event_count(self) -> int:
        """Obtiene el número de eventos pendientes."""
        return len(self.get_uncommitted_events())
```

**Lo que NO incluye IAggregateRoot**:
- ❌ Event Sourcing (load_from_history, replay_events)
- ❌ Optimistic Locking (version, increment_version)
- ❌ Snapshots (create_snapshot, load_from_snapshot)

Estas funcionalidades pueden agregarse en el futuro si se necesitan, pero actualmente el proyecto NO implementa Event Sourcing. Los eventos se publican vía event bus para comunicación entre bounded contexts, no se persisten para reconstruir estado.

**Implementación en Agregados**:
```python
from dataclasses import dataclass, field
from typing import List, Sequence

@dataclass
class Article(IAggregateRoot):
    """Article aggregate root."""
    
    id: str
    title: str
    content: str
    # ... otros campos
    
    _domain_events: List[IDomainEvent] = field(default_factory=list)
    _uncommitted_events: List[IDomainEvent] = field(default_factory=list)
    
    @property
    def domain_events(self) -> Sequence[IDomainEvent]:
        return tuple(self._domain_events)
    
    def get_uncommitted_events(self) -> Sequence[IDomainEvent]:
        return tuple(self._uncommitted_events)
    
    def mark_events_as_committed(self) -> None:
        self._uncommitted_events.clear()
    
    def publish(self) -> None:
        """Lógica de negocio que genera eventos."""
        # Validaciones
        if self.quality_score < 0.5:
            raise InvalidOperationException("Quality too low")
        
        # Cambio de estado
        self.status = ArticleStatus.PUBLISHED
        
        # Generar evento
        event = ArticlePublished(article_id=self.id)
        self._domain_events.append(event)
        self._uncommitted_events.append(event)
```

### Factory Pattern

Las Factories encapsulan la lógica compleja de creación de aggregates, separando la responsabilidad de creación de la lógica de negocio.

**Ubicación**: `src/domain/factories/`

**Principio**: Un aggregate NO debe crearse a sí mismo. La creación compleja (validación, limpieza, normalización) es responsabilidad de una Factory.

#### ArticleFactory

La `ArticleFactory` es el único punto de entrada para crear instancias de `Article`.

**Responsabilidades**:
- Validar datos de entrada antes de crear el aggregate
- Limpiar y normalizar datos (títulos, URLs, contenido)
- Crear Value Objects validados
- Instanciar Article usando constructor simple
- Emitir evento ArticleCreated
- Aplicar metadatos RSS opcionales
- Evaluar calidad básica del contenido

**Interface Pública**:

```python
class ArticleFactory:
    """Factory para crear Article aggregates con validaciones."""
    
    def create_article(
        self,
        title: str,
        url: str,
        source_id: SourceId,
        content: Optional[str] = None,
        article_id: Optional[ArticleId] = None,
        thumbnail_url: Optional[str] = None,
        guid: Optional[str] = None,
        published_at: Optional[datetime] = None,
        description: Optional[str] = None,
        **metadata,
    ) -> Article:
        """Crea Article con validaciones y limpieza."""
        
    def create_from_feed_item(
        self,
        feed_item: FeedItem,
        source_id: SourceId,
        quality_assessment: bool = True,
    ) -> Article:
        """Crea Article desde RSS feed item."""
        
    def validate_article_creation_data(
        self,
        title: str,
        url: str,
        source_id: str,
        **kwargs
    ) -> ValidationResult:
        """Valida datos antes de crear (opcional)."""
```

**Flujo de Creación**:

```
1. Command Handler recibe CreateArticleCommand
   ↓
2. Handler inyecta ArticleFactory (DI)
   ↓
3. Factory valida datos de entrada
   ├─ Si inválido → lanza ValueError con detalles
   └─ Si válido → continúa
   ↓
4. Factory limpia y normaliza datos
   ├─ Limpia título (remueve prefijos RSS)
   ├─ Normaliza URL (lowercase, sin fragments)
   └─ Limpia contenido (espacios, párrafos)
   ↓
5. Factory crea Value Objects
   ├─ ArticleTitle(clean_title)
   ├─ ArticleUrl(normalized_url)
   └─ ArticleContent.create(clean_content)
   ↓
6. Factory llama constructor simple de Article
   article = Article(title_vo, url_vo, source_id, ...)
   ↓
7. Factory emite ArticleCreated event
   article._add_domain_event(ArticleCreated(...))
   ↓
8. Factory aplica metadatos RSS (si existen)
   ├─ article.set_rss_guid(guid)
   ├─ article.set_pub_date(pub_date)
   └─ article.set_description(description)
   ↓
9. Factory retorna Article al Handler
   ↓
10. Handler persiste Article
    await repository.save(article)
    ↓
11. Handler publica eventos
    await event_bus.publish(article.get_uncommitted_events())
    ↓
12. Handler marca eventos como committed
    article.mark_events_as_committed()
```

**Ejemplo de uso en Handler**:

```python
from src.domain.factories.article_factory import ArticleFactory

class CreateArticleHandler:
    """Handler para crear nuevos Articles."""
    
    def __init__(
        self,
        article_factory: ArticleFactory,
        article_repository: IArticleWriteRepository,
        event_bus: IEventBus,
    ):
        self._factory = article_factory
        self._repository = article_repository
        self._event_bus = event_bus
    
    async def handle(self, command: CreateArticleCommand) -> CreateArticleResult:
        """Crea Article usando Factory."""
        
        # 1. Usar Factory para crear (valida, limpia, crea)
        try:
            article = self._factory.create_article(
                title=command.title,
                url=command.url,
                source_id=command.source_id,
                content=command.content,
            )
        except ValueError as e:
            return CreateArticleResult.failure(str(e))
        
        # 2. Persistir aggregate
        await self._repository.save(article)
        
        # 3. Publicar eventos
        events = article.get_uncommitted_events()
        await self._event_bus.publish_all(events)
        
        # 4. Marcar eventos como committed
        article.mark_events_as_committed()
        
        # 5. Retornar resultado
        return CreateArticleResult.success(article)
```

**Constructor de Article**:

El constructor de `Article` es simple y solo acepta Value Objects ya validados:

```python
# ✅ CORRECTO - Usar ArticleFactory
article = factory.create_article(title="...", url="...", source_id=source_id)

# ❌ INCORRECTO - No instanciar Article directamente con strings
article = Article(title="...", url="...", source_id="...")  # TypeError

# ✅ CORRECTO - Constructor solo acepta Value Objects
article = Article(
    title=ArticleTitle("..."),
    url=ArticleUrl("..."),
    source_id=SourceId("...")
)
```

**Beneficios**:
- 🎯 Separación clara de responsabilidades (Factory crea, Aggregate maneja negocio)
- 🔒 Validaciones centralizadas y consistentes
- 🧹 Limpieza de datos automática
- 📝 Código más mantenible y testeable
- ✨ Fácil agregar nuevas formas de creación

**Diagrama de Componentes**:

```
┌─────────────────────────────────────────────────────────┐
│              Application Layer (Handlers)                │
│                                                          │
│  ✅ Siempre usa ArticleFactory                          │
│  ✅ Patrón claro y consistente                          │
└─────────────────────────────────────────────────────────┘
                          ↓
              ┌──────────────────────┐
              │   ArticleFactory     │
              │    (Domain Layer)    │
              │                      │
              │ RESPONSABILIDADES:   │
              │ - Validación         │
              │ - Limpieza           │
              │ - Normalización      │
              │ - RSS parsing        │
              │ - Creación           │
              │ - Emitir eventos     │
              └──────────────────────┘
                          ↓
              ┌──────────────────────┐
              │  Article Aggregate   │
              │    (Domain Layer)    │
              │                      │
              │ ENFOCADO:            │
              │ - Lógica negocio     │
              │ - Invariantes        │
              │ - Eventos dominio    │
              │ - Comportamiento     │
              └──────────────────────┘
```

### Event-Driven Architecture
```python
# Eventos de dominio
class ArticleCreated(DomainEvent):
    article_id: str
    timestamp: datetime

# Event handlers
class OnArticleCreated:
    async def handle(self, event: ArticleCreated) -> None:
        # Efectos secundarios
        pass
```

## Dependency Injection

Usa `dependency-injector` para IoC:

```python
# En bootstrap/containers/
class ApplicationContainer(containers.DeclarativeContainer):
    config = providers.Configuration()
    
    # Repositories
    article_repository = providers.Singleton(
        SqlAlchemyArticleRepository,
        session_factory=infrastructure.session_factory
    )
    
    # Services
    article_service = providers.Factory(
        ArticleService,
        repository=article_repository
    )
```

## Testing Strategy

### Unit Tests
- Testear lógica de dominio aislada
- Mock dependencies
- Ubicación: `tests/unit/domain/`

### Integration Tests
- Testear integración con DB, APIs externas
- Usar test database
- Ubicación: `tests/integration/`

### E2E Tests
- Testear flujos completos via API
- Ubicación: `tests/e2e/`

## Convenciones de Naming

- **Aggregates**: Sustantivos en singular (Article, Source)
- **Commands**: Verbos imperativos (CreateArticle, UpdateSource)
- **Events**: Pasado (ArticleCreated, SourceUpdated)
- **Handlers**: Sufijo Handler (CreateArticleHandler)
- **Repositories**: Sufijo Repository (ArticleRepository)
- **Services**: Sufijo Service (ArticleService)
- **Mappers**: Sufijo Mapper (UpdateSourceMapper, FetchFromSourcesMapper)

## Mapper Pattern (Application Layer)

### Principio: Mapper por Caso de Uso

Cada comando o query que necesite serializar agregados de dominio a DTOs debe tener su propio mapper local.

**Ubicación**: `src/app/commands/<feature>/<use-case>/mapper.py`

**Ejemplo**:
```
src/app/commands/sources/update_source/
├── command.py
├── handler.py
├── mapper.py          # ← Mapper específico del caso de uso
├── result.py
└── validator.py
```

### Estructura de un Mapper

```python
"""Mapper para [UseCase] command."""

from typing import Dict, Any
from src.domain.aggregates.article import Article


class UpdateSourceMapper:
    """
    Mapper específico para UpdateSource command.
    
    Serializa Source aggregates a DTOs para UpdateSourceResult.
    
    Responsabilidades:
    - Serializar agregados de dominio a DTOs
    - Convertir Value Objects a primitivos
    - NO contiene lógica de negocio
    """
    
    @staticmethod
    def source_to_summary(source: Source) -> Dict[str, Any]:
        """
        Serializa Source a DTO resumido.
        
        Args:
            source: Source aggregate del dominio
            
        Returns:
            Dict con datos resumidos del source
        """
        return {
            "id": str(source.id),
            "name": str(source.name),
            "url": str(source.url),
            "status": str(source.status),
            "is_active": source.is_active,
            "updated_at": source.updated_at.isoformat(),
        }
```

### Reglas para Mappers

1. **Un mapper por caso de uso**: No compartir mappers entre casos de uso
2. **Métodos estáticos**: Usar `@staticmethod` para métodos de serialización
3. **Sin lógica de negocio**: Solo transformación de datos
4. **Conversión a primitivos**: Convertir Value Objects a strings, ints, floats, etc.
5. **Docstrings completos**: Documentar propósito y uso de cada método
6. **Type hints**: Siempre usar type hints en parámetros y retorno

### Cuándo Crear un Mapper

Crear un mapper local cuando:
- El handler necesita serializar agregados para el Result Object
- El query adapter necesita transformar datos para DTOs de respuesta
- Se requiere conversión de Value Objects a primitivos

**NO crear mapper cuando**:
- Solo se pasan agregados sin serializar
- La conversión es trivial (un solo campo)
- El caso de uso no retorna datos serializados

### Testing de Mappers

Cada mapper debe tener su archivo de tests:

**Ubicación**: `tests/unit/app/commands/<feature>/<use-case>/test_<use_case>_mapper.py`

**Tests mínimos**:
```python
class TestUpdateSourceMapper:
    def test_serializes_correctly(self):
        """Debería serializar correctamente."""
        pass
    
    def test_handles_none_values(self):
        """Debería manejar valores None."""
        pass
    
    def test_converts_value_objects_to_primitives(self):
        """Debería convertir Value Objects a primitivos."""
        pass
    
    def test_includes_all_required_fields(self):
        """Debería incluir todos los campos requeridos."""
        pass
    
    def test_is_static_method(self):
        """Debería ser método estático."""
        pass
```

### Beneficios del Patrón

✅ **Alta cohesión**: Mapper vive junto al caso de uso que lo usa
✅ **Bajo acoplamiento**: No hay dependencias entre casos de uso
✅ **Single Responsibility**: Cada mapper tiene una sola responsabilidad
✅ **Fácil de testear**: Tests aislados y enfocados
✅ **Fácil de mantener**: Cambios en un caso de uso no afectan otros
✅ **Clean Architecture**: Application Layer no hace serialización directa


## Process Managers (CQRS Estricto)

### Ubicación

```
src/<bounded-context>/app/process_managers/
```

### Principios (Greg Young, Vaughn Vernon, Udi Dahan)

Los Process Managers orquestan flujos de negocio complejos de forma event-driven.

**Lo que SÍ hacen**:
- ✅ Escuchar Domain Events
- ✅ Emitir Commands al bus
- ✅ Mantener estado del proceso
- ✅ Coordinar flujos multi-paso

**Lo que NO hacen**:
- ❌ Queries directas a repositorios
- ❌ Llamadas directas a handlers
- ❌ Lógica de negocio (eso está en Domain)
- ❌ Persistencia directa

### Diferencia: Command Handler vs Process Manager

| Aspecto | Command Handler | Process Manager |
|---------|-----------------|-----------------|
| **Propósito** | 1 operación simple | Orquestación compleja |
| **Agregados** | 1 agregado | Múltiples agregados |
| **Queries** | NO | NO (usa eventos) |
| **Emite comandos** | NO | SÍ |
| **Escucha eventos** | NO | SÍ |
| **Estado** | Sin estado | Mantiene estado del proceso |

### Estructura

```
src/scraping/app/
├── commands/
│   └── scrape_source/              # Handler simple (1 source)
├── queries/
│   └── get_active_sources/         # Query pura
└── process_managers/
    └── scraping_sources_pipeline_manager.py  # Orquestación
```

### Ejemplo

```python
class ScrapingSourcesPipelineManager:
    """
    Process Manager para el pipeline de scraping.
    
    Escucha Domain Events y emite Commands al bus.
    NO hace queries directamente.
    NO llama handlers directamente.
    """
    
    def __init__(self, command_bus: IMediator, logger: ILogger):
        self._command_bus = command_bus
        self._logger = logger
        self._active_pipelines: Dict[str, PipelineState] = {}
    
    async def on_scraping_pipeline_requested(
        self,
        pipeline_id: str,
        source_ids: List[str],
    ) -> None:
        """Reacciona al inicio del pipeline."""
        state = PipelineState(pipeline_id, source_ids)
        self._active_pipelines[pipeline_id] = state
        
        # Emitir comando para cada source
        for source_id in source_ids:
            await self._command_bus.send(
                ScrapeSourceCommand(source_id=source_id, pipeline_id=pipeline_id)
            )
    
    async def on_source_scraped(
        self,
        pipeline_id: str,
        source_id: str,
        success: bool,
    ) -> None:
        """Reacciona cuando una source termina."""
        state = self._active_pipelines.get(pipeline_id)
        
        if success:
            state.completed_sources.add(source_id)
        else:
            state.failed_sources.add(source_id)
        
        if state.is_complete:
            await self._handle_pipeline_completed(pipeline_id)
```

### Flujo Event-Driven

```
API/CLI → StartPipelineCommand
              ↓
         Command Handler (simple)
              ↓
         Emite: PipelineStarted
              ↓ (Event Bus)
         Process Manager
              ↓
         Emite: ScrapeSourceCommand (para cada source)
              ↓ (Command Bus)
         Command Handler (simple)
              ↓
         Emite: SourceScraped
              ↓ (Event Bus)
         Process Manager
              ↓
         Si todas completadas → Emite: PipelineCompleted
```

### Cuándo Usar Process Manager

✅ **Usar Process Manager cuando**:
- Flujo involucra múltiples comandos
- Necesitas coordinar múltiples agregados
- El proceso tiene múltiples pasos
- Necesitas trackear estado del proceso

❌ **NO usar Process Manager cuando**:
- Operación simple (1 agregado, 1 operación)
- No hay coordinación entre pasos
- El handler puede completar en una sola operación
