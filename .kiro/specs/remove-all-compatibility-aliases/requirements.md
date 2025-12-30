# Requirements Document: Eliminación Completa de Alias de Compatibilidad

## Introducción

Este documento especifica los requisitos para eliminar sistemáticamente todos los alias de compatibilidad temporal en el proyecto, dejando el código limpio, consistente y sin referencias legacy.

## Glossary

- **Alias**: Asignación de un nombre alternativo a una clase, función o tipo existente
- **Compatibility Alias**: Alias creado temporalmente durante migraciones para mantener compatibilidad con código antiguo
- **DEPRECATED**: Marcador que indica que un elemento debe eliminarse
- **Bounded Context**: Límite explícito dentro del cual un modelo de dominio es definido y aplicable
- **Type Alias**: Alias de tipo usado para mejorar legibilidad (ej: `Event = IDomainEvent`)
- **Property Alias**: Property que expone un atributo con nombre alternativo
- **Legacy Code**: Código antiguo que usa nombres previos a migraciones

## Requirements

### Requirement 1: Identificación y Categorización de Alias

**User Story:** Como desarrollador, quiero identificar todos los alias existentes en el proyecto, para poder planificar su eliminación sistemática.

#### Acceptance Criteria

1. WHEN el sistema escanea el directorio `src/` THEN el sistema SHALL identificar todos los alias de compatibilidad existentes
2. WHEN se identifican alias THEN el sistema SHALL categorizar cada alias por bounded context (Shared, RSS Article, RSS Feed, Chunking)
3. WHEN se categorizan alias THEN el sistema SHALL clasificar cada alias por prioridad (DEPRECATED, Evaluar, Mantener)
4. WHEN se clasifican alias THEN el sistema SHALL generar un inventario completo con ubicación exacta de cada alias
5. WHEN se genera el inventario THEN el sistema SHALL incluir el archivo, línea y tipo de alias para cada entrada

### Requirement 2: Verificación de Uso de Alias

**User Story:** Como desarrollador, quiero verificar dónde se usan los alias antes de eliminarlos, para evitar romper el código existente.

#### Acceptance Criteria

1. WHEN se verifica un alias THEN el sistema SHALL buscar todas las referencias al nombre del alias en el código
2. WHEN se encuentran referencias THEN el sistema SHALL listar todos los archivos que usan el alias
3. WHEN se listan archivos THEN el sistema SHALL incluir el número de línea de cada uso
4. WHEN no se encuentran referencias THEN el sistema SHALL marcar el alias como seguro para eliminar
5. WHEN se encuentran referencias THEN el sistema SHALL generar un plan de migración para actualizar cada uso

### Requirement 3: Actualización de Referencias a Alias

**User Story:** Como desarrollador, quiero actualizar automáticamente todas las referencias a alias, para migrar al nombre canónico sin errores.

#### Acceptance Criteria

1. WHEN se actualizan referencias THEN el sistema SHALL reemplazar el nombre del alias por el nombre canónico en todos los archivos
2. WHEN se reemplazan nombres THEN el sistema SHALL preservar la estructura y formato del código
3. WHEN se preserva formato THEN el sistema SHALL mantener indentación, espaciado y comentarios
4. WHEN se actualizan imports THEN el sistema SHALL actualizar declaraciones `from X import Alias` a `from X import Canonical`
5. WHEN se actualizan usos THEN el sistema SHALL reemplazar `Alias(...)` por `Canonical(...)` en todo el código

### Requirement 4: Eliminación de Definiciones de Alias

**User Story:** Como desarrollador, quiero eliminar las definiciones de alias una vez que no se usan, para limpiar el código.

#### Acceptance Criteria

1. WHEN todas las referencias están actualizadas THEN el sistema SHALL eliminar la línea de definición del alias
2. WHEN se elimina un alias THEN el sistema SHALL eliminar también el comentario asociado (ej: "# Alias para compatibilidad")
3. WHEN se eliminan alias de un archivo THEN el sistema SHALL preservar otros alias que aún se necesiten
4. WHEN se elimina el último alias de un bloque THEN el sistema SHALL eliminar líneas en blanco extra
5. WHEN se eliminan alias de `__init__.py` THEN el sistema SHALL actualizar la lista `__all__` para remover el alias

