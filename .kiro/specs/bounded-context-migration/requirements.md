# Requirements Document

## Introduction

Este documento define los requisitos para migrar la arquitectura actual del proyecto a una estructura basada en Bounded Contexts siguiendo Domain-Driven Design (DDD) y Clean Architecture. La migración se realizará de forma incremental, copiando archivos desde las capas más bajas (domain) hacia las superiores (infrastructure, api), actualizando solo las dependencias necesarias.

## Glossary

- **Bounded Context**: Un límite explícito dentro del cual un modelo de dominio particular es definido y aplicable. Cada bounded context tiene su propio modelo de dominio, lenguaje ubicuo y límites claros.
- **Article Context**: Bounded context responsable de la gestión de artículos, incluyendo su creación, procesamiento, análisis de calidad, categorización y publicación.
- **Source Context**: Bounded context responsable de la gestión de fuentes RSS, incluyendo su configuración, validación, métricas de salud y estado.
- **Fetching Context**: Bounded context responsable de las operaciones de scraping, sesiones de fetch, coordinación de operaciones y manejo de errores.
- **Shared Kernel**: Código compartido entre bounded contexts que incluye abstracciones base, interfaces comunes y utilidades.
- **Genesis Files**: Archivos fundacionales sin dependencias externas que deben migrarse primero (aggregates, value objects base).
- **Dependency Graph**: Grafo de dependencias entre archivos que determina el orden de migración.
- **Clean Architecture Layers**: Capas arquitectónicas (domain, application, infrastructure, api) que deben mantenerse separadas.
- **Deprecation Marker**: Decorador o comentario que marca un archivo como deprecado antes de su eliminación, permitiendo detectar usos no migrados.
- **Deprecation Warning**: Advertencia en logs que indica cuando se usa código deprecado, facilitando la identificación de dependencias faltantes.
- **Safe Deletion**: Proceso de eliminación de archivos deprecados solo después de confirmar que no existen referencias activas y que todos los tests pasan.

## Requirements

### Requirement 1

**User Story:** Como desarrollador, quiero una estructura de bounded contexts clara, para que cada contexto tenga responsabilidades bien definidas y límites explícitos.

#### Acceptance Criteria

1. WHEN se analiza la estructura actual THEN el sistema SHALL identificar tres bounded contexts principales: Article, Source y Fetching
2. WHEN se define un bounded context THEN el sistema SHALL crear la estructura de directorios con las capas domain, app, infrastructure y api
3. WHEN se organiza el código THEN cada bounded context SHALL contener solo el código relacionado con su responsabilidad específica
4. WHEN se establece el shared kernel THEN el sistema SHALL incluir abstracciones base, interfaces comunes y utilidades compartidas
5. WHEN se definen límites THEN cada bounded context SHALL tener interfaces claras para comunicación con otros contextos

### Requirement 2

**User Story:** Como desarrollador, quiero migrar archivos desde las capas más bajas hacia arriba, para evitar errores de dependencias faltantes durante la migración.

#### Acceptance Criteria

1. WHEN se inicia la migración THEN el sistema SHALL comenzar con los genesis files (aggregates sin dependencias externas)
2. WHEN se migra un archivo THEN el sistema SHALL verificar que todas sus dependencias ya existan en la nueva estructura
3. WHEN se detecta una dependencia faltante THEN el sistema SHALL migrar primero la dependencia antes de continuar
4. WHEN se completa la capa domain THEN el sistema SHALL proceder con la capa application
5. WHEN se completa la capa application THEN el sistema SHALL proceder con infrastructure y finalmente api

### Requirement 3

**User Story:** Como desarrollador, quiero copiar archivos tal cual sin reescribirlos, para minimizar el riesgo de introducir errores durante la migración.

#### Acceptance Criteria

1. WHEN se migra un archivo THEN el sistema SHALL copiar el contenido exacto sin modificaciones
2. WHEN se actualiza un import THEN el sistema SHALL solo cambiar las rutas de importación para reflejar la nueva estructura
3. WHEN se copia un archivo THEN el sistema SHALL marcar el archivo original como deprecado inmediatamente
4. WHEN se preserva funcionalidad THEN todos los tests existentes SHALL seguir pasando después de actualizar imports
5. WHEN se mantiene compatibilidad THEN el sistema SHALL asegurar que la funcionalidad no cambie durante la migración

