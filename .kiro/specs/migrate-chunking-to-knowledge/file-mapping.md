# File and Class Mapping: chunking → knowledge

## Domain Layer

### Aggregates
```
src/chunking/domain/aggregates/content_chunk.py
→ src/knowledge/domain/aggregates/knowledge_chunk.py

Class: ContentChunk → KnowledgeChunk
```

### Value Objects
```
src/chunking/domain/value_objects/vector_embedding.py
→ src/knowledge/domain/value_objects/knowledge_embedding.py
Class: VectorEmbedding → KnowledgeEmbedding

src/chunking/domain/value_objects/chunk_summary.py
→ src/knowledge/domain/value_objects/knowledge_summary.py
Class: ChunkSummary → KnowledgeSummary

src/chunking/domain/value_objects/chunk_id.py
→ src/knowledge/domain/value_objects/knowledge_chunk_id.py
Class: ChunkId → KnowledgeChunkId

src/chunking/domain/value_objects/chunk_status.py
→ src/knowledge/domain/value_objects/knowledge_status.py
Class: ChunkStatus → KnowledgeStatus

src/chunking/domain/value_objects/token_count.py
→ src/knowledge/domain/value_objects/knowledge_metrics.py
Class: TokenCount → KnowledgeMetrics

src/chunking/domain/value_objects/tldr.py
→ src/knowledge/domain/value_objects/knowledge_tldr.py
Class: TLDR → KnowledgeTLDR
```

### Events
```
src/chunking/domain/events/article_ai_processed.py
→ src/knowledge/domain/events/knowledge_extracted.py
Class: ArticleAIProcessedEvent → KnowledgeExtractedEvent

src/chunking/domain/events/created.py
→ src/knowledge/domain/events/chunk_created.py
Class: ChunkCreatedEvent → KnowledgeChunkCreatedEvent

src/chunking/domain/events/embedded.py
→ src/knowledge/domain/events/knowledge_enriched.py
Class: ChunkEmbeddedEvent → KnowledgeEnrichedEvent

src/chunking/domain/events/summarized.py
→ src/knowledge/domain/events/knowledge_summarized.py
Class: ChunkSummarizedEvent → KnowledgeSummarizedEvent

src/chunking/domain/events/completed.py
→ src/knowledge/domain/events/knowledge_indexed.py
Class: ChunkCompletedEvent → KnowledgeIndexedEvent

src/chunking/domain/events/failed.py
→ src/knowledge/domain/events/processing_failed.py
Class: ChunkFailedEvent → KnowledgeProcessingFailedEvent
```

### Services
```
src/chunking/domain/services/chunking.py
→ src/knowledge/domain/services/knowledge_extraction.py
Class: ChunkingService → KnowledgeExtractionService

src/chunking/domain/services/chunk_validation.py
→ src/knowledge/domain/services/knowledge_validation.py
Class: ChunkValidationService → KnowledgeValidationService
```

### Interfaces - Repositories
```
src/chunking/domain/interfaces/repositories/chunk_repository.py
→ src/knowledge/domain/interfaces/repositories/knowledge_repository.py
Class: IChunkRepository → IKnowledgeRepository

src/chunking/domain/interfaces/repositories/chunk_read_repository.py
→ src/knowledge/domain/interfaces/repositories/knowledge_read_repository.py
Class: IChunkReadRepository → IKnowledgeReadRepository

src/chunking/domain/interfaces/repositories/chunk_write_repository.py
→ src/knowledge/domain/interfaces/repositories/knowledge_write_repository.py
Class: IChunkWriteRepository → IKnowledgeWriteRepository
```

### Interfaces - External Services
```
src/chunking/domain/interfaces/external/embedding_service.py
→ src/knowledge/domain/interfaces/external/embedding_service.py
Class: IEmbeddingService → IEmbeddingService (sin cambio)

src/chunking/domain/interfaces/external/summarization_service.py
→ src/knowledge/domain/interfaces/external/summarization_service.py
Class: ISummarizationService → ISummarizationService (sin cambio)

src/chunking/domain/interfaces/external/token_encoder.py
→ src/knowledge/domain/interfaces/external/token_encoder.py
Class: ITokenEncoder → ITokenEncoder (sin cambio)
```

