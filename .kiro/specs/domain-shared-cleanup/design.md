# Design Document: Domain Shared Cleanup

## Overview

Este diseño describe el proceso para analizar, consolidar y limpiar las clases en `src/domain/shared/`. El objetivo es mantener un dominio limpio eliminando clases huérfanas, consolidando duplicados, e integrando clases útiles donde corresponda.

## Architecture

### Análisis Inicial

Basado en el análisis del codebase, se identificaron:

**Clases USADAS (15):**
- `deprecated` (decorator)
- `ErrorDetails`
- `CategoryCollection`
- `ContentQuality`
- `QualityLevel`
- `QualityAssessment`
- `TagCollection`
- `QualityThreshold`
- `Language`
- `ContentHash`
- `DeduplicationStrategy`
- `SimilarityScore`
- `SimilarityType`
- `SimilarityScores`
- `SimilarityWeights`

**Clases HUÉRFANAS (5):**
- `MetricType` - Solo exportado en `__init__.py`, no usado en código
- `DomainSimilarityScore` - Solo exportado en `__init__.py`, no usado en código
- `PatternSimilarityWeights` - Solo exportado en `__init__.py`, no usado en código
- `SimilarityExplanation` - Solo exportado en `__init__.py`, no usado en código
- `SimilarityThreshold` - Solo exportado en `__init__.py`, no usado en código

**Clases DUPLICADAS (1):**
- `MetricType` - Existe en `src/domain/shared/value_objects/classification/` Y en `src/domain/value_objects/classification/`

## Components and Interfaces

### 1. Análisis de Uso

**Componente**: `UsageAnalyzer`

**Responsabilidad**: Analizar imports y uso de clases en el codebase

**Métodos**:
- `analyze_class_usage(class_name: str) -> UsageReport`
- `find_all_imports(class_name: str) -> List[str]`
- `is_orphaned(class_name: str) -> bool`

### 2. Detector de Duplicados

**Componente**: `DuplicateDetector`

**Responsabilidad**: Identificar clases duplicadas por nombre y funcionalidad

**Métodos**:
- `find_duplicates() -> List[DuplicatePair]`
- `compare_functionality(class1: str, class2: str) -> SimilarityScore`
- `recommend_consolidation(duplicate_pair: DuplicatePair) -> ConsolidationPlan`
- `prioritize_non_shared_version(duplicate_pair: DuplicatePair) -> str` - Siempre recomienda mantener versión fuera de shared/

### 2.1. Analizador Exhaustivo de Clases

**Componente**: `ExhaustiveClassAnalyzer`

**Responsabilidad**: Generar informe detallado de cada clase

**Métodos**:
- `analyze_class(class_path: str) -> ClassAnalysisReport`
- `find_real_usage(class_name: str) -> List[UsageExample]` - No solo imports, sino uso real
- `find_tests(class_name: str) -> List[str]`
- `find_dependencies(class_name: str) -> List[str]`
- `find_dependents(class_name: str) -> List[str]`
- `get_last_modified(class_path: str) -> datetime`
- `count_lines_of_code(class_path: str) -> int`
- `generate_recommendation(analysis: ClassAnalysisReport) -> Recommendation`

### 3. Integrador de Clases

**Componente**: `ClassIntegrator`

**Responsabilidad**: Proponer e implementar integración de clases huérfanas útiles

**Métodos**:
- `find_integration_opportunities(class_name: str) -> List[IntegrationOpportunity]`
- `propose_integration(opportunity: IntegrationOpportunity) -> IntegrationPlan`
- `apply_integration(plan: IntegrationPlan) -> IntegrationResult`

### 4. Limpiador de Clases

**Componente**: `ClassCleaner`

**Responsabilidad**: Eliminar clases huérfanas sin uso potencial

**Métodos**:
- `can_be_removed(class_name: str) -> bool`
- `remove_class(class_name: str) -> RemovalResult`
- `update_init_files() -> None`

## Data Models

### ClassAnalysisReport

```python
@dataclass
class ClassAnalysisReport:
    # 1. Ubicación
    class_name: str
    file_path: str
    module_path: str
    
    # 2. Métricas de código
    lines_of_code: int
    complexity_score: float
    
    # 3. Uso
    import_locations: List[str]
    real_usage_examples: List[UsageExample]
    usage_count: int
    is_used: bool
    
    # 4. Tests
    test_files: List[str]
    test_coverage: float
    
    # 5. Duplicados
    duplicates: List[str]
    is_duplicate: bool
    
    # 6. Dependencias
    dependencies: List[str]  # Clases que usa
    dependents: List[str]    # Clases que la usan
    
    # 7. Metadata
    last_modified: datetime
    author: str
    
    # 8. Recomendación
    recommendation: Recommendation
    recommendation_reason: str
    
    # 9. Potencial de integración
    integration_opportunities: List[IntegrationOpportunity]
    
    # 10. Notas adicionales
    notes: str

@dataclass
class UsageExample:
    file_path: str
    line_number: int
    code_snippet: str
    context: str
```

