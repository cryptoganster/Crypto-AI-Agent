# Requirements Document

## Introduction

Este documento define los requisitos para migrar los bounded contexts `source/` y `article/` a una estructura más específica y escalable bajo `src/rss/`, con sub-bounded contexts `feed/` y `article/`. Esta migración mejora el Ubiquitous Language del dominio RSS y prepara el sistema para soportar múltiples tipos de contenido en el futuro (Twitter, PDF, Books, etc.).

## Glossary

- **RSS**: Really Simple Syndication, formato estándar para distribución de contenido web
- **RssFeed**: Fuente RSS que contiene múltiples artículos (anteriormente "Source")
- **RssArticle**: Artículo individual obtenido de un feed RSS (anteriormente "Article")
- **Bounded Context**: Límite explícito dentro del cual un modelo de dominio es definido y aplicable
- **Sub-Bounded Context**: División lógica dentro de un bounded context para mayor granularidad
- **Ubiquitous Language**: Lenguaje común compartido entre desarrolladores y expertos del dominio
- **Aggregate Root**: Entidad raíz que garantiza consistencia dentro de un cluster de objetos
- **Value Object**: Objeto inmutable definido por sus atributos, sin identidad propia
- **Domain Event**: Evento que representa algo que ocurrió en el dominio

## Requirements

### Requirement 1: Reestructurar Bounded Contexts con Granularidad

**User Story:** Como arquitecto del sistema, quiero organizar los bounded contexts de RSS con mayor granularidad, para que cada concepto del dominio (Feed y Article) tenga su propio espacio bien definido y sea más fácil de mantener y escalar.

#### Acceptance Criteria

1. WHEN se crea la nueva estructura THEN el sistema SHALL tener un bounded context `src/rss/` que contenga dos sub-bounded contexts: `feed/` y `article/`
2. WHEN se organiza el código THEN cada sub-bounded context SHALL tener su propia estructura completa de capas (app, domain, infra, container)
3. WHEN se define la arquitectura THEN el sistema SHALL mantener separación clara entre Feed (fuente RSS) y Article (contenido individual)
4. WHEN se implementa la estructura THEN cada sub-bounded context SHALL ser independiente y tener su propio container de DI
5. WHEN se organiza el código THEN el sistema SHALL incluir un directorio `src/rss/shared/` para conceptos compartidos entre sub-bounded contexts

### Requirement 2: Renombrar Aggregates con Lenguaje Ubicuo Específico

**User Story:** Como desarrollador del dominio, quiero que los aggregates usen nombres específicos del dominio RSS (RssFeed, RssArticle), para que el código refleje claramente el lenguaje ubicuo y evite ambigüedades con futuros tipos de contenido.

#### Acceptance Criteria

1. WHEN se renombra el aggregate THEN `Source` SHALL convertirse en `RssFeed` en todos los archivos
2. WHEN se renombra el aggregate THEN `Article` SHALL convertirse en `RssArticle` en todos los archivos
3. WHEN se actualizan los nombres THEN el sistema SHALL mantener la coherencia en todos los archivos relacionados (events, commands, queries, repositories)
4. WHEN se renombran las clases THEN los nombres de archivos SHALL reflejar los nuevos nombres de clase (rss_feed.py, rss_article.py)
5. WHEN se actualiza el código THEN todos los imports SHALL usar los nuevos nombres de clase

### Requirement 3: Renombrar Value Objects con Prefijo RSS

**User Story:** Como desarrollador del dominio, quiero que los value objects relacionados con RSS tengan el prefijo "Rss" en sus nombres, para que sea claro a qué dominio pertenecen y evitar conflictos con futuros value objects de otros dominios.

#### Acceptance Criteria

1. WHEN se renombran value objects THEN `SourceId` SHALL convertirse en `RssFeedId`
2. WHEN se renombran value objects THEN `ArticleId` SHALL convertirse en `RssArticleId`
3. WHEN se renombran value objects THEN `SourceUrl` SHALL convertirse en `RssFeedUrl`
4. WHEN se renombran value objects THEN `ArticleUrl` SHALL convertirse en `RssArticleUrl`
5. WHEN se actualizan los nombres THEN todos los value objects relacionados con RSS SHALL tener el prefijo "Rss"

