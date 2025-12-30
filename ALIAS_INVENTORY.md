# Inventario Completo de Alias en src/

**Fecha**: 15 de Diciembre, 2024

## 📋 Resumen Ejecutivo

Se identificaron **68 alias** en el directorio `src/`, distribuidos en diferentes bounded contexts y capas arquitectónicas.

## 📊 Estadísticas Generales

| Categoría | Cantidad | Propósito |
|-----------|----------|-----------|
| **Shared Kernel** | 8 | Compatibilidad legacy |
| **RSS Article** | 35 | Migración Article → RssArticle |
| **RSS Feed** | 14 | Migración Source → RssFeed |
| **Chunking** | 2 | Migración ContentChunk → KnowledgeChunk |
| **Otros** | 9 | Varios |
| **TOTAL** | **68** | - |

---

## 🔍 Análisis Detallado por Bounded Context

### 1. Shared Kernel (8 alias)

#### 1.1 Domain Events
**Archivo**: `src/shared/kernel/domain_event.py:68`
```python
IDomainEvent = IDomainEvent  # ⚠️ Auto-referencia (posible error)
```
**Acción**: ❓ Verificar si es necesario o eliminar

#### 1.2 Event Publishers
**Archivo**: `src/shared/infra/event_bus/event_publisher_with_dispatch.py:109`
```python
# Legacy compatibility alias - DEPRECATED
EnhancedDomainEventPublisher = EventPublisherWithDispatch
```
**Acción**: ⚠️ Eliminar (marcado como DEPRECATED)

**Archivo**: `src/shared/infra/event_bus/in_memory_event_publisher.py:8`
```python
# Type alias para compatibilidad
Event = IDomainEvent
```
**Acción**: ✅ Mantener (type alias útil)

**Archivo**: `src/shared/infra/event_bus/in_memory_event_publisher.py:92`
```python
# Legacy compatibility alias - DEPRECATED
InMemoryDomainEventPublisher = InMemoryEventPublisher
```
**Acción**: ⚠️ Eliminar (marcado como DEPRECATED)

**Archivo**: `src/shared/infra/event_bus/event_publisher.py:12`
```python
# Type alias para compatibilidad
Event = IDomainEvent
```
**Acción**: ✅ Mantener (type alias útil)

**Archivo**: `src/shared/infra/event_bus/event_publisher.py:389-392`
```python
# Legacy compatibility aliases - DEPRECATED
LoggingDomainEventPublisher = EventPublisher
create_domain_event_publisher = create_event_publisher
get_domain_event_publisher = get_event_publisher
set_domain_event_publisher = set_event_publisher
```
**Acción**: ⚠️ Eliminar (4 alias marcados como DEPRECATED)

#### 1.3 Unit of Work
**Archivo**: `src/shared/infra/persistence/sqlalchemy_uow.py:154`
```python
# Alias para backward compatibility
UnitOfWork = SqlAlchemyUnitOfWork
```
**Acción**: ⚠️ Evaluar uso y considerar eliminar

#### 1.4 Quality Threshold
**Archivo**: `src/shared/domain/value_objects/quality_threshold.py:120-123`
```python
# Backward compatibility: exponer 'score' como alias de 'value'
@property
def score(self) -> float:
    return self.value
```
**Acción**: ✅ Mantener (property alias útil)

---

### 2. RSS Article Bounded Context (35 alias)

#### 2.1 Aggregate
**Archivo**: `src/rss/article/domain/aggregates/rss_article.py:562`
```python
# Alias para compatibilidad
Article = RssArticle
```
**Acción**: ⚠️ Evaluar uso y considerar eliminar

#### 2.2 Factories
**Archivo**: `src/rss/article/domain/interfaces/factories/article_factory.py:12`
```python
# Alias para compatibilidad
Article = RssArticle
```
**Acción**: ⚠️ Evaluar uso y considerar eliminar

**Archivo**: `src/rss/article/domain/interfaces/factories/article_factory.py:108`
```python
# Alias para compatibilidad
IArticleFactory = IRssArticleFactory
```
**Acción**: ⚠️ Evaluar uso y considerar eliminar

**Archivo**: `src/rss/article/domain/factories/__init__.py:10`
```python
# Alias para compatibilidad
ArticleFactory = RssArticleFactory
```
**Acción**: ⚠️ Evaluar uso y considerar eliminar