### Requirement 4

**User Story:** Como desarrollador, quiero identificar y migrar solo archivos con uso activo, para limpiar código obsoleto durante el proceso.

#### Acceptance Criteria

1. WHEN se analiza un archivo THEN el sistema SHALL verificar si tiene referencias activas en el código
2. WHEN un archivo no tiene uso THEN el sistema SHALL omitirlo de la migración
3. WHEN se detecta código duplicado THEN el sistema SHALL consolidar en el shared kernel si es compartido
4. WHEN se identifica código específico THEN el sistema SHALL moverlo al bounded context apropiado
5. WHEN se completa la migración THEN el sistema SHALL generar un reporte de archivos obsoletos no migrados

### Requirement 5

**User Story:** Como desarrollador, quiero migrar el Article bounded context primero, para establecer el patrón que seguirán los demás contextos.

#### Acceptance Criteria

1. WHEN se migra Article context THEN el sistema SHALL incluir aggregates, entities, value objects, events, services, factories y repositories del dominio
2. WHEN se migra la capa application THEN el sistema SHALL incluir commands, queries, event handlers e interfaces
3. WHEN se migra infrastructure THEN el sistema SHALL incluir persistence (mappers, ORM models), messaging, http y events
4. WHEN se migra api THEN el sistema SHALL incluir routers y schemas específicos de articles
5. WHEN se completa Article context THEN el sistema SHALL servir como template para Source y Fetching contexts

### Requirement 6

**User Story:** Como desarrollador, quiero un shared kernel bien definido, para compartir código común entre bounded contexts sin duplicación.

#### Acceptance Criteria

1. WHEN se crea el shared kernel THEN el sistema SHALL incluir abstracciones base (AggregateRoot, Entity, ValueObject, DomainEvent)
2. WHEN se define el kernel THEN el sistema SHALL incluir interfaces comunes (ICommand, IQuery, IMediator, IEventBus, IRepository)
3. WHEN se organiza el kernel THEN el sistema SHALL incluir utilidades compartidas (logger, event bus, dependency injection)
4. WHEN se usa el kernel THEN todos los bounded contexts SHALL importar desde shared/kernel
5. WHEN se modifica el kernel THEN los cambios SHALL afectar a todos los contextos que lo usan

### Requirement 7

**User Story:** Como desarrollador, quiero mantener la separación de capas de Clean Architecture, para preservar la independencia del dominio.

#### Acceptance Criteria

1. WHEN se organiza domain layer THEN el sistema SHALL incluir solo lógica de negocio pura sin dependencias de frameworks
2. WHEN se organiza application layer THEN el sistema SHALL incluir casos de uso que orquestan el dominio
3. WHEN se organiza infrastructure layer THEN el sistema SHALL incluir implementaciones técnicas de interfaces del dominio
4. WHEN se organiza api layer THEN el sistema SHALL incluir solo endpoints REST y validación de entrada
5. WHEN se verifica separación THEN domain layer SHALL no tener imports de application, infrastructure o api

### Requirement 8

**User Story:** Como desarrollador, quiero actualizar solo los imports necesarios, para que el código migrado funcione en la nueva estructura.

#### Acceptance Criteria

1. WHEN se actualiza un import THEN el sistema SHALL cambiar rutas de `src.domain.aggregates.article` a `src.article.domain.aggregates.article`
2. WHEN se actualiza un import del shared kernel THEN el sistema SHALL usar `src.shared.kernel.*`
3. WHEN se mantiene compatibilidad THEN los imports relativos SHALL convertirse a absolutos
4. WHEN se verifica corrección THEN el sistema SHALL ejecutar verificación de imports con mypy
5. WHEN se detecta import roto THEN el sistema SHALL reportar el error antes de continuar

### Requirement 9

**User Story:** Como desarrollador, quiero migrar Source y Fetching contexts después de Article, para aplicar las lecciones aprendidas.

#### Acceptance Criteria

