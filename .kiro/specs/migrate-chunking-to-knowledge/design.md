# Design Document

## Overview

Este documento describe el diseño técnico para migrar el bounded context `chunking` a `knowledge`, incluyendo la estrategia de renombrado, actualización de imports, y deprecación segura del código antiguo.

## Architecture

### Bounded Context Actual vs Nuevo

```
┌─────────────────────────────────────────────────────────┐
│                    ANTES (chunking)                      │
│                                                          │
│  src/chunking/                                          │
│  ├── domain/                                            │
│  │   ├── aggregates/ContentChunk                       │
│  │   ├── value_objects/VectorEmbedding                 │
│  │   └── events/ArticleAIProcessedEvent                │
│  ├── app/                                               │
│  │   ├── commands/ChunkArticleCommand                  │
│  │   └── process_managers/ArticleAIProcessingPipeline  │
│  └── infra/                                             │
│      └── persistence/ChunkRepository                    │
└─────────────────────────────────────────────────────────┘
                          ↓
                    MIGRACIÓN
                          ↓
┌─────────────────────────────────────────────────────────┐
│                   DESPUÉS (knowledge)                    │
│                                                          │
│  src/knowledge/                                         │
│  ├── domain/                                            │
│  │   ├── aggregates/KnowledgeChunk                     │
│  │   ├── value_objects/KnowledgeEmbedding              │
│  │   └── events/KnowledgeExtractedEvent                │
│  ├── app/                                               │
│  │   ├── commands/ExtractKnowledgeCommand              │
│  │   └── process_managers/KnowledgeProcessingPipeline  │
│  └── infra/                                             │
│      └── persistence/KnowledgeRepository                │
└─────────────────────────────────────────────────────────┘
```

## Components and Interfaces

### 1. Migration Script

**Ubicación**: `scripts/migrate_chunking_to_knowledge.py`

**Responsabilidades**:
- Duplicar bounded context
- Renombrar archivos y clases
- Actualizar imports
- Deprecar archivos antiguos
- Generar reportes

**Interface**:
```python
class MigrationOrchestrator:
    """Orquesta el proceso completo de migración."""
    
    def duplicate_bounded_context(
        self,
        source: Path,
        target: Path
    ) -> DuplicationResult:
        """Duplica bounded context completo."""
        pass
    
    def rename_files_and_classes(
        self,
        target: Path,
        mapping: NameMapping
    ) -> RenameResult:
        """Renombra archivos y clases según mapeo."""
        pass
    
    def update_imports(
        self,
        target: Path,
        mapping: NameMapping
    ) -> ImportUpdateResult:
        """Actualiza imports en archivos."""
        pass
    
    def deprecate_old_files(
        self,
        source: Path,
        verification: VerificationResult
    ) -> DeprecationResult:
        """Depreca archivos antiguos con .bak."""
        pass
    
    def generate_report(
        self,
        results: List[MigrationResult]
    ) -> MigrationReport:
        """Genera reporte de migración."""
        pass
```

### 2. File Renamer

**Responsabilidades**:
- Renombrar archivos Python
- Actualizar nombres de clases
- Actualizar docstrings
- Mantener estructura de directorios

**Interface**:
```python
class FileRenamer:
    """Renombra archivos y actualiza contenido."""
    
    def rename_file(
        self,
        file_path: Path,
        old_name: str,
        new_name: str
    ) -> RenameResult:
        """Renombra archivo y actualiza contenido."""
        pass
    
    def update_class_names(
        self,
        file_path: Path,
        class_mapping: Dict[str, str]
    ) -> UpdateResult:
        """Actualiza nombres de clases en archivo."""
        pass
    
    def update_docstrings(
        self,
        file_path: Path,
        term_mapping: Dict[str, str]
    ) -> UpdateResult:
        """Actualiza terminología en docstrings."""
        pass
```

### 3. Import Updater

**Responsabilidades**:
- Detectar imports de `src.chunking`
- Actualizar a `src.knowledge`
- Actualizar referencias a clases renombradas
- Validar sintaxis Python

