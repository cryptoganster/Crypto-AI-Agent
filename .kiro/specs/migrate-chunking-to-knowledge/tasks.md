# Implementation Plan

- [ ] 1. Crear script de migración base
  - Crear archivo `scripts/migrate_chunking_to_knowledge.py`
  - Implementar estructura básica del script
  - Agregar logging y manejo de errores
  - _Requirements: 1.1, 1.2_

- [ ] 2. Implementar MigrationOrchestrator
  - Crear clase `MigrationOrchestrator`
  - Implementar método `duplicate_bounded_context()`
  - Implementar método `rename_files_and_classes()`
  - Implementar método `update_imports()`
  - Implementar método `deprecate_old_files()`
  - Implementar método `generate_report()`
  - _Requirements: 1.1, 2.1, 3.1, 4.1, 9.1_

- [ ] 3. Implementar FileRenamer
  - Crear clase `FileRenamer`
  - Implementar método `rename_file()`
  - Implementar método `update_class_names()` usando AST
  - Implementar método `update_docstrings()`
  - _Requirements: 2.1, 2.2, 2.3_

- [ ] 4. Implementar ImportUpdater
  - Crear clase `ImportUpdater`
  - Implementar método `find_imports()` usando AST
  - Implementar método `update_import()`
  - Implementar método `update_class_references()`
  - Implementar método `validate_syntax()`
  - _Requirements: 3.1, 3.2, 3.4, 3.5_

- [ ] 5. Implementar DeprecationManager
  - Crear clase `DeprecationManager`
  - Implementar método `deprecate_file()`
  - Implementar método `add_deprecation_comment()`
  - Implementar método `verify_migration()`
  - _Requirements: 4.1, 4.2, 4.3, 4.5_

- [ ] 6. Implementar VerificationEngine
  - Crear clase `VerificationEngine`
  - Implementar método `run_tests()`
  - Implementar método `verify_no_old_imports()`
  - Implementar método `verify_handlers_registered()`
  - Implementar método `generate_verification_report()`
  - _Requirements: 8.1, 8.2, 8.3, 8.4_

- [ ] 7. Crear NameMapping completo
  - Definir mapeo de aggregates
  - Definir mapeo de value objects
  - Definir mapeo de events
  - Definir mapeo de commands
  - Definir mapeo de process managers
  - Definir mapeo de services
  - Definir mapeo de repositories
  - Definir mapeo de containers
  - Definir mapeo de file names
  - _Requirements: 2.3, 2.4, 2.5, 2.6, 2.7_

- [ ]* 8. Crear tests unitarios del script
  - Crear `tests/unit/scripts/test_migration_orchestrator.py`
  - Test para `duplicate_bounded_context()`
  - Test para `rename_files_and_classes()`
  - Test para `update_imports()`
  - Test para `deprecate_old_files()`
  - Test para rollback en caso de fallo
  - _Requirements: All_

- [ ] 9. Ejecutar dry-run de migración
  - Ejecutar script en modo dry-run
  - Revisar reporte de cambios propuestos
  - Validar mapeo de nombres
  - Ajustar mapeo si es necesario
  - _Requirements: 1.5, 2.1, 3.6_

- [ ] 10. CHECKPOINT - Validar preparación
  - Verificar que script funciona en dry-run
  - Verificar que mapeo de nombres es correcto
  - Verificar que no hay conflictos
  - Obtener aprobación para proceder

- [ ] 11. Fase 1: Duplicar bounded context
  - Ejecutar `duplicate_bounded_context()`
  - Copiar `src/chunking/` → `src/knowledge/`
  - Verificar que todos los archivos fueron copiados
  - Verificar que estructura de directorios es idéntica
  - Generar reporte de duplicación
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_

- [ ] 12. Fase 2: Renombrar value objects
  - Renombrar `vector_embedding.py` → `knowledge_embedding.py`
  - Actualizar clase `VectorEmbedding` → `KnowledgeEmbedding`
  - Renombrar `chunk_summary.py` → `knowledge_summary.py`
  - Actualizar clase `ChunkSummary` → `KnowledgeSummary`
  - Renombrar `chunk_id.py` → `knowledge_chunk_id.py`
  - Actualizar clase `ChunkId` → `KnowledgeChunkId`
  - Renombrar `chunk_status.py` → `knowledge_status.py`
  - Actualizar clase `ChunkStatus` → `KnowledgeStatus`
  - Renombrar `token_count.py` → `knowledge_metrics.py`
  - Actualizar clase `TokenCount` → `KnowledgeMetrics`
  - Renombrar `tldr.py` → `knowledge_tldr.py`
  - Actualizar clase `TLDR` → `KnowledgeTLDR`
  - Actualizar `__init__.py` en `value_objects/`
  - _Requirements: 2.1, 2.2, 2.4_

