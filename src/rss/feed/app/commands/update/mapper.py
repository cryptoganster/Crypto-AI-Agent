"""Mapper para UpdateSource command."""

from typing import Any, Dict

from src.rss.feed.domain.aggregates import Source


class UpdateSourceMapper:
    """
    Mapper específico para UpdateSource command.

    Serializa Source aggregates a DTOs para UpdateSourceResult.

    Responsabilidades:
    - Serializar Source a DTO resumido para capturar estado antes/después
    - Convertir Value Objects a primitivos
    - NO contiene lógica de negocio
    """

    @staticmethod
    def source_to_summary(source: Source) -> Dict[str, Any]:
        """
        Serializa Source a DTO resumido.

        Usado para capturar estado antes/después de actualización en UpdateSourceResult.

        Args:
            source: Source aggregate del dominio

        Returns:
            Dict con datos resumidos del source

        Example:
            >>> source = Source(id="src-123", name="Test Source", ...)
            >>> dto = UpdateSourceMapper.source_to_summary(source)
            >>> dto["id"]
            'src-123'
        """
        return {
            "id": str(source.id),
            "name": str(source.name),
            "url": str(source.url),
            "description": str(source.description) if source.description else None,
            "status": str(source.status),
            "is_active": source.is_active,
            "success_rate": source.metrics.success_rate if source.metrics else 0.0,
            "updated_at": source.updated_at.isoformat(),
        }
