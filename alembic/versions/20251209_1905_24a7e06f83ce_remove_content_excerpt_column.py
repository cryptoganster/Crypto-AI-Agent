"""remove_content_excerpt_column

Revision ID: 24a7e06f83ce
Revises: rename_scrapped_to_scraped
Create Date: 2025-12-09 19:05:15.336490

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '24a7e06f83ce'
down_revision: Union[str, None] = 'rename_scrapped_to_scraped'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Elimina columna content_excerpt de tabla articles."""
    op.drop_column('articles', 'content_excerpt', schema='crypto_news_scraper')


def downgrade() -> None:
    """Restaura columna content_excerpt."""
    op.add_column(
        'articles',
        sa.Column('content_excerpt', sa.Text(), nullable=True, comment='Extracto del contenido para preview'),
        schema='crypto_news_scraper'
    )
