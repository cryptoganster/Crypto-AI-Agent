# Design Document

## Overview

Este documento describe el diseño técnico para migrar la arquitectura actual del proyecto a una estructura basada en Bounded Contexts siguiendo Domain-Driven Design (DDD) y Clean Architecture. La migración se realizará de forma incremental, copiando archivos desde las capas más bajas (domain) hacia las superiores (infrastructure, api), con un proceso de deprecación y eliminación segura entre tareas.

### Objetivos

1. Organizar el código en bounded contexts claros: Article, Source y Fetching
2. Mantener Clean Architecture con separación de capas (domain, app, infrastructure, api)
3. Crear un shared kernel para código común entre contextos
4. Migrar archivos sin reescribirlos, solo actualizando imports
5. Deprecar archivos antes de eliminarlos para detectar dependencias no migradas
6. Limpiar código obsoleto de forma incremental entre tareas
7. Preservar toda la funcionalidad existente sin regresiones

### Principios de Diseño

- **Bottom-Up Migration**: Migrar desde genesis files (aggregates) hacia arriba
- **Copy, Don't Rewrite**: Copiar contenido exacto, solo actualizar imports
- **Deprecate Before Delete**: Marcar como deprecado, validar, luego eliminar
- **Incremental Cleanup**: Limpiar archivos deprecados al final de cada tarea
- **Test-Driven Validation**: Ejecutar tests después de cada cambio
- **Log-Based Detection**: Usar logs para detectar uso de código deprecado


## Architecture

### Target Structure

```
src/
├── article/                    # Article Bounded Context
│   ├── domain/
│   │   ├── aggregates/        # Article aggregate
│   │   ├── entities/          # Domain entities
│   │   ├── value_objects/     # Article-specific VOs
│   │   ├── events/            # Article domain events
│   │   ├── services/          # Article domain services
│   │   ├── factories/         # ArticleFactory
│   │   └── repositories/      # Repository interfaces
│   ├── app/
│   │   ├── commands/          # Article commands
│   │   ├── queries/           # Article queries
│   │   ├── event_handlers/    # Article event handlers
│   │   └── interfaces/        # Application interfaces
│   ├── infrastructure/
│   │   ├── persistence/
│   │   │   ├── mappers/       # ORM mappers
│   │   │   └── orm_models/    # SQLAlchemy models
│   │   ├── messaging/         # Event publishing
│   │   └── http/              # External HTTP clients
│   └── api/
│       ├── routers/           # FastAPI routers
│       └── schemas/           # Pydantic schemas
│
├── source/                     # Source Bounded Context
│   └── ... (same structure)
│
├── fetching/                   # Fetching Bounded Context
│   ├── app/
│   │   └── process_managers/  # Fetch orchestration
│   └── ... (same structure)
│
└── shared/
    ├── kernel/                 # Shared abstractions
    │   ├── aggregate_root.py
    │   ├── entity.py
    │   ├── value_object.py
    │   ├── domain_event.py
    │   ├── commands.py
    │   ├── queries.py
    │   ├── bus.py
    │   ├── errors.py
    │   └── uow.py
    ├── infra/                  # Shared infrastructure
    │   ├── logger/
    │   ├── event_bus/
    │   └── di/                 # Dependency injection
    └── utils/                  # Shared utilities
```


### Bounded Context Boundaries

#### Article Context
**Responsabilidad**: Gestión completa del ciclo de vida de artículos

**Componentes**:
- Article aggregate (raíz)
- Value objects: ArticleTitle, ArticleUrl, ArticleContent, ContentQuality, etc.
- Domain services: ArticleQualityService, ArticleDeduplicationService, etc.
- Commands: CreateArticle, UpdateArticle, PublishArticle, ArchiveArticle
- Queries: GetArticle, ListArticles, GetArticleStats
- Events: ArticleCreated, ArticlePublished, ArticleArchived

**Límites**: No conoce detalles de Source ni Fetching. Se comunica vía eventos.

#### Source Context
**Responsabilidad**: Gestión de fuentes RSS y su configuración

**Componentes**:
- Source aggregate (raíz)
- Value objects: SourceUrl, SourceName, SourceMetrics, SourceConfiguration
- Domain services: SourceValidationService, SourceHealthService
- Commands: CreateSource, UpdateSource, ActivateSource, DeactivateSource
- Queries: GetSource, ListSources, GetSourceHealth
- Events: SourceCreated, SourceActivated, SourceHealthDegraded

**Límites**: No conoce Article ni Fetching. Publica eventos de cambios de estado.

#### Fetching Context
**Responsabilidad**: Orquestación de operaciones de scraping

**Componentes**:
- FetchSession aggregate (raíz)
- Entities: FetchRecord
- Value objects: FetchState, FetchLimit, FetchSessionStatus
- Domain services: FetchOperationCoordinator, ErrorTrackingService
- Process managers: FetchProcessManager, ScrapingProcessManager
- Commands: StartFetchSession, CompleteFetchSession
- Queries: GetFetchSession, ListFetchSessions
- Events: FetchSessionStarted, FetchSessionCompleted

**Límites**: Coordina entre Source y Article vía eventos. No accede directamente a sus aggregates.


## Components and Interfaces

### Shared Kernel

El shared kernel contiene abstracciones y utilidades compartidas entre todos los bounded contexts.

