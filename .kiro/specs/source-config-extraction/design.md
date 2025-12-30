# Design Document

## Overview

Este documento describe el diseño técnico para extraer y gestionar las configuraciones de sources desde archivos estáticos en lugar de la base de datos. La solución utiliza archivos Python con dataclasses para definir configuraciones tipadas, organizadas por dominio con soporte para herencia y overrides.

## Architecture

### Decisión: Archivos Python con Dataclasses

**Razón de la elección:**
- ✅ Type hints nativos (validación en tiempo de desarrollo)
- ✅ Autocompletado en IDEs
- ✅ Versionado en Git
- ✅ Fácil de importar y usar en código
- ✅ Permite herencia y composición
- ✅ Validación con Pydantic (opcional)

**Alternativas descartadas:**
- ❌ YAML/JSON: Sin type hints, validación en runtime
- ❌ DB + Cache: Más complejo, no versionado
- ❌ Configuración dinámica: Dificulta debugging

### Estructura de Directorios

```
src/shared/config/
├── __init__.py
├── sources/
│   ├── __init__.py
│   ├── base.py                    # Configuraciones base y defaults
│   ├── registry.py                # Registry para acceder a configs
│   ├── domains/
│   │   ├── __init__.py
│   │   ├── cointelegraph.py      # Config para cointelegraph.com
│   │   ├── coindesk.py           # Config para coindesk.com
│   │   └── default.py            # Config por defecto
│   └── sources/
│       ├── __init__.py
│       ├── cointelegraph_rss.py  # Config específica
│       └── coindesk_rss.py       # Config específica
└── loader.py                      # Cargador de configuraciones
```


## Components and Interfaces

### 1. ScrapingConfig (Base Dataclass)

```python
from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class ScrapingConfig:
    """Configuración de scraping para una source."""
    
    # Selectores CSS
    content_selectors: List[str] = field(default_factory=list)
    excluded_selectors: List[str] = field(default_factory=list)
    fallback_selectors: List[str] = field(default_factory=list)
    
    # Estrategias de espera
    scroll_needed: bool = False
    wait_strategy: str = "domcontentloaded"  # domcontentloaded, networkidle, load
    wait_timeout_ms: int = 3000
    selector_timeout_ms: int = 5000
    
    # Filtros de texto
    excluded_texts: List[str] = field(default_factory=list)
    excluded_text_patterns: List[str] = field(default_factory=list)
    
    def merge_with(self, other: "ScrapingConfig") -> "ScrapingConfig":
        """Merge con otra config (override)."""
        pass
```

### 2. SourceConfig (Configuración Completa)

```python
@dataclass
class SourceConfig:
    """Configuración completa de una source."""
    
    # Identificación
    source_id: str
    name: str
    url: str
    domain: str
    
    # Configuración de scraping
    scraping: ScrapingConfig
    
    # Configuración de fetching
    fetch_interval_minutes: int = 360
    timeout_seconds: int = 30
    max_retries: int = 3
    
    # HTTP
    user_agent: Optional[str] = None
    follow_redirects: bool = True
    verify_ssl: bool = True
    custom_headers: dict = field(default_factory=dict)
```


### 3. SourceConfigRegistry (Singleton)

```python
class SourceConfigRegistry:
    """Registry para acceder a configuraciones de sources."""
    
    def __init__(self):
        self._configs: Dict[str, SourceConfig] = {}
        self._domain_configs: Dict[str, ScrapingConfig] = {}
        self._default_config: ScrapingConfig = None
    
    def register_source(self, config: SourceConfig) -> None:
        """Registra una configuración de source."""
        pass
    
    def register_domain_config(self, domain: str, config: ScrapingConfig) -> None:
        """Registra una configuración base por dominio."""
        pass
    
    def get_source_config(self, source_id: str) -> Optional[SourceConfig]:
        """Obtiene configuración de una source por ID."""
        pass
    
    def get_config_by_domain(self, domain: str) -> Optional[ScrapingConfig]:
        """Obtiene configuración base por dominio."""
        pass
    
    def get_config_by_url(self, url: str) -> Optional[SourceConfig]:
        """Obtiene configuración por URL."""
        pass
    
    def list_all_configs(self) -> List[SourceConfig]:
        """Lista todas las configuraciones."""
        pass
    
    def has_config(self, source_id: str) -> bool:
        """Verifica si existe configuración para una source."""
        pass
    
    def get_default_config(self) -> ScrapingConfig:
        """Obtiene configuración por defecto."""
        pass
```