#### 2.3 Repositories
**Archivo**: `src/rss/article/domain/interfaces/repositories/__init__.py:11-12`
```python
# Aliases para compatibilidad
IArticleReadRepository = IRssArticleReadRepository
IArticleWriteRepository = IRssArticleWriteRepository
```
**Acción**: ⚠️ Evaluar uso y considerar eliminar (2 alias)

#### 2.4 Value Objects - Metadata (9 alias)
**Archivo**: `src/rss/article/domain/value_objects/metadata/__init__.py:31-39`
```python
# Aliases para compatibilidad
ArticleId = RssArticleId
ArticleUrl = RssArticleUrl
ArticleAuthor = RssArticleAuthor
ArticleContent = RssArticleContent
ArticleDescription = RssArticleDescription
ArticleGuid = RssArticleGuid
ArticlePubDate = RssArticlePubDate
ArticleSummary = RssArticleSummary
ArticleTimestamps = RssArticleTimestamps
```
**Acción**: ⚠️ Evaluar uso y considerar eliminar (9 alias)

**Archivo**: `src/rss/article/domain/value_objects/metadata/rss_article_id.py:108`
```python
# Alias para compatibilidad
ArticleId = RssArticleId
```
**Acción**: ⚠️ Duplicado del anterior

**Archivo**: `src/rss/article/domain/value_objects/metadata/rss_article_url.py:109`
```python
# Alias para compatibilidad
ArticleUrl = RssArticleUrl
```
**Acción**: ⚠️ Duplicado del anterior

#### 2.5 Value Objects - Analysis (5 alias)
**Archivo**: `src/rss/article/domain/value_objects/deduplication_result.py:41`
```python
# Alias para compatibilidad
ArticleDeduplicationResult = RssArticleDeduplicationResult
```
**Acción**: ⚠️ Evaluar uso y considerar eliminar

**Archivo**: `src/rss/article/domain/value_objects/analysis/quality.py:199`
```python
# Alias para compatibilidad
ArticleQuality = RssArticleQuality
```
**Acción**: ⚠️ Evaluar uso y considerar eliminar

**Archivo**: `src/rss/article/domain/value_objects/analysis/duplicate.py:143`
```python
# Alias para compatibilidad
ArticleDuplicate = RssArticleDuplicate
```
**Acción**: ⚠️ Evaluar uso y considerar eliminar

**Archivo**: `src/rss/article/domain/value_objects/analysis/error.py:236`
```python
# Alias para compatibilidad
ArticleError = RssArticleError
```
**Acción**: ⚠️ Evaluar uso y considerar eliminar

**Archivo**: `src/rss/article/domain/value_objects/analysis/metrics.py:130`
```python
# Alias para compatibilidad
ArticleMetrics = RssArticleMetrics
```
**Acción**: ⚠️ Evaluar uso y considerar eliminar

#### 2.6 Container
**Archivo**: `src/rss/article/container.py:1046`
```python
# Alias para compatibilidad
ArticleContainer = RssArticleContainer
```
**Acción**: ⚠️ Evaluar uso y considerar eliminar

#### 2.7 Process Managers (2 alias)
**Archivo**: `src/rss/article/app/process_managers/content_extraction_pipeline.py:282`
```python
# Alias para compatibilidad
ArticleContentExtractionPipeline = RssArticleContentExtractionPipeline
```
**Acción**: ⚠️ Evaluar uso y considerar eliminar

**Archivo**: `src/rss/article/app/process_managers/content_analysis_pipeline.py:481`
```python
# Alias para compatibilidad
ArticleContentAnalysisPipeline = RssArticleContentAnalysisPipeline
```
**Acción**: ⚠️ Evaluar uso y considerar eliminar

#### 2.8 Queries
**Archivo**: `src/rss/article/app/queries/get_by_id/result.py:9`
```python
# Alias para mantener compatibilidad con código existente
ArticleDTO = ArticleReadModel
```
**Acción**: ⚠️ Evaluar uso y considerar eliminar

#### 2.9 Mappers (4 alias)
**Archivo**: `src/rss/article/infra/persistence/mappers/rss_article_mapper.py:18-20`
```python
# Alias para compatibilidad
ArticleId = RssArticleId
Article = RssArticle
```
**Acción**: ⚠️ Evaluar uso y considerar eliminar (2 alias)