#### Core Abstractions

```python
# src/shared/kernel/aggregate_root.py
class IAggregateRoot(ABC):
    """Interface base para Aggregate Roots."""
    
    @property
    @abstractmethod
    def domain_events(self) -> Sequence[IDomainEvent]:
        pass
    
    @abstractmethod
    def get_uncommitted_events(self) -> Sequence[IDomainEvent]:
        pass
    
    @abstractmethod
    def mark_events_as_committed(self) -> None:
        pass
```

```python
# src/shared/kernel/commands.py
class ICommand(Protocol):
    """Interface para comandos CQRS."""
    pass

class ICommandHandler(Protocol[TCommand, TResult]):
    """Interface para handlers de comandos."""
    async def handle(self, command: TCommand) -> TResult:
        pass
```

```python
# src/shared/kernel/bus.py
class IMediator(Protocol):
    """Interface para mediator pattern."""
    async def send(self, command: ICommand) -> Any:
        pass

class IEventBus(Protocol):
    """Interface para event bus."""
    async def publish(self, event: IDomainEvent) -> None:
        pass
    
    async def publish_all(self, events: Sequence[IDomainEvent]) -> None:
        pass
```


### Deprecation System

Sistema para marcar, detectar y eliminar código deprecado de forma segura.

#### Deprecation Decorator

```python
# src/shared/utils/deprecated.py
import warnings
import functools
from typing import Callable, TypeVar, Any
from loguru import logger

F = TypeVar('F', bound=Callable[..., Any])

def deprecated(
    reason: str,
    new_location: str,
    removal_version: str = "next"
) -> Callable[[F], F]:
    """
    Marca una función, clase o módulo como deprecado.
    
    Args:
        reason: Razón de la deprecación
        new_location: Nueva ubicación del código
        removal_version: Versión en la que se eliminará
        
    Example:
        @deprecated(
            reason="Migrado a bounded context",
            new_location="src.article.domain.aggregates.article",
            removal_version="2.0"
        )
        class Article:
            pass
    """
    def decorator(obj: F) -> F:
        @functools.wraps(obj)
        def wrapper(*args, **kwargs):
            # Emitir warning
            warning_msg = (
                f"{obj.__name__} is deprecated: {reason}. "
                f"Use {new_location} instead. "
                f"Will be removed in version {removal_version}."
            )
            warnings.warn(warning_msg, DeprecationWarning, stacklevel=2)
            
            # Log deprecation con stack trace
            logger.warning(
                "DEPRECATION WARNING",
                deprecated_item=obj.__name__,
                reason=reason,
                new_location=new_location,
                removal_version=removal_version,
                stack_info=True
            )
            
            return obj(*args, **kwargs)
        
        # Marcar como deprecado
        wrapper.__deprecated__ = True
        wrapper.__deprecation_info__ = {
            "reason": reason,
            "new_location": new_location,
            "removal_version": removal_version
        }
        
        return wrapper
    
    return decorator
```


#### Module-Level Deprecation

```python
# Para deprecar módulos completos
# src/domain/aggregates/article.py (archivo original)

from src.shared.utils.deprecated import deprecated
from src.article.domain.aggregates.article import Article as NewArticle

# Deprecar la clase en la ubicación antigua
@deprecated(
    reason="Migrado a Article bounded context",
    new_location="src.article.domain.aggregates.article.Article",
    removal_version="2.0"
)
class Article(NewArticle):
    """Deprecated: Use src.article.domain.aggregates.article.Article instead."""
    pass

# También podemos deprecar el módulo completo
import warnings
warnings.warn(
    "Module src.domain.aggregates.article is deprecated. "
    "Use src.article.domain.aggregates.article instead.",
    DeprecationWarning,
    stacklevel=2
)
```

#### Deprecation Detection Script

```python
# scripts/check_deprecations.py
import re
from pathlib import Path
from typing import List, Tuple

def check_deprecation_warnings_in_logs(
    log_dir: Path = Path("logs")
) -> List[Tuple[str, str, str]]:
    """
    Busca deprecation warnings en archivos de log.
    
    Returns:
        Lista de (archivo_log, deprecated_item, new_location)
    """
    warnings = []
    
    for log_file in log_dir.glob("*.log"):
        with open(log_file) as f:
            for line in f:
                if "DEPRECATION WARNING" in line:
                    # Parsear el warning
                    match = re.search(
                        r'deprecated_item=(\S+).*new_location=(\S+)',
                        line
                    )
                    if match:
                        warnings.append((
                            str(log_file),
                            match.group(1),
                            match.group(2)
                        ))
    
    return warnings

def find_references_to_deprecated(
    deprecated_path: str,
    src_dir: Path = Path("src")
) -> List[Tuple[str, int, str]]:
    """
    Busca referencias a código deprecado en el código fuente.
    
    Returns:
        Lista de (archivo, línea, contenido)
    """
    references = []
    
    for py_file in src_dir.rglob("*.py"):
        with open(py_file) as f:
            for line_num, line in enumerate(f, 1):
                if deprecated_path in line and "import" in line:
                    references.append((
                        str(py_file),
                        line_num,
                        line.strip()
                    ))
    
    return references
```


## Data Models

### Migration State Tracking

Para trackear el progreso de la migración, usaremos un archivo JSON:

```python
# migration_state.json
{
  "version": "1.0",
  "started_at": "2024-01-15T10:00:00Z",
  "current_phase": "article_domain",
  "completed_tasks": [
    "shared_kernel_setup",
    "article_aggregates_migration"
  ],
  "deprecated_files": [
    {
      "original_path": "src/domain/aggregates/article.py",
      "new_path": "src/article/domain/aggregates/article.py",
      "deprecated_at": "2024-01-15T10:30:00Z",
      "status": "deprecated",  # deprecated | safe_to_delete | deleted
      "references_found": 0,
      "last_checked": "2024-01-15T11:00:00Z"
    }
  ],
  "contexts": {
    "article": {
      "status": "in_progress",  # not_started | in_progress | completed
      "layers": {
        "domain": "completed",
        "app": "in_progress",
        "infrastructure": "not_started",
        "api": "not_started"
      }
    },
    "source": {
      "status": "not_started",
      "layers": {}
    },
    "fetching": {
      "status": "not_started",
      "layers": {}
    }
  }
}
```

### File Mapping Registry

Registro de mapeo entre archivos antiguos y nuevos:

```python
# file_mapping.json
{
  "mappings": [
    {
      "old_path": "src/domain/aggregates/article.py",
      "new_path": "src/article/domain/aggregates/article.py",
      "type": "aggregate",
      "context": "article",
      "layer": "domain",
      "migrated_at": "2024-01-15T10:30:00Z"
    },
    {
      "old_path": "src/domain/value_objects/article_title.py",
      "new_path": "src/article/domain/value_objects/article_title.py",
      "type": "value_object",
      "context": "article",
      "layer": "domain",
      "migrated_at": "2024-01-15T10:35:00Z"
    }
  ],
  "import_transformations": [
    {
      "old_import": "from src.domain.aggregates.article import Article",
      "new_import": "from src.article.domain.aggregates.article import Article"
    },
    {
      "old_import": "from src.domain.shared.interfaces.core.aggregate_root import IAggregateRoot",
      "new_import": "from src.shared.kernel.aggregate_root import IAggregateRoot"
    }
  ]
}
```


## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Import Validity After Migration
*For any* archivo migrado, todos sus imports deben ser válidos y resolverse correctamente en la nueva estructura
**Validates: Requirements 2.2, 8.1, 8.2**

### Property 2: Content Preservation
*For any* archivo migrado, el contenido (excepto imports) debe ser idéntico al archivo original
**Validates: Requirements 3.1**

### Property 3: Import Path Transformation
*For any* import actualizado, debe seguir el patrón de transformación correcto (src.domain.* → src.{context}.domain.*)
**Validates: Requirements 3.2, 8.1**

### Property 4: Deprecation Marker Presence
*For any* archivo copiado a la nueva estructura, el archivo original debe contener el decorador @deprecated
**Validates: Requirements 3.3, 13.1**

### Property 5: Shared Kernel Import Consistency
*For any* bounded context, los imports de abstracciones base deben venir de src.shared.kernel
**Validates: Requirements 6.4**

### Property 6: Domain Layer Independence
*For any* archivo en domain/, no debe importar de app/, infrastructure/ o api/
**Validates: Requirements 7.1, 7.5**

### Property 7: Absolute Import Usage
*For any* archivo migrado, no debe contener imports relativos
**Validates: Requirements 8.3**

### Property 8: Container Import Updates
*For any* container en bootstrap/, los imports deben usar las nuevas rutas de bounded contexts
**Validates: Requirements 11.1**

### Property 9: API Route Preservation
*For any* endpoint de API, las rutas y contratos deben permanecer sin cambios después de la migración
**Validates: Requirements 12.1**

### Property 10: Router Import Updates
*For any* router en api/, los imports deben usar las nuevas rutas de bounded contexts
**Validates: Requirements 12.3**


## Error Handling

### Migration Errors

```python
class MigrationError(Exception):
    """Base exception for migration errors."""
    pass

class DependencyNotFoundError(MigrationError):
    """Raised when a dependency hasn't been migrated yet."""
    def __init__(self, file: str, missing_dependency: str):
        self.file = file
        self.missing_dependency = missing_dependency
        super().__init__(
            f"Cannot migrate {file}: dependency {missing_dependency} not found"
        )

class DeprecationWarningFoundError(MigrationError):
    """Raised when deprecation warnings are found in logs."""
    def __init__(self, warnings: List[Tuple[str, str, str]]):
        self.warnings = warnings
        super().__init__(
            f"Found {len(warnings)} deprecation warnings in logs. "
            "Cannot proceed with deletion."
        )

class ActiveReferencesError(MigrationError):
    """Raised when trying to delete a file with active references."""
    def __init__(self, file: str, references: List[Tuple[str, int, str]]):
        self.file = file
        self.references = references
        super().__init__(
            f"Cannot delete {file}: found {len(references)} active references"
        )

class TestFailureError(MigrationError):
    """Raised when tests fail after migration."""
    def __init__(self, failed_tests: List[str]):
        self.failed_tests = failed_tests
        super().__init__(
            f"Migration validation failed: {len(failed_tests)} tests failed"
        )
```

### Error Recovery