### 4. ConfigLoader

```python
class ConfigLoader:
    """Cargador de configuraciones desde archivos Python."""
    
    def __init__(self, registry: SourceConfigRegistry, logger: ILogger):
        self._registry = registry
        self._logger = logger
    
    def load_all_configs(self) -> None:
        """Carga todas las configuraciones."""
        self._load_domain_configs()
        self._load_source_configs()
        self._validate_configs()
    
    def _load_domain_configs(self) -> None:
        """Carga configuraciones base por dominio."""
        pass
    
    def _load_source_configs(self) -> None:
        """Carga configuraciones específicas de sources."""
        pass
    
    def _validate_configs(self) -> None:
        """Valida todas las configuraciones cargadas."""
        pass
```


## Data Models

### Ejemplo: Configuración de Cointelegraph

```python
# src/shared/config/sources/domains/cointelegraph.py

from src.shared.config.sources.base import ScrapingConfig

COINTELEGRAPH_BASE_CONFIG = ScrapingConfig(
    # Selectores de contenido principal
    content_selectors=[
        ".post-content",
        "article",
        "main"
    ],
    
    # Elementos a excluir (ads, banners, forms, etc.)
    excluded_selectors=[
        "#buzzsprout-player",
        ".m-auto.relative",
        ".newsletter-subscription-form",
        ".post-content__disclaimer",
        ".text-banner",
        "[aria-label*=\"advertisement\"]",
        "[class*=\"-tos\"]",
        "[class*=\"comment\"]",
        "[class*=\"newsletter-subscription\"]",
        "[class*=\"related\"]",
        "[class*=\"share\"]",
        "[class*=\"social\"]",
        "[class*=\"widget\"]",
        "[data-ct-widget]",
        "aside",
        "footer",
        "form",
        "header",
        "iframe",
        "nav",
        "noscript",
        "script",
        "svg",
        "template"
    ],
    
    # Selectores de respaldo
    fallback_selectors=[
        "article",
        "main",
        "[role='main']",
        ".article-content",
        ".post-content",
        ".entry-content",
        "body"
    ],
    
    # Estrategia de espera
    scroll_needed=True,
    wait_strategy="domcontentloaded",
    wait_timeout_ms=3000,
    selector_timeout_ms=5000,
    
    # Patrones de texto a excluir
    excluded_text_patterns=[
        "Related:",
        "Magazine:"
    ]
)
```


### Ejemplo: Configuración Específica de Source

```python
# src/shared/config/sources/sources/cointelegraph_rss.py

from src.shared.config.sources.base import SourceConfig
from src.shared.config.sources.domains.cointelegraph import COINTELEGRAPH_BASE_CONFIG

COINTELEGRAPH_RSS_CONFIG = SourceConfig(
    source_id="7222b20f-fde7-46c8-a6ab-812ad398f260",
    name="cointelegraph",
    url="https://cointelegraph.com/rss",
    domain="cointelegraph.com",
    
    # Usa configuración base de dominio
    scraping=COINTELEGRAPH_BASE_CONFIG,
    
    # Configuración de fetching
    fetch_interval_minutes=360,
    timeout_seconds=30,
    max_retries=3,
    
    # HTTP
    user_agent="Mozilla/5.0 (compatible; ScrapingService/1.0)",
    follow_redirects=True,
    verify_ssl=True
)
```

### Ejemplo: Override de Configuración

```python
# Si una source necesita configuración personalizada

from dataclasses import replace

CUSTOM_CONFIG = replace(
    COINTELEGRAPH_BASE_CONFIG,
    # Override solo lo necesario
    wait_timeout_ms=5000,
    excluded_selectors=COINTELEGRAPH_BASE_CONFIG.excluded_selectors + [
        ".custom-element"  # Agregar selector adicional
    ]
)
```


## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Config loading completeness
*For any* source defined en los archivos de configuración, cuando el sistema carga las configuraciones, entonces todas las sources deben estar registradas en el registry
**Validates: Requirements 1.1, 1.2**

### Property 2: Domain config inheritance
*For any* source que usa una configuración de dominio base, cuando se obtiene su configuración, entonces debe incluir todos los campos de la configuración base más cualquier override específico
**Validates: Requirements 2.2, 2.4**

### Property 3: Config validation on load
*For any* configuración cargada, cuando el sistema valida las configuraciones, entonces todas las configuraciones con campos requeridos faltantes deben generar warnings pero no fallar el inicio
**Validates: Requirements 3.1, 3.2, 3.3**

