# Design Document

## Overview

El bounded context de AI/Content Processing es responsable de transformar artículos scrapeados en contenido estructurado, semánticamente indexado y listo para generación mediante RAG. Este bounded context implementa un pipeline completo que incluye chunking inteligente, generación de embeddings vectoriales, summarización jerárquica, almacenamiento vectorial, búsqueda semántica, clustering y generación de contenido nuevo.

### Arquitectura de Aggregates

Este bounded context define **3 Aggregate Roots** siguiendo DDD estricto:

1. **ContentChunk** (Aggregate Root)
   - Representa un segmento procesado de texto con su embedding y summary
   - Tiene su propio ciclo de vida independiente
   - Permite búsqueda vectorial eficiente sin cargar artículos completos
   - Repository: `ContentChunkRepository`

2. **SemanticCluster** (Aggregate Root)
   - Agrupa artículos similares basándose en embeddings semánticos
   - Mantiene centroid y términos frecuentes del cluster
   - Repository: `SemanticClusterRepository`

3. **ContextPack** (Aggregate Root)
   - Ensambla contexto para generación RAG
   - Coordina chunks relevantes para un query específico
   - Efímero, puede ser recreado en cualquier momento
   - Repository: `ContextPackRepository` (opcional)

**Nota Importante**: NO existe un aggregate `ProcessedArticle` para evitar duplicar el aggregate `Article` del Article BC. El estado de procesamiento se maneja mediante:
- **Read Model**: `ArticleProcessingStatus` (actualizado por eventos)
- **Eventos de dominio**: `ChunkCreatedEvent`, `ChunkEmbeddedEvent`, `ArticleAIProcessedEvent`, etc.
- **Queries**: Conteo de chunks por `article_id`

### Bounded Context Justification

Este es un bounded context separado porque:
- **Responsabilidad única**: Procesamiento de contenido con AI/ML
- **Tecnologías específicas**: LLMs, embeddings, vector search
- **Independencia**: Puede evolucionar sin afectar scraping o article management
- **Escalabilidad**: Puede escalar independientemente (GPU, batching)
- **Lenguaje ubicuo**: Términos específicos de ML/AI (embeddings, chunks, RAG)

### Relación con otros Bounded Contexts

- **Article BC**: Consume artículos scrapeados (referencia externa vía `article_id`), emite eventos de procesamiento
- **Scraping BC**: Recibe eventos cuando nuevos artículos están disponibles
- **Content Generation BC** (futuro): Provee capacidades de RAG

## Architecture

### High-Level Architecture


```
┌─────────────────────────────────────────────────────────────────┐
│                     AI Content Processing BC                     │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │              Application Layer                             │ │
│  │                                                            │ │
│  │  Commands:                    Queries:                    │ │
│  │  - ProcessArticleContent      - SearchSimilarChunks       │ │
│  │  - GenerateContentWithRAG     - GetArticleClusters        │ │
│  │  - DetectDuplicateArticle     - GetProcessingStatus       │ │
│  │                                                            │ │
│  │  Event Handlers:                                          │ │
│  │  - OnArticleScraped → ProcessArticleContent               │ │
│  │  - OnArticleUpdated → ReprocessArticleContent             │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │              Domain Layer                                  │ │
│  │                                                            │ │
│  │  Aggregates:                  Value Objects:              │ │
│  │  - ContentChunk               - VectorEmbedding           │ │
│  │  - ContextPack                - ChunkSummary              │ │
│  │  - SemanticCluster            - TLDR                      │ │
│  │                               - TokenCount                │ │
│  │                               - ChunkMetadata             │ │
│  │  Domain Services:                                         │ │
│  │  - TextCleaningService                                    │ │
│  │  - ChunkingService                                        │ │
│  │  - SummarizationService                                   │ │
│  │  - ClusteringService                                      │ │
│  │  - RAGContextAssemblyService                              │ │
│  │                                                            │ │
│  │  Interfaces (External):                                   │ │
│  │  - IEmbeddingService                                      │ │
│  │  - ILLMService                                            │ │
│  │  - IVectorStore                                           │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │              Infrastructure Layer                          │ │
│  │                                                            │ │
│  │  Adapters:                                                │ │
│  │  - NomicEmbeddingAdapter (IEmbeddingService)              │ │
│  │  - OpenAILLMAdapter (ILLMService)                         │ │
│  │  - PgVectorStoreAdapter (IVectorStore)                    │ │
│  │                                                            │ │
│  │  Repositories:                                            │ │
│  │  - ContentChunkRepository                                 │ │
│  │  - SemanticClusterRepository                              │ │
│  │  - ContextPackRepository (optional)                       │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### Processing Pipeline Flow

```
Article BC                          AI Content Processing BC
─────────────────────────────────────────────────────────────
Article (Aggregate)                 
  ↓ emite                           
ArticleQualityCalculated            
  ↓                                 
  ├─────────────────────────────────→ ProcessArticleContentCommand
                                      ↓
                                    ProcessArticleContentHandler
                                      ↓
                                    ┌─────────────────────────────────┐
                                    │ 1. Chunking (ChunkingService)   │
                                    │    - Split text (1200-1500 tok) │
                                    │    - Overlap: 150 tokens        │
                                    │    Output: chunk data           │
                                    └─────────────────────────────────┘
                                      ↓
                                    ┌─────────────────────────────────┐
                                    │ 2. Create ContentChunk          │
                                    │    Aggregates (PENDING)         │
                                    │    - ContentChunkRepository     │
                                    │    - Emite: ChunkCreatedEvent   │
                                    └─────────────────────────────────┘
                                      ↓
                                    ┌─────────────────────────────────┐
                                    │ 3. Generate Embeddings          │
                                    │    (IEmbeddingService)          │
                                    │    - Batch processing (32)      │
                                    │    - nomic-embed-text (768)     │
                                    └─────────────────────────────────┘
                                      ↓
                                    ┌─────────────────────────────────┐
                                    │ 4. Update Chunks with Embedding │
                                    │    - chunk.embed(embedding)     │
                                    │    - Status: EMBEDDED           │
                                    │    - Emite: ChunkEmbeddedEvent  │
                                    └─────────────────────────────────┘
                                      ↓
                                    ┌─────────────────────────────────┐
                                    │ 5. Generate Summaries           │
                                    │    (SummarizationService)       │
                                    │    - Chunk summaries (3-5 sent) │
                                    │    - Global summary             │
                                    │    - TLDR (3-5 bullets)         │
                                    └─────────────────────────────────┘
                                      ↓
                                    ┌─────────────────────────────────┐
                                    │ 6. Update Chunks with Summary   │
                                    │    - chunk.summarize(summary)   │
                                    │    - Status: SUMMARIZED         │
                                    │    - Emite: ChunkSummarizedEvent│
                                    └─────────────────────────────────┘
                                      ↓
                                    ┌─────────────────────────────────┐
                                    │ 7. Mark Chunks as Completed     │
                                    │    - chunk.mark_as_completed()  │
                                    │    - Status: COMPLETED          │
                                    │    - Emite: ChunkCompletedEvent │
                                    └─────────────────────────────────┘
                                      ↓
                                    ┌─────────────────────────────────┐
                                    │ 8. Update Read Model            │
                                    │    (ArticleProcessingStatus)    │
                                    │    - Via Event Handlers         │
                                    │    - Actualiza contadores       │
                                    │    - Guarda global summary/TLDR │
                                    └─────────────────────────────────┘
                                      ↓ emite
                                    ArticleAIProcessedEvent
  ←─────────────────────────────────┘
  ↓ (opcional)