### Exceptions
```
src/chunking/domain/exceptions.py
→ src/knowledge/domain/exceptions.py
Classes:
- ChunkingException → KnowledgeException
- ChunkNotFoundException → KnowledgeChunkNotFoundException
- ChunkValidationException → KnowledgeValidationException
- EmbeddingException → KnowledgeEmbeddingException
```

## Application Layer

### Commands
```
src/chunking/app/commands/chunk_article/
→ src/knowledge/app/commands/extract_knowledge/
Command: ChunkArticleCommand → ExtractKnowledgeCommand
Handler: ChunkArticleHandler → ExtractKnowledgeHandler
Result: ChunkArticleResult → ExtractKnowledgeResult

src/chunking/app/commands/generate_chunk_embeddings/
→ src/knowledge/app/commands/enrich_knowledge/
Command: GenerateChunkEmbeddingsCommand → EnrichKnowledgeCommand
Handler: GenerateChunkEmbeddingsHandler → EnrichKnowledgeHandler
Result: GenerateChunkEmbeddingsResult → EnrichKnowledgeResult

src/chunking/app/commands/generate_chunk_summaries/
→ src/knowledge/app/commands/summarize_knowledge/
Command: GenerateChunkSummariesCommand → SummarizeKnowledgeCommand
Handler: GenerateChunkSummariesHandler → SummarizeKnowledgeHandler
Result: GenerateChunkSummariesResult → SummarizeKnowledgeResult

src/chunking/app/commands/generate_global_summary/
→ src/knowledge/app/commands/generate_knowledge_summary/
Command: GenerateGlobalSummaryCommand → GenerateKnowledgeSummaryCommand
Handler: GenerateGlobalSummaryHandler → GenerateKnowledgeSummaryHandler
Result: GenerateGlobalSummaryResult → GenerateKnowledgeSummaryResult

src/chunking/app/commands/generate_tldr/
→ src/knowledge/app/commands/generate_knowledge_tldr/
Command: GenerateTLDRCommand → GenerateKnowledgeTLDRCommand
Handler: GenerateTLDRHandler → GenerateKnowledgeTLDRHandler
Result: GenerateTLDRResult → GenerateKnowledgeTLDRResult

src/chunking/app/commands/persist_chunks/
→ src/knowledge/app/commands/index_knowledge/
Command: PersistChunksCommand → IndexKnowledgeCommand
Handler: PersistChunksHandler → IndexKnowledgeHandler
Result: PersistChunksResult → IndexKnowledgeResult
```

### Queries
```
src/chunking/app/queries/get_article_chunks/
→ src/knowledge/app/queries/get_knowledge_chunks/
Query: GetArticleChunksQuery → GetKnowledgeChunksQuery
Handler: GetArticleChunksHandler → GetKnowledgeChunksHandler
DTO: ArticleChunksDTO → KnowledgeChunksDTO

src/chunking/app/queries/get_article_processing_status/
→ src/knowledge/app/queries/get_knowledge_processing_status/
Query: GetArticleProcessingStatusQuery → GetKnowledgeProcessingStatusQuery
Handler: GetArticleProcessingStatusHandler → GetKnowledgeProcessingStatusHandler
DTO: ArticleProcessingStatusDTO → KnowledgeProcessingStatusDTO

src/chunking/app/queries/get_processing_metrics/
→ src/knowledge/app/queries/get_knowledge_metrics/
Query: GetProcessingMetricsQuery → GetKnowledgeMetricsQuery
Handler: GetProcessingMetricsHandler → GetKnowledgeMetricsHandler
DTO: ProcessingMetricsDTO → KnowledgeMetricsDTO

src/chunking/app/queries/get_processing_status/
→ src/knowledge/app/queries/get_processing_status/
Query: GetProcessingStatusQuery → GetProcessingStatusQuery (sin cambio)
Handler: GetProcessingStatusHandler → GetProcessingStatusHandler (sin cambio)
```

### Process Managers
```
src/chunking/app/process_managers/article_ai_processing_pipeline.py
→ src/knowledge/app/process_managers/knowledge_processing_pipeline.py
Class: ArticleAIProcessingPipeline → KnowledgeProcessingPipeline
```

