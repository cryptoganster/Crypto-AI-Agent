# Requirements Document

## Introduction

Este spec documenta la migración del bounded context `chunking` a `knowledge` para mejorar la claridad del lenguaje ubicuo y alinear el código con el valor de negocio que representa: construir y gestionar una base de conocimiento consultable.

## Glossary

- **Bounded Context**: Límite explícito dentro del cual un modelo de dominio es definido y aplicable
- **Knowledge Base**: Base de conocimiento construida a partir de artículos procesados
- **Knowledge Chunk**: Fragmento atómico de conocimiento extraído de un artículo
- **Migration**: Proceso de renombrar y mover código de un bounded context a otro
- **Deprecation**: Marcar código antiguo como obsoleto antes de eliminarlo
- **Backup Extension**: Extensión `.bak` agregada a archivos deprecados para mantenerlos como respaldo sin que Python los lea

## Requirements

### Requirement 1

**User Story:** Como desarrollador del sistema, quiero duplicar el bounded context `chunking` a `knowledge` sin perder funcionalidad, para poder realizar la migración de forma segura.

#### Acceptance Criteria

1. WHEN se ejecuta el comando de duplicación THEN el sistema SHALL crear una copia exacta de `src/chunking/` en `src/knowledge/`
2. WHEN la duplicación se completa THEN el sistema SHALL verificar que todos los archivos fueron copiados correctamente
3. WHEN la duplicación se completa THEN el sistema SHALL mantener la estructura de directorios idéntica
4. WHEN la duplicación se completa THEN el sistema SHALL preservar todos los imports y referencias internas
5. WHEN la duplicación se completa THEN el sistema SHALL reportar el número de archivos copiados

### Requirement 2

**User Story:** Como desarrollador del sistema, quiero renombrar archivos y clases en `src/knowledge/` siguiendo el nuevo lenguaje ubicuo, para que el código refleje el dominio de "gestión de conocimiento".

#### Acceptance Criteria

1. WHEN se renombra un archivo THEN el sistema SHALL actualizar el nombre del archivo siguiendo la convención `knowledge_*` o `*_knowledge`
2. WHEN se renombra una clase THEN el sistema SHALL actualizar todas las referencias a esa clase dentro del archivo
3. WHEN se renombra un aggregate THEN el sistema SHALL renombrar de `ContentChunk` a `KnowledgeChunk`
4. WHEN se renombran value objects THEN el sistema SHALL renombrar siguiendo el patrón `Knowledge*` (ej: `KnowledgeEmbedding`, `KnowledgeSummary`)
5. WHEN se renombran eventos THEN el sistema SHALL usar verbos de negocio (ej: `KnowledgeExtracted`, `KnowledgeEnriched`, `KnowledgeIndexed`)
6. WHEN se renombran comandos THEN el sistema SHALL usar verbos de negocio (ej: `ExtractKnowledgeCommand`, `EnrichKnowledgeCommand`)
7. WHEN se renombra el process manager THEN el sistema SHALL renombrar de `ArticleAIProcessingPipeline` a `KnowledgeProcessingPipeline`

### Requirement 3

**User Story:** Como desarrollador del sistema, quiero actualizar imports en archivos de forma incremental, para minimizar el riesgo de romper el sistema durante la migración.

#### Acceptance Criteria

1. WHEN se actualiza un archivo THEN el sistema SHALL cambiar imports de `src.chunking` a `src.knowledge`
2. WHEN se actualiza un archivo THEN el sistema SHALL actualizar referencias a clases renombradas
3. WHEN se actualiza un archivo THEN el sistema SHALL actualizar `__init__.py` correspondiente
4. WHEN se actualiza un archivo THEN el sistema SHALL verificar que no quedan imports rotos
5. WHEN se actualiza un archivo THEN el sistema SHALL ejecutar validación de sintaxis Python
6. WHEN se actualiza un archivo THEN el sistema SHALL reportar el progreso de la migración

### Requirement 4

**User Story:** Como desarrollador del sistema, quiero deprecar archivos originales de `src/chunking/` agregando extensión `.bak`, para mantener respaldo sin que Python los lea.

#### Acceptance Criteria

