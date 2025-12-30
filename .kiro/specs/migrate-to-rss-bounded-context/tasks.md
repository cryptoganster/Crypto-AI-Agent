# Implementation Plan

## Overview

Este plan de implementación describe los pasos para migrar los bounded contexts `source/` y `article/` a la nueva estructura `src/rss/feed/` y `src/rss/article/`. La migración se realizará de forma incremental usando comandos bash simples para minimizar riesgos.

## Task List

- [x] 1. Crear estructura de directorios para RSS bounded context
  - Crear `src/rss/` como bounded context principal
  - Crear `src/rss/feed/` como sub-BC para feeds RSS
  - Crear `src/rss/article/` como sub-BC para artículos RSS
  - Crear `src/rss/shared/` para conceptos compartidos
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_

- [x] 2. Copiar bounded context Source a RssFeed
  - Copiar `src/source/` → `src/rss/feed/`
  - Mantener estructura completa (app, domain, infra)
  - Preservar todos los archivos y directorios
  - _Requirements: 14.1, 14.2_

- [x] 3. Copiar bounded context Article a RssArticle
  - Copiar `src/article/` → `src/rss/article/`
  - Mantener estructura completa (app, domain, infra)
  - Preservar todos los archivos y directorios
  - _Requirements: 14.1, 14.2_

- [x] 4. Renombrar archivos en src/rss/feed/
  - Renombrar `source.py` → `rss_feed.py`
  - Renombrar `source_id.py` → `rss_feed_id.py`
  - Renombrar `source_url.py` → `rss_feed_url.py`
  - Renombrar `source_model.py` → `rss_feed_model.py`
  - Renombrar `source_mapper.py` → `rss_feed_mapper.py`
  - Renombrar `source_factory.py` → `rss_feed_factory.py`
  - Renombrar todos los archivos de repositories con prefijo "rss_feed"
  - Renombrar directorios de commands: `create_source/` → `create/`, `update_source/` → `update/`, etc.
  - Renombrar directorios de queries sin prefijo redundante
  - Los eventos NO llevan prefijo (ya están en `src/rss/feed/domain/events/`)
  - _Requirements: 2.4, 3.1, 3.3, 4.5, 5.5, 6.5, 7.4, 8.4, 9.4_

- [x] 5. Renombrar archivos en src/rss/article/
  - Renombrar `article.py` → `rss_article.py`
  - Renombrar `article_id.py` → `rss_article_id.py`
  - Renombrar `article_url.py` → `rss_article_url.py`
  - Renombrar `article_model.py` → `rss_article_model.py`
  - Renombrar `article_mapper.py` → `rss_article_mapper.py`
  - Renombrar `article_factory.py` → `rss_article_factory.py`
  - Renombrar todos los archivos de repositories con prefijo "rss_article"
  - Renombrar directorios de commands sin prefijo redundante (ya están en `src/rss/article/app/commands/`)
  - Renombrar directorios de queries sin prefijo redundante (ya están en `src/rss/article/app/queries/`)
  - Los eventos NO llevan prefijo (ya están en `src/rss/article/domain/events/`)
  - _Requirements: 2.4, 3.2, 3.4, 4.5, 5.5, 6.5, 7.4, 8.4, 9.4_

- [x] 6. Renombrar clases en src/rss/feed/
  - Renombrar clase `Source` → `RssFeed`
  - Renombrar clase `SourceId` → `RssFeedId`
  - Renombrar clase `SourceUrl` → `RssFeedUrl`
  - Renombrar clase `SourceModel` → `RssFeedModel`
  - Renombrar clase `SourceMapper` → `RssFeedMapper`
  - Renombrar clase `SourceFactory` → `RssFeedFactory`
  - Renombrar clase `SourceCreated` → `RssFeedCreated`
  - Renombrar clase `SourceUpdated` → `RssFeedUpdated`
  - Renombrar clase `CreateSourceCommand` → `CreateRssFeedCommand`
  - Renombrar clase `UpdateSourceCommand` → `UpdateRssFeedCommand`
  - Renombrar clase `GetSourceByIdQuery` → `GetRssFeedByIdQuery`
  - Renombrar clase `ISourceReadRepository` → `IRssFeedReadRepository`
  - Renombrar clase `ISourceWriteRepository` → `IRssFeedWriteRepository`
  - Renombrar clase `SqlAlchemySourceReadRepository` → `RssFeedReadRepository`
  - Renombrar clase `SqlAlchemySourceWriteRepository` → `RssFeedWriteRepository`
  - _Requirements: 2.1, 2.2, 2.3, 2.5, 3.1, 3.5, 4.1, 4.2, 4.4, 5.1, 5.2, 5.4, 6.1, 6.2, 6.5, 7.1, 7.2, 7.5, 8.1, 8.2, 8.5, 9.1, 9.2, 9.5_

