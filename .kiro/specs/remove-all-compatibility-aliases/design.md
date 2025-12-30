# Design Document: Eliminación Completa de Alias de Compatibilidad

## Overview

Este documento describe el diseño técnico para eliminar sistemáticamente todos los alias de compatibilidad temporal del proyecto, asegurando que el código quede limpio, consistente y completamente funcional.

### Objetivos

1. **Eliminar 68 alias** de compatibilidad identificados en el inventario
2. **Mantener funcionalidad** verificando con tests antes y después
3. **Procesar por fases** para minimizar riesgos y facilitar debugging
4. **Generar reportes** detallados de cada fase y del proceso completo
5. **Código limpio** sin referencias legacy ni alias temporales

### Alcance

**Incluye**:
- Eliminación de alias en `src/` (68 alias)
- Actualización de referencias en código
- Actualización de `__all__` en `__init__.py`
- Ejecución de tests pre y post eliminación
- Validación de imports
- Actualización de documentación
- Generación de reportes

**Excluye**:
- Type aliases útiles (`Event = IDomainEvent`)
- Property aliases de API pública
- Alias en tests (se actualizan automáticamente)
- Alias en scripts archivados

## Architecture

### Componentes Principales

```
┌─────────────────────────────────────────────────────────┐
│           AliasRemovalOrchestrator                      │
│  (Coordina el proceso completo de eliminación)          │
└─────────────────────────────────────────────────────────┘
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
        ▼                 ▼                 ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ AliasScanner │  │ AliasRemover │  │ TestRunner   │
│              │  │              │  │              │
│ - Identifica │  │ - Actualiza  │  │ - Ejecuta    │
│ - Categoriza │  │ - Elimina    │  │ - Compara    │
│ - Verifica   │  │ - Valida     │  │ - Reporta    │
└──────────────┘  └──────────────┘  └──────────────┘
        │                 │                 │
        └─────────────────┼─────────────────┘
                          ▼
                ┌──────────────────┐
                │  ReportGenerator │
                │                  │
                │  - Estadísticas  │
                │  - Cambios       │
                │  - Resultados    │
                └──────────────────┘
```

### Flujo de Procesamiento por Fases

```
┌─────────────────────────────────────────────────────────┐
│ Fase 0: Preparación                                     │
│ - Ejecutar tests baseline                               │
│ - Cargar inventario de alias                            │
│ - Validar que todos los tests pasan                     │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│ Fase 1: DEPRECATED (6 alias)                            │
│ - EnhancedDomainEventPublisher                          │
│ - InMemoryDomainEventPublisher                          │
│ - LoggingDomainEventPublisher                           │
│ - create_domain_event_publisher                         │
│ - get_domain_event_publisher                            │
│ - set_domain_event_publisher                            │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
                  [Ejecutar Tests]
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│ Fase 2: Shared Kernel (6 alias)                         │
│ - UnitOfWork                                            │
│ - IDomainEvent (auto-ref)                               │
│ - Event (mantener)                                      │
│ - score property (mantener)                             │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
                  [Ejecutar Tests]
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│ Fase 3: RSS Feed (14 alias)                             │
│ - Source → RssFeed                                      │
│ - ISourceReadRepository → IRssFeedReadRepository        │
│ - ISourceWriteRepository → IRssFeedWriteRepository      │
│ - SourceCreated → RssFeedCreated                        │
│ - SourceStatus → RssFeedStatus                          │
│ - SourceName → RssFeedName                              │
│ - SourceHealth → RssFeedHealth                          │
│ - SourceMetadata → RssFeedMetadata                      │
│ - SourceId → RssFeedId                                  │
│ - SourceIdentity → RssFeedIdentity                      │
│ - RssUrl → RssFeedUrl                                   │
│ - SourceUrl → RssFeedUrl                                │
│ - SourceMetrics → RssFeedMetrics                        │
│ - RssSourceMetrics → RssFeedMetrics                     │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
                  [Ejecutar Tests]
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│ Fase 4: RSS Article (35 alias)                          │
│ - Article → RssArticle                                  │
│ - IArticleFactory → IRssArticleFactory                  │
│ - ArticleFactory → RssArticleFactory                    │
│ - IArticleReadRepository → IRssArticleReadRepository    │
│ - IArticleWriteRepository → IRssArticleWriteRepository  │
│ - ArticleId → RssArticleId                              │
│ - ArticleUrl → RssArticleUrl                            │
│ - ArticleAuthor → RssArticleAuthor                      │
│ - ArticleContent → RssArticleContent                    │
│ - ArticleDescription → RssArticleDescription            │
│ - ArticleGuid → RssArticleGuid                          │
│ - ArticlePubDate → RssArticlePubDate                    │
│ - ArticleSummary → RssArticleSummary                    │
│ - ArticleTimestamps → RssArticleTimestamps              │
│ - ArticleDeduplicationResult → RssArticleDedup...       │
│ - ArticleQuality → RssArticleQuality                    │
│ - ArticleDuplicate → RssArticleDuplicate                │
│ - ArticleError → RssArticleError                        │
│ - ArticleMetrics → RssArticleMetrics                    │
│ - ArticleContainer → RssArticleContainer                │
│ - ArticleContentExtractionPipeline → Rss...            │
│ - ArticleContentAnalysisPipeline → Rss...              │
│ - ArticleDTO → ArticleReadModel                         │
│ - ArticleMapper → RssArticleMapper                      │
│ - ArticleReadModelMapper → RssArticleReadModelMapper    │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
                  [Ejecutar Tests]
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│ Fase 5: Chunking (2 alias)                              │
│ - ContentChunk → KnowledgeChunk                         │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
                  [Ejecutar Tests]
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│ Fase 6: Finalización                                    │
│ - Ejecutar tests completos                              │
│ - Validar imports                                       │
│ - Generar reporte final                                 │
│ - Actualizar documentación                              │
└─────────────────────────────────────────────────────────┘
```

