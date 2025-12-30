# Implementation Plan

- [x] 1. Agregar find_by_guid al Repository
  - Agregar método find_by_guid() a IArticleReadRepository interface
  - Implementar find_by_guid() en ArticleReadRepository
  - Agregar tests unitarios para find_by_guid()
  - Agregar tests de integración con base de datos
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

- [ ] 2. Refactorizar ArticleDeduplicationService
  - Eliminar similarity_threshold del constructor
  - Eliminar métodos calculate_similarity(), is_duplicate(), find_duplicate(), find_all_duplicates()
  - Agregar enable_updates al constructor
  - Implementar nuevo check_duplicate() que retorna (is_duplicate, duplicate_id, match_method, is_update)
  - Implementar _check_by_guid() privado
  - Implementar _check_by_url() privado
  - Implementar _is_article_update() privado
  - Actualizar docstrings y type hints
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 2.1, 2.2, 2.3, 3.1, 3.2, 3.3, 3.4, 4.1, 4.2, 4.3, 4.4, 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7, 7.8_

- [ ] 3. Actualizar tests de ArticleDeduplicationService
  - Test: GUID match detecta duplicado con match_method='guid'
  - Test: URL match detecta duplicado cuando no hay GUID
  - Test: pub_date posterior marca como update (is_update=True)
  - Test: pub_date anterior marca como duplicate (is_update=False)
  - Test: Sin GUID usa solo verificación por URL
  - Test: enable_updates=False nunca marca update
  - Test: Artículo sin pub_date marca como duplicate
  - Test: Retorna None cuando no hay duplicado
  - Eliminar tests de similitud de contenido
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 2.1, 2.2, 4.1, 4.2, 4.3, 10.2, 10.3_

- [ ] 4. Crear UpdateArticleFromFeedCommand
  - Crear command.py con UpdateArticleFromFeedCommand dataclass
  - Incluir article_id, title, url, description, pub_date, content, author, categories, thumbnail_url
  - Incluir correlation_id y triggered_by para tracking
  - Agregar docstrings completos
  - _Requirements: 5.2, 8.4_

- [ ] 5. Crear UpdateArticleFromFeedResult
  - Crear result.py con UpdateArticleFromFeedResult
  - Implementar success(), not_found(), failure() factory methods
  - Incluir article en resultado exitoso
  - Incluir error_message en resultado fallido
  - _Requirements: 5.2_

- [ ] 6. Implementar UpdateArticleFromFeedHandler
  - Crear handler.py con UpdateArticleFromFeedHandler
  - Inyectar IArticleReadRepository, IArticleWriteRepository, IUnitOfWork, IEventBus, ILogger
  - Implementar handle() que carga artículo, actualiza campos, persiste, emite evento
  - Usar UoW para transacción
  - Publicar eventos fuera de transacción
  - Agregar logging detallado
  - _Requirements: 5.2, 5.3, 5.4, 5.5, 5.6_

- [ ] 7. Agregar tests para UpdateArticleFromFeedHandler
  - Test: Actualiza artículo exitosamente
  - Test: Retorna not_found si artículo no existe
  - Test: Emite ArticleUpdatedFromFeed event
  - Test: Usa UoW correctamente (commit en éxito, rollback en error)
  - Test: Actualiza solo campos modificados
  - Test: Logging correcto en éxito y error
  - _Requirements: 5.2, 5.3, 5.4, 5.5_

- [ ] 8. Implementar Article.update_from_feed()
  - Agregar método update_from_feed() a Article aggregate
  - Actualizar title si cambió (comparar Value Objects)
  - Actualizar url si cambió
  - Actualizar description si cambió
  - Actualizar pub_date si cambió
  - Actualizar content si se proporciona
  - Actualizar author si cambió
  - Actualizar categories si cambió
  - Actualizar thumbnail_url si cambió
  - Emitir ArticleUpdatedFromFeed event con lista de campos actualizados
  - Agregar método privado _get_updated_fields() para trackear cambios
  - _Requirements: 5.3, 5.4_

- [ ] 9. Agregar tests para Article.update_from_feed()
  - Test: Actualiza título si cambió
  - Test: Actualiza URL si cambió
  - Test: Actualiza contenido si se proporciona
  - Test: No actualiza si valores son iguales
  - Test: Emite ArticleUpdatedFromFeed event
  - Test: Event incluye lista de campos actualizados
  - Test: Maneja valores None correctamente
  - _Requirements: 5.3, 5.4_

- [ ] 10. Crear ArticleUpdatedFromFeed event
  - Crear article_updated_from_feed.py en domain/events
  - Definir dataclass frozen con article_id, updated_fields, occurred_at
  - Agregar docstrings explicando cuándo se emite
  - Exportar desde __init__.py
  - _Requirements: 5.5, 9.1, 9.2_

- [ ] 11. Implementar OnArticleUpdatedFromFeedHandler
  - Crear on_article_updated_from_feed.py en app/event_handlers
  - Inyectar IMediator (command bus) y ILogger
  - Implementar handle() que determina qué re-procesar según updated_fields
  - Si 'content' o 'url' cambió → emitir ScrapeArticleContentCommand
  - Si solo metadata cambió → emitir ExtractArticlePlaintextCommand
  - Agregar logging detallado
  - _Requirements: 9.3, 9.4, 9.5_

