# Event-Driven Architecture

## Filosofía

Este proyecto usa **Event-Driven Architecture (EDA)** para desacoplar bounded contexts y coordinar flujos de trabajo complejos de forma escalable y resiliente.

## Principios Fundamentales

### 1. Desacoplamiento Temporal y Espacial

**Temporal**: El emisor no espera al receptor
**Espacial**: El emisor no conoce al receptor

```python
# ✅ CORRECTO - Desacoplado
class CreateArticleHandler:
    async def handle(self, command):
        article = self._factory.create_article(...)
        await self._repository.save(article)
        
        # Emitir evento (fire-and-forget)
        events = article.get_uncommitted_events()
        await self._event_bus.publish_all(events)  # ← No espera respuesta
        
        return CreateArticleResult.success(article)

# ❌ INCORRECTO - Acoplado
class CreateArticleHandler:
    async def handle(self, command):
        article = self._factory.create_article(...)
        await self._repository.save(article)
        
        # Llamada directa (acoplado)
        await self._quality_service.calculate_quality(article)  # ❌
        await self._summary_service.generate_summary(article)   # ❌
```

### 2. Separación Read/Write (CQRS)

**Command Handlers**: Escriben estado, emiten eventos
**Event Handlers**: Leen estado, emiten comandos
**Query Handlers**: Solo leen, no emiten nada

```python
# Command Handler (WRITE)
class ScrapeArticleContentHandler:
    async def handle(self, command: ScrapeArticleContentCommand):
        # 1. LEER usando Read Repository
        article = await self._read_repo.find_by_id(command.article_id)
        
        # 2. LÓGICA DE NEGOCIO
        article.scrape_content(content)
        
        # 3. ESCRIBIR usando Write Repository
        await self._write_repo.save(article)
        
        # 4. EMITIR EVENTO
        await self._event_bus.publish(ArticleContentScraped(...))

# Event Handler (COORDINA)
class OnArticleContentScrapedHandler:
    async def handle(self, event: ArticleContentScraped):
        # Emitir siguiente comando en la cadena
        command = ExtractArticlePlaintextCommand(
            article_id=event.article_id
        )
        await self._command_bus.send(command)
```

### 3. Event Handlers Granulares como Coordinadores Ligeros

Este proyecto usa **Event Handlers Granulares** que actúan como **coordinadores ligeros** (similar a Process Managers pero sin estado).

**Patrón Correcto: Event → Event Handler → Command → Command Handler**

```
[Domain Event A]
    ↓
[Event Handler] (coordinador - empaqueta datos del evento)
    ↓
[Command B con datos del Event A]
    ↓
[Command Handler B] (procesa command, NO lee evento)
```

**Event Handler como Coordinador**:
- ✅ Escucha eventos de dominio
- ✅ Extrae datos relevantes del evento
- ✅ Empaqueta datos en command (copy-by-value)
- ✅ Envía command al command bus
- ✅ Sin estado (stateless)

**Datos Permitidos en Commands (del evento anterior)**:
- ✅ IDs y referencias
- ✅ Datos inmutables (strings, números)
- ✅ Metadata para logging
- ✅ Datos calculados
- ✅ Estado mínimo necesario

**Datos NO Permitidos**:
- ❌ Aggregate completo
- ❌ Entidades completas
- ❌ Referencias mutables
- ❌ Estado del Read Model

**Cuándo usar Event Handler Granular**:
- ✅ Flujo lineal (A → B → C → D)
- ✅ Sin estado compartido entre pasos
- ✅ Cada paso es independiente
- ✅ Fácil de testear y debuggear

**Cuándo usar Process Manager**:
- ✅ Flujo complejo con bifurcaciones
- ✅ Necesita mantener estado del proceso
- ✅ Coordina múltiples agregados
- ✅ Requiere compensación o rollback

## Estructura de Event Handlers

### Ubicación

```
src/<bounded-context>/app/event_handlers/
├── __init__.py
├── on_article_content_scraped.py
├── on_article_plaintext_extracted.py
├── on_article_markdown_converted.py
├── on_article_metrics_calculated.py
├── on_article_language_detected.py
├── on_article_summary_generated.py
├── on_article_keywords_extracted.py
└── on_article_quality_calculated.py
```

### Patrón de Event Handler Simple

```python
"""Handler para [EventName] event."""

from src.[bounded_context].domain.events import [EventName]
from src.[bounded_context].app.commands.[next_command].command import (
    [NextCommand],
)
from src.shared.kernel import IMediator
from src.shared.kernel.logger import ILogger


class On[EventName]Handler:
    """
    Handler para [EventName].
    
    Responsabilidad: Cuando [evento ocurre], [acción siguiente].
    
    Flujo:
    - [EventName] → [NextCommand]
    """
    
    def __init__(
        self,
        command_bus: IMediator,
        logger: ILogger,
    ):
        self._command_bus = command_bus
        self._logger = logger.bind(
            layer="application",
            component="On[EventName]Handler",
        )
    
    async def handle(self, event: [EventName]) -> None:
        """
        Maneja [EventName].
        
        Si [condición exitosa] → Emite [NextCommand]
        Si [condición falló] → Log error
        
        Args:
            event: Evento [EventName]
        """
        # 1. Validar evento
        if not event.success:
            self._logger.warning(
                "[Descripción del error]",
                article_id=event.article_id,
                error=event.error_message if hasattr(event, 'error_message') else None,
            )
            return
        
        # 2. Emitir siguiente comando
        command = [NextCommand](
            article_id=event.article_id,
            # ... otros parámetros
        )
        
        try:
            await self._command_bus.send(command)
            
            self._logger.info(
                "[NextCommand] command emitido",
                article_id=event.article_id,
            )
        except Exception as e:
            self._logger.error(
                "Error emitiendo [NextCommand] command",
                article_id=event.article_id,
                error=str(e),
            )
```

### Características de Event Handlers Simples

✅ **Sin estado**: No mantienen estado entre invocaciones
✅ **Idempotentes**: Pueden ejecutarse múltiples veces sin efectos secundarios
✅ **Fire-and-forget**: No esperan respuesta del comando emitido
✅ **Fail-safe**: Errores no detienen el flujo completo
✅ **Logging detallado**: Cada paso loggea su ejecución

## Flujos Event-Driven

### Flujo 1: Content Extraction Pipeline

```
StartScrapingCommand
    ↓
StartScrapingHandler (emite ScrapingStarted)
    ↓ (Event Bus)
OnScrapingStartedHandler
    ↓
ScrapeSourceCommand (para cada source)
    ↓
ScrapeSourceHandler (emite SourceScraped)
    ↓ (Event Bus)
OnSourceScrapedHandler
    ↓
ScrapingCompleted (cuando todas las sources terminan)
    ↓ (Event Bus)
OnScrapingCompletedHandler
    ↓
ScrapeArticleContentCommand (para cada artículo)
    ↓
ScrapeArticleContentHandler (emite ArticleContentScraped)
    ↓ (Event Bus)
OnArticleContentScrapedHandler
    ↓
ExtractArticlePlaintextCommand
    ↓
ExtractArticlePlaintextHandler (emite ArticlePlaintextExtracted)
    ↓ (Event Bus)
OnArticlePlaintextExtractedHandler
    ↓
ConvertArticleToMarkdownCommand
    ↓
ConvertArticleToMarkdownHandler (emite ArticleMarkdownConverted)
    ↓ (Event Bus)
OnArticleMarkdownConvertedHandler
    ↓
[Inicia Content Analysis Pipeline]
```

### Flujo 2: Content Analysis Pipeline

```
ArticleMarkdownConverted
    ↓ (Event Bus)
OnArticleMarkdownConvertedHandler
    ↓
CalculateArticleMetricsCommand
    ↓
CalculateArticleMetricsHandler (emite ArticleMetricsCalculated)
    ↓ (Event Bus)
OnArticleMetricsCalculatedHandler
    ↓
DetectArticleLanguageCommand
    ↓
DetectArticleLanguageHandler (emite ArticleLanguageDetected)
    ↓ (Event Bus)
OnArticleLanguageDetectedHandler
    ↓
GenerateArticleSummaryCommand
    ↓
GenerateArticleSummaryHandler (emite ArticleSummaryGenerated)
    ↓ (Event Bus)
OnArticleSummaryGeneratedHandler
    ↓
ExtractArticleKeywordsCommand
    ↓
ExtractArticleKeywordsHandler (emite ArticleKeywordsExtracted)
    ↓ (Event Bus)
OnArticleKeywordsExtractedHandler
    ↓
CalculateArticleQualityCommand
    ↓
CalculateArticleQualityHandler (emite ArticleQualityCalculated)
    ↓ (Event Bus)
OnArticleQualityCalculatedHandler
    ↓
[FIN - Artículo completamente procesado]
```

## Registro de Event Handlers

### En Container

```python
# src/article/container.py

def register_event_handlers(self) -> None:
    """Registra todos los event handlers del bounded context."""
    
    # Content Extraction Pipeline
    self.infra.register_event_handler(
        ArticleContentScraped,
        self.get_on_article_content_scraped_handler(),
    )
    
    self.infra.register_event_handler(
        ArticlePlaintextExtracted,
        self.get_on_article_plaintext_extracted_handler(),
    )
    
    self.infra.register_event_handler(
        ArticleMarkdownConverted,
        self.get_on_article_markdown_converted_handler(),
    )
    
    # Content Analysis Pipeline
    self.infra.register_event_handler(
        ArticleMetricsCalculated,
        self.get_on_article_metrics_calculated_handler(),
    )
    
    self.infra.register_event_handler(
        ArticleLanguageDetected,
        self.get_on_article_language_detected_handler(),
    )
    
    self.infra.register_event_handler(
        ArticleSummaryGenerated,
        self.get_on_article_summary_generated_handler(),
    )
    
    self.infra.register_event_handler(
        ArticleKeywordsExtracted,
        self.get_on_article_keywords_extracted_handler(),
    )
    
    self.infra.register_event_handler(
        ArticleQualityCalculated,
        self.get_on_article_quality_calculated_handler(),
    )
    
    # Cross-Bounded-Context
    self.infra.register_event_handler(
        ScrapingCompleted,
        self.get_on_scraping_completed_handler(),
    )
```

### Factory Methods

```python
def get_on_article_content_scraped_handler(
    self
) -> OnArticleContentScrapedHandler:
    """Factory para OnArticleContentScrapedHandler."""
    return OnArticleContentScrapedHandler(
        command_bus=self.infra.mediator,
        logger=self.infra.logger,
    )
```

## Beneficios de Event-Driven Architecture

### 1. Desacoplamiento

✅ Bounded contexts independientes
✅ Fácil agregar nuevos handlers sin modificar existentes
✅ Cambios en un handler no afectan otros

### 2. Escalabilidad

✅ Procesamiento asíncrono
✅ Fácil paralelizar (múltiples workers)
✅ Backpressure natural (event queue)

### 3. Resiliencia

✅ Fallos aislados (un handler falla, otros continúan)
✅ Retry automático (event bus puede reintentar)
✅ Dead letter queue para eventos fallidos

### 4. Observabilidad

✅ Cada evento loggea su ejecución
✅ Fácil trazar flujo completo
✅ Métricas por evento (latencia, throughput)

### 5. Testabilidad

✅ Handlers simples y aislados
✅ Fácil mockear event bus
✅ Tests unitarios independientes

## Testing de Event Handlers

### Test Unitario

```python
import pytest
from unittest.mock import AsyncMock, Mock

from src.article.app.event_handlers.on_article_content_scraped import (
    OnArticleContentScrapedHandler,
)
from src.article.domain.events import ArticleContentScraped


class TestOnArticleContentScrapedHandler:
    """Tests para OnArticleContentScrapedHandler."""
    
    @pytest.fixture
    def mock_command_bus(self):
        """Mock para command bus."""
        return AsyncMock()
    
    @pytest.fixture
    def mock_logger(self):
        """Mock para logger."""
        logger = Mock()
        logger.bind.return_value = logger
        return logger
    
    @pytest.fixture
    def handler(self, mock_command_bus, mock_logger):
        """Handler con dependencias mockeadas."""
        return OnArticleContentScrapedHandler(
            command_bus=mock_command_bus,
            logger=mock_logger,
        )
    
    async def test_handle_successful_event_emits_command(
        self,
        handler,
        mock_command_bus,
    ):
        """Debería emitir ExtractArticlePlaintextCommand cuando evento exitoso."""
        # Arrange
        event = ArticleContentScraped(
            article_id="test-123",
            success=True,
            content_length=1000,
        )
        
        # Act
        await handler.handle(event)
        
        # Assert
        mock_command_bus.send.assert_called_once()
        command = mock_command_bus.send.call_args[0][0]
        assert command.article_id == "test-123"
    
    async def test_handle_failed_event_does_not_emit_command(
        self,
        handler,
        mock_command_bus,
    ):
        """No debería emitir comando cuando evento falló."""
        # Arrange
        event = ArticleContentScraped(
            article_id="test-456",
            success=False,
            error_message="Scraping failed",
        )
        
        # Act
        await handler.handle(event)
        
        # Assert
        mock_command_bus.send.assert_not_called()
```

### Test de Integración

```python
@pytest.mark.integration
class TestArticleContentExtractionFlow:
    """Tests de integración para flujo completo."""
    
    async def test_complete_extraction_flow(
        self,
        container,
        test_article,
    ):
        """Debería completar flujo de extracción completo."""
        # Arrange
        mediator = container.infra.mediator
        
        # Act - Emitir comando inicial
        command = ScrapeArticleContentCommand(
            article_id=str(test_article.id)
        )
        result = await mediator.send(command)
        
        # Assert - Verificar que todos los pasos se ejecutaron
        assert result.success
        
        # Verificar eventos emitidos
        events = test_article.get_uncommitted_events()
        event_types = [type(e).__name__ for e in events]
        
        assert "ArticleContentScraped" in event_types
        assert "ArticlePlaintextExtracted" in event_types
        assert "ArticleMarkdownConverted" in event_types
```

## Anti-Patrones a Evitar

### ❌ Anti-Patrón 1: Event Handler con Lógica de Negocio

```python
# ❌ INCORRECTO - Lógica de negocio en event handler
class OnArticleContentScrapedHandler:
    async def handle(self, event: ArticleContentScraped):
        # Lógica de negocio (debería estar en aggregate)
        if len(event.content) < 100:
            return  # ❌ Decisión de negocio
        
        # Calcular calidad (debería estar en domain service)
        quality = self._calculate_quality(event.content)  # ❌
        
        command = ExtractArticlePlaintextCommand(...)
        await self._command_bus.send(command)
```

**Problema**: Event handlers solo coordinan, no contienen lógica de negocio.

**Solución**: Mover lógica al aggregate o domain service.

### ❌ Anti-Patrón 2: Event Handler con Estado

```python
# ❌ INCORRECTO - Event handler con estado
class OnArticleContentScrapedHandler:
    def __init__(self, command_bus, logger):
        self._command_bus = command_bus
        self._logger = logger
        self._processed_articles = set()  # ❌ Estado
    
    async def handle(self, event: ArticleContentScraped):
        if event.article_id in self._processed_articles:
            return  # ❌ Depende de estado
        
        self._processed_articles.add(event.article_id)  # ❌
        # ...
```

**Problema**: Event handlers deben ser stateless.

**Solución**: Usar Process Manager si necesitas estado.

### ❌ Anti-Patrón 3: Event Handler Esperando Respuesta

```python
# ❌ INCORRECTO - Esperar respuesta del comando
class OnArticleContentScrapedHandler:
    async def handle(self, event: ArticleContentScraped):
        command = ExtractArticlePlaintextCommand(...)
        result = await self._command_bus.send(command)  # ❌ Espera respuesta
        
        if result.success:  # ❌ Depende del resultado
            # Hacer algo más
            pass
```

**Problema**: Event handlers son fire-and-forget.

**Solución**: Emitir comando y dejar que otro event handler maneje el resultado.

### ❌ Anti-Patrón 4: Reutilizar Event Handlers

```python
# ❌ INCORRECTO - Event handler genérico reutilizable
class GenericEventHandler:
    def __init__(self, command_bus, next_command_factory):
        self._command_bus = command_bus
        self._next_command_factory = next_command_factory
    
    async def handle(self, event):
        command = self._next_command_factory(event)
        await self._command_bus.send(command)
```

**Problema**: Abstracción innecesaria, dificulta debugging y testing.

**Solución**: Duplicar código simple es mejor que abstraer prematuramente.

## Comparación: Event Handler vs Process Manager

| Aspecto | Event Handler Granular | Process Manager |
|---------|------------------------|-----------------|
| **Propósito** | Coordinar paso único | Coordinar flujo complejo |
| **Estado** | Sin estado | Mantiene estado |
| **Complejidad** | Simple (5-10 líneas) | Complejo (50+ líneas) |
| **Flujo** | Lineal (A → B) | Bifurcado (A → B/C/D) |
| **Testing** | Muy fácil | Más complejo |
| **Debugging** | Muy fácil | Más difícil |
| **Cuándo usar** | Flujos simples | Flujos complejos |

## Resumen

- 🎯 Event-Driven Architecture desacopla bounded contexts
- 🔄 Event Handlers Granulares para flujos lineales simples
- 📝 Process Managers para flujos complejos con estado
- ✅ Command Handlers escriben, Event Handlers coordinan
- 🚫 Event Handlers NO contienen lógica de negocio
- 🔥 Fire-and-forget: No esperar respuestas
- 📊 Logging detallado para observabilidad
- 🧪 Tests unitarios simples y aislados

## Referencias

- **Architecture**: `.kiro/steering/architecture.md`
- **Domain Patterns**: `.kiro/steering/domain-patterns.md`
- **Handler Registration**: `.kiro/steering/handler-registration.md`
- **Testing Guidelines**: `.kiro/steering/testing-guidelines.md`

---

**Última actualización**: 2024-12-06