- [x] 7. Renombrar clases en src/rss/article/
  - Renombrar clase `Article` → `RssArticle`
  - Renombrar clase `ArticleId` → `RssArticleId`
  - Renombrar clase `ArticleUrl` → `RssArticleUrl`
  - Renombrar clase `ArticleModel` → `RssArticleModel`
  - Renombrar clase `ArticleMapper` → `RssArticleMapper`
  - Renombrar clase `ArticleFactory` → `RssArticleFactory`
  - Renombrar clase `ArticleCreated` → `RssArticleCreated`
  - Renombrar clase `ArticleContentScraped` → `RssArticleContentScraped`
  - Renombrar clase `CreateArticleCommand` → `CreateRssArticleCommand`
  - Renombrar clase `ScrapeArticleContentCommand` → `ScrapeRssArticleContentCommand`
  - Renombrar clase `GetArticleByIdQuery` → `GetRssArticleByIdQuery`
  - Renombrar clase `IArticleReadRepository` → `IRssArticleReadRepository`
  - Renombrar clase `IArticleWriteRepository` → `IRssArticleWriteRepository`
  - Renombrar clase `SqlAlchemyArticleReadRepository` → `RssArticleReadRepository`
  - Renombrar clase `SqlAlchemyArticleWriteRepository` → `RssArticleWriteRepository`
  - _Requirements: 2.1, 2.2, 2.3, 2.5, 3.2, 3.5, 4.2, 4.3, 4.4, 5.2, 5.3, 5.4, 6.3, 6.4, 6.5, 7.1, 7.2, 7.5, 8.1, 8.2, 8.5, 9.2, 9.3, 9.5_

- [x] 7.1. Completar renombramientos de clases restantes en src/rss/feed/
  - Renombrar clases de Value Objects que aún tienen prefijo `Source`:
    - `SourceConfiguration` → `RssFeedConfiguration`
    - `SourceMetrics` → `RssFeedMetrics`
    - `SourceDescription` → `RssFeedDescription`
    - `SourceIdentity` → `RssFeedIdentity`
    - `SourceMetadata` → `RssFeedMetadata`
    - `SourceHealth` → `RssFeedHealth`
    - `SourceName` → `RssFeedName`
    - `SourceStatus` → `RssFeedStatus`
  - Renombrar clases de Excepciones con prefijo `Source`
  - Renombrar clases de DTOs con prefijo `Source`
  - Renombrar clases de Services con prefijo `Source`
  - Renombrar `SourceMapper` → `RssFeedMapper`
  - Renombrar eventos adicionales con prefijo `Source`
  - _Requirements: 2.1, 2.2, 2.3, 2.5, 3.1, 3.5, 6.1, 6.2, 6.5_

- [x] 7.2. Completar renombramientos de clases restantes en src/rss/article/
  - Renombrar clases de Value Objects que aún tienen prefijo `Article`:
    - `ArticleMetrics` → `RssArticleMetrics`
    - `ArticleError` → `RssArticleError`
    - `ArticleAnalysis` → `RssArticleAnalysis`
    - `ArticleDuplicate` → `RssArticleDuplicate`
    - `ArticleQuality` → `RssArticleQuality`
    - `ArticleDeduplicationResult` → `RssArticleDeduplicationResult`
    - `ArticleDescription` → `RssArticleDescription`
    - `ArticlePubDate` → `RssArticlePubDate`
    - `ArticleTimestamps` → `RssArticleTimestamps`
    - `ArticleAuthor` → `RssArticleAuthor`
    - `ArticleMetadata` → `RssArticleMetadata`
    - `ArticleGuid` → `RssArticleGuid`
    - `ArticleSummary` → `RssArticleSummary`
    - `ArticleContent` → `RssArticleContent`
  - Renombrar clases de Excepciones con prefijo `Article`
  - Renombrar clases de Services con prefijo `Article`
  - Renombrar clases de Process Managers con prefijo `Article`
  - Renombrar `ArticleContainer` → `RssArticleContainer`
  - _Requirements: 2.1, 2.2, 2.3, 2.5, 3.2, 3.5, 6.3, 6.4, 6.5_

