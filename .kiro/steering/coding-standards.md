# Estándares de Código

## Python Version
- Python 3.11+
- Usar type hints en todas las funciones y métodos

## Code Style

### Formatting
- **Black**: Formatter automático (line-length: 88)
- **isort**: Ordenar imports (profile: black)
- Ejecutar antes de commit:
  ```bash
  black src/ tests/
  isort src/ tests/
  ```

### Linting
- **flake8**: Linter para detectar problemas
- **mypy**: Type checking estático
- Configuración en `pyproject.toml`

## Type Hints

### Obligatorio
```python
# ✅ Correcto
def calculate_score(content: str, threshold: float) -> float:
    return len(content) * threshold

async def fetch_articles(source_id: str) -> list[Article]:
    pass

# ❌ Incorrecto
def calculate_score(content, threshold):
    return len(content) * threshold
```

### Tipos Complejos
```python
from typing import Optional, Union, Protocol
from collections.abc import Sequence

# Optional para valores que pueden ser None
def find_article(id: str) -> Optional[Article]:
    pass

# Protocol para duck typing
class IRepository(Protocol):
    async def save(self, entity: Entity) -> None:
        ...
```

## Naming Conventions

### Variables y Funciones
- **snake_case** para variables, funciones y métodos
- Nombres descriptivos, evitar abreviaciones

```python
# ✅ Correcto
article_count = 10
def calculate_quality_score(article: Article) -> float:
    pass

# ❌ Incorrecto
artCnt = 10
def calcQS(art):
    pass
```

### Clases
- **PascalCase** para clases
- Sustantivos descriptivos

```python
# ✅ Correcto
class ArticleRepository:
    pass

class ContentQualityAnalyzer:
    pass

# ❌ Incorrecto
class article_repo:
    pass
```

### Constantes
- **UPPER_SNAKE_CASE** para constantes

```python
# ✅ Correcto
MAX_RETRY_ATTEMPTS = 3
DEFAULT_TIMEOUT_SECONDS = 30

# ❌ Incorrecto
maxRetryAttempts = 3
```

### Private Members
- Prefijo `_` para métodos/atributos privados
- Prefijo `__` para name mangling (raro)

```python
class ArticleService:
    def __init__(self):
        self._cache = {}  # Privado
    
    def _validate_content(self, content: str) -> bool:
        # Método privado
        pass
```

## Docstrings

### Formato Google Style
```python
def fetch_articles(
    source_id: str,
    limit: int = 10,
    include_archived: bool = False
) -> list[Article]:
    """Fetch articles from a specific source.
    
    Args:
        source_id: The unique identifier of the source
        limit: Maximum number of articles to fetch
        include_archived: Whether to include archived articles
        
    Returns:
        List of Article objects matching the criteria
        
    Raises:
        SourceNotFoundException: If source_id doesn't exist
        FetchException: If fetching fails
    """
    pass
```

### Clases
```python
class ArticleQualityService:
    """Service for assessing article quality.
    
    This service analyzes various metrics to determine
    the quality level of an article.
    
    Attributes:
        threshold: Minimum quality score threshold
        analyzer: Content analyzer instance
    """
    
    def __init__(self, threshold: float):
        self.threshold = threshold
```

## Error Handling

### Custom Exceptions
```python
# Definir excepciones específicas del dominio
class DomainException(Exception):
    """Base exception for domain errors."""
    pass

class ArticleNotFoundException(DomainException):
    """Raised when article is not found."""
    pass

class InvalidContentException(DomainException):
    """Raised when content validation fails."""
    pass
```

### Try-Except
```python
# ✅ Correcto - Específico
try:
    article = await repository.find_by_id(article_id)
except ArticleNotFoundException:
    logger.warning(f"Article {article_id} not found")
    raise

# ❌ Incorrecto - Demasiado genérico
try:
    article = await repository.find_by_id(article_id)
except Exception:
    pass
```

## Async/Await

### Uso Consistente
```python
# ✅ Correcto
async def fetch_and_process(source_id: str) -> ProcessingResult:
    articles = await fetch_articles(source_id)
    results = await asyncio.gather(
        *[process_article(a) for a in articles]
    )
    return combine_results(results)

# ❌ Incorrecto - Mezclar sync/async sin razón
def fetch_and_process(source_id: str):
    articles = asyncio.run(fetch_articles(source_id))
    # ...
```

## Imports

### Orden
1. Standard library
2. Third-party packages
3. Local application imports

```python
# ✅ Correcto
import asyncio
from datetime import datetime
from typing import Optional

from sqlalchemy import select
from pydantic import BaseModel

from src.domain.aggregates.article import Article
from src.domain.value_objects.content_quality import ContentQuality
```

### Imports Absolutos
```python
# ✅ Correcto
from src.domain.aggregates.article import Article
from src.infra.persistence.repositories.article_repository import ArticleRepository

# ❌ Incorrecto
from ..domain.aggregates.article import Article
```

## Logging

### Uso de Loguru
```python
from loguru import logger

# Niveles apropiados
logger.debug("Detailed debug information")
logger.info("General information")
logger.warning("Warning message")
logger.error("Error occurred", exc_info=True)

# Contexto estructurado
logger.info(
    "Article processed",
    article_id=article.id,
    quality_score=article.quality_score
)
```

## Testing

### Naming
```python
# test_<module>_<function>.py
# test_article_repository.py

class TestArticleRepository:
    def test_save_article_success(self):
        pass
    
    def test_save_article_with_invalid_data_raises_exception(self):
        pass
    
    async def test_find_by_id_returns_article(self):
        pass
```

### Arrange-Act-Assert
```python
def test_calculate_quality_score():
    # Arrange
    article = Article(content="test content")
    service = ArticleQualityService(threshold=0.5)
    
    # Act
    score = service.calculate_score(article)
    
    # Assert
    assert score > 0.5
    assert isinstance(score, float)
```

## Comments

### Cuándo Comentar
- Lógica compleja no obvia
- Decisiones de diseño importantes
- Workarounds temporales (con TODO/FIXME)

```python
# ✅ Correcto - Explica el "por qué"
# We use exponential backoff here because the external API
# has rate limiting that requires increasing delays
await retry_with_backoff(fetch_content)

# ❌ Incorrecto - Explica el "qué" (obvio del código)
# Increment counter by 1
counter += 1
```

### TODO/FIXME
```python
# TODO: Implement caching for frequently accessed articles
# FIXME: This breaks with Unicode characters in titles
# HACK: Temporary workaround until API v2 is available
```

## Performance

### List Comprehensions vs Loops
```python
# ✅ Preferir comprehensions cuando sea legible
article_ids = [a.id for a in articles if a.is_published]

# ✅ Usar loops para lógica compleja
processed = []
for article in articles:
    if article.is_published:
        result = complex_processing(article)
        if result.is_valid:
            processed.append(result)
```

### Generators para Grandes Datasets
```python
# ✅ Correcto - Usa generator
def fetch_all_articles() -> Generator[Article, None, None]:
    for batch in fetch_batches():
        yield from batch

# ❌ Incorrecto - Carga todo en memoria
def fetch_all_articles() -> list[Article]:
    return [article for batch in fetch_batches() for article in batch]
```