- [ ] 12. Agregar tests para OnArticleUpdatedFromFeedHandler
  - Test: Emite ScrapeArticleContentCommand si content cambió
  - Test: Emite ScrapeArticleContentCommand si url cambió
  - Test: Emite ExtractArticlePlaintextCommand si solo metadata cambió
  - Test: Logging correcto
  - Test: Usa correlation_id correcto
  - _Requirements: 9.3, 9.4_

- [ ] 13. Registrar UpdateArticleFromFeedHandler en container
  - Agregar factory method get_update_article_from_feed_handler() en ArticleContainer
  - Inyectar dependencias correctas
  - Registrar handler en mediator durante register_pipeline_handlers()
  - Agregar a lista de handlers registrados en logging
  - _Requirements: 5.2_

- [ ] 14. Registrar OnArticleUpdatedFromFeedHandler en event bus
  - Agregar factory method get_on_article_updated_from_feed_handler() en ArticleContainer
  - Registrar event handler en event bus durante register_event_handlers()
  - Agregar a lista de event handlers registrados en logging
  - _Requirements: 9.1, 9.2_

- [ ] 15. Actualizar ScrapingCoordinator para usar nuevo check_duplicate()
  - Actualizar llamada a check_duplicate() para recibir 4 valores (is_duplicate, duplicate_id, match_method, is_update)
  - Si is_update=True → emitir UpdateArticleFromFeedCommand con article_id y ArticleData
  - Si is_duplicate=True y is_update=False → skip artículo y loggear como duplicado
  - Si is_duplicate=False → continuar con creación normal
  - Agregar logging detallado con match_method
  - _Requirements: 1.5, 2.4, 8.1, 8.2, 8.3, 8.4, 8.5_

- [ ] 16. Agregar tests de integración para ScrapingCoordinator
  - Test: Detecta update por GUID y emite UpdateArticleFromFeedCommand
  - Test: Detecta duplicate por GUID y skip artículo
  - Test: Detecta duplicate por URL y skip artículo
  - Test: No detecta duplicate y crea artículo nuevo
  - Test: Logging correcto para cada caso
  - _Requirements: 8.1, 8.2, 8.3, 8.4_

- [ ] 17. Agregar configuración RSS_ENABLE_ARTICLE_UPDATES
  - Agregar enable_article_updates a RssConfig dataclass
  - Leer RSS_ENABLE_ARTICLE_UPDATES de variables de entorno (default: "true")
  - Pasar enable_article_updates a ArticleDeduplicationService en container
  - Agregar docstrings explicando el propósito
  - _Requirements: 10.1, 10.2, 10.3, 10.4_

- [ ] 18. Actualizar ArticleDeduplicationService para usar configuración
  - Usar self._enable_updates en _is_article_update()
  - Si enable_updates=False, siempre retornar False (tratar como duplicate)
  - Agregar logging WARNING cuando se detecta potencial update pero está deshabilitado
  - _Requirements: 10.2, 10.3, 10.5_

- [ ] 19. Agregar tests para configuración de updates
  - Test: enable_updates=True permite updates
  - Test: enable_updates=False trata updates como duplicates
  - Test: Logging WARNING cuando update detectado pero deshabilitado
  - Test: Configuración se lee correctamente de env vars
  - _Requirements: 10.1, 10.2, 10.3, 10.5_

- [ ] 20. Checkpoint - Verificar que todos los tests pasan
  - Ejecutar suite completa de tests unitarios
  - Ejecutar tests de integración
  - Verificar que no hay regresiones
  - Verificar logging en todos los flujos
  - _Ensure all tests pass, ask the user if questions arise._

- [ ] 21. Agregar logging detallado para observability
  - Logging INFO cuando se detecta duplicado (incluir match_method)
  - Logging INFO cuando se detecta update (incluir old/new pub_date)
  - Logging INFO cuando se actualiza artículo (incluir updated_fields)
  - Logging WARNING cuando update detectado pero deshabilitado
  - Logging ERROR cuando falla actualización
  - _Requirements: Observability_

- [ ] 22. Agregar métricas para monitoreo
  - Métrica: articles.duplicates.detected (counter, tags: match_method)
  - Métrica: articles.updates.processed (counter)
  - Métrica: articles.deduplication.duration (histogram, tags: match_method)
  - Métrica: articles.updates.duration (histogram)
  - _Requirements: Observability_

- [ ] 23. Actualizar documentación
  - Actualizar README con nueva funcionalidad de updates
  - Documentar variables de entorno RSS_ENABLE_ARTICLE_UPDATES
  - Agregar ejemplos de uso en docs/
  - Actualizar diagramas de arquitectura si es necesario
  - _Requirements: Documentation_

- [ ] 24. Test end-to-end del flujo completo
  - Test: Feed con artículo nuevo → crea artículo
  - Test: Feed con mismo GUID, pub_date posterior → actualiza artículo
  - Test: Feed con mismo GUID, pub_date anterior → skip como duplicado
  - Test: Feed con misma URL, sin GUID → skip como duplicado
  - Test: Artículo actualizado → re-procesa contenido → genera nuevos embeddings
  - _Requirements: 1.1, 2.1, 4.1, 5.1, 9.1_

- [ ] 25. Checkpoint final - Validación completa
  - Todos los tests pasan (unit, integration, e2e)
  - Logging funciona correctamente
  - Métricas se registran correctamente
  - Configuración funciona correctamente
  - No hay regresiones en funcionalidad existente
  - _Ensure all tests pass, ask the user if questions arise._
