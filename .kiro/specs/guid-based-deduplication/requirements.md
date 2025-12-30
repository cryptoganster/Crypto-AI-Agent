# Requirements Document

## Introducción

Este documento especifica los requisitos para implementar un sistema de deduplicación multi-nivel basado en RSS GUID que mejora la detección de duplicados y permite actualizar artículos cuando el feed RSS los modifica.

## Glossary

- **GUID**: Globally Unique Identifier proporcionado por el feed RSS para cada artículo
- **Deduplicación**: Proceso de detectar y prevenir la creación de artículos duplicados
- **Actualización de Artículo**: Proceso de actualizar un artículo existente cuando el feed RSS proporciona contenido modificado
- **ArticleData**: DTO con datos del artículo obtenidos del feed RSS
- **ArticleDeduplicationService**: Servicio de dominio que detecta duplicados
- **IArticleReadRepository**: Interface para queries de lectura de artículos
- **Match Method**: Método usado para detectar duplicado (guid, url, none)

## Requirements

### Requirement 1

**User Story:** Como sistema de scraping, quiero detectar duplicados usando RSS GUID primero, para evitar crear artículos duplicados cuando la URL cambia por parámetros de tracking.

#### Acceptance Criteria

1. WHEN un artículo tiene RSS GUID THEN el sistema SHALL buscar artículos existentes con el mismo GUID y source_id
2. WHEN se encuentra un artículo con el mismo GUID THEN el sistema SHALL retornar que es duplicado con método 'guid'
3. WHEN el artículo tiene GUID pero no se encuentra duplicado por GUID THEN el sistema SHALL continuar con verificación por URL
4. WHEN el artículo no tiene GUID THEN el sistema SHALL omitir verificación por GUID y continuar con URL
5. WHEN se detecta duplicado por GUID THEN el sistema SHALL loggear el article_id del duplicado encontrado

### Requirement 2

**User Story:** Como sistema de scraping, quiero mantener la deduplicación por URL + Source como fallback, para detectar duplicados cuando no hay GUID disponible.

#### Acceptance Criteria

1. WHEN la verificación por GUID no encuentra duplicado THEN el sistema SHALL buscar por URL y source_id
2. WHEN se encuentra un artículo con la misma URL y source_id THEN el sistema SHALL retornar que es duplicado con método 'url'
3. WHEN no se encuentra duplicado por URL THEN el sistema SHALL retornar que no es duplicado
4. WHEN se detecta duplicado por URL THEN el sistema SHALL loggear el article_id del duplicado encontrado

### Requirement 3

**User Story:** Como sistema de scraping, quiero eliminar la deduplicación por similitud de contenido, para preservar artículos similares que enriquecen el contexto para RAG/LLM.

#### Acceptance Criteria

1. WHEN se verifica duplicados THEN el sistema SHALL NOT usar similitud de contenido como criterio
2. WHEN dos artículos tienen contenido similar pero URLs diferentes THEN el sistema SHALL permitir ambos artículos
3. WHEN dos artículos tienen contenido similar pero GUIDs diferentes THEN el sistema SHALL permitir ambos artículos
4. WHEN se configura el servicio de deduplicación THEN el sistema SHALL NOT aceptar similarity_threshold como parámetro

### Requirement 4

**User Story:** Como sistema de scraping, quiero diferenciar entre duplicado exacto y actualización de artículo, para poder actualizar artículos cuando el feed RSS los modifica.

#### Acceptance Criteria

1. WHEN se encuentra duplicado por GUID THEN el sistema SHALL comparar pub_date del artículo nuevo vs existente
2. WHEN el pub_date del nuevo artículo es posterior al existente THEN el sistema SHALL marcar como 'update' en lugar de 'duplicate'
3. WHEN el pub_date del nuevo artículo es igual o anterior al existente THEN el sistema SHALL marcar como 'duplicate'
4. WHEN el artículo existente no tiene pub_date THEN el sistema SHALL marcar como 'duplicate' por defecto
5. WHEN se detecta 'update' THEN el sistema SHALL retornar flag is_update=True junto con el article_id existente

### Requirement 5

**User Story:** Como sistema de scraping, quiero actualizar artículos existentes cuando el feed RSS proporciona contenido modificado, para mantener la información actualizada.

#### Acceptance Criteria

1. WHEN se detecta que un artículo es actualización (is_update=True) THEN el sistema SHALL emitir UpdateArticleFromFeedCommand
2. WHEN se ejecuta UpdateArticleFromFeedCommand THEN el sistema SHALL cargar el artículo existente por ID
3. WHEN se carga el artículo existente THEN el sistema SHALL actualizar title, content, description si han cambiado
4. WHEN se actualiza el artículo THEN el sistema SHALL actualizar pub_date con la nueva fecha
5. WHEN se actualiza el artículo THEN el sistema SHALL emitir ArticleUpdatedFromFeed event
6. WHEN se actualiza el artículo THEN el sistema SHALL NOT crear un nuevo artículo

### Requirement 6

**User Story:** Como desarrollador, quiero que el repositorio tenga método find_by_guid, para buscar artículos por RSS GUID eficientemente.

