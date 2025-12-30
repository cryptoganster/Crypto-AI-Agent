"""Configuración para Clustering Bounded Context.

Carga configuración desde variables de entorno para clustering semántico.
"""

import os
from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class ClusteringConfig:
    """
    Configuración para clustering semántico de artículos.

    Attributes:
        algorithm: Algoritmo de clustering ("kmeans" o "dbscan")
        n_clusters: Número de clusters para KMeans
        dbscan_eps: Epsilon para DBSCAN (distancia máxima)
        dbscan_min_samples: Mínimo de samples para DBSCAN
        min_cluster_size: Tamaño mínimo de cluster para considerar válido
        random_state: Seed para reproducibilidad

    Requirements: 10.3.5
    """

    algorithm: Literal["kmeans", "dbscan"]
    n_clusters: int
    dbscan_eps: float
    dbscan_min_samples: int
    min_cluster_size: int
    random_state: int

    @classmethod
    def from_env(cls) -> "ClusteringConfig":
        """
        Carga configuración desde variables de entorno.

        Variables de entorno:
        - CLUSTERING_ALGORITHM: Algoritmo ("kmeans" o "dbscan", default: "kmeans")
        - CLUSTERING_N_CLUSTERS: Número de clusters (default: 10)
        - CLUSTERING_DBSCAN_EPS: Epsilon para DBSCAN (default: 0.3)
        - CLUSTERING_DBSCAN_MIN_SAMPLES: Min samples DBSCAN (default: 2)
        - CLUSTERING_MIN_CLUSTER_SIZE: Tamaño mínimo de cluster (default: 3)
        - CLUSTERING_RANDOM_STATE: Seed para reproducibilidad (default: 42)

        Returns:
            ClusteringConfig con valores cargados

        Raises:
            ValueError: Si la configuración es inválida

        Examples:
            >>> config = ClusteringConfig.from_env()
            >>> config.algorithm in ["kmeans", "dbscan"]
            True
            >>> config.n_clusters > 0
            True
        """
        algorithm = os.getenv("CLUSTERING_ALGORITHM", "kmeans").lower()
        n_clusters = int(os.getenv("CLUSTERING_N_CLUSTERS", "10"))
        dbscan_eps = float(os.getenv("CLUSTERING_DBSCAN_EPS", "0.3"))
        dbscan_min_samples = int(os.getenv("CLUSTERING_DBSCAN_MIN_SAMPLES", "2"))
        min_cluster_size = int(os.getenv("CLUSTERING_MIN_CLUSTER_SIZE", "3"))
        random_state = int(os.getenv("CLUSTERING_RANDOM_STATE", "42"))

        # Validar configuración
        if algorithm not in ["kmeans", "dbscan"]:
            raise ValueError(
                f"CLUSTERING_ALGORITHM debe ser 'kmeans' o 'dbscan', "
                f"recibido: {algorithm}"
            )

        if n_clusters < 1:
            raise ValueError(
                f"CLUSTERING_N_CLUSTERS debe ser >= 1, recibido: {n_clusters}"
            )

        if n_clusters > 100:
            raise ValueError(
                f"CLUSTERING_N_CLUSTERS demasiado alto: {n_clusters}. "
                f"Máximo recomendado: 100"
            )

        if dbscan_eps <= 0:
            raise ValueError(
                f"CLUSTERING_DBSCAN_EPS debe ser > 0, recibido: {dbscan_eps}"
            )

        if dbscan_eps > 1.0:
            raise ValueError(
                f"CLUSTERING_DBSCAN_EPS demasiado alto: {dbscan_eps}. "
                f"Máximo recomendado: 1.0"
            )

        if dbscan_min_samples < 1:
            raise ValueError(
                f"CLUSTERING_DBSCAN_MIN_SAMPLES debe ser >= 1, "
                f"recibido: {dbscan_min_samples}"
            )

        if min_cluster_size < 1:
            raise ValueError(
                f"CLUSTERING_MIN_CLUSTER_SIZE debe ser >= 1, "
                f"recibido: {min_cluster_size}"
            )

        return cls(
            algorithm=algorithm,
            n_clusters=n_clusters,
            dbscan_eps=dbscan_eps,
            dbscan_min_samples=dbscan_min_samples,
            min_cluster_size=min_cluster_size,
            random_state=random_state,
        )

    def validate(self) -> None:
        """
        Valida la configuración.

        Raises:
            ValueError: Si la configuración es inválida
        """
        if self.algorithm not in ["kmeans", "dbscan"]:
            raise ValueError(
                f"algorithm debe ser 'kmeans' o 'dbscan', recibido: {self.algorithm}"
            )

        if self.n_clusters < 1:
            raise ValueError(f"n_clusters debe ser >= 1, recibido: {self.n_clusters}")

        if self.dbscan_eps <= 0:
            raise ValueError(f"dbscan_eps debe ser > 0, recibido: {self.dbscan_eps}")

        if self.dbscan_min_samples < 1:
            raise ValueError(
                f"dbscan_min_samples debe ser >= 1, "
                f"recibido: {self.dbscan_min_samples}"
            )

        if self.min_cluster_size < 1:
            raise ValueError(
                f"min_cluster_size debe ser >= 1, " f"recibido: {self.min_cluster_size}"
            )