### Event Handlers
```
src/chunking/app/event_handlers/on_article_quality_calculated.py
→ src/knowledge/app/event_handlers/on_article_quality_calculated.py
Class: OnArticleQualityCalculatedHandler → OnArticleQualityCalculatedHandler (sin cambio)
```

### Read Models
```
src/chunking/app/read_models/article_processing_status.py
→ src/knowledge/app/read_models/knowledge_processing_status.py
Class: ArticleProcessingStatus → KnowledgeProcessingStatus
```

## Infrastructure Layer

### Persistence - Models
```
src/chunking/infra/persistence/models/chunk_model.py
→ src/knowledge/infra/persistence/models/knowledge_chunk_model.py
Class: ChunkModel → KnowledgeChunkModel

src/chunking/infra/persistence/models/processing_status_model.py
→ src/knowledge/infra/persistence/models/knowledge_processing_status_model.py
Class: ProcessingStatusModel → KnowledgeProcessingStatusModel
```

### Persistence - Repositories
```
src/chunking/infra/persistence/repositories/chunk_repository.py
→ src/knowledge/infra/persistence/repositories/knowledge_repository.py
Class: SqlAlchemyChunkRepository → SqlAlchemyKnowledgeRepository

src/chunking/infra/persistence/repositories/chunk_read_repository.py
→ src/knowledge/infra/persistence/repositories/knowledge_read_repository.py
Class: SqlAlchemyChunkReadRepository → SqlAlchemyKnowledgeReadRepository

src/chunking/infra/persistence/repositories/chunk_write_repository.py
→ src/knowledge/infra/persistence/repositories/knowledge_write_repository.py
Class: SqlAlchemyChunkWriteRepository → SqlAlchemyKnowledgeWriteRepository

src/chunking/infra/persistence/repositories/processing_status_repository.py
→ src/knowledge/infra/persistence/repositories/knowledge_processing_status_repository.py
Class: ProcessingStatusRepository → KnowledgeProcessingStatusRepository
```

### Persistence - Mappers
```
src/chunking/infra/persistence/mappers/chunk_mapper.py
→ src/knowledge/infra/persistence/mappers/knowledge_chunk_mapper.py
Class: ChunkMapper → KnowledgeChunkMapper

src/chunking/infra/persistence/mappers/processing_status_mapper.py
→ src/knowledge/infra/persistence/mappers/knowledge_processing_status_mapper.py
Class: ProcessingStatusMapper → KnowledgeProcessingStatusMapper
```

### Persistence - Vector Store
```
src/chunking/infra/persistence/pg_vector_store_adapter.py
→ src/knowledge/infra/persistence/pg_vector_store_adapter.py
Class: PgVectorStoreAdapter → PgVectorStoreAdapter (sin cambio, pero actualizar imports)
```

### External Services
```
src/chunking/infra/external/ollama_embedding_adapter.py
→ src/knowledge/infra/external/ollama_embedding_adapter.py
Class: OllamaEmbeddingAdapter → OllamaEmbeddingAdapter (sin cambio)

src/chunking/infra/external/langchain_markdown_splitter.py
→ src/knowledge/infra/external/langchain_markdown_splitter.py
Class: LangChainMarkdownSplitter → LangChainMarkdownSplitter (sin cambio)

src/chunking/infra/external/langchain_token_encoder.py
→ src/knowledge/infra/external/langchain_token_encoder.py
Class: LangChainTokenEncoder → LangChainTokenEncoder (sin cambio)

src/chunking/infra/external/huggingface_token_encoder.py
→ src/knowledge/infra/external/huggingface_token_encoder.py
Class: HuggingFaceTokenEncoder → HuggingFaceTokenEncoder (sin cambio)
```

## Container
```
src/chunking/container.py
→ src/knowledge/container.py
Class: ChunkingContainer → KnowledgeContainer
```

## Tests

### Unit Tests - Domain
```
tests/unit/chunking/domain/aggregates/test_content_chunk.py
→ tests/unit/knowledge/domain/aggregates/test_knowledge_chunk.py

tests/unit/chunking/domain/value_objects/test_vector_embedding.py
→ tests/unit/knowledge/domain/value_objects/test_knowledge_embedding.py

tests/unit/chunking/domain/value_objects/test_chunk_summary.py
→ tests/unit/knowledge/domain/value_objects/test_knowledge_summary.py

tests/unit/chunking/domain/services/test_chunking.py
→ tests/unit/knowledge/domain/services/test_knowledge_extraction.py
```

