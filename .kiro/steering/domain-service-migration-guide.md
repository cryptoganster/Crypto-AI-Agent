# Guía de Migración de Domain Services a Bounded Contexts

## Introducción

Esta guía documenta el proceso para migrar domain services desde `src/domain/services/` a sus respectivos bounded contexts siguiendo los principios de Domain-Driven Design y Clean Architecture.

## Cuándo Migrar un Domain Service

Migrar un domain service cuando:
- ✅ El service está claramente asociado a un bounded context específico
- ✅ El service solo opera sobre aggregates de un bounded context
- ✅ El service no es compartido entre múltiples bounded contexts
- ✅ Se quiere mejorar la cohesión del bounded context

NO migrar cuando:
- ❌ El service es compartido entre múltiples bounded contexts
- ❌ El service contiene lógica cross-cutting
- ❌ El service es parte del shared kernel

## Estructura de Destino

```
src/<bounded-context>/domain/
├── services/
│   ├── __init__.py
│   └── <service_name>.py
├── interfaces/
│   ├── services/
│   │   ├── __init__.py
│   │   └── <service_name>.py
│   └── external/
│       ├── __init__.py
│       └── <external_service_name>.py
```

## Checklist de Migración

### Fase 1: Preparación

- [ ] 1. Identificar el domain service a migrar
- [ ] 2. Verificar que pertenece a un solo bounded context
- [ ] 3. Identificar todas las dependencias del service
- [ ] 4. Identificar todos los archivos que importan el service
- [ ] 5. Decidir el nuevo nombre del archivo (más corto y descriptivo)

### Fase 2: Crear Estructura

- [ ] 6. Crear directorios si no existen:
  ```bash
  mkdir -p src/<bounded-context>/domain/services
  mkdir -p src/<bounded-context>/domain/interfaces/services
  mkdir -p src/<bounded-context>/domain/interfaces/external  # si aplica
  ```

- [ ] 7. Crear archivo de interface en nueva ubicación
  - Ubicación: `src/<bounded-context>/domain/interfaces/services/<service_name>.py`
  - Si no existe interface, crearla (Dependency Inversion Principle)
  - Usar `Protocol` o `ABC` según corresponda

- [ ] 8. Crear archivo de implementación en nueva ubicación
  - Ubicación: `src/<bounded-context>/domain/services/<service_name>.py`
  - Copiar código del service original
  - Actualizar imports internos

- [ ] 9. Crear/actualizar `__init__.py` en `services/`
  ```python
  from .service_name import ServiceClass
  
  __all__ = ["ServiceClass"]
  ```

- [ ] 10. Crear/actualizar `__init__.py` en `interfaces/services/`
  ```python
  from .service_name import IServiceClass
  
  __all__ = ["IServiceClass"]
  ```

### Fase 3: Actualizar Dependencias

- [ ] 11. Actualizar imports en handlers
  ```python
  # Antes
  from src.domain.services.articles.article_xxx_service import ArticleXxxService
  
  # Después
  from src.article.domain.services import ArticleXxxService
  ```

- [ ] 12. Actualizar imports en containers (DI)
  ```python
  # Antes
  from src.domain.services.articles.article_xxx_service import ArticleXxxService
  
  # Después
  from src.article.domain.services import ArticleXxxService
  ```

- [ ] 13. Actualizar imports en otros services
  - Buscar: `grep -r "from src.domain.services" src/`
  - Actualizar cada ocurrencia

- [ ] 14. Actualizar imports en infrastructure
  - Buscar en `src/infra/`
  - Actualizar adaptadores que usen el service

- [ ] 15. Actualizar imports en tests
  - Buscar en `tests/`
  - Actualizar todos los tests que importen el service

### Fase 4: Deprecar Archivos Originales

- [ ] 16. Agregar comentario DEPRECATED al archivo original del service
  ```python
  """
  DEPRECATED: Este archivo ha sido movido a src/<bounded-context>/domain/services/<service_name>.py
  
  <Descripción original>
  
  MIGRACIÓN:
  - Nuevo módulo: src/<bounded-context>/domain/services/<service_name>.py
  - Nueva interface: src/<bounded-context>/domain/interfaces/services/<service_name>.py
  - Usar: from src.<bounded-context>.domain.services import ServiceClass
  """
  ```