## Components and Interfaces

### 1. AliasScanner

**Responsabilidad**: Identificar y categorizar alias en el código.

```python
class AliasInfo:
    """Información de un alias."""
    name: str                    # Nombre del alias
    canonical_name: str          # Nombre canónico
    file_path: str              # Archivo donde está definido
    line_number: int            # Línea de definición
    bounded_context: str        # Bounded context (Shared, RSS Article, etc.)
    priority: str               # DEPRECATED, Evaluar, Mantener
    comment: Optional[str]      # Comentario asociado
    in_all_list: bool          # Si está en __all__

class AliasScanner:
    """Escanea y categoriza alias en el código."""
    
    def scan_directory(self, directory: Path) -> List[AliasInfo]:
        """Escanea directorio y retorna lista de alias encontrados."""
        
    def categorize_by_context(self, aliases: List[AliasInfo]) -> Dict[str, List[AliasInfo]]:
        """Agrupa alias por bounded context."""
        
    def categorize_by_priority(self, aliases: List[AliasInfo]) -> Dict[str, List[AliasInfo]]:
        """Agrupa alias por prioridad."""
        
    def find_alias_usages(self, alias: AliasInfo) -> List[UsageInfo]:
        """Encuentra todos los usos de un alias en el código."""
```

### 2. AliasRemover

**Responsabilidad**: Actualizar referencias y eliminar definiciones de alias.

```python
class UsageInfo:
    """Información de uso de un alias."""
    file_path: str
    line_number: int
    line_content: str
    usage_type: str  # 'import', 'usage', 'type_hint'

class AliasRemover:
    """Remueve alias y actualiza referencias."""
    
    def update_references(self, alias: AliasInfo, usages: List[UsageInfo]) -> List[str]:
        """Actualiza todas las referencias al alias con el nombre canónico."""
        
    def remove_alias_definition(self, alias: AliasInfo) -> None:
        """Elimina la definición del alias del archivo."""
        
    def update_all_list(self, file_path: str, alias_name: str) -> None:
        """Actualiza lista __all__ removiendo el alias."""
        
    def validate_syntax(self, file_path: str) -> bool:
        """Valida que el archivo tiene sintaxis correcta después de cambios."""
```

### 3. TestRunner

**Responsabilidad**: Ejecutar tests y comparar resultados.