- [x] 7.3. Actualizar todas las importaciones de src.source a src.rss.feed
  - Buscar todas las importaciones `from src.source` en todo el proyecto (≈182 ocurrencias)
  - Actualizar a `from src.rss.feed`
  - Verificar en: src/, tests/, scripts/
  - Actualizar imports en containers de DI
  - Actualizar imports en otros bounded contexts (knowledge, rag, scraping)
  - Verificar que no queden referencias a src.source
  - _Requirements: 12.1, 12.3, 12.4, 12.5_

- [x] 7.4. Actualizar todas las importaciones de src.article a src.rss.article
  - Buscar todas las importaciones `from src.article` en todo el proyecto (≈311 ocurrencias)
  - Actualizar a `from src.rss.article`
  - Verificar en: src/, tests/, scripts/
  - Actualizar imports en containers de DI
  - Actualizar imports en otros bounded contexts (knowledge, rag, scraping)
  - Verificar que no queden referencias a src.article
  - _Requirements: 12.2, 12.3, 12.4, 12.5_

- [x] 8. Actualizar imports internos en src/rss/feed/
  - Actualizar imports de `from src.source.` → `from src.rss.feed.`
  - Actualizar imports de aggregates, value objects, events
  - Actualizar imports de repositories, factories, mappers
  - Actualizar imports de commands, queries, handlers
  - Verificar que no queden imports del path antiguo
  - _Requirements: 12.1, 12.5_

- [x] 9. Actualizar imports internos en src/rss/article/
  - Actualizar imports de `from src.article.` → `from src.rss.article.`
  - Actualizar imports de aggregates, value objects, events
  - Actualizar imports de repositories, factories, mappers
  - Actualizar imports de commands, queries, handlers
  - Verificar que no queden imports del path antiguo
  - _Requirements: 12.2, 12.5_

- [x] 10. Crear SourceReference value object en src/knowledge/
  - Crear `src/knowledge/domain/value_objects/source_reference.py`
  - Implementar SourceReference con source_type, source_id, source_url
  - Validar source_types conocidos (rss_article, tweet, pdf_document, etc.)
  - Agregar métodos helper (is_rss_article(), is_tweet(), etc.)
  - Documentar con ejemplos de uso
  - _Requirements: 13.4_

- [x] 11. Actualizar KnowledgeChunk para usar SourceReference
  - Reemplazar `article_id: str` con `source: SourceReference`
  - Actualizar constructor de KnowledgeChunk
  - Actualizar métodos que usan article_id
  - Actualizar eventos para incluir source_type
  - Actualizar validaciones de invariantes
  - _Requirements: 13.4_

- [x] 11.1. Actualizar interfaces de servicios de chunking para usar SourceReference
  - Actualizar `IChunkingService.chunk_text()` para aceptar SourceReference
  - Actualizar `IChunkValidationService` para validar SourceReference
  - Actualizar `IVectorStore.store_chunks()` para usar source_id y source_type
  - Actualizar `IVectorStore.get_tldrs()` para usar source_ids
  - Actualizar `IVectorStore.delete_chunks()` para usar source_id
  - Actualizar documentación de interfaces
  - _Requirements: 13.4_

- [x] 11.2. Actualizar implementaciones de servicios de chunking
  - Actualizar `ChunkingService.chunk_text()` para crear chunks con SourceReference
  - Actualizar `ChunkValidationService` para validar source consistency
  - Actualizar creación de chunks en el servicio para usar SourceReference
  - Verificar que todos los métodos usen source en lugar de article_id
  - _Requirements: 13.4_