Article.add_tag("ai-processed")
```



### RAG Generation Flow

```
User Request: "Generate content about Bitcoin ETFs"
    ↓
GenerateContentWithRAGCommand
    ↓
GenerateContentWithRAGHandler
    ↓
┌─────────────────────────────────────────────────────────────┐
│ 1. Query Embedding (IEmbeddingService)                      │
│    - Generate embedding for query                           │
│    - Model: nomic-embed-text                                │
│    Output: query_vector                                     │
└─────────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────────┐
│ 2. Semantic Search (IVectorStore)                           │
│    - Search similar chunks (cosine distance)                │
│    - Apply filters (date, source, topics)                   │
│    - Retrieve top-k chunks (k=10-20)                        │
│    Output: List[ContentChunk with metadata]                 │
└─────────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────────┐
│ 3. Context Assembly (RAGContextAssemblyService)             │
│    - Order chunks by relevance + date                       │
│    - Include chunk summaries + TLDRs                        │
│    - Limit total tokens to budget                           │
│    - Format for LLM prompt                                  │
│    Output: ContextPack                                      │
└─────────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────────┐
│ 4. Content Generation (ILLMService)                         │
│    - Use RAG prompt template                                │
│    - Include context pack                                   │
│    - Generate structured content                            │
│    - Cite sources                                           │
│    Output: GeneratedContent with citations                  │
└─────────────────────────────────────────────────────────────┘
    ↓
ContentGeneratedEvent
```

## Components and Interfaces

### Domain Layer

#### Aggregates

**1. ContentChunk**

```python
@dataclass
class ContentChunk(IAggregateRoot):
    """
    Aggregate root para chunk de contenido procesado.
    
    Cada chunk es independiente y puede ser consultado/actualizado
    sin cargar el artículo completo. Esto permite búsqueda vectorial
    eficiente y procesamiento paralelo.
    """
    
    id: ChunkId
    article_id: str  # Referencia externa al Article BC
    
    # Contenido
    content: str
    embedding: Optional[VectorEmbedding]
    summary: Optional[ChunkSummary]
    
    # Posición en el artículo original
    position: int  # 0-indexed
    start_char: int
    end_char: int
    
    # Metadata
    token_count: TokenCount
    source_url: str
    
    # Estado del procesamiento
    status: ChunkStatus  # PENDING, EMBEDDED, SUMMARIZED, COMPLETED
    
    # Timestamps
    created_at: datetime
    updated_at: datetime
    
    # Eventos
    _domain_events: List[IDomainEvent]
    _uncommitted_events: List[IDomainEvent]
    
    def embed(self, embedding: VectorEmbedding) -> None:
        """
        Agrega embedding al chunk.
        
        Invariantes:
        - Embedding debe ser válido (768 dims, normalizado)
        - Solo se puede embedear una vez
        """
        if self.embedding is not None:
            raise ValueError("Chunk already has embedding")
        
        if embedding.dimension != 768:
            raise ValueError("Embedding must be 768 dimensions")
        
        self.embedding = embedding
        self.status = ChunkStatus.EMBEDDED
        self.updated_at = datetime.now(timezone.utc)
        
        self._add_domain_event(ChunkEmbeddedEvent(
            chunk_id=str(self.id),
            article_id=self.article_id,
        ))
    
    def summarize(self, summary: ChunkSummary) -> None:
        """
        Agrega summary al chunk.
        
        Invariantes:
        - Summary debe ser válido (3-5 frases)
        - Debe tener embedding primero
        """
        if self.embedding is None:
            raise ValueError("Chunk must be embedded before summarizing")
        
        if not (3 <= summary.sentence_count <= 5):
            raise ValueError("Summary must have 3-5 sentences")
        
        self.summary = summary
        self.status = ChunkStatus.SUMMARIZED
        self.updated_at = datetime.now(timezone.utc)
        
        self._add_domain_event(ChunkSummarizedEvent(
            chunk_id=str(self.id),
            article_id=self.article_id,
        ))
    
    def mark_as_completed(self) -> None:
        """
        Marca chunk como completamente procesado.
        
        Invariantes:
        - Debe tener embedding y summary
        """
        if self.embedding is None or self.summary is None:
            raise ValueError("Chunk must have embedding and summary to complete")
        
        self.status = ChunkStatus.COMPLETED
        self.updated_at = datetime.now(timezone.utc)
        
        self._add_domain_event(ChunkCompletedEvent(
            chunk_id=str(self.id),
            article_id=self.article_id,
        ))
```

**2. ContextPack**

```python
@dataclass
class ContextPack(IAggregateRoot):
    """
    Aggregate root para context pack de RAG.
    
    Representa un conjunto de chunks y summaries recuperados
    para generación de contenido. Es efímero y puede ser
    recreado en cualquier momento.
    """
    
    id: ContextPackId
    query: str
    query_embedding: VectorEmbedding
    
    # Referencias a chunks (NO los chunks completos)
    chunk_ids: List[ChunkId]
    
    # Metadata
    total_tokens: int
    relevance_scores: List[float]
    sources: List[str]  # URLs de artículos originales
    
    # Configuración
    max_tokens: int
    created_at: datetime
    
    # Eventos
    _domain_events: List[IDomainEvent]
    _uncommitted_events: List[IDomainEvent]
    
    def add_chunk(
        self, 
        chunk_id: ChunkId,
        token_count: int,
        relevance_score: float,
        source_url: str,
    ) -> None:
        """
        Agrega chunk al context pack.
        
        Invariantes:
        - No exceder max_tokens
        - Relevance scores ordenados descendentemente
        """
        if self.total_tokens + token_count > self.max_tokens:
            raise ContextPackFullException(
                f"Cannot add chunk: would exceed max_tokens ({self.max_tokens})"
            )
        
        # Invariante: Mantener orden por relevancia
        if self.relevance_scores and relevance_score > self.relevance_scores[-1]:
            raise ValueError("Chunks must be added in descending relevance order")
        
        self.chunk_ids.append(chunk_id)
        self.relevance_scores.append(relevance_score)
        self.total_tokens += token_count
        
        if source_url not in self.sources:
            self.sources.append(source_url)
    
    def is_full(self) -> bool:
        """Verifica si el context pack está lleno."""
        return self.total_tokens >= self.max_tokens