### Property 4: Default config fallback
*For any* source sin configuración específica, cuando se solicita su configuración, entonces el sistema debe retornar la configuración por defecto del dominio o la configuración global por defecto
**Validates: Requirements 1.4, 2.4**

### Property 5: Config registry uniqueness
*For any* dos sources con el mismo source_id, cuando se registran en el registry, entonces solo la última configuración debe permanecer y se debe registrar un warning
**Validates: Requirements 3.5**

### Property 6: Selector list immutability
*For any* configuración cargada, cuando se obtiene una lista de selectores, entonces modificar la lista retornada no debe afectar la configuración original
**Validates: Requirements 1.2**

### Property 7: Hot reload validation
*For any* archivo de configuración modificado en modo development, cuando se detecta el cambio, entonces el sistema debe validar la nueva configuración antes de aplicarla y mantener la anterior si la validación falla
**Validates: Requirements 6.3, 6.4**


## Error Handling

### Configuración Inválida

```python
class ConfigValidationError(Exception):
    """Error cuando una configuración es inválida."""
    pass

class ConfigNotFoundError(Exception):
    """Error cuando no se encuentra una configuración."""
    pass
```

**Estrategia:**
- Validación al cargar: Log warning, usar defaults
- Configuración faltante: Log warning, usar config de dominio o default
- Selectores inválidos: Log warning, continuar (validación en runtime)
- Timeouts fuera de rango: Log warning, usar valores por defecto

### Logging

```python
# Al cargar configuraciones
logger.info("Cargando configuraciones de sources", count=len(configs))

# Configuración faltante
logger.warning(
    "Source sin configuración específica, usando default",
    source_id=source_id,
    domain=domain
)

# Validación fallida
logger.warning(
    "Configuración inválida detectada",
    source_id=source_id,
    errors=validation_errors
)

# Hot reload
logger.info(
    "Configuración recargada",
    source_id=source_id,
    file=config_file
)
```


## Testing Strategy

### Unit Tests

**Ubicación:** `tests/unit/shared/config/sources/`

**Tests de ScrapingConfig:**
```python
def test_scraping_config_defaults():
    """Debería usar valores por defecto correctos."""
    
def test_scraping_config_merge():
    """Debería mergear configuraciones correctamente."""
    
def test_scraping_config_immutability():
    """Listas de selectores deben ser inmutables."""
```

**Tests de SourceConfigRegistry:**
```python
def test_register_and_retrieve_source_config():
    """Debería registrar y recuperar configuración."""
    
def test_get_config_by_domain():
    """Debería obtener configuración por dominio."""
    
def test_get_config_by_url():
    """Debería obtener configuración por URL."""
    
def test_fallback_to_default():
    """Debería usar default cuando no existe config."""
    
def test_duplicate_source_id_warning():
    """Debería registrar warning con IDs duplicados."""
```

**Tests de ConfigLoader:**
```python
def test_load_all_configs():
    """Debería cargar todas las configuraciones."""
    
def test_validate_configs():
    """Debería validar configuraciones al cargar."""
    
def test_invalid_config_uses_default():
    """Debería usar default con config inválida."""
```

### Property-Based Tests

**Framework:** `hypothesis`

```python
from hypothesis import given, strategies as st

@given(
    content_selectors=st.lists(st.text(min_size=1), min_size=1),
    wait_timeout_ms=st.integers(min_value=100, max_value=30000)
)
def test_scraping_config_always_valid(content_selectors, wait_timeout_ms):
    """Configuración debe ser válida con cualquier input válido."""
    config = ScrapingConfig(
        content_selectors=content_selectors,
        wait_timeout_ms=wait_timeout_ms
    )
    assert len(config.content_selectors) > 0
    assert config.wait_timeout_ms > 0
```

### Integration Tests

**Tests con archivos reales:**
```python
def test_load_cointelegraph_config():
    """Debería cargar configuración de Cointelegraph."""
    
def test_load_coindesk_config():
    """Debería cargar configuración de Coindesk."""
    
def test_all_sources_have_valid_configs():
    """Todas las sources deben tener configuraciones válidas."""
```


## Migration Strategy

### Script de Migración

**Ubicación:** `scripts/migrate_source_configs.py`

