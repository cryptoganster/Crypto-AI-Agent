# AI Content Processing BC - Architecture Summary

## Aggregate Roots (3)

### 1. ContentChunk
- **Responsabilidad**: Segmento procesado de texto con embedding y summary
- **Ciclo de vida**: PENDING → EMBEDDED → SUMMARIZED → COMPLETED
- **Repository**: `ContentChunkRepository`
- **Invariantes**: 10 invariantes (tamaño, posición, embedding, summary, etc.)

### 2. SemanticCluster
- **Responsabilidad**: Agrupa artículos similares semánticamente
- **Repository**: `SemanticClusterRepository`
- **Invariantes**: 6 invariantes (tamaño, unicidad, centroid, etc.)

### 3. ContextPack
- **Responsabilidad**: Ensambla contexto para generación RAG
- **Repository**: `ContextPackRepository` (opcional, efímero)
- **Invariantes**: 6 invariantes (límite tokens, ordenamiento, etc.)

## Value Objects (7)

1. **VectorEmbedding**: Vector 768 dims normalizado
2. **ChunkSummary**: Resumen 3-5 frases
3. **TLDR**: 3-5 bullets
4. **TokenCount**: Conteo con tiktoken
5. **ChunkMetadata**: Metadata contextual
6. **GlobalSummary**: Resumen global de artículo
7. **ChunkStatus**: Enum de estados

## Read Models (CQRS)

### ArticleProcessingStatus
- **NO es aggregate**
- Actualizado por event handlers
- Provee vista materializada del estado de procesamiento
- Campos: total_chunks, chunks_embedded, chunks_summarized, has_tldr, etc.

## Domain Services (5)

1. **ChunkingService**: Divide texto en chunks
2. **SummarizationService**: Genera summaries jerárquicos
3. **ClusteringService**: Agrupa artículos similares
4. **RAGContextAssemblyService**: Ensambla context packs
5. **TextCleaningService**: Limpia y normaliza texto

## External Service Interfaces (3)

1. **IEmbeddingService**: Genera embeddings (nomic-embed-text)
2. **ILLMService**: Genera texto con LLM (GPT-4/Llama)
3. **IVectorStore**: Almacena y busca vectores (pgvector)

## Database Tables

1. **ai_content_chunks**: Chunks (aggregate root)
2. **ai_article_processing_status**: Read model
3. **ai_semantic_clusters**: Clusters (aggregate root)
4. **ai_context_packs**: Context packs (aggregate root, opcional)
5. **ai_article_cluster_assignments**: Relación artículo-cluster

## Key Design Decisions

### ✅ NO hay ProcessedArticle aggregate
- **Razón**: Evitar duplicar el Article aggregate del Article BC
- **Solución**: Read model + eventos para estado de procesamiento

### ✅ ContentChunk como Aggregate Root
- **Razón**: Permite búsqueda vectorial eficiente sin cargar artículos completos
- **Ventaja**: Procesamiento paralelo, escalabilidad

### ✅ Consistencia Eventual
- Los aggregates se comunican por eventos
- Read models se actualizan asíncronamente
- Cada aggregate tiene su propia transacción

### ✅ Referencias Externas
- `article_id` es referencia al Article BC (no FK)
- Límites de bounded context respetados

## Event Flow

```
Article BC                          AI Content Processing BC
─────────────────────────────────────────────────────────────
Article                             
  ↓ emite                           
ArticleQualityCalculated            
  ↓                                 
  ├─────────────────────────────────→ ProcessArticleContentCommand
                                      ↓
                                    Create ContentChunk aggregates
                                      ↓ emite
                                    ChunkCreatedEvent
                                      ↓
                                    Update with embeddings
                                      ↓ emite
                                    ChunkEmbeddedEvent
                                      ↓
                                    Update with summaries
                                      ↓ emite
                                    ChunkSummarizedEvent
                                      ↓
                                    Mark as completed
                                      ↓ emite
                                    ChunkCompletedEvent
                                      ↓
                                    Update Read Model
                                    (ArticleProcessingStatus)
                                      ↓ emite
                                    ArticleAIProcessedEvent
  ←─────────────────────────────────┘
```

## Total Invariantes: ~22

- ContentChunk: 10 invariantes
- SemanticCluster: 6 invariantes
- ContextPack: 6 invariantes
- Value Objects: ~10 invariantes adicionales

## Correctness Properties: 15

Todas las properties están mapeadas a requirements específicos y serán implementadas como property-based tests usando `hypothesis`.
