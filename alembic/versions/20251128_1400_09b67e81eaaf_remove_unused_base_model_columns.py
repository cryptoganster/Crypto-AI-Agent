"""remove_unused_base_model_columns

Elimina columnas no utilizadas del BaseModel:
- is_deleted, deleted_at, deleted_by (soft delete)
- created_by, updated_by (auditoría de usuario)
- metadata_json (metadatos extensibles)

Estas columnas no se usan en la lógica de negocio y agregan complejidad innecesaria.

Revision ID: 09b67e81eaaf
Revises: 75c76e3e4068
Create Date: 2025-11-28 14:00:10.045008

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '09b67e81eaaf'
down_revision: Union[str, None] = '75c76e3e4068'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Elimina columnas no utilizadas de todas las tablas que heredan de BaseModel.
    
    Columnas a eliminar:
    - is_deleted, deleted_at, deleted_by (soft delete no utilizado)
    - created_by, updated_by (auditoría de usuario no utilizada)
    - metadata_json (metadatos extensibles no utilizados)
    """
    # Lista de tablas que heredan de BaseModel
    tables = [
        'sources',
        'fetch_sessions',
    ]
    
    schema = 'crypto_news_scraper'
    
    for table in tables:
        # Eliminar columnas de soft delete
        op.drop_column(table, 'is_deleted', schema=schema)
        op.drop_column(table, 'deleted_at', schema=schema)
        op.drop_column(table, 'deleted_by', schema=schema)
        
        # Eliminar columnas de auditoría de usuario
        op.drop_column(table, 'created_by', schema=schema)
        op.drop_column(table, 'updated_by', schema=schema)
        
        # Eliminar metadata_json
        op.drop_column(table, 'metadata_json', schema=schema)


def downgrade() -> None:
    """
    Restaura las columnas eliminadas en caso de rollback.
    
    NOTA: Los datos de estas columnas se perderán permanentemente.
    Solo se restaura la estructura de las columnas.
    """
    tables = [
        'sources',
        'fetch_sessions',
    ]
    
    schema = 'crypto_news_scraper'
    
    for table in tables:
        # Restaurar columnas de soft delete
        op.add_column(
            table,
            sa.Column('is_deleted', sa.Boolean(), server_default='false', nullable=False),
            schema=schema
        )
        op.add_column(
            table,
            sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
            schema=schema
        )
        op.add_column(
            table,
            sa.Column('deleted_by', sa.String(255), nullable=True),
            schema=schema
        )
        
        # Restaurar columnas de auditoría de usuario
        op.add_column(
            table,
            sa.Column('created_by', sa.String(255), nullable=True),
            schema=schema
        )
        op.add_column(
            table,
            sa.Column('updated_by', sa.String(255), nullable=True),
            schema=schema
        )
        
        # Restaurar metadata_json
        op.add_column(
            table,
            sa.Column('metadata_json', postgresql.JSONB(), nullable=True),
            schema=schema
        )
