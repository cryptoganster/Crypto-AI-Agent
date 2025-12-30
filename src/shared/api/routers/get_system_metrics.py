"""Get system metrics endpoint."""

from typing import Any, Dict

from fastapi import Depends, HTTPException, status

from src.rss.article.app.queries import GetQualityMetricsQuery

from .dependencies import get_system_container


async def get_system_metrics(system=Depends(get_system_container)) -> Dict[str, Any]:
    """
    **Query:** Multiple query adapters + Query Handlers (CQRS Read Side)

    Obtiene métricas agregadas del sistema.
    Usa el nuevo GetQualityMetricsHandler para métricas de calidad.
    """
    try:
        sources_adapter = system.infra.query_adapters.get_sources_list_adapter()
        articles_adapter = system.infra.query_adapters.get_count_articles_adapter()
        fetch_adapter = system.infra.query_adapters.get_count_fetch_sessions_adapter()

        # Usar el nuevo query handler para métricas de calidad
        quality_handler = system.articles.get_quality_metrics_handler()

        total_sources = await sources_adapter.count_all()
        total_articles = await articles_adapter.total()
        articles_24h = await articles_adapter.recent(hours=24)
        articles_7d = await articles_adapter.recent(hours=168)

        total_sessions = await fetch_adapter.count_total()
        completed_sessions = await fetch_adapter.count_by_status("COMPLETED")

        # Obtener métricas de calidad usando el handler
        quality_query = GetQualityMetricsQuery(hours=168)  # Últimos 7 días
        quality_metrics = await quality_handler.handle(quality_query)

        return {
            "sources": {"total": total_sources, "active": 0},
            "articles": {
                "total": total_articles,
                "last_24h": articles_24h,
                "last_7d": articles_7d,
            },
            "fetch_sessions": {
                "total": total_sessions,
                "completed": completed_sessions,
                "success_rate": (
                    completed_sessions / total_sessions if total_sessions > 0 else 0
                ),
            },
            "quality": {"average_score": quality_metrics.average_score},
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )
