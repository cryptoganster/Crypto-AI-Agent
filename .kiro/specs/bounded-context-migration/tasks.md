# Implementation Plan

- [x] 1. Setup: Crear herramientas y utilidades de migración
  - ✅ Crear decorador @deprecated en src/shared/utils/deprecated.py
  - ⚠️ Crear script de análisis de dependencias en scripts/analyze_dependencies.py (PENDIENTE)
  - ⚠️ Crear script de detección de deprecation warnings en scripts/check_deprecations.py (PENDIENTE)
  - ⚠️ Crear sistema de tracking de migración (migration_state.json) (PENDIENTE)
  - ⚠️ Crear sistema de backup y checkpoints (PENDIENTE)
  - _Requirements: 13.1, 13.2, 14.1_

- [x] 2. Phase 1: Shared Kernel - Core Abstractions
  - ✅ Crear estructura src/shared/kernel/
  - ✅ Migrar IAggregateRoot desde src/domain/shared/interfaces/core/aggregate_root.py
  - ✅ Migrar IEntity desde src/domain/shared/interfaces/core/entity.py
  - ✅ Migrar IValueObject desde src/domain/shared/interfaces/core/value_object.py
  - ✅ Migrar IDomainEvent desde src/domain/shared/interfaces/core/domain_event.py
  - ⚠️ Deprecar archivos originales con @deprecated (VERIFICAR)
  - _Requirements: 6.1, 1.2_

- [x] 3. Phase 1: Shared Kernel - Command/Query Interfaces
  - ✅ Crear src/shared/kernel/commands.py con ICommand e ICommandHandler
  - ✅ Crear src/shared/kernel/queries.py con IQuery e IQueryHandler
  - ✅ Crear src/shared/kernel/bus.py con IMediator e IEventBus
  - ✅ Crear src/shared/kernel/errors.py con excepciones base
  - ✅ Crear src/shared/kernel/uow.py con IUnitOfWork
  - _Requirements: 6.2, 1.2_

- [x] 4. Phase 1: Shared Infrastructure
  - ✅ Migrar logger a src/shared/infra/logger/ (ya existe)
  - ✅ Migrar event bus a src/shared/infra/event_bus/ (ya existe)
  - ✅ Agregar decoradores @deprecated a archivos originales en src/infra/logging/
  - ✅ Agregar decoradores @deprecated a archivos originales en src/infra/events/
  - ✅ Migrar IAPScheduler a src/shared/kernel/scheduler.py
  - ✅ Migrar APSchedulerAdapter a src/shared/infra/scheduling/apscheduler.py (renombrar sin "adapter")
  - ✅ Deprecar archivos originales de scheduler
  - ⚠️ Migrar DI base a src/shared/infra/di/ (VERIFICAR)
  - _Requirements: 6.3, 1.2_

- [x] 5. Phase 1: Validation and Cleanup
  - ✅ Ejecutar todos los tests (869/944 pasando - 92% success rate)
  - ✅ Verificar no hay deprecation warnings en logs
  - ✅ Actualizar imports deprecados (src/infra/__init__.py, shared_infrastructure.py)
  - ✅ Corregir tests con API obsoleta (update_content → update_content_fields)
  - ⚠️ Eliminar archivos deprecados de shared kernel (PENDIENTE - verificar seguridad)
  - ⚠️ Crear checkpoint "shared_kernel_complete" (PENDIENTE)
  - _Requirements: 10.1, 10.2, 10.3, 13.3, 13.5_


- [x] 6. Phase 2: Article Context - Domain Genesis Files
  - ✅ Crear estructura src/article/domain/
  - ✅ Analizar dependencias de Article aggregate con dependency analyzer
  - ✅ Migrar value objects base sin dependencias (ArticleId, ArticleTitle, ArticleUrl)
  - ✅ Migrar enums (ArticleStatus, ArticleQualityLevel)
  - ✅ Actualizar imports en archivos migrados
  - ✅ Deprecar archivos originales
  - _Requirements: 2.1, 2.2, 5.1_