```python
class TestResult:
    """Resultado de ejecución de tests."""
    total_tests: int
    passed: int
    failed: int
    skipped: int
    duration: float
    failed_tests: List[str]

class TestRunner:
    """Ejecuta tests y compara resultados."""
    
    def run_all_tests(self) -> TestResult:
        """Ejecuta suite completa de tests."""
        
    def compare_results(self, baseline: TestResult, current: TestResult) -> bool:
        """Compara resultados con baseline."""
        
    def get_failed_test_details(self, test_name: str) -> str:
        """Obtiene detalles de un test fallido."""
```

### 4. ImportValidator

**Responsabilidad**: Validar que imports son correctos.

```python
class ImportValidator:
    """Valida imports después de cambios."""
    
    def validate_module(self, module_path: str) -> Tuple[bool, Optional[str]]:
        """Intenta importar módulo y retorna éxito/error."""
        
    def validate_all_modified_modules(self, modified_files: List[str]) -> Dict[str, Optional[str]]:
        """Valida todos los módulos modificados."""
```

### 5. ReportGenerator

**Responsabilidad**: Generar reportes detallados del proceso.

```python
class PhaseReport:
    """Reporte de una fase."""
    phase_name: str
    aliases_processed: int
    files_modified: int
    lines_changed: int
    test_result: TestResult
    duration: float
    success: bool

class ReportGenerator:
    """Genera reportes del proceso."""
    
    def generate_phase_report(self, phase: PhaseReport) -> str:
        """Genera reporte de una fase."""
        
    def generate_final_report(self, phases: List[PhaseReport]) -> str:
        """Genera reporte final completo."""
        
    def generate_statistics(self, phases: List[PhaseReport]) -> Dict[str, Any]:
        """Genera estadísticas agregadas."""
```

### 6. AliasRemovalOrchestrator

**Responsabilidad**: Coordinar el proceso completo.

```python
class AliasRemovalOrchestrator:
    """Orquesta el proceso completo de eliminación de alias."""
    
    def __init__(
        self,
        scanner: AliasScanner,
        remover: AliasRemover,
        test_runner: TestRunner,
        import_validator: ImportValidator,
        report_generator: ReportGenerator,
    ):
        self._scanner = scanner
        self._remover = remover
        self._test_runner = test_runner
        self._import_validator = import_validator
        self._report_generator = report_generator
    
    def execute(self) -> bool:
        """Ejecuta el proceso completo de eliminación."""
        # 1. Preparación
        # 2. Procesar cada fase
        # 3. Validar y reportar
        
    def process_phase(self, phase_name: str, aliases: List[AliasInfo]) -> PhaseReport:
        """Procesa una fase completa."""
        # 1. Actualizar referencias
        # 2. Eliminar definiciones
        # 3. Ejecutar tests
        # 4. Validar imports
        # 5. Generar reporte
        
    def rollback_phase(self, phase_name: str, modified_files: List[str]) -> None:
        """Revierte cambios de una fase si falla."""
```

## Data Models

### Alias Inventory Structure

