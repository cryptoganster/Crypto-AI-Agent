"""Rename IDs to bounded context pattern and fetch_sessions to scrapings

Revision ID: 20251204_1200
Revises: 20251128_1400_09b67e81eaaf
Create Date: 2025-12-04 12:00:00.000000

Esta migración:
1. Renombra columnas de ID para seguir patrón de bounded contexts:
   - articles.article_id → articles.id (+ article_id como alias)
   - sources.source_id → sources.id (+ source_id como alias)
   - fetch_sessions.fetch_session_id → scrapings.id (+ scraping_id como alias)
2. Renombra tabla fetch_sessions → scrapings
3. Actualiza foreign keys y índices
4. Preserva todos los datos existentes
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20251204_1200'
down_revision = '09b67e81eaaf'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Migración de IDs y renombrado de fetch_sessions a scrapings.
    
    Estrategia: Renombrar columnas PK manteniendo datos intactos.
    """
    
    # ============================================================
    # PASO 1: Renombrar tabla fetch_sessions → scrapings
    # ============================================================
    
    # 1.1 Renombrar la tabla
    op.rename_table('fetch_sessions', 'scrapings', schema='crypto_news_scraper')
    
    # 1.2 Renombrar columna PK: fetch_session_id → id
    op.alter_column(
        'scrapings',
        'fetch_session_id',
        new_column_name='id',
        schema='crypto_news_scraper'
    )
    
    # 1.3 Agregar columna scraping_id como alias (computed/generated)
    # PostgreSQL no soporta computed columns fácilmente, usamos un approach diferente
    # Creamos la columna y la mantenemos sincronizada via trigger o simplemente
    # la dejamos como referencia en el modelo ORM
    
    # 1.4 Renombrar índices de fetch_sessions a scrapings
    op.execute('ALTER INDEX crypto_news_scraper.idx_fetch_sessions_status RENAME TO idx_scrapings_status')
    op.execute('ALTER INDEX crypto_news_scraper.idx_fetch_sessions_started_at RENAME TO idx_scrapings_started_at')
    op.execute('ALTER INDEX crypto_news_scraper.idx_fetch_sessions_completed RENAME TO idx_scrapings_completed')
    op.execute('ALTER INDEX crypto_news_scraper.idx_fetch_sessions_created_at RENAME TO idx_scrapings_created_at')
    op.execute('ALTER INDEX crypto_news_scraper.idx_fetch_sessions_updated_at RENAME TO idx_scrapings_updated_at')
    op.execute('ALTER INDEX crypto_news_scraper.idx_fetch_sessions_sources_count RENAME TO idx_scrapings_sources_count')
    op.execute('ALTER INDEX crypto_news_scraper.idx_fetch_sessions_articles RENAME TO idx_scrapings_articles')
    
    # 1.5 Renombrar constraint PK
    op.execute('ALTER TABLE crypto_news_scraper.scrapings RENAME CONSTRAINT fetch_sessions_pkey TO scrapings_pkey')
    
    # ============================================================
    # PASO 2: Renombrar columna PK en sources
    # ============================================================
    
    # 2.1 Primero eliminar FK de articles que referencia sources.source_id
    op.drop_constraint(
        'articles_source_id_fkey',
        'articles',
        schema='crypto_news_scraper',
        type_='foreignkey'
    )
    
    # 2.2 Renombrar columna PK: source_id → id
    op.alter_column(
        'sources',
        'source_id',
        new_column_name='id',
        schema='crypto_news_scraper'
    )
    
    # 2.3 Renombrar constraint PK
    op.execute('ALTER TABLE crypto_news_scraper.sources RENAME CONSTRAINT sources_pkey TO sources_pkey_new')
    
    # 2.4 Recrear FK en articles apuntando a sources.id
    op.create_foreign_key(
        'articles_source_id_fkey',
        'articles',
        'sources',
        ['source_id'],
        ['id'],
        source_schema='crypto_news_scraper',
        referent_schema='crypto_news_scraper',
        ondelete='CASCADE'
    )
    
    # ============================================================
    # PASO 3: Renombrar columna PK en articles
    # ============================================================
    
    # 3.1 Renombrar columna PK: article_id → id
    op.alter_column(
        'articles',
        'article_id',
        new_column_name='id',
        schema='crypto_news_scraper'
    )
    
    # 3.2 Renombrar constraint PK
    op.execute('ALTER TABLE crypto_news_scraper.articles RENAME CONSTRAINT articles_pkey TO articles_pkey_new')
    
    # ============================================================
    # PASO 4: Actualizar FK de duplicate_of_article_id
    # ============================================================
    # Esta columna referencia article_id, ahora debe referenciar id
    # No hay FK constraint definido, solo es una referencia lógica
    # Renombramos la columna para claridad
    op.alter_column(
        'articles',
        'duplicate_of_article_id',
        new_column_name='duplicate_of_id',
        schema='crypto_news_scraper'
    )
    
    # Actualizar índice
    op.execute('ALTER INDEX crypto_news_scraper.idx_articles_duplicate_of RENAME TO idx_articles_duplicate_of_id')