### Requirement 4: Renombrar Domain Events con Prefijo RSS

**User Story:** Como desarrollador del sistema, quiero que los domain events relacionados con RSS tengan el prefijo "Rss" en sus nombres, para que sea claro qué bounded context los emite y facilitar el debugging de flujos event-driven.

#### Acceptance Criteria

1. WHEN se renombran eventos THEN `SourceCreated` SHALL convertirse en `RssFeedCreated`
2. WHEN se renombran eventos THEN `ArticleCreated` SHALL convertirse en `RssArticleCreated`
3. WHEN se renombran eventos THEN `ArticleContentScraped` SHALL convertirse en `RssArticleContentScraped`
4. WHEN se renombran eventos THEN todos los eventos relacionados con RSS SHALL tener el prefijo "Rss"
5. WHEN se actualizan los eventos THEN los nombres de archivo SHALL reflejar los nuevos nombres (rss_feed_created.py, rss_article_created.py)

### Requirement 5: Actualizar Commands y Queries con Prefijo RSS

**User Story:** Como desarrollador de la capa de aplicación, quiero que los commands y queries relacionados con RSS tengan el prefijo "Rss" en sus nombres, para que sea claro qué bounded context manejan y mantener consistencia con el resto del código.

#### Acceptance Criteria

1. WHEN se renombran commands THEN `CreateSourceCommand` SHALL convertirse en `CreateRssFeedCommand`
2. WHEN se renombran commands THEN `CreateArticleCommand` SHALL convertirse en `CreateRssArticleCommand`
3. WHEN se renombran queries THEN `GetSourceByIdQuery` SHALL convertirse en `GetRssFeedByIdQuery`
4. WHEN se renombran queries THEN `GetArticleByIdQuery` SHALL convertirse en `GetRssArticleByIdQuery`
5. WHEN se actualizan los nombres THEN los directorios de commands/queries SHALL reflejar los nuevos nombres

### Requirement 6: Actualizar Repositories con Prefijo RSS

**User Story:** Como desarrollador de infraestructura, quiero que los repositories relacionados con RSS tengan el prefijo "Rss" en sus nombres, para que sea claro qué aggregates persisten y mantener consistencia con el patrón de naming.

#### Acceptance Criteria

1. WHEN se renombran repositories THEN `ISourceReadRepository` SHALL convertirse en `IRssFeedReadRepository`
2. WHEN se renombran repositories THEN `ISourceWriteRepository` SHALL convertirse en `IRssFeedWriteRepository`
3. WHEN se renombran repositories THEN `IArticleReadRepository` SHALL convertirse en `IRssArticleReadRepository`
4. WHEN se renombran repositories THEN `IArticleWriteRepository` SHALL convertirse en `IRssArticleWriteRepository`
5. WHEN se actualizan las implementaciones THEN las clases concretas en infra SHALL reflejar los nuevos nombres

### Requirement 7: Actualizar Factories con Prefijo RSS

**User Story:** Como desarrollador del dominio, quiero que las factories relacionadas con RSS tengan el prefijo "Rss" en sus nombres, para que sea claro qué aggregates crean y mantener consistencia con el patrón Factory.

#### Acceptance Criteria

1. WHEN se renombran factories THEN `SourceFactory` SHALL convertirse en `RssFeedFactory`
2. WHEN se renombran factories THEN `ArticleFactory` SHALL convertirse en `RssArticleFactory`
3. WHEN se actualizan las factories THEN los métodos de creación SHALL usar los nuevos nombres de aggregate
4. WHEN se actualizan las factories THEN los nombres de archivo SHALL reflejar los nuevos nombres (rss_feed_factory.py, rss_article_factory.py)
5. WHEN se actualizan las factories THEN todos los imports en handlers SHALL usar los nuevos nombres

### Requirement 8: Actualizar Mappers con Prefijo RSS

**User Story:** Como desarrollador de la capa de aplicación, quiero que los mappers relacionados con RSS tengan el prefijo "Rss" en sus nombres, para que sea claro qué aggregates serializan y mantener consistencia con el patrón Mapper.

#### Acceptance Criteria