### Unit Tests - Application
```
tests/unit/chunking/app/commands/test_chunk_article.py
→ tests/unit/knowledge/app/commands/test_extract_knowledge.py

tests/unit/chunking/app/process_managers/test_article_ai_processing_pipeline.py
→ tests/unit/knowledge/app/process_managers/test_knowledge_processing_pipeline.py
```

### Integration Tests
```
tests/integration/chunking/test_chunk_repository.py
→ tests/integration/knowledge/test_knowledge_repository.py

tests/integration/chunking/test_vector_store.py
→ tests/integration/knowledge/test_vector_store.py
```

## Summary Statistics

- **Total files to rename**: ~80-100 archivos
- **Total classes to rename**: ~60-80 clases
- **Total directories to rename**: ~15-20 directorios
- **Bounded contexts affected**: article, source, fetching, shared
- **Estimated imports to update**: ~200-300 import statements

## Sed Commands for Bulk Renaming

### Classes (in order of dependencies)
```bash
# Value Objects
find src/knowledge -type f -name "*.py" -exec sed -i '' 's/VectorEmbedding/KnowledgeEmbedding/g' {} +
find src/knowledge -type f -name "*.py" -exec sed -i '' 's/ChunkSummary/KnowledgeSummary/g' {} +
find src/knowledge -type f -name "*.py" -exec sed -i '' 's/ChunkId/KnowledgeChunkId/g' {} +
find src/knowledge -type f -name "*.py" -exec sed -i '' 's/ChunkStatus/KnowledgeStatus/g' {} +
find src/knowledge -type f -name "*.py" -exec sed -i '' 's/TokenCount/KnowledgeMetrics/g' {} +
find src/knowledge -type f -name "*.py" -exec sed -i '' 's/\bTLDR\b/KnowledgeTLDR/g' {} +

# Events
find src/knowledge -type f -name "*.py" -exec sed -i '' 's/ArticleAIProcessedEvent/KnowledgeExtractedEvent/g' {} +
find src/knowledge -type f -name "*.py" -exec sed -i '' 's/ChunkCreatedEvent/KnowledgeChunkCreatedEvent/g' {} +
find src/knowledge -type f -name "*.py" -exec sed -i '' 's/ChunkEmbeddedEvent/KnowledgeEnrichedEvent/g' {} +
find src/knowledge -type f -name "*.py" -exec sed -i '' 's/ChunkSummarizedEvent/KnowledgeSummarizedEvent/g' {} +
find src/knowledge -type f -name "*.py" -exec sed -i '' 's/ChunkCompletedEvent/KnowledgeIndexedEvent/g' {} +
find src/knowledge -type f -name "*.py" -exec sed -i '' 's/ChunkFailedEvent/KnowledgeProcessingFailedEvent/g' {} +

# Aggregates
find src/knowledge -type f -name "*.py" -exec sed -i '' 's/ContentChunk/KnowledgeChunk/g' {} +

# Services
find src/knowledge -type f -name "*.py" -exec sed -i '' 's/ChunkingService/KnowledgeExtractionService/g' {} +
find src/knowledge -type f -name "*.py" -exec sed -i '' 's/ChunkValidationService/KnowledgeValidationService/g' {} +

# Commands
find src/knowledge -type f -name "*.py" -exec sed -i '' 's/ChunkArticleCommand/ExtractKnowledgeCommand/g' {} +
find src/knowledge -type f -name "*.py" -exec sed -i '' 's/ChunkArticleHandler/ExtractKnowledgeHandler/g' {} +
find src/knowledge -type f -name "*.py" -exec sed -i '' 's/GenerateChunkEmbeddingsCommand/EnrichKnowledgeCommand/g' {} +
find src/knowledge -type f -name "*.py" -exec sed -i '' 's/GenerateChunkSummariesCommand/SummarizeKnowledgeCommand/g' {} +
find src/knowledge -type f -name "*.py" -exec sed -i '' 's/GenerateGlobalSummaryCommand/GenerateKnowledgeSummaryCommand/g' {} +
find src/knowledge -type f -name "*.py" -exec sed -i '' 's/GenerateTLDRCommand/GenerateKnowledgeTLDRCommand/g' {} +
find src/knowledge -type f -name "*.py" -exec sed -i '' 's/PersistChunksCommand/IndexKnowledgeCommand/g' {} +

# Process Managers
find src/knowledge -type f -name "*.py" -exec sed -i '' 's/ArticleAIProcessingPipeline/KnowledgeProcessingPipeline/g' {} +

# Containers
find src/knowledge -type f -name "*.py" -exec sed -i '' 's/ChunkingContainer/KnowledgeContainer/g' {} +

# Repositories
find src/knowledge -type f -name "*.py" -exec sed -i '' 's/IChunkRepository/IKnowledgeRepository/g' {} +
find src/knowledge -type f -name "*.py" -exec sed -i '' 's/SqlAlchemyChunkRepository/SqlAlchemyKnowledgeRepository/g' {} +

# Models
find src/knowledge -type f -name "*.py" -exec sed -i '' 's/ChunkModel/KnowledgeChunkModel/g' {} +

# Exceptions
find src/knowledge -type f -name "*.py" -exec sed -i '' 's/ChunkingException/KnowledgeException/g' {} +
find src/knowledge -type f -name "*.py" -exec sed -i '' 's/ChunkNotFoundException/KnowledgeChunkNotFoundException/g' {} +
```

