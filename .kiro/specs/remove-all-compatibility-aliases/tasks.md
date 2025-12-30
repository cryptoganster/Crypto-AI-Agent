# Implementation Plan: Eliminación Completa de Alias de Compatibilidad

## Overview

Este plan detalla las tareas para implementar la eliminación sistemática de 68 alias de compatibilidad, procesando por fases con validación continua mediante tests.

---

## Phase 0: Preparación y Setup

- [ ] 1. Crear estructura base del proyecto
  - Crear directorio `scripts/alias_removal/`
  - Crear módulos base para componentes
  - Configurar logging
  - _Requirements: 1.1, 9.1_

- [ ] 2. Implementar AliasInfo y modelos de datos
  - Crear dataclass `AliasInfo` con todos los campos
  - Crear dataclass `UsageInfo` para referencias
  - Crear dataclass `TestResult` para resultados de tests
  - Crear dataclass `PhaseReport` para reportes de fase
  - _Requirements: 1.4, 9.2_

- [ ] 3. Implementar AliasScanner
  - Implementar `scan_directory()` para encontrar alias
  - Implementar `categorize_by_context()` para agrupar por bounded context
  - Implementar `categorize_by_priority()` para agrupar por prioridad
  - Implementar `find_alias_usages()` para encontrar referencias
  - _Requirements: 1.1, 1.2, 1.3, 2.1, 2.2_

- [ ] 4. Ejecutar tests baseline
  - Ejecutar `pytest tests/ -v` y capturar resultados
  - Guardar resultados como baseline
  - Verificar que todos los tests pasan
  - Si algún test falla, detener proceso
  - _Requirements: 5.1, 5.2, 5.3, 5.4_

---

## Phase 1: Eliminar Alias DEPRECATED

- [ ] 5. Implementar AliasRemover básico
  - Implementar `update_references()` para actualizar referencias
  - Implementar `remove_alias_definition()` para eliminar definición
  - Implementar `update_all_list()` para actualizar `__all__`
  - Implementar `validate_syntax()` para validar sintaxis
  - _Requirements: 3.1, 3.2, 3.3, 4.1, 4.2, 4.5_

- [ ] 6. Procesar alias: EnhancedDomainEventPublisher
  - Buscar referencias con `grep -r "EnhancedDomainEventPublisher" src/`
  - Actualizar referencias a `EventPublisherWithDispatch`
  - Eliminar definición en `event_publisher_with_dispatch.py:109`
  - Actualizar `__all__` si es necesario
  - _Requirements: 2.1, 3.1, 4.1_

- [ ] 7. Procesar alias: InMemoryDomainEventPublisher
  - Buscar referencias con `grep -r "InMemoryDomainEventPublisher" src/`
  - Actualizar referencias a `InMemoryEventPublisher`
  - Eliminar definición en `in_memory_event_publisher.py:92`
  - Actualizar `__all__` si es necesario
  - _Requirements: 2.1, 3.1, 4.1_

- [ ] 8. Procesar alias: LoggingDomainEventPublisher
  - Buscar referencias con `grep -r "LoggingDomainEventPublisher" src/`
  - Actualizar referencias a `EventPublisher`
  - Eliminar definición en `event_publisher.py:389`
  - Actualizar `__all__` si es necesario
  - _Requirements: 2.1, 3.1, 4.1_

- [ ] 9. Procesar alias: create_domain_event_publisher
  - Buscar referencias con `grep -r "create_domain_event_publisher" src/`
  - Actualizar referencias a `create_event_publisher`
  - Eliminar definición en `event_publisher.py:390`
  - Actualizar `__all__` si es necesario
  - _Requirements: 2.1, 3.1, 4.1_

- [ ] 10. Procesar alias: get_domain_event_publisher
  - Buscar referencias con `grep -r "get_domain_event_publisher" src/`
  - Actualizar referencias a `get_event_publisher`
  - Eliminar definición en `event_publisher.py:391`
  - Actualizar `__all__` si es necesario
  - _Requirements: 2.1, 3.1, 4.1_

- [ ] 11. Procesar alias: set_domain_event_publisher
  - Buscar referencias con `grep -r "set_domain_event_publisher" src/`
  - Actualizar referencias a `set_event_publisher`
  - Eliminar definición en `event_publisher.py:392`
  - Actualizar `__all__` si es necesario
  - _Requirements: 2.1, 3.1, 4.1_

- [ ] 12. Implementar TestRunner
  - Implementar `run_all_tests()` para ejecutar pytest
  - Implementar `compare_results()` para comparar con baseline
  - Implementar `get_failed_test_details()` para detalles de fallos
  - _Requirements: 6.1, 6.2, 6.4_