**Archivo**: `src/rss/article/infra/persistence/mappers/__init__.py:10-12`
```python
# Aliases para compatibilidad
ArticleMapper = RssArticleMapper
ArticleReadModelMapper = RssArticleReadModelMapper
```
**Acción**: ⚠️ Evaluar uso y considerar eliminar (2 alias)

---

### 3. RSS Feed Bounded Context (14 alias)

#### 3.1 Aggregate
**Archivo**: `src/rss/feed/domain/aggregates/__init__.py:6`
```python
# Alias para compatibilidad hacia atrás
Source = RssFeed
```
**Acción**: ⚠️ Evaluar uso y considerar eliminar

#### 3.2 Repositories
**Archivo**: `src/rss/feed/domain/interfaces/repositories/__init__.py:7-8`
```python
# Aliases para compatibilidad
ISourceReadRepository = IRssFeedReadRepository
ISourceWriteRepository = IRssFeedWriteRepository
```
**Acción**: ⚠️ Evaluar uso y considerar eliminar (2 alias)

#### 3.3 Events
**Archivo**: `src/rss/feed/domain/events/created.py:98`
```python
# Alias para compatibilidad hacia atrás
SourceCreated = RssFeedCreated
```
**Acción**: ⚠️ Evaluar uso y considerar eliminar

#### 3.4 Value Objects (10 alias)
**Archivo**: `src/rss/feed/domain/value_objects/status.py:218`
```python
# Alias para compatibilidad hacia atrás
SourceStatus = RssFeedStatus
```
**Acción**: ⚠️ Evaluar uso y considerar eliminar

**Archivo**: `src/rss/feed/domain/value_objects/name.py:92`
```python
# Alias para compatibilidad hacia atrás
SourceName = RssFeedName
```
**Acción**: ⚠️ Evaluar uso y considerar eliminar

**Archivo**: `src/rss/feed/domain/value_objects/source_health.py:146`
```python
# Alias para compatibilidad hacia atrás
SourceHealth = RssFeedHealth
```
**Acción**: ⚠️ Evaluar uso y considerar eliminar

**Archivo**: `src/rss/feed/domain/value_objects/source_metadata.py:139`
```python
# Alias para compatibilidad hacia atrás
SourceMetadata = RssFeedMetadata
```
**Acción**: ⚠️ Evaluar uso y considerar eliminar

**Archivo**: `src/rss/feed/domain/value_objects/rss_feed_id.py:77`
```python
# Alias para compatibilidad hacia atrás
SourceId = RssFeedId
```
**Acción**: ⚠️ Evaluar uso y considerar eliminar

**Archivo**: `src/rss/feed/domain/value_objects/source_identity.py:100`
```python
# Alias para compatibilidad hacia atrás
SourceIdentity = RssFeedIdentity
```
**Acción**: ⚠️ Evaluar uso y considerar eliminar

**Archivo**: `src/rss/feed/domain/value_objects/rss_feed_url.py:122-123`
```python
# Alias para compatibilidad hacia atrás
RssUrl = RssFeedUrl
SourceUrl = RssFeedUrl
```
**Acción**: ⚠️ Evaluar uso y considerar eliminar (2 alias)

**Archivo**: `src/rss/feed/domain/value_objects/metrics.py:223-224`
```python
# Alias para compatibilidad hacia atrás
SourceMetrics = RssFeedMetrics
RssSourceMetrics = RssFeedMetrics
```
**Acción**: ⚠️ Evaluar uso y considerar eliminar (2 alias)

---

### 4. Chunking Bounded Context (2 alias)

**Archivo**: `src/chunking/domain/services/chunking.py:14`
```python
# Alias for backward compatibility
ContentChunk = KnowledgeChunk
```
**Acción**: ⚠️ Evaluar uso y considerar eliminar

**Archivo**: `src/chunking/domain/aggregates/__init__.py:6`
```python
# Alias for backward compatibility
ContentChunk = KnowledgeChunk
```
**Acción**: ⚠️ Evaluar uso y considerar eliminar

---

## 🎯 Recomendaciones por Prioridad

### 🔴 Alta Prioridad - Eliminar Inmediatamente (7 alias)