- [ ] 13. Fase 2: Renombrar events
  - Renombrar `article_ai_processed.py` → `knowledge_extracted.py`
  - Actualizar clase `ArticleAIProcessedEvent` → `KnowledgeExtractedEvent`
  - Renombrar `created.py` → `chunk_created.py`
  - Actualizar clase `ChunkCreatedEvent` → `KnowledgeChunkCreatedEvent`
  - Renombrar `embedded.py` → `knowledge_enriched.py`
  - Actualizar clase `ChunkEmbeddedEvent` → `KnowledgeEnrichedEvent`
  - Renombrar `summarized.py` → `knowledge_summarized.py`
  - Actualizar clase `ChunkSummarizedEvent` → `KnowledgeSummarizedEvent`
  - Renombrar `completed.py` → `knowledge_indexed.py`
  - Actualizar clase `ChunkCompletedEvent` → `KnowledgeIndexedEvent`
  - Renombrar `failed.py` → `processing_failed.py`
  - Actualizar clase `ChunkFailedEvent` → `KnowledgeProcessingFailedEvent`
  - Actualizar `__init__.py` en `events/`
  - _Requirements: 2.1, 2.2, 2.5_

- [ ] 14. Fase 2: Renombrar aggregate
  - Renombrar `content_chunk.py` → `knowledge_chunk.py`
  - Actualizar clase `ContentChunk` → `KnowledgeChunk`
  - Actualizar imports de value objects renombrados
  - Actualizar imports de events renombrados
  - Actualizar docstrings con nueva terminología
  - Actualizar `__init__.py` en `aggregates/`
  - _Requirements: 2.1, 2.2, 2.3_

- [ ] 15. Fase 2: Renombrar services
  - Renombrar `chunking.py` → `knowledge_extraction.py`
  - Actualizar clase `ChunkingService` → `KnowledgeExtractionService`
  - Renombrar `chunk_validation.py` → `knowledge_validation.py`
  - Actualizar clase `ChunkValidationService` → `KnowledgeValidationService`
  - Actualizar imports de aggregates renombrados
  - Actualizar `__init__.py` en `services/`
  - _Requirements: 2.1, 2.2_

- [ ] 16. Fase 2: Renombrar commands
  - Renombrar directorio `chunk_article/` → `extract_knowledge/`
  - Actualizar `ChunkArticleCommand` → `ExtractKnowledgeCommand`
  - Renombrar directorio `generate_chunk_embeddings/` → `enrich_knowledge/`
  - Actualizar `GenerateChunkEmbeddingsCommand` → `EnrichKnowledgeCommand`
  - Renombrar directorio `generate_chunk_summaries/` → `summarize_knowledge/`
  - Actualizar `GenerateChunkSummariesCommand` → `SummarizeKnowledgeCommand`
  - Renombrar directorio `generate_global_summary/` → `generate_knowledge_summary/`
  - Actualizar `GenerateGlobalSummaryCommand` → `GenerateKnowledgeSummaryCommand`
  - Renombrar directorio `generate_tldr/` → `generate_knowledge_tldr/`
  - Actualizar `GenerateTLDRCommand` → `GenerateKnowledgeTLDRCommand`
  - Renombrar directorio `persist_chunks/` → `index_knowledge/`
  - Actualizar `PersistChunksCommand` → `IndexKnowledgeCommand`
  - Actualizar imports en todos los handlers
  - _Requirements: 2.1, 2.2, 2.6_

- [ ] 17. Fase 2: Renombrar process manager
  - Renombrar `article_ai_processing_pipeline.py` → `knowledge_processing_pipeline.py`
  - Actualizar clase `ArticleAIProcessingPipeline` → `KnowledgeProcessingPipeline`
  - Actualizar imports de commands renombrados
  - Actualizar imports de events renombrados
  - Actualizar docstrings con nueva terminología
  - _Requirements: 2.1, 2.2, 2.7_

- [ ] 18. Fase 2: Renombrar queries
  - Renombrar directorio `get_article_chunks/` → `get_knowledge_chunks/`
  - Renombrar directorio `get_article_processing_status/` → `get_knowledge_processing_status/`
  - Renombrar directorio `get_processing_metrics/` → `get_knowledge_metrics/`
  - Actualizar clases de queries
  - Actualizar imports
  - _Requirements: 2.1, 2.2_

- [ ] 19. Fase 2: Renombrar repositories
  - Actualizar interfaces de repositorios
  - Actualizar implementaciones de repositorios
  - Actualizar mappers
  - Actualizar modelos ORM si es necesario
  - _Requirements: 2.1, 2.2_