- [ ] 13. Ejecutar tests post-Fase 1
  - Ejecutar `pytest tests/ -v`
  - Comparar con baseline
  - Si fallan tests, ejecutar rollback
  - Generar reporte de fase
  - _Requirements: 6.1, 6.2, 6.3, 7.3_

---

## Phase 2: Eliminar Alias de Shared Kernel

- [ ] 14. Procesar alias: UnitOfWork
  - Buscar referencias con `grep -r "^UnitOfWork[^a-zA-Z]" src/`
  - Actualizar referencias a `SqlAlchemyUnitOfWork`
  - Eliminar definición en `sqlalchemy_uow.py:154`
  - Actualizar `__all__` si es necesario
  - _Requirements: 2.1, 3.1, 4.1_

- [ ] 15. Analizar alias: IDomainEvent = IDomainEvent
  - Verificar si es auto-referencia errónea
  - Si es error, eliminar línea
  - Si es intencional, documentar razón
  - _Requirements: 8.3_

- [ ] 16. Ejecutar tests post-Fase 2
  - Ejecutar `pytest tests/ -v`
  - Comparar con baseline
  - Si fallan tests, ejecutar rollback
  - Generar reporte de fase
  - _Requirements: 6.1, 6.2, 6.3, 7.3_

---

## Phase 3: Eliminar Alias de RSS Feed

- [ ] 17. Procesar alias: Source → RssFeed
  - Buscar referencias con `grep -r "from.*import.*Source[^a-zA-Z]" src/`
  - Actualizar referencias a `RssFeed`
  - Eliminar definición en `aggregates/__init__.py:6`
  - Actualizar `__all__`
  - _Requirements: 2.1, 3.1, 4.1, 4.5_

- [ ] 18. Procesar alias de repositorios RSS Feed
  - `ISourceReadRepository` → `IRssFeedReadRepository`
  - `ISourceWriteRepository` → `IRssFeedWriteRepository`
  - Actualizar referencias en todos los archivos
  - Eliminar definiciones en `repositories/__init__.py`
  - Actualizar `__all__`
  - _Requirements: 2.1, 3.1, 4.1, 4.5_

- [ ] 19. Procesar alias de eventos RSS Feed
  - `SourceCreated` → `RssFeedCreated`
  - Actualizar referencias
  - Eliminar definición en `events/created.py:98`
  - _Requirements: 2.1, 3.1, 4.1_

- [ ] 20. Procesar alias de value objects RSS Feed (parte 1)
  - `SourceStatus` → `RssFeedStatus`
  - `SourceName` → `RssFeedName`
  - `SourceHealth` → `RssFeedHealth`
  - `SourceMetadata` → `RssFeedMetadata`
  - Actualizar referencias y eliminar definiciones
  - _Requirements: 2.1, 3.1, 4.1_

- [ ] 21. Procesar alias de value objects RSS Feed (parte 2)
  - `SourceId` → `RssFeedId`
  - `SourceIdentity` → `RssFeedIdentity`
  - `RssUrl` → `RssFeedUrl`
  - `SourceUrl` → `RssFeedUrl`
  - Actualizar referencias y eliminar definiciones
  - _Requirements: 2.1, 3.1, 4.1_

- [ ] 22. Procesar alias de métricas RSS Feed
  - `SourceMetrics` → `RssFeedMetrics`
  - `RssSourceMetrics` → `RssFeedMetrics`
  - Actualizar referencias y eliminar definiciones
  - _Requirements: 2.1, 3.1, 4.1_

- [ ] 23. Ejecutar tests post-Fase 3
  - Ejecutar `pytest tests/ -v`
  - Comparar con baseline
  - Si fallan tests, ejecutar rollback
  - Generar reporte de fase
  - _Requirements: 6.1, 6.2, 6.3, 7.3_

---

## Phase 4: Eliminar Alias de RSS Article

- [ ] 24. Procesar alias: Article → RssArticle
  - Buscar referencias con `grep -r "from.*import.*Article[^a-zA-Z]" src/`
  - Actualizar referencias a `RssArticle`
  - Eliminar definiciones en múltiples archivos
  - Actualizar `__all__` en todos los archivos
  - _Requirements: 2.1, 3.1, 4.1, 4.5, 8.5_

- [ ] 25. Procesar alias de factories RSS Article
  - `IArticleFactory` → `IRssArticleFactory`
  - `ArticleFactory` → `RssArticleFactory`
  - Actualizar referencias y eliminar definiciones
  - Actualizar `__all__`
  - _Requirements: 2.1, 3.1, 4.1, 4.5_