### DuplicatePair

```python
@dataclass
class DuplicatePair:
    class1_path: str
    class2_path: str
    similarity_score: float
    recommended_keeper: str
    reason: str
```

### IntegrationOpportunity

```python
@dataclass
class IntegrationOpportunity:
    orphaned_class: str
    target_location: str
    use_case: str
    confidence: float
    benefits: List[str]
```

### CleanupReport

```python
@dataclass
class CleanupReport:
    # Executive Summary
    total_classes_analyzed: int
    classes_used: int
    classes_orphaned: int
    classes_duplicated: int
    
    # Detailed Analysis
    class_reports: List[ClassAnalysisReport]
    
    # Actions Taken
    classes_kept: List[str]
    classes_removed: List[str]
    classes_consolidated: List[DuplicatePair]
    classes_integrated: List[IntegrationOpportunity]
    
    # Metrics
    total_lines_removed: int
    total_imports_updated: int
    tests_affected: int
    
    # Metadata
    timestamp: datetime
    duration: timedelta
    
    # Recommendations
    future_actions: List[str]
    warnings: List[str]

@dataclass
class Recommendation(Enum):
    KEEP = "keep"
    REMOVE = "remove"
    CONSOLIDATE = "consolidate"
    INTEGRATE = "integrate"
    EVALUATE = "evaluate"
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Análisis completo de clases

*For any* directorio en `src/domain/shared/`, el análisis debe identificar todas las clases Python definidas
**Validates: Requirements 1.1**

### Property 2: Detección correcta de imports

*For any* clase analizada, si existe un import de esa clase en el codebase, debe ser detectado y listado
**Validates: Requirements 1.2, 1.4**

### Property 3: Clasificación correcta de huérfanas

*For any* clase sin imports, debe ser marcada como "huérfana" en el reporte
**Validates: Requirements 1.3**

### Property 4: Identificación de duplicados por nombre

*For any* par de clases con nombres idénticos en diferentes ubicaciones, deben ser identificadas como duplicadas
**Validates: Requirements 2.1**

### Property 5: Preservación de funcionalidad

*For any* clase eliminada, todos los tests existentes deben seguir pasando después de la eliminación
**Validates: Requirements 3.3**

### Property 6: Actualización de exports

*For any* clase eliminada, el archivo `__init__.py` correspondiente debe ser actualizado para remover el export
**Validates: Requirements 3.4**

### Property 7: Consolidación de imports

*For any* clase consolidada, todos los imports de la clase eliminada deben ser actualizados para usar la clase mantenida
**Validates: Requirements 2.5**

### Property 8: Integridad del reporte

*For any* operación de limpieza completada, el reporte debe incluir todas las clases analizadas, eliminadas, consolidadas e integradas
**Validates: Requirements 5.1, 5.2, 5.3, 5.4, 5.5**

## Error Handling

### Errores de Análisis

- **ClassNotFoundError**: Cuando una clase referenciada no existe
- **ImportAnalysisError**: Cuando falla el análisis de imports
- **DuplicateDetectionError**: Cuando falla la detección de duplicados

### Errores de Consolidación

- **ConsolidationError**: Cuando falla la consolidación de duplicados
- **ImportUpdateError**: Cuando falla la actualización de imports
- **TestFailureError**: Cuando los tests fallan después de consolidación

### Errores de Eliminación

- **RemovalError**: Cuando falla la eliminación de una clase
- **InitFileUpdateError**: Cuando falla la actualización de `__init__.py`

## Testing Strategy

### Unit Tests

- Test de análisis de uso para clases conocidas
- Test de detección de duplicados con casos conocidos
- Test de actualización de imports
- Test de eliminación de clases
- Test de generación de reportes

### Property-Based Tests

Se usará `hypothesis` para property-based testing en Python.

**Configuración**: Cada test ejecutará mínimo 100 iteraciones.

**Tests a implementar**:

1. **Test de análisis completo** (Property 1)
   - Generar estructuras de directorios aleatorias
   - Verificar que todas las clases sean detectadas

2. **Test de detección de imports** (Property 2)
   - Generar archivos Python con imports aleatorios
   - Verificar que todos los imports sean detectados

3. **Test de clasificación de huérfanas** (Property 3)
   - Generar clases con y sin imports
   - Verificar clasificación correcta

4. **Test de preservación de funcionalidad** (Property 5)
   - Simular eliminación de clases
   - Verificar que tests sigan pasando

### Integration Tests

- Test de flujo completo de análisis → consolidación → limpieza
- Test de actualización de múltiples archivos
- Test de generación de reporte final

## Implementation Plan

### Fase 1: Análisis

1. Implementar `UsageAnalyzer` para detectar uso de clases
2. Generar reporte inicial de todas las clases
3. Clasificar clases en: usadas, huérfanas, duplicadas

### Fase 2: Análisis Exhaustivo de Cada Clase

Para CADA clase en `src/domain/shared/`, generar informe detallado:

**Informe por Clase debe incluir:**
1. **Ubicación**: Path completo del archivo
2. **Líneas de código**: Número de líneas
3. **Imports encontrados**: Lista completa de archivos que importan la clase
4. **Uso real**: Ejemplos de uso en el código (no solo imports)
5. **Tests existentes**: Tests que cubren la clase
6. **Duplicados**: Si existe versión similar en otro lugar
7. **Dependencias**: Qué otras clases usa
8. **Dependientes**: Qué otras clases la usan
9. **Última modificación**: Fecha del último cambio
10. **Recomendación**: MANTENER / ELIMINAR / CONSOLIDAR / INTEGRAR

### Fase 3: Consolidación de Duplicados

**Regla de Prioridad**: Siempre mantener versiones FUERA de `shared/`, eliminar de `shared/`

**MetricType**: 
- **Ubicaciones**: 
  - `src/domain/shared/value_objects/classification/metric_type.py`
  - `src/domain/value_objects/classification/metric_type.py`
- **Decisión**: ELIMINAR de `shared/`, MANTENER en `domain/value_objects/`
- **Razón**: Prioridad a duplicados fuera de shared
- **Acción**: 
  1. Verificar que ambas versiones sean idénticas
  2. Actualizar imports en `src/domain/shared/value_objects/__init__.py` para importar desde `domain/value_objects/`
  3. Eliminar archivo de `shared/`
  4. Verificar tests

### Fase 4: Evaluación Exhaustiva de Clases Huérfanas

**Para cada clase sin uso directo, analizar:**

**DomainSimilarityScore**:
- **Análisis completo**: Buscar palabras clave: "domain", "similarity", "score", "subdomain"
- **Uso potencial**: Detección de artículos duplicados del mismo dominio
- **Integración propuesta**: `ArticleSimilarityService` para comparar dominios
- **Decisión**: MANTENER con documentación de uso futuro

**PatternSimilarityWeights**:
- **Análisis completo**: Buscar palabras clave: "pattern", "url", "path", "query"
- **Uso potencial**: Análisis de patrones de URL en detección de duplicados
- **Integración propuesta**: `ArticleDeduplicationService` para análisis de patrones
- **Decisión**: MANTENER con documentación de uso futuro

**SimilarityExplanation**:
- **Análisis completo**: Buscar palabras clave: "explanation", "reason", "why", "duplicate"
- **Uso potencial**: Explicar a usuarios por qué dos artículos son similares
- **Integración propuesta**: API responses para mostrar razones de similitud
- **Decisión**: MANTENER con documentación de uso futuro

**SimilarityThreshold**:
- **Análisis completo**: Buscar palabras clave: "threshold", "similarity", "duplicate"
- **Comparación con**: `QualityThreshold` (propósito diferente)
- **Uso potencial**: Configurar umbrales de similitud para detección de duplicados
- **Integración propuesta**: Comandos de fetch para filtrar duplicados
- **Decisión**: MANTENER - propósito de dominio diferente a `QualityThreshold`

### Fase 5: Generación de Informe Exhaustivo

**Crear archivo**: `docs/domain-shared-analysis-report.md`

**Contenido del informe:**

1. **Executive Summary**
   - Total de clases analizadas
   - Clases usadas vs huérfanas
   - Duplicados encontrados
   - Recomendaciones principales

2. **Análisis Detallado por Clase** (para TODAS las clases)
   - Sección individual para cada clase con los 10 puntos del informe
   - Gráfico de dependencias
   - Ejemplos de uso real

3. **Matriz de Duplicados**
   - Tabla comparativa de clases duplicadas
   - Diferencias entre versiones
   - Recomendación de consolidación

4. **Clases Huérfanas con Potencial**
   - Lista de clases sin uso actual
   - Casos de uso propuestos
   - Plan de integración futura

5. **Plan de Acción**
   - Clases a eliminar (con justificación)
   - Clases a consolidar (con mapeo)
   - Clases a mantener (con documentación)
   - Clases a integrar (con ubicaciones)

### Fase 6: Verificación Doble (Automática + Manual)

**Verificación Automática:**
1. Ejecutar script de análisis exhaustivo
2. Generar informe preliminar
3. Ejecutar todos los tests
4. Verificar que no hay imports rotos

**Verificación Manual (CRÍTICA):**
1. **Revisar informe automático** - No confiar 100% en resultados del script
2. **Inspección manual de cada clase** - Abrir archivos y verificar uso real
3. **Validar recomendaciones** - Confirmar que decisiones automáticas son correctas
4. **Buscar falsos positivos** - Clases marcadas como "no usadas" que sí se usan
5. **Buscar falsos negativos** - Clases marcadas como "usadas" que no se usan realmente
6. **Verificar contexto de negocio** - Entender propósito de dominio de cada clase
7. **Consultar con equipo** - Discutir decisiones importantes antes de eliminar

**Checklist de Verificación Manual:**
- [ ] Revisar TODAS las clases marcadas para eliminación
- [ ] Verificar manualmente que no hay uso oculto (reflection, dynamic imports, etc.)
- [ ] Confirmar que duplicados son realmente idénticos
- [ ] Validar que tests cubren funcionalidad crítica
- [ ] Revisar historial de commits para entender propósito original
- [ ] Buscar TODOs o comentarios que indiquen uso futuro
- [ ] Verificar documentación externa (ADRs, wikis, etc.)

**Proceso de Doble Check:**
```
1. Script genera recomendación → 
2. Humano revisa y valida → 
3. Si hay duda, investigar más → 
4. Solo proceder si hay certeza 100%
```

### Fase 7: Limpieza (Solo Después de Verificación Manual)

1. Consolidar `MetricType` (eliminar de shared, mantener en domain/value_objects)
2. Actualizar todos los imports
3. Actualizar `__init__.py` files
4. Verificar que todos los tests pasen
5. Ejecutar property-based tests
6. **Checkpoint manual**: Revisar cambios antes de commit

### Fase 8: Documentación

1. Finalizar reporte de análisis exhaustivo
2. Actualizar documentación de arquitectura
3. Documentar casos de uso de clases mantenidas
4. Crear ADR (Architecture Decision Record) para decisiones importantes
5. Documentar proceso de verificación manual realizado
6. Registrar lecciones aprendidas

## Análisis Exhaustivo Requerido

### Metodología de Análisis

Para cada clase en `src/domain/shared/`, se debe:

1. **Análisis Estático**
   - Contar líneas de código
   - Identificar imports (qué usa)
   - Identificar dependientes (quién la usa)
   - Calcular complejidad ciclomática

2. **Análisis de Uso**
   - Buscar imports de la clase
   - Buscar uso REAL (no solo imports)
   - Identificar patrones de uso
   - Determinar frecuencia de uso

3. **Análisis de Tests**
   - Encontrar tests unitarios
   - Encontrar tests de integración
   - Calcular cobertura
   - Verificar calidad de tests

4. **Análisis de Duplicados**
   - Buscar clases con mismo nombre
   - Comparar funcionalidad
   - Identificar diferencias
   - Recomendar consolidación

5. **Análisis de Potencial**
   - Buscar palabras clave relacionadas
   - Identificar casos de uso potenciales
   - Evaluar valor de dominio
   - Proponer integraciones

6. **Análisis de Metadata**
   - Fecha de última modificación
   - Autor original
   - Historial de cambios
   - Comentarios y documentación

### Criterios de Decisión

**MANTENER si:**
- Tiene uso activo en el código
- Tiene tests con buena cobertura
- Representa concepto de dominio importante
- Tiene potencial de uso futuro claro

**ELIMINAR si:**
- No tiene uso en el código
- No tiene tests
- No representa concepto de dominio relevante
- No tiene potencial de uso futuro

**CONSOLIDAR si:**
- Existe duplicado en otra ubicación
- Versión fuera de shared/ es preferida
- Funcionalidad es idéntica o similar

**INTEGRAR si:**
- No tiene uso actual pero es útil
- Casos de uso claros identificados
- Mejora calidad del código existente

## Decisiones de Diseño

### 1. Prioridad a Versiones Fuera de Shared

**Decisión**: Cuando existe duplicado, siempre mantener versión FUERA de `src/domain/shared/` y eliminar la de shared.

**Razón**: 
- `shared/` debe contener solo Value Objects verdaderamente compartidos entre múltiples bounded contexts
- Value Objects específicos de un contexto deben vivir en ese contexto
- Reduce acoplamiento entre módulos

**Alternativa considerada**: Mantener versión en shared y eliminar otras.

**Por qué se rechazó**: Viola principio de separación de contextos. Shared debe ser minimal.

### 2. Mantener Clases de Similitud

**Decisión**: Mantener `DomainSimilarityScore`, `PatternSimilarityWeights`, `SimilarityExplanation`, y `SimilarityThreshold` aunque actualmente no se usen.

**Razón**: Estas clases forman un sistema cohesivo de análisis de similitud que será útil cuando se implemente detección avanzada de duplicados. Son Value Objects bien diseñados que encapsulan lógica de dominio importante.

**Alternativa considerada**: Eliminarlas y recrearlas cuando se necesiten.

**Por qué se rechazó**: Recrear Value Objects bien diseñados es costoso y propenso a errores. Es mejor mantenerlos documentados para uso futuro.

### 2. Consolidar MetricType

**Decisión**: Eliminar `MetricType` de `src/domain/shared/` y mantener solo la versión en `src/domain/value_objects/`.

**Razón**: Tener dos versiones idénticas causa confusión y viola DRY. La versión en `domain/value_objects` es la que se usa actualmente.

**Alternativa considerada**: Mantener ambas versiones.

**Por qué se rechazó**: Duplicación innecesaria que dificulta mantenimiento.

### 3. No Consolidar SimilarityThreshold con QualityThreshold

**Decisión**: Mantener `SimilarityThreshold` y `QualityThreshold` como clases separadas.

**Razón**: Aunque ambas representan umbrales (0.0-1.0), tienen propósitos de dominio diferentes:
- `QualityThreshold`: Umbral de calidad de contenido (legibilidad, unicidad, etc.)
- `SimilarityThreshold`: Umbral de similitud entre artículos (para detección de duplicados)

**Alternativa considerada**: Crear un `Threshold` genérico.

**Por qué se rechazó**: Perdería semántica de dominio específica. Los Value Objects deben ser específicos del dominio.

## Limitaciones del Análisis Automático

### Casos que el Script NO Puede Detectar

1. **Imports Dinámicos**
   ```python
   module_name = "src.domain.shared.value_objects.similarity"
   module = importlib.import_module(module_name)
   ```

2. **Uso via Reflection**
   ```python
   class_name = "SimilarityScore"
   cls = getattr(module, class_name)
   ```

3. **Uso en Strings/Templates**
   ```python
   template = "Use {SimilarityScore} for analysis"
   ```

4. **Uso en Configuración Externa**
   - Archivos YAML/JSON que referencian clases
   - Variables de entorno
   - Configuración de frameworks

5. **Uso Futuro Planificado**
   - TODOs en código
   - Tickets/issues abiertos
   - Roadmap del proyecto

6. **Uso en Branches No Mergeados**
   - Features en desarrollo
   - Pull requests pendientes

### Por Qué la Verificación Manual es CRÍTICA

- **Falsos positivos**: Script puede marcar clase como "no usada" cuando sí se usa
- **Contexto de negocio**: Solo humanos entienden propósito de dominio
- **Decisiones estratégicas**: Eliminar clase puede afectar roadmap futuro
- **Riesgo de regresión**: Eliminar clase usada rompe producción

### Estrategia de Mitigación

1. **Nunca confiar 100% en script**
2. **Siempre revisar manualmente antes de eliminar**
3. **Cuando hay duda, NO eliminar**
4. **Documentar razones de decisiones**
5. **Hacer cambios incrementales con checkpoints**
6. **Mantener backup antes de eliminar**

## Summary

Este diseño proporciona un plan claro para limpiar `src/domain/shared/`:

1. **Análisis exhaustivo**: 10 puntos por clase, 6 metodologías de análisis
2. **Doble verificación**: Automática + Manual (CRÍTICA)
3. **Prioridad clara**: Mantener versiones fuera de shared, eliminar de shared
4. **Eliminar**: `MetricType` duplicado (después de verificación manual)
5. **Mantener**: Clases de similitud para uso futuro
6. **Documentar**: Informe completo + ADRs + casos de uso
7. **Verificar**: Tests + revisión manual + checkpoints

**Principio fundamental**: La verificación manual es OBLIGATORIA. El script es una herramienta de ayuda, no la fuente de verdad absoluta.

El resultado será un dominio más limpio y mantenible, con Value Objects bien organizados, documentados, y verificados manualmente.
