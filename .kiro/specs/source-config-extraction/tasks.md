# Implementation Plan

- [ ] 1. Crear estructura base de configuraciones
  - Crear directorio `src/shared/config/sources/`
  - Crear subdirectorios `domains/` y `sources/`
  - Crear archivo `base.py` con dataclasses base
  - _Requirements: 1.1, 7.1-7.5_

- [ ] 1.1 Implementar ScrapingConfig dataclass
  - Definir campos para selectores CSS (content, excluded, fallback)
  - Definir campos para estrategias de espera (scroll_needed, wait_strategy, timeouts)
  - Definir campos para filtros de texto (excluded_texts, excluded_text_patterns)
  - Implementar método `merge_with()` para combinar configuraciones
  - _Requirements: 2.2_

- [ ] 1.2 Implementar SourceConfig dataclass
  - Definir campos de identificación (source_id, name, url, domain)
  - Incluir ScrapingConfig como campo
  - Definir campos de fetching (fetch_interval, timeout, max_retries)
  - Definir campos HTTP (user_agent, follow_redirects, verify_ssl, custom_headers)
  - _Requirements: 1.1_

- [ ]* 1.3 Escribir tests unitarios para dataclasses
  - Test de valores por defecto de ScrapingConfig
  - Test de merge de configuraciones
  - Test de inmutabilidad de listas
  - Test de creación de SourceConfig
  - _Requirements: 1.1, 2.2_

- [ ] 2. Implementar SourceConfigRegistry
  - Crear clase SourceConfigRegistry como singleton
  - Implementar diccionarios internos (_configs, _domain_configs, _default_config)
  - Implementar método `register_source()`
  - Implementar método `register_domain_config()`
  - _Requirements: 1.2, 7.1-7.5_

- [ ] 2.1 Implementar métodos de consulta del registry
  - Implementar `get_source_config(source_id)`
  - Implementar `get_config_by_domain(domain)`
  - Implementar `get_config_by_url(url)`
  - Implementar `list_all_configs()`
  - Implementar `has_config(source_id)`
  - Implementar `get_default_config()`
  - _Requirements: 7.1-7.5_

- [ ] 2.2 Implementar resolución de jerarquía de configuraciones
  - Implementar lógica específica > dominio > default
  - Implementar matching de patrones de dominio
  - Implementar fallback a configuración por defecto
  - _Requirements: 1.4, 2.4_

- [ ]* 2.3 Escribir property test para resolución de jerarquía
  - **Property 2: Domain config inheritance**
  - **Validates: Requirements 2.2, 2.4**

- [ ]* 2.4 Escribir tests unitarios para registry
  - Test de registro y recuperación de configs
  - Test de consulta por dominio
  - Test de consulta por URL
  - Test de fallback a default
  - Test de warning con IDs duplicados
  - _Requirements: 1.2, 1.4, 3.5_

- [ ] 3. Implementar ConfigLoader
  - Crear clase ConfigLoader
  - Implementar método `load_all_configs()`
  - Implementar método `_load_domain_configs()`
  - Implementar método `_load_source_configs()`
  - _Requirements: 1.1, 3.1_

- [ ] 3.1 Implementar validación de configuraciones
  - Implementar método `_validate_configs()`
  - Validar campos requeridos presentes
  - Validar rangos de timeouts
  - Registrar warnings para configs inválidas
  - Usar valores por defecto cuando sea necesario
  - _Requirements: 3.1, 3.2, 3.3, 3.4_

- [ ] 3.2 Implementar manejo de errores en carga
  - Crear excepciones `ConfigValidationError` y `ConfigNotFoundError`
  - Implementar logging detallado de errores
  - Continuar carga con warnings en lugar de fallar
  - _Requirements: 3.1, 3.2, 3.3_

- [ ]* 3.3 Escribir property test para validación
  - **Property 3: Config validation on load**
  - **Validates: Requirements 3.1, 3.2, 3.3**

- [ ]* 3.4 Escribir tests unitarios para loader
  - Test de carga de todas las configs
  - Test de validación de configs
  - Test de uso de default con config inválida
  - _Requirements: 1.1, 3.1_

- [ ] 4. Crear configuración por defecto
  - Crear archivo `src/shared/config/sources/domains/default.py`
  - Definir DEFAULT_SCRAPING_CONFIG con valores sensatos
  - Documentar cada campo con comentarios
  - _Requirements: 1.4, 5.1-5.5_

