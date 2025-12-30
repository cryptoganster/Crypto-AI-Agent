# Requirements Document: Limpieza de Archivos Deprecated

## Introducción

Este documento define los requisitos para la limpieza sistemática de archivos deprecated en `src/domain/` que ya fueron migrados a sus respectivos bounded contexts. Los archivos contienen código legacy que ya no se usa y debe ser eliminado de forma segura.

## Glossary

- **Deprecated File**: Archivo que contiene código que ha sido migrado a otra ubicación y ya no debe usarse
- **Bounded Context**: Contexto delimitado en DDD que agrupa código relacionado (ej: `src/article/`, `src/source/`)
- **Migration**: Proceso de mover código desde ubicaciones centralizadas a bounded contexts específicos
- **Backup (.bak)**: Extensión temporal para archivos que permite revertir cambios si es necesario
- **Domain Services**: Servicios que contienen lógica de negocio del dominio
- **Interfaces**: Contratos (Protocols) que definen comportamiento esperado de servicios

## Requirements

### Requirement 1: Identificación de Archivos Deprecated

**User Story:** Como desarrollador, quiero identificar todos los archivos deprecated en `src/domain/`, para saber qué archivos deben ser eliminados.

#### Acceptance Criteria

1. WHEN se ejecuta el análisis THEN el sistema SHALL listar todos los archivos en `src/domain/services/articles/` que fueron migrados
2. WHEN se ejecuta el análisis THEN el sistema SHALL listar todos los archivos en `src/domain/interfaces/services/articles/` que fueron migrados
3. WHEN se genera el reporte THEN el sistema SHALL incluir la ruta completa de cada archivo deprecated
4. WHEN se genera el reporte THEN el sistema SHALL incluir la nueva ubicación de cada archivo migrado
5. WHEN se genera el reporte THEN el sistema SHALL verificar que existen las nuevas ubicaciones

### Requirement 2: Investigación de Dependencias

**User Story:** Como desarrollador, quiero investigar qué archivos aún importan código deprecated, para resolver dependencias antes de eliminar.

#### Acceptance Criteria

1. WHEN se investigan dependencias THEN el sistema SHALL buscar todos los imports de archivos deprecated en `src/`
2. WHEN se investigan dependencias THEN el sistema SHALL buscar todos los imports de archivos deprecated en `tests/`
3. WHEN se encuentra un import deprecated THEN el sistema SHALL registrar el archivo que lo importa
4. WHEN se encuentra un import deprecated THEN el sistema SHALL registrar la línea exacta del import
5. WHEN se completa la investigación THEN el sistema SHALL generar un reporte de dependencias por archivo

### Requirement 3: Resolución de Dependencias

**User Story:** Como desarrollador, quiero actualizar todos los imports que usan código deprecated, para que apunten a las nuevas ubicaciones.

#### Acceptance Criteria

1. WHEN se resuelven dependencias THEN el sistema SHALL actualizar imports de `src/domain/services/articles/` a `src/article/domain/services/`
2. WHEN se resuelven dependencias THEN el sistema SHALL actualizar imports de `src/domain/interfaces/services/articles/` a `src/article/domain/interfaces/services/`
3. WHEN se actualiza un import THEN el sistema SHALL mantener el nombre de la clase/función importada
4. WHEN se actualiza un import THEN el sistema SHALL preservar el formato del código (indentación, line breaks)
5. WHEN se completan las actualizaciones THEN el sistema SHALL verificar que no quedan imports deprecated

### Requirement 4: Backup de Archivos

**User Story:** Como desarrollador, quiero crear backups de archivos deprecated antes de eliminarlos, para poder revertir si algo falla.

#### Acceptance Criteria

1. WHEN se hace backup de un archivo THEN el sistema SHALL renombrar el archivo agregando extensión `.bak`
2. WHEN se hace backup THEN el sistema SHALL preservar el contenido original del archivo
3. WHEN se hace backup THEN el sistema SHALL mantener el archivo en la misma ubicación
4. WHEN se completa el backup THEN el sistema SHALL verificar que el archivo `.bak` existe
5. WHEN se completa el backup THEN el sistema SHALL registrar la operación en el log

### Requirement 5: Ejecución de Tests

**User Story:** Como desarrollador, quiero ejecutar tests después de hacer backup, para verificar que el sistema funciona sin los archivos deprecated.

#### Acceptance Criteria

1. WHEN se ejecutan tests THEN el sistema SHALL ejecutar la suite completa de tests unitarios
2. WHEN se ejecutan tests THEN el sistema SHALL ejecutar tests de integración relevantes
3. WHEN los tests fallan THEN el sistema SHALL reportar qué tests fallaron
4. WHEN los tests fallan THEN el sistema SHALL indicar que se deben revertir los backups
5. WHEN todos los tests pasan THEN el sistema SHALL confirmar que es seguro eliminar los archivos

### Requirement 6: Eliminación Final

**User Story:** Como desarrollador, quiero eliminar definitivamente los archivos deprecated después de confirmar que todo funciona, para mantener el código limpio.

#### Acceptance Criteria

1. WHEN se eliminan archivos THEN el sistema SHALL eliminar solo archivos con extensión `.bak`
2. WHEN se elimina un archivo THEN el sistema SHALL verificar que todos los tests pasaron previamente
3. WHEN se elimina un archivo THEN el sistema SHALL registrar la eliminación en el log
4. WHEN se completa la eliminación THEN el sistema SHALL verificar que no quedan archivos `.bak`
5. WHEN se completa la eliminación THEN el sistema SHALL generar un reporte final de archivos eliminados

### Requirement 7: Documentación del Proceso

**User Story:** Como desarrollador, quiero documentar el proceso de limpieza, para tener un registro de qué se eliminó y por qué.

#### Acceptance Criteria

1. WHEN se completa la limpieza THEN el sistema SHALL generar un documento de resumen
2. WHEN se genera el resumen THEN el sistema SHALL listar todos los archivos eliminados
3. WHEN se genera el resumen THEN el sistema SHALL incluir las nuevas ubicaciones de cada archivo
4. WHEN se genera el resumen THEN el sistema SHALL incluir estadísticas (número de archivos, líneas de código)
5. WHEN se genera el resumen THEN el sistema SHALL incluir fecha y hora de la operación

## Archivos Identificados para Limpieza

### Domain Services (src/domain/services/articles/)

1. `article_content_extraction_service.py` → `src/article/domain/services/content_extraction.py`
2. `article_language_detection_service.py` → `src/article/domain/services/language_detection.py`
3. `article_metrics_calculation_service.py` → `src/article/domain/services/metrics_calculation.py`
4. `article_plaintext_extraction_service.py` → `src/article/domain/services/plaintext_extraction.py`
5. `sentence_relevance_scorer.py` → `src/article/domain/services/sentence_relevance_scorer.py`

### Interfaces (src/domain/interfaces/services/articles/)

1. `article_content_extraction_service.py` → `src/article/domain/interfaces/services/content_extraction.py`
2. `article_language_detection_service.py` → `src/article/domain/interfaces/services/language_detection.py`
3. `article_metrics_calculation_service.py` → `src/article/domain/interfaces/services/metrics_calculation.py`
4. `article_scraping_service.py` → `src/article/domain/interfaces/external/scraping_service.py`

## Notas Técnicas

- Los archivos ya contienen comentarios DEPRECATED con información de migración
- Las nuevas ubicaciones ya existen y están siendo usadas
- Los tests ya fueron actualizados para usar las nuevas ubicaciones
- El proceso debe ser reversible hasta la eliminación final