- [x] 11.3. Actualizar repositorios de chunks para usar SourceReference
  - Actualizar `IContentChunkReadRepository.find_by_article_id()` → `find_by_source()`
  - Actualizar queries para filtrar por source_id y source_type
  - Actualizar mappers para convertir entre SourceReference y modelo ORM
  - Actualizar modelos ORM para incluir source_type
  - Crear migración de base de datos para agregar columna source_type
  - _Requirements: 13.4, 9.3_

- [x] 11.4. Actualizar command handlers de chunking
  - Actualizar `ChunkArticleCommand` para aceptar source_type
  - Actualizar `ChunkArticleHandler` para crear SourceReference
  - Actualizar validaciones en handlers para usar SourceReference
  - Actualizar result objects para incluir source information
  - _Requirements: 13.4_

- [x] 11.5. Actualizar tests de chunking para usar SourceReference
  - Actualizar `test_chunk_article_handler.py` para usar SourceReference
  - Actualizar fixtures para crear chunks con SourceReference
  - Actualizar assertions para verificar source en lugar de article_id
  - Actualizar tests de eventos para verificar source_type
  - Verificar que todos los tests de chunking pasen
  - _Requirements: 13.4, 11.1, 11.2_

- [x] 12. Actualizar imports en src/knowledge/
  - Actualizar imports de `from src.article.` → `from src.rss.article.`
  - Actualizar imports de `from src.source.` → `from src.rss.feed.`
  - Verificar que todos los imports usen los nuevos paths
  - Verificar que el código compile sin errores
  - _Requirements: 12.3, 12.5_

- [x] 13. Actualizar imports en src/rag/
  - ✅ Verificado: No existe directorio `src/rag` que requiera actualización
  - ✅ Verificado: `src/chunking`, `src/knowledge` no tienen imports de `src.article` o `src.source`
  - ✅ Todos los bounded contexts ya usan los paths correctos
  - _Requirements: 12.4, 12.5_
  - _Completado: 2024-12-14_

- [x] 14. Actualizar containers de DI
  - ✅ `src/rss/feed/container.py` existe como `RssFeedContainer`
  - ✅ `src/rss/article/container.py` existe como `RssArticleContainer`
  - ✅ Aliases de compatibilidad: `SourceContainer`, `ArticleContainer`
  - ✅ Factory methods actualizados con nuevos nombres
  - ✅ Handlers registrados correctamente en mediator
  - ✅ Container principal (`src/bootstrap/lifespan.py`) compone sub-containers
  - ✅ Todos los bounded contexts se inicializan correctamente
  - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5_
  - _Completado: 2024-12-14_

- [x] 15. Actualizar tests en tests/unit/
  - Renombrar `test_source.py` → `test_rss_feed.py`
  - Renombrar `test_article.py` → `test_rss_article.py`
  - Renombrar clases de test (TestSource → TestRssFeed)
  - Actualizar imports en todos los tests unitarios
  - Verificar que todos los tests pasen
  - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5_
  - _Completado: 2024-12-14 - 42 archivos actualizados, 419 cambios_

- [x] 16. Actualizar tests en tests/integration/
  - Renombrar directorios de tests para reflejar nueva estructura
  - Actualizar imports en todos los tests de integración
  - Actualizar fixtures para usar nuevos nombres de clase
  - Verificar que todos los tests de integración pasen
  - _Requirements: 11.4, 11.5_
  - _Completado: 2024-12-14 - 6 archivos actualizados, 71 cambios_

- [x] 17. Actualizar tests en tests/pbt/
  - Actualizar imports en tests de property-based testing
  - Actualizar generadores para usar nuevos nombres de clase
  - Verificar que todos los tests PBT pasen
  - _Requirements: 11.4, 11.5_
  - _Completado: 2024-12-14 - 22 archivos actualizados, 151 cambios_

- [x] 18. Actualizar ORM models y migraciones
  - Renombrar tabla `sources` → `rss_feeds`
  - Renombrar tabla `articles` → `rss_articles`
  - Crear migración de Alembic para renombrar tablas
  - Actualizar foreign keys y constraints
  - Verificar que las migraciones funcionen correctamente
  - _Requirements: 9.3, 9.4, 9.5_
  - _Completado: 2024-12-14 - Migración ejecutada exitosamente, datos preservados_