```python
{
    "deprecated": [
        {
            "name": "EnhancedDomainEventPublisher",
            "canonical": "EventPublisherWithDispatch",
            "file": "src/shared/infra/event_bus/event_publisher_with_dispatch.py",
            "line": 109,
            "context": "Shared",
            "comment": "# Legacy compatibility alias - DEPRECATED"
        },
        # ... más alias deprecated
    ],
    "shared": [
        {
            "name": "UnitOfWork",
            "canonical": "SqlAlchemyUnitOfWork",
            "file": "src/shared/infra/persistence/sqlalchemy_uow.py",
            "line": 154,
            "context": "Shared",
            "comment": "# Alias para backward compatibility"
        },
        # ... más alias shared
    ],
    "rss_feed": [
        # ... alias de RSS Feed
    ],
    "rss_article": [
        # ... alias de RSS Article
    ],
    "chunking": [
        # ... alias de Chunking
    ],
    "keep": [
        {
            "name": "Event",
            "canonical": "IDomainEvent",
            "file": "src/shared/infra/event_bus/event_publisher.py",
            "line": 12,
            "context": "Shared",
            "comment": "# Type alias para compatibilidad",
            "reason": "Type alias útil para legibilidad"
        }
    ]
}
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Reference Update Completeness
*For any* alias being removed, all references to that alias in the codebase should be updated to use the canonical name before the alias definition is removed.
**Validates: Requirements 2.1, 3.1**

### Property 2: Test Stability
*For any* phase of alias removal, the test suite should pass with the same results before and after the phase completes.
**Validates: Requirements 5.3, 6.3**

### Property 3: Import Validity
*For any* file modified during alias removal, all imports in that file should remain valid and importable after modifications.
**Validates: Requirements 11.2, 11.3**

### Property 4: Syntax Preservation
*For any* file modified during alias removal, the Python syntax should remain valid after all modifications.
**Validates: Requirements 3.3, 4.4**

### Property 5: __all__ Consistency
*For any* alias removed from a module's `__all__` list, the canonical name should remain in `__all__` if it was exported.
**Validates: Requirements 4.5**

### Property 6: Phase Independence
*For any* two consecutive phases, the success of phase N should not depend on whether phase N-1 was executed, only that the codebase is in a valid state.
**Validates: Requirements 7.2, 7.3**

### Property 7: Rollback Completeness
*For any* phase that fails, rolling back should restore all modified files to their exact pre-phase state.
**Validates: Requirements 10.2, 10.3**

### Property 8: Documentation Consistency
*For any* alias removed from code, references to that alias in documentation should be updated to use the canonical name.
**Validates: Requirements 12.2, 12.3**

## Error Handling

### Error Types

1. **TestFailureError**: Tests fallan después de eliminar alias
   - **Acción**: Rollback de la fase, reportar alias problemático
   
2. **ImportError**: Import falla después de actualizar referencias
   - **Acción**: Rollback de la fase, reportar módulo problemático
   
3. **SyntaxError**: Sintaxis inválida después de modificar archivo
   - **Acción**: Rollback del archivo, reportar error de sintaxis
   
4. **AliasNotFoundError**: Alias no encontrado en ubicación esperada
   - **Acción**: Skip alias, reportar en log
   
5. **MultipleDefinitionsError**: Alias definido en múltiples lugares
   - **Acción**: Reportar, requerir intervención manual

### Error Recovery Strategy

```python
try:
    # Procesar fase
    phase_report = orchestrator.process_phase(phase_name, aliases)
    
    if not phase_report.success:
        # Rollback automático
        orchestrator.rollback_phase(phase_name, phase_report.modified_files)
        raise PhaseFailureError(f"Fase {phase_name} falló", phase_report)
        
except TestFailureError as e:
    logger.error(f"Tests fallaron en fase {phase_name}")
    logger.error(f"Tests fallidos: {e.failed_tests}")
    # Rollback ya ejecutado
    return False
    
except ImportError as e:
    logger.error(f"Import falló en fase {phase_name}")
    logger.error(f"Módulo: {e.module}, Error: {e.message}")
    # Rollback ya ejecutado
    return False
```

## Testing Strategy

### Unit Tests

**Objetivo**: Verificar componentes individuales.

```python
# test_alias_scanner.py
def test_scan_directory_finds_all_aliases():
    """Debería encontrar todos los alias en directorio."""
    
def test_categorize_by_context_groups_correctly():
    """Debería agrupar alias por bounded context correctamente."""
    
def test_find_alias_usages_finds_all_references():
    """Debería encontrar todas las referencias a un alias."""

# test_alias_remover.py
def test_update_references_replaces_all_occurrences():
    """Debería reemplazar todas las ocurrencias del alias."""
    
def test_remove_alias_definition_removes_line():
    """Debería eliminar la línea de definición del alias."""
    
def test_update_all_list_removes_alias():
    """Debería remover alias de lista __all__."""

# test_test_runner.py
def test_run_all_tests_executes_suite():
    """Debería ejecutar suite completa de tests."""
    
def test_compare_results_detects_differences():
    """Debería detectar diferencias entre resultados."""