**Interface**:
```python
class ImportUpdater:
    """Actualiza imports en archivos Python."""
    
    def find_imports(
        self,
        file_path: Path
    ) -> List[ImportStatement]:
        """Encuentra todos los imports en archivo."""
        pass
    
    def update_import(
        self,
        file_path: Path,
        old_import: str,
        new_import: str
    ) -> UpdateResult:
        """Actualiza import específico."""
        pass
    
    def update_class_references(
        self,
        file_path: Path,
        class_mapping: Dict[str, str]
    ) -> UpdateResult:
        """Actualiza referencias a clases."""
        pass
    
    def validate_syntax(
        self,
        file_path: Path
    ) -> ValidationResult:
        """Valida sintaxis Python del archivo."""
        pass
```

### 4. Deprecation Manager

**Responsabilidades**:
- Renombrar archivos a `.bak`
- Agregar comentarios de deprecación
- Verificar que archivos migrados existen
- Mantener estructura de respaldo

**Interface**:
```python
class DeprecationManager:
    """Gestiona deprecación de archivos antiguos."""
    
    def deprecate_file(
        self,
        file_path: Path,
        new_location: Path
    ) -> DeprecationResult:
        """Depreca archivo agregando .bak."""
        pass
    
    def add_deprecation_comment(
        self,
        file_path: Path,
        new_location: str
    ) -> None:
        """Agrega comentario indicando nueva ubicación."""
        pass
    
    def verify_migration(
        self,
        old_path: Path,
        new_path: Path
    ) -> VerificationResult:
        """Verifica que migración fue exitosa."""
        pass
```

### 5. Verification Engine

**Responsabilidades**:
- Ejecutar tests
- Verificar imports
- Verificar handlers registrados
- Generar reporte de verificación

**Interface**:
```python
class VerificationEngine:
    """Verifica que migración fue exitosa."""
    
    def run_tests(
        self,
        test_path: Path
    ) -> TestResult:
        """Ejecuta tests y retorna resultados."""
        pass
    
    def verify_no_old_imports(
        self,
        project_root: Path
    ) -> ImportVerificationResult:
        """Verifica que no hay imports a código antiguo."""
        pass
    
    def verify_handlers_registered(
        self,
        container_path: Path
    ) -> HandlerVerificationResult:
        """Verifica que handlers están registrados."""
        pass
    
    def generate_verification_report(
        self,
        results: List[VerificationResult]
    ) -> VerificationReport:
        """Genera reporte de verificación."""
        pass
```

## Data Models

### NameMapping

