"""fix_rss_articles_foreign_key_to_rss_feeds

Revision ID: 4d3daa9b25f6
Revises: rename_tables_to_rss
Create Date: 2025-12-15 00:54:20.923417

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4d3daa9b25f6'
down_revision: Union[str, None] = 'rename_tables_to_rss'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Corrige la foreign key de rss_articles.source_id para que apunte a rss_feeds.id
    en lugar de sources.id (que no existe).
    """
    # 1. Intentar eliminar la foreign key constraint incorrecta si existe
    # Usamos batch_alter_table con if_exists para evitar errores
    with op.batch_alter_table('rss_articles', schema='crypto_news_scraper') as batch_op:
        # Intentar eliminar cualquier constraint existente en source_id
        # Nota: El nombre puede variar, así que usamos try/except en el código SQL directo
        pass
    
    # 2. Ejecutar SQL directo para eliminar cualquier constraint en source_id (si existe)
    op.execute("""
        DO $$ 
        BEGIN
            -- Eliminar constraint si existe
            IF EXISTS (
                SELECT 1 FROM information_schema.table_constraints 
                WHERE constraint_name = 'rss_articles_source_id_fkey' 
                AND table_schema = 'crypto_news_scraper'
                AND table_name = 'rss_articles'
            ) THEN
                ALTER TABLE crypto_news_scraper.rss_articles 
                DROP CONSTRAINT rss_articles_source_id_fkey;
            END IF;
        END $$;
    """)
    
    # 3. Crear la foreign key correcta apuntando a rss_feeds
    op.create_foreign_key(
        'rss_articles_source_id_fkey',
        'rss_articles',
        'rss_feeds',
        ['source_id'],
        ['id'],
        source_schema='crypto_news_scraper',
        referent_schema='crypto_news_scraper',
        ondelete='CASCADE'
    )


def downgrade() -> None:
    """
    Revierte la corrección de la foreign key.
    Nota: No podemos revertir a 'sources' porque esa tabla no existe.
    """
    # Eliminar la foreign key correcta
    op.drop_constraint(
        'rss_articles_source_id_fkey',
        'rss_articles',
        schema='crypto_news_scraper',
        type_='foreignkey'
    )
    
    # No recreamos la constraint incorrecta porque la tabla 'sources' no existe
