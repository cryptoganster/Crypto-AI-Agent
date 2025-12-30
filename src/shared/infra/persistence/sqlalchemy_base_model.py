"""Base SQLAlchemy model con campos comunes y funcionalidades DDD.

Este módulo proporciona la clase base para todos los modelos ORM del proyecto,
incluyendo campos de auditoría y versionado optimista.

Uso:
    from src.shared.infra.persistence import Base, BaseModel

    class MyModel(BaseModel):
        __tablename__ = "my_table"
        my_id = Column(String, primary_key=True)
"""

from datetime import datetime, timezone
from typing import Any, Dict

from sqlalchemy import Column, DateTime, Integer, MetaData
from sqlalchemy.orm import declarative_base
from sqlalchemy.sql import func

# Configurar metadata con schema por defecto
metadata = MetaData(schema="crypto_news_scraper")
Base = declarative_base(metadata=metadata)


class BaseModel(Base):
    """
    Modelo base para todos los agregados con campos comunes DDD.

    Proporciona:
    - Timestamps de auditoría (created_at, updated_at)
    - Versionado optimista (version)

    NOTA: Cada modelo derivado debe definir su propia columna PK específica
    (source_id, article_id, fetch_session_id, etc.) para evitar ambigüedad.
    """

    __abstract__ = True
    __table_args__ = {"schema": "crypto_news_scraper"}

    # Timestamps de auditoría
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Versionado optimista para concurrencia
    version = Column(Integer, default=1, nullable=False)

    def update_version(self) -> None:
        """Incrementa la versión para control de concurrencia optimista."""
        if self.version is None:
            self.version = 1
        else:
            self.version += 1
        self.updated_at = datetime.now(timezone.utc)

    def to_dict(self) -> Dict[str, Any]:
        """Serializa el modelo a diccionario."""
        return {
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "version": self.version,
        }

    def __repr__(self) -> str:
        """Representación base - modelos derivados deben sobrescribir."""
        return f"<{self.__class__.__name__}(created_at={self.created_at})>"