- [x] 19. Deprecar archivos antiguos
  - Agregar comentario DEPRECATED a `src/source/` files
  - Agregar comentario DEPRECATED a `src/article/` files
  - Incluir path de migración en comentarios
  - Mantener archivos temporalmente para referencia
  - _Requirements: 14.1, 14.2_

- [x] 20. Verificar compilación y tests
  - Ejecutar `pytest tests/unit/ -v` y verificar que todos pasen
  - Ejecutar `pytest tests/integration/ -v` y verificar que todos pasen
  - Ejecutar `pytest tests/pbt/ -v` y verificar que todos pasen
  - Verificar que no haya errores de import
  - Verificar que el sistema compile correctamente
  - _Requirements: 14.3, 14.4, 14.5_

- [ ] 21. Actualizar documentación
  - Actualizar `architecture.md` con nueva estructura de BCs
  - Actualizar `domain-patterns.md` con ejemplos de RssFeed y RssArticle
  - Crear documento de migración con mapeo completo
  - Actualizar diagramas de arquitectura
  - Crear guía para agregar futuros BCs (Twitter, PDF, etc.)
  - _Requirements: 15.1, 15.2, 15.3, 15.4, 15.5_

- [ ] 22. Eliminar archivos deprecados
  - Eliminar `src/source/` directory
  - Eliminar `src/article/` directory
  - Verificar que no queden referencias a paths antiguos
  - Ejecutar tests finales para confirmar
  - _Requirements: 14.5_

- [ ] 23. Checkpoint final - Validación completa
  - Ejecutar suite completa de tests
  - Verificar que no haya imports rotos
  - Verificar que el sistema compile sin errores
  - Verificar que la documentación esté actualizada
  - Confirmar que la migración está completa
  - _Requirements: All_

## Comandos Bash Útiles

### Crear Estructura de Directorios

```bash
# Task 1
mkdir -p src/rss/feed/{app,domain,infra}
mkdir -p src/rss/article/{app,domain,infra}
mkdir -p src/rss/shared/{value_objects,exceptions}
```

### Copiar Bounded Contexts

```bash
# Task 2
cp -r src/source/* src/rss/feed/

# Task 3
cp -r src/article/* src/rss/article/
```

### Renombrar Archivos (Ejemplo para Feed)

```bash
# Task 4 - Renombrar archivos en src/rss/feed/
cd src/rss/feed/

# Aggregates
find . -name "*source.py" -exec bash -c 'mv "$0" "${0/source/rss_feed}"' {} \;

# Value Objects
find . -name "*source_id.py" -exec bash -c 'mv "$0" "${0/source_id/rss_feed_id}"' {} \;
find . -name "*source_url.py" -exec bash -c 'mv "$0" "${0/source_url/rss_feed_url}"' {} \;

# Events (sin prefijo rss_feed, ya están en src/rss/feed/domain/events/)
# Los eventos NO llevan prefijo porque el contexto ya está dado por el path
# Ejemplo: src/rss/feed/domain/events/created.py (no rss_feed_created.py)

# Commands (sin sufijo redundante, ya están en src/rss/feed/app/commands/)
mv src/rss/feed/app/commands/create_source src/rss/feed/app/commands/create
mv src/rss/feed/app/commands/update_source src/rss/feed/app/commands/update
mv src/rss/feed/app/commands/activate_source src/rss/feed/app/commands/activate
mv src/rss/feed/app/commands/remove_source src/rss/feed/app/commands/remove

# Queries (sin sufijo redundante, ya están en src/rss/feed/app/queries/)
# Los queries también se renombran sin prefijo redundante

# Repositories
find . -name "*source_read_repository.py" -exec bash -c 'mv "$0" "${0/source_read_repository/rss_feed_read_repository}"' {} \;
find . -name "*source_write_repository.py" -exec bash -c 'mv "$0" "${0/source_write_repository/rss_feed_write_repository}"' {} \;

# Factories
find . -name "*source_factory.py" -exec bash -c 'mv "$0" "${0/source_factory/rss_feed_factory}"' {} \;

# Mappers
find . -name "*source_mapper.py" -exec bash -c 'mv "$0" "${0/source_mapper/rss_feed_mapper}"' {} \;

# Models
find . -name "*source_model.py" -exec bash -c 'mv "$0" "${0/source_model/rss_feed_model}"' {} \;

cd ../../..
```

