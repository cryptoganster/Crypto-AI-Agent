# Clustering Bounded Context

**Parent:** `../../AGENTS.md`

## OVERVIEW

Semantic article clustering using embeddings and sklearn algorithms.

## WHERE TO LOOK

| Task | Location | Notes |
|------|----------|-------|
| Clustering logic | `domain/services/` | ArticleClusteringService |
| Algorithms | `infra/external/` | scikit-learn integration |
| Cluster storage | `infra/persistence/` | ClusterRepository |

## CONVENTIONS

- **Vector similarity**: Uses embeddings from chunking BC
- **Algorithms**: sklearn clustering (DBSCAN, KMeans configured)
