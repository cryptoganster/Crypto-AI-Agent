# Requirements Document

## Introducción

Este documento define los requisitos para extraer y gestionar las configuraciones de sources (fuentes RSS) desde la base de datos hacia archivos de configuración estáticos, permitiendo un acceso más eficiente y versionado de las configuraciones de scraping.

## Glossary

- **Source**: Fuente RSS de la cual se obtienen artículos
- **Scraping Config**: Configuración JSON que define cómo extraer contenido de una source específica (selectores CSS, timeouts, estrategias de espera)
- **Configuration File**: Archivo estático (Python, YAML o JSON) que contiene las configuraciones de sources
- **Domain Pattern**: Patrón de configuración reutilizable basado en el dominio del sitio web
- **Content Selector**: Selector CSS usado para identificar el contenido principal de un artículo
- **Excluded Selector**: Selector CSS usado para identificar elementos a excluir (ads, banners, etc.)
- **Wait Strategy**: Estrategia de espera para contenido dinámico (domcontentloaded, networkidle, etc.)

## Requirements

### Requirement 1

**User Story:** Como desarrollador, quiero extraer las configuraciones de sources desde la base de datos a archivos estáticos, para poder versionarlas en Git y acceder a ellas sin consultas a la DB.

#### Acceptance Criteria

1. WHEN el sistema inicia THEN el sistema SHALL cargar las configuraciones de sources desde archivos estáticos en lugar de la base de datos
2. WHEN se necesita la configuración de scraping de una source THEN el sistema SHALL obtenerla desde memoria sin consultar la base de datos
3. WHEN se modifica una configuración en el archivo estático THEN el sistema SHALL aplicar los cambios después de reiniciar
4. WHEN una source no tiene configuración definida THEN el sistema SHALL usar una configuración por defecto basada en el dominio
5. WHEN se agrega una nueva source THEN el desarrollador SHALL poder agregar su configuración al archivo estático

### Requirement 2

**User Story:** Como desarrollador, quiero organizar las configuraciones por dominio o patrón, para reducir duplicación y facilitar el mantenimiento.

#### Acceptance Criteria

1. WHEN múltiples sources comparten el mismo dominio base THEN el sistema SHALL permitir definir una configuración base reutilizable
2. WHEN una source específica necesita configuración personalizada THEN el sistema SHALL permitir sobrescribir la configuración base
3. WHEN se define un patrón de dominio (ej: "*.cointelegraph.com") THEN el sistema SHALL aplicar la configuración a todas las sources que coincidan
4. WHEN se consulta la configuración de una source THEN el sistema SHALL resolver la jerarquía (específica > dominio > default)
5. WHEN se documenta una configuración THEN el sistema SHALL incluir comentarios explicando los selectores y estrategias

### Requirement 3

**User Story:** Como desarrollador, quiero validar las configuraciones de scraping al inicio del sistema, para detectar errores de configuración tempranamente.

#### Acceptance Criteria

1. WHEN el sistema carga las configuraciones THEN el sistema SHALL validar que todos los campos requeridos estén presentes
2. WHEN una configuración tiene selectores CSS inválidos THEN el sistema SHALL registrar un warning pero continuar
3. WHEN una configuración tiene timeouts fuera de rango THEN el sistema SHALL usar valores por defecto y registrar un warning
4. WHEN faltan configuraciones para sources activas THEN el sistema SHALL registrar un error y usar configuración por defecto
5. WHEN se detectan configuraciones duplicadas THEN el sistema SHALL registrar un warning indicando el conflicto

### Requirement 4

**User Story:** Como desarrollador, quiero migrar las configuraciones existentes desde la DB a archivos estáticos, para no perder las configuraciones actuales.

#### Acceptance Criteria

1. WHEN se ejecuta el script de migración THEN el sistema SHALL extraer todas las configuraciones de la tabla sources
2. WHEN se extraen las configuraciones THEN el sistema SHALL formatearlas en el formato del archivo estático elegido
3. WHEN se generan los archivos de configuración THEN el sistema SHALL preservar todos los campos de scraping_config
4. WHEN se completa la migración THEN el sistema SHALL generar un reporte de las sources migradas
5. WHEN hay configuraciones con valores NULL THEN el sistema SHALL usar valores por defecto apropiados

