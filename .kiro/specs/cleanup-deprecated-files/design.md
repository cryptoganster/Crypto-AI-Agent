# Design Document: Limpieza de Archivos Deprecated

## Overview

Este documento describe el diseño del proceso de limpieza de archivos deprecated en `src/domain/` que ya fueron migrados a bounded contexts específicos. El proceso sigue un enfoque conservador de 4 pasos que permite revertir cambios si es necesario.

## Architecture

### Flujo del Proceso

```
┌─────────────────────────────────────────────────────────┐
│                    PASO 1: INVESTIGAR                    │
│                                                          │
│  1. Identificar archivos deprecated                     │
│  2. Buscar dependencias (imports)                       │
│  3. Generar reporte de dependencias                     │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│                PASO 2: RESOLVER DEPENDENCIAS             │
│                                                          │
│  1. Actualizar imports en src/                          │
│  2. Actualizar imports en tests/                        │
│  3. Verificar que no quedan imports deprecated          │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│              PASO 3: MARCAR CON .bak                     │
│                                                          │
│  1. Renombrar archivos deprecated a .bak                │
│  2. Verificar que archivos .bak existen                 │
│  3. Sistema no lee archivos .bak (como si no existieran)│
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│              PASO 4: EJECUTAR PRUEBAS                    │
│                                                          │
│  1. Ejecutar pytest completo                            │
│  2. Si tests pasan → Eliminar .bak                      │
│  3. Si tests fallan → Revertir .bak a .py              │
│  4. Generar reporte final                               │
└─────────────────────────────────────────────────────────┘
```

## Components and Interfaces

### Paso 1: Investigación

**Objetivo**: Identificar archivos deprecated y sus dependencias.

**Componentes**:

1. **File Scanner**: Identifica archivos deprecated
   - Input: Directorio `src/domain/`
   - Output: Lista de archivos deprecated con metadatos

2. **Dependency Analyzer**: Busca imports de archivos deprecated
   - Input: Lista de archivos deprecated
   - Output: Mapa de dependencias (archivo → lista de importadores)

3. **Report Generator**: Genera reporte de investigación
   - Input: Archivos deprecated + dependencias
   - Output: Documento markdown con hallazgos

**Algoritmo**:

```python
def investigate_deprecated_files():
    # 1. Identificar archivos deprecated
    deprecated_files = [
        "src/domain/services/articles/article_content_extraction_service.py",
        "src/domain/services/articles/article_language_detection_service.py",
        "src/domain/services/articles/article_metrics_calculation_service.py",
        "src/domain/services/articles/article_plaintext_extraction_service.py",
        "src/domain/services/articles/sentence_relevance_scorer.py",
        "src/domain/interfaces/services/articles/article_content_extraction_service.py",
        "src/domain/interfaces/services/articles/article_language_detection_service.py",
        "src/domain/interfaces/services/articles/article_metrics_calculation_service.py",
        "src/domain/interfaces/services/articles/article_scraping_service.py",
    ]
    
    # 2. Para cada archivo, buscar dependencias
    dependencies = {}
    for file in deprecated_files:
        # Buscar imports en src/ y tests/
        importers = find_importers(file)
        dependencies[file] = importers
    
    # 3. Generar reporte
    generate_investigation_report(deprecated_files, dependencies)
```

### Paso 2: Resolución de Dependencias

**Objetivo**: Actualizar todos los imports para usar nuevas ubicaciones.

**Componentes**:

1. **Import Updater**: Actualiza imports deprecated
   - Input: Archivo con import deprecated + nueva ubicación
   - Output: Archivo actualizado con nuevo import

2. **Verification Scanner**: Verifica que no quedan imports deprecated
   - Input: Directorios src/ y tests/
   - Output: Lista de imports deprecated restantes (debe estar vacía)

**Mapeo de Migraciones**:

```python
MIGRATION_MAP = {
    # Services
    "src.domain.services.articles.article_content_extraction_service": 
        "src.article.domain.services.content_extraction",
    "src.domain.services.articles.article_language_detection_service": 
        "src.article.domain.services.language_detection",
    "src.domain.services.articles.article_metrics_calculation_service": 
        "src.article.domain.services.metrics_calculation",
    "src.domain.services.articles.article_plaintext_extraction_service": 
        "src.article.domain.services.plaintext_extraction",
    "src.domain.services.articles.sentence_relevance_scorer": 
        "src.article.domain.services.sentence_relevance_scorer",
    
    # Interfaces
    "src.domain.interfaces.services.articles.article_content_extraction_service": 
        "src.article.domain.interfaces.services.content_extraction",
    "src.domain.interfaces.services.articles.article_language_detection_service": 
        "src.article.domain.interfaces.services.language_detection",
    "src.domain.interfaces.services.articles.article_metrics_calculation_service": 
        "src.article.domain.interfaces.services.metrics_calculation",
    "src.domain.interfaces.services.articles.article_scraping_service": 
        "src.article.domain.interfaces.external.scraping_service",
}
```