```

### Integration Tests

**Objetivo**: Verificar integración entre componentes.

```python
# test_alias_removal_integration.py
def test_complete_phase_processing():
    """Debería procesar fase completa correctamente."""
    
def test_rollback_restores_files():
    """Debería restaurar archivos en rollback."""
    
def test_import_validation_after_removal():
    """Debería validar imports después de remover alias."""
```

### Property-Based Tests

**Objetivo**: Verificar propiedades universales.

```python
from hypothesis import given, strategies as st

@given(alias_name=st.text(min_size=1), canonical_name=st.text(min_size=1))
def test_reference_update_completeness(alias_name, canonical_name):
    """
    Property 1: Reference Update Completeness
    
    Para cualquier alias, todas las referencias deben actualizarse
    antes de eliminar la definición.
    """
    # Generar código con alias
    # Actualizar referencias
    # Verificar que no quedan referencias al alias
    
@given(phase_aliases=st.lists(st.text()))
def test_test_stability(phase_aliases):
    """
    Property 2: Test Stability
    
    Para cualquier fase, los tests deben pasar igual antes y después.
    """
    # Ejecutar tests antes
    # Procesar fase
    # Ejecutar tests después
    # Comparar resultados
```

### End-to-End Tests

**Objetivo**: Verificar proceso completo.

```python
def test_complete_alias_removal_process():
    """Debería completar proceso completo de eliminación."""
    # 1. Ejecutar baseline tests
    # 2. Procesar todas las fases
    # 3. Verificar que todos los alias fueron eliminados
    # 4. Verificar que tests pasan
    # 5. Verificar que imports son válidos
```

## Performance Considerations

### Optimizaciones

1. **Parallel Processing**: Procesar archivos independientes en paralelo
2. **Caching**: Cachear resultados de búsqueda de referencias
3. **Incremental Testing**: Solo ejecutar tests afectados por cambios
4. **Batch Updates**: Actualizar múltiples referencias en un archivo de una vez

### Estimaciones de Tiempo

- **Fase 1 (DEPRECATED)**: ~2 minutos
- **Fase 2 (Shared)**: ~3 minutos
- **Fase 3 (RSS Feed)**: ~5 minutos
- **Fase 4 (RSS Article)**: ~10 minutos
- **Fase 5 (Chunking)**: ~2 minutos
- **Total estimado**: ~25-30 minutos

## Security Considerations

- **Backup**: Crear backup antes de iniciar proceso
- **Git Integration**: Usar git para tracking de cambios
- **Validation**: Validar sintaxis antes de escribir archivos
- **Rollback**: Capacidad de revertir cambios en cualquier momento

## Deployment Strategy

### Pre-Deployment

1. Crear branch para eliminación de alias
2. Ejecutar tests baseline
3. Crear backup del código

### Deployment

1. Ejecutar orchestrator
2. Monitorear progreso por fase
3. Verificar reportes de cada fase

### Post-Deployment

1. Ejecutar tests completos
2. Validar imports
3. Revisar reportes
4. Commit cambios
5. Crear PR para review

## Monitoring and Logging

### Logging Levels

- **DEBUG**: Detalles de cada operación
- **INFO**: Progreso de fases
- **WARNING**: Alias no encontrados, referencias ambiguas
- **ERROR**: Fallos de tests, errores de import
- **CRITICAL**: Fallos que requieren rollback

### Métricas

- Alias procesados por fase
- Archivos modificados
- Líneas cambiadas
- Tiempo por fase
- Tests ejecutados
- Tests fallidos

## Future Enhancements

1. **Dry Run Mode**: Simular eliminación sin modificar archivos
2. **Interactive Mode**: Pedir confirmación antes de cada fase
3. **Selective Removal**: Eliminar solo alias específicos
4. **Parallel Phases**: Procesar fases independientes en paralelo
5. **AI-Assisted**: Usar AI para detectar referencias complejas

## References

- **ALIAS_INVENTORY.md**: Inventario completo de alias
- **CLEANUP_COMPLETED.md**: Reporte de limpieza anterior
- **Architecture Guidelines**: `.kiro/steering/architecture.md`
- **Testing Guidelines**: `.kiro/steering/testing-guidelines.md`