```

**3. SemanticCluster**

```python
@dataclass
class SemanticCluster(IAggregateRoot):
    """
    Aggregate root para cluster semántico de artículos.
    
    Representa un grupo de artículos similares basado en
    embeddings semánticos.
    """
    
    id: ClusterId
    label: str  # Descriptive label (e.g., "Bitcoin ETF Regulation")
    
    # Referencias a artículos (externos al BC)
    article_ids: List[str]
    
    # Centroid del cluster
    centroid: VectorEmbedding
    
    # Metadata
    size: int
    top_terms: List[Tuple[str, float]]  # (term, frequency)
    
    # Timestamps
    created_at: datetime
    updated_at: datetime
    
    # Eventos
    _domain_events: List[IDomainEvent]
    _uncommitted_events: List[IDomainEvent]
    
    def add_article(self, article_id: str) -> None:
        """
        Agrega artículo al cluster.
        
        Invariantes:
        - No duplicar article_ids
        - Mantener size sincronizado
        """
        if article_id in self.article_ids:
            raise ValueError(f"Article {article_id} already in cluster")
        
        self.article_ids.append(article_id)
        self.size += 1
        self.updated_at = datetime.now(timezone.utc)
        
        self._add_domain_event(ArticleAddedToClusterEvent(
            cluster_id=str(self.id),
            article_id=article_id,
        ))
    
    def remove_article(self, article_id: str) -> None:
        """
        Remueve artículo del cluster.
        
        Invariantes:
        - Artículo debe existir en el cluster
        - Mantener size sincronizado
        """
        if article_id not in self.article_ids:
            raise ValueError(f"Article {article_id} not in cluster")
        
        self.article_ids.remove(article_id)
        self.size -= 1
        self.updated_at = datetime.now(timezone.utc)
        
        self._add_domain_event(ArticleRemovedFromClusterEvent(
            cluster_id=str(self.id),
            article_id=article_id,
        ))
    
    def update_centroid(self, new_centroid: VectorEmbedding) -> None:
        """
        Actualiza centroid del cluster.
        
        Invariantes:
        - Centroid debe ser válido (768 dims, normalizado)
        """
        if new_centroid.dimension != 768:
            raise ValueError("Centroid must be 768 dimensions")
        
        self.centroid = new_centroid
        self.updated_at = datetime.now(timezone.utc)
    
    def update_label(self, label: str, top_terms: List[Tuple[str, float]]) -> None:
        """
        Actualiza label y términos del cluster.
        
        Invariantes:
        - Label no puede estar vacío
        - Top terms deben tener frecuencia > 0
        """
        if not label or not label.strip():
            raise ValueError("Label cannot be empty")
        
        for term, freq in top_terms:
            if freq <= 0:
                raise ValueError(f"Term frequency must be > 0, got {freq}")
        
        self.label = label.strip()
        self.top_terms = top_terms
        self.updated_at = datetime.now(timezone.utc)
```

#### Value Objects

**1. VectorEmbedding**

```python
@dataclass(frozen=True)
class VectorEmbedding:
    """
    Value object para embedding vectorial.
    
    Representa un vector de embeddings normalizado.
    """
    
    vector: np.ndarray  # Shape: (768,)
    model: str  # e.g., "nomic-embed-text"
    dimension: int  # 768
    
    def __post_init__(self):
        if self.vector.shape != (self.dimension,):
            raise ValueError(
                f"Invalid vector shape: {self.vector.shape}, "
                f"expected ({self.dimension},)"
            )
        
        # Verificar normalización
        magnitude = np.linalg.norm(self.vector)
        if not np.isclose(magnitude, 1.0, atol=1e-5):
            raise ValueError(
                f"Vector not normalized: magnitude={magnitude}"
            )
    
    def cosine_similarity(self, other: "VectorEmbedding") -> float:
        """Calcula similitud coseno con otro embedding."""
        return float(np.dot(self.vector, other.vector))
    
    def to_list(self) -> List[float]:
        """Convierte a lista para serialización."""
        return self.vector.tolist()
    
    @classmethod
    def from_list(cls, vector_list: List[float], model: str) -> "VectorEmbedding":
        """Crea desde lista."""
        vector = np.array(vector_list, dtype=np.float32)
        return cls(vector=vector, model=model, dimension=len(vector_list))
```

**2. ChunkSummary**

```python
@dataclass(frozen=True)
class ChunkSummary:
    """
    Value object para summary de chunk.
    
    Representa un resumen de 3-5 frases de un chunk.
    """
    
    content: str
    sentence_count: int
    
    def __post_init__(self):
        if not self.content:
            raise ValueError("Summary cannot be empty")
        
        if self.sentence_count < 3 or self.sentence_count > 5:
            raise ValueError(
                f"Summary must have 3-5 sentences, got {self.sentence_count}"
            )
```

**3. TLDR**

```python
@dataclass(frozen=True)
class TLDR:
    """
    Value object para TLDR (Too Long; Didn't Read).
    
    Representa un resumen ultra-conciso en bullets.
    """
    
    bullets: List[str]  # 3-5 bullets
    
    def __post_init__(self):
        if len(self.bullets) < 3 or len(self.bullets) > 5:
            raise ValueError(
                f"TLDR must have 3-5 bullets, got {len(self.bullets)}"
            )
        
        for bullet in self.bullets:
            if not bullet or len(bullet) < 10:
                raise ValueError("Each bullet must be at least 10 characters")
    
    @property
    def content(self) -> str:
        """Retorna TLDR formateado."""
        return "\n".join(f"- {bullet}" for bullet in self.bullets)
```

**4. TokenCount**

```python
@dataclass(frozen=True)
class TokenCount:
    """
    Value object para conteo de tokens.
    
    Usa tiktoken para conteo preciso.
    """
    
    value: int
    encoding: str  # e.g., "cl100k_base"
    
    def __post_init__(self):
        if self.value < 0:
            raise ValueError("Token count cannot be negative")
    
    @classmethod
    def from_text(cls, text: str, encoding: str = "cl100k_base") -> "TokenCount":
        """Cuenta tokens en texto usando tiktoken."""
        import tiktoken
        
        enc = tiktoken.get_encoding(encoding)
        tokens = enc.encode(text)
        
        return cls(value=len(tokens), encoding=encoding)