```python
@dataclass
class NameMapping:
    """Mapeo de nombres antiguos a nuevos."""
    
    # Aggregates
    aggregates: Dict[str, str] = field(default_factory=lambda: {
        "ContentChunk": "KnowledgeChunk",
    })
    
    # Value Objects
    value_objects: Dict[str, str] = field(default_factory=lambda: {
        "VectorEmbedding": "KnowledgeEmbedding",
        "ChunkSummary": "KnowledgeSummary",
        "ChunkId": "KnowledgeChunkId",
        "ChunkStatus": "KnowledgeStatus",
        "TokenCount": "KnowledgeMetrics",
        "TLDR": "KnowledgeTLDR",
    })
    
    # Events
    events: Dict[str, str] = field(default_factory=lambda: {
        "ArticleAIProcessedEvent": "KnowledgeExtractedEvent",
        "ChunkCreatedEvent": "KnowledgeChunkCreatedEvent",
        "ChunkEmbeddedEvent": "KnowledgeEnrichedEvent",
        "ChunkSummarizedEvent": "KnowledgeSummarizedEvent",
        "ChunkCompletedEvent": "KnowledgeIndexedEvent",
        "ChunkFailedEvent": "KnowledgeProcessingFailedEvent",
    })
    
    # Commands
    commands: Dict[str, str] = field(default_factory=lambda: {
        "ChunkArticleCommand": "ExtractKnowledgeCommand",
        "GenerateChunkEmbeddingsCommand": "EnrichKnowledgeCommand",
        "GenerateChunkSummariesCommand": "SummarizeKnowledgeCommand",
        "GenerateGlobalSummaryCommand": "GenerateKnowledgeSummaryCommand",
        "GenerateTLDRCommand": "GenerateKnowledgeTLDRCommand",
        "PersistChunksCommand": "IndexKnowledgeCommand",
    })
    
    # Process Managers
    process_managers: Dict[str, str] = field(default_factory=lambda: {
        "ArticleAIProcessingPipeline": "KnowledgeProcessingPipeline",
    })
    
    # Services
    services: Dict[str, str] = field(default_factory=lambda: {
        "ChunkingService": "KnowledgeExtractionService",
        "ChunkValidationService": "KnowledgeValidationService",
    })
    
    # Repositories
    repositories: Dict[str, str] = field(default_factory=lambda: {
        "ChunkRepository": "KnowledgeRepository",
        "ProcessingStatusRepository": "KnowledgeProcessingStatusRepository",
    })
    
    # Containers
    containers: Dict[str, str] = field(default_factory=lambda: {
        "ChunkingContainer": "KnowledgeContainer",
    })
    
    # File names
    file_names: Dict[str, str] = field(default_factory=lambda: {
        "content_chunk.py": "knowledge_chunk.py",
        "vector_embedding.py": "knowledge_embedding.py",
        "chunk_summary.py": "knowledge_summary.py",
        "chunk_id.py": "knowledge_chunk_id.py",
        "chunk_status.py": "knowledge_status.py",
        "token_count.py": "knowledge_metrics.py",
        "tldr.py": "knowledge_tldr.py",
        "article_ai_processed.py": "knowledge_extracted.py",
        "created.py": "chunk_created.py",
        "embedded.py": "knowledge_enriched.py",
        "summarized.py": "knowledge_summarized.py",
        "completed.py": "knowledge_indexed.py",
        "failed.py": "processing_failed.py",
        "chunking.py": "knowledge_extraction.py",
        "chunk_validation.py": "knowledge_validation.py",
        "article_ai_processing_pipeline.py": "knowledge_processing_pipeline.py",
    })
    
    def get_all_mappings(self) -> Dict[str, str]:
        """Retorna todos los mapeos combinados."""
        all_mappings = {}
        all_mappings.update(self.aggregates)
        all_mappings.update(self.value_objects)
        all_mappings.update(self.events)
        all_mappings.update(self.commands)
        all_mappings.update(self.process_managers)
        all_mappings.update(self.services)
        all_mappings.update(self.repositories)
        all_mappings.update(self.containers)
        return all_mappings
```

### MigrationResult

```python
@dataclass
class MigrationResult:
    """Resultado de operación de migración."""
    
    success: bool
    operation: str  # "duplicate", "rename", "update_imports", etc.
    files_affected: List[Path]
    errors: List[str]
    warnings: List[str]
    duration_seconds: float
    
    def __str__(self) -> str:
        status = "✅ SUCCESS" if self.success else "❌ FAILED"
        return f"{status} - {self.operation} ({len(self.files_affected)} files)"
```

### MigrationReport

```python
@dataclass
class MigrationReport:
    """Reporte completo de migración."""
    
    started_at: datetime
    completed_at: datetime
    total_files_migrated: int
    total_classes_renamed: int
    total_imports_updated: int
    total_files_deprecated: int
    results: List[MigrationResult]
    verification: VerificationResult
    
    @property
    def duration_seconds(self) -> float:
        return (self.completed_at - self.started_at).total_seconds()
    
    @property
    def success_rate(self) -> float:
        if not self.results:
            return 0.0
        successful = sum(1 for r in self.results if r.success)
        return successful / len(self.results)
    
    def to_markdown(self) -> str:
        """Genera reporte en formato Markdown."""
        pass
```

## Error Handling

### Estrategia de Rollback

