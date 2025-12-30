# Patrones de Dominio

## Domain-Driven Design (DDD)

Este proyecto sigue principios de DDD para modelar la lógica de negocio.

## Building Blocks

### 1. Aggregates (Raíces de Agregado)

Los aggregates son clusters de objetos de dominio que se tratan como una unidad.

**Ubicación**: `src/domain/aggregates/`

**Aggregates en el proyecto**:
- `Article`: Artículo scrapeado con su contenido y metadatos
- `Source`: Fuente RSS con configuración y métricas
- `FetchSession`: Sesión de scraping con registros de fetch

**Reglas**:
- Solo la raíz del agregado puede ser referenciada desde fuera
- Las transacciones no deben cruzar límites de agregados
- Cada agregado tiene un ID único
- Los agregados publican eventos de dominio
- Todos los aggregates implementan `IAggregateRoot`

**Interface IAggregateRoot**:

Todos los aggregate roots implementan la interface `IAggregateRoot` que define el contrato básico para manejo de eventos de dominio:

```python
from abc import ABC, abstractmethod
from typing import Sequence
from src.domain.shared.interfaces.core.domain_event import IDomainEvent

class IAggregateRoot(ABC):
    """Interface base para Aggregate Roots."""
    
    @property
    @abstractmethod
    def domain_events(self) -> Sequence[IDomainEvent]:
        """Lista de eventos de dominio pendientes."""
        pass
    
    @abstractmethod
    def get_uncommitted_events(self) -> Sequence[IDomainEvent]:
        """Obtiene eventos no confirmados."""
        pass
    
    @abstractmethod
    def mark_events_as_committed(self) -> None:
        """Marca eventos como confirmados."""
        pass
    
    # Métodos de conveniencia (implementación por defecto)
    def has_uncommitted_events(self) -> bool:
        return len(self.get_uncommitted_events()) > 0
    
    def get_event_count(self) -> int:
        return len(self.get_uncommitted_events())
```

**Lo que NO incluye IAggregateRoot**:

Este proyecto NO implementa Event Sourcing. Por lo tanto, `IAggregateRoot` NO incluye:
- ❌ `load_from_history()` - No reconstruimos estado desde eventos
- ❌ `version` property - No usamos optimistic locking basado en versiones
- ❌ `increment_version()` - No manejamos versiones de agregados
- ❌ `create_snapshot()` / `load_from_snapshot()` - No usamos snapshots

Los eventos de dominio se usan para:
- ✅ Comunicación entre bounded contexts vía event bus
- ✅ Efectos secundarios (enviar emails, actualizar métricas, etc.)
- ✅ Auditoría y logging

Los eventos NO se usan para:
- ❌ Reconstruir estado de agregados (Event Sourcing)
- ❌ Persistir como fuente de verdad

**Ejemplo de Implementación**:
```python
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Sequence

@dataclass
class Article(IAggregateRoot):
    """Article aggregate root."""
    
    id: str
    source_id: str
    title: str
    url: str
    content: str
    published_at: datetime
    quality_score: Optional[float] = None
    status: ArticleStatus = ArticleStatus.DRAFT
    
    # Eventos de dominio
    _domain_events: List[IDomainEvent] = field(default_factory=list)
    _uncommitted_events: List[IDomainEvent] = field(default_factory=list)
    
    @property
    def domain_events(self) -> Sequence[IDomainEvent]:
        """Lista inmutable de eventos."""
        return tuple(self._domain_events)
    
    def get_uncommitted_events(self) -> Sequence[IDomainEvent]:
        """Eventos pendientes de publicar."""
        return tuple(self._uncommitted_events)
    
    def mark_events_as_committed(self) -> None:
        """Limpia eventos después de publicación."""
        self._uncommitted_events.clear()
    
    def publish(self) -> None:
        """Publish the article."""
        # Validaciones (invariantes)
        if self.quality_score is None:
            raise InvalidOperationException("Cannot publish without quality score")
        
        if self.quality_score < 0.5:
            raise InvalidOperationException("Quality score too low")
        
        # Cambio de estado
        self.status = ArticleStatus.PUBLISHED
        
        # Generar evento
        event = ArticlePublished(article_id=self.id, quality_score=self.quality_score)
        self._domain_events.append(event)
        self._uncommitted_events.append(event)
    
    def archive(self) -> None:
        """Archive the article."""
        self.status = ArticleStatus.ARCHIVED
        
        event = ArticleArchived(article_id=self.id)
        self._domain_events.append(event)
        self._uncommitted_events.append(event)
```

