"""Add source_id and source_type to content_chunks

Revision ID: add_source_ref_chunks
Revises: 9dc9f48003f5
Create Date: 2024-12-13 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_source_ref_chunks'
down_revision = '9dc9f48003f5'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Agrega columnas source_id y source_type a ai_content_chunks.
    
    Migración:
    1. Agregar columnas source_id y source_type (nullable inicialmente)
    2. Copiar article_id a source_id
    3. Establecer source_type = 'rss_article' para todos los registros
    4. Hacer source_id y source_type NOT NULL
    5. Crear índices para búsquedas eficientes
    """
    # 1. Agregar columnas (nullable inicialmente)
    op.add_column(
        'ai_content_chunks',
        sa.Column('source_id', sa.String(), nullable=True),
        schema='crypto_news_scraper'
    )
    op.add_column(
        'ai_content_chunks',
        sa.Column('source_type', sa.String(), nullable=True),
        schema='crypto_news_scraper'
    )
    
    # 2. Copiar article_id a source_id
    op.execute("""
        UPDATE crypto_news_scraper.ai_content_chunks
        SET source_id = article_id
        WHERE source_id IS NULL
    """)
    
    # 3. Establecer source_type = 'rss_article'
    op.execute("""
        UPDATE crypto_news_scraper.ai_content_chunks
        SET source_type = 'rss_article'
        WHERE source_type IS NULL
    """)
    
    # 4. Hacer columnas NOT NULL
    op.alter_column(
        'ai_content_chunks',
        'source_id',
        nullable=False,
        schema='crypto_news_scraper'
    )
    op.alter_column(
        'ai_content_chunks',
        'source_type',
        nullable=False,
        schema='crypto_news_scraper'
    )
    
    # 5. Crear índices
    op.create_index(
        'ix_content_chunks_source_id',
        'ai_content_chunks',
        ['source_id'],
        schema='crypto_news_scraper'
    )
    op.create_index(
        'ix_content_chunks_source_type',
        'ai_content_chunks',
        ['source_type'],
        schema='crypto_news_scraper'
    )
    op.create_index(
        'ix_content_chunks_source_position',
        'ai_content_chunks',
        ['source_id', 'source_type', 'position'],
        schema='crypto_news_scraper'
    )


def downgrade() -> None:
    """
    Revierte la migración eliminando source_id y source_type.
    """
    # Eliminar índices
    op.drop_index('ix_content_chunks_source_position', table_name='ai_content_chunks', schema='crypto_news_scraper')
    op.drop_index('ix_content_chunks_source_type', table_name='ai_content_chunks', schema='crypto_news_scraper')
    op.drop_index('ix_content_chunks_source_id', table_name='ai_content_chunks', schema='crypto_news_scraper')
    
    # Eliminar columnas
    op.drop_column('ai_content_chunks', 'source_type', schema='crypto_news_scraper')
    op.drop_column('ai_content_chunks', 'source_id', schema='crypto_news_scraper')
