# RAG Bounded Context

**Parent:** `../../AGENTS.md`

## OVERVIEW

Retrieval-augmented generation: semantic search, query processing, context assembly.

## WHERE TO LOOK

| Task | Location | Notes |
|------|----------|-------|
| Query logic | `domain/services/` | RAGQueryService |
| Context assembly | `app/queries/` | Query handlers |
| External APIs | `infra/external/` | LLM integrations |

## CONVENTIONS

- **Uses chunking**: Retrieves from KnowledgeChunkRepository
- **Assembly**: Combines relevant chunks for LLM context
