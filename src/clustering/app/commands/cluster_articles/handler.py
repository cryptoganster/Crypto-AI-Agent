"""Handler para ClusterArticlesCommand."""

from typing import List

from src.chunking.domain.interfaces.services import IVectorStore
from src.clustering.app.commands.cluster_articles.command import ClusterArticlesCommand
from src.clustering.app.commands.cluster_articles.result import (
    ClusterArticlesResult,
    ClusterInfo,
)
from src.clustering.domain.aggregates.semantic_cluster import SemanticCluster
from src.clustering.domain.services.clustering import ClusteringService
from src.shared.kernel.logger import ILogger


class ClusterArticlesHandler:
    """
    Handler para ejecutar clustering de artículos.

    Responsabilidades:
    - Recuperar embeddings de artículos desde vector store
    - Ejecutar clustering usando ClusteringService
    - Asignar labels descriptivos a clusters
    - Persistir clusters (futuro: usar repository)
    - Manejar errores y logging

    Flujo:
    1. Validar comando
    2. Recuperar embeddings de artículos procesados
    3. Ejecutar clustering (KMeans o DBSCAN)
    4. Asignar labels usando TF-IDF
    5. Identificar outliers
    6. Retornar resultado con clusters creados

    Examples:
        >>> handler = ClusterArticlesHandler(vector_store, logger)
        >>> command = ClusterArticlesCommand(algorithm="kmeans", n_clusters=5)
        >>> result = await handler.handle(command)
        >>> result.success
        True
        >>> len(result.clusters) <= 5
        True
    """

    def __init__(
        self,
        vector_store: IVectorStore,
        logger: ILogger,
    ):
        """
        Inicializa ClusterArticlesHandler.

        Args:
            vector_store: Vector store para recuperar embeddings
            logger: Logger para registrar operaciones
        """
        self._vector_store = vector_store
        self._logger = logger.bind(
            layer="application",
            component="ClusterArticlesHandler",
        )

    async def handle(
        self,
        command: ClusterArticlesCommand,
    ) -> ClusterArticlesResult:
        """
        Ejecuta clustering de artículos.

        Args:
            command: Comando con parámetros de clustering

        Returns:
            ClusterArticlesResult con clusters creados o error

        Validates: Requirements 6.1
        """
        self._logger.info(
            "Iniciando clustering de artículos",
            algorithm=command.algorithm,
            n_clusters=command.n_clusters,
            min_articles=command.min_articles,
            recalculate=command.recalculate,
        )

        try:
            # 1. Validar comando
            validation_error = self._validate_command(command)
            if validation_error:
                self._logger.warning(
                    "Validación de comando fallida",
                    error=validation_error,
                )
                return ClusterArticlesResult.failure(validation_error)

            # 2. Recuperar embeddings de artículos
            # TODO: Implementar query para obtener embeddings de artículos
            # Por ahora, retornamos error indicando que falta implementación
            self._logger.warning(
                "Recuperación de embeddings no implementada aún",
                note="Requiere query interface para obtener embeddings de artículos",
            )

            return ClusterArticlesResult.failure(
                "Clustering no disponible: falta implementar query de embeddings"
            )

            # Código futuro (cuando tengamos query interface):
            # embeddings = await self._get_article_embeddings()
            #
            # if len(embeddings) < command.min_articles:
            #     return ClusterArticlesResult.failure(
            #         f"Insuficientes artículos para clustering: "
            #         f"{len(embeddings)} < {command.min_articles}"
            #     )
            #
            # # 3. Ejecutar clustering
            # clustering_service = ClusteringService(
            #     algorithm=command.algorithm,
            #     n_clusters=command.n_clusters,
            # )
            #
            # clusters = clustering_service.cluster_articles(embeddings)
            #
            # # 4. Asignar labels descriptivos
            # article_texts = await self._get_article_texts(
            #     [aid for aid, _ in embeddings]
            # )
            # clustering_service.assign_cluster_labels(clusters, article_texts)
            #
            # # 5. Identificar outliers (artículos sin cluster)
            # clustered_article_ids = set()
            # for cluster in clusters:
            #     clustered_article_ids.update(cluster.article_ids)
            #
            # all_article_ids = set(aid for aid, _ in embeddings)
            # outliers = list(all_article_ids - clustered_article_ids)
            #
            # # 6. Persistir clusters (futuro: usar repository)
            # # await self._cluster_repository.save_all(clusters)
            #
            # # 7. Crear resultado
            # cluster_infos = [
            #     ClusterInfo(
            #         cluster_id=str(cluster.id),
            #         label=cluster.label,
            #         size=cluster.size,
            #         article_ids=cluster.article_ids,
            #     )
            #     for cluster in clusters
            # ]
            #
            # self._logger.info(
            #     "Clustering completado exitosamente",
            #     num_clusters=len(clusters),
            #     total_articles=len(embeddings),
            #     num_outliers=len(outliers),
            # )
            #
            # return ClusterArticlesResult.success_result(
            #     clusters=cluster_infos,
            #     total_articles=len(embeddings),
            #     outliers=outliers,
            # )

        except ValueError as e:
            self._logger.error(
                "Error de validación en clustering",
                error=str(e),
            )
            return ClusterArticlesResult.failure(f"Error de validación: {str(e)}")

        except Exception as e:
            self._logger.error(
                "Error inesperado en clustering",
                error=str(e),
                exc_info=True,
            )
            return ClusterArticlesResult.failure(f"Error inesperado: {str(e)}")

    def _validate_command(self, command: ClusterArticlesCommand) -> str:
        """
        Valida parámetros del comando.

        Args:
            command: Comando a validar

        Returns:
            Mensaje de error si la validación falla, None si es válido
        """
        # Validar algoritmo
        if command.algorithm not in ["kmeans", "dbscan"]:
            return (
                f"Algoritmo inválido: {command.algorithm}. "
                f"Debe ser 'kmeans' o 'dbscan'"
            )

        # Validar n_clusters para kmeans
        if command.algorithm == "kmeans":
            if command.n_clusters < 1:
                return f"n_clusters debe ser >= 1, recibido: {command.n_clusters}"

            if command.n_clusters > 100:
                return (
                    f"n_clusters demasiado alto: {command.n_clusters}. "
                    f"Máximo recomendado: 100"
                )

        # Validar min_articles
        if command.min_articles is not None and command.min_articles < 2:
            return f"min_articles debe ser >= 2, recibido: {command.min_articles}"

        return None

    async def _get_article_embeddings(self):
        """
        Recupera embeddings de artículos procesados.

        TODO: Implementar cuando tengamos query interface.

        Returns:
            Lista de (article_id, VectorEmbedding)
        """
        # Placeholder para implementación futura
        # Necesitamos una query que retorne:
        # - article_id
        # - embedding promedio del artículo (o del global summary)
        #
        # Opciones:
        # 1. Calcular embedding promedio de todos los chunks del artículo
        # 2. Usar embedding del global summary (si existe)
        # 3. Usar embedding del primer chunk (menos preciso)
        pass

    async def _get_article_texts(self, article_ids: List[str]):
        """
        Recupera textos de artículos para TF-IDF.

        TODO: Implementar cuando tengamos query interface.

        Args:
            article_ids: Lista de IDs de artículos

        Returns:
            Diccionario {article_id: texto}
        """
        # Placeholder para implementación futura
        # Necesitamos una query que retorne el texto completo
        # o el global summary de cada artículo
        pass