Estos alias están marcados explícitamente como **DEPRECATED**:

1. ✅ ~~`IRssFetcherService`~~ - YA ELIMINADO
2. ✅ ~~`FetchSessionMapper`~~ - YA ELIMINADO
3. ⚠️ `EnhancedDomainEventPublisher` → `EventPublisherWithDispatch`
4. ⚠️ `InMemoryDomainEventPublisher` → `InMemoryEventPublisher`
5. ⚠️ `LoggingDomainEventPublisher` → `EventPublisher`
6. ⚠️ `create_domain_event_publisher` → `create_event_publisher`
7. ⚠️ `get_domain_event_publisher` → `get_event_publisher`
8. ⚠️ `set_domain_event_publisher` → `set_event_publisher`

### 🟡 Media Prioridad - Evaluar Uso (59 alias)

Estos alias son para "compatibilidad" pero deberían evaluarse:

#### RSS Article (35 alias)
- Aggregate: `Article` → `RssArticle`
- Factories: `IArticleFactory`, `ArticleFactory`
- Repositories: `IArticleReadRepository`, `IArticleWriteRepository`
- Value Objects: 9 metadata + 5 analysis
- Container: `ArticleContainer`
- Process Managers: 2 alias
- Queries: `ArticleDTO`
- Mappers: 4 alias

#### RSS Feed (14 alias)
- Aggregate: `Source` → `RssFeed`
- Repositories: 2 alias
- Events: `SourceCreated`
- Value Objects: 10 alias

#### Chunking (2 alias)
- `ContentChunk` → `KnowledgeChunk`

#### Shared (2 alias)
- `UnitOfWork` → `SqlAlchemyUnitOfWork`
- `IDomainEvent = IDomainEvent` (auto-referencia)

### 🟢 Baja Prioridad - Mantener (2 alias)

Estos son type alias útiles:

1. ✅ `Event = IDomainEvent` (en event publishers)
2. ✅ `score` property como alias de `value` (en QualityThreshold)

---

## 📝 Plan de Acción Sugerido

### Fase 1: Eliminar DEPRECATED (Inmediato)

```bash
# 1. Verificar uso de alias deprecated
grep -r "EnhancedDomainEventPublisher" src/
grep -r "InMemoryDomainEventPublisher" src/
grep -r "LoggingDomainEventPublisher" src/
grep -r "create_domain_event_publisher" src/
grep -r "get_domain_event_publisher" src/
grep -r "set_domain_event_publisher" src/

# 2. Si no hay uso, eliminar
```

### Fase 2: Evaluar Alias de Migración (1-2 semanas)

Para cada bounded context:

1. **Buscar uso del alias**:
   ```bash
   grep -r "Article = RssArticle" src/
   grep -r "^Article[^a-z]" src/  # Buscar uso de Article
   ```

2. **Si hay uso**:
   - Actualizar imports a usar nombre nuevo
   - Eliminar alias

3. **Si no hay uso**:
   - Eliminar alias directamente

### Fase 3: Documentar Decisiones

Crear documento con:
- Alias eliminados
- Alias mantenidos (con justificación)
- Guía de migración para desarrolladores

---

## 🔍 Comandos Útiles para Verificación

### Buscar uso de un alias específico
```bash
# Ejemplo: Buscar uso de "Article" (no "RssArticle")
grep -r "from.*import.*Article[^a-zA-Z]" src/
grep -r "Article\." src/ | grep -v "RssArticle"
```

### Contar referencias
```bash
# Contar cuántas veces se usa el alias
grep -r "Article = RssArticle" src/ | wc -l
```

### Verificar imports
```bash
# Ver todos los imports de un módulo
grep -r "from src.rss.article" src/
```

---

## 📊 Resumen Final

| Estado | Cantidad | Acción |
|--------|----------|--------|
| ✅ Eliminados | 2 | IRssFetcherService, FetchSessionMapper |
| ⚠️ DEPRECATED | 6 | Eliminar inmediatamente |
| ⚠️ Evaluar | 59 | Verificar uso y considerar eliminar |
| ✅ Mantener | 2 | Type alias útiles |
| **TOTAL** | **69** | - |

---

**Generado**: 15 de Diciembre, 2024
**Última actualización**: Después de eliminar 2 alias
