"""Handler para GetArticleClusters query."""

from typing import List

from src.clustering.app.queries.get_article_clusters.dto import (
    ClusterDTO,
    GetArticleClustersResultDTO,
)
from src.clustering.app.queries.get_article_clusters.query import (
    GetArticleClustersQuery,
)
from src.clustering.domain.aggregates.semantic_cluster import SemanticCluster
from src.clustering.domain.interfaces.cluster_repository import (
    IClusterReadRepository,
)
from src.shared.kernel.logger import ILogger


class GetArticleClustersHandler:
    """
    Handler para obtener clusters de artículos.

    Flujo:
    1. Recuperar clusters del repository
    2. Aplicar filtros
    3. Ordenar resultados
    4. Retornar cluster DTOs

    Validates: Requirements 6.4
    """

    def __init__(
        self,
        cluster_repository: IClusterReadRepository,
        logger: ILogger,
    ):
        """
        Inicializa el handler.

        Args:
            cluster_repository: Repository para leer clusters
            logger: Logger para registrar operaciones
        """
        self._repository = cluster_repository
        self._logger = logger.bind(
            layer="application",
            component="GetArticleClustersHandler",
        )

    async def handle(
        self,
        query: GetArticleClustersQuery,
    ) -> GetArticleClustersResultDTO:
        """
        Ejecuta query para obtener clusters.

        Args:
            query: Query con parámetros de filtrado y ordenamiento

        Returns:
            GetArticleClustersResultDTO con clusters encontrados

        Raises:
            Exception: Si la recuperación falla
        """
        self._logger.info(
            "Obteniendo clusters de artículos",
            min_size=query.min_size,
            order_by=query.order_by,
            ascending=query.ascending,
        )

        try:
            # 1. Recuperar clusters del repository con filtros
            clusters: List[SemanticCluster] = await self._repository.find_all(
                min_size=query.min_size,
                order_by=query.order_by,
                ascending=query.ascending,
            )

            # 2. Convertir a DTOs
            cluster_dtos = []
            for cluster in clusters:
                cluster_dto = ClusterDTO(
                    cluster_id=str(cluster.id),
                    label=cluster.label,
                    size=cluster.size,
                    article_ids=cluster.article_ids.copy(),
                    top_terms=cluster.top_terms.copy(),
                    created_at=cluster.created_at,
                    updated_at=cluster.updated_at,
                )
                cluster_dtos.append(cluster_dto)

            self._logger.info(
                "Clusters recuperados exitosamente",
                total_clusters=len(cluster_dtos),
                min_size_filter=query.min_size,
            )

            return GetArticleClustersResultDTO(
                clusters=cluster_dtos,
                total_clusters=len(cluster_dtos),
                min_size_filter=query.min_size,
                order_by=query.order_by,
            )

        except Exception as e:
            self._logger.error(
                "Error obteniendo clusters",
                error=str(e),
                min_size=query.min_size,
            )
            raise