- [ ] 26. Procesar alias de repositorios RSS Article
  - `IArticleReadRepository` → `IRssArticleReadRepository`
  - `IArticleWriteRepository` → `IRssArticleWriteRepository`
  - Actualizar referencias y eliminar definiciones
  - Actualizar `__all__`
  - _Requirements: 2.1, 3.1, 4.1, 4.5_

- [ ] 27. Procesar alias de metadata RSS Article (parte 1)
  - `ArticleId` → `RssArticleId`
  - `ArticleUrl` → `RssArticleUrl`
  - `ArticleAuthor` → `RssArticleAuthor`
  - `ArticleContent` → `RssArticleContent`
  - `ArticleDescription` → `RssArticleDescription`
  - Actualizar referencias y eliminar definiciones
  - _Requirements: 2.1, 3.1, 4.1, 8.5_

- [ ] 28. Procesar alias de metadata RSS Article (parte 2)
  - `ArticleGuid` → `RssArticleGuid`
  - `ArticlePubDate` → `RssArticlePubDate`
  - `ArticleSummary` → `RssArticleSummary`
  - `ArticleTimestamps` → `RssArticleTimestamps`
  - Actualizar referencias y eliminar definiciones
  - _Requirements: 2.1, 3.1, 4.1, 8.5_

- [ ] 29. Procesar alias de analysis RSS Article
  - `ArticleDeduplicationResult` → `RssArticleDeduplicationResult`
  - `ArticleQuality` → `RssArticleQuality`
  - `ArticleDuplicate` → `RssArticleDuplicate`
  - `ArticleError` → `RssArticleError`
  - `ArticleMetrics` → `RssArticleMetrics`
  - Actualizar referencias y eliminar definiciones
  - _Requirements: 2.1, 3.1, 4.1_

- [ ] 30. Procesar alias de containers y pipelines RSS Article
  - `ArticleContainer` → `RssArticleContainer`
  - `ArticleContentExtractionPipeline` → `RssArticleContentExtractionPipeline`
  - `ArticleContentAnalysisPipeline` → `RssArticleContentAnalysisPipeline`
  - Actualizar referencias y eliminar definiciones
  - _Requirements: 2.1, 3.1, 4.1_

- [ ] 31. Procesar alias de queries y mappers RSS Article
  - `ArticleDTO` → `ArticleReadModel`
  - `ArticleMapper` → `RssArticleMapper`
  - `ArticleReadModelMapper` → `RssArticleReadModelMapper`
  - Actualizar referencias y eliminar definiciones
  - _Requirements: 2.1, 3.1, 4.1_

- [ ] 32. Ejecutar tests post-Fase 4
  - Ejecutar `pytest tests/ -v`
  - Comparar con baseline
  - Si fallan tests, ejecutar rollback
  - Generar reporte de fase
  - _Requirements: 6.1, 6.2, 6.3, 7.3_

---

## Phase 5: Eliminar Alias de Chunking

- [ ] 33. Procesar alias: ContentChunk → KnowledgeChunk
  - Buscar referencias con `grep -r "ContentChunk" src/`
  - Actualizar referencias a `KnowledgeChunk`
  - Eliminar definiciones en `chunking/domain/services/chunking.py:14`
  - Eliminar definición en `chunking/domain/aggregates/__init__.py:6`
  - Actualizar `__all__`
  - _Requirements: 2.1, 3.1, 4.1, 4.5, 8.5_

- [ ] 34. Ejecutar tests post-Fase 5
  - Ejecutar `pytest tests/ -v`
  - Comparar con baseline
  - Si fallan tests, ejecutar rollback
  - Generar reporte de fase
  - _Requirements: 6.1, 6.2, 6.3, 7.3_

---

## Phase 6: Validación y Finalización

- [ ] 35. Implementar ImportValidator
  - Implementar `validate_module()` para validar imports
  - Implementar `validate_all_modified_modules()` para validar todos
  - _Requirements: 11.1, 11.2_

- [ ] 36. Validar imports de todos los módulos modificados
  - Obtener lista de archivos modificados
  - Intentar importar cada módulo
  - Reportar errores de importación
  - _Requirements: 11.2, 11.3, 11.4_

- [ ] 37. Ejecutar tests completos finales
  - Ejecutar `pytest tests/ -v --cov=src`
  - Verificar cobertura
  - Comparar con baseline original
  - Generar reporte de tests final
  - _Requirements: 6.1, 6.2, 6.3_

- [ ] 38. Implementar ReportGenerator
  - Implementar `generate_phase_report()` para reportes de fase
  - Implementar `generate_final_report()` para reporte final
  - Implementar `generate_statistics()` para estadísticas
  - _Requirements: 9.1, 9.2, 9.3, 9.4_