### Renombrar Clases en Archivos

```bash
# Task 6 - Renombrar clases en src/rss/feed/
find src/rss/feed/ -type f -name "*.py" -exec sed -i '' 's/class Source(/class RssFeed(/g' {} \;
find src/rss/feed/ -type f -name "*.py" -exec sed -i '' 's/class SourceId(/class RssFeedId(/g' {} \;
find src/rss/feed/ -type f -name "*.py" -exec sed -i '' 's/class SourceUrl(/class RssFeedUrl(/g' {} \;
find src/rss/feed/ -type f -name "*.py" -exec sed -i '' 's/class SourceModel(/class RssFeedModel(/g' {} \;
find src/rss/feed/ -type f -name "*.py" -exec sed -i '' 's/class SourceMapper(/class RssFeedMapper(/g' {} \;
find src/rss/feed/ -type f -name "*.py" -exec sed -i '' 's/class SourceFactory(/class RssFeedFactory(/g' {} \;
find src/rss/feed/ -type f -name "*.py" -exec sed -i '' 's/class SourceCreated(/class RssFeedCreated(/g' {} \;
find src/rss/feed/ -type f -name "*.py" -exec sed -i '' 's/class CreateSourceCommand(/class CreateRssFeedCommand(/g' {} \;
find src/rss/feed/ -type f -name "*.py" -exec sed -i '' 's/class ISourceReadRepository(/class IRssFeedReadRepository(/g' {} \;
find src/rss/feed/ -type f -name "*.py" -exec sed -i '' 's/class ISourceWriteRepository(/class IRssFeedWriteRepository(/g' {} \;
find src/rss/feed/ -type f -name "*.py" -exec sed -i '' 's/class SqlAlchemySourceReadRepository(/class RssFeedReadRepository(/g' {} \;
find src/rss/feed/ -type f -name "*.py" -exec sed -i '' 's/class SqlAlchemySourceWriteRepository(/class RssFeedWriteRepository(/g' {} \;

# Task 7 - Renombrar clases en src/rss/article/
find src/rss/article/ -type f -name "*.py" -exec sed -i '' 's/class Article(/class RssArticle(/g' {} \;
find src/rss/article/ -type f -name "*.py" -exec sed -i '' 's/class ArticleId(/class RssArticleId(/g' {} \;
find src/rss/article/ -type f -name "*.py" -exec sed -i '' 's/class ArticleUrl(/class RssArticleUrl(/g' {} \;
find src/rss/article/ -type f -name "*.py" -exec sed -i '' 's/class ArticleModel(/class RssArticleModel(/g' {} \;
find src/rss/article/ -type f -name "*.py" -exec sed -i '' 's/class ArticleMapper(/class RssArticleMapper(/g' {} \;
find src/rss/article/ -type f -name "*.py" -exec sed -i '' 's/class ArticleFactory(/class RssArticleFactory(/g' {} \;
find src/rss/article/ -type f -name "*.py" -exec sed -i '' 's/class ArticleCreated(/class RssArticleCreated(/g' {} \;
find src/rss/article/ -type f -name "*.py" -exec sed -i '' 's/class CreateArticleCommand(/class CreateRssArticleCommand(/g' {} \;
find src/rss/article/ -type f -name "*.py" -exec sed -i '' 's/class IArticleReadRepository(/class IRssArticleReadRepository(/g' {} \;
find src/rss/article/ -type f -name "*.py" -exec sed -i '' 's/class IArticleWriteRepository(/class IRssArticleWriteRepository(/g' {} \;
find src/rss/article/ -type f -name "*.py" -exec sed -i '' 's/class SqlAlchemyArticleReadRepository(/class SqlAlchemyRssArticleReadRepository(/g' {} \;
find src/rss/article/ -type f -name "*.py" -exec sed -i '' 's/class SqlAlchemyArticleWriteRepository(/class SqlAlchemyRssArticleWriteRepository(/g' {} \;
```

