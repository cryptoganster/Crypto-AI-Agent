# Design Document

## Overview

Este diseño implementa un sistema de deduplicación multi-nivel basado en RSS GUID que:

1. Usa GUID como criterio primario de deduplicación (más confiable)
2. Mantiene URL + Source como criterio secundario (fallback)
3. Elimina deduplicación por similitud de contenido (preserva contexto para RAG)
4. Diferencia entre duplicado exacto vs actualización de artículo
5. Permite actualizar artículos cuando el feed RSS los modifica

## Architecture

### Flujo de Deduplicación Multi-Nivel

```
ArticleData (del feed RSS)
    ↓
ArticleDeduplicationService.check_duplicate()
    ↓
┌─────────────────────────────────────────┐
│ Nivel 1: Verificación por GUID         │
│ - Si tiene GUID → find_by_guid()        │
│ - Si encuentra → Comparar pub_date      │
│   - pub_date nuevo > existente → UPDATE │
│   - pub_date nuevo ≤ existente → DUP    │
└─────────────────────────────────────────┘
    ↓ (si no hay GUID o no hay match)
┌─────────────────────────────────────────┐
│ Nivel 2: Verificación por URL          │
│ - find_by_url_and_source()              │
│ - Si encuentra → DUPLICATE              │
└─────────────────────────────────────────┘
    ↓ (si no hay match)
┌─────────────────────────────────────────┐
│ Resultado: NO DUPLICATE                 │
│ - Crear nuevo artículo                  │
└─────────────────────────────────────────┘
```

### Flujo de Actualización de Artículo

```
Detección: is_update=True
    ↓
ScrapingCoordinator
    ↓
UpdateArticleFromFeedCommand
    ↓
UpdateArticleFromFeedHandler
    ↓
1. Cargar Article existente (Write Repo)
2. Actualizar campos modificados
3. Persistir cambios
4. Emitir ArticleUpdatedFromFeed event
    ↓
Event Bus
    ↓
OnArticleUpdatedFromFeedHandler
    ↓
Re-ejecutar pipeline de procesamiento:
- ScrapeArticleContentCommand (si URL cambió)
- ExtractArticlePlaintextCommand
- ConvertArticleToMarkdownCommand
- CalculateArticleMetricsCommand
- DetectArticleLanguageCommand
- GenerateArticleSummaryCommand
- ExtractArticleKeywordsCommand
- CalculateArticleQualityCommand
- ProcessArticleForAICommand (re-generar embeddings)
```

## Components and Interfaces

### 1. IArticleReadRepository (Actualizado)

```python
# src/article/domain/interfaces/repositories/article_read_repository.py

from typing import Optional, Protocol
from src.article.domain.dtos import ArticleDTO

class IArticleReadRepository(Protocol):
    """Repository para operaciones de lectura de artículos."""
    
    async def find_by_guid(
        self,
        guid: str,
        source_id: Optional[str] = None,
    ) -> Optional[ArticleDTO]:
        """
        Busca artículo por RSS GUID.
        
        Args:
            guid: GUID del feed RSS
            source_id: Opcional - filtrar por source específico
            
        Returns:
            ArticleDTO si existe, None en caso contrario
        """
        ...
    
    async def find_by_url_and_source(
        self,
        url: str,
        source_id: str,
    ) -> Optional[ArticleDTO]:
        """Busca artículo por URL y source_id (existente)."""
        ...
```

### 2. ArticleDeduplicationService (Refactorizado)

```python
# src/article/infra/services/deduplication.py

from typing import Optional, Tuple
from datetime import datetime
from src.scraping.domain.interfaces.external.rss_feed_fetcher import ArticleData
from src.source.domain.aggregates import Source
from src.article.domain.interfaces.repositories import IArticleReadRepository

class ArticleDeduplicationService:
    """
    Servicio de deduplicación multi-nivel.
    
    Estrategia:
    1. Verificar por GUID (si existe)
    2. Verificar por URL + Source (fallback)
    3. NO verificar por similitud de contenido
    """
    
    def __init__(
        self,
        article_queries: IArticleReadRepository,
        enable_updates: bool = True,
    ):
        """
        Inicializa servicio de deduplicación.
        
        Args:
            article_queries: Repository para queries de artículos
            enable_updates: Si se permiten actualizaciones de artículos
        """
        self._article_queries = article_queries
        self._enable_updates = enable_updates
    
    async def check_duplicate(
        self,
        article_data: ArticleData,
        source: Source,
    ) -> Tuple[bool, Optional[str], Optional[str], bool]:
        """
        Verifica duplicados usando estrategia multi-nivel.
        
        Args:
            article_data: Datos del artículo desde RSS
            source: Source aggregate
            
        Returns:
            Tupla (is_duplicate, duplicate_id, match_method, is_update):
            - is_duplicate: True si es duplicado
            - duplicate_id: ID del artículo duplicado (si existe)
            - match_method: 'guid' | 'url' | None
            - is_update: True si es actualización, False si es duplicado exacto
        """
        # Nivel 1: Verificar por GUID
        if article_data.guid:
            result = await self._check_by_guid(article_data, source)
            if result[0]:  # is_duplicate
                return result
        
        # Nivel 2: Verificar por URL
        result = await self._check_by_url(article_data, source)
        if result[0]:  # is_duplicate
            return result
        
        # No es duplicado
        return (False, None, None, False)
    
    async def _check_by_guid(
        self,
        article_data: ArticleData,
        source: Source,
    ) -> Tuple[bool, Optional[str], Optional[str], bool]:
        """Verifica duplicado por GUID."""
        existing = await self._article_queries.find_by_guid(
            guid=article_data.guid,
            source_id=str(source.id),
        )
        
        if existing is None:
            return (False, None, None, False)
        
        # Determinar si es actualización
        is_update = self._is_article_update(article_data, existing)
        
        return (True, str(existing.id), 'guid', is_update)
    
    async def _check_by_url(
        self,
        article_data: ArticleData,
        source: Source,
    ) -> Tuple[bool, Optional[str], Optional[str], bool]:
        """Verifica duplicado por URL."""
        existing = await self._article_queries.find_by_url_and_source(
            url=article_data.url,
            source_id=str(source.id),
        )
        
        if existing is None:
            return (False, None, None, False)
        
        # URL match siempre es duplicado exacto (no update)
        return (True, str(existing.id), 'url', False)
    
    def _is_article_update(
        self,
        article_data: ArticleData,
        existing: ArticleDTO,
    ) -> bool:
        """
        Determina si el artículo es actualización del existente.
        
        Criterios:
        - Actualizaciones habilitadas
        - Ambos tienen pub_date
        - pub_date nuevo > pub_date existente
        """
        if not self._enable_updates:
            return False
        
        if article_data.pub_date is None or existing.pub_date is None:
            return False
        
        return article_data.pub_date > existing.pub_date
```

### 3. UpdateArticleFromFeedCommand

```python
# src/article/app/commands/update_article_from_feed/command.py

from dataclasses import dataclass
from typing import Optional, List
from datetime import datetime

@dataclass(frozen=True)
class UpdateArticleFromFeedCommand:
    """
    Command para actualizar artículo existente desde feed RSS.
    
    Se usa cuando el feed RSS proporciona contenido actualizado
    para un artículo existente (mismo GUID, pub_date más reciente).
    """
    
    # ID del artículo existente
    article_id: str
    
    # Datos actualizados del feed
    title: str
    url: str
    description: Optional[str]
    pub_date: Optional[datetime]
    
    # Contenido actualizado (si está disponible)
    content: Optional[str]
    
    # Metadatos opcionales
    author: Optional[str]
    categories: Optional[List[str]]
    thumbnail_url: Optional[str]
    
    # Tracking
    correlation_id: Optional[str] = None
    triggered_by: str = "feed_update"
```

### 4. UpdateArticleFromFeedHandler

```python
# src/article/app/commands/update_article_from_feed/handler.py

from src.article.app.commands.update_article_from_feed.command import (
    UpdateArticleFromFeedCommand,
)
from src.article.app.commands.update_article_from_feed.result import (
    UpdateArticleFromFeedResult,
)
from src.article.domain.interfaces.repositories import (
    IArticleReadRepository,
    IArticleWriteRepository,
)
from src.shared.kernel.uow import IUnitOfWork
from src.shared.kernel.event_bus import IEventBus
from src.shared.kernel.logger import ILogger

class UpdateArticleFromFeedHandler:
    """
    Handler para actualizar artículo existente desde feed RSS.
    
    Responsabilidades:
    - Cargar artículo existente
    - Actualizar campos modificados
    - Persistir cambios
    - Emitir ArticleUpdatedFromFeed event
    """
    
    def __init__(
        self,
        read_repo: IArticleReadRepository,
        write_repo: IArticleWriteRepository,
        uow: IUnitOfWork,
        event_bus: IEventBus,
        logger: ILogger,
    ):
        self._read_repo = read_repo
        self._write_repo = write_repo
        self._uow = uow
        self._event_bus = event_bus
        self._logger = logger.bind(
            layer="application",
            component="UpdateArticleFromFeedHandler",
        )
    
    async def handle(
        self,
        command: UpdateArticleFromFeedCommand,
    ) -> UpdateArticleFromFeedResult:
        """Actualiza artículo desde feed RSS."""
        
        self._logger.info(
            "Actualizando artículo desde feed",
            article_id=command.article_id,
            correlation_id=command.correlation_id,
        )
        
        async with self._uow:
            # 1. Cargar artículo existente
            article = await self._write_repo.load(command.article_id)
            
            if article is None:
                self._logger.warning(
                    "Artículo no encontrado para actualización",
                    article_id=command.article_id,
                )
                return UpdateArticleFromFeedResult.not_found(command.article_id)
            
            # 2. Actualizar campos modificados
            article.update_from_feed(
                title=command.title,
                url=command.url,
                description=command.description,
                pub_date=command.pub_date,
                content=command.content,
                author=command.author,
                categories=command.categories,
                thumbnail_url=command.thumbnail_url,
            )
            
            # 3. Persistir cambios
            await self._write_repo.save(article)
            
            # 4. Commit
            await self._uow.commit()
        
        # 5. Publicar eventos (fuera de transacción)
        events = article.get_uncommitted_events()
        await self._event_bus.publish_all(events)
        article.mark_events_as_committed()
        
        self._logger.info(
            "Artículo actualizado exitosamente",
            article_id=command.article_id,
        )
        
        return UpdateArticleFromFeedResult.success(article)
```

### 5. Article Aggregate (Nuevo método)

```python
# src/article/domain/aggregates/article.py

def update_from_feed(
    self,
    title: str,
    url: str,
    description: Optional[str] = None,
    pub_date: Optional[datetime] = None,
    content: Optional[str] = None,
    author: Optional[str] = None,
    categories: Optional[List[str]] = None,
    thumbnail_url: Optional[str] = None,
) -> None:
    """
    Actualiza artículo con datos del feed RSS.
    
    Se usa cuando el feed proporciona contenido actualizado
    para un artículo existente (mismo GUID, pub_date más reciente).
    
    Args:
        title: Título actualizado
        url: URL actualizada
        description: Descripción actualizada
        pub_date: Fecha de publicación actualizada
        content: Contenido actualizado (si disponible)
        author: Autor actualizado
        categories: Categorías actualizadas
        thumbnail_url: Thumbnail actualizado
    """
    from src.article.domain.value_objects.metadata import (
        ArticleTitle,
        ArticleUrl,
        ArticleDescription,
        ArticlePubDate,
    )
    from src.article.domain.events import ArticleUpdatedFromFeed
    
    # Actualizar título si cambió
    new_title = ArticleTitle(title)
    if new_title != self._metadata.title:
        self._metadata = self._metadata.with_title(new_title)
    
    # Actualizar URL si cambió
    new_url = ArticleUrl(url)
    if new_url != self._metadata.url:
        self._metadata = self._metadata.with_url(new_url)
    
    # Actualizar description si cambió
    if description:
        new_desc = ArticleDescription(description)
        if new_desc != self._metadata.description:
            self._metadata = self._metadata.with_description(new_desc)
    
    # Actualizar pub_date si cambió
    if pub_date:
        new_pub_date = ArticlePubDate(pub_date)
        if new_pub_date != self._metadata.pub_date:
            self._metadata = self._metadata.with_pub_date(new_pub_date)
    
    # Actualizar contenido si se proporciona
    if content:
        from src.article.domain.value_objects.metadata import ArticleContent
        new_content = ArticleContent.create(content)
        self._content = self._content.with_scrapped(new_content.scrapped)
    
    # Actualizar author si cambió
    if author and author != self._metadata.author:
        self._metadata = self._metadata.with_author(author)
    
    # Actualizar categories si cambió
    if categories and categories != self._metadata.categories:
        self._metadata = self._metadata.with_categories(categories)
    
    # Actualizar thumbnail si cambió
    if thumbnail_url:
        from src.article.domain.value_objects.metadata import ArticleThumbnailUrl
        new_thumbnail = ArticleThumbnailUrl(thumbnail_url)
        if new_thumbnail != self._metadata.thumbnail_url:
            self._metadata = self._metadata.with_thumbnail_url(new_thumbnail)
    
    # Emitir evento
    event = ArticleUpdatedFromFeed(
        article_id=str(self.id),
        updated_fields=self._get_updated_fields(),
        occurred_at=datetime.now(timezone.utc),
    )
    self._add_domain_event(event)
```

### 6. ArticleUpdatedFromFeed Event

```python
# src/article/domain/events/article_updated_from_feed.py

from dataclasses import dataclass
from datetime import datetime
from typing import List

@dataclass(frozen=True)
class ArticleUpdatedFromFeed:
    """
    Evento emitido cuando un artículo es actualizado desde feed RSS.
    
    Se emite cuando el feed proporciona contenido actualizado
    para un artículo existente (mismo GUID, pub_date más reciente).
    """
    
    article_id: str
    updated_fields: List[str]  # ['title', 'content', 'pub_date', etc.]
    occurred_at: datetime
```

### 7. OnArticleUpdatedFromFeedHandler

```python
# src/article/app/event_handlers/on_article_updated_from_feed.py

from src.article.domain.events import ArticleUpdatedFromFeed
from src.shared.kernel.mediator import IMediator
from src.shared.kernel.logger import ILogger

class OnArticleUpdatedFromFeedHandler:
    """
    Handler para ArticleUpdatedFromFeed event.
    
    Responsabilidad: Re-ejecutar pipeline de procesamiento cuando
    un artículo es actualizado desde el feed RSS.
    """
    
    def __init__(
        self,
        command_bus: IMediator,
        logger: ILogger,
    ):
        self._command_bus = command_bus
        self._logger = logger.bind(
            layer="application",
            component="OnArticleUpdatedFromFeedHandler",
        )
    
    async def handle(self, event: ArticleUpdatedFromFeed) -> None:
        """
        Re-ejecuta pipeline de procesamiento para artículo actualizado.
        
        Si el contenido cambió, re-procesa:
        - Scraping (si URL cambió)
        - Plaintext extraction
        - Markdown conversion
        - Metrics calculation
        - Language detection
        - Summary generation
        - Keywords extraction
        - Quality calculation
        - AI processing (embeddings)
        """
        self._logger.info(
            "Artículo actualizado desde feed, re-procesando",
            article_id=event.article_id,
            updated_fields=event.updated_fields,
        )
        
        # Si el contenido o URL cambió, re-scrapear
        if 'content' in event.updated_fields or 'url' in event.updated_fields:
            from src.article.app.commands.scrape_article_content import (
                ScrapeArticleContentCommand,
            )
            
            await self._command_bus.send(
                ScrapeArticleContentCommand(
                    article_id=event.article_id,
                    correlation_id=f"update-{event.article_id}",
                    triggered_by="article_updated_from_feed",
                )
            )
        else:
            # Si solo cambió metadata, re-procesar desde plaintext
            from src.article.app.commands.extract_article_plaintext import (
                ExtractArticlePlaintextCommand,
            )
            
            await self._command_bus.send(
                ExtractArticlePlaintextCommand(
                    article_id=event.article_id,
                    correlation_id=f"update-{event.article_id}",
                    triggered_by="article_updated_from_feed",
                )
            )
```

## Data Models

### ArticleDTO (Sin cambios)

El DTO ya incluye todos los campos necesarios incluyendo `rss_guid` y `pub_date`.

### ArticleModel (Sin cambios)

El modelo ORM ya tiene:
- `rss_guid` (String(500), indexed)
- `pub_date` (DateTime, indexed)

## Correctness Properties

*Una property es una característica o comportamiento que debe mantenerse verdadero en todas las ejecuciones válidas del sistema.*

### Property 1: GUID match es prioritario

*Para cualquier* ArticleData con GUID, si existe un artículo con el mismo GUID y source_id, debe detectarse como duplicado antes de verificar por URL.

**Validates: Requirements 1.1, 1.2**

### Property 2: URL match es fallback

*Para cualquier* ArticleData sin GUID o sin match por GUID, si existe un artículo con la misma URL y source_id, debe detectarse como duplicado.

**Validates: Requirements 2.1, 2.2**

### Property 3: Similitud de contenido no se usa

*Para cualquier* par de artículos con contenido similar pero URLs diferentes, ambos deben permitirse en el sistema.

**Validates: Requirements 3.1, 3.2, 3.3**

### Property 4: Actualización detectada por pub_date

*Para cualquier* ArticleData con GUID que matchea un artículo existente, si pub_date nuevo > pub_date existente, debe marcarse como actualización (is_update=True).

**Validates: Requirements 4.1, 4.2**

### Property 5: Actualización re-procesa contenido

*Para cualquier* artículo actualizado desde feed, el sistema debe re-ejecutar el pipeline de procesamiento completo.

**Validates: Requirements 9.3, 9.4**

### Property 6: Artículos sin GUID funcionan

*Para cualquier* ArticleData sin GUID, el sistema debe funcionar correctamente usando solo deduplicación por URL.

**Validates: Requirements 1.4, Compatibility**

### Property 7: Match method es correcto

*Para cualquier* detección de duplicado, el match_method retornado debe corresponder al método que encontró el duplicado ('guid' o 'url').

**Validates: Requirements 7.4, 7.5**

### Property 8: Configuración de updates respetada

*Para cualquier* detección de actualización, si enable_updates=False, debe tratarse como duplicado exacto (is_update=False).

**Validates: Requirements 10.2, 10.3**

## Error Handling

### Errores en find_by_guid

- **Error de DB**: Loggear y lanzar excepción
- **GUID inválido**: Continuar con verificación por URL
- **Timeout**: Loggear y lanzar excepción

### Errores en UpdateArticleFromFeedHandler

- **Artículo no encontrado**: Retornar UpdateArticleFromFeedResult.not_found()
- **Error de validación**: Retornar UpdateArticleFromFeedResult.failure()
- **Error de persistencia**: Rollback automático, loggear y lanzar excepción

### Errores en re-procesamiento

- **Error en pipeline**: Loggear pero no detener el flujo
- **Comando falla**: Loggear y continuar con siguiente paso

## Testing Strategy

### Unit Tests

1. **ArticleDeduplicationService**
   - Test: GUID match detecta duplicado
   - Test: URL match detecta duplicado cuando no hay GUID
   - Test: pub_date posterior marca como update
   - Test: pub_date anterior marca como duplicate
   - Test: Sin GUID usa solo URL
   - Test: enable_updates=False nunca marca update

2. **UpdateArticleFromFeedHandler**
   - Test: Actualiza campos modificados
   - Test: No actualiza campos sin cambios
   - Test: Emite ArticleUpdatedFromFeed event
   - Test: Retorna not_found si artículo no existe

3. **Article.update_from_feed()**
   - Test: Actualiza título si cambió
   - Test: Actualiza contenido si cambió
   - Test: No actualiza si valores son iguales
   - Test: Emite evento con campos actualizados

### Integration Tests

1. **find_by_guid()**
   - Test: Encuentra artículo por GUID y source
   - Test: Retorna None si no existe
   - Test: Funciona sin source_id (busca en todas)

2. **Flujo completo de actualización**
   - Test: Detecta update → Ejecuta comando → Re-procesa contenido
   - Test: Detecta duplicate → Skip artículo

### Property-Based Tests

1. **Property: GUID prioritario**
   - Generar ArticleData con GUID
   - Verificar que siempre se busca por GUID primero

2. **Property: pub_date determina update**
   - Generar pares de pub_dates
   - Verificar que nuevo > existente → update

## Configuration

### Variables de Entorno

```bash
# Habilitar actualizaciones de artículos
RSS_ENABLE_ARTICLE_UPDATES=true  # default: true

# Habilitar deduplicación por URL (existente)
RSS_ENABLE_URL_DUPLICATE_CHECK=true  # default: true
```

### RssConfig (Actualizado)

```python
# src/shared/config/rss_config.py

@dataclass
class RssConfig:
    """Configuración para RSS scraping."""
    
    # Existente
    enable_duplicate_url_check: bool = True
    
    # Nuevo
    enable_article_updates: bool = True
    
    def __post_init__(self):
        # Existente
        self.enable_duplicate_url_check = (
            os.getenv("RSS_ENABLE_URL_DUPLICATE_CHECK", "true").lower() == "true"
        )
        
        # Nuevo
        self.enable_article_updates = (
            os.getenv("RSS_ENABLE_ARTICLE_UPDATES", "true").lower() == "true"
        )
```

## Migration Strategy

### Fase 1: Agregar find_by_guid al Repository

1. Agregar método a IArticleReadRepository
2. Implementar en ArticleReadRepository
3. Tests unitarios e integración

### Fase 2: Refactorizar ArticleDeduplicationService

1. Eliminar similarity_threshold del constructor
2. Eliminar métodos de similitud de contenido
3. Agregar check_duplicate() con retorno extendido
4. Agregar _check_by_guid() y _check_by_url()
5. Agregar _is_article_update()
6. Tests unitarios

### Fase 3: Implementar UpdateArticleFromFeedCommand

1. Crear command, handler, result
2. Implementar Article.update_from_feed()
3. Crear ArticleUpdatedFromFeed event
4. Tests unitarios

### Fase 4: Implementar OnArticleUpdatedFromFeedHandler

1. Crear event handler
2. Registrar en event bus
3. Tests de integración

### Fase 5: Actualizar ScrapingCoordinator

1. Usar nuevo check_duplicate() con 4 valores de retorno
2. Manejar is_update=True → emitir UpdateArticleFromFeedCommand
3. Manejar is_duplicate=True, is_update=False → skip
4. Tests de integración

### Fase 6: Configuración y Observability

1. Agregar RSS_ENABLE_ARTICLE_UPDATES a config
2. Agregar logging detallado
3. Agregar métricas

## Performance Considerations

### Índices Existentes

- `idx_articles_rss_guid` ya existe (no requiere migración)
- `idx_articles_pub_date` ya existe (no requiere migración)

### Query Performance

- `find_by_guid()`: < 50ms (índice en rss_guid)
- `find_by_url_and_source()`: < 50ms (índice único existente)
- Total deduplicación: < 100ms (2 queries máximo)

### Eliminación de Similitud

- **Antes**: calculate_similarity() podía tomar 200-500ms por comparación
- **Después**: Solo queries indexadas (< 100ms total)
- **Mejora**: 5-10x más rápido

## Observability

### Logging

```python
# Detección de duplicado
logger.info(
    "Duplicado detectado",
    article_id=duplicate_id,
    match_method=match_method,  # 'guid' o 'url'
    is_update=is_update,
    url=article_data.url,
    guid=article_data.guid,
)

# Actualización de artículo
logger.info(
    "Artículo actualizado desde feed",
    article_id=article_id,
    updated_fields=updated_fields,
    old_pub_date=old_pub_date,
    new_pub_date=new_pub_date,
)

# Skip por duplicado
logger.info(
    "Artículo duplicado, skipping",
    duplicate_id=duplicate_id,
    match_method=match_method,
    url=article_data.url,
)
```

### Métricas

- `articles.duplicates.detected` (counter, tags: match_method)
- `articles.updates.processed` (counter)
- `articles.deduplication.duration` (histogram, tags: match_method)
- `articles.updates.duration` (histogram)

## Backward Compatibility

### Artículos sin GUID

- Funcionan normalmente con deduplicación por URL
- No se ven afectados por el cambio

### Artículos Existentes

- No requieren migración
- Continúan funcionando con deduplicación por URL
- Si el feed empieza a proporcionar GUID, se usará en futuros fetches

### API Pública

- No hay cambios breaking en interfaces públicas
- ArticleDeduplicationService mantiene compatibilidad (solo elimina métodos no usados)

## Future Enhancements

### Posibles Mejoras Futuras

1. **Cross-Source Deduplication**: Detectar mismo GUID en diferentes sources
2. **Merge de Duplicados**: UI para mergear artículos duplicados existentes
3. **Historial de Actualizaciones**: Trackear versiones de artículos
4. **Notificaciones**: Alertar cuando artículos importantes se actualizan
5. **Deduplicación Semántica Opcional**: Usar embeddings para detectar duplicados semánticos (sin eliminarlos, solo marcarlos)
