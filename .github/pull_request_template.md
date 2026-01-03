## Descripción

<!-- Describe los cambios realizados en este PR -->

## Tipo de Cambio

<!-- Marca con 'x' el tipo de cambio -->

- [ ] 🐛 Bug fix (cambio que corrige un issue)
- [ ] ✨ Nueva funcionalidad (cambio que agrega funcionalidad)
- [ ] 💥 Breaking change (cambio que rompe compatibilidad)
- [ ] 📝 Documentación (cambios solo en documentación)
- [ ] 🎨 Refactoring (cambio que no corrige bug ni agrega funcionalidad)
- [ ] ⚡ Performance (cambio que mejora performance)
- [ ] ✅ Tests (agregar o corregir tests)
- [ ] 🔧 Chore (cambios en build, CI, dependencias)

## Motivación y Contexto

<!-- ¿Por qué es necesario este cambio? ¿Qué problema resuelve? -->
<!-- Si corrige un issue abierto, linkéalo aquí: Fixes #123 -->

## ¿Cómo se ha probado?

<!-- Describe las pruebas que ejecutaste para verificar los cambios -->

- [ ] Tests unitarios
- [ ] Tests de integración
- [ ] Tests manuales
- [ ] Property-based tests

**Detalles de testing**:
<!-- Describe escenarios de prueba específicos -->

## Checklist

<!-- Marca con 'x' los items completados -->

### Código
- [ ] Mi código sigue las convenciones de estilo del proyecto
- [ ] He ejecutado `black` y `isort` en mi código
- [ ] He ejecutado `mypy` y corregido errores de tipo
- [ ] He ejecutado `flake8` y corregido warnings
- [ ] He agregado tests que prueban mi cambio
- [ ] Todos los tests nuevos y existentes pasan localmente
- [ ] He verificado que no hay regresiones

### Documentación
- [ ] He actualizado la documentación relevante
- [ ] He actualizado docstrings en funciones/clases modificadas
- [ ] He actualizado README.md si es necesario
- [ ] He actualizado archivos en `.kiro/steering/` si es necesario

### Domain-Driven Design
- [ ] Los cambios respetan los bounded contexts
- [ ] Los agregados mantienen sus invariantes
- [ ] Los eventos de dominio están correctamente definidos
- [ ] Los value objects son inmutables
- [ ] La lógica de negocio está en el domain layer

### Clean Architecture
- [ ] Las dependencias apuntan hacia el dominio
- [ ] No hay dependencias de infrastructure en domain
- [ ] Los handlers usan el mediator correctamente
- [ ] Los repositorios implementan interfaces del dominio

### CQRS
- [ ] Commands y Queries están separados
- [ ] Commands modifican estado, Queries solo leen
- [ ] Los handlers tienen una sola responsabilidad
- [ ] Los mappers están en el lugar correcto

### Base de Datos
- [ ] He creado migraciones de Alembic si es necesario
- [ ] Las migraciones son reversibles (up/down)
- [ ] He probado las migraciones en ambiente local
- [ ] Los índices están correctamente definidos

### Seguridad
- [ ] No hay credenciales hardcodeadas
- [ ] Los datos sensibles están en variables de entorno
- [ ] He validado inputs de usuario
- [ ] He considerado casos de edge y errores

## Screenshots (si aplica)

<!-- Agrega screenshots si hay cambios visuales -->

## Impacto

### Breaking Changes
<!-- Si hay breaking changes, descríbelos aquí -->

- [ ] Este PR introduce breaking changes
- [ ] He actualizado la documentación de migración

### Performance
<!-- Si hay impacto en performance, descríbelo -->

- [ ] Este PR mejora performance
- [ ] Este PR puede afectar performance negativamente
- [ ] No hay impacto en performance

### Dependencias
<!-- Si agregaste/actualizaste dependencias -->

- [ ] He agregado nuevas dependencias
- [ ] He actualizado dependencias existentes
- [ ] He verificado vulnerabilidades con `safety check`

## Notas Adicionales

<!-- Cualquier información adicional para los revisores -->

## Checklist para Revisores

<!-- Para los revisores del PR -->

- [ ] El código es legible y mantenible
- [ ] Los tests cubren casos importantes
- [ ] La documentación es clara
- [ ] No hay code smells obvios
- [ ] Los principios SOLID se respetan
- [ ] La arquitectura se mantiene limpia
- [ ] No hay duplicación innecesaria

---

**Relacionado con**: <!-- Links a issues, PRs, documentos -->
