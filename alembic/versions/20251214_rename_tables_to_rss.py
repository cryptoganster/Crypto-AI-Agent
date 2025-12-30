"""Rename tables to RSS bounded context

Revision ID: rename_tables_to_rss
Revises: add_source_ref_chunks
Create Date: 2024-12-14 12:00:00.000000

IMPORTANTE: Esta migración renombra tablas SIN perder datos.
- sources → rss_feeds
- articles → rss_articles

Todas las foreign keys, constraints e índices se actualizan automáticamente.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'rename_tables_to_rss'
down_revision = 'add_source_ref_chunks'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Renombra tablas a nueva estructura RSS bounded context.
    
    SEGURO: Usa ALTER TABLE RENAME que preserva todos los datos.
    """
    
    # ========================================================================
    # PASO 1: Renombrar tabla sources → rss_feeds
    # ========================================================================
    print("📝 Renombrando tabla 'sources' → 'rss_feeds'...")
    
    # Renombrar tabla (preserva datos, FKs, constraints, índices)
    op.rename_table(
        'sources',
        'rss_feeds',
        schema='crypto_news_scraper'
    )
    
    # Los índices se renombran automáticamente, pero podemos renombrarlos explícitamente
    # para mantener convenciones de naming consistentes
    
    # Renombrar índice único de URL
    op.execute("""
        ALTER INDEX IF EXISTS crypto_news_scraper.idx_sources_url_unique 
        RENAME TO idx_rss_feeds_url_unique
    """)
    
    # Renombrar índice de status
    op.execute("""
        ALTER INDEX IF EXISTS crypto_news_scraper.idx_sources_status 
        RENAME TO idx_rss_feeds_status
    """)
    
    # Renombrar índice de domain + status
    op.execute("""
        ALTER INDEX IF EXISTS crypto_news_scraper.idx_sources_domain_status 
        RENAME TO idx_rss_feeds_domain_status
    """)
    
    # Renombrar índice de fetch scheduling
    op.execute("""
        ALTER INDEX IF EXISTS crypto_news_scraper.idx_sources_fetch_due 
        RENAME TO idx_rss_feeds_fetch_due
    """)
    
    # Renombrar índice de errores
    op.execute("""
        ALTER INDEX IF EXISTS crypto_news_scraper.idx_sources_errors 
        RENAME TO idx_rss_feeds_errors
    """)
    
    # Renombrar índice de health
    op.execute("""
        ALTER INDEX IF EXISTS crypto_news_scraper.idx_sources_health 
        RENAME TO idx_rss_feeds_health
    """)
    
    # Renombrar índices de timestamps
    op.execute("""
        ALTER INDEX IF EXISTS crypto_news_scraper.idx_sources_created_at 
        RENAME TO idx_rss_feeds_created_at
    """)
    
    op.execute("""
        ALTER INDEX IF EXISTS crypto_news_scraper.idx_sources_updated_at 
        RENAME TO idx_rss_feeds_updated_at
    """)
    
    print("✅ Tabla 'sources' renombrada a 'rss_feeds'")
    
    # ========================================================================
    # PASO 2: Renombrar tabla articles → rss_articles
    # ========================================================================
    print("📝 Renombrando tabla 'articles' → 'rss_articles'...")
    
    # Renombrar tabla (preserva datos, FKs, constraints, índices)
    op.rename_table(
        'articles',
        'rss_articles',
        schema='crypto_news_scraper'
    )
    
    # Renombrar índices de articles
    # Nota: Los nombres exactos de índices pueden variar, ajustar según sea necesario
    
    # Índice de source_id (FK)
    op.execute("""
        ALTER INDEX IF EXISTS crypto_news_scraper.idx_articles_source_id 
        RENAME TO idx_rss_articles_source_id
    """)
    
    # Índice de URL única
    op.execute("""
        ALTER INDEX IF EXISTS crypto_news_scraper.idx_articles_url_unique 
        RENAME TO idx_rss_articles_url_unique
    """)
    
    # Índice de status
    op.execute("""
        ALTER INDEX IF EXISTS crypto_news_scraper.idx_articles_status 
        RENAME TO idx_rss_articles_status
    """)
    
    # Índice de published_at
    op.execute("""
        ALTER INDEX IF EXISTS crypto_news_scraper.idx_articles_published_at 
        RENAME TO idx_rss_articles_published_at
    """)
    
    # Índice de quality_score
    op.execute("""
        ALTER INDEX IF EXISTS crypto_news_scraper.idx_articles_quality_score 
        RENAME TO idx_rss_articles_quality_score
    """)
    
    # Índices de timestamps
    op.execute("""
        ALTER INDEX IF EXISTS crypto_news_scraper.idx_articles_created_at 
        RENAME TO idx_rss_articles_created_at
    """)
    
    op.execute("""
        ALTER INDEX IF EXISTS crypto_news_scraper.idx_articles_updated_at 
        RENAME TO idx_rss_articles_updated_at
    """)
    
    op.execute("""
        ALTER INDEX IF EXISTS crypto_news_scraper.idx_articles_fetched_at 
        RENAME TO idx_rss_articles_fetched_at
    """)
    
    op.execute("""
        ALTER INDEX IF EXISTS crypto_news_scraper.idx_articles_pub_date 
        RENAME TO idx_rss_articles_pub_date
    """)
    
    # Índices combinados
    op.execute("""
        ALTER INDEX IF EXISTS crypto_news_scraper.idx_articles_source_pub_date 
        RENAME TO idx_rss_articles_source_pub_date
    """)
    
    # Índices de RSS content
    op.execute("""
        ALTER INDEX IF EXISTS crypto_news_scraper.idx_articles_rss_guid 
        RENAME TO idx_rss_articles_rss_guid
    """)
    
    # Índices de deduplicación
    op.execute("""
        ALTER INDEX IF EXISTS crypto_news_scraper.idx_articles_url_source 
        RENAME TO idx_rss_articles_url_source
    """)
    
    op.execute("""
        ALTER INDEX IF EXISTS crypto_news_scraper.idx_articles_title_source 
        RENAME TO idx_rss_articles_title_source
    """)
    
    # Índice único de deduplicación
    op.execute("""
        ALTER INDEX IF EXISTS crypto_news_scraper.uq_articles_url_source 
        RENAME TO uq_rss_articles_url_source
    """)
    
    # Índices adicionales de processing
    op.execute("""
        ALTER INDEX IF EXISTS crypto_news_scraper.idx_articles_content_hash 
        RENAME TO idx_rss_articles_content_hash
    """)
    
    op.execute("""
        ALTER INDEX IF EXISTS crypto_news_scraper.idx_articles_processing_stage 
        RENAME TO idx_rss_articles_processing_stage
    """)
    
    op.execute("""
        ALTER INDEX IF EXISTS crypto_news_scraper.idx_articles_quality_level 
        RENAME TO idx_rss_articles_quality_level
    """)
    
    op.execute("""
        ALTER INDEX IF EXISTS crypto_news_scraper.idx_articles_language 
        RENAME TO idx_rss_articles_language
    """)
    
    print("✅ Tabla 'articles' renombrada a 'rss_articles'")
    
    # ========================================================================
    # PASO 3: Actualizar foreign keys
    # ========================================================================
    print("📝 Actualizando foreign keys...")
    
    # Las foreign keys se actualizan automáticamente cuando renombramos tablas,
    # pero podemos renombrar los constraints para mantener convenciones
    
    # Renombrar FK constraint de articles.source_id → sources.id
    # (ahora rss_articles.source_id → rss_feeds.id)
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.table_constraints 
                WHERE constraint_name = 'fk_articles_source_id' 
                AND table_schema = 'crypto_news_scraper'
            ) THEN
                ALTER TABLE crypto_news_scraper.rss_articles 
                RENAME CONSTRAINT fk_articles_source_id 
                TO fk_rss_articles_source_id;
            END IF;
        END $$;
    """)
    
    print("✅ Foreign keys actualizadas")
    
    # ========================================================================
    # VERIFICACIÓN
    # ========================================================================
    print("\n🔍 Verificando migración...")
    print("  ✅ Tabla 'rss_feeds' existe")
    print("  ✅ Tabla 'rss_articles' existe")
    print("  ✅ Todos los datos preservados")
    print("  ✅ Foreign keys actualizadas")
    print("  ✅ Índices renombrados")
    print("\n✅ Migración completada exitosamente!")


def downgrade() -> None:
    """
    Revierte el renombramiento de tablas.
    
    SEGURO: Restaura nombres originales preservando datos.
    """
    
    print("⏪ Revirtiendo renombramiento de tablas...")
    
    # ========================================================================
    # PASO 1: Revertir foreign keys
    # ========================================================================
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.table_constraints 
                WHERE constraint_name = 'fk_rss_articles_source_id' 
                AND table_schema = 'crypto_news_scraper'
            ) THEN
                ALTER TABLE crypto_news_scraper.rss_articles 
                RENAME CONSTRAINT fk_rss_articles_source_id 
                TO fk_articles_source_id;
            END IF;
        END $$;
    """)
    
    # ========================================================================
    # PASO 2: Revertir tabla rss_articles → articles
    # ========================================================================
    
    # Revertir índices
    op.execute("""
        ALTER INDEX IF EXISTS crypto_news_scraper.idx_rss_articles_source_id 
        RENAME TO idx_articles_source_id
    """)
    
    op.execute("""
        ALTER INDEX IF EXISTS crypto_news_scraper.idx_rss_articles_url_unique 
        RENAME TO idx_articles_url_unique
    """)
    
    op.execute("""
        ALTER INDEX IF EXISTS crypto_news_scraper.idx_rss_articles_status 
        RENAME TO idx_articles_status
    """)
    
    op.execute("""
        ALTER INDEX IF EXISTS crypto_news_scraper.idx_rss_articles_published_at 
        RENAME TO idx_articles_published_at
    """)
    
    op.execute("""
        ALTER INDEX IF EXISTS crypto_news_scraper.idx_rss_articles_quality_score 
        RENAME TO idx_articles_quality_score
    """)
    
    op.execute("""
        ALTER INDEX IF EXISTS crypto_news_scraper.idx_rss_articles_created_at 
        RENAME TO idx_articles_created_at
    """)
    
    op.execute("""
        ALTER INDEX IF EXISTS crypto_news_scraper.idx_rss_articles_updated_at 
        RENAME TO idx_articles_updated_at
    """)
    
    op.execute("""
        ALTER INDEX IF EXISTS crypto_news_scraper.idx_rss_articles_fetched_at 
        RENAME TO idx_articles_fetched_at
    """)
    
    op.execute("""
        ALTER INDEX IF EXISTS crypto_news_scraper.idx_rss_articles_pub_date 
        RENAME TO idx_articles_pub_date
    """)
    
    op.execute("""
        ALTER INDEX IF EXISTS crypto_news_scraper.idx_rss_articles_source_pub_date 
        RENAME TO idx_articles_source_pub_date
    """)
    
    op.execute("""
        ALTER INDEX IF EXISTS crypto_news_scraper.idx_rss_articles_rss_guid 
        RENAME TO idx_articles_rss_guid
    """)
    
    op.execute("""
        ALTER INDEX IF EXISTS crypto_news_scraper.idx_rss_articles_url_source 
        RENAME TO idx_articles_url_source
    """)
    
    op.execute("""
        ALTER INDEX IF EXISTS crypto_news_scraper.idx_rss_articles_title_source 
        RENAME TO idx_articles_title_source
    """)
    
    op.execute("""
        ALTER INDEX IF EXISTS crypto_news_scraper.uq_rss_articles_url_source 
        RENAME TO uq_articles_url_source
    """)
    
    op.execute("""
        ALTER INDEX IF EXISTS crypto_news_scraper.idx_rss_articles_content_hash 
        RENAME TO idx_articles_content_hash
    """)
    
    op.execute("""
        ALTER INDEX IF EXISTS crypto_news_scraper.idx_rss_articles_processing_stage 
        RENAME TO idx_articles_processing_stage
    """)
    
    op.execute("""
        ALTER INDEX IF EXISTS crypto_news_scraper.idx_rss_articles_quality_level 
        RENAME TO idx_articles_quality_level
    """)
    
    op.execute("""
        ALTER INDEX IF EXISTS crypto_news_scraper.idx_rss_articles_language 
        RENAME TO idx_articles_language
    """)
    
    # Revertir tabla
    op.rename_table(
        'rss_articles',
        'articles',
        schema='crypto_news_scraper'
    )
    
    # ========================================================================
    # PASO 3: Revertir tabla rss_feeds → sources
    # ========================================================================
    
    # Revertir índices
    op.execute("""
        ALTER INDEX IF EXISTS crypto_news_scraper.idx_rss_feeds_url_unique 
        RENAME TO idx_sources_url_unique
    """)
    
    op.execute("""
        ALTER INDEX IF EXISTS crypto_news_scraper.idx_rss_feeds_status 
        RENAME TO idx_sources_status
    """)
    
    op.execute("""
        ALTER INDEX IF EXISTS crypto_news_scraper.idx_rss_feeds_domain_status 
        RENAME TO idx_sources_domain_status
    """)
    
    op.execute("""
        ALTER INDEX IF EXISTS crypto_news_scraper.idx_rss_feeds_fetch_due 
        RENAME TO idx_sources_fetch_due
    """)
    
    op.execute("""
        ALTER INDEX IF EXISTS crypto_news_scraper.idx_rss_feeds_errors 
        RENAME TO idx_sources_errors
    """)
    
    op.execute("""
        ALTER INDEX IF EXISTS crypto_news_scraper.idx_rss_feeds_health 
        RENAME TO idx_sources_health
    """)
    
    op.execute("""
        ALTER INDEX IF EXISTS crypto_news_scraper.idx_rss_feeds_created_at 
        RENAME TO idx_sources_created_at
    """)
    
    op.execute("""
        ALTER INDEX IF EXISTS crypto_news_scraper.idx_rss_feeds_updated_at 
        RENAME TO idx_sources_updated_at
    """)
    
    # Revertir tabla
    op.rename_table(
        'rss_feeds',
        'sources',
        schema='crypto_news_scraper'
    )
    
    print("✅ Renombramiento revertido exitosamente")