### Requirement 5: Ejecución de Tests Pre-Eliminación

**User Story:** Como desarrollador, quiero ejecutar todos los tests antes de eliminar alias, para establecer una baseline de funcionamiento correcto.

#### Acceptance Criteria

1. WHEN se inicia el proceso THEN el sistema SHALL ejecutar la suite completa de tests
2. WHEN se ejecutan tests THEN el sistema SHALL registrar el resultado de cada test
3. WHEN todos los tests pasan THEN el sistema SHALL proceder con la eliminación de alias
4. WHEN algún test falla THEN el sistema SHALL detener el proceso y reportar los fallos
5. WHEN se reportan fallos THEN el sistema SHALL incluir el nombre del test, archivo y mensaje de error

### Requirement 6: Ejecución de Tests Post-Eliminación

**User Story:** Como desarrollador, quiero ejecutar todos los tests después de eliminar alias, para verificar que no se rompió nada.

#### Acceptance Criteria

1. WHEN se completa la eliminación THEN el sistema SHALL ejecutar la suite completa de tests nuevamente
2. WHEN se ejecutan tests post-eliminación THEN el sistema SHALL comparar resultados con la baseline pre-eliminación
3. WHEN todos los tests pasan THEN el sistema SHALL marcar la eliminación como exitosa
4. WHEN algún test falla THEN el sistema SHALL identificar qué alias causó el problema
5. WHEN se identifica el problema THEN el sistema SHALL generar un reporte con el alias problemático y el test que falló

### Requirement 7: Procesamiento por Fases

**User Story:** Como desarrollador, quiero eliminar alias en fases ordenadas por prioridad, para minimizar riesgos y facilitar debugging.

#### Acceptance Criteria

1. WHEN se inicia el proceso THEN el sistema SHALL procesar alias en orden: DEPRECATED, luego Shared, luego RSS Feed, luego RSS Article, luego Chunking
2. WHEN se procesa una fase THEN el sistema SHALL completar todos los alias de esa fase antes de continuar
3. WHEN se completa una fase THEN el sistema SHALL ejecutar tests antes de proceder a la siguiente fase
4. WHEN una fase falla THEN el sistema SHALL detener el proceso y reportar la fase problemática
5. WHEN se reporta una fase problemática THEN el sistema SHALL incluir lista de alias procesados en esa fase

### Requirement 8: Manejo de Casos Especiales

**User Story:** Como desarrollador, quiero manejar correctamente casos especiales de alias, para evitar eliminar alias que deben mantenerse.

#### Acceptance Criteria

1. WHEN se encuentra un type alias útil (ej: `Event = IDomainEvent`) THEN el sistema SHALL marcarlo como "mantener" y no eliminarlo
2. WHEN se encuentra un property alias (ej: `@property def score()`) THEN el sistema SHALL marcarlo como "mantener" y no eliminarlo
3. WHEN se encuentra un alias auto-referencial (ej: `X = X`) THEN el sistema SHALL marcarlo como "error" y reportarlo
4. WHEN se encuentra un alias en `__all__` THEN el sistema SHALL actualizar `__all__` al eliminar el alias
5. WHEN se encuentran alias duplicados THEN el sistema SHALL eliminar todos excepto uno en el archivo principal

### Requirement 9: Generación de Reportes

**User Story:** Como desarrollador, quiero recibir reportes detallados del proceso, para entender qué se hizo y verificar resultados.

#### Acceptance Criteria

1. WHEN se completa el proceso THEN el sistema SHALL generar un reporte de eliminación completo
2. WHEN se genera el reporte THEN el sistema SHALL incluir número total de alias eliminados por bounded context
3. WHEN se incluyen estadísticas THEN el sistema SHALL mostrar archivos modificados, líneas eliminadas y referencias actualizadas
4. WHEN se reportan cambios THEN el sistema SHALL listar cada archivo modificado con resumen de cambios
5. WHEN se completa exitosamente THEN el sistema SHALL generar un reporte de tests mostrando que todos pasan