**Flujo de Eventos**:

1. **Agregado genera evento**: `article.publish()` agrega evento a `_uncommitted_events`
2. **Repositorio persiste**: `await repository.save(article)` guarda el agregado
3. **Repositorio obtiene eventos**: `events = article.get_uncommitted_events()`
4. **Event bus publica**: `await event_bus.publish(events)`
5. **Agregado marca como confirmados**: `article.mark_events_as_committed()`
6. **Event handlers reaccionan**: Efectos secundarios se ejecutan de forma asíncrona

### 2. Entities (Entidades)

Objetos con identidad única que persiste en el tiempo.

**Ubicación**: `src/domain/entities/`

**Ejemplo**:
```python
@dataclass
class FetchRecord:
    """Entity representing a single fetch operation."""
    
    id: str
    session_id: str
    source_id: str
    fetched_at: datetime
    articles_count: int
    status: FetchStatus
    error_message: Optional[str] = None
```

### 3. Value Objects (Objetos de Valor)

Objetos inmutables sin identidad, definidos por sus atributos.

**Ubicación**: `src/domain/value_objects/`

**Características**:
- Inmutables
- Igualdad por valor, no por identidad
- Sin efectos secundarios
- Pueden contener lógica de validación

**Ejemplo**:
```python
from dataclasses import dataclass

@dataclass(frozen=True)
class ContentQuality:
    """Value object representing content quality metrics."""
    
    score: float
    readability: float
    uniqueness: float
    
    def __post_init__(self):
        if not 0 <= self.score <= 1:
            raise ValueError("Score must be between 0 and 1")
        if not 0 <= self.readability <= 1:
            raise ValueError("Readability must be between 0 and 1")
        if not 0 <= self.uniqueness <= 1:
            raise ValueError("Uniqueness must be between 0 and 1")
    
    @property
    def is_high_quality(self) -> bool:
        return self.score >= 0.7

@dataclass(frozen=True)
class RssUrl:
    """Value object for RSS URL."""
    
    value: str
    
    def __post_init__(self):
        if not self.value.startswith(('http://', 'https://')):
            raise ValueError("URL must start with http:// or https://")
        if not self._is_valid_rss_url(self.value):
            raise ValueError("Invalid RSS URL format")
    
    def _is_valid_rss_url(self, url: str) -> bool:
        # Validation logic
        return True
```

### 4. Domain Events (Eventos de Dominio)

Representan algo que ha ocurrido en el dominio.

**Ubicación**: `src/domain/events/`

**Características**:
- Inmutables
- Nombrados en pasado
- Contienen datos relevantes del evento
- Timestamp incluido

**Ejemplo**:
```python
from dataclasses import dataclass
from datetime import datetime

@dataclass(frozen=True)
class DomainEvent:
    """Base class for domain events."""
    occurred_at: datetime = field(default_factory=datetime.utcnow)

@dataclass(frozen=True)
class ArticleCreated(DomainEvent):
    """Event raised when an article is created."""
    article_id: str
    source_id: str
    title: str

@dataclass(frozen=True)
class ArticlePublished(DomainEvent):
    """Event raised when an article is published."""
    article_id: str
    quality_score: float

@dataclass(frozen=True)
class SourceHealthDegraded(DomainEvent):
    """Event raised when source health degrades."""
    source_id: str
    error_rate: float
    consecutive_failures: int
```

### 5. Domain Services (Servicios de Dominio)

Lógica de dominio que no pertenece naturalmente a un agregado o entidad.

**Ubicación**: `src/domain/services/`

**Cuándo usar**:
- Operaciones que involucran múltiples agregados
- Lógica de negocio sin estado
- Cálculos complejos del dominio

**Ejemplo**:
```python
class ArticleDeduplicationService:
    """Service for detecting duplicate articles."""
    
    def __init__(self, similarity_threshold: float = 0.85):
        self.similarity_threshold = similarity_threshold
    
    def is_duplicate(
        self,
        article: Article,
        existing_articles: list[Article]
    ) -> bool:
        """Check if article is a duplicate of existing articles."""
        for existing in existing_articles:
            similarity = self._calculate_similarity(article, existing)
            if similarity >= self.similarity_threshold:
                return True
        return False
    
    def _calculate_similarity(
        self,
        article1: Article,
        article2: Article
    ) -> float:
        # Similarity calculation logic
        pass

class ArticleQualityService:
    """Service for assessing article quality."""
    
    def calculate_quality(self, article: Article) -> ContentQuality:
        """Calculate quality metrics for an article."""
        readability = self._calculate_readability(article.content)
        uniqueness = self._calculate_uniqueness(article.content)
        score = (readability + uniqueness) / 2
        
        return ContentQuality(
            score=score,
            readability=readability,
            uniqueness=uniqueness
        )
```

