# Chunking Bounded Context

**Parent:** `../../AGENTS.md`

## OVERVIEW

AI content processing: chunking, embeddings (Ollama), vector storage (pgvector).

## WHERE TO LOOK

| Task | Location | Notes |
|------|----------|-------|
| Chunking logic | `domain/services/` | ContentChunkService |
| Embeddings | `infra/external/` | Ollama embeddings |
| Vector DB | `infra/persistence/` | pgvector repositories |

## CONVENTIONS

- **Models**: nomic-embed-text, mxbai-embed-large via Ollama
- **Chunk size**: Configurable in `.env`
- **DEPRECATED**: Repository methods using `source_id` - migrate to `*_by_source()`