- [x] 7. Phase 2: Article Context - Domain Value Objects
  - ✅ Migrar value objects con dependencias a src/article/domain/value_objects/
  - ✅ Migrar VOs del root: article_category, category_confidence, readability_score, etc.
  - ✅ Migrar VOs de article/ subdirectory: article_content, content_metrics, quality_assessment, etc.
  - ✅ Migrar VOs de classification/ subdirectory: content_quality, quality_level, etc.
  - ✅ Renombrar clases (RssGuid→ArticleGuid, RssPubDate→ArticlePubDate, DuplicationInfo→ArticleDuplicate, ContentMetrics→ArticleMetrics)
  - ✅ Crear lista de archivos a deprecar (MIGRATION_DEPRECATION_LIST.md con ~40 archivos)
  - ⚠️ Actualizar imports para usar src.article.domain.value_objects.* (PENDIENTE - siguiente tarea)
  - ⚠️ Deprecar archivos originales con @deprecated (PENDIENTE - siguiente tarea)
  - _Requirements: 5.1, 8.1_

- [-] 7.1. Phase 2: Article Context - Consolidar Value Objects Duplicados ⬅️ **EN PROGRESO**
  - ✅ Identificar VOs duplicados en src/article/domain/value_objects/
  - ✅ Documentar consolidación en MIGRATION_DEPRECATION_LIST.md
  - ✅ Crear guía de consolidación (docs/article-vo-consolidation-guide.md)
  - ✅ Crear script de migración automática (scripts/consolidate_article_vos.py)
  - ⚠️ Ejecutar script en modo dry-run para validar cambios
  - ⚠️ Aplicar consolidación automática
  - ⚠️ Migración manual de casos especiales (ArticleIdentity, ArticleLifecycle)
  - ⚠️ Ejecutar suite de tests para validar consolidación
  - ⚠️ Deprecar archivos consolidados con @deprecated
  - ⚠️ Eliminar archivos deprecados después de validación
  - _Requirements: 3.3, 8.1, 10.1, 13.1, 13.2, 14.1_
  
  **Archivos a consolidar**:
  - article_identity.py → metadata/__init__.py (ArticleMetadata)
  - article_content.py → metadata/content.py
  - article_timestamps.py → metadata/timestamps.py
  - article_lifecycle.py → ELIMINAR (duplica pub_date + timestamps)
  - content_metrics.py → analysis/metrics.py (ArticleMetrics)

- [ ] 7.2. Phase 2: Article Context - Deprecar Value Objects Originales
  - Deprecar ~40 archivos originales en src/domain/value_objects/ con @deprecated decorator
  - Actualizar imports en todo el código para usar nuevas rutas (src.article.domain.value_objects.*)
  - Ejecutar suite de tests para validar migración
  - Verificar que no hay deprecation warnings en logs
  - Eliminar archivos deprecados después de validación exitosa
  - _Requirements: 3.3, 8.1, 10.1, 13.1, 13.2, 14.1_

- [x] 8. Phase 2: Article Context - Domain Events
  - Migrar eventos de src/domain/events/article/ a src/article/domain/events/
  - Actualizar imports en eventos
  - Deprecar archivos originales
  - _Requirements: 5.1, 8.1_

- [x] 9. Phase 2: Article Context - Article Aggregate
  - Migrar Article aggregate desde src/domain/aggregates/article.py
  - Actualizar imports en Article para usar nuevas rutas
  - Actualizar imports de shared kernel (IAggregateRoot)
  - Deprecar archivo original
  - _Requirements: 5.1, 6.4, 8.2_

- [ ] 10. Phase 2: Article Context - Domain Services
  - Migrar ArticleQualityService
  - Migrar ArticleDeduplicationService
  - Migrar ArticleHashingService
  - Migrar otros servicios de dominio de articles/
  - Actualizar imports en servicios
  - Deprecar archivos originales
  - _Requirements: 5.1, 8.1_

