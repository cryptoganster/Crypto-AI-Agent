# Integration Tests - Article Repository

## Overview

Este directorio contiene tests de integración para el `ArticleWriteRepository` que verifican la persistencia y reconstrucción del Article aggregate con todos sus Value Objects.

## Tests Implementados

### 1. TestArticleRepositoryPersistence

Tests de persistencia básica:

- **test_save_new_article_with_value_objects**: Verifica que un Article nuevo con todos los VOs se persiste correctamente
- **test_update_existing_article_with_value_objects**: Verifica que las actualizaciones preservan los VOs
- **test_delete_article**: Verifica la eliminación correcta

### 2. TestArticleRepositoryReconstruction

Tests de reconstrucción desde base de datos:

- **test_reconstruct_article_with_all_value_objects**: Verifica que todos los VOs se reconstruyen correctamente
- **test_reconstruct_article_with_optional_value_objects_none**: Verifica manejo de VOs opcionales None
- **test_reconstruct_preserves_value_object_types**: Verifica que los tipos internos de VOs se preservan

### 3. TestArticleRepositoryEventSourcing

Tests de event sourcing:

- **test_events_are_not_emitted_on_reconstruction**: Verifica que reconstruir no emite eventos
- **test_events_persist_through_save_cycle**: Verifica que eventos se manejan en el ciclo de guardado
- **test_multiple_operations_generate_multiple_events**: Verifica generación de múltiples eventos

### 4. TestArticleRepositoryOptimisticLocking

Tests de optimistic locking:

- **test_version_increments_on_save**: Verifica incremento de version
- **test_version_persists_through_updates**: Verifica persistencia de version en actualizaciones
- **test_version_preserved_on_reconstruction**: Verifica que version se preserva al reconstruir
- **test_concurrent_updates_use_version**: Verifica uso de version para actualizaciones concurrentes

## Requisitos

### Opción 1: SQLite (Desarrollo)

```bash
pip install aiosqlite
```

### Opción 2: PostgreSQL (Producción-like)

1. Crear base de datos de prueba:
```sql
CREATE DATABASE scraping_test;
```

2. Actualizar `TEST_DATABASE_URL` en el archivo de tests:
```python
TEST_DATABASE_URL = "postgresql+asyncpg://user:password@localhost/scraping_test"
```

## Ejecución

### Ejecutar todos los tests de integración:
```bash
pytest tests/integration/infra/persistence/ -v
```

### Ejecutar solo tests de persistencia:
```bash
pytest tests/integration/infra/persistence/test_article_repository_integration.py::TestArticleRepositoryPersistence -v
```

### Ejecutar con marcador integration:
```bash
pytest -m integration
```

## Cobertura

Estos tests cubren:

✅ Persistencia de Article con Value Objects nuevos:
- ReadabilityScore
- WordCount
- ReadingTime
- ContentLanguage
- TagCollection
- KeywordCollection
- ArticleCategory
- ValidationInfo
- ArticleQualityLevel

✅ Reconstrucción correcta desde DB:
- Todos los VOs se reconstruyen con tipos correctos
- VOs opcionales manejan None correctamente
- Properties retornan primitivos correctamente

✅ Event Sourcing:
- Eventos no se emiten en reconstrucción
- Eventos se manejan en ciclo de guardado
- Múltiples operaciones generan múltiples eventos

✅ Optimistic Locking:
- Version se incrementa correctamente
- Version persiste en actualizaciones
- Version se preserva en reconstrucción
- Detección de actualizaciones concurrentes

## Notas

- Los tests usan SQLite en memoria por defecto para velocidad
- Para tests más realistas, usar PostgreSQL
- Los tests están aislados (cada test tiene su propia DB)
- Los fixtures manejan setup/teardown automáticamente
- Los tests son independientes y pueden ejecutarse en cualquier orden

## Relación con Spec

Estos tests implementan el task 39 del plan de refactorización:

```markdown
- [ ] 39. Escribir integration tests con Repository
  - Test: Article persiste correctamente con nuevos VOs
  - Test: Article se reconstruye correctamente desde DB
  - Test: Event sourcing funciona con persistencia
  - Test: Optimistic locking funciona con version
```

Todos los sub-tasks están cubiertos por los tests implementados.