- [ ] 5. Migrar configuraciones existentes desde DB
  - Crear script `scripts/migrate_source_configs.py`
  - Implementar conexión a DB y consulta de sources
  - Implementar agrupación de sources por dominio
  - _Requirements: 4.1_

- [ ] 5.1 Implementar generación de archivos de configuración
  - Implementar función `generate_domain_config()`
  - Implementar función `generate_source_config()`
  - Formatear código Python correctamente
  - Preservar todos los campos de scraping_config
  - _Requirements: 4.2, 4.3_

- [ ] 5.2 Implementar manejo de valores NULL en migración
  - Detectar campos NULL en DB
  - Usar valores por defecto apropiados
  - Documentar campos con defaults
  - _Requirements: 4.5_

- [ ] 5.3 Generar reporte de migración
  - Contar sources migradas
  - Listar dominios identificados
  - Reportar configuraciones con valores NULL
  - Guardar reporte en archivo
  - _Requirements: 4.4_

- [ ]* 5.4 Escribir property test para migración
  - **Property 4: Default config fallback**
  - **Validates: Requirements 1.4, 2.4**

- [ ] 6. Ejecutar migración y crear configuraciones
  - Ejecutar script de migración contra DB
  - Revisar archivos generados manualmente
  - Crear configuraciones de dominio (cointelegraph, coindesk)
  - Crear configuraciones específicas de sources
  - _Requirements: 4.1, 4.2, 4.3_

- [ ] 7. Checkpoint - Verificar configuraciones migradas
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 8. Integrar registry con dependency injection
  - Agregar factory `get_source_config_registry()` en SharedContainer
  - Implementar carga de configs al inicio
  - Registrar como singleton
  - _Requirements: 1.1_

- [ ] 8.1 Actualizar handlers para usar registry
  - Modificar ScrapeArticleContentHandler para usar registry
  - Remover consultas a DB para obtener scraping_config
  - Implementar fallback a config por defecto
  - _Requirements: 1.2_

- [ ]* 8.2 Escribir property test para acceso sin DB
  - **Property 1: Config loading completeness**
  - **Validates: Requirements 1.1, 1.2**

- [ ]* 8.3 Escribir tests de integración
  - Test de carga de config de Cointelegraph
  - Test de carga de config de Coindesk
  - Test de que todas las sources tienen configs válidas
  - _Requirements: 1.1, 1.2_

- [ ] 9. Implementar hot reload para development
  - Instalar dependencia `watchdog`
  - Crear clase `ConfigFileHandler` para detectar cambios
  - Crear clase `ConfigWatcher` para observar directorio
  - _Requirements: 6.1, 6.2_

- [ ] 9.1 Implementar validación en hot reload
  - Validar nueva config antes de aplicar
  - Mantener config anterior si validación falla
  - Registrar errores de validación
  - _Requirements: 6.3, 6.4_

- [ ] 9.2 Integrar watcher con startup
  - Iniciar watcher solo en modo development
  - Deshabilitar en production
  - Agregar logging de eventos de reload
  - _Requirements: 6.5_

- [ ]* 9.3 Escribir property test para hot reload
  - **Property 7: Hot reload validation**
  - **Validates: Requirements 6.3, 6.4**

- [ ] 10. Checkpoint - Verificar integración completa
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 11. Documentar uso del sistema de configuraciones
  - Crear README en `src/shared/config/sources/`
  - Documentar cómo agregar nuevas sources
  - Documentar cómo crear configuraciones de dominio
  - Documentar estructura de archivos
  - _Requirements: 5.1-5.5_

- [ ] 11.1 Crear ejemplos de configuraciones
  - Ejemplo de configuración simple
  - Ejemplo de configuración con override
  - Ejemplo de configuración de dominio
  - _Requirements: 5.1-5.5_

- [ ]* 11.2 Escribir property tests adicionales
  - **Property 5: Config registry uniqueness**
  - **Property 6: Selector list immutability**
  - **Validates: Requirements 3.5, 1.2**

- [ ] 12. Testing final y validación
  - Ejecutar suite completa de tests
  - Verificar que scraping funciona correctamente
  - Verificar performance (acceso <1ms)
  - Verificar que no hay queries a DB para configs
  - _Requirements: 1.2_

- [ ] 13. Cleanup y optimización
  - Remover código deprecated relacionado con DB configs
  - Agregar comentarios en DB indicando uso de archivos estáticos
  - Optimizar imports y estructura de archivos
  - _Requirements: 1.1_