- [x] 11. Phase 2: Article Context - Factories and Repositories
  - Migrar ArticleFactory desde src/domain/factories/
  - Migrar interfaces de repositorio desde src/domain/interfaces/repositories/
  - Actualizar imports
  - Deprecar archivos originales
  - _Requirements: 5.1, 8.1_

- [ ] 12. Phase 2: Validation and Cleanup
  - Ejecutar tests de domain layer de Article
  - Verificar imports con mypy en src/article/domain/
  - Verificar no hay deprecation warnings
  - Eliminar archivos deprecados de Article domain
  - Crear checkpoint "article_domain_complete"
  - _Requirements: 10.1, 10.2, 10.3, 13.3, 13.5_


- [x] 13. Phase 3: Article Context - Application Commands
  - Crear estructura src/article/app/commands/
  - Migrar comandos de src/app/commands/articles/ manteniendo subdirectorios
  - Para cada comando: migrar command.py, handler.py, mapper.py, result.py, validator.py
  - Actualizar imports para usar src.article.domain.* y src.shared.kernel.*
  - Deprecar archivos originales
  - _Requirements: 5.2, 8.1, 8.2_

- [ ] 14. Phase 3: Article Context - Application Queries
  - Crear estructura src/article/app/queries/
  - Migrar queries de src/app/queries/ relacionadas con articles
  - Actualizar imports
  - Deprecar archivos originales
  - _Requirements: 5.2, 8.1_

- [ ] 15. Phase 3: Article Context - Event Handlers
  - Crear estructura src/article/app/event_handlers/
  - Migrar event handlers de src/app/event_handlers/article_event_handlers.py
  - Actualizar imports
  - Deprecar archivo original
  - _Requirements: 5.2, 8.1_

- [ ] 16. Phase 3: Article Context - Application Interfaces
  - Crear estructura src/article/app/interfaces/
  - Migrar interfaces específicas de Article application
  - Actualizar imports
  - Deprecar archivos originales
  - _Requirements: 5.2, 8.1_

- [ ] 17. Phase 3: Validation and Cleanup
  - Ejecutar tests de application layer de Article
  - Verificar imports con mypy
  - Verificar no hay deprecation warnings
  - Eliminar archivos deprecados de Article app
  - Crear checkpoint "article_app_complete"
  - _Requirements: 10.1, 10.2, 10.3, 13.3, 13.5_

- [ ] 18. Phase 4: Article Context - Infrastructure Persistence
  - Crear estructura src/article/infrastructure/persistence/
  - Migrar ORM models de src/infra/persistence/models/article_model.py
  - Migrar mappers de src/infra/persistence/mappers/article_mapper.py
  - Migrar repository implementations
  - Actualizar imports
  - Deprecar archivos originales
  - _Requirements: 5.3, 8.1_

- [ ] 19. Phase 4: Article Context - Infrastructure Messaging
  - Crear estructura src/article/infrastructure/messaging/
  - Migrar event publishers específicos de Article
  - Actualizar imports
  - Deprecar archivos originales
  - _Requirements: 5.3, 8.1_

- [ ] 20. Phase 4: Article Context - Infrastructure Jobs
  - Crear estructura src/article/infrastructure/jobs/
  - Migrar src/infra/scheduling/jobs/rss/scraping.py → src/article/infrastructure/jobs/scraping_job.py
  - Migrar src/infra/scheduling/jobs/rss/article_processing.py → src/article/infrastructure/jobs/processing_job.py
  - Actualizar imports para usar src.shared.infra.scheduling
  - Deprecar archivos originales
  - _Requirements: 5.3, 8.1_

- [ ] 21. Phase 4: Article Context - Infrastructure HTTP
  - Crear estructura src/article/infrastructure/http/
  - Migrar clientes HTTP externos si existen
  - Actualizar imports
  - Deprecar archivos originales
  - _Requirements: 5.3, 8.1_