#### Acceptance Criteria

1. WHEN se llama find_by_guid con guid y source_id THEN el sistema SHALL buscar en la tabla articles donde rss_guid = guid AND source_id = source_id
2. WHEN se encuentra un artículo THEN el sistema SHALL retornar ArticleDTO con todos los campos
3. WHEN no se encuentra artículo THEN el sistema SHALL retornar None
4. WHEN se llama find_by_guid solo con guid (sin source_id) THEN el sistema SHALL buscar en todas las sources
5. WHEN hay error en la query THEN el sistema SHALL loggear el error y lanzar excepción

### Requirement 7

**User Story:** Como sistema de scraping, quiero que la deduplicación retorne información detallada del match, para tomar decisiones informadas sobre qué hacer con el artículo.

#### Acceptance Criteria

1. WHEN se verifica duplicado THEN el sistema SHALL retornar tupla (is_duplicate, duplicate_id, match_method, is_update)
2. WHEN es duplicado THEN is_duplicate SHALL ser True
3. WHEN no es duplicado THEN is_duplicate SHALL ser False y duplicate_id SHALL ser None
4. WHEN se encuentra por GUID THEN match_method SHALL ser 'guid'
5. WHEN se encuentra por URL THEN match_method SHALL ser 'url'
6. WHEN no se encuentra THEN match_method SHALL ser None
7. WHEN es actualización THEN is_update SHALL ser True
8. WHEN es duplicado exacto THEN is_update SHALL ser False

### Requirement 8

**User Story:** Como sistema de scraping, quiero que el scraping coordinator maneje actualizaciones de artículos, para procesar correctamente artículos modificados en el feed.

#### Acceptance Criteria

1. WHEN se detecta is_update=True THEN el coordinator SHALL emitir UpdateArticleFromFeedCommand en lugar de crear nuevo
2. WHEN se detecta is_duplicate=True y is_update=False THEN el coordinator SHALL skip el artículo y loggear como duplicado
3. WHEN se detecta is_duplicate=False THEN el coordinator SHALL continuar con creación normal del artículo
4. WHEN se emite UpdateArticleFromFeedCommand THEN el coordinator SHALL incluir article_id del existente y ArticleData del nuevo
5. WHEN se procesa actualización THEN el coordinator SHALL loggear con nivel INFO indicando que es update

### Requirement 9

**User Story:** Como sistema, quiero que las actualizaciones de artículos re-procesen el contenido, para que los embeddings y análisis reflejen el contenido actualizado.

#### Acceptance Criteria

1. WHEN se actualiza un artículo desde feed THEN el sistema SHALL emitir ArticleUpdatedFromFeed event
2. WHEN ArticleUpdatedFromFeed es emitido THEN el sistema SHALL incluir article_id y campos actualizados
3. WHEN se recibe ArticleUpdatedFromFeed event THEN el sistema SHALL re-ejecutar el pipeline de procesamiento de contenido
4. WHEN se re-procesa contenido THEN el sistema SHALL actualizar plaintext, markdown, embeddings, y summaries
5. WHEN se re-procesa contenido THEN el sistema SHALL mantener el article_id original (no crear nuevo)

### Requirement 10

**User Story:** Como administrador, quiero configurar si las actualizaciones de artículos están habilitadas, para controlar el comportamiento del sistema.

#### Acceptance Criteria

1. WHEN se configura el sistema THEN el sistema SHALL leer RSS_ENABLE_ARTICLE_UPDATES de variables de entorno
2. WHEN RSS_ENABLE_ARTICLE_UPDATES es "true" THEN el sistema SHALL procesar actualizaciones de artículos
3. WHEN RSS_ENABLE_ARTICLE_UPDATES es "false" THEN el sistema SHALL tratar actualizaciones como duplicados y skipearlas
4. WHEN la variable no está definida THEN el sistema SHALL usar valor por defecto "true"
5. WHEN se deshabilitan actualizaciones THEN el sistema SHALL loggear con nivel WARNING cuando detecta potencial actualización

## Non-Functional Requirements

### Performance

1. La búsqueda por GUID debe ejecutarse en < 50ms (índice ya existe)
2. La verificación de duplicados completa debe ejecutarse en < 100ms
3. La actualización de artículo debe ejecutarse en < 200ms

### Observability

1. Todas las detecciones de duplicados deben loggearse con nivel INFO
2. Todas las actualizaciones de artículos deben loggearse con nivel INFO
3. Los errores en deduplicación deben loggearse con nivel ERROR
4. Las métricas deben incluir: duplicados detectados, actualizaciones procesadas, método de match usado

### Compatibility

1. El cambio debe ser backward compatible con artículos existentes sin GUID
2. Los artículos sin GUID deben seguir usando deduplicación por URL
3. La eliminación de similitud de contenido no debe afectar artículos existentes

## Out of Scope

- Deduplicación cross-source (artículos del mismo GUID en diferentes sources se consideran diferentes)
- Merge de artículos duplicados existentes en la base de datos
- Detección de duplicados por hash de contenido
- Deduplicación semántica usando embeddings
- UI para gestionar duplicados manualmente