## File Renaming Script

```bash
#!/bin/bash
# rename_files.sh - Renombra archivos en src/knowledge/

cd src/knowledge

# Value Objects
mv domain/value_objects/vector_embedding.py domain/value_objects/knowledge_embedding.py
mv domain/value_objects/chunk_summary.py domain/value_objects/knowledge_summary.py
mv domain/value_objects/chunk_id.py domain/value_objects/knowledge_chunk_id.py
mv domain/value_objects/chunk_status.py domain/value_objects/knowledge_status.py
mv domain/value_objects/token_count.py domain/value_objects/knowledge_metrics.py
mv domain/value_objects/tldr.py domain/value_objects/knowledge_tldr.py

# Events
mv domain/events/article_ai_processed.py domain/events/knowledge_extracted.py
mv domain/events/created.py domain/events/chunk_created.py
mv domain/events/embedded.py domain/events/knowledge_enriched.py
mv domain/events/summarized.py domain/events/knowledge_summarized.py
mv domain/events/completed.py domain/events/knowledge_indexed.py
mv domain/events/failed.py domain/events/processing_failed.py

# Aggregates
mv domain/aggregates/content_chunk.py domain/aggregates/knowledge_chunk.py

# Services
mv domain/services/chunking.py domain/services/knowledge_extraction.py
mv domain/services/chunk_validation.py domain/services/knowledge_validation.py

# Commands (directories)
mv app/commands/chunk_article app/commands/extract_knowledge
mv app/commands/generate_chunk_embeddings app/commands/enrich_knowledge
mv app/commands/generate_chunk_summaries app/commands/summarize_knowledge
mv app/commands/generate_global_summary app/commands/generate_knowledge_summary
mv app/commands/generate_tldr app/commands/generate_knowledge_tldr
mv app/commands/persist_chunks app/commands/index_knowledge

# Queries (directories)
mv app/queries/get_article_chunks app/queries/get_knowledge_chunks
mv app/queries/get_article_processing_status app/queries/get_knowledge_processing_status
mv app/queries/get_processing_metrics app/queries/get_knowledge_metrics

# Process Managers
mv app/process_managers/article_ai_processing_pipeline.py app/process_managers/knowledge_processing_pipeline.py

# Read Models
mv app/read_models/article_processing_status.py app/read_models/knowledge_processing_status.py

# Repositories
mv infra/persistence/repositories/chunk_repository.py infra/persistence/repositories/knowledge_repository.py
mv infra/persistence/repositories/chunk_read_repository.py infra/persistence/repositories/knowledge_read_repository.py
mv infra/persistence/repositories/chunk_write_repository.py infra/persistence/repositories/knowledge_write_repository.py

# Mappers
mv infra/persistence/mappers/chunk_mapper.py infra/persistence/mappers/knowledge_chunk_mapper.py

# Models
mv infra/persistence/models/chunk_model.py infra/persistence/models/knowledge_chunk_model.py

echo "✅ File renaming complete"
```