- [ ] 17. Agregar comentario DEPRECATED a la interface original (si existe)
  ```python
  """
  DEPRECATED: Este archivo ha sido movido a src/<bounded-context>/domain/interfaces/services/<service_name>.py
  
  Interface para ServiceClass.
  
  MIGRACIÓN:
  - Nuevo módulo: src/<bounded-context>/domain/interfaces/services/<service_name>.py
  - Usar: from src.<bounded-context>.domain.interfaces.services import IServiceClass
  """
  ```

### Fase 5: Verificación

- [ ] 18. Verificar que todos los imports funcionan
  ```bash
  python -c "from src.<bounded-context>.domain.services import ServiceClass"
  python -c "from src.<bounded-context>.domain.interfaces.services import IServiceClass"
  ```

- [ ] 19. Ejecutar tests relacionados
  ```bash
  pytest tests/unit/<bounded-context>/ -v
  pytest tests/integration/<bounded-context>/ -v
  ```

- [ ] 20. Ejecutar suite completa de tests
  ```bash
  pytest tests/ -v
  ```

- [ ] 21. Verificar que no hay imports rotos
  ```bash
  # Buscar imports del archivo antiguo
  grep -r "from src.domain.services.<old-path>" src/
  grep -r "from src.domain.interfaces.services.<old-path>" src/
  ```

- [ ] 22. Verificar que handlers funcionan
  ```python
  # Importar todos los handlers que usan el service
  from src.<bounded-context>.app.commands.xxx.handler import XxxHandler
  ```

### Fase 6: Documentación

- [ ] 23. Crear documento de resumen de migración
  - Ubicación: `DOMAIN_SERVICES_MIGRATION_SUMMARY.md`
  - Incluir: servicios migrados, cambios de imports, archivos actualizados

- [ ] 24. Crear guía rápida de referencia
  - Ubicación: `MIGRATION_QUICK_REFERENCE.md`
  - Incluir: tabla de cambios de imports, verificación rápida

- [ ] 25. Actualizar documentación de arquitectura
  - Actualizar `.kiro/steering/architecture.md` si es necesario
  - Actualizar diagramas de bounded contexts

### Fase 7: Limpieza (Opcional - Después de 1-2 Sprints)

- [ ] 26. Eliminar archivos deprecados
  ```bash
  rm src/domain/services/<old-path>/<service_file>.py
  rm src/domain/interfaces/services/<old-path>/<interface_file>.py
  ```

- [ ] 27. Actualizar `__init__.py` en ubicaciones antiguas
  - Remover exports de services migrados

- [ ] 28. Verificar que no quedan referencias
  ```bash
  grep -r "ServiceClass" src/domain/services/
  grep -r "IServiceClass" src/domain/interfaces/services/
  ```

## Convenciones de Naming

### Archivos
- **Service**: `<feature>_<action>.py` (ej: `metrics_calculation.py`)
- **Interface**: Mismo nombre que el service
- **Evitar**: Prefijos redundantes como `article_` si ya está en `src/article/`

### Clases
- **Service**: `Article<Feature>Service` (ej: `ArticleMetricsCalculationService`)
- **Interface**: `IArticle<Feature>Service` (ej: `IArticleMetricsCalculationService`)

### Imports
```python
# ✅ CORRECTO - Import desde __init__.py
from src.article.domain.services import ArticleMetricsCalculationService
from src.article.domain.interfaces.services import IArticleMetricsCalculationService

# ❌ INCORRECTO - Import directo del archivo
from src.article.domain.services.metrics_calculation import ArticleMetricsCalculationService
```

## Casos Especiales

### Services Externos (Infrastructure)

Si el service es una interface para servicios externos (Playwright, Trafilatura, etc.):

- **Ubicación**: `src/<bounded-context>/domain/interfaces/external/`
- **Ejemplo**: `IArticleScrapingService` → `src/article/domain/interfaces/external/scraping_service.py`

```python
# __init__.py en interfaces/external/
from .scraping_service import IArticleScrapingService

__all__ = ["IArticleScrapingService"]
```

### Services sin Interface

Si el service no tiene interface, crear una:

1. Crear interface usando `Protocol` o `ABC`
2. Hacer que el service implemente la interface
3. Actualizar handlers para depender de la interface (DIP)

```python
# Interface (Protocol)
from typing import Protocol
from src.article.domain.aggregates.article import Article

class IArticleMetricsCalculationService(Protocol):
    def calculate_metrics(self, article: Article) -> tuple[int, int]:
        ...

# Implementación
class ArticleMetricsCalculationService(IArticleMetricsCalculationService):
    def calculate_metrics(self, article: Article) -> tuple[int, int]:
        # Implementación
        pass
```

### Services con Dependencias Auxiliares

Si el service tiene clases auxiliares (ej: `SentenceRelevanceScorer`):

1. Migrar las clases auxiliares al mismo bounded context
2. Mantenerlas en el mismo archivo o crear archivo separado
3. Exportar desde `__init__.py`

```python
# __init__.py
from .summary_extraction import ArticleSummaryExtractionService
from .sentence_relevance_scorer import SentenceRelevanceScorer, ScoredSentence

__all__ = [
    "ArticleSummaryExtractionService",
    "SentenceRelevanceScorer",
    "ScoredSentence",
]
```

## Comandos Útiles

### Buscar Imports del Service Antiguo
```bash
# Buscar imports del service
grep -r "from src.domain.services.articles.article_xxx_service" src/

# Buscar imports de la interface
grep -r "from src.domain.interfaces.services.articles.article_xxx_service" src/

# Buscar cualquier referencia al service
grep -r "ArticleXxxService" src/
```

### Verificar Imports Nuevos
```bash
# Verificar que el service se puede importar
python -c "from src.article.domain.services import ArticleXxxService; print('✓ OK')"

# Verificar que la interface se puede importar
python -c "from src.article.domain.interfaces.services import IArticleXxxService; print('✓ OK')"
```

### Ejecutar Tests Específicos
```bash
# Tests del bounded context
pytest tests/unit/article/ -v

# Tests que usan el service
pytest tests/ -k "article_xxx" -v

# Tests de property-based testing
pytest tests/pbt/ -v
```

## Ejemplo Completo: ArticleMetricsCalculationService

### Antes de la Migración
```
src/domain/
├── services/
│   └── articles/
│       └── article_metrics_calculation_service.py
└── interfaces/
    └── services/
        └── articles/
            └── article_metrics_calculation_service.py
```

### Después de la Migración
```
src/article/domain/
├── services/
│   ├── __init__.py
│   └── metrics_calculation.py
└── interfaces/
    └── services/
        ├── __init__.py
        └── metrics_calculation.py
```

### Cambio de Import
```python
# ❌ ANTES
from src.domain.services.articles.article_metrics_calculation_service import (
    ArticleMetricsCalculationService,
)
from src.domain.interfaces.services.articles import (
    IArticleMetricsCalculationService,
)

# ✅ DESPUÉS
from src.article.domain.services import ArticleMetricsCalculationService
from src.article.domain.interfaces.services import IArticleMetricsCalculationService
```

## Beneficios de la Migración

1. **Mejor Organización**: Código relacionado agrupado en bounded context
2. **Clean Architecture**: Separación clara de responsabilidades
3. **Mantenibilidad**: Más fácil encontrar y modificar código
4. **Preparación para Microservicios**: Bounded contexts bien definidos
5. **Imports Limpios**: Imports más cortos y claros

## Referencias

- **Architecture**: `.kiro/steering/architecture.md`
- **Domain Patterns**: `.kiro/steering/domain-patterns.md`
- **Coding Standards**: `.kiro/steering/coding-standards.md`
- **Testing Guidelines**: `.kiro/steering/testing-guidelines.md`

## Historial de Migraciones

### 2024-12-02: Article Domain Services
- ✅ ArticleMetricsCalculationService
- ✅ ArticleLanguageDetectionService
- ✅ ArticlePlaintextExtractionService (+ nueva interface)
- ✅ ArticleSummaryExtractionService (renombrado de ArticleContentExtractionService)
- ✅ IArticleScrapingService (a interfaces/external)
- ✅ SentenceRelevanceScorer (auxiliar)

**Resultado**: 5 services migrados, 5 interfaces migradas, todos los tests pasando.

---

**Última actualización**: 2024-12-02