1. **Dependency Not Found**: Migrar la dependencia primero, luego reintentar
2. **Deprecation Warnings**: Identificar y migrar los archivos que usan código deprecado
3. **Active References**: Actualizar las referencias antes de eliminar
4. **Test Failures**: Revertir cambios y analizar el problema


## Testing Strategy

### Unit Testing

**Objetivo**: Verificar componentes individuales del sistema de migración

**Tests a implementar**:
- Test de deprecation decorator: verificar que emita warnings correctos
- Test de import transformation: verificar que las rutas se transformen correctamente
- Test de dependency detection: verificar que detecte dependencias correctamente
- Test de reference finder: verificar que encuentre referencias a archivos

**Ejemplo**:
```python
def test_deprecation_decorator_emits_warning():
    """Debería emitir warning cuando se usa código deprecado."""
    @deprecated(
        reason="Test",
        new_location="new.module",
        removal_version="2.0"
    )
    def old_function():
        return "old"
    
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        old_function()
        
        assert len(w) == 1
        assert issubclass(w[0].category, DeprecationWarning)
        assert "new.module" in str(w[0].message)
```

### Integration Testing

**Objetivo**: Verificar que los componentes funcionen juntos correctamente

**Tests a implementar**:
- Test de migración completa de un archivo simple
- Test de detección de deprecation warnings en logs
- Test de eliminación segura de archivos
- Test de actualización de imports en múltiples archivos

**Ejemplo**:
```python
async def test_safe_file_deletion_with_no_references():
    """Debería eliminar archivo cuando no hay referencias."""
    # Arrange
    deprecated_file = Path("src/domain/aggregates/article.py")
    migration_service = MigrationService()
    
    # Act
    result = await migration_service.safe_delete(deprecated_file)
    
    # Assert
    assert result.success is True
    assert not deprecated_file.exists()
```


### Property-Based Testing

**Framework**: Hypothesis (Python property-based testing library)

**Configuración**: Mínimo 100 iteraciones por propiedad

**Properties a testear**:

#### Property Test 1: Import Transformation Correctness
```python
from hypothesis import given, strategies as st

@given(
    old_path=st.text(min_size=1),
    context=st.sampled_from(["article", "source", "fetching"]),
    layer=st.sampled_from(["domain", "app", "infrastructure", "api"])
)
def test_import_transformation_preserves_structure(old_path, context, layer):
    """
    **Feature: bounded-context-migration, Property 3: Import Path Transformation**
    
    For any import path, transforming it should follow the correct pattern.
    """
    transformer = ImportTransformer()
    new_path = transformer.transform(old_path, context, layer)
    
    # Property: new path should start with src.{context}.{layer}
    assert new_path.startswith(f"src.{context}.{layer}")
    
    # Property: transformation should be reversible
    original_parts = old_path.split(".")
    new_parts = new_path.split(".")
    assert len(new_parts) >= len(original_parts)
```

#### Property Test 2: Content Preservation
```python
@given(
    file_content=st.text(min_size=10, max_size=1000),
    imports=st.lists(st.text(min_size=5), min_size=0, max_size=10)
)
def test_migration_preserves_non_import_content(file_content, imports):
    """
    **Feature: bounded-context-migration, Property 2: Content Preservation**
    
    For any file content, migration should preserve everything except imports.
    """
    migrator = FileMigrator()
    
    # Create file with imports and content
    original = "\n".join(imports) + "\n\n" + file_content
    
    # Migrate
    migrated = migrator.migrate_content(original, "article", "domain")
    
    # Property: non-import content should be identical
    original_content = extract_non_import_content(original)
    migrated_content = extract_non_import_content(migrated)
    
    assert original_content == migrated_content
```

#### Property Test 3: Deprecation Marker Presence
```python
@given(
    file_path=st.text(min_size=5),
    context=st.sampled_from(["article", "source", "fetching"])
)
def test_copied_files_have_deprecation_marker(file_path, context):
    """
    **Feature: bounded-context-migration, Property 4: Deprecation Marker Presence**
    
    For any file copied, the original must have @deprecated decorator.
    """
    migrator = FileMigrator()
    
    # Copy file
    migrator.copy_and_deprecate(file_path, context)
    
    # Property: original file should contain @deprecated
    original_content = Path(file_path).read_text()
    assert "@deprecated" in original_content
    assert "new_location=" in original_content
```


#### Property Test 4: Domain Layer Independence
```python
@given(
    domain_file=st.text(min_size=10),
    imports=st.lists(
        st.sampled_from([
            "from src.article.domain",
            "from src.shared.kernel",
            "from datetime import",
            "from typing import"
        ]),
        min_size=1,
        max_size=5
    )
)
def test_domain_files_have_no_invalid_imports(domain_file, imports):
    """
    **Feature: bounded-context-migration, Property 6: Domain Layer Independence**
    
    For any file in domain/, it should not import from app/, infrastructure/ or api/.
    """
    validator = LayerValidator()
    
    # Create domain file with imports
    content = "\n".join(imports) + "\n\n" + domain_file
    
    # Property: should not have invalid imports
    invalid_imports = validator.find_invalid_domain_imports(content)
    
    assert len(invalid_imports) == 0, f"Found invalid imports: {invalid_imports}"
```

#### Property Test 5: Absolute Import Usage
```python
@given(
    file_content=st.text(min_size=10),
    num_imports=st.integers(min_value=1, max_value=10)
)
def test_migrated_files_use_absolute_imports(file_content, num_imports):
    """
    **Feature: bounded-context-migration, Property 7: Absolute Import Usage**
    
    For any migrated file, all imports should be absolute (no relative imports).
    """
    migrator = FileMigrator()
    
    # Migrate file
    migrated_content = migrator.migrate_content(file_content, "article", "domain")
    
    # Property: should not contain relative imports
    relative_import_patterns = [
        "from .",
        "from ..",
        "import ."
    ]
    
    for pattern in relative_import_patterns:
        assert pattern not in migrated_content
```

### End-to-End Testing

**Objetivo**: Verificar flujos completos de migración

**Scenarios a testear**:
1. Migración completa de Article context
2. Detección y corrección de deprecation warnings
3. Eliminación segura de archivos deprecados
4. Ejecución de API después de migración

**Ejemplo**:
```python
async def test_complete_article_context_migration():
    """Debería migrar Article context completamente sin errores."""
    # Arrange
    migration_orchestrator = MigrationOrchestrator()
    
    # Act
    result = await migration_orchestrator.migrate_context("article")
    
    # Assert
    assert result.success is True
    assert result.deprecated_files_count > 0
    assert result.deleted_files_count == 0  # No se eliminan hasta validar
    
    # Verify structure
    assert Path("src/article/domain").exists()
    assert Path("src/article/app").exists()
    assert Path("src/article/infrastructure").exists()
    assert Path("src/article/api").exists()
    
    # Verify tests pass
    test_result = await run_tests("tests/article/")
    assert test_result.failed == 0
```


## Migration Algorithm

### Phase 1: Shared Kernel Setup

1. Crear estructura de directorios `src/shared/kernel/`
2. Migrar abstracciones base desde `src/domain/shared/interfaces/core/`:
   - `aggregate_root.py` → `src/shared/kernel/aggregate_root.py`
   - `entity.py` → `src/shared/kernel/entity.py`
   - `value_object.py` → `src/shared/kernel/value_object.py`
   - `domain_event.py` → `src/shared/kernel/domain_event.py`
3. Crear interfaces comunes:
   - `commands.py` (ICommand, ICommandHandler)
   - `queries.py` (IQuery, IQueryHandler)
   - `bus.py` (IMediator, IEventBus)
   - `errors.py` (excepciones base)
   - `uow.py` (IUnitOfWork)
4. Migrar shared infrastructure:
   - Logger → `src/shared/infra/logger/`
   - Event bus → `src/shared/infra/event_bus/`
   - DI containers base → `src/shared/infra/di/`
5. Deprecar archivos originales
6. Ejecutar tests
7. Verificar no hay deprecation warnings
8. Eliminar archivos deprecados si todo pasa

### Phase 2: Article Context - Domain Layer

**Orden de migración (bottom-up)**:

1. **Genesis files** (sin dependencias externas):
   - Value objects base: `ArticleId`, `ArticleTitle`, `ArticleUrl`
   - Enums: `ArticleStatus`, `ArticleQualityLevel`

2. **Value objects con dependencias**:
   - `ContentQuality` (depende de value objects base)
   - `ArticleContent`, `ArticleSummary`, etc.

3. **Events**:
   - `ArticleCreated`, `ArticlePublished`, etc.

4. **Aggregate**:
   - `Article` (depende de VOs y events)

5. **Entities**:
   - Si existen entities relacionadas

6. **Domain Services**:
   - `ArticleQualityService`
   - `ArticleDeduplicationService`
   - etc.

7. **Factories**:
   - `ArticleFactory`

8. **Repository Interfaces**:
   - `IArticleRepository`

**Proceso por archivo**:
```python
def migrate_file(source_path: Path, context: str, layer: str):
    # 1. Verificar dependencias
    dependencies = analyze_dependencies(source_path)
    for dep in dependencies:
        if not dep.exists_in_new_structure():
            raise DependencyNotFoundError(source_path, dep)
    
    # 2. Copiar archivo
    target_path = build_target_path(source_path, context, layer)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_path, target_path)
    
    # 3. Actualizar imports en archivo copiado
    update_imports(target_path, context, layer)
    
    # 4. Deprecar archivo original
    deprecate_file(source_path, target_path)
    
    # 5. Registrar en mapping
    register_migration(source_path, target_path)
    
    return target_path
```


### Phase 3: Article Context - Application Layer

1. **Commands** (en orden de dependencias):
   - Command DTOs primero
   - Validators
   - Mappers (locales por comando)
   - Handlers
   - Result objects

2. **Queries**:
   - Query DTOs
   - Query handlers
   - DTOs de respuesta

3. **Event Handlers**:
   - Handlers de eventos de dominio

4. **Interfaces**:
   - Interfaces específicas de aplicación

**Proceso**:
- Mismo algoritmo que domain layer
- Verificar que domain layer esté completo antes de empezar
- Actualizar imports para usar `src.article.domain.*`

### Phase 4: Article Context - Infrastructure Layer

1. **Persistence**:
   - ORM models
   - Mappers (domain ↔ ORM)
   - Repository implementations

2. **Messaging**:
   - Event publishers
   - Message handlers

3. **HTTP**:
   - External API clients

4. **Config**:
   - Configuration específica del contexto