### Actualizar Imports

```bash
# Task 8 - Actualizar imports en src/rss/feed/
find src/rss/feed/ -type f -name "*.py" -exec sed -i '' 's/from src\.source\./from src.rss.feed./g' {} \;

# Task 9 - Actualizar imports en src/rss/article/
find src/rss/article/ -type f -name "*.py" -exec sed -i '' 's/from src\.article\./from src.rss.article./g' {} \;

# Task 12 - Actualizar imports en src/knowledge/
find src/knowledge/ -type f -name "*.py" -exec sed -i '' 's/from src\.article\./from src.rss.article./g' {} \;
find src/knowledge/ -type f -name "*.py" -exec sed -i '' 's/from src\.source\./from src.rss.feed./g' {} \;

# Task 13 - Actualizar imports en src/rag/
find src/rag/ -type f -name "*.py" -exec sed -i '' 's/from src\.article\./from src.rss.article./g' {} \;
find src/rag/ -type f -name "*.py" -exec sed -i '' 's/from src\.source\./from src.rss.feed./g' {} \;
```

### Buscar Referencias Antiguas

```bash
# Buscar imports antiguos
grep -r "from src.source" src/
grep -r "from src.article" src/

# Buscar clases antiguas
grep -r "class Source(" src/
grep -r "class Article(" src/

# Buscar imports en tests
grep -r "from src.source" tests/
grep -r "from src.article" tests/
```

### Ejecutar Tests

```bash
# Task 20 - Verificar tests
pytest tests/unit/ -v
pytest tests/integration/ -v
pytest tests/pbt/ -v

# Verificar imports
python -c "from src.rss.feed.domain.aggregates.rss_feed import RssFeed; print('✓ RssFeed OK')"
python -c "from src.rss.article.domain.aggregates.rss_article import RssArticle; print('✓ RssArticle OK')"
python -c "from src.knowledge.domain.value_objects.source_reference import SourceReference; print('✓ SourceReference OK')"
```

### Deprecar Archivos Antiguos

```bash
# Task 19 - Agregar comentarios DEPRECATED
echo '"""
DEPRECATED: Este bounded context ha sido movido a src/rss/feed/

MIGRACIÓN:
- Nuevo módulo: src/rss/feed/
- Usar: from src.rss.feed.domain.aggregates.rss_feed import RssFeed
- Este directorio será eliminado en una versión futura
"""' | cat - src/source/__init__.py > temp && mv temp src/source/__init__.py

echo '"""
DEPRECATED: Este bounded context ha sido movido a src/rss/article/

MIGRACIÓN:
- Nuevo módulo: src/rss/article/
- Usar: from src.rss.article.domain.aggregates.rss_article import RssArticle
- Este directorio será eliminado en una versión futura
"""' | cat - src/article/__init__.py > temp && mv temp src/article/__init__.py
```

### Eliminar Archivos Deprecados

```bash
# Task 22 - Eliminar directorios antiguos (SOLO después de validación completa)
rm -rf src/source/
rm -rf src/article/
```

## Notas Importantes

1. **Ejecutar tests después de cada fase**: No avanzar a la siguiente fase si los tests fallan
2. **Usar git branches**: Crear branch para la migración y hacer commits frecuentes
3. **Backup**: Hacer backup antes de eliminar archivos antiguos
4. **Validación incremental**: Verificar que el sistema compile después de cada tarea
5. **Documentación**: Actualizar documentación a medida que se avanza

## Rollback Plan

Si algo sale mal:

1. Revertir al último commit estable
2. Revisar logs de errores
3. Corregir el problema específico
4. Continuar desde la última tarea exitosa

## Success Criteria

La migración será exitosa cuando:

- ✅ Todos los tests pasen (unit, integration, pbt)
- ✅ No haya errores de import
- ✅ El sistema compile correctamente
- ✅ La documentación esté actualizada
- ✅ Los archivos antiguos estén eliminados
- ✅ El bounded context `knowledge/` use `SourceReference`