```

**5. ChunkMetadata**

```python
@dataclass(frozen=True)
class ChunkMetadata:
    """
    Value object para metadata de chunk.
    
    Agrupa información contextual del chunk.
    """
    
    article_id: str
    source_url: str
    published_at: Optional[datetime]
    topics: List[str]
    tokens_mentioned: List[str]
    
    def __post_init__(self):
        if not self.article_id or not self.article_id.strip():
            raise ValueError("article_id cannot be empty")
        
        if not self.source_url or not self.source_url.startswith(("http://", "https://")):
            raise ValueError("source_url must be a valid URL")
```

**6. GlobalSummary**

```python
@dataclass(frozen=True)
class GlobalSummary:
    """
    Value object para summary global de artículo.
    
    Representa un resumen del artículo completo.
    """
    
    content: str
    article_id: str
    
    def __post_init__(self):
        if not self.content or not self.content.strip():
            raise ValueError("Global summary cannot be empty")
        
        if len(self.content) < 50:
            raise ValueError("Global summary too short (min 50 characters)")
```

**7. ChunkStatus**

```python
class ChunkStatus(str, Enum):
    """
    Enum para estado de procesamiento de chunk.
    """
    PENDING = "PENDING"
    EMBEDDED = "EMBEDDED"
    SUMMARIZED = "SUMMARIZED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
```

#### Read Models (CQRS)

**ArticleProcessingStatus**

```python
@dataclass
class ArticleProcessingStatus:
    """
    Read model para estado de procesamiento de artículo.
    
    NO es aggregate. Se actualiza mediante event handlers.
    Provee vista materializada del estado de procesamiento.
    """
    
    article_id: str
    total_chunks: int
    chunks_embedded: int
    chunks_summarized: int
    chunks_completed: int
    has_global_summary: bool
    has_tldr: bool
    cluster_id: Optional[str]
    status: str  # PENDING, PROCESSING, COMPLETED, FAILED
    started_at: datetime
    completed_at: Optional[datetime]
    
    @property
    def is_completed(self) -> bool:
        """Verifica si el procesamiento está completo."""
        return (
            self.total_chunks > 0 and
            self.chunks_completed == self.total_chunks and
            self.has_global_summary and
            self.has_tldr
        )
    
    @property
    def progress_percentage(self) -> float:
        """Calcula porcentaje de progreso."""
        if self.total_chunks == 0:
            return 0.0
        return (self.chunks_completed / self.total_chunks) * 100
```

#### Domain Services

**1. ChunkingService**

```python
class ChunkingService:
    """
    Domain service para chunking inteligente de texto.
    
    Responsabilidades:
    - Dividir texto en chunks semánticamente coherentes
    - Mantener overlap entre chunks
    - Preservar contexto
    """
    
    def __init__(
        self,
        chunk_size: int = 1200,
        chunk_overlap: int = 150,
        separators: List[str] = None,
    ):
        self._chunk_size = chunk_size
        self._chunk_overlap = chunk_overlap
        self._separators = separators or ["\n\n", "\n", ". ", " ", ""]
    
    def chunk_text(
        self, 
        text: str, 
        article_id: str,
        source_url: str,
    ) -> List[ContentChunk]:
        """
        Divide texto en chunks con overlap.
        
        Args:
            text: Texto a dividir
            article_id: ID del artículo
            source_url: URL del artículo
            
        Returns:
            Lista de ContentChunk
        """
        # Usar LangChain RecursiveCharacterTextSplitter
        from langchain.text_splitter import RecursiveCharacterTextSplitter
        
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=self._chunk_size,
            chunk_overlap=self._chunk_overlap,
            separators=self._separators,
            length_function=self._count_tokens,
        )
        
        chunks_text = splitter.split_text(text)
        
        # Crear ContentChunk objects (sin embeddings aún)
        chunks = []
        current_pos = 0
        
        for i, chunk_text in enumerate(chunks_text):
            token_count = TokenCount.from_text(chunk_text)
            
            # Encontrar posición en texto original
            start_char = text.find(chunk_text, current_pos)
            end_char = start_char + len(chunk_text)
            current_pos = end_char
            
            # Crear chunk (embedding y summary se agregan después)
            chunk = ContentChunk(
                content=chunk_text,
                embedding=None,  # Se agrega después
                summary=None,  # Se agrega después
                position=i,
                start_char=start_char,
                end_char=end_char,
                token_count=token_count,
                article_id=article_id,
                source_url=source_url,
            )
            
            chunks.append(chunk)
        
        return chunks
    
    def _count_tokens(self, text: str) -> int:
        """Cuenta tokens usando tiktoken."""
        return TokenCount.from_text(text).value
```

**2. SummarizationService**

```python
class SummarizationService:
    """
    Domain service para summarización jerárquica.
    
    Responsabilidades:
    - Generar chunk summaries (3-5 frases)
    - Generar global summary (artículo completo)
    - Fusionar summaries en TLDR
    """
    
    def __init__(self, llm_service: ILLMService):
        self._llm = llm_service
    
    async def summarize_chunk(self, chunk: ContentChunk) -> ChunkSummary:
        """
        Genera summary de 3-5 frases para un chunk.
        
        Args:
            chunk: Chunk a resumir
            
        Returns:
            ChunkSummary
        """
        prompt = f"""Resume el siguiente texto en 3-5 frases claras y concisas, 
manteniendo hechos importantes, actores, números y fechas. 
No agregues información nueva.

Texto:
{chunk.content}

Resumen:"""
        
        summary_text = await self._llm.generate(
            prompt=prompt,
            max_tokens=200,
            temperature=0.3,
        )
        
        # Contar frases
        sentences = summary_text.split(". ")
        sentence_count = len([s for s in sentences if s.strip()])
        
        return ChunkSummary(
            content=summary_text,
            sentence_count=sentence_count,
        )
    
    async def generate_global_summary(
        self, 
        full_text: str,
        existing_summary: Optional[str] = None,
    ) -> str:
        """
        Genera summary global del artículo completo.
        
        Args:
            full_text: Texto completo del artículo
            existing_summary: Summary extractivo existente (opcional)
            
        Returns:
            Global summary
        """
        prompt = f"""Genera un resumen global de este artículo manteniendo 
la información crítica.

{f"Resumen extractivo existente: {existing_summary}" if existing_summary else ""}

Artículo:
{full_text[:4000]}  # Limitar para no exceder context window

Resumen global:"""
        
        return await self._llm.generate(
            prompt=prompt,
            max_tokens=300,
            temperature=0.3,
        )
    
    async def fuse_into_tldr(
        self,
        global_summary: str,
        chunk_summaries: List[ChunkSummary],
        metadata: Dict[str, Any],
    ) -> TLDR:
        """
        Fusiona summaries en TLDR de 3-5 bullets.
        
        Args:
            global_summary: Summary global
            chunk_summaries: Summaries de chunks
            metadata: Metadata del artículo (fecha, fuente, etc.)
            
        Returns:
            TLDR
        """
        chunk_summaries_text = "\n".join(
            f"- {cs.content}" for cs in chunk_summaries
        )
        
        prompt = f"""Usa los siguientes datos:

1) Summary global:
{global_summary}

2) Summaries por chunk:
{chunk_summaries_text}

3) Metadata:
- Fuente: {metadata.get('source', 'Unknown')}
- Fecha: {metadata.get('date', 'Unknown')}
- Tokens mencionados: {metadata.get('tokens', [])}

Genera un TLDR final de 3-5 bullets con:
- Qué pasó
- Impacto en el mercado cripto
- Tokens afectados
- Actores involucrados
- Riesgo regulatorio o técnico

No agregues información nueva.

TLDR:"""
        
        tldr_text = await self._llm.generate(
            prompt=prompt,
            max_tokens=250,
            temperature=0.3,
        )
        
        # Parsear bullets
        bullets = [
            line.strip("- ").strip()
            for line in tldr_text.split("\n")
            if line.strip().startswith("-")
        ]
        
        return TLDR(bullets=bullets)