Si la migración falla en cualquier punto:

1. **Fase 1-2 (Duplicación y Renombrado)**: 
   - Eliminar `src/knowledge/` completo
   - No hay cambios en `src/chunking/`

2. **Fase 3-4 (Imports y Deprecación)**:
   - Restaurar archivos `.bak` a originales
   - Eliminar `src/knowledge/`

3. **Fase 5-6 (Externa y Tests)**:
   - Revertir cambios en bounded contexts externos
   - Restaurar tests originales

### Validaciones en Cada Paso

```python
class MigrationValidator:
    """Valida cada paso de la migración."""
    
    def validate_duplication(
        self,
        source: Path,
        target: Path
    ) -> ValidationResult:
        """Valida que duplicación fue exitosa."""
        # Verificar que todos los archivos existen
        # Verificar que contenido es idéntico
        pass
    
    def validate_rename(
        self,
        file_path: Path,
        expected_classes: List[str]
    ) -> ValidationResult:
        """Valida que renombrado fue exitoso."""
        # Verificar que clases nuevas existen
        # Verificar sintaxis Python
        pass
    
    def validate_imports(
        self,
        file_path: Path
    ) -> ValidationResult:
        """Valida que imports son correctos."""
        # Verificar que no hay imports rotos
        # Verificar que imports apuntan a src.knowledge
        pass
    
    def validate_deprecation(
        self,
        old_path: Path,
        new_path: Path
    ) -> ValidationResult:
        """Valida que deprecación es segura."""
        # Verificar que archivo nuevo existe
        # Verificar que no hay imports activos al antiguo
        pass
```

## Testing Strategy

### Unit Tests

**Ubicación**: `tests/unit/scripts/test_migration.py`

```python
class TestMigrationOrchestrator:
    """Tests para MigrationOrchestrator."""
    
    def test_duplicate_bounded_context_success(self):
        """Debería duplicar bounded context correctamente."""
        pass
    
    def test_rename_files_and_classes_success(self):
        """Debería renombrar archivos y clases correctamente."""
        pass
    
    def test_update_imports_success(self):
        """Debería actualizar imports correctamente."""
        pass
    
    def test_deprecate_old_files_success(self):
        """Debería deprecar archivos antiguos correctamente."""
        pass
    
    def test_rollback_on_failure(self):
        """Debería hacer rollback si falla algún paso."""
        pass
```

### Integration Tests

**Ubicación**: `tests/integration/test_knowledge_migration.py`

