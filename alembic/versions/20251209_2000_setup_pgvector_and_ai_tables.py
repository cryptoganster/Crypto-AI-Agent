"""setup_pgvector_and_ai_tables

Revision ID: setup_pgvector_ai
Revises: 24a7e06f83ce
Create Date: 2025-12-09 20:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'setup_pgvector_ai'
down_revision: Union[str, None] = '24a7e06f83ce'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Instala extensión pgvector y crea tablas para AI content processing.
    
    Tablas creadas:
    - ai_processed_articles: Artículos procesados con AI
    - ai_semantic_clusters: Clusters semánticos de artículos
    - ai_content_chunks: Chunks de contenido con embeddings vectoriales
    - ai_context_packs: Context packs para RAG (opcional, auditoría)
    """
    # 1. Instalar extensión pgvector
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')
    
    # 2. Crear tabla ai_semantic_clusters (debe crearse primero por FK)
    op.create_table(
        'ai_semantic_clusters',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('label', sa.String(500), nullable=False, comment='Etiqueta descriptiva del cluster'),
        
        # Centroid del cluster (vector de 768 dimensiones)
        sa.Column('centroid', postgresql.ARRAY(sa.Float), nullable=False, comment='Centroid del cluster (vector 768D)'),
        
        # Metadata
        sa.Column('size', sa.Integer, nullable=False, server_default='0', comment='Número de artículos en el cluster'),
        sa.Column('top_terms', postgresql.JSONB, nullable=True, comment='Términos más frecuentes: [{term, frequency}]'),
        
        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        
        schema='crypto_news_scraper',
        comment='Clusters semánticos de artículos similares'
    )
    
    # 3. Crear tabla ai_processed_articles
    op.create_table(
        'ai_processed_articles',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('article_id', sa.String(255), nullable=False, unique=True, comment='ID del artículo original'),
        
        # Summaries
        sa.Column('global_summary', sa.Text, nullable=True, comment='Resumen global del artículo'),
        sa.Column('tldr', postgresql.JSONB, nullable=True, comment='TLDR en formato bullets: [string]'),
        
        # Metadata
        sa.Column('total_chunks', sa.Integer, nullable=False, server_default='0', comment='Total de chunks creados'),
        sa.Column('total_tokens', sa.Integer, nullable=False, server_default='0', comment='Total de tokens procesados'),
        
        # Clustering
        sa.Column('cluster_id', postgresql.UUID(as_uuid=True), nullable=True, comment='ID del cluster semántico'),
        sa.Column('similar_articles', postgresql.JSONB, nullable=True, comment='IDs de artículos similares: [string]'),
        
        # Estado
        sa.Column('status', sa.String(50), nullable=False, server_default='PENDING', comment='Estado: PENDING, PROCESSING, COMPLETED, FAILED'),
        
        # Timestamps
        sa.Column('processing_started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('processing_completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        
        schema='crypto_news_scraper',
        comment='Artículos procesados con AI (chunking, embeddings, summaries)'
    )
    
    # FK a clusters
    op.create_foreign_key(
        'fk_processed_articles_cluster',
        'ai_processed_articles',
        'ai_semantic_clusters',
        ['cluster_id'],
        ['id'],
        source_schema='crypto_news_scraper',
        referent_schema='crypto_news_scraper',
        ondelete='SET NULL'
    )
    
    # 4. Crear tabla ai_content_chunks
    op.create_table(
        'ai_content_chunks',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('article_id', sa.String(255), nullable=False, comment='ID del artículo original'),
        sa.Column('processed_article_id', postgresql.UUID(as_uuid=True), nullable=False, comment='ID del artículo procesado'),
        
        # Contenido
        sa.Column('content', sa.Text, nullable=False, comment='Contenido del chunk'),
        sa.Column('summary', sa.Text, nullable=True, comment='Resumen del chunk (3-5 frases)'),
        
        # Embedding vectorial (768 dimensiones para nomic-embed-text)
        # Nota: pgvector usa tipo VECTOR, pero SQLAlchemy no lo soporta nativamente
        # Lo creamos como ARRAY de floats y luego lo convertimos
        sa.Column('embedding', postgresql.ARRAY(sa.Float), nullable=False, comment='Embedding vectorial (768D)'),
        
        # Posición en el artículo
        sa.Column('position', sa.Integer, nullable=False, comment='Posición del chunk (0-indexed)'),
        sa.Column('start_char', sa.Integer, nullable=False, comment='Índice de inicio en texto original'),
        sa.Column('end_char', sa.Integer, nullable=False, comment='Índice de fin en texto original'),
        
        # Metadata
        sa.Column('token_count', sa.Integer, nullable=False, comment='Número de tokens en el chunk'),
        sa.Column('source_url', sa.Text, nullable=False, comment='URL del artículo original'),
        
        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        
        schema='crypto_news_scraper',
        comment='Chunks de contenido con embeddings vectoriales'
    )
    
    # FK a processed_articles
    op.create_foreign_key(
        'fk_chunks_processed_article',
        'ai_content_chunks',
        'ai_processed_articles',
        ['processed_article_id'],
        ['id'],
        source_schema='crypto_news_scraper',
        referent_schema='crypto_news_scraper',
        ondelete='CASCADE'
    )
    
    # 5. Crear tabla ai_context_packs (opcional, para auditoría)
    op.create_table(
        'ai_context_packs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('query', sa.Text, nullable=False, comment='Query de búsqueda'),
        sa.Column('query_embedding', postgresql.ARRAY(sa.Float), nullable=False, comment='Embedding del query (768D)'),
        
        # Chunks recuperados
        sa.Column('chunk_ids', postgresql.JSONB, nullable=False, comment='IDs de chunks recuperados: [uuid]'),
        sa.Column('relevance_scores', postgresql.JSONB, nullable=False, comment='Scores de relevancia: [float]'),
        
        # Metadata
        sa.Column('total_tokens', sa.Integer, nullable=False, comment='Total de tokens en el context pack'),
        sa.Column('sources', postgresql.JSONB, nullable=True, comment='URLs de fuentes: [string]'),
        
        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        
        schema='crypto_news_scraper',
        comment='Context packs para RAG (auditoría)'
    )
    
    # 6. Crear índices
    
    # Índices en ai_processed_articles
    op.create_index(
        'idx_processed_articles_article_id',
        'ai_processed_articles',
        ['article_id'],
        schema='crypto_news_scraper'
    )
    op.create_index(
        'idx_processed_articles_cluster_id',
        'ai_processed_articles',
        ['cluster_id'],
        schema='crypto_news_scraper'
    )
    op.create_index(
        'idx_processed_articles_status',
        'ai_processed_articles',
        ['status'],
        schema='crypto_news_scraper'
    )
    
    # Índices en ai_content_chunks
    op.create_index(
        'idx_chunks_article_id',
        'ai_content_chunks',
        ['article_id'],
        schema='crypto_news_scraper'
    )
    op.create_index(
        'idx_chunks_processed_article_id',
        'ai_content_chunks',
        ['processed_article_id'],
        schema='crypto_news_scraper'
    )
    
    # Índice en ai_context_packs
    op.create_index(
        'idx_context_packs_created_at',
        'ai_context_packs',
        ['created_at'],
        schema='crypto_news_scraper'
    )
    
    # 7. Convertir columnas ARRAY a tipo VECTOR de pgvector
    # Esto debe hacerse con SQL directo porque SQLAlchemy no soporta VECTOR nativamente
    op.execute("""
        ALTER TABLE crypto_news_scraper.ai_semantic_clusters 
        ALTER COLUMN centroid TYPE vector(768) USING centroid::vector(768)
    """)
    
    op.execute("""
        ALTER TABLE crypto_news_scraper.ai_content_chunks 
        ALTER COLUMN embedding TYPE vector(768) USING embedding::vector(768)
    """)
    
    op.execute("""
        ALTER TABLE crypto_news_scraper.ai_context_packs 
        ALTER COLUMN query_embedding TYPE vector(768) USING query_embedding::vector(768)
    """)


def downgrade() -> None:
    """Elimina tablas de AI processing y extensión pgvector."""
    
    # Eliminar índices
    op.drop_index('idx_context_packs_created_at', table_name='ai_context_packs', schema='crypto_news_scraper')
    op.drop_index('idx_chunks_processed_article_id', table_name='ai_content_chunks', schema='crypto_news_scraper')
    op.drop_index('idx_chunks_article_id', table_name='ai_content_chunks', schema='crypto_news_scraper')
    op.drop_index('idx_processed_articles_status', table_name='ai_processed_articles', schema='crypto_news_scraper')
    op.drop_index('idx_processed_articles_cluster_id', table_name='ai_processed_articles', schema='crypto_news_scraper')
    op.drop_index('idx_processed_articles_article_id', table_name='ai_processed_articles', schema='crypto_news_scraper')
    
    # Eliminar tablas (en orden inverso por FKs)
    op.drop_table('ai_context_packs', schema='crypto_news_scraper')
    op.drop_table('ai_content_chunks', schema='crypto_news_scraper')
    op.drop_table('ai_processed_articles', schema='crypto_news_scraper')
    op.drop_table('ai_semantic_clusters', schema='crypto_news_scraper')
    
    # Eliminar extensión pgvector
    op.execute('DROP EXTENSION IF EXISTS vector')