- [ ] 20. Fase 3: Actualizar imports internos en src/knowledge/
  - Actualizar todos los `__init__.py`
  - Actualizar imports en domain layer
  - Actualizar imports en application layer
  - Actualizar imports en infrastructure layer
  - Validar sintaxis Python en todos los archivos
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

- [ ] 21. Fase 3: Actualizar container
  - Renombrar `ChunkingContainer` → `KnowledgeContainer`
  - Actualizar factory methods
  - Actualizar registro de command handlers
  - Actualizar registro de event handlers
  - Actualizar imports
  - _Requirements: 5.1, 5.2, 5.3, 5.4_

- [ ] 22. CHECKPOINT - Validar src/knowledge/ funciona
  - Ejecutar validación de sintaxis
  - Verificar que no hay imports rotos internos
  - Verificar que estructura es correcta

- [ ] 23. Fase 4: Deprecar archivos en src/chunking/
  - Agregar extensión `.bak` a todos los archivos Python
  - Agregar comentarios de deprecación
  - Verificar que archivos migrados existen
  - Generar reporte de deprecación
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

- [ ] 24. Fase 5: Actualizar container principal
  - Actualizar `src/bootstrap/containers/main.py`
  - Cambiar import de `ChunkingContainer` a `KnowledgeContainer`
  - Actualizar registro del container
  - Verificar que container se inicializa correctamente
  - _Requirements: 5.1, 5.5_

- [ ] 25. Fase 6: Actualizar bounded context article
  - Buscar imports de `src.chunking` en `src/article/`
  - Actualizar a `src.knowledge`
  - Actualizar referencias a clases renombradas
  - Validar sintaxis Python
  - _Requirements: 6.1, 6.2, 6.3, 6.4_

- [ ] 26. Fase 6: Actualizar bounded context source
  - Buscar imports de `src.chunking` en `src/source/`
  - Actualizar a `src.knowledge`
  - Actualizar referencias a clases renombradas
  - Validar sintaxis Python
  - _Requirements: 6.1, 6.2, 6.3, 6.4_

- [ ] 27. Fase 6: Actualizar bounded context fetching
  - Buscar imports de `src.chunking` en `src/fetching/`
  - Actualizar a `src.knowledge`
  - Actualizar referencias a clases renombradas
  - Validar sintaxis Python
  - _Requirements: 6.1, 6.2, 6.3, 6.4_

- [ ] 28. Fase 6: Actualizar shared kernel
  - Buscar imports de `src.chunking` en `src/shared/`
  - Actualizar a `src.knowledge`
  - Actualizar referencias a clases renombradas
  - Validar sintaxis Python
  - _Requirements: 6.1, 6.2, 6.3, 6.4_

- [ ] 29. Fase 6: Actualizar API endpoints
  - Buscar imports de `src.chunking` en `src/presentation/`
  - Actualizar a `src.knowledge`
  - Actualizar referencias a clases renombradas
  - Actualizar schemas si es necesario
  - Validar sintaxis Python
  - _Requirements: 6.1, 6.2, 6.3, 6.4_

- [ ] 30. CHECKPOINT - Validar imports externos
  - Verificar que no hay imports a `src.chunking` en código activo
  - Ejecutar búsqueda global de imports antiguos
  - Validar sintaxis Python en todo el proyecto

- [ ] 31. Fase 7: Duplicar y actualizar tests unitarios
  - Copiar `tests/unit/chunking/` → `tests/unit/knowledge/`
  - Actualizar imports en tests
  - Actualizar referencias a clases renombradas
  - Actualizar nombres de tests si es necesario
  - _Requirements: 7.1, 7.2, 7.3_

- [ ] 32. Fase 7: Ejecutar tests unitarios
  - Ejecutar `pytest tests/unit/knowledge/ -v`
  - Verificar que todos los tests pasan
  - Corregir tests fallidos si es necesario
  - _Requirements: 7.4_

- [ ] 33. Fase 7: Duplicar y actualizar tests de integración
  - Copiar tests de integración relacionados
  - Actualizar imports en tests
  - Actualizar referencias a clases renombradas
  - _Requirements: 7.1, 7.2, 7.3_

- [ ] 34. Fase 7: Ejecutar tests de integración
  - Ejecutar `pytest tests/integration/ -v -k knowledge`
  - Verificar que todos los tests pasan
  - Corregir tests fallidos si es necesario
  - _Requirements: 7.4, 6.5_

- [ ] 35. Fase 7: Deprecar tests antiguos
  - Agregar extensión `.bak` a tests en `tests/unit/chunking/`
  - Agregar comentarios de deprecación
  - _Requirements: 7.5_