**Algoritmo**:

```python
def resolve_dependencies(dependencies_map):
    for deprecated_file, importers in dependencies_map.items():
        # Obtener nueva ubicación
        new_location = get_new_location(deprecated_file)
        
        # Actualizar cada archivo que importa
        for importer_file in importers:
            update_imports_in_file(
                file=importer_file,
                old_import=deprecated_file,
                new_import=new_location
            )
    
    # Verificar que no quedan imports deprecated
    remaining = find_deprecated_imports()
    if remaining:
        raise Exception(f"Imports deprecated restantes: {remaining}")
```

### Paso 3: Backup con .bak

**Objetivo**: Renombrar archivos deprecated a .bak para que no sean leídos.

**Componentes**:

1. **File Renamer**: Renombra archivos a .bak
   - Input: Lista de archivos deprecated
   - Output: Archivos renombrados con extensión .bak

2. **Backup Verifier**: Verifica que backups existen
   - Input: Lista de archivos esperados .bak
   - Output: Confirmación de que todos existen

**Algoritmo**:

```python
def backup_deprecated_files(deprecated_files):
    backed_up = []
    
    for file_path in deprecated_files:
        # Renombrar a .bak
        backup_path = file_path + ".bak"
        os.rename(file_path, backup_path)
        
        # Verificar que existe
        if not os.path.exists(backup_path):
            raise Exception(f"Backup failed: {backup_path}")
        
        backed_up.append(backup_path)
        print(f"✓ Backed up: {file_path} → {backup_path}")
    
    return backed_up
```

**Ventajas del .bak**:
- Python no importa archivos .bak (como si no existieran)
- Fácil de revertir (solo renombrar de vuelta)
- Mantiene el archivo en la misma ubicación
- No requiere git stash o commits temporales

### Paso 4: Ejecutar Pruebas y Eliminar

**Objetivo**: Verificar que el sistema funciona sin archivos deprecated y eliminarlos.

**Componentes**:

1. **Test Runner**: Ejecuta suite de tests
   - Input: Ninguno
   - Output: Resultado de tests (pass/fail)

2. **File Cleaner**: Elimina archivos .bak si tests pasan
   - Input: Lista de archivos .bak + resultado de tests
   - Output: Archivos eliminados o revertidos

3. **Report Generator**: Genera reporte final
   - Input: Archivos eliminados + estadísticas
   - Output: Documento markdown con resumen

**Algoritmo**:

```python
def execute_tests_and_cleanup(backup_files):
    # 1. Ejecutar tests
    print("Ejecutando tests...")
    test_result = run_pytest()
    
    if test_result.success:
        # 2. Tests pasaron → Eliminar .bak
        print("✓ Tests pasaron. Eliminando archivos .bak...")
        for backup_file in backup_files:
            os.remove(backup_file)
            print(f"✓ Eliminado: {backup_file}")
        
        # 3. Generar reporte final
        generate_cleanup_report(backup_files, success=True)
        
    else:
        # 2. Tests fallaron → Revertir .bak
        print("✗ Tests fallaron. Revirtiendo backups...")
        for backup_file in backup_files:
            original_file = backup_file.replace(".bak", "")
            os.rename(backup_file, original_file)
            print(f"✓ Revertido: {backup_file} → {original_file}")
        
        # 3. Generar reporte de fallo
        generate_cleanup_report(backup_files, success=False, errors=test_result.errors)
        
        raise Exception("Tests fallaron. Archivos revertidos.")
```

## Data Models

### DeprecatedFile

```python
@dataclass
class DeprecatedFile:
    """Representa un archivo deprecated."""
    
    path: str                    # Ruta del archivo deprecated
    new_location: str            # Nueva ubicación después de migración
    importers: List[str]         # Archivos que lo importan
    backup_path: Optional[str]   # Ruta del backup .bak
    deleted: bool = False        # Si fue eliminado
```

### DependencyMap

```python
@dataclass
class DependencyMap:
    """Mapa de dependencias de archivos deprecated."""
    
    deprecated_file: str         # Archivo deprecated
    importers: List[ImportInfo]  # Lista de importadores
    
@dataclass
class ImportInfo:
    """Información de un import."""
    
    file: str                    # Archivo que importa
    line_number: int             # Línea del import
    import_statement: str        # Statement completo
```