1. WHEN se migra Source context THEN el sistema SHALL seguir el mismo patrón establecido por Article context
2. WHEN se migra Fetching context THEN el sistema SHALL incluir process managers en la capa application
3. WHEN se identifican dependencias cruzadas THEN el sistema SHALL usar eventos de dominio para comunicación entre contextos
4. WHEN se completan los tres contextos THEN el sistema SHALL tener una estructura consistente
5. WHEN se verifica integridad THEN todos los tests SHALL pasar con la nueva estructura

### Requirement 10

**User Story:** Como desarrollador, quiero un proceso de migración incremental con limpieza entre tareas, para mantener el código limpio y validar cada paso.

#### Acceptance Criteria

1. WHEN se completa una tarea de migración THEN el sistema SHALL ejecutar todos los tests relacionados
2. WHEN todos los tests pasan THEN el sistema SHALL verificar que no existan deprecation warnings en los logs
3. WHEN no hay warnings THEN el sistema SHALL eliminar los archivos deprecados de esa tarea
4. WHEN se detecta un test fallido o warning THEN el sistema SHALL detener la eliminación hasta resolver el problema
5. WHEN se completa la migración completa THEN el sistema SHALL generar documentación y reporte final

### Requirement 11

**User Story:** Como desarrollador, quiero preservar la funcionalidad de dependency injection, para que los containers sigan funcionando con la nueva estructura.

#### Acceptance Criteria

1. WHEN se migran containers THEN el sistema SHALL actualizar las rutas de importación en bootstrap/containers
2. WHEN se organizan containers THEN cada bounded context SHALL tener su propio container
3. WHEN se mantiene el shared infrastructure THEN el sistema SHALL tener un container compartido para logger, event bus y mediator
4. WHEN se registran handlers THEN el sistema SHALL mantener el patrón de registro actual
5. WHEN se inicializa la aplicación THEN todos los containers SHALL cargarse correctamente

### Requirement 12

**User Story:** Como desarrollador, quiero mantener la compatibilidad con la API REST existente, para que los clientes no se vean afectados.

#### Acceptance Criteria

1. WHEN se migran routers THEN los endpoints SHALL mantener las mismas rutas y contratos
2. WHEN se organizan schemas THEN cada bounded context SHALL tener sus propios schemas de request/response
3. WHEN se actualizan dependencies THEN los routers SHALL usar los nuevos paths de importación
4. WHEN se ejecuta la API THEN todos los endpoints SHALL responder correctamente
5. WHEN se verifica compatibilidad THEN los tests E2E SHALL pasar sin modificaciones

### Requirement 13

**User Story:** Como desarrollador, quiero deprecar archivos antes de eliminarlos, para detectar dependencias no migradas y evitar regresiones.

#### Acceptance Criteria

1. WHEN se copia un archivo a la nueva estructura THEN el sistema SHALL agregar un decorador @deprecated al archivo original
2. WHEN se usa código deprecado THEN el sistema SHALL emitir una advertencia en los logs indicando el archivo y la ubicación del uso
3. WHEN se completa una tarea de migración THEN el sistema SHALL verificar que no existan warnings de deprecación en los logs
4. WHEN no existen warnings de deprecación THEN el sistema SHALL verificar que todos los tests pasen
5. WHEN se confirma seguridad THEN el sistema SHALL eliminar los archivos deprecados al final de cada tarea

### Requirement 14

**User Story:** Como desarrollador, quiero un proceso de eliminación segura, para asegurar que no se eliminen archivos con dependencias activas.

#### Acceptance Criteria

1. WHEN se marca un archivo para eliminación THEN el sistema SHALL buscar todas las referencias al archivo en el código
2. WHEN se encuentran referencias THEN el sistema SHALL reportar error y detener la eliminación
3. WHEN no se encuentran referencias THEN el sistema SHALL ejecutar la suite completa de tests
4. WHEN todos los tests pasan THEN el sistema SHALL revisar los logs de las últimas ejecuciones buscando deprecation warnings
5. WHEN no hay warnings y tests pasan THEN el sistema SHALL eliminar el archivo deprecado de forma segura