1. WHEN se renombran mappers THEN `SourceMapper` SHALL convertirse en `RssFeedMapper`
2. WHEN se renombran mappers THEN `ArticleMapper` SHALL convertirse en `RssArticleMapper`
3. WHEN se actualizan los mappers THEN los métodos de serialización SHALL usar los nuevos nombres de aggregate
4. WHEN se actualizan los mappers THEN los nombres de archivo SHALL reflejar los nuevos nombres
5. WHEN se actualizan los mappers THEN todos los imports en handlers SHALL usar los nuevos nombres

### Requirement 9: Actualizar ORM Models con Prefijo RSS

**User Story:** Como desarrollador de infraestructura, quiero que los modelos ORM relacionados con RSS tengan el prefijo "Rss" en sus nombres, para que sea claro qué tablas representan y mantener consistencia con los aggregates del dominio.

#### Acceptance Criteria

1. WHEN se renombran modelos ORM THEN `SourceModel` SHALL convertirse en `RssFeedModel`
2. WHEN se renombran modelos ORM THEN `ArticleModel` SHALL convertirse en `RssArticleModel`
3. WHEN se actualizan los modelos THEN los nombres de tabla SHALL reflejar los nuevos nombres (rss_feeds, rss_articles)
4. WHEN se actualizan los modelos THEN los nombres de archivo SHALL reflejar los nuevos nombres
5. WHEN se actualizan los modelos THEN todos los imports en repositories SHALL usar los nuevos nombres

### Requirement 10: Actualizar Containers de Dependency Injection

**User Story:** Como desarrollador del sistema, quiero que cada sub-bounded context tenga su propio container de DI, para que las dependencias estén organizadas por contexto y sea más fácil gestionar el ciclo de vida de los objetos.

#### Acceptance Criteria

1. WHEN se organizan los containers THEN `src/rss/feed/` SHALL tener su propio `container.py` con `RssFeedContainer`
2. WHEN se organizan los containers THEN `src/rss/article/` SHALL tener su propio `container.py` con `RssArticleContainer`
3. WHEN se configuran los containers THEN cada container SHALL registrar solo las dependencias de su sub-bounded context
4. WHEN se configuran los containers THEN el container principal SHALL componer los sub-containers
5. WHEN se actualizan los containers THEN todos los factory methods SHALL usar los nuevos nombres de clase

### Requirement 11: Actualizar Tests con Prefijo RSS

**User Story:** Como desarrollador del sistema, quiero que los tests relacionados con RSS tengan el prefijo "Rss" en sus nombres, para que sea claro qué componentes testean y mantener consistencia con el código de producción.

#### Acceptance Criteria

1. WHEN se renombran tests THEN `test_source.py` SHALL convertirse en `test_rss_feed.py`
2. WHEN se renombran tests THEN `test_article.py` SHALL convertirse en `test_rss_article.py`
3. WHEN se actualizan los tests THEN las clases de test SHALL usar los nuevos nombres (TestRssFeed, TestRssArticle)
4. WHEN se actualizan los tests THEN todos los imports SHALL usar los nuevos nombres de clase
5. WHEN se ejecutan los tests THEN todos los tests SHALL pasar sin errores

### Requirement 12: Actualizar Imports en Todo el Sistema

**User Story:** Como desarrollador del sistema, quiero que todos los imports en el codebase usen los nuevos paths y nombres de clase, para que el sistema compile correctamente y no haya referencias rotas.

#### Acceptance Criteria

1. WHEN se actualizan imports THEN `from src.source.domain.aggregates.source` SHALL convertirse en `from src.rss.feed.domain.aggregates.rss_feed`
2. WHEN se actualizan imports THEN `from src.article.domain.aggregates.article` SHALL convertirse en `from src.rss.article.domain.aggregates.rss_article`
3. WHEN se actualizan imports THEN todos los imports en `src/knowledge/` SHALL usar los nuevos paths
4. WHEN se actualizan imports THEN todos los imports en `src/rag/` SHALL usar los nuevos paths
5. WHEN se actualizan imports THEN el sistema SHALL compilar sin errores de import

### Requirement 13: Preparar Sistema para Futuros Bounded Contexts

**User Story:** Como arquitecto del sistema, quiero que la nueva estructura facilite agregar futuros bounded contexts (Twitter, PDF, Books), para que el sistema sea escalable y cada tipo de contenido tenga su propio espacio bien definido.

