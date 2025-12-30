"""Rename content_scrapped to content_scraped

Revision ID: rename_scrapped_to_scraped
Revises: 
Create Date: 2025-12-07 19:45:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'rename_scrapped_to_scraped'
down_revision = '20251204_1200'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Renombra content_scrapped a content_scraped sin perder datos."""
    # Renombrar columna en la tabla articles
    op.alter_column(
        'articles',
        'content_scrapped',
        new_column_name='content_scraped',
        schema='crypto_news_scraper'
    )


def downgrade() -> None:
    """Revierte el cambio: content_scraped → content_scrapped."""
    # Renombrar de vuelta
    op.alter_column(
        'articles',
        'content_scraped',
        new_column_name='content_scrapped',
        schema='crypto_news_scraper'
    )