```

**3. ClusteringService**

```python
class ClusteringService:
    """
    Domain service para clustering semántico.
    
    Responsabilidades:
    - Agrupar artículos similares
    - Calcular centroids
    - Asignar labels descriptivos
    """
    
    def __init__(
        self,
        algorithm: str = "kmeans",  # "kmeans" or "dbscan"
        n_clusters: int = 10,
    ):
        self._algorithm = algorithm
        self._n_clusters = n_clusters
    
    def cluster_articles(
        self,
        embeddings: List[Tuple[str, VectorEmbedding]],  # (article_id, embedding)
    ) -> List[SemanticCluster]:
        """
        Agrupa artículos en clusters semánticos.
        
        Args:
            embeddings: Lista de (article_id, embedding)
            
        Returns:
            Lista de SemanticCluster
        """
        from sklearn.cluster import KMeans, DBSCAN
        import numpy as np
        
        # Preparar matriz de embeddings
        article_ids = [aid for aid, _ in embeddings]
        vectors = np.array([emb.vector for _, emb in embeddings])
        
        # Clustering
        if self._algorithm == "kmeans":
            clusterer = KMeans(n_clusters=self._n_clusters, random_state=42)
        else:
            clusterer = DBSCAN(eps=0.3, min_samples=2, metric="cosine")
        
        labels = clusterer.fit_predict(vectors)
        
        # Crear SemanticCluster objects
        clusters = []
        unique_labels = set(labels)
        
        for label in unique_labels:
            if label == -1:  # Outliers en DBSCAN
                continue
            
            # Artículos en este cluster
            cluster_article_ids = [
                article_ids[i] for i, l in enumerate(labels) if l == label
            ]
            
            # Calcular centroid
            cluster_vectors = vectors[labels == label]
            centroid_vector = cluster_vectors.mean(axis=0)
            centroid_vector = centroid_vector / np.linalg.norm(centroid_vector)
            
            centroid = VectorEmbedding(
                vector=centroid_vector,
                model="nomic-embed-text",
                dimension=768,
            )
            
            # Crear cluster
            cluster = SemanticCluster(
                id=ClusterId.generate(),
                label=f"Cluster {label}",  # Se actualiza después con términos
                article_ids=cluster_article_ids,
                centroid=centroid,
                size=len(cluster_article_ids),
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
                top_terms=[],  # Se calcula después
            )
            
            clusters.append(cluster)
        
        return clusters
    
    def assign_cluster_labels(
        self,
        clusters: List[SemanticCluster],
        article_texts: Dict[str, str],  # article_id -> text
    ) -> None:
        """
        Asigna labels descriptivos a clusters basados en términos frecuentes.
        
        Args:
            clusters: Lista de clusters
            article_texts: Textos de artículos por ID
        """
        from sklearn.feature_extraction.text import TfidfVectorizer
        
        for cluster in clusters:
            # Obtener textos del cluster
            texts = [
                article_texts[aid]
                for aid in cluster.article_ids
                if aid in article_texts
            ]
            
            if not texts:
                continue
            
            # TF-IDF para encontrar términos importantes
            vectorizer = TfidfVectorizer(
                max_features=10,
                stop_words="english",
                ngram_range=(1, 2),
            )
            
            tfidf_matrix = vectorizer.fit_transform(texts)
            feature_names = vectorizer.get_feature_names_out()
            
            # Top términos
            scores = tfidf_matrix.sum(axis=0).A1
            top_indices = scores.argsort()[-5:][::-1]
            top_terms = [(feature_names[i], scores[i]) for i in top_indices]
            
            # Actualizar cluster
            cluster.top_terms = top_terms
            cluster.label = " | ".join([term for term, _ in top_terms[:3]])
```

**4. RAGContextAssemblyService**

```python
class RAGContextAssemblyService:
    """
    Domain service para ensamblar context packs para RAG.
    
    Responsabilidades:
    - Recuperar chunks relevantes
    - Ordenar por relevancia y fecha
    - Limitar tokens
    - Formatear para LLM
    """
    
    def __init__(
        self,
        vector_store: IVectorStore,
        max_tokens: int = 4000,
    ):
        self._vector_store = vector_store
        self._max_tokens = max_tokens
    
    async def assemble_context_pack(
        self,
        query: str,
        query_embedding: VectorEmbedding,
        top_k: int = 20,
        filters: Optional[Dict[str, Any]] = None,
    ) -> ContextPack:
        """
        Ensambla context pack para RAG.
        
        Args:
            query: Query de búsqueda
            query_embedding: Embedding del query
            top_k: Número de chunks a recuperar
            filters: Filtros adicionales (fecha, source, etc.)
            
        Returns:
            ContextPack
        """
        # Buscar chunks similares
        search_results = await self._vector_store.search_similar(
            query_embedding=query_embedding,
            top_k=top_k,
            filters=filters,
        )
        
        # Crear context pack
        context_pack = ContextPack(
            id=ContextPackId.generate(),
            query=query,
            query_embedding=query_embedding,
            chunks=[],
            chunk_summaries=[],
            tldrs=[],
            total_tokens=0,
            relevance_scores=[],
            sources=[],
            max_tokens=self._max_tokens,
            created_at=datetime.now(timezone.utc),
        )
        
        # Agregar chunks hasta límite de tokens
        for chunk, score in search_results:
            try:
                context_pack.add_chunk(chunk, score)
                context_pack.chunk_summaries.append(chunk.summary)
                
                if chunk.source_url not in context_pack.sources:
                    context_pack.sources.append(chunk.source_url)
            
            except ContextPackFullException:
                break
        
        # Recuperar TLDRs de artículos únicos
        unique_article_ids = list(set(chunk.article_id for chunk in context_pack.chunks))
        tldrs = await self._vector_store.get_tldrs(unique_article_ids)
        context_pack.tldrs = tldrs
        
        return context_pack