```python
class TestKnowledgeMigration:
    """Tests de integración para migración completa."""
    
    async def test_knowledge_extraction_pipeline_works(self):
        """Debería ejecutar pipeline de extracción de conocimiento."""
        pass
    
    async def test_knowledge_enrichment_works(self):
        """Debería enriquecer conocimiento con embeddings."""
        pass
    
    async def test_knowledge_indexing_works(self):
        """Debería indexar conocimiento en vector store."""
        pass
    
    async def test_knowledge_search_works(self):
        """Debería buscar conocimiento semánticamente."""
        pass
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Duplication Completeness

*For any* file in `src/chunking/`, after duplication, an equivalent file should exist in `src/knowledge/` with identical content.

**Validates: Requirements 1.1, 1.2, 1.3**

### Property 2: Rename Consistency

*For any* class renamed in a file, all references to that class within the same file should be updated to the new name.

**Validates: Requirements 2.2, 2.3, 2.4, 2.5, 2.6, 2.7**

### Property 3: Import Correctness

*For any* file in `src/knowledge/`, all imports should point to `src.knowledge` and not to `src.chunking`.

**Validates: Requirements 3.1, 3.2, 3.4**

### Property 4: Deprecation Safety

*For any* file deprecated with `.bak` extension, there should be no active imports to that file in the codebase.

**Validates: Requirements 4.3, 4.4**

### Property 5: Handler Registration

*For any* command or event handler in `src/knowledge/`, it should be registered in the `KnowledgeContainer`.

**Validates: Requirements 5.2, 5.3, 5.4, 5.5**

### Property 6: Test Coverage Preservation

*For any* test file in `tests/unit/chunking/`, after migration, an equivalent test file should exist in `tests/unit/knowledge/` with updated imports.

**Validates: Requirements 7.1, 7.2, 7.3**

### Property 7: No Broken Imports

*For any* Python file in the project, running `python -m py_compile` should succeed without import errors.

**Validates: Requirements 3.4, 6.4, 8.3**

### Property 8: Migration Idempotence

*For any* migration operation, running it twice should produce the same result as running it once (no duplicate files, no double renaming).

**Validates: All requirements (general correctness)**

## Implementation Plan

### Phase 1: Script Development (1-2 days)

1. Crear `scripts/migrate_chunking_to_knowledge.py`
2. Implementar `MigrationOrchestrator`
3. Implementar `FileRenamer`
4. Implementar `ImportUpdater`
5. Implementar `DeprecationManager`
6. Implementar `VerificationEngine`
7. Crear tests unitarios del script

### Phase 2: Dry Run (0.5 days)

1. Ejecutar script en modo dry-run (sin cambios reales)
2. Revisar reporte de cambios propuestos
3. Ajustar mapeo de nombres si es necesario
4. Validar que no hay conflictos

### Phase 3: Ejecución (0.5 days)

1. Ejecutar script de migración
2. Verificar que duplicación fue exitosa
3. Verificar que renombrado fue exitoso
4. Verificar que imports fueron actualizados
5. Ejecutar tests

### Phase 4: Verificación (0.5 days)

1. Ejecutar suite completa de tests
2. Verificar handlers registrados
3. Verificar que no hay imports rotos
4. Generar reporte de migración

### Phase 5: Documentación (0.5 days)

1. Crear documento de mapeo de nombres
2. Actualizar arquitectura
3. Crear guía de referencia rápida
4. Comunicar cambios al equipo

### Phase 6: Limpieza (después de 2 sprints)

1. Verificar estabilidad
2. Eliminar archivos `.bak`
3. Eliminar directorio `src/chunking/`

## Monitoring and Observability

### Métricas a Trackear

1. **Duración de migración**: Tiempo total de ejecución
2. **Archivos migrados**: Número de archivos procesados
3. **Clases renombradas**: Número de clases actualizadas
4. **Imports actualizados**: Número de imports modificados
5. **Tests pasando**: Porcentaje de tests exitosos
6. **Handlers registrados**: Número de handlers correctamente registrados

### Logs

```python
# Logging durante migración
logger.info("Iniciando migración chunking → knowledge")
logger.info("Fase 1: Duplicando bounded context", files=file_count)
logger.info("Fase 2: Renombrando archivos y clases", renames=rename_count)
logger.info("Fase 3: Actualizando imports", updates=import_count)
logger.info("Fase 4: Deprecando archivos antiguos", deprecated=deprecated_count)
logger.info("Migración completada", duration=duration, success_rate=success_rate)
```

## Security Considerations

1. **Backup**: Mantener archivos `.bak` como respaldo
2. **Validación**: Validar sintaxis Python después de cada cambio
3. **Tests**: Ejecutar tests después de cada fase
4. **Rollback**: Capacidad de revertir cambios si algo falla
5. **Verificación**: Verificar que no hay imports rotos antes de deprecar

## Performance Considerations

1. **Procesamiento paralelo**: Procesar archivos en paralelo cuando sea posible
2. **Cache**: Cachear resultados de parsing de AST
3. **Incremental**: Permitir migración incremental (archivo por archivo)
4. **Progress**: Mostrar progreso durante ejecución

## References

- **DDD**: Domain-Driven Design by Eric Evans
- **Refactoring**: Refactoring by Martin Fowler
- **Python AST**: Python Abstract Syntax Trees documentation
- **Architecture**: `.kiro/steering/architecture.md`
- **Domain Patterns**: `.kiro/steering/domain-patterns.md`