### Phase 5: Article Context - API Layer

1. **Routers**:
   - FastAPI routers
   - Dependency injection setup

2. **Schemas**:
   - Pydantic request schemas
   - Pydantic response schemas

### Phase 6: Validation and Cleanup

```python
async def validate_and_cleanup_context(context: str):
    """Valida y limpia archivos deprecados de un contexto."""
    
    # 1. Ejecutar todos los tests del contexto
    test_result = await run_tests(f"tests/{context}/")
    if test_result.failed > 0:
        raise TestFailureError(test_result.failed_tests)
    
    # 2. Verificar imports con mypy
    mypy_result = await run_mypy(f"src/{context}/")
    if mypy_result.errors > 0:
        raise MigrationError(f"Mypy found {mypy_result.errors} errors")
    
    # 3. Buscar deprecation warnings en logs
    warnings = check_deprecation_warnings_in_logs()
    if warnings:
        raise DeprecationWarningFoundError(warnings)
    
    # 4. Para cada archivo deprecado
    deprecated_files = get_deprecated_files_for_context(context)
    for file in deprecated_files:
        # 4.1. Buscar referencias activas
        references = find_references_to_deprecated(file.path)
        if references:
            raise ActiveReferencesError(file.path, references)
        
        # 4.2. Eliminar archivo
        file.path.unlink()
        logger.info(f"Deleted deprecated file: {file.path}")
        
        # 4.3. Actualizar estado
        update_migration_state(file, status="deleted")
    
    # 5. Ejecutar tests nuevamente
    final_test_result = await run_tests(f"tests/{context}/")
    if final_test_result.failed > 0:
        raise TestFailureError(final_test_result.failed_tests)
    
    logger.info(f"Context {context} migration completed and cleaned up")
```


### Phase 7: Source Context Migration

Repetir fases 2-6 para Source context:
- Seguir el mismo patrón establecido por Article
- Usar las lecciones aprendidas
- Mantener consistencia en estructura

### Phase 8: Fetching Context Migration

Repetir fases 2-6 para Fetching context:
- Incluir process managers en app layer
- Mantener consistencia con Article y Source

### Phase 9: Bootstrap and Containers

1. Actualizar containers en `src/bootstrap/containers/`:
   - Crear `article_container.py`
   - Crear `source_container.py`
   - Crear `fetching_container.py`
   - Crear `shared_container.py`
   - Actualizar `main.py` para usar nuevos containers

2. Actualizar imports en todos los containers

3. Verificar que la aplicación inicie correctamente

### Phase 10: Final Validation

1. Ejecutar suite completa de tests
2. Ejecutar tests E2E
3. Verificar que API responda correctamente
4. Revisar logs finales
5. Generar reporte de migración
6. Generar documentación de nueva estructura

## Import Transformation Rules

### Rule 1: Domain Aggregates
```
OLD: from src.domain.aggregates.article import Article
NEW: from src.article.domain.aggregates.article import Article
```

### Rule 2: Domain Value Objects
```
OLD: from src.domain.value_objects.article_title import ArticleTitle
NEW: from src.article.domain.value_objects.article_title import ArticleTitle
```

### Rule 3: Shared Kernel
```
OLD: from src.domain.shared.interfaces.core.aggregate_root import IAggregateRoot
NEW: from src.shared.kernel.aggregate_root import IAggregateRoot
```

### Rule 4: Application Commands
```
OLD: from src.app.commands.articles.create_article.command import CreateArticleCommand
NEW: from src.article.app.commands.create_article.command import CreateArticleCommand
```

### Rule 5: Infrastructure Repositories
```
OLD: from src.infra.persistence.repositories.article_repository import ArticleRepository
NEW: from src.article.infrastructure.persistence.repositories.article_repository import ArticleRepository
```

### Rule 6: API Routers
```
OLD: from src.presentation.routers.articles import router
NEW: from src.article.api.routers.articles import router
```


## Dependency Graph Analysis

### Tool for Analyzing Dependencies

```python
# scripts/analyze_dependencies.py
import ast
from pathlib import Path
from typing import Set, Dict, List
from dataclasses import dataclass

@dataclass
class FileDependency:
    """Representa una dependencia de archivo."""
    source_file: Path
    imported_module: str
    import_line: int

class DependencyAnalyzer:
    """Analiza dependencias entre archivos Python."""
    
    def __init__(self, src_dir: Path = Path("src")):
        self.src_dir = src_dir
        self.dependency_graph: Dict[Path, Set[str]] = {}
    
    def analyze_file(self, file_path: Path) -> Set[str]:
        """Analiza las dependencias de un archivo."""
        dependencies = set()
        
        with open(file_path) as f:
            try:
                tree = ast.parse(f.read())
            except SyntaxError:
                return dependencies
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    dependencies.add(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    dependencies.add(node.module)
        
        return dependencies
    
    def build_dependency_graph(self) -> Dict[Path, Set[str]]:
        """Construye el grafo completo de dependencias."""
        for py_file in self.src_dir.rglob("*.py"):
            deps = self.analyze_file(py_file)
            self.dependency_graph[py_file] = deps
        
        return self.dependency_graph
    
    def get_migration_order(self, context: str) -> List[Path]:
        """
        Determina el orden de migración basado en dependencias.
        
        Returns:
            Lista de archivos en orden de migración (genesis primero)
        """
        # Filtrar archivos del contexto
        context_files = [
            f for f in self.dependency_graph.keys()
            if self._belongs_to_context(f, context)
        ]
        
        # Ordenar por número de dependencias (menos dependencias primero)
        sorted_files = sorted(
            context_files,
            key=lambda f: len(self.dependency_graph[f])
        )
        
        return sorted_files
    
    def _belongs_to_context(self, file: Path, context: str) -> bool:
        """Determina si un archivo pertenece a un contexto."""
        # Lógica para determinar contexto basado en imports y contenido
        pass
```