### CleanupReport

```python
@dataclass
class CleanupReport:
    """Reporte final de limpieza."""
    
    total_files: int             # Total de archivos procesados
    files_deleted: int           # Archivos eliminados
    files_reverted: int          # Archivos revertidos
    test_result: str             # "passed" o "failed"
    timestamp: datetime          # Fecha y hora
    files: List[DeprecatedFile]  # Lista de archivos procesados
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Backup Reversibility

*For any* archivo deprecated, después de crear backup con .bak, debe ser posible revertir el archivo a su estado original renombrando de .bak a .py

**Validates: Requirements 4.2, 4.3**

### Property 2: Import Update Completeness

*For any* archivo deprecated, después de resolver dependencias, no debe existir ningún import que apunte a la ubicación deprecated

**Validates: Requirements 3.5**

### Property 3: Test Safety

*For any* conjunto de archivos .bak, si los tests pasan, entonces el sistema funciona correctamente sin los archivos deprecated

**Validates: Requirements 5.5**

### Property 4: Backup Existence

*For any* archivo deprecated que se renombra a .bak, el archivo .bak debe existir en el filesystem

**Validates: Requirements 4.4**

### Property 5: Cleanup Completeness

*For any* proceso de limpieza exitoso, no deben quedar archivos .bak en el sistema

**Validates: Requirements 6.4**

## Error Handling

### Errores en Paso 1 (Investigación)

- **Archivo no encontrado**: Registrar warning y continuar
- **Error de lectura**: Registrar error y continuar con siguiente archivo
- **Sin dependencias**: Continuar normalmente (es válido)

### Errores en Paso 2 (Resolución)

- **Import no encontrado**: Registrar error y abortar (crítico)
- **Archivo no escribible**: Registrar error y abortar (crítico)
- **Imports restantes**: Abortar y mostrar lista de imports pendientes

### Errores en Paso 3 (Backup)

- **Rename falla**: Abortar inmediatamente (crítico)
- **Backup no existe**: Abortar y revertir backups previos
- **Permisos insuficientes**: Abortar y mostrar error

### Errores en Paso 4 (Tests)

- **Tests fallan**: Revertir todos los .bak automáticamente
- **Eliminación falla**: Registrar error pero continuar (archivos .bak quedan)
- **Reporte falla**: Registrar warning pero continuar

## Testing Strategy

### Unit Tests

No se requieren unit tests para este proceso de limpieza, ya que es un script de migración one-time.

### Integration Tests

**Test 1: Backup y Revert**
```python
def test_backup_and_revert():
    # Crear archivo temporal
    test_file = "test_deprecated.py"
    create_test_file(test_file)
    
    # Hacer backup
    backup_file = backup_deprecated_files([test_file])[0]
    
    # Verificar que .bak existe y original no
    assert os.path.exists(backup_file)
    assert not os.path.exists(test_file)
    
    # Revertir
    os.rename(backup_file, test_file)
    
    # Verificar que original existe y .bak no
    assert os.path.exists(test_file)
    assert not os.path.exists(backup_file)
```

**Test 2: Import Update**
```python
def test_import_update():
    # Crear archivo con import deprecated
    test_file = "test_importer.py"
    with open(test_file, "w") as f:
        f.write("from src.domain.services.articles.article_metrics_calculation_service import ArticleMetricsCalculationService\n")
    
    # Actualizar import
    update_imports_in_file(
        file=test_file,
        old_import="src.domain.services.articles.article_metrics_calculation_service",
        new_import="src.article.domain.services.metrics_calculation"
    )
    
    # Verificar que import fue actualizado
    with open(test_file, "r") as f:
        content = f.read()
    
    assert "src.article.domain.services.metrics_calculation" in content
    assert "src.domain.services.articles" not in content
```

### Manual Testing

1. **Dry Run**: Ejecutar pasos 1-2 sin hacer cambios reales
2. **Backup Test**: Ejecutar paso 3 y verificar que archivos .bak existen
3. **Test Run**: Ejecutar paso 4 y verificar que tests pasan
4. **Revert Test**: Simular fallo de tests y verificar que revert funciona

## Implementation Plan

Ver `tasks.md` para el plan detallado de implementación.

## Referencias

- **DOMAIN_SERVICES_MIGRATION_SUMMARY.md**: Documentación de migraciones previas
- **MIGRATION_COMPLETED.md**: Resumen de migraciones completadas
- **Architecture Guidelines**: `.kiro/steering/architecture.md`
- **Domain Service Migration Guide**: `.kiro/steering/domain-service-migration-guide.md`