```

#### External Service Interfaces

**1. IEmbeddingService**

```python
class IEmbeddingService(Protocol):
    """
    Interface para servicio de embeddings.
    
    Implementaciones:
    - NomicEmbeddingAdapter (nomic-embed-text)
    - SentenceTransformersAdapter (sentence-transformers)
    """
    
    async def embed_text(self, text: str) -> VectorEmbedding:
        """
        Genera embedding para un texto.
        
        Args:
            text: Texto a embedear
            
        Returns:
            VectorEmbedding
        """
        ...
    
    async def embed_batch(self, texts: List[str]) -> List[VectorEmbedding]:
        """
        Genera embeddings para batch de textos.
        
        Args:
            texts: Lista de textos
            
        Returns:
            Lista de VectorEmbedding
        """
        ...
```

**2. ILLMService**

```python
class ILLMService(Protocol):
    """
    Interface para servicio de LLM.
    
    Implementaciones:
    - OpenAILLMAdapter (GPT-4)
    - LlamaLLMAdapter (Llama 3.x)
    - OllamaLLMAdapter (local)
    """
    
    async def generate(
        self,
        prompt: str,
        max_tokens: int = 500,
        temperature: float = 0.7,
        system_prompt: Optional[str] = None,
    ) -> str:
        """
        Genera texto usando LLM.
        
        Args:
            prompt: Prompt para el LLM
            max_tokens: Máximo de tokens a generar
            temperature: Temperature (0.0-1.0)
            system_prompt: System prompt opcional
            
        Returns:
            Texto generado
        """
        ...
```

**3. IVectorStore**

```python
class IVectorStore(Protocol):
    """
    Interface para vector store.
    
    Implementaciones:
    - PgVectorStoreAdapter (PostgreSQL + pgvector)
    """
    
    async def store_chunks(
        self,
        chunks: List[ContentChunk],
        article_id: str,
    ) -> List[str]:
        """
        Almacena chunks con embeddings.
        
        Args:
            chunks: Lista de chunks
            article_id: ID del artículo
            
        Returns:
            Lista de IDs de chunks creados
        """
        ...
    
    async def search_similar(
        self,
        query_embedding: VectorEmbedding,
        top_k: int = 10,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Tuple[ContentChunk, float]]:
        """
        Busca chunks similares.
        
        Args:
            query_embedding: Embedding del query
            top_k: Número de resultados
            filters: Filtros adicionales
            
        Returns:
            Lista de (chunk, similarity_score)
        """
        ...
    
    async def get_tldrs(self, article_ids: List[str]) -> List[TLDR]:
        """
        Obtiene TLDRs de artículos.
        
        Args:
            article_ids: IDs de artículos
            
        Returns:
            Lista de TLDR
        """
        ...
    
    async def delete_chunks(self, article_id: str) -> None:
        """
        Elimina chunks de un artículo.
        
        Args:
            article_id: ID del artículo
        """
        ...
```



## Data Models

### Database Schema (PostgreSQL + pgvector)

```sql
-- Extensión pgvector
CREATE EXTENSION IF NOT EXISTS vector;

-- Tabla de chunks (Aggregate Root)
CREATE TABLE ai_content_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    article_id VARCHAR(255) NOT NULL,  -- Referencia externa al Article BC
    
    -- Contenido
    content TEXT NOT NULL,
    summary TEXT,
    
    -- Embedding vectorial
    embedding VECTOR(768),  -- Nullable hasta que se genere
    
    -- Posición en el artículo original
    position INTEGER NOT NULL,
    start_char INTEGER NOT NULL,
    end_char INTEGER NOT NULL,
    
    -- Metadata
    token_count INTEGER NOT NULL,
    source_url TEXT NOT NULL,
    published_at TIMESTAMP WITH TIME ZONE,
    topics JSONB,  -- Array de topics
    tokens_mentioned JSONB,  -- Array de tokens cripto mencionados
    
    -- Estado del procesamiento
    status VARCHAR(50) NOT NULL DEFAULT 'PENDING',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT chk_token_count CHECK (token_count >= 100 AND token_count <= 2000),
    CONSTRAINT chk_position CHECK (position >= 0),
    CONSTRAINT chk_char_positions CHECK (start_char < end_char AND start_char >= 0)
);

-- Índice HNSW para búsqueda vectorial eficiente
CREATE INDEX idx_chunks_embedding_hnsw 
ON ai_content_chunks 
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64)
WHERE embedding IS NOT NULL;  -- Índice parcial

-- Índices adicionales
CREATE INDEX idx_chunks_article_id ON ai_content_chunks(article_id);
CREATE INDEX idx_chunks_status ON ai_content_chunks(status);
CREATE INDEX idx_chunks_position ON ai_content_chunks(article_id, position);

-- Tabla de estado de procesamiento (Read Model)
CREATE TABLE ai_article_processing_status (
    article_id VARCHAR(255) PRIMARY KEY,
    
    -- Contadores
    total_chunks INTEGER NOT NULL DEFAULT 0,
    chunks_embedded INTEGER NOT NULL DEFAULT 0,
    chunks_summarized INTEGER NOT NULL DEFAULT 0,
    chunks_completed INTEGER NOT NULL DEFAULT 0,
    
    -- Summaries globales
    has_global_summary BOOLEAN NOT NULL DEFAULT FALSE,
    has_tldr BOOLEAN NOT NULL DEFAULT FALSE,
    global_summary TEXT,
    tldr JSONB,  -- Array de bullets
    
    -- Clustering
    cluster_id UUID,
    
    -- Estado
    status VARCHAR(50) NOT NULL DEFAULT 'PENDING',
    
    -- Timestamps
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT fk_cluster 
        FOREIGN KEY (cluster_id) 
        REFERENCES ai_semantic_clusters(id) 
        ON DELETE SET NULL
);

CREATE INDEX idx_processing_status_status ON ai_article_processing_status(status);
CREATE INDEX idx_processing_status_cluster ON ai_article_processing_status(cluster_id);

-- Tabla de clusters semánticos (Aggregate Root)
CREATE TABLE ai_semantic_clusters (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    label VARCHAR(500) NOT NULL,
    
    -- Centroid del cluster
    centroid VECTOR(768) NOT NULL,
    
    -- Referencias a artículos
    article_ids JSONB NOT NULL,  -- Array de article IDs
    
    -- Metadata
    size INTEGER NOT NULL DEFAULT 0,
    top_terms JSONB,  -- Array de {term, frequency}
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT chk_label_not_empty CHECK (label <> ''),
    CONSTRAINT chk_size_matches CHECK (size >= 0)
);

