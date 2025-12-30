"""make_fetch_sessions_source_id_nullable

Revision ID: 97afae804420
Revises: ab8984800ce7
Create Date: 2025-11-28 09:37:30.553340

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '97afae804420'
down_revision: Union[str, None] = 'ab8984800ce7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Hace source_id nullable en fetch_sessions.
    
    FetchSession puede procesar múltiples sources (sources_to_fetch array),
    por lo que source_id singular no es requerido.
    """
    # Hacer source_id nullable
    op.alter_column(
        'fetch_sessions',
        'source_id',
        existing_type=sa.String(),
        nullable=True,
        schema='crypto_news_scraper'
    )


def downgrade() -> None:
    """Revierte source_id a NOT NULL."""
    # Primero, actualizar registros con source_id NULL a un valor por defecto
    op.execute(
        "UPDATE crypto_news_scraper.fetch_sessions "
        "SET source_id = 'unknown' "
        "WHERE source_id IS NULL"
    )
    
    # Luego hacer la columna NOT NULL
    op.alter_column(
        'fetch_sessions',
        'source_id',
        existing_type=sa.String(),
        nullable=False,
        schema='crypto_news_scraper'
    )