### 6. Factories (Fábricas)

Encapsulan la lógica compleja de creación de agregados, separando la responsabilidad de creación de la lógica de negocio.

**Ubicación**: `src/domain/factories/`

**Principio Fundamental**: Un aggregate NO debe crearse a sí mismo cuando la creación es compleja. La validación, limpieza y normalización son responsabilidades de una Factory.

#### Cuándo Usar Factories

✅ **Usar Factory cuando**:
- La creación requiere validación compleja de múltiples campos
- Se necesita limpieza o normalización de datos
- La creación involucra múltiples pasos o transformaciones
- Se crean aggregates desde diferentes fuentes (RSS, API, CSV, etc.)
- Se necesita aplicar lógica de negocio durante la creación
- La creación puede fallar y necesita manejo de errores detallado

❌ **NO usar Factory cuando**:
- La creación es trivial (solo asignar valores)
- Los Value Objects ya manejan toda la validación
- No hay transformación de datos
- El aggregate se reconstruye desde persistencia (usar Repository)

#### ArticleFactory - Ejemplo Completo

**Responsabilidades**:
- ✅ Validar datos de entrada antes de crear el aggregate
- ✅ Limpiar y normalizar datos (títulos, URLs, contenido)
- ✅ Crear Value Objects validados
- ✅ Instanciar Article usando constructor simple
- ✅ Emitir evento ArticleCreated
- ✅ Aplicar metadatos RSS opcionales
- ✅ Evaluar calidad básica del contenido

**Implementación**:

