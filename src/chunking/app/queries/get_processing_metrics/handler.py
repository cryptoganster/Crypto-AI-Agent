"""Handler para GetProcessingMetricsQuery."""

from typing import Dict

from src.chunking.app.process_managers.article_ai_processing_pipeline import (
    ArticleAIProcessingPipeline,
)
from src.chunking.app.queries.get_processing_metrics.dto import ProcessingMetricsDTO
from src.chunking.app.queries.get_processing_metrics.query import (
    GetProcessingMetricsQuery,
)
from src.shared.kernel.logger import ILogger


class GetProcessingMetricsHandler:
    """
    Handler para GetProcessingMetricsQuery.

    Calcula métricas agregadas de procesamiento AI a través de
    múltiples artículos consultando el estado del Process Manager.

    Este es un query puro (CQRS) - NO modifica estado.

    Responsabilidades:
    - Consultar estado del Process Manager
    - Calcular métricas agregadas
    - Retornar DTO con métricas
    - NO modificar estado

    Example:
        >>> handler = GetProcessingMetricsHandler(pipeline, logger)
        >>> query = GetProcessingMetricsQuery()
        >>> metrics = await handler.handle(query)
        >>> print(metrics.total_articles_processed)
        150
    """

    def __init__(
        self,
        pipeline: ArticleAIProcessingPipeline,
        logger: ILogger,
    ):
        """
        Inicializa el handler.

        Args:
            pipeline: Process Manager con estado de pipelines
            logger: Logger para registrar operaciones
        """
        self._pipeline = pipeline
        self._logger = logger.bind(
            layer="application",
            component="GetProcessingMetricsHandler",
        )

    async def handle(self, query: GetProcessingMetricsQuery) -> ProcessingMetricsDTO:
        """
        Ejecuta la query de métricas de procesamiento.

        Calcula métricas agregadas consultando el estado del Process Manager.
        Aplica filtros de fecha y estado si se especifican.

        Args:
            query: Query con filtros opcionales

        Returns:
            DTO con métricas agregadas

        Example:
            >>> query = GetProcessingMetricsQuery()
            >>> metrics = await handler.handle(query)
            >>> metrics.success_rate_percentage
            93.5
        """
        self._logger.info(
            "Calculando métricas de procesamiento",
            start_date=query.start_date,
            end_date=query.end_date,
            state_filter=query.state_filter,
        )

        # Obtener todos los estados de pipelines activos
        pipeline_states = self._pipeline.get_all_pipeline_states()

        # Aplicar filtros
        filtered_states = self._apply_filters(
            pipeline_states,
            query.start_date,
            query.end_date,
            query.state_filter,
        )

        # Calcular métricas agregadas
        metrics = self._calculate_metrics(filtered_states)

        self._logger.info(
            "Métricas calculadas",
            total_articles=metrics.total_articles_processed,
            completed=metrics.articles_completed,
            failed=metrics.articles_failed,
            success_rate=f"{metrics.success_rate_percentage:.1f}%",
        )

        return metrics

    def _apply_filters(
        self,
        pipeline_states: Dict,
        start_date,
        end_date,
        state_filter,
    ) -> Dict:
        """
        Aplica filtros a los estados de pipeline.

        Args:
            pipeline_states: Diccionario de estados por article_id
            start_date: Fecha de inicio (opcional)
            end_date: Fecha de fin (opcional)
            state_filter: Filtro de estado (opcional)

        Returns:
            Diccionario filtrado de estados
        """
        filtered = {}

        for article_id, state in pipeline_states.items():
            # Filtrar por fecha
            if start_date and state.metrics.started_at:
                if state.metrics.started_at < start_date:
                    continue

            if end_date and state.metrics.started_at:
                if state.metrics.started_at > end_date:
                    continue

            # Filtrar por estado
            if state_filter and state.state.value != state_filter:
                continue

            filtered[article_id] = state

        return filtered

    def _calculate_metrics(self, pipeline_states: Dict) -> ProcessingMetricsDTO:
        """
        Calcula métricas agregadas desde los estados de pipeline.

        Args:
            pipeline_states: Diccionario de estados por article_id

        Returns:
            DTO con métricas calculadas
        """
        # Contadores
        total_articles = len(pipeline_states)
        articles_completed = 0
        articles_failed = 0
        articles_in_progress = 0

        total_chunks_created = 0
        total_chunks_embedded = 0
        total_chunks_summarized = 0
        total_chunks_completed = 0
        total_chunks_failed = 0

        total_processing_time = 0.0
        articles_with_duration = 0

        articles_by_state: Dict[str, int] = {}

        # Iterar sobre todos los estados
        for state in pipeline_states.values():
            # Contar por estado
            state_value = state.state.value
            articles_by_state[state_value] = articles_by_state.get(state_value, 0) + 1

            if state.state.value == "completed":
                articles_completed += 1
            elif state.state.value == "failed":
                articles_failed += 1
            else:
                articles_in_progress += 1

            # Sumar métricas de chunks
            total_chunks_created += state.metrics.chunks_created
            total_chunks_embedded += state.metrics.chunks_embedded
            total_chunks_summarized += state.metrics.chunks_summarized
            total_chunks_completed += state.metrics.chunks_completed
            total_chunks_failed += state.metrics.chunks_failed

            # Sumar tiempos de procesamiento
            if state.metrics.duration_seconds:
                total_processing_time += state.metrics.duration_seconds
                articles_with_duration += 1

        # Calcular promedios
        average_chunks_per_article = (
            total_chunks_created / total_articles if total_articles > 0 else 0.0
        )

        average_processing_time = (
            total_processing_time / articles_with_duration
            if articles_with_duration > 0
            else 0.0
        )

        # Calcular tasas
        success_rate = (
            articles_completed / total_articles if total_articles > 0 else 0.0
        )

        failure_rate = articles_failed / total_articles if total_articles > 0 else 0.0

        return ProcessingMetricsDTO(
            total_articles_processed=total_articles,
            articles_completed=articles_completed,
            articles_failed=articles_failed,
            articles_in_progress=articles_in_progress,
            total_chunks_created=total_chunks_created,
            total_chunks_embedded=total_chunks_embedded,
            total_chunks_summarized=total_chunks_summarized,
            total_chunks_completed=total_chunks_completed,
            total_chunks_failed=total_chunks_failed,
            average_chunks_per_article=average_chunks_per_article,
            average_processing_time_seconds=average_processing_time,
            success_rate=success_rate,
            failure_rate=failure_rate,
            articles_by_state=articles_by_state,
        )