```python
"""
Script para migrar configuraciones desde DB a archivos Python.

Uso:
    python scripts/migrate_source_configs.py --output src/shared/config/sources/
"""

import asyncio
from sqlalchemy import select
from src.infra.persistence.models import SourceModel

async def migrate_configs():
    """Migra configuraciones desde DB a archivos."""
    
    # 1. Conectar a DB
    # 2. Obtener todas las sources
    # 3. Agrupar por dominio
    # 4. Generar archivos de configuración
    # 5. Generar reporte
    
    pass

def generate_domain_config(domain: str, sources: List[SourceModel]) -> str:
    """Genera archivo de configuración de dominio."""
    pass

def generate_source_config(source: SourceModel) -> str:
    """Genera archivo de configuración de source."""
    pass
```

### Pasos de Migración

1. **Backup de DB**
   ```bash
   docker exec tradingapp-postgres pg_dump -U postgres postgres > backup.sql
   ```

2. **Ejecutar script de migración**
   ```bash
   python scripts/migrate_source_configs.py
   ```

3. **Revisar archivos generados**
   - Verificar que todas las sources fueron migradas
   - Revisar configuraciones por dominio
   - Ajustar manualmente si es necesario

4. **Actualizar código para usar registry**
   - Modificar handlers que consultan DB
   - Usar `SourceConfigRegistry` en lugar de queries

5. **Testing**
   - Ejecutar tests unitarios
   - Ejecutar tests de integración
   - Verificar scraping funciona correctamente

6. **Deprecar campos en DB (opcional)**
   - Mantener campos por compatibilidad
   - Agregar comentarios indicando que se usan archivos estáticos


## Integration with Existing Code

### Uso en Scraping Handlers

**Antes (consultando DB):**
```python
class ScrapeArticleContentHandler:
    async def handle(self, command: ScrapeArticleContentCommand):
        # Consultar source desde DB
        source = await self._source_repo.find_by_id(command.source_id)
        
        # Usar scraping_config de la DB
        scraping_config = source.scraping_config
        
        # Scraping...
```

**Después (usando registry):**
```python
class ScrapeArticleContentHandler:
    def __init__(
        self,
        config_registry: SourceConfigRegistry,
        scraper_service: IScraperService,
        logger: ILogger
    ):
        self._config_registry = config_registry
        self._scraper_service = scraper_service
        self._logger = logger
    
    async def handle(self, command: ScrapeArticleContentCommand):
        # Obtener config desde registry (en memoria)
        source_config = self._config_registry.get_source_config(command.source_id)
        
        if not source_config:
            # Fallback a config por defecto
            source_config = self._config_registry.get_default_config()
        
        # Usar scraping config
        scraping_config = source_config.scraping
        
        # Scraping con configuración
        content = await self._scraper_service.scrape(
            url=command.article_url,
            config=scraping_config
        )
```

### Dependency Injection

```python
# src/shared/container.py

class SharedContainer(containers.DeclarativeContainer):
    
    def get_source_config_registry(self) -> SourceConfigRegistry:
        """Factory para SourceConfigRegistry (Singleton)."""
        if not hasattr(self, '_config_registry'):
            registry = SourceConfigRegistry()
            loader = ConfigLoader(registry, self.infra.logger)
            loader.load_all_configs()
            self._config_registry = registry
        return self._config_registry
```


## Hot Reload (Development Mode)

### File Watcher

```python
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class ConfigFileHandler(FileSystemEventHandler):
    """Handler para detectar cambios en archivos de configuración."""
    
    def __init__(self, loader: ConfigLoader, logger: ILogger):
        self._loader = loader
        self._logger = logger
    
    def on_modified(self, event):
        """Cuando un archivo es modificado."""
        if event.src_path.endswith('.py'):
            self._logger.info("Config file modified", file=event.src_path)
            try:
                # Recargar configuraciones
                self._loader.load_all_configs()
                self._logger.info("Configs reloaded successfully")
            except Exception as e:
                self._logger.error("Failed to reload configs", error=str(e))

class ConfigWatcher:
    """Watcher para hot reload de configuraciones."""
    
    def __init__(self, config_dir: str, loader: ConfigLoader, logger: ILogger):
        self._config_dir = config_dir
        self._loader = loader
        self._logger = logger
        self._observer = None
    
    def start(self):
        """Inicia el watcher."""
        if os.getenv("ENVIRONMENT") != "development":
            return
        
        handler = ConfigFileHandler(self._loader, self._logger)
        self._observer = Observer()
        self._observer.schedule(handler, self._config_dir, recursive=True)
        self._observer.start()
        self._logger.info("Config watcher started", dir=self._config_dir)
    
    def stop(self):
        """Detiene el watcher."""
        if self._observer:
            self._observer.stop()
            self._observer.join()
```