```python
from typing import Optional
from datetime import datetime
from src.domain.aggregates.article import Article
from src.domain.value_objects.article import (
    ArticleId, ArticleTitle, ArticleUrl, ArticleContent,
    ArticleThumbnailUrl, SourceId
)
from src.domain.events.article import ArticleCreated

class ArticleFactory:
    """Factory para crear Article aggregates con validaciones."""
    
    def create_article(
        self,
        title: str,
        url: str,
        source_id: SourceId,
        content: Optional[str] = None,
        article_id: Optional[ArticleId] = None,
        thumbnail_url: Optional[str] = None,
        guid: Optional[str] = None,
        published_at: Optional[datetime] = None,
        description: Optional[str] = None,
        **metadata,
    ) -> Article:
        """
        Crea Article con validaciones y limpieza.
        
        Args:
            title: Título del artículo (será limpiado)
            url: URL del artículo (será normalizada)
            source_id: ID de la fuente RSS
            content: Contenido completo (opcional)
            article_id: ID personalizado (opcional, se genera si no se provee)
            thumbnail_url: URL de imagen (opcional)
            guid: GUID del feed RSS (opcional)
            published_at: Fecha de publicación (opcional)
            description: Descripción corta (opcional)
            **metadata: Metadatos adicionales
            
        Returns:
            Article aggregate validado y listo para persistir
            
        Raises:
            ValueError: Si los datos son inválidos
            
        Example:
            >>> factory = ArticleFactory()
            >>> article = factory.create_article(
            ...     title="Python Best Practices",
            ...     url="https://example.com/article",
            ...     source_id=SourceId("src-123"),
            ...     content="Full content here..."
            ... )
        """
        # 1. Validar datos de entrada
        validation_errors = self._validate_input(title, url, content)
        if validation_errors:
            raise ValueError(f"Validación fallida: {', '.join(validation_errors)}")
        
        # 2. Limpiar y normalizar datos
        clean_title = self._clean_title(title)
        normalized_url = self._normalize_url(url)
        clean_content = self._clean_content(content) if content else None
        
        # 3. Crear Value Objects
        article_id_vo = article_id or ArticleId.generate()
        title_vo = ArticleTitle(clean_title)
        url_vo = ArticleUrl(normalized_url)
        content_vo = ArticleContent.create(clean_content) if clean_content else None
        thumbnail_vo = ArticleThumbnailUrl(thumbnail_url) if thumbnail_url else None
        
        # 4. Instanciar Article (constructor simple)
        article = Article(
            id=article_id_vo,
            title=title_vo,
            url=url_vo,
            source_id=source_id,
            content=content_vo,
            thumbnail_url=thumbnail_vo,
        )
        
        # 5. Emitir evento ArticleCreated
        event = ArticleCreated(
            article_id=str(article_id_vo),
            source_id=str(source_id),
            title=clean_title,
            url=normalized_url,
            occurred_at=datetime.utcnow()
        )
        article._add_domain_event(event)
        
        # 6. Aplicar metadatos RSS si existen
        if guid:
            article.set_rss_guid(guid)
        if published_at:
            article.set_pub_date(published_at)
        if description:
            article.set_description(description)
        
        return article
    
    def create_from_feed_item(
        self,
        feed_item: FeedItem,
        source_id: SourceId,
        quality_assessment: bool = True,
    ) -> Article:
        """
        Crea Article desde RSS feed item.
        
        Args:
            feed_item: Item del feed RSS
            source_id: ID de la fuente
            quality_assessment: Si evaluar calidad automáticamente
            
        Returns:
            Article creado desde feed
        """
        # Usar description como fallback para content
        content = feed_item.content or feed_item.description
        
        article = self.create_article(
            title=feed_item.title,
            url=feed_item.link,
            source_id=source_id,
            content=content,
            guid=feed_item.guid,
            published_at=feed_item.pub_date,
            description=feed_item.description,
            author=feed_item.author,
            categories=feed_item.categories,
        )
        
        # Evaluar calidad si se solicita
        if quality_assessment and content:
            quality = self._assess_basic_quality(content)
            article.set_quality_level(quality)
        
        return article
    
    # Métodos privados de validación y limpieza
    
    def _validate_input(
        self, 
        title: str, 
        url: str, 
        content: Optional[str]
    ) -> list[str]:
        """Valida datos de entrada y retorna lista de errores."""
        errors = []
        
        if not title or len(title.strip()) == 0:
            errors.append("Título es requerido")
        elif len(title) > 500:
            errors.append("Título debe tener máximo 500 caracteres")
        
        if not url or not url.startswith(('http://', 'https://')):
            errors.append("URL debe incluir protocolo válido (http/https)")
        
        return errors
    
    def _clean_title(self, title: str) -> str:
        """Limpia título removiendo prefijos RSS y espacios extra."""
        # Remover prefijos comunes de RSS
        prefixes = ["RSS:", "[FEED]", "[RSS]", "RSS -", "Feed:"]
        clean = title.strip()
        
        for prefix in prefixes:
            if clean.startswith(prefix):
                clean = clean[len(prefix):].strip()
        
        # Remover sufijos
        suffixes = [" - RSS", " | RSS Feed", " - Feed"]
        for suffix in suffixes:
            if clean.endswith(suffix):
                clean = clean[:-len(suffix)].strip()
        
        return clean
    
    def _normalize_url(self, url: str) -> str:
        """Normaliza URL a formato estándar."""
        # Convertir a lowercase (dominio)
        parts = url.split('/', 3)
        if len(parts) >= 3:
            parts[2] = parts[2].lower()  # Dominio a lowercase
        
        normalized = '/'.join(parts)
        
        # Remover fragment (#)
        if '#' in normalized:
            normalized = normalized.split('#')[0]
        
        return normalized
    
    def _clean_content(self, content: str) -> str:
        """Limpia contenido removiendo espacios extra."""
        # Remover espacios múltiples
        import re
        clean = re.sub(r'\s+', ' ', content)
        
        # Preservar párrafos
        clean = re.sub(r'\n\s*\n', '\n\n', clean)
        
        return clean.strip()
    
    def _assess_basic_quality(self, content: str) -> ArticleQualityLevel:
        """Evalúa calidad básica basada en longitud."""
        word_count = len(content.split())
        
        if word_count < 100:
            return ArticleQualityLevel.LOW
        elif word_count < 500:
            return ArticleQualityLevel.MEDIUM
        else:
            return ArticleQualityLevel.HIGH
```

#### Uso en Command Handlers