1. WHEN se depreca un archivo THEN el sistema SHALL renombrar el archivo agregando extensión `.bak`
2. WHEN se depreca un archivo THEN el sistema SHALL verificar que el archivo migrado en `src/knowledge/` existe y funciona
3. WHEN se depreca un archivo THEN el sistema SHALL verificar que no hay imports activos al archivo deprecado
4. WHEN se depreca un archivo THEN el sistema SHALL mantener el archivo `.bak` en su ubicación original
5. WHEN se depreca un archivo THEN el sistema SHALL agregar comentario en el archivo `.bak` indicando su nueva ubicación

### Requirement 5

**User Story:** Como desarrollador del sistema, quiero actualizar el container de DI para usar el nuevo bounded context `knowledge`, para que la inyección de dependencias funcione correctamente.

#### Acceptance Criteria

1. WHEN se actualiza el container THEN el sistema SHALL renombrar de `ChunkingContainer` a `KnowledgeContainer`
2. WHEN se actualiza el container THEN el sistema SHALL actualizar todos los factory methods
3. WHEN se actualiza el container THEN el sistema SHALL actualizar el registro de handlers
4. WHEN se actualiza el container THEN el sistema SHALL actualizar el registro de event handlers
5. WHEN se actualiza el container THEN el sistema SHALL verificar que todos los handlers se registran correctamente

### Requirement 6

**User Story:** Como desarrollador del sistema, quiero actualizar imports en otros bounded contexts que dependen de `chunking`, para que el sistema completo use el nuevo bounded context `knowledge`.

#### Acceptance Criteria

1. WHEN se actualizan bounded contexts externos THEN el sistema SHALL identificar todos los archivos que importan desde `src.chunking`
2. WHEN se actualizan bounded contexts externos THEN el sistema SHALL actualizar imports a `src.knowledge`
3. WHEN se actualizan bounded contexts externos THEN el sistema SHALL actualizar referencias a clases renombradas
4. WHEN se actualizan bounded contexts externos THEN el sistema SHALL verificar que no quedan imports rotos
5. WHEN se actualizan bounded contexts externos THEN el sistema SHALL ejecutar tests de integración

### Requirement 7

**User Story:** Como desarrollador del sistema, quiero actualizar tests para usar el nuevo bounded context `knowledge`, para mantener la cobertura de tests durante la migración.

#### Acceptance Criteria

1. WHEN se actualizan tests THEN el sistema SHALL duplicar tests de `tests/unit/chunking/` a `tests/unit/knowledge/`
2. WHEN se actualizan tests THEN el sistema SHALL actualizar imports en tests
3. WHEN se actualizan tests THEN el sistema SHALL actualizar referencias a clases renombradas
4. WHEN se actualizan tests THEN el sistema SHALL ejecutar tests para verificar que pasan
5. WHEN se actualizan tests THEN el sistema SHALL deprecar tests antiguos con extensión `.bak`

### Requirement 8

**User Story:** Como desarrollador del sistema, quiero verificar que la migración fue exitosa, para asegurar que el sistema funciona correctamente con el nuevo bounded context.

#### Acceptance Criteria

1. WHEN se completa la migración THEN el sistema SHALL ejecutar todos los tests unitarios
2. WHEN se completa la migración THEN el sistema SHALL ejecutar todos los tests de integración
3. WHEN se completa la migración THEN el sistema SHALL verificar que no hay imports a `src.chunking`
4. WHEN se completa la migración THEN el sistema SHALL verificar que todos los handlers están registrados
5. WHEN se completa la migración THEN el sistema SHALL generar reporte de migración con estadísticas

### Requirement 9

**User Story:** Como desarrollador del sistema, quiero documentar los cambios de la migración, para que el equipo entienda el nuevo lenguaje ubicuo y la estructura del bounded context.

#### Acceptance Criteria

1. WHEN se documenta la migración THEN el sistema SHALL crear documento de mapeo de nombres antiguos a nuevos
2. WHEN se documenta la migración THEN el sistema SHALL actualizar documentación de arquitectura
3. WHEN se documenta la migración THEN el sistema SHALL crear guía de referencia rápida
4. WHEN se documenta la migración THEN el sistema SHALL documentar el nuevo lenguaje ubicuo
5. WHEN se documenta la migración THEN el sistema SHALL crear checklist de verificación post-migración

### Requirement 10

**User Story:** Como desarrollador del sistema, quiero eliminar archivos `.bak` después de verificar que la migración es estable, para limpiar el código base.

#### Acceptance Criteria

