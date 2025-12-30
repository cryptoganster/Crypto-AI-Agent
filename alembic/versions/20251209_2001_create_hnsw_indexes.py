"""create_hnsw_indexes

Revision ID: create_hnsw_indexes
Revises: setup_pgvector_ai
Create Date: 2025-12-09 20:01:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'create_hnsw_indexes'
down_revision: Union[str, None] = 'setup_pgvector_ai'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Crea índices HNSW para búsqueda vectorial eficiente.
    
    HNSW (Hierarchical Navigable Small World) es un algoritmo de búsqueda
    de vecinos más cercanos aproximados (ANN) que ofrece:
    - Búsquedas muy rápidas (sub-linear time)
    - Alta precisión
    - Buen balance entre velocidad y memoria
    
    Parámetros:
    - m=16: Número de conexiones bidireccionales por nodo (default: 16)
      - Valores más altos: mejor recall, más memoria
      - Valores más bajos: menos memoria, menor recall
    - ef_construction=64: Tamaño de la lista dinámica durante construcción
      - Valores más altos: mejor calidad de índice, construcción más lenta
      - Valores más bajos: construcción más rápida, menor calidad
    
    Operador vector_cosine_ops:
    - Usa distancia coseno para similitud
    - Ideal para embeddings normalizados
    - Rango: [0, 2] donde 0 = idénticos, 2 = opuestos
    """
    
    # Índice HNSW en ai_content_chunks.embedding
    # Este es el índice más importante para búsqueda semántica
    op.execute("""
        CREATE INDEX idx_chunks_embedding_hnsw 
        ON crypto_news_scraper.ai_content_chunks 
        USING hnsw (embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 64)
    """)
    
    # Índice HNSW en ai_semantic_clusters.centroid
    # Para búsqueda de clusters similares
    op.execute("""
        CREATE INDEX idx_clusters_centroid_hnsw 
        ON crypto_news_scraper.ai_semantic_clusters 
        USING hnsw (centroid vector_cosine_ops)
        WITH (m = 16, ef_construction = 64)
    """)
    
    # Índice HNSW en ai_context_packs.query_embedding
    # Para búsqueda de queries similares (auditoría/cache)
    op.execute("""
        CREATE INDEX idx_context_packs_query_embedding_hnsw 
        ON crypto_news_scraper.ai_context_packs 
        USING hnsw (query_embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 64)
    """)


def downgrade() -> None:
    """Elimina índices HNSW."""
    
    op.execute('DROP INDEX IF EXISTS crypto_news_scraper.idx_context_packs_query_embedding_hnsw')
    op.execute('DROP INDEX IF EXISTS crypto_news_scraper.idx_clusters_centroid_hnsw')
    op.execute('DROP INDEX IF EXISTS crypto_news_scraper.idx_chunks_embedding_hnsw')