- [ ] 39. Generar reporte final completo
  - Agregar estadísticas de todas las fases
  - Listar todos los archivos modificados
  - Incluir resultados de tests
  - Incluir validación de imports
  - Guardar en `ALIAS_REMOVAL_COMPLETE.md`
  - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5_

- [ ] 40. Actualizar documentación
  - Buscar referencias a alias en archivos `.md`
  - Actualizar referencias con nombres canónicos
  - Actualizar `ALIAS_INVENTORY.md` marcando como eliminados
  - Actualizar `CLEANUP_COMPLETED.md` con nuevos resultados
  - _Requirements: 12.1, 12.2, 12.3, 12.4_

---

## Phase 7: Implementación del Orchestrator

- [ ] 41. Implementar AliasRemovalOrchestrator
  - Implementar `__init__()` con inyección de dependencias
  - Implementar `execute()` para proceso completo
  - Implementar `process_phase()` para procesar una fase
  - Implementar `rollback_phase()` para revertir cambios
  - _Requirements: 7.1, 7.2, 7.3, 10.1, 10.2_

- [ ] 42. Implementar manejo de errores y rollback
  - Capturar excepciones por tipo
  - Implementar rollback automático en fallos
  - Guardar estado antes de cada fase
  - Restaurar estado en rollback
  - _Requirements: 10.1, 10.2, 10.3, 10.4_

- [ ] 43. Crear script ejecutable principal
  - Crear `scripts/alias_removal/run.py`
  - Configurar logging
  - Instanciar orchestrator con dependencias
  - Ejecutar proceso completo
  - Manejar argumentos de línea de comandos
  - _Requirements: 7.1_

---

## Phase 8: Testing del Sistema

- [ ] 44. Crear tests unitarios para AliasScanner
  - Test: `test_scan_directory_finds_all_aliases()`
  - Test: `test_categorize_by_context_groups_correctly()`
  - Test: `test_find_alias_usages_finds_all_references()`
  - _Requirements: Testing Strategy_

- [ ] 45. Crear tests unitarios para AliasRemover
  - Test: `test_update_references_replaces_all_occurrences()`
  - Test: `test_remove_alias_definition_removes_line()`
  - Test: `test_update_all_list_removes_alias()`
  - _Requirements: Testing Strategy_

- [ ] 46. Crear tests unitarios para TestRunner
  - Test: `test_run_all_tests_executes_suite()`
  - Test: `test_compare_results_detects_differences()`
  - _Requirements: Testing Strategy_

- [ ] 47. Crear tests de integración
  - Test: `test_complete_phase_processing()`
  - Test: `test_rollback_restores_files()`
  - Test: `test_import_validation_after_removal()`
  - _Requirements: Testing Strategy_

- [ ] 48. Crear tests end-to-end
  - Test: `test_complete_alias_removal_process()`
  - Usar subset pequeño de alias para test
  - Verificar proceso completo funciona
  - _Requirements: Testing Strategy_

---

## Checkpoint Final

- [ ] 49. Verificación completa del sistema
  - Todos los tests pasan (baseline y post-eliminación)
  - Todos los imports son válidos
  - No quedan alias de compatibilidad (excepto los marcados como "mantener")
  - Documentación actualizada
  - Reportes generados

---

## Notas de Implementación

### Orden de Ejecución

Las tareas deben ejecutarse en el orden especificado. Cada fase depende de la anterior.

### Criterios de Éxito por Fase

- ✅ Todos los alias de la fase eliminados
- ✅ Tests pasan igual que baseline
- ✅ Imports válidos
- ✅ Reporte de fase generado

### Rollback

Si cualquier fase falla:
1. Ejecutar rollback automático
2. Restaurar archivos modificados
3. Verificar que tests vuelven a pasar
4. Generar reporte de fallo
5. Detener proceso

### Alias a Mantener

NO eliminar estos alias (marcados como "mantener"):
- `Event = IDomainEvent` (type alias útil)
- `@property def score()` (property alias de API)

### Estimación de Tiempo

- **Phase 0**: 10 minutos
- **Phase 1**: 5 minutos
- **Phase 2**: 3 minutos
- **Phase 3**: 5 minutos
- **Phase 4**: 10 minutos
- **Phase 5**: 2 minutos
- **Phase 6**: 5 minutos
- **Phase 7**: 5 minutos
- **Phase 8**: 10 minutos
- **Total**: ~55 minutos (desarrollo + ejecución)

### Comandos Útiles

```bash
# Buscar referencias a un alias
grep -r "AliasName" src/

# Ejecutar tests
pytest tests/ -v

# Validar imports
python -c "import src.module"

# Ver archivos modificados
git status

# Crear backup
git stash
```