## Monitoring and Logging

### Migration Logging

```python
# Configuración de logging para migración
from loguru import logger

logger.add(
    "logs/migration_{time}.log",
    rotation="1 day",
    retention="30 days",
    level="INFO",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
    filter=lambda record: "migration" in record["extra"]
)

# Uso
migration_logger = logger.bind(migration=True)

migration_logger.info(
    "File migrated",
    source=str(source_path),
    target=str(target_path),
    context=context,
    layer=layer
)

migration_logger.warning(
    "DEPRECATION WARNING",
    deprecated_item=item_name,
    new_location=new_path,
    caller_file=caller_file,
    caller_line=caller_line
)
```

### Progress Tracking

```python
# Dashboard simple para trackear progreso
class MigrationProgress:
    """Trackea el progreso de la migración."""
    
    def __init__(self):
        self.total_files = 0
        self.migrated_files = 0
        self.deprecated_files = 0
        self.deleted_files = 0
        self.failed_files = 0
    
    def print_progress(self):
        """Imprime el progreso actual."""
        print(f"""
Migration Progress:
==================
Total files:      {self.total_files}
Migrated:         {self.migrated_files} ({self._percentage(self.migrated_files)}%)
Deprecated:       {self.deprecated_files}
Deleted:          {self.deleted_files}
Failed:           {self.failed_files}
Remaining:        {self.total_files - self.migrated_files}
        """)
    
    def _percentage(self, count: int) -> float:
        if self.total_files == 0:
            return 0.0
        return round((count / self.total_files) * 100, 2)
```

### Deprecation Warning Dashboard

```python
# Script para visualizar deprecation warnings
def generate_deprecation_report():
    """Genera reporte de deprecation warnings."""
    warnings = check_deprecation_warnings_in_logs()
    
    # Agrupar por archivo deprecado
    by_file = {}
    for log_file, deprecated_item, new_location in warnings:
        if deprecated_item not in by_file:
            by_file[deprecated_item] = []
        by_file[deprecated_item].append((log_file, new_location))
    
    # Imprimir reporte
    print("Deprecation Warnings Report")
    print("=" * 50)
    for item, occurrences in by_file.items():
        print(f"\n{item}:")
        print(f"  New location: {occurrences[0][1]}")
        print(f"  Occurrences: {len(occurrences)}")
        for log_file, _ in occurrences[:5]:  # Mostrar primeros 5
            print(f"    - {log_file}")
```


## Rollback Strategy

### Backup Before Migration

```python
def create_backup():
    """Crea backup completo antes de iniciar migración."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = Path(f"backups/pre_migration_{timestamp}")
    
    # Copiar src/ completo
    shutil.copytree("src", backup_dir / "src")
    
    # Copiar tests/
    shutil.copytree("tests", backup_dir / "tests")
    
    # Guardar estado de git
    subprocess.run(["git", "stash", "save", f"Pre-migration backup {timestamp}"])
    
    logger.info(f"Backup created at {backup_dir}")
    return backup_dir
```

### Rollback Procedure

```python
def rollback_migration(backup_dir: Path):
    """Revierte la migración al estado del backup."""
    
    # 1. Eliminar nueva estructura
    for context in ["article", "source", "fetching"]:
        context_dir = Path(f"src/{context}")
        if context_dir.exists():
            shutil.rmtree(context_dir)
    
    # 2. Eliminar shared kernel
    shared_dir = Path("src/shared")
    if shared_dir.exists():
        shutil.rmtree(shared_dir)
    
    # 3. Restaurar desde backup
    shutil.copytree(backup_dir / "src", "src", dirs_exist_ok=True)
    shutil.copytree(backup_dir / "tests", "tests", dirs_exist_ok=True)
    
    # 4. Restaurar git stash
    subprocess.run(["git", "stash", "pop"])
    
    logger.info("Migration rolled back successfully")
```

### Checkpoint System

```python
class MigrationCheckpoint:
    """Sistema de checkpoints para rollback parcial."""
    
    def __init__(self):
        self.checkpoints: List[Dict] = []
    
    def create_checkpoint(self, name: str, description: str):
        """Crea un checkpoint."""
        checkpoint = {
            "name": name,
            "description": description,
            "timestamp": datetime.now().isoformat(),
            "migration_state": self._capture_state(),
            "git_commit": self._get_git_commit()
        }
        self.checkpoints.append(checkpoint)
        
        # Guardar a disco
        with open("migration_checkpoints.json", "w") as f:
            json.dump(self.checkpoints, f, indent=2)
        
        logger.info(f"Checkpoint created: {name}")
    
    def rollback_to_checkpoint(self, name: str):
        """Revierte a un checkpoint específico."""
        checkpoint = next(
            (cp for cp in self.checkpoints if cp["name"] == name),
            None
        )
        
        if not checkpoint:
            raise ValueError(f"Checkpoint {name} not found")
        
        # Revertir a commit de git
        subprocess.run(["git", "reset", "--hard", checkpoint["git_commit"]])
        
        logger.info(f"Rolled back to checkpoint: {name}")
```


