"""add_markdown_without_url_to_articles

Revision ID: 9dc9f48003f5
Revises: create_hnsw_indexes
Create Date: 2025-12-11 20:35:39.966390

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9dc9f48003f5'
down_revision: Union[str, None] = 'create_hnsw_indexes'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Agrega campo markdown_without_url a tabla articles."""
    op.add_column(
        'articles',
        sa.Column(
            'markdown_without_url',
            sa.Text(),
            nullable=True,
            comment='Contenido en formato Markdown sin URLs (para procesamiento AI/ML)',
        ),
        schema='crypto_news_scraper'
    )


def downgrade() -> None:
    """Remueve campo markdown_without_url de tabla articles."""
    op.drop_column('articles', 'markdown_without_url', schema='crypto_news_scraper')
