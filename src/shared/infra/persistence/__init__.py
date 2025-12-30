"""Shared infrastructure for persistence."""

from src.shared.infra.persistence.sqlalchemy_base_model import (
    Base,
    BaseModel,
)
from src.shared.infra.persistence.sqlalchemy_uow import (
    UnitOfWork,  # Alias for backward compatibility
)
from src.shared.infra.persistence.sqlalchemy_uow import (
    SqlAlchemyUnitOfWork,
)

__all__ = [
    # Base models
    "Base",
    "BaseModel",
    # Unit of Work
    "SqlAlchemyUnitOfWork",
    "UnitOfWork",
]