CREATE INDEX idx_clusters_size ON ai_semantic_clusters(size);
CREATE INDEX idx_clusters_updated_at ON ai_semantic_clusters(updated_at);

-- Tabla de context packs (Aggregate Root - opcional, efímero)
CREATE TABLE ai_context_packs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    query TEXT NOT NULL,
    query_embedding VECTOR(768) NOT NULL,
    
    -- Referencias a chunks
    chunk_ids JSONB NOT NULL,  -- Array de chunk UUIDs
    relevance_scores JSONB NOT NULL,  -- Array de scores (float)
    
    -- Metadata
    total_tokens INTEGER NOT NULL,
    max_tokens INTEGER NOT NULL,
    sources JSONB,  -- Array de URLs
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT chk_total_tokens CHECK (total_tokens <= max_tokens),
    CONSTRAINT chk_max_tokens CHECK (max_tokens > 0)
);

CREATE INDEX idx_context_packs_created_at ON ai_context_packs(created_at);

-- Tabla de relación artículo-cluster (para queries eficientes)
CREATE TABLE ai_article_cluster_assignments (
    article_id VARCHAR(255) PRIMARY KEY,
    cluster_id UUID NOT NULL,
    assigned_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT fk_cluster_assignment 
        FOREIGN KEY (cluster_id) 
        REFERENCES ai_semantic_clusters(id) 
        ON DELETE CASCADE
);

CREATE INDEX idx_article_cluster_cluster_id ON ai_article_cluster_assignments(cluster_id);
```

## Aggregate Invariantes

### ContentChunk Aggregate

1. **Invariante de Tamaño**: `100 <= token_count <= 2000`
2. **Invariante de Contenido**: `content` no puede estar vacío
3. **Invariante de Posición**: `position >= 0`
4. **Invariante de Caracteres**: `start_char < end_char` y ambos `>= 0`
5. **Invariante de Referencia**: `article_id` debe ser válido y no vacío
6. **Invariante de Embedding**: Si existe, debe ser 768 dims y normalizado (magnitud ≈ 1.0)
7. **Invariante de Summary**: Si existe, debe tener 3-5 frases
8. **Invariante de URL**: `source_url` debe ser URL válida (http:// o https://)
9. **Invariante de Transición de Estado**: `PENDING → EMBEDDED → SUMMARIZED → COMPLETED`
10. **Invariante de Completitud**: Para marcar como `COMPLETED`, debe tener embedding y summary

### SemanticCluster Aggregate

1. **Invariante de Tamaño**: `size == len(article_ids)`
2. **Invariante de Unicidad**: No puede haber `article_ids` duplicados
3. **Invariante de Label**: `label` no puede estar vacío
4. **Invariante de Centroid**: Debe ser 768 dims y normalizado
5. **Invariante de Timestamps**: `updated_at >= created_at`
6. **Invariante de Top Terms**: Cada término debe tener frecuencia > 0

### ContextPack Aggregate

1. **Invariante de Límite de Tokens**: `total_tokens <= max_tokens`
2. **Invariante de Alineación**: `len(chunk_ids) == len(relevance_scores)`
3. **Invariante de Ordenamiento**: `relevance_scores` debe estar ordenado descendentemente
4. **Invariante de Query**: `query` no puede estar vacío
5. **Invariante de Query Embedding**: Debe ser 768 dims y normalizado
6. **Invariante de Max Tokens**: `max_tokens > 0`

### Value Objects Invariantes

**VectorEmbedding**:
- Dimensión exacta: 768
- Normalizado: magnitud ≈ 1.0 (±0.0001)
- Modelo no vacío

**ChunkSummary**:
- Contenido no vacío
- 3-5 frases

**TLDR**:
- 3-5 bullets
- Cada bullet mínimo 10 caracteres

**TokenCount**:
- Valor >= 0
- Encoding válido

**ChunkMetadata**:
- article_id no vacío
- source_url válida (http:// o https://)

**GlobalSummary**:
- Contenido no vacío
- Mínimo 50 caracteres

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Chunk Size Bounds

*For any* text chunked by the system, all resulting chunks should have token counts between 100 and 2000 tokens.

**Validates: Requirements 1.1, 1.2**

### Property 2: Chunk Overlap Consistency

*For any* two consecutive chunks, the overlap should be approximately 150 tokens (±10% tolerance).

**Validates: Requirements 1.2**

### Property 3: Embedding Dimension Consistency

*For any* embedding generated, the vector dimension should be exactly 768.

**Validates: Requirements 2.2**

### Property 4: Embedding Normalization

*For any* embedding generated, the vector magnitude should be 1.0 (±0.0001 tolerance).

**Validates: Requirements 2.6**

### Property 5: Summary Sentence Count

*For any* chunk summary generated, the number of sentences should be between 3 and 5.

**Validates: Requirements 3.1**

### Property 6: TLDR Bullet Count

*For any* TLDR generated, the number of bullets should be between 3 and 5.

**Validates: Requirements 3.5**

### Property 7: Vector Search Ordering

*For any* semantic search result, the chunks should be ordered by similarity score in descending order.

**Validates: Requirements 5.5**

### Property 8: Vector Search Top-K

*For any* semantic search with parameter k, the result should contain exactly k chunks (or fewer if not enough exist).

**Validates: Requirements 5.3**

### Property 9: Context Pack Token Limit

*For any* context pack assembled, the total token count should not exceed the configured max_tokens.

**Validates: Requirements 7.4**

### Property 10: Context Pack Ordering

*For any* context pack, chunks should be ordered first by relevance score (descending), then by publication date (descending).

**Validates: Requirements 7.3**

### Property 11: Duplicate Detection Threshold

*For any* duplicate detection result, all returned similar articles should have similarity score > threshold (0.85).

**Validates: Requirements 9.2**

### Property 12: Cluster Assignment Uniqueness

*For any* article, it should be assigned to at most one cluster at any given time.

**Validates: Requirements 6.4**

### Property 13: Chunk Position Monotonicity

*For any* list of chunks from the same article, the position values should be strictly increasing (0, 1, 2, ...).

**Validates: Requirements 1.7**

### Property 14: Batch Processing Size

*For any* batch processing operation, the batch size should not exceed 32 items.

**Validates: Requirements 11.1**

### Property 15: Generated Content Citation

*For any* content generated with RAG, the output should include references to source chunks used.

**Validates: Requirements 8.6**

## Error Handling

### Domain Exceptions

```python
class AIProcessingException(DomainException):
    """Base exception for AI processing errors."""
    pass

class ChunkingException(AIProcessingException):
    """Raised when chunking fails."""
    pass