### Requirement 10: Rollback en Caso de Fallo

**User Story:** Como desarrollador, quiero poder revertir cambios si algo sale mal, para mantener el código en estado funcional.

#### Acceptance Criteria

1. WHEN se detecta un fallo THEN el sistema SHALL ofrecer opción de rollback automático
2. WHEN se ejecuta rollback THEN el sistema SHALL restaurar todos los archivos modificados a su estado original
3. WHEN se restauran archivos THEN el sistema SHALL verificar que los tests vuelven a pasar
4. WHEN se completa rollback THEN el sistema SHALL generar un reporte explicando qué falló y qué se revirtió
5. WHEN se genera reporte de rollback THEN el sistema SHALL incluir recomendaciones para resolver el problema

### Requirement 11: Validación de Imports

**User Story:** Como desarrollador, quiero validar que todos los imports son correctos después de eliminar alias, para evitar errores de importación.

#### Acceptance Criteria

1. WHEN se eliminan alias THEN el sistema SHALL verificar que todos los imports son válidos
2. WHEN se verifican imports THEN el sistema SHALL intentar importar cada módulo modificado
3. WHEN un import falla THEN el sistema SHALL reportar el módulo y el error de importación
4. WHEN todos los imports son válidos THEN el sistema SHALL marcar la validación como exitosa
5. WHEN se completa validación THEN el sistema SHALL generar lista de módulos verificados

### Requirement 12: Actualización de Documentación

**User Story:** Como desarrollador, quiero actualizar la documentación para reflejar la eliminación de alias, para mantener docs sincronizados con el código.

#### Acceptance Criteria

1. WHEN se eliminan alias THEN el sistema SHALL buscar referencias a alias en archivos `.md`
2. WHEN se encuentran referencias en docs THEN el sistema SHALL actualizar la documentación con nombres canónicos
3. WHEN se actualiza documentación THEN el sistema SHALL preservar el formato markdown
4. WHEN se completa actualización THEN el sistema SHALL generar lista de archivos de documentación modificados
5. WHEN se genera lista THEN el sistema SHALL incluir resumen de cambios por archivo

## Priorización de Alias

### Fase 1: DEPRECATED (Alta Prioridad)
- 6 alias marcados explícitamente como DEPRECATED
- Deben eliminarse primero por estar obsoletos

### Fase 2: Shared Kernel (Media-Alta Prioridad)
- 8 alias en infraestructura compartida
- Afectan múltiples bounded contexts

### Fase 3: RSS Feed (Media Prioridad)
- 14 alias de migración Source → RssFeed
- Bounded context bien definido

### Fase 4: RSS Article (Media Prioridad)
- 35 alias de migración Article → RssArticle
- Mayor cantidad, requiere cuidado

### Fase 5: Chunking (Baja Prioridad)
- 2 alias ContentChunk → KnowledgeChunk
- Bounded context pequeño

## Casos Especiales a Mantener

1. **Type Aliases Útiles**: `Event = IDomainEvent` (mejora legibilidad)
2. **Property Aliases**: `@property def score()` (compatibilidad de API)

## Métricas de Éxito

- ✅ 68 alias eliminados exitosamente
- ✅ 0 tests fallando después de eliminación
- ✅ 0 errores de importación
- ✅ Documentación actualizada
- ✅ Código más limpio y mantenible

## Restricciones

- NO eliminar type aliases útiles que mejoran legibilidad
- NO eliminar property aliases que son parte de la API pública
- NO proceder si tests fallan en baseline
- NO continuar a siguiente fase si fase actual falla
- NO modificar archivos fuera de `src/` excepto documentación

## Dependencias

- pytest instalado y configurado
- Acceso de lectura/escritura a `src/`
- Suite de tests completa y funcional
- Git para tracking de cambios (opcional pero recomendado)