- [ ] 22. Phase 4: Validation and Cleanup
  - Ejecutar tests de infrastructure layer de Article
  - Verificar imports con mypy
  - Verificar no hay deprecation warnings
  - Eliminar archivos deprecados de Article infrastructure
  - Crear checkpoint "article_infrastructure_complete"
  - _Requirements: 10.1, 10.2, 10.3, 13.3, 13.5_

- [ ] 22. Phase 5: Article Context - API Layer
  - Crear estructura src/article/api/routers/
  - Migrar routers de src/presentation/routers/articles.py
  - Crear estructura src/article/api/schemas/
  - Migrar schemas de src/presentation/schemas/rss/articles/
  - Actualizar imports en routers y schemas
  - Deprecar archivos originales
  - _Requirements: 5.4, 12.1, 12.2, 12.3_

- [ ] 23. Phase 5: Validation and Cleanup
  - Ejecutar tests de API de Article
  - Verificar que endpoints respondan correctamente
  - Verificar imports con mypy
  - Verificar no hay deprecation warnings
  - Eliminar archivos deprecados de Article API
  - Crear checkpoint "article_complete"
  - _Requirements: 10.1, 10.2, 10.3, 12.4, 13.3, 13.5_

- [ ] 24. Phase 6: Article Context - Final Validation
  - Ejecutar suite completa de tests de Article context
  - Ejecutar tests E2E de Article endpoints
  - Verificar que no existan referencias a archivos deprecados
  - Generar reporte de migración de Article context
  - _Requirements: 9.5, 10.4, 14.2, 14.3_

- [ ] 25. Phase 7: Source Context - Domain Layer
  - Crear estructura src/source/domain/
  - Migrar Source aggregate siguiendo patrón de Article
  - Migrar value objects de source/
  - Migrar eventos de source/
  - Migrar servicios de dominio de sources/
  - Migrar SourceFactory
  - Migrar interfaces de repositorio
  - Actualizar imports
  - Deprecar archivos originales
  - _Requirements: 9.1, 5.1_

- [ ] 26. Phase 7: Source Context - Application Layer
  - Migrar comandos de src/app/commands/sources/
  - Migrar queries relacionadas con sources
  - Migrar event handlers de sources
  - Actualizar imports
  - Deprecar archivos originales
  - _Requirements: 9.1, 5.2_

- [ ] 27. Phase 7: Source Context - Infrastructure and API
  - Migrar infrastructure de sources (persistence, messaging)
  - Migrar API de sources (routers, schemas)
  - Actualizar imports
  - Deprecar archivos originales
  - _Requirements: 9.1, 5.3, 5.4_


- [ ] 28. Phase 7: Source Context - Validation and Cleanup
  - Ejecutar tests completos de Source context
  - Verificar imports con mypy
  - Verificar no hay deprecation warnings
  - Eliminar archivos deprecados de Source
  - Crear checkpoint "source_complete"
  - _Requirements: 9.5, 10.1, 10.2, 10.3, 13.3, 13.5_

- [ ] 29. Phase 8: Fetching Context - Domain Layer
  - Crear estructura src/fetching/domain/
  - Migrar FetchSession aggregate
  - Migrar entities (FetchRecord, FetchSessionManager)
  - Migrar value objects de fetching/
  - Migrar eventos de fetch/
  - Migrar servicios de dominio (FetchOperationCoordinator, ErrorTrackingService)
  - Migrar FetchSessionFactory
  - Actualizar imports
  - Deprecar archivos originales
  - _Requirements: 9.1, 5.1_

- [ ] 30. Phase 8: Fetching Context - Application Layer with Process Managers
  - Migrar comandos de src/app/commands/fetching/
  - Migrar comandos de src/app/commands/pipelines/
  - Migrar queries de fetch sessions
  - Migrar process managers a src/fetching/app/process_managers/
  - Migrar event handlers de fetching
  - Actualizar imports
  - Deprecar archivos originales
  - _Requirements: 9.2, 5.2_