## Performance Considerations

### Parallel Migration

Para archivos sin dependencias entre sí, podemos migrar en paralelo:

```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

async def migrate_files_parallel(files: List[Path], context: str, layer: str):
    """Migra múltiples archivos en paralelo."""
    
    # Agrupar por nivel de dependencias
    levels = group_by_dependency_level(files)
    
    # Migrar cada nivel en paralelo
    for level_files in levels:
        tasks = [
            migrate_file_async(file, context, layer)
            for file in level_files
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Verificar errores
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Migration failed: {result}")
                raise result
```

### Caching

Cache de análisis de dependencias para evitar re-análisis:

```python
class DependencyCache:
    """Cache de análisis de dependencias."""
    
    def __init__(self, cache_file: Path = Path(".migration_cache.json")):
        self.cache_file = cache_file
        self.cache = self._load_cache()
    
    def get_dependencies(self, file: Path) -> Optional[Set[str]]:
        """Obtiene dependencias del cache."""
        file_hash = self._hash_file(file)
        cached = self.cache.get(str(file))
        
        if cached and cached["hash"] == file_hash:
            return set(cached["dependencies"])
        
        return None
    
    def set_dependencies(self, file: Path, dependencies: Set[str]):
        """Guarda dependencias en cache."""
        file_hash = self._hash_file(file)
        self.cache[str(file)] = {
            "hash": file_hash,
            "dependencies": list(dependencies)
        }
        self._save_cache()
```

### Incremental Migration

Migrar en batches pequeños para validar frecuentemente:

```python
BATCH_SIZE = 10  # Migrar 10 archivos a la vez

def migrate_in_batches(files: List[Path], context: str, layer: str):
    """Migra archivos en batches pequeños."""
    
    for i in range(0, len(files), BATCH_SIZE):
        batch = files[i:i + BATCH_SIZE]
        
        logger.info(f"Migrating batch {i//BATCH_SIZE + 1}")
        
        # Migrar batch
        for file in batch:
            migrate_file(file, context, layer)
        
        # Validar después de cada batch
        run_tests_for_batch(batch)
        check_deprecation_warnings()
```


## Security Considerations

### Safe File Operations

```python
def safe_file_operation(operation: Callable, *args, **kwargs):
    """Ejecuta operación de archivo de forma segura."""
    try:
        # Verificar permisos
        if not has_write_permission():
            raise PermissionError("No write permission")
        
        # Crear backup temporal
        temp_backup = create_temp_backup()
        
        try:
            # Ejecutar operación
            result = operation(*args, **kwargs)
            
            # Eliminar backup temporal
            temp_backup.unlink()
            
            return result
        except Exception as e:
            # Restaurar desde backup temporal
            restore_from_temp_backup(temp_backup)
            raise e
    except Exception as e:
        logger.error(f"File operation failed: {e}")
        raise
```

### Validation Before Deletion

```python
def validate_before_deletion(file: Path) -> bool:
    """Valida que es seguro eliminar un archivo."""
    
    # 1. Verificar que está marcado como deprecado
    if not is_deprecated(file):
        logger.error(f"Cannot delete {file}: not marked as deprecated")
        return False
    
    # 2. Verificar que no tiene referencias activas
    references = find_references_to_deprecated(str(file))
    if references:
        logger.error(f"Cannot delete {file}: has {len(references)} active references")
        return False
    
    # 3. Verificar que existe archivo de reemplazo
    new_location = get_new_location(file)
    if not new_location.exists():
        logger.error(f"Cannot delete {file}: replacement {new_location} not found")
        return False
    
    # 4. Verificar que tests pasan
    if not all_tests_pass():
        logger.error(f"Cannot delete {file}: tests are failing")
        return False
    
    return True
```

## Summary

Este diseño proporciona una estrategia completa para migrar la arquitectura actual a bounded contexts con las siguientes características clave:

1. **Migración Incremental**: Bottom-up desde genesis files, validando en cada paso
2. **Deprecación Segura**: Marcar archivos como deprecados antes de eliminar, con warnings en logs
3. **Limpieza Entre Tareas**: Eliminar archivos deprecados al final de cada tarea después de validar
4. **Preservación de Funcionalidad**: Copiar sin reescribir, solo actualizar imports
5. **Validación Continua**: Tests y verificación de imports después de cada cambio
6. **Rollback Capability**: Sistema de backups y checkpoints para revertir si es necesario
7. **Bounded Contexts Claros**: Article, Source y Fetching con límites bien definidos
8. **Shared Kernel**: Abstracciones comunes compartidas entre contextos
9. **Clean Architecture**: Separación estricta de capas (domain, app, infrastructure, api)
10. **Property-Based Testing**: Validación formal de propiedades de corrección

La migración se realizará en 10 fases principales, comenzando con el shared kernel, luego Article context (como template), seguido de Source y Fetching contexts, actualizando containers y finalizando con validación completa.