1. WHEN se eliminan archivos `.bak` THEN el sistema SHALL verificar que han pasado al menos 2 sprints desde la migración
2. WHEN se eliminan archivos `.bak` THEN el sistema SHALL verificar que todos los tests pasan
3. WHEN se eliminan archivos `.bak` THEN el sistema SHALL verificar que no hay referencias a archivos `.bak`
4. WHEN se eliminan archivos `.bak` THEN el sistema SHALL eliminar directorio completo `src/chunking/`
5. WHEN se eliminan archivos `.bak` THEN el sistema SHALL actualizar `.gitignore` si es necesario

## Mapeo de Nombres

**Ver mapeo completo en**: `file-mapping.md`

El mapeo incluye:
- ~80-100 archivos a renombrar
- ~60-80 clases a renombrar
- ~15-20 directorios a renombrar
- ~200-300 import statements a actualizar

### Resumen de Cambios Principales

**Aggregates**: `ContentChunk` → `KnowledgeChunk`

**Value Objects**: `VectorEmbedding` → `KnowledgeEmbedding`, `ChunkSummary` → `KnowledgeSummary`, etc.

**Events**: `ArticleAIProcessedEvent` → `KnowledgeExtractedEvent`, `ChunkCreatedEvent` → `KnowledgeChunkCreatedEvent`, etc.

**Commands**: `ChunkArticleCommand` → `ExtractKnowledgeCommand`, `GenerateChunkEmbeddingsCommand` → `EnrichKnowledgeCommand`, etc.

**Process Managers**: `ArticleAIProcessingPipeline` → `KnowledgeProcessingPipeline`

**Containers**: `ChunkingContainer` → `KnowledgeContainer`

## Orden de Migración

### Fase 1: Preparación (Requirement 1)
1. Duplicar `src/chunking/` → `src/knowledge/`
2. Verificar duplicación exitosa

### Fase 2: Renombrado Interno (Requirement 2)
1. Value Objects (sin dependencias externas)
2. Events (dependen de VOs)
3. Aggregates (dependen de VOs y Events)
4. Services (dependen de Aggregates)
5. Commands (dependen de todo lo anterior)
6. Process Managers (dependen de Commands y Events)

### Fase 3: Actualización de Imports (Requirement 3)
1. Actualizar `__init__.py` en cada directorio
2. Actualizar imports internos en `src/knowledge/`
3. Actualizar container `src/knowledge/container.py`

### Fase 4: Deprecación (Requirement 4)
1. Deprecar archivos en `src/chunking/` con extensión `.bak`
2. Verificar que no hay imports rotos

### Fase 5: Migración Externa (Requirements 5-6)
1. Actualizar containers principales
2. Actualizar bounded contexts que dependen de chunking
3. Actualizar API endpoints si existen

### Fase 6: Tests (Requirement 7)
1. Duplicar y actualizar tests
2. Ejecutar suite completa de tests
3. Deprecar tests antiguos

### Fase 7: Verificación (Requirement 8)
1. Ejecutar todos los tests
2. Verificar handlers registrados
3. Generar reporte de migración

### Fase 8: Documentación (Requirement 9)
1. Crear documento de mapeo
2. Actualizar arquitectura
3. Crear guía de referencia

### Fase 9: Limpieza (Requirement 10)
1. Esperar 2 sprints
2. Eliminar archivos `.bak`
3. Eliminar directorio `src/chunking/`

## Riesgos y Mitigaciones

### Riesgo 1: Imports Rotos
**Mitigación**: Verificar imports después de cada cambio usando `python -m py_compile`

### Riesgo 2: Tests Fallando
**Mitigación**: Ejecutar tests después de cada fase de migración

### Riesgo 3: Handlers No Registrados
**Mitigación**: Verificar registro de handlers en startup

### Riesgo 4: Pérdida de Funcionalidad
**Mitigación**: Mantener archivos `.bak` como respaldo durante 2 sprints

### Riesgo 5: Confusión en el Equipo
**Mitigación**: Documentar claramente el mapeo de nombres y comunicar cambios

## Métricas de Éxito

1. ✅ 100% de tests pasando después de migración
2. ✅ 0 imports a `src.chunking` en código activo
3. ✅ 100% de handlers registrados correctamente
4. ✅ Documentación completa del nuevo lenguaje ubicuo
5. ✅ Tiempo de migración < 1 sprint
