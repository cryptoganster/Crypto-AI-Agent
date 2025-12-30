"""PaginatedResponse schema."""

from typing import Generic, List, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    """Response paginado genérico."""

    items: List[T] = Field(..., description="Lista de items")
    total: int = Field(..., ge=0, description="Total de items disponibles")
    limit: int = Field(..., ge=1, le=1000, description="Límite de items por página")
    offset: int = Field(..., ge=0, description="Offset de la página actual")
    has_more: bool = Field(..., description="Indica si hay más páginas")

    @classmethod
    def create(
        cls, items: List[T], total: int, limit: int, offset: int
    ) -> "PaginatedResponse[T]":
        """Factory method para crear respuesta paginada."""
        return cls(
            items=items,
            total=total,
            limit=limit,
            offset=offset,
            has_more=(offset + limit) < total,
        )
