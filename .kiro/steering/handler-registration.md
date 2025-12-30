# Guía de Registro de Handlers

## Introducción

Esta guía documenta el proceso de registro de handlers en el Mediator, cómo agregar nuevos handlers, y cómo diagnosticar y resolver problemas de registro.

## Arquitectura del Sistema de Handlers

### Componentes Principales

```
┌─────────────────────────────────────────────────────────┐
│                    Application Startup                   │
│                                                          │
│  1. Container.register_pipeline_handlers()              │
│     ├─ Registra Pipeline Handlers                       │
│     ├─ Registra Command Handlers                        │
│     ├─ Registra Query Handlers                          │
│     └─ Logging de handlers registrados                  │
│                                                          │
│  2. Validación de handlers críticos (development)       │
│     └─ _validate_critical_handlers()                    │
│                                                          │
│  3. Pipeline ejecuta                                     │
│     └─ Mediator.send(Command) → Handler.handle()        │
└─────────────────────────────────────────────────────────┘
```

### Flujo de Registro

1. **Startup**: `main.py` inicializa containers
2. **Registration**: Cada container registra sus handlers
3. **Validation**: Sistema valida handlers críticos (solo en development)
4. **Execution**: Mediator encuentra y ejecuta handlers

## Registro de Handlers

### Ubicación de Registro

Los handlers se registran en los containers de DI:

- **FetchingContainer**: `src/bootstrap/containers/fetching_container.py`
- **ArticleContainer**: `src/bootstrap/containers/article_container.py`
- **SourceContainer**: `src/bootstrap/containers/source_container.py`

### Método `register_pipeline_handlers()`

Cada container debe implementar `register_pipeline_handlers()` para registrar TODOS los handlers necesarios.

**Estructura**:

```python
def register_pipeline_handlers(self) -> None:
    """
    Registra TODOS los handlers necesarios para ejecutar pipelines.
    
    Incluye:
    - Pipeline handlers (RunFetchPipelineHandler)
    - Command handlers usados por pipelines (StartFetchSessionHandler, etc.)
    - Query handlers si son necesarios
    """
    handlers_registered = []
    
    # 1. Registrar pipeline handlers
    self.infra.register_handler(
        RunFetchPipelineCommand,
        self.get_run_fetch_pipeline_handler(),
    )
    handlers_registered.append("RunFetchPipelineHandler")
    
    # 2. Registrar command handlers
    self.infra.register_handler(
        StartFetchSessionCommand,
        self.get_start_fetch_session_handler(),
    )
    handlers_registered.append("StartFetchSessionHandler")
    
    # 3. Logging de handlers registrados
    self.infra.logger.info(
        "Pipeline handlers registrados en Mediator",
        handlers=handlers_registered,
        count=len(handlers_registered),
    )
```

## Cómo Agregar un Nuevo Handler

### Paso 1: Crear el Command/Query

```python
# src/app/commands/articles/archive_article/command.py
from dataclasses import dataclass

@dataclass(frozen=True)
class ArchiveArticleCommand:
    """Command para archivar un artículo."""
    article_id: str
    reason: str
```

### Paso 2: Crear el Handler

```python
# src/app/commands/articles/archive_article/handler.py
from src.app.commands.articles.archive_article.command import ArchiveArticleCommand
from src.app.commands.articles.archive_article.result import ArchiveArticleResult

class ArchiveArticleHandler:
    """Handler para archivar artículos."""
    
    def __init__(
        self,
        article_repository: IArticleWriteRepository,
        event_bus: IEventBus,
        logger: ILogger,
    ):
        self._repository = article_repository
        self._event_bus = event_bus
        self._logger = logger
    
    async def handle(self, command: ArchiveArticleCommand) -> ArchiveArticleResult:
        """Ejecuta el comando de archivar artículo."""
        # Implementación
        pass
```

### Paso 3: Agregar Factory Method al Container

```python
# src/bootstrap/containers/article_container.py

def get_archive_article_handler(self) -> ArchiveArticleHandler:
    """Factory para ArchiveArticleHandler."""
    return ArchiveArticleHandler(
        article_repository=self.get_article_write_repository(),
        event_bus=self.infra.event_bus,
        logger=self.infra.logger,
    )
```

### Paso 4: Registrar en `register_pipeline_handlers()`

```python
# src/bootstrap/containers/article_container.py

def register_pipeline_handlers(self) -> None:
    """Registra todos los handlers."""
    handlers_registered = []
    
    # ... handlers existentes ...
    
    # NUEVO: Registrar ArchiveArticleHandler
    from src.app.commands.articles.archive_article.command import (
        ArchiveArticleCommand,
    )
    
    self.infra.register_handler(
        ArchiveArticleCommand,
        self.get_archive_article_handler(),
    )
    handlers_registered.append("ArchiveArticleHandler")
    
    self.infra.logger.info(
        "Pipeline handlers registrados en Mediator",
        handlers=handlers_registered,
        count=len(handlers_registered),
    )
```

### Paso 5: Agregar a Validación de Handlers Críticos (Opcional)

Si el handler es crítico para el funcionamiento del sistema:

```python
# src/main.py

def _validate_critical_handlers(mediator: IMediator) -> None:
    """Valida que los handlers críticos estén registrados."""
    from src.app.commands.articles.archive_article.command import (
        ArchiveArticleCommand,
    )
    
    critical_commands = [
        # ... comandos existentes ...
        ArchiveArticleCommand,  # NUEVO
    ]
    
    # ... resto de la validación ...
```

## Troubleshooting

### Error: HandlerNotFoundError

**Síntoma**:
```
HandlerNotFoundError: No handler registered for StartFetchSessionCommand
```

**Causa**: El comando no tiene un handler registrado en el Mediator.

**Solución**:

1. **Verificar que el handler existe**:
   ```bash
   # Buscar el handler
   find src/app -name "*start_fetch_session*handler.py"
   ```

2. **Verificar que el container tiene factory method**:
   ```python
   # En FetchingContainer
   def get_start_fetch_session_handler(self) -> StartFetchSessionHandler:
       return StartFetchSessionHandler(...)
   ```

3. **Verificar que está registrado**:
   ```python
   # En FetchingContainer.register_pipeline_handlers()
   self.infra.register_handler(
       StartFetchSessionCommand,
       self.get_start_fetch_session_handler(),
   )
   ```

4. **Verificar que se llama register_pipeline_handlers()**:
   ```python
   # En main.py
   _container.fetching.register_pipeline_handlers()
   ```

### Error: Handler Registration Fails

**Síntoma**:
```
ERROR Failed to register handler handler=StartFetchSessionHandler error=...
```

**Causa**: Error al instanciar el handler (dependencias faltantes, etc.)

**Solución**:

1. **Revisar logs detallados**:
   ```bash
   # Buscar en logs
   grep "Failed to register handler" logs/app.log
   ```

2. **Verificar dependencias del handler**:
   ```python
   # Asegurar que todas las dependencias están disponibles
   def get_start_fetch_session_handler(self):
       return StartFetchSessionHandler(
           repository=self.get_fetch_session_repository(),  # ¿Existe?
           event_bus=self.infra.event_bus,  # ¿Está inicializado?
           logger=self.infra.logger,  # ¿Está disponible?
       )
   ```

3. **Verificar imports**:
   ```python
   # Asegurar que los imports son correctos
   from src.app.commands.fetching.start_fetch_session.command import (
       StartFetchSessionCommand,
   )
   from src.app.commands.fetching.start_fetch_session.handler import (
       StartFetchSessionHandler,
   )
   ```

### Error: Critical Handler Missing (Development)

**Síntoma**:
```
RuntimeError: Critical handlers missing: StartFetchSessionCommand
```

**Causa**: Handler crítico no está registrado y estás en modo development.

**Solución**:

1. **Registrar el handler** (ver pasos arriba)

2. **O remover de lista de críticos** (si no es realmente crítico):
   ```python
   # En main.py
   critical_commands = [
       RunFetchPipelineCommand,
       # StartFetchSessionCommand,  # Comentar si no es crítico
   ]
   ```

### Debugging: Ver Handlers Registrados

**Opción 1: Logs de Startup**

```bash
# Buscar en logs
grep "Pipeline handlers registrados" logs/app.log
```

**Opción 2: Agregar Logging Temporal**

```python
# En main.py, después de register_pipeline_handlers()
system_logger.info(
    "Handlers registrados en Mediator",
    handlers=list(_container.infra.mediator._handler_registry.keys())
)
```

**Opción 3: Debugger**

```python
# Agregar breakpoint después de registro
import pdb; pdb.set_trace()

# Inspeccionar registry
print(_container.infra.mediator._handler_registry)
```

## Patrones Comunes

### Patrón 1: Handler con Dependencias Simples

```python
class SimpleHandler:
    def __init__(self, repository: IRepository, logger: ILogger):
        self._repository = repository
        self._logger = logger

# Registro
def get_simple_handler(self):
    return SimpleHandler(
        repository=self.get_repository(),
        logger=self.infra.logger,
    )
```

### Patrón 2: Handler con Múltiples Repositorios

```python
class ComplexHandler:
    def __init__(
        self,
        article_repo: IArticleRepository,
        source_repo: ISourceRepository,
        event_bus: IEventBus,
    ):
        self._article_repo = article_repo
        self._source_repo = source_repo
        self._event_bus = event_bus

# Registro
def get_complex_handler(self):
    return ComplexHandler(
        article_repo=self.get_article_repository(),
        source_repo=self.get_source_repository(),
        event_bus=self.infra.event_bus,
    )
```

### Patrón 3: Handler con Servicios de Dominio

```python
class ServiceBasedHandler:
    def __init__(
        self,
        repository: IRepository,
        quality_service: ArticleQualityService,
        dedup_service: ArticleDeduplicationService,
    ):
        self._repository = repository
        self._quality_service = quality_service
        self._dedup_service = dedup_service

# Registro
def get_service_based_handler(self):
    return ServiceBasedHandler(
        repository=self.get_repository(),
        quality_service=self.get_article_quality_service(),
        dedup_service=self.get_article_deduplication_service(),
    )
```

## Checklist para Agregar Nuevo Handler

- [ ] 1. Crear Command/Query en `src/app/commands/` o `src/app/queries/`
- [ ] 2. Crear Handler en el mismo directorio
- [ ] 3. Crear Result Object
- [ ] 4. Agregar factory method en Container apropiado
- [ ] 5. Registrar en `register_pipeline_handlers()`
- [ ] 6. Agregar logging del handler registrado
- [ ] 7. Agregar a validación de críticos (si aplica)
- [ ] 8. Escribir tests unitarios del handler
- [ ] 9. Escribir tests de integración (si aplica)
- [ ] 10. Verificar que el handler se registra correctamente en startup
- [ ] 11. Verificar que el comando se ejecuta sin HandlerNotFoundError

## Best Practices

### 1. Registrar TODOS los Handlers Usados

❌ **Incorrecto**: Solo registrar pipeline handlers

```python
def register_pipeline_handlers(self):
    # Solo registra el pipeline handler
    self.infra.register_handler(
        RunFetchPipelineCommand,
        self.get_run_fetch_pipeline_handler(),
    )
```

✅ **Correcto**: Registrar pipeline handlers Y command handlers

```python
def register_pipeline_handlers(self):
    # Pipeline handler
    self.infra.register_handler(
        RunFetchPipelineCommand,
        self.get_run_fetch_pipeline_handler(),
    )
    
    # Command handlers usados por el pipeline
    self.infra.register_handler(
        StartFetchSessionCommand,
        self.get_start_fetch_session_handler(),
    )
```

### 2. Logging Detallado

✅ **Correcto**: Loggear lista de handlers registrados

```python
handlers_registered = []

self.infra.register_handler(Command1, handler1)
handlers_registered.append("Handler1")

self.infra.register_handler(Command2, handler2)
handlers_registered.append("Handler2")

self.infra.logger.info(
    "Pipeline handlers registrados",
    handlers=handlers_registered,
    count=len(handlers_registered),
)
```

### 3. Manejo de Errores

✅ **Correcto**: Continuar registrando otros handlers si uno falla

```python
def register_pipeline_handlers(self):
    handlers_registered = []
    errors = []
    
    try:
        self.infra.register_handler(Command1, self.get_handler1())
        handlers_registered.append("Handler1")
    except Exception as e:
        errors.append(f"Handler1: {str(e)}")
        self.infra.logger.error("Failed to register Handler1", error=str(e))
    
    try:
        self.infra.register_handler(Command2, self.get_handler2())
        handlers_registered.append("Handler2")
    except Exception as e:
        errors.append(f"Handler2: {str(e)}")
        self.infra.logger.error("Failed to register Handler2", error=str(e))
    
    if errors:
        self.infra.logger.warning(
            "Some handlers failed to register",
            errors=errors,
            successful=handlers_registered,
        )
```

### 4. Validación de Handlers Críticos

✅ **Correcto**: Validar en development, warning en production

```python
def _validate_critical_handlers(mediator: IMediator, config: AppConfig) -> None:
    critical_commands = [
        StartFetchSessionCommand,
        RunFetchPipelineCommand,
    ]
    
    missing = []
    for command_type in critical_commands:
        if command_type not in mediator._handler_registry:
            missing.append(command_type.__name__)
    
    if missing:
        message = f"Critical handlers missing: {', '.join(missing)}"
        
        if config.environment == "development":
            raise RuntimeError(message)
        else:
            logger.warning(message)
```

## Ejemplos Completos

### Ejemplo 1: Agregar Handler Simple

**Comando**:
```python
# src/app/commands/articles/mark_as_read/command.py
@dataclass(frozen=True)
class MarkArticleAsReadCommand:
    article_id: str
    user_id: str
```

**Handler**:
```python
# src/app/commands/articles/mark_as_read/handler.py
class MarkArticleAsReadHandler:
    def __init__(self, repository: IArticleRepository, logger: ILogger):
        self._repository = repository
        self._logger = logger
    
    async def handle(self, command: MarkArticleAsReadCommand) -> MarkArticleAsReadResult:
        article = await self._repository.find_by_id(command.article_id)
        if not article:
            return MarkArticleAsReadResult.failure("Article not found")
        
        article.mark_as_read(command.user_id)
        await self._repository.save(article)
        
        return MarkArticleAsReadResult.success(article)
```

**Registro**:
```python
# src/bootstrap/containers/article_container.py

def get_mark_article_as_read_handler(self) -> MarkArticleAsReadHandler:
    return MarkArticleAsReadHandler(
        repository=self.get_article_write_repository(),
        logger=self.infra.logger,
    )

def register_pipeline_handlers(self) -> None:
    handlers_registered = []
    
    # ... otros handlers ...
    
    from src.app.commands.articles.mark_as_read.command import (
        MarkArticleAsReadCommand,
    )
    
    self.infra.register_handler(
        MarkArticleAsReadCommand,
        self.get_mark_article_as_read_handler(),
    )
    handlers_registered.append("MarkArticleAsReadHandler")
    
    self.infra.logger.info(
        "Pipeline handlers registrados",
        handlers=handlers_registered,
        count=len(handlers_registered),
    )
```

### Ejemplo 2: Agregar Handler con Servicios

**Comando**:
```python
# src/app/commands/articles/assess_quality/command.py
@dataclass(frozen=True)
class AssessArticleQualityCommand:
    article_id: str
```

**Handler**:
```python
# src/app/commands/articles/assess_quality/handler.py
class AssessArticleQualityHandler:
    def __init__(
        self,
        repository: IArticleRepository,
        quality_service: ArticleQualityService,
        readability_service: ArticleReadabilityService,
        logger: ILogger,
    ):
        self._repository = repository
        self._quality_service = quality_service
        self._readability_service = readability_service
        self._logger = logger
    
    async def handle(
        self, 
        command: AssessArticleQualityCommand
    ) -> AssessArticleQualityResult:
        article = await self._repository.find_by_id(command.article_id)
        if not article:
            return AssessArticleQualityResult.failure("Article not found")
        
        # Usar servicios de dominio
        quality = self._quality_service.calculate_quality(article)
        readability = self._readability_service.calculate_readability(article)
        
        article.set_quality_metrics(quality, readability)
        await self._repository.save(article)
        
        return AssessArticleQualityResult.success(article, quality, readability)
```

**Registro**:
```python
# src/bootstrap/containers/article_container.py

def get_assess_article_quality_handler(self) -> AssessArticleQualityHandler:
    return AssessArticleQualityHandler(
        repository=self.get_article_write_repository(),
        quality_service=self.get_article_quality_service(),
        readability_service=self.get_article_readability_service(),
        logger=self.infra.logger,
    )

def register_pipeline_handlers(self) -> None:
    handlers_registered = []
    
    # ... otros handlers ...
    
    from src.app.commands.articles.assess_quality.command import (
        AssessArticleQualityCommand,
    )
    
    self.infra.register_handler(
        AssessArticleQualityCommand,
        self.get_assess_article_quality_handler(),
    )
    handlers_registered.append("AssessArticleQualityHandler")
    
    self.infra.logger.info(
        "Pipeline handlers registrados",
        handlers=handlers_registered,
        count=len(handlers_registered),
    )
```

## Referencias

- **Design Document**: `.kiro/specs/fix-mediator-handler-registration/design.md`
- **Requirements**: `.kiro/specs/fix-mediator-handler-registration/requirements.md`
- **Architecture**: `.kiro/steering/architecture.md`
- **Domain Patterns**: `.kiro/steering/domain-patterns.md`

## Preguntas Frecuentes

### ¿Dónde registro handlers de queries?

Los query handlers se registran en el mismo lugar que los command handlers, en `register_pipeline_handlers()`.

### ¿Puedo registrar handlers dinámicamente en runtime?

No recomendado. Todos los handlers deben registrarse durante el startup para garantizar consistencia.

### ¿Qué pasa si olvido registrar un handler?

El sistema lanzará `HandlerNotFoundError` cuando intentes enviar el comando. En development, la validación de startup detectará handlers críticos faltantes.

### ¿Cómo testeo que un handler está registrado?

```python
def test_handler_is_registered():
    container = FetchingContainer()
    container.register_pipeline_handlers()
    
    # Verificar que el handler está en el registry
    assert StartFetchSessionCommand in container.infra.mediator._handler_registry
```

### ¿Puedo tener múltiples handlers para el mismo comando?

No. El Mediator solo soporta un handler por comando. Si necesitas múltiples acciones, usa eventos de dominio y event handlers.