### Requirement 5

**User Story:** Como desarrollador, quiero que las configuraciones sean fáciles de leer y modificar, para poder ajustar selectores y estrategias rápidamente.

#### Acceptance Criteria

1. WHEN se visualiza un archivo de configuración THEN el formato SHALL ser legible y bien estructurado
2. WHEN se documenta un selector CSS THEN el sistema SHALL incluir comentarios explicando qué elemento selecciona
3. WHEN se define una estrategia de espera THEN el sistema SHALL incluir comentarios explicando cuándo usarla
4. WHEN se agrupan configuraciones THEN el sistema SHALL organizarlas por dominio o categoría
5. WHEN se usan valores por defecto THEN el sistema SHALL documentar claramente cuáles son los defaults

### Requirement 6

**User Story:** Como desarrollador, quiero que el sistema soporte hot-reload de configuraciones en desarrollo, para poder probar cambios sin reiniciar.

#### Acceptance Criteria

1. WHEN el sistema está en modo development THEN el sistema SHALL detectar cambios en archivos de configuración
2. WHEN se modifica un archivo de configuración THEN el sistema SHALL recargar las configuraciones automáticamente
3. WHEN se recarga una configuración THEN el sistema SHALL validar la nueva configuración antes de aplicarla
4. WHEN una recarga falla por configuración inválida THEN el sistema SHALL mantener la configuración anterior y registrar el error
5. WHEN el sistema está en modo production THEN el hot-reload SHALL estar deshabilitado

### Requirement 7

**User Story:** Como desarrollador, quiero acceder a las configuraciones a través de una interface clara, para no depender de la estructura interna de los archivos.

#### Acceptance Criteria

1. WHEN se necesita la configuración de una source THEN el sistema SHALL proporcionar un método `get_source_config(source_id)`
2. WHEN se consulta una configuración por dominio THEN el sistema SHALL proporcionar un método `get_config_by_domain(domain)`
3. WHEN se listan todas las configuraciones THEN el sistema SHALL proporcionar un método `list_all_configs()`
4. WHEN se verifica si existe una configuración THEN el sistema SHALL proporcionar un método `has_config(source_id)`
5. WHEN se obtiene la configuración por defecto THEN el sistema SHALL proporcionar un método `get_default_config()`

## Configuraciones Actuales Identificadas

Basado en la consulta a la DB, las sources actuales tienen:

### Campos de Scraping Config (JSONB)
- `scroll_needed`: boolean - Si se necesita scroll para cargar contenido
- `wait_strategy`: string - Estrategia de espera (domcontentloaded, networkidle, etc.)
- `wait_timeout_ms`: integer - Timeout de espera en milisegundos
- `selector_timeout_ms`: integer - Timeout para selectores CSS
- `content_selectors`: array[string] - Selectores CSS para contenido principal
- `excluded_selectors`: array[string] - Selectores CSS para elementos a excluir
- `fallback_selectors`: array[string] - Selectores CSS de respaldo
- `excluded_texts`: array[string] - Textos específicos a excluir
- `excluded_text_patterns`: array[string] - Patrones de texto a excluir

### Campos Adicionales de Source
- `fetch_interval_minutes`: integer - Intervalo de fetch
- `timeout_seconds`: integer - Timeout general
- `max_retries`: integer - Reintentos máximos
- `user_agent`: string - User agent personalizado
- `follow_redirects`: boolean - Seguir redirects
- `verify_ssl`: boolean - Verificar SSL
- `custom_headers`: jsonb - Headers HTTP personalizados
- `configuration`: jsonb - Configuración general adicional

## Notas de Implementación

- Las configuraciones actuales son muy detalladas y específicas por source
- Hay patrones comunes entre sources del mismo dominio (ej: cointelegraph, coindesk)
- Los selectores CSS son extensos y requieren mantenimiento
- Las configuraciones deben ser fáciles de actualizar cuando los sitios cambian su estructura