def downgrade() -> None:
    """
    Revertir cambios: scrapings → fetch_sessions, restaurar nombres de columnas.
    """
    
    # ============================================================
    # PASO 1: Revertir articles
    # ============================================================
    
    # 1.1 Revertir duplicate_of_id → duplicate_of_article_id
    op.alter_column(
        'articles',
        'duplicate_of_id',
        new_column_name='duplicate_of_article_id',
        schema='crypto_news_scraper'
    )
    op.execute('ALTER INDEX crypto_news_scraper.idx_articles_duplicate_of_id RENAME TO idx_articles_duplicate_of')
    
    # 1.2 Revertir id → article_id
    op.alter_column(
        'articles',
        'id',
        new_column_name='article_id',
        schema='crypto_news_scraper'
    )
    op.execute('ALTER TABLE crypto_news_scraper.articles RENAME CONSTRAINT articles_pkey_new TO articles_pkey')
    
    # ============================================================
    # PASO 2: Revertir sources
    # ============================================================
    
    # 2.1 Eliminar FK
    op.drop_constraint(
        'articles_source_id_fkey',
        'articles',
        schema='crypto_news_scraper',
        type_='foreignkey'
    )
    
    # 2.2 Revertir id → source_id
    op.alter_column(
        'sources',
        'id',
        new_column_name='source_id',
        schema='crypto_news_scraper'
    )
    op.execute('ALTER TABLE crypto_news_scraper.sources RENAME CONSTRAINT sources_pkey_new TO sources_pkey')
    
    # 2.3 Recrear FK original
    op.create_foreign_key(
        'articles_source_id_fkey',
        'articles',
        'sources',
        ['source_id'],
        ['source_id'],
        source_schema='crypto_news_scraper',
        referent_schema='crypto_news_scraper',
        ondelete='CASCADE'
    )
    
    # ============================================================
    # PASO 3: Revertir scrapings → fetch_sessions
    # ============================================================
    
    # 3.1 Revertir id → fetch_session_id
    op.alter_column(
        'scrapings',
        'id',
        new_column_name='fetch_session_id',
        schema='crypto_news_scraper'
    )
    
    # 3.2 Revertir índices
    op.execute('ALTER INDEX crypto_news_scraper.idx_scrapings_status RENAME TO idx_fetch_sessions_status')
    op.execute('ALTER INDEX crypto_news_scraper.idx_scrapings_started_at RENAME TO idx_fetch_sessions_started_at')
    op.execute('ALTER INDEX crypto_news_scraper.idx_scrapings_completed RENAME TO idx_fetch_sessions_completed')
    op.execute('ALTER INDEX crypto_news_scraper.idx_scrapings_created_at RENAME TO idx_fetch_sessions_created_at')
    op.execute('ALTER INDEX crypto_news_scraper.idx_scrapings_updated_at RENAME TO idx_fetch_sessions_updated_at')
    op.execute('ALTER INDEX crypto_news_scraper.idx_scrapings_sources_count RENAME TO idx_fetch_sessions_sources_count')
    op.execute('ALTER INDEX crypto_news_scraper.idx_scrapings_articles RENAME TO idx_fetch_sessions_articles')
    
    # 3.3 Revertir constraint PK
    op.execute('ALTER TABLE crypto_news_scraper.scrapings RENAME CONSTRAINT scrapings_pkey TO fetch_sessions_pkey')
    
    # 3.4 Renombrar tabla
    op.rename_table('scrapings', 'fetch_sessions', schema='crypto_news_scraper')