class EmbeddingGenerationException(AIProcessingException):
    """Raised when embedding generation fails."""
    pass

class SummarizationException(AIProcessingException):
    """Raised when summarization fails."""
    pass

class VectorStoreException(AIProcessingException):
    """Raised when vector store operations fail."""
    pass

class ContextPackFullException(AIProcessingException):
    """Raised when context pack exceeds token limit."""
    pass

class ClusteringException(AIProcessingException):
    """Raised when clustering fails."""
    pass
```

### Error Recovery Strategies

1. **Chunking Failures**: Log error, skip article, continue with next
2. **Embedding Failures**: Retry up to 3 times with exponential backoff
3. **Summarization Failures**: Use fallback extractive summary
4. **Vector Store Failures**: Rollback transaction, log error
5. **LLM Timeouts**: Retry with reduced max_tokens

## Testing Strategy

### Unit Tests

**Domain Layer**:
- Value Objects: Validation, immutability
- Aggregates: Business logic, event generation
- Domain Services: Chunking, summarization, clustering logic

**Application Layer**:
- Command Handlers: Command execution, error handling
- Query Handlers: Data retrieval, filtering
- Event Handlers: Event processing, command emission

### Property-Based Tests

Using `hypothesis` for property testing:

```python
from hypothesis import given, strategies as st

@given(
    text=st.text(min_size=1000, max_size=10000),
    chunk_size=st.integers(min_value=1000, max_value=1500),
)
def test_chunking_size_bounds(text, chunk_size):
    """Property: All chunks should be within size bounds."""
    service = ChunkingService(chunk_size=chunk_size)
    chunks = service.chunk_text(text, "test-id", "https://test.com")
    
    for chunk in chunks:
        assert 100 <= chunk.token_count.value <= 2000

@given(
    vector=st.lists(
        st.floats(min_value=-1.0, max_value=1.0),
        min_size=768,
        max_size=768,
    )
)
def test_embedding_normalization(vector):
    """Property: Embeddings should be normalized."""
    import numpy as np
    
    vec_array = np.array(vector, dtype=np.float32)
    vec_array = vec_array / np.linalg.norm(vec_array)
    
    embedding = VectorEmbedding(
        vector=vec_array,
        model="test",
        dimension=768,
    )
    
    magnitude = np.linalg.norm(embedding.vector)
    assert np.isclose(magnitude, 1.0, atol=1e-5)
```

### Integration Tests

**Vector Store**:
- Store and retrieve chunks
- Semantic search accuracy
- Index performance

**External Services**:
- Embedding generation (nomic-embed-text)
- LLM generation (GPT-4 / Llama)
- Batch processing

### E2E Tests

**Complete Pipeline**:
1. Trigger ArticleQualityCalculated event
2. Verify ProcessArticleForAICommand execution
3. Verify chunks created in database
4. Verify embeddings stored
5. Verify summaries generated
6. Verify ArticleAIProcessedEvent emitted

**RAG Flow**:
1. Generate content request
2. Verify semantic search
3. Verify context pack assembly
4. Verify content generation
5. Verify source citations

## Performance Considerations

### Optimization Strategies

1. **Batch Processing**:
   - Embeddings: Batch size 32
   - Summaries: Parallel processing with concurrency limit
   - Database inserts: Bulk inserts

2. **Caching**:
   - Embedding cache for frequently accessed chunks
   - LLM response cache for common queries
   - Cluster assignments cache

3. **Indexing**:
   - HNSW index for vector search (m=16, ef_construction=64)
   - B-tree indexes on article_id, cluster_id
   - Partial indexes on status column

4. **Connection Pooling**:
   - PostgreSQL: pool_size=20, max_overflow=40
   - HTTP clients: connection pooling enabled

### Scalability

- **Horizontal Scaling**: Stateless services, can scale workers
- **Vertical Scaling**: GPU for embeddings, more RAM for vector search
- **Async Processing**: All I/O operations async
- **Queue-Based**: Use Celery/BullMQ for background processing

## Deployment Considerations

### Dependencies

```
# Core
langchain>=0.1.0
tiktoken>=0.5.0
numpy>=1.24.0
scikit-learn>=1.3.0

# Embeddings
nomic>=1.0.0
sentence-transformers>=2.2.0

# LLM
openai>=1.0.0
llama-cpp-python>=0.2.0  # For local Llama

# Vector Store
psycopg[binary]>=3.1.0
pgvector>=0.2.0

# NLP
nltk>=3.8.0
spacy>=3.7.0
```

### Environment Variables

```bash
# LLM Configuration
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4-turbo-preview
LLAMA_MODEL_PATH=/models/llama-3-8b-instruct.gguf

# Embedding Configuration
NOMIC_API_KEY=...
EMBEDDING_MODEL=nomic-embed-text
EMBEDDING_DIMENSION=768

# Vector Store
POSTGRES_VECTOR_DB_URL=postgresql://...
VECTOR_INDEX_TYPE=hnsw
VECTOR_INDEX_M=16
VECTOR_INDEX_EF_CONSTRUCTION=64

# Processing Configuration
CHUNK_SIZE=1200
CHUNK_OVERLAP=150
MAX_CONTEXT_TOKENS=4000
BATCH_SIZE=32
MAX_CONCURRENCY=10

# Performance
ENABLE_EMBEDDING_CACHE=true
ENABLE_LLM_CACHE=true
CACHE_TTL_SECONDS=3600
```

### Infrastructure

- **Database**: PostgreSQL 15+ with pgvector extension
- **Compute**: GPU recommended for embeddings (NVIDIA T4 or better)
- **Memory**: 16GB+ RAM for vector operations
- **Storage**: SSD for database (vector indexes benefit from fast I/O)

## Migration Strategy

### Phase 1: Foundation (Week 1-2)
- Set up PostgreSQL with pgvector
- Implement chunking service
- Implement embedding service (nomic-embed-text)
- Basic vector storage

### Phase 2: Summarization (Week 3)
- Implement LLM service
- Hierarchical summarization
- TLDR generation

### Phase 3: Search & Retrieval (Week 4)
- Semantic search
- Context pack assembly
- RAG generation

### Phase 4: Advanced Features (Week 5-6)
- Semantic clustering
- Duplicate detection
- Performance optimization

### Phase 5: Integration (Week 7)
- Event-driven integration with Article BC
- End-to-end testing
- Production deployment

## References

- **LangChain Documentation**: https://python.langchain.com/
- **pgvector Documentation**: https://github.com/pgvector/pgvector
- **Nomic Embed**: https://www.nomic.ai/blog/nomic-embed-text-v1
- **RAG Pattern**: https://arxiv.org/abs/2005.11401
- **Existing Capabilities**: `.kiro/steering/existing-content-processing-capabilities.md`