```python
from src.domain.factories.article_factory import ArticleFactory

class CreateArticleHandler:
    """Handler para crear nuevos Articles."""
    
    def __init__(
        self,
        article_factory: ArticleFactory,  # ← Inyectar Factory
        article_repository: IArticleWriteRepository,
        event_bus: IEventBus,
    ):
        self._factory = article_factory
        self._repository = article_repository
        self._event_bus = event_bus
    
    async def handle(self, command: CreateArticleCommand) -> CreateArticleResult:
        """Crea Article usando Factory."""
        
        # 1. Usar Factory para crear (valida, limpia, crea)
        try:
            article = self._factory.create_article(
                title=command.title,
                url=command.url,
                source_id=command.source_id,
                content=command.content,
            )
        except ValueError as e:
            return CreateArticleResult.failure(str(e))
        
        # 2. Persistir aggregate
        await self._repository.save(article)
        
        # 3. Publicar eventos
        events = article.get_uncommitted_events()
        await self._event_bus.publish_all(events)
        
        # 4. Marcar eventos como committed
        article.mark_events_as_committed()
        
        return CreateArticleResult.success(article)
```

#### Constructor Simple del Aggregate

El constructor de `Article` debe ser simple y solo aceptar Value Objects:

```python
@dataclass
class Article(IAggregateRoot):
    """Article aggregate root."""
    
    def __init__(
        self,
        title: ArticleTitle,      # ← Value Object, no string
        url: ArticleUrl,          # ← Value Object, no string
        source_id: SourceId,      # ← Value Object, no string
        article_id: Optional[ArticleId] = None,
        content: Optional[ArticleContent] = None,
        thumbnail_url: Optional[ArticleThumbnailUrl] = None,
    ):
        """
        Constructor simple - solo inicializa estado.
        
        NO valida (VOs ya validaron).
        NO limpia datos (Factory ya limpió).
        NO emite eventos (Factory emite).
        
        Args:
            title: ArticleTitle Value Object
            url: ArticleUrl Value Object
            source_id: SourceId Value Object
            article_id: ArticleId opcional
            content: ArticleContent opcional
            thumbnail_url: ArticleThumbnailUrl opcional
        """
        self._id = article_id or ArticleId.generate()
        self._title = title
        self._url = url
        self._source_id = source_id
        self._content = content
        self._thumbnail_url = thumbnail_url
        
        # Estado interno
        self._domain_events: List[IDomainEvent] = []
        self._uncommitted_events: List[IDomainEvent] = []
```

#### Anti-Patrones a Evitar

❌ **Anti-Patrón 1: Factory Method Estático en Aggregate**

```python
# ❌ INCORRECTO - No mezclar creación con lógica de negocio
class Article:
    @classmethod
    def create(cls, title: str, url: str, source_id: str) -> "Article":
        # Validación
        if not title:
            raise ValueError("Title required")
        
        # Limpieza
        clean_title = title.strip()
        
        # Creación
        article = cls(title=clean_title, url=url, source_id=source_id)
        
        # Evento
        article._events.append(ArticleCreated(...))
        
        return article
    
    def publish(self) -> None:
        # Lógica de negocio
        pass
```

**Problema**: El aggregate tiene dos responsabilidades (creación + negocio). Viola Single Responsibility Principle.

✅ **Correcto**: Usar Factory separada

```python
# ✅ CORRECTO - Factory maneja creación
class ArticleFactory:
    def create_article(self, title: str, url: str, source_id: SourceId) -> Article:
        # Validación, limpieza, creación, eventos
        pass

# ✅ CORRECTO - Aggregate solo maneja negocio
class Article:
    def publish(self) -> None:
        # Solo lógica de negocio
        pass
```

❌ **Anti-Patrón 2: Constructor Complejo con Validación**

```python
# ❌ INCORRECTO - Constructor hace demasiado
class Article:
    def __init__(self, title: str, url: str, source_id: str):
        # Validación en constructor
        if not title or len(title) > 500:
            raise ValueError("Invalid title")
        
        # Limpieza en constructor
        self._title = title.strip().replace("RSS:", "")
        
        # Normalización en constructor
        self._url = url.lower()
        
        # Eventos en constructor
        self._events.append(ArticleCreated(...))
```

**Problema**: Constructor complejo, difícil de testear, mezcla responsabilidades.

✅ **Correcto**: Constructor simple, Factory maneja complejidad

```python
# ✅ CORRECTO - Constructor simple
class Article:
    def __init__(
        self, 
        title: ArticleTitle,  # Ya validado
        url: ArticleUrl,      # Ya validado
        source_id: SourceId   # Ya validado
    ):
        self._title = title
        self._url = url
        self._source_id = source_id
        # NO valida, NO limpia, NO emite eventos
```

