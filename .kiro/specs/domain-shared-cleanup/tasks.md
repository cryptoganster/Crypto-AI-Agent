# Implementation Plan: Domain Shared Cleanup

- [x] 1. Crear script de análisis exhaustivo
  - Implementar `ExhaustiveClassAnalyzer` para analizar cada clase
  - Implementar detección de imports (estática)
  - Implementar detección de uso real (no solo imports)
  - Implementar análisis de tests y cobertura
  - Implementar detección de duplicados
  - Implementar análisis de dependencias (usa/usada por)
  - Implementar cálculo de métricas (LOC, complejidad)
  - Implementar detección de metadata (última modificación, autor)
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_

- [x] 2. Ejecutar análisis automático inicial
  - Ejecutar script sobre todas las clases en `src/domain/shared/`
  - Generar informe preliminar en formato markdown
  - Incluir los 10 puntos de análisis por cada clase
  - Generar estadísticas generales
  - Identificar duplicados automáticamente
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 2.1_

- [x] 3. Verificación manual del informe automático (CRÍTICA)
  - Revisar CADA clase marcada para eliminación
  - Buscar falsos positivos (marcadas como no usadas pero sí usadas)
  - Buscar falsos negativos (marcadas como usadas pero no usadas)
  - Verificar imports dinámicos manualmente
  - Revisar TODOs y comentarios en código
  - Consultar historial de commits
  - Validar contexto de negocio de cada clase
  - _Requirements: 1.1, 1.2, 1.3, 3.1_

- [x] 4. Análisis exhaustivo de MetricType duplicado
  - Comparar versión en `src/domain/shared/value_objects/classification/`
  - Comparar versión en `src/domain/value_objects/classification/`
  - Verificar que son idénticas
  - Identificar todos los imports de ambas versiones
  - Determinar cuál versión se usa más
  - Confirmar decisión: mantener en `domain/value_objects/`, eliminar de `shared/`
  - _Requirements: 2.1, 2.2, 2.3, 2.4_

- [x] 5. Análisis exhaustivo de clases de similitud huérfanas
  - Analizar `DomainSimilarityScore` - buscar palabras clave relacionadas
  - Analizar `PatternSimilarityWeights` - buscar casos de uso potenciales
  - Analizar `SimilarityExplanation` - evaluar valor para UI/API
  - Analizar `SimilarityThreshold` - comparar con `QualityThreshold`
  - Documentar casos de uso futuros para cada una
  - Decidir: MANTENER con documentación o ELIMINAR
  - _Requirements: 3.1, 3.2, 4.1, 4.2_

- [ ] 6. Generar informe exhaustivo final
  - Crear `docs/domain-shared-analysis-report.md`
  - Incluir Executive Summary con estadísticas
  - Incluir análisis detallado de TODAS las clases (sección por clase)
  - Incluir matriz de duplicados con comparación
  - Incluir lista de clases huérfanas con potencial
  - Incluir plan de acción detallado
  - Incluir notas de verificación manual realizada
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

- [x] 7. Checkpoint - Revisión manual del plan de acción
  - Revisar informe exhaustivo completo
  - Validar todas las decisiones (MANTENER/ELIMINAR/CONSOLIDAR)
  - Confirmar que no hay falsos positivos
  - Obtener aprobación del equipo si es necesario
  - Solo proceder si hay certeza 100%

- [ ] 8. Consolidar MetricType (eliminar de shared)
  - Actualizar imports en `src/domain/shared/value_objects/__init__.py`
  - Cambiar import para usar versión de `domain/value_objects/`
  - Eliminar archivo `src/domain/shared/value_objects/classification/metric_type.py`
  - Actualizar `src/domain/shared/value_objects/classification/__init__.py`
  - _Requirements: 2.5, 3.4_

- [ ] 9. Verificar que tests pasen después de consolidación
  - Ejecutar todos los tests unitarios
  - Ejecutar todos los tests de integración
  - Verificar que no hay imports rotos
  - Verificar que no hay regresiones
  - _Requirements: 3.3_

- [ ] 10. Documentar clases de similitud mantenidas
  - Crear docstrings detallados para `DomainSimilarityScore`
  - Crear docstrings detallados para `PatternSimilarityWeights`
  - Crear docstrings detallados para `SimilarityExplanation`
  - Crear docstrings detallados para `SimilarityThreshold`
  - Documentar casos de uso futuros en cada clase
  - Agregar ejemplos de uso en docstrings
  - _Requirements: 4.3, 4.4_

- [ ] 11. Actualizar documentación de arquitectura
  - Actualizar `.kiro/steering/architecture.md` con estructura final
  - Documentar decisión de priorizar versiones fuera de shared
  - Documentar clases mantenidas en shared y sus propósitos
  - Actualizar diagrama de dependencias si existe
  - _Requirements: 5.5, 7.5_

- [ ] 12. Crear ADR para decisiones importantes
  - Crear ADR: "Priorizar versiones fuera de shared/"
  - Crear ADR: "Mantener clases de similitud para uso futuro"
  - Crear ADR: "No consolidar SimilarityThreshold con QualityThreshold"
  - Documentar contexto, decisión, consecuencias
  - _Requirements: 5.5_

- [ ] 13. Checkpoint final - Verificación completa
  - Revisar todos los cambios realizados
  - Ejecutar suite completa de tests
  - Verificar que informe exhaustivo está completo
  - Verificar que documentación está actualizada
  - Confirmar que no hay regresiones

- [ ] 14. Generar reporte de limpieza final
  - Resumir clases analizadas (total)
  - Resumir clases eliminadas (con justificación)
  - Resumir clases consolidadas (con mapeo)
  - Resumir clases mantenidas (con documentación)
  - Incluir métricas: LOC eliminadas, imports actualizados, tests afectados
  - Incluir lecciones aprendidas
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_