#### Acceptance Criteria

1. WHEN se diseña la estructura THEN el patrón `src/<content_type>/<sub_context>/` SHALL ser replicable para futuros bounded contexts
2. WHEN se documenta la arquitectura THEN el sistema SHALL incluir ejemplos de cómo agregar `src/twitter/tweet/` y `src/twitter/account/`
3. WHEN se documenta la arquitectura THEN el sistema SHALL incluir ejemplos de cómo agregar `src/pdf/document/` y `src/pdf/library/`
4. WHEN se implementa el patrón THEN el bounded context `knowledge/` SHALL usar `SourceReference` genérico para soportar múltiples tipos
5. WHEN se valida la arquitectura THEN agregar un nuevo tipo de contenido SHALL requerir solo crear un nuevo bounded context sin modificar existentes

### Requirement 14: Mantener Compatibilidad Durante Migración

**User Story:** Como desarrollador del sistema, quiero que la migración se realice de forma incremental y segura, para que el sistema siga funcionando durante el proceso de migración y se puedan detectar errores tempranamente.

#### Acceptance Criteria

1. WHEN se inicia la migración THEN los archivos antiguos SHALL marcarse como DEPRECATED con comentarios claros
2. WHEN se migra el código THEN los archivos antiguos SHALL mantenerse temporalmente para referencia
3. WHEN se actualizan imports THEN el sistema SHALL compilar después de cada paso de migración
4. WHEN se ejecutan tests THEN todos los tests SHALL pasar después de cada paso de migración
5. WHEN se completa la migración THEN los archivos antiguos SHALL eliminarse solo después de validación completa

### Requirement 15: Actualizar Documentación y Steering Files

**User Story:** Como desarrollador del sistema, quiero que la documentación y steering files reflejen la nueva estructura, para que los desarrolladores tengan guías actualizadas sobre cómo trabajar con el código.

#### Acceptance Criteria

1. WHEN se actualiza documentación THEN `architecture.md` SHALL reflejar la nueva estructura de bounded contexts
2. WHEN se actualiza documentación THEN `domain-patterns.md` SHALL incluir ejemplos con RssFeed y RssArticle
3. WHEN se actualiza documentación THEN se SHALL crear un documento de migración con el mapeo completo de nombres antiguos a nuevos
4. WHEN se actualiza documentación THEN los diagramas de arquitectura SHALL mostrar la nueva estructura
5. WHEN se actualiza documentación THEN se SHALL incluir guías para agregar futuros bounded contexts (Twitter, PDF, etc.)

## Non-Functional Requirements

### Performance
- La migración NO debe afectar el performance del sistema
- Los tests deben ejecutarse en el mismo tiempo o menos

### Maintainability
- El código migrado debe ser más fácil de mantener que el código original
- La nueva estructura debe facilitar agregar nuevos bounded contexts

### Scalability
- La nueva estructura debe soportar fácilmente agregar Twitter, PDF, Books, etc.
- Cada bounded context debe ser independiente y escalable

### Testability
- Todos los tests existentes deben pasar después de la migración
- La nueva estructura debe facilitar escribir tests aislados por bounded context

## Success Criteria

La migración será exitosa cuando:

1. ✅ Toda la estructura `src/source/` esté migrada a `src/rss/feed/`
2. ✅ Toda la estructura `src/article/` esté migrada a `src/rss/article/`
3. ✅ Todos los nombres de clase usen el prefijo "Rss" (RssFeed, RssArticle, etc.)
4. ✅ Todos los imports estén actualizados en todo el codebase
5. ✅ Todos los tests pasen sin errores
6. ✅ El sistema compile sin errores
7. ✅ La documentación esté actualizada
8. ✅ Los archivos antiguos estén eliminados
9. ✅ El bounded context `knowledge/` use `SourceReference` genérico
10. ✅ La arquitectura esté preparada para futuros bounded contexts

## Out of Scope

- Implementación de bounded contexts para Twitter, PDF, Books (solo preparación)
- Cambios en la lógica de negocio de los aggregates
- Optimizaciones de performance
- Cambios en la base de datos (solo renombrar tablas)
- Migración de datos existentes en producción
