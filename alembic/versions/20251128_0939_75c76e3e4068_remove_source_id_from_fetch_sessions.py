"""remove_source_id_from_fetch_sessions

Revision ID: 75c76e3e4068
Revises: 97afae804420
Create Date: 2025-11-28 09:39:45.165449

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '75c76e3e4068'
down_revision: Union[str, None] = '97afae804420'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Elimina source_id de fetch_sessions.
    
    FetchSession usa sources_to_fetch (ARRAY) para múltiples sources,
    por lo que source_id singular es redundante y confuso.
    """
    # Eliminar columna source_id
    op.drop_column(
        'fetch_sessions',
        'source_id',
        schema='crypto_news_scraper'
    )


def downgrade() -> None:
    """Restaura source_id como nullable."""
    # Agregar columna source_id como nullable
    op.add_column(
        'fetch_sessions',
        sa.Column(
            'source_id',
            sa.String(),
            nullable=True,
            comment='ID de la fuente RSS principal (legacy, usar sources_to_fetch)'
        ),
        schema='crypto_news_scraper'
    )
    
    # Crear índice
    op.create_index(
        'ix_fetch_sessions_source_id',
        'fetch_sessions',
        ['source_id'],
        schema='crypto_news_scraper'
    )