### Uso en Startup

```python
# src/main.py

async def startup():
    # Cargar configuraciones
    registry = container.shared.get_source_config_registry()
    
    # Iniciar watcher en development
    if config.environment == "development":
        watcher = ConfigWatcher(
            config_dir="src/shared/config/sources",
            loader=container.shared.get_config_loader(),
            logger=logger
        )
        watcher.start()
```


## Performance Considerations

### Memory Usage

**Estimación:**
- ~50 sources × ~2KB por config = ~100KB
- Negligible para aplicación moderna
- Todas las configs en memoria (no lazy loading)

### Startup Time

**Impacto:**
- Cargar 50 configs: ~10-50ms
- Validación: ~5-10ms
- Total: <100ms adicional al startup
- Aceptable para aplicación

### Access Time

**Antes (DB query):**
- Query a DB: 5-50ms
- Parsing JSON: 1-5ms
- Total: 6-55ms por access

**Después (registry):**
- Dict lookup: <1ms
- Total: <1ms por access
- **Mejora: 6-55x más rápido**

### Caching Strategy

No necesario - todas las configs ya están en memoria.

## Backward Compatibility

### Fase de Transición

**Opción 1: Dual mode (recomendado)**
```python
class ScrapeArticleContentHandler:
    async def handle(self, command):
        # Intentar obtener desde registry
        config = self._config_registry.get_source_config(command.source_id)
        
        if not config:
            # Fallback a DB (backward compatibility)
            source = await self._source_repo.find_by_id(command.source_id)
            config = self._convert_db_to_config(source)
        
        # Usar config...
```

**Opción 2: Registry only (más limpio)**
```python
# Todas las sources deben estar en registry
# Si no existe, usar default
config = self._config_registry.get_source_config(command.source_id)
if not config:
    config = self._config_registry.get_default_config()
```

### Mantener DB Sync (Opcional)

Si se desea mantener DB actualizada:
```python
# Script para sincronizar configs a DB
async def sync_configs_to_db():
    """Sincroniza configuraciones desde archivos a DB."""
    registry = SourceConfigRegistry()
    loader = ConfigLoader(registry, logger)
    loader.load_all_configs()
    
    for config in registry.list_all_configs():
        await update_source_in_db(config)
```


## Benefits Summary

### Development Experience
- ✅ Type hints y autocompletado en IDE
- ✅ Validación en tiempo de desarrollo
- ✅ Fácil de modificar y testear
- ✅ Versionado en Git (historial de cambios)
- ✅ Code review de configuraciones

### Performance
- ✅ 6-55x más rápido que queries a DB
- ✅ Sin overhead de red
- ✅ Sin parsing de JSON en runtime
- ✅ Todas las configs en memoria

### Maintainability
- ✅ Configuraciones organizadas por dominio
- ✅ Reutilización de configs base
- ✅ Fácil agregar nuevas sources
- ✅ Documentación inline con comentarios
- ✅ Refactoring seguro con type hints

### Operations
- ✅ No requiere acceso a DB para configs
- ✅ Configs versionadas con código
- ✅ Deploy atómico (código + configs)
- ✅ Rollback fácil (Git revert)
- ✅ Hot reload en development

## Risks and Mitigations

### Risk 1: Configuraciones desincronizadas con DB

**Mitigación:**
- Script de migración inicial
- Documentar que archivos son source of truth
- Opcional: Script de sync configs → DB

### Risk 2: Merge conflicts en Git

**Mitigación:**
- Archivos separados por source
- Estructura clara y organizada
- Documentación de formato

### Risk 3: Configuraciones inválidas en producción

**Mitigación:**
- Validación al cargar
- Tests de integración
- CI/CD valida configs antes de deploy

### Risk 4: Pérdida de flexibilidad (no cambios sin deploy)

**Mitigación:**
- Hot reload en development
- Deploy rápido con CI/CD
- Configuraciones por dominio (menos cambios)

## Future Enhancements

### Phase 2: UI para editar configuraciones
- Admin panel para modificar configs
- Genera archivos Python automáticamente
- Preview de cambios antes de commit

### Phase 3: A/B testing de configuraciones
- Múltiples configs por source
- Selección basada en feature flags
- Métricas de performance por config

### Phase 4: Machine learning para optimizar selectores
- Analizar éxito de scraping
- Sugerir mejores selectores
- Auto-ajuste de timeouts