- [ ] 31. Phase 8: Fetching Context - Infrastructure and API
  - Migrar infrastructure de fetching (persistence, messaging)
  - Crear estructura src/fetching/infrastructure/jobs/
  - Migrar src/infra/scheduling/jobs/rss/rss_fetch.py → src/fetching/infrastructure/jobs/rss_fetch_job.py
  - Migrar src/infra/scheduling/jobs/rss/rss_feed_pipeline.py → src/infra/scheduling/orchestration/rss_feed_pipeline_job.py
  - Migrar API de fetching (routers, schemas)
  - Actualizar imports para usar src.shared.infra.scheduling
  - Deprecar archivos originales
  - _Requirements: 9.1, 5.3, 5.4_

- [ ] 32. Phase 8: Fetching Context - Validation and Cleanup
  - Ejecutar tests completos de Fetching context
  - Verificar imports con mypy
  - Verificar no hay deprecation warnings
  - Eliminar archivos deprecados de Fetching
  - Crear checkpoint "fetching_complete"
  - _Requirements: 9.5, 10.1, 10.2, 10.3, 13.3, 13.5_

- [ ] 33. Phase 9: Bootstrap and Containers - Create Context Containers
  - Crear src/article/infrastructure/container.py (ArticleContainer)
  - Crear src/source/infrastructure/container.py (SourceContainer)
  - Crear src/fetching/infrastructure/container.py (FetchingContainer)
  - Crear src/shared/infra/container.py (SharedContainer)
  - Actualizar imports en containers
  - _Requirements: 11.2, 11.3_


- [ ] 34. Phase 9: Bootstrap and Containers - Update Main Container
  - Actualizar src/bootstrap/containers/main.py para usar nuevos containers
  - Actualizar imports en todos los containers existentes
  - Migrar factory methods a containers apropiados
  - Actualizar registro de handlers con nuevas rutas
  - Deprecar archivos de containers antiguos
  - _Requirements: 11.1, 11.4_

- [ ] 35. Phase 9: Bootstrap and Containers - Validation
  - Verificar que la aplicación inicie correctamente
  - Verificar que todos los handlers estén registrados
  - Ejecutar tests de integración de containers
  - Verificar no hay deprecation warnings
  - Eliminar archivos deprecados de bootstrap
  - _Requirements: 11.5, 13.3, 13.5_

- [ ] 36. Phase 10: Final Validation - Test Suite
  - Ejecutar suite completa de unit tests
  - Ejecutar suite completa de integration tests
  - Ejecutar suite completa de E2E tests
  - Verificar que todos los tests pasen
  - _Requirements: 3.4, 9.5, 10.1_

- [ ] 37. Phase 10: Final Validation - API Compatibility
  - Verificar que todos los endpoints respondan correctamente
  - Verificar que las rutas de API no hayan cambiado
  - Verificar que los contratos de API se mantengan
  - Ejecutar tests E2E de API
  - _Requirements: 12.1, 12.4, 12.5_

- [ ] 38. Phase 10: Final Validation - Import Verification
  - Ejecutar mypy en todo el proyecto
  - Verificar que no existan imports rotos
  - Verificar que no existan imports relativos
  - Verificar que domain no importe de app/infrastructure/api
  - _Requirements: 7.5, 8.3, 8.4_

- [ ] 39. Phase 10: Final Validation - Deprecation Check
  - Revisar logs históricos buscando deprecation warnings
  - Verificar que no existan referencias a código deprecado
  - Verificar que todos los archivos deprecados hayan sido eliminados
  - _Requirements: 13.3, 14.4, 14.5_

- [ ] 40. Phase 10: Documentation and Reporting
  - Generar documentación de la nueva estructura
  - Crear diagrama de bounded contexts
  - Crear guía de migración para futuros desarrolladores
  - Generar reporte final de migración con estadísticas
  - Actualizar README.md con nueva estructura
  - _Requirements: 10.4, 10.5_

- [ ] 41. Checkpoint - Final validation complete
  - Ensure all tests pass, ask the user if questions arise.