- [ ] 36. Fase 8: Ejecutar suite completa de tests
  - Ejecutar `pytest tests/ -v`
  - Verificar que todos los tests pasan
  - Generar reporte de cobertura
  - _Requirements: 8.1, 8.2_

- [ ] 37. Fase 8: Verificar handlers registrados
  - Ejecutar aplicación en modo startup
  - Verificar logs de registro de handlers
  - Verificar que todos los handlers de knowledge están registrados
  - Verificar que no hay errores de registro
  - _Requirements: 8.4_

- [ ] 38. Fase 8: Verificar no hay imports antiguos
  - Ejecutar búsqueda global: `grep -r "from src.chunking" src/`
  - Ejecutar búsqueda global: `grep -r "import src.chunking" src/`
  - Verificar que no hay resultados (excepto archivos `.bak`)
  - _Requirements: 8.3_

- [ ] 39. Fase 8: Generar reporte de migración
  - Generar reporte con estadísticas
  - Incluir número de archivos migrados
  - Incluir número de clases renombradas
  - Incluir número de imports actualizados
  - Incluir resultados de tests
  - Incluir verificación de handlers
  - _Requirements: 8.5_

- [ ] 40. CHECKPOINT - Validar migración completa
  - Revisar reporte de migración
  - Verificar que todos los tests pasan
  - Verificar que handlers están registrados
  - Verificar que no hay imports rotos
  - Obtener aprobación para documentar

- [ ] 41. Fase 9: Crear documento de mapeo
  - Crear `docs/KNOWLEDGE_MIGRATION_MAPPING.md`
  - Documentar mapeo de aggregates
  - Documentar mapeo de value objects
  - Documentar mapeo de events
  - Documentar mapeo de commands
  - Documentar mapeo de services
  - Documentar ejemplos de uso
  - _Requirements: 9.1_

- [ ] 42. Fase 9: Actualizar documentación de arquitectura
  - Actualizar `.kiro/steering/architecture.md`
  - Actualizar diagramas de bounded contexts
  - Documentar nuevo lenguaje ubicuo
  - Actualizar ejemplos de código
  - _Requirements: 9.2_

- [ ] 43. Fase 9: Crear guía de referencia rápida
  - Crear `docs/KNOWLEDGE_QUICK_REFERENCE.md`
  - Tabla de cambios de nombres
  - Ejemplos de imports nuevos
  - Comandos comunes
  - Queries comunes
  - _Requirements: 9.3_

- [ ] 44. Fase 9: Documentar lenguaje ubicuo
  - Documentar términos del dominio knowledge
  - Documentar eventos de dominio
  - Documentar comandos
  - Documentar queries
  - Documentar agregados
  - _Requirements: 9.4_

- [ ] 45. Fase 9: Crear checklist de verificación
  - Crear `docs/KNOWLEDGE_MIGRATION_CHECKLIST.md`
  - Checklist de verificación post-migración
  - Checklist de limpieza
  - Checklist de comunicación
  - _Requirements: 9.5_

- [ ] 46. Comunicar cambios al equipo
  - Enviar email con resumen de cambios
  - Compartir documentación
  - Programar sesión de Q&A si es necesario
  - Actualizar README del proyecto

- [ ] 47. FINAL CHECKPOINT - Migración completa
  - Todos los tests pasan
  - Handlers registrados correctamente
  - Documentación completa
  - Equipo informado
  - Sistema funcionando correctamente

## Fase 10: Limpieza (Después de 2 sprints)

- [ ] 48. Verificar estabilidad del sistema
  - Verificar que no hay issues relacionados con migración
  - Verificar que tests siguen pasando
  - Verificar que no hay regresiones
  - _Requirements: 10.1, 10.2_

- [ ] 49. Eliminar archivos .bak
  - Verificar que no hay referencias a archivos `.bak`
  - Eliminar todos los archivos `.bak` en `src/chunking/`
  - Eliminar todos los archivos `.bak` en `tests/unit/chunking/`
  - _Requirements: 10.3, 10.4_

- [ ] 50. Eliminar directorio src/chunking/
  - Verificar que directorio está vacío o solo tiene `.bak`
  - Eliminar directorio completo `src/chunking/`
  - Eliminar directorio completo `tests/unit/chunking/`
  - _Requirements: 10.4_

- [ ] 51. Actualizar .gitignore si es necesario
  - Verificar si hay entradas relacionadas con chunking
  - Actualizar a knowledge si es necesario
  - _Requirements: 10.5_

- [ ] 52. Commit final de limpieza
  - Crear commit con eliminación de archivos antiguos
  - Mensaje: "chore: remove deprecated chunking bounded context"
  - Push a repositorio
