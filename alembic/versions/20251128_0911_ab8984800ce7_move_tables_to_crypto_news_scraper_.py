"""move_tables_to_crypto_news_scraper_schema

Revision ID: ab8984800ce7
Revises: 20251122_2200
Create Date: 2025-11-28 09:11:27.641787

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ab8984800ce7'
down_revision: Union[str, None] = '20251122_2200'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Mueve las tablas del schema public a crypto_news_scraper."""
    
    # Crear schema si no existe
    op.execute("CREATE SCHEMA IF NOT EXISTS crypto_news_scraper")
    
    # Mover tablas al nuevo schema
    # Nota: Si las tablas ya existen en crypto_news_scraper, esto fallará
    # En ese caso, las tablas ya están en el lugar correcto
    
    # Verificar si las tablas existen en public antes de moverlas
    connection = op.get_bind()
    
    # Mover tabla sources
    result = connection.execute(sa.text(
        "SELECT EXISTS (SELECT 1 FROM information_schema.tables "
        "WHERE table_schema = 'public' AND table_name = 'sources')"
    ))
    if result.scalar():
        op.execute("ALTER TABLE public.sources SET SCHEMA crypto_news_scraper")
    
    # Mover tabla articles
    result = connection.execute(sa.text(
        "SELECT EXISTS (SELECT 1 FROM information_schema.tables "
        "WHERE table_schema = 'public' AND table_name = 'articles')"
    ))
    if result.scalar():
        op.execute("ALTER TABLE public.articles SET SCHEMA crypto_news_scraper")
    
    # Mover tabla fetch_sessions
    result = connection.execute(sa.text(
        "SELECT EXISTS (SELECT 1 FROM information_schema.tables "
        "WHERE table_schema = 'public' AND table_name = 'fetch_sessions')"
    ))
    if result.scalar():
        op.execute("ALTER TABLE public.fetch_sessions SET SCHEMA crypto_news_scraper")


def downgrade() -> None:
    """Revierte las tablas al schema public."""
    
    # Mover tablas de vuelta a public
    connection = op.get_bind()
    
    # Mover tabla sources
    result = connection.execute(sa.text(
        "SELECT EXISTS (SELECT 1 FROM information_schema.tables "
        "WHERE table_schema = 'crypto_news_scraper' AND table_name = 'sources')"
    ))
    if result.scalar():
        op.execute("ALTER TABLE crypto_news_scraper.sources SET SCHEMA public")
    
    # Mover tabla articles
    result = connection.execute(sa.text(
        "SELECT EXISTS (SELECT 1 FROM information_schema.tables "
        "WHERE table_schema = 'crypto_news_scraper' AND table_name = 'articles')"
    ))
    if result.scalar():
        op.execute("ALTER TABLE crypto_news_scraper.articles SET SCHEMA public")
    
    # Mover tabla fetch_sessions
    result = connection.execute(sa.text(
        "SELECT EXISTS (SELECT 1 FROM information_schema.tables "
        "WHERE table_schema = 'crypto_news_scraper' AND table_name = 'fetch_sessions')"
    ))
    if result.scalar():
        op.execute("ALTER TABLE crypto_news_scraper.fetch_sessions SET SCHEMA public")