❌ **Anti-Patrón 3: Múltiples Formas de Crear sin Factory**

```python
# ❌ INCORRECTO - Creación dispersa
class Article:
    @classmethod
    def create(cls, title: str, url: str) -> "Article":
        pass
    
    @classmethod
    def from_rss(cls, entry: dict) -> "Article":
        pass
    
    @classmethod
    def from_api(cls, data: dict) -> "Article":
        pass
```

**Problema**: Aggregate sobrecargado con métodos de creación.

✅ **Correcto**: Factory centraliza todas las formas de creación

```python
# ✅ CORRECTO - Factory centraliza creación
class ArticleFactory:
    def create_article(self, title: str, url: str, source_id: SourceId) -> Article:
        pass
    
    def create_from_feed_item(self, feed_item: FeedItem, source_id: SourceId) -> Article:
        pass
    
    def create_from_api_response(self, response: dict, source_id: SourceId) -> Article:
        pass
```

#### Beneficios del Patrón Factory

✅ **Separación de Responsabilidades**: Factory crea, Aggregate maneja negocio
✅ **Validaciones Centralizadas**: Un solo lugar para validar datos
✅ **Limpieza Automática**: Datos siempre limpios y normalizados
✅ **Fácil de Testear**: Factory y Aggregate se testean independientemente
✅ **Fácil de Extender**: Agregar nuevas formas de creación sin modificar Aggregate
✅ **Código Mantenible**: Cambios en creación no afectan lógica de negocio

#### Resumen

- 🎯 Usa Factories para creación compleja de aggregates
- 🔒 Mantén constructores de aggregates simples
- 🧹 Centraliza validación y limpieza en Factory
- 📝 Separa responsabilidades: Factory crea, Aggregate maneja negocio
- ✨ Evita factory methods estáticos en aggregates

### 7. Repositories (Interfaces)

Interfaces para persistencia, definidas en el dominio.

**Ubicación**: `src/domain/interfaces/repositories/`

**Características**:
- Solo interfaces (Protocol)
- Operaciones en términos del dominio
- Implementación en infrastructure layer

**Ejemplo**:
```python
from typing import Protocol, Optional

class IArticleRepository(Protocol):
    """Repository interface for Article aggregate."""
    
    async def save(self, article: Article) -> None:
        """Save an article."""
        ...
    
    async def find_by_id(self, article_id: str) -> Optional[Article]:
        """Find article by ID."""
        ...
    
    async def find_by_url(self, url: str) -> Optional[Article]:
        """Find article by URL."""
        ...
    
    async def find_duplicates(
        self,
        article: Article,
        threshold: float
    ) -> list[Article]:
        """Find potential duplicate articles."""
        ...
    
    async def delete(self, article_id: str) -> None:
        """Delete an article."""
        ...
```

## Invariantes de Dominio

Los invariantes son reglas que siempre deben ser verdaderas.

**Ejemplo**:
```python
class Article:
    def publish(self) -> None:
        # Invariante: Solo artículos con calidad suficiente pueden publicarse
        if self.quality_score is None or self.quality_score < 0.5:
            raise InvalidOperationException(
                "Cannot publish article with insufficient quality"
            )
        
        # Invariante: Solo artículos en estado DRAFT pueden publicarse
        if self.status != ArticleStatus.DRAFT:
            raise InvalidOperationException(
                f"Cannot publish article in {self.status} status"
            )
        
        self.status = ArticleStatus.PUBLISHED
        self._events.append(ArticlePublished(article_id=self.id))
```

## Ubiquitous Language

Usar el mismo lenguaje en código, documentación y conversaciones:

- **Article**: Artículo scrapeado
- **Source**: Fuente RSS
- **Fetch**: Operación de scraping
- **Quality Score**: Puntuación de calidad
- **Publish**: Publicar un artículo
- **Archive**: Archivar un artículo
- **Deduplication**: Detección de duplicados
- **Health**: Salud de una fuente (tasa de éxito)

## Bounded Contexts

El proyecto tiene estos contextos delimitados:

1. **Article Management**: Gestión de artículos
2. **Source Management**: Gestión de fuentes RSS
3. **Fetching**: Operaciones de scraping
4. **Content Analysis**: Análisis de contenido

Cada contexto puede tener su propio modelo de dominio.
