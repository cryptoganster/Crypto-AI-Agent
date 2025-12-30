# Embedding Container - Quick Start Guide

## What Was Built

The **EmbeddingContainer** is a dependency injection container for the Embedding bounded context that manages:
- Vector embedding generation using Nomic Embed API
- Similarity search across article chunks
- Event-driven integration with Chunking BC

## Files Created

```
✅ src/embedding/container.py                           (350 lines)
✅ src/shared/config/embedding_config.py                (120 lines)
✅ tests/integration/embedding/test_embedding_container.py (400 lines)
✅ .kiro/specs/.../EMBEDDING_CONTAINER_COMPLETION.md
✅ .kiro/specs/.../EMBEDDING_CONTAINER_SUMMARY.md
```

## Quick Usage

### 1. Setup Environment

```bash
# Add to .env
NOMIC_API_KEY=your-api-key-here
EMBEDDING_MODEL=nomic-embed-text-v1.5
EMBEDDING_DIMENSION=768
EMBEDDING_BATCH_SIZE=32
```

### 2. Initialize Container

```python
from src.embedding.container import EmbeddingContainer
from src.shared.container import SharedContainer

# Create containers
shared = SharedContainer()
embedding = EmbeddingContainer(shared)

# Register handlers
embedding.register_handlers()
```

### 3. Generate Embeddings

```python
# Get service
embedding_service = embedding.get_embedding_service()

# Generate embeddings
texts = ["Article chunk 1", "Article chunk 2"]
embeddings = await embedding_service.generate_embeddings(texts)

# embeddings = [[0.1, 0.2, ...], [0.3, 0.4, ...]]  # 768-dim vectors
```

### 4. Search Similar Chunks

```python
# Get query handler
search_handler = embedding.get_search_similar_chunks_handler()

# Search
from src.embedding.app.queries.search_similar_chunks.query import (
    SearchSimilarChunksQuery,
)

query = SearchSimilarChunksQuery(
    query_text="machine learning",
    top_k=5,
    min_similarity=0.7,
)

result = await search_handler.handle(query)

for chunk in result.chunks:
    print(f"Similarity: {chunk.similarity_score}")
    print(f"Content: {chunk.content}")
```

## Event Flow

```
1. Article BC → ArticleQualityCalculated
   ↓
2. Chunking BC → ProcessArticleForAI
   ↓
3. Chunking BC → ArticleChunked
   ↓
4. Embedding BC → GenerateArticleEmbedding  ← YOU ARE HERE
   ↓
5. Embedding BC → ArticleEmbeddingGenerated
```

## Testing

```bash
# Run all tests
pytest tests/integration/embedding/test_embedding_container.py -v

# Run specific test
pytest tests/integration/embedding/test_embedding_container.py::TestEmbeddingContainer::test_get_embedding_service_resolves_correctly -v

# With coverage
pytest tests/integration/embedding/ --cov=src/embedding --cov-report=html
```

## Key Components

### Services
- **EmbeddingService**: Generates vector embeddings
- **NomicEmbedAdapter**: Integrates with Nomic Embed API

### Repositories
- **ArticleEmbeddingReadRepository**: Query embeddings
- **ArticleEmbeddingWriteRepository**: Store embeddings

### Handlers
- **GenerateArticleEmbeddingHandler**: Command to generate embeddings
- **SearchSimilarChunksHandler**: Query to search similar content
- **OnArticleChunkedHandler**: Event handler for chunking completion

## Configuration

### EmbeddingConfig

```python
from src.shared.config.embedding_config import EmbeddingConfig

# Load from environment
config = EmbeddingConfig.from_env()

# Access values
print(config.nomic_api_key)        # "your-api-key"
print(config.embedding_model)      # "nomic-embed-text-v1.5"
print(config.embedding_dimension)  # 768
print(config.batch_size)           # 32

# Validate
config.validate()  # Raises ValueError if invalid
```

## Architecture

### Dependency Graph

```
EmbeddingContainer
├── EmbeddingService
│   └── NomicEmbedAdapter (API client)
├── ArticleEmbeddingFactory
├── ArticleEmbeddingReadRepository
├── ArticleEmbeddingWriteRepository
├── GenerateArticleEmbeddingHandler
│   ├── EmbeddingService
│   ├── ArticleEmbeddingFactory
│   ├── ArticleEmbeddingWriteRepository
│   └── UnitOfWork
├── SearchSimilarChunksHandler
│   ├── EmbeddingService
│   └── ArticleEmbeddingReadRepository
└── OnArticleChunkedHandler
    └── CommandBus
```

### Event-Driven Integration

```
Chunking BC                    Embedding BC
    │                              │
    │  ArticleChunked             │
    ├──────────────────────────────>
    │                              │
    │                    OnArticleChunkedHandler
    │                              │
    │                    GenerateArticleEmbeddingCommand
    │                              │
    │                    GenerateArticleEmbeddingHandler
    │                              │
    │  ArticleEmbeddingGenerated  │
    <──────────────────────────────┤
    │                              │
```

## Common Operations

### Generate Embeddings for Article

```python
from src.embedding.app.commands.generate_article_embedding.command import (
    GenerateArticleEmbeddingCommand,
)

command = GenerateArticleEmbeddingCommand(
    article_id="article-123",
    chunks=[
        {"chunk_id": "chunk-1", "content": "Text 1"},
        {"chunk_id": "chunk-2", "content": "Text 2"},
    ],
)

result = await mediator.send(command)

if result.success:
    print(f"Generated {len(result.embeddings)} embeddings")
```

### Search Similar Content

```python
from src.embedding.app.queries.search_similar_chunks.query import (
    SearchSimilarChunksQuery,
)

query = SearchSimilarChunksQuery(
    query_text="artificial intelligence",
    top_k=10,
    min_similarity=0.75,
    article_ids=["article-1", "article-2"],  # Optional filter
)

result = await mediator.send(query)

for chunk in result.chunks:
    print(f"{chunk.article_id}: {chunk.similarity_score:.2f}")
```

## Troubleshooting

### API Key Not Found

```
ValueError: NOMIC_API_KEY environment variable is required
```

**Solution**: Add `NOMIC_API_KEY` to your `.env` file

### Invalid Model Name

```
ValueError: embedding_model must be one of ['nomic-embed-text-v1', 'nomic-embed-text-v1.5']
```

**Solution**: Use a valid model name in `EMBEDDING_MODEL`

### Handler Not Registered

```
HandlerNotFoundError: No handler registered for GenerateArticleEmbeddingCommand
```

**Solution**: Call `embedding.register_handlers()` during startup

## Next Steps

1. ✅ Container implemented
2. ✅ Configuration added
3. ✅ Tests written
4. ⏭️ Integrate with main application container
5. ⏭️ Test end-to-end flow
6. ⏭️ Add monitoring and metrics

## References

- **Full Documentation**: `EMBEDDING_CONTAINER_COMPLETION.md`
- **Summary**: `EMBEDDING_CONTAINER_SUMMARY.md`
- **Chunking Container**: `CHUNKING_CONTAINER_SUMMARY.md`
- **Architecture**: `.kiro/steering/architecture.md`

---

**Status**: ✅ READY TO USE
**Date**: 2024-12-11
