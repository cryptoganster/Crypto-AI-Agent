"""Domain service para clustering semántico de artículos."""

from typing import Dict, List, Optional, Tuple

import numpy as np
from sklearn.cluster import DBSCAN, KMeans
from sklearn.feature_extraction.text import TfidfVectorizer

from src.clustering.domain.aggregates.semantic_cluster import SemanticCluster
from src.clustering.domain.value_objects import ClusterId, VectorEmbedding


class ClusteringService:
    """
    Domain service para clustering semántico.

    Responsabilidades:
    - Agrupar artículos similares usando embeddings
    - Calcular centroids de clusters
    - Asignar labels descriptivos usando TF-IDF

    Soporta dos algoritmos:
    - KMeans: Requiere especificar número de clusters
    - DBSCAN: Detecta clusters automáticamente basado en densidad

    Examples:
        >>> service = ClusteringService(algorithm="kmeans", n_clusters=5)
        >>> embeddings = [(article_id, embedding), ...]
        >>> clusters = service.cluster_articles(embeddings)
        >>> len(clusters)
        5
    """

    def __init__(
        self,
        algorithm: str = "kmeans",
        n_clusters: int = 10,
        dbscan_eps: float = 0.3,
        dbscan_min_samples: int = 2,
        random_state: int = 42,
    ):
        """
        Inicializa ClusteringService.

        Args:
            algorithm: Algoritmo a usar ("kmeans" o "dbscan")
            n_clusters: Número de clusters para KMeans
            dbscan_eps: Epsilon para DBSCAN (distancia máxima)
            dbscan_min_samples: Mínimo de samples para DBSCAN
            random_state: Seed para reproducibilidad

        Raises:
            ValueError: Si el algoritmo no es válido
        """
        if algorithm not in ["kmeans", "dbscan"]:
            raise ValueError(
                f"Algoritmo debe ser 'kmeans' o 'dbscan', recibido: {algorithm}"
            )

        if n_clusters < 1:
            raise ValueError(f"n_clusters debe ser >= 1, recibido: {n_clusters}")

        if dbscan_eps <= 0:
            raise ValueError(f"dbscan_eps debe ser > 0, recibido: {dbscan_eps}")

        if dbscan_min_samples < 1:
            raise ValueError(
                f"dbscan_min_samples debe ser >= 1, recibido: {dbscan_min_samples}"
            )

        self._algorithm = algorithm
        self._n_clusters = n_clusters
        self._dbscan_eps = dbscan_eps
        self._dbscan_min_samples = dbscan_min_samples
        self._random_state = random_state

    def cluster_articles(
        self,
        embeddings: List[Tuple[str, VectorEmbedding]],
    ) -> List[SemanticCluster]:
        """
        Agrupa artículos en clusters semánticos.

        Args:
            embeddings: Lista de (article_id, embedding)

        Returns:
            Lista de SemanticCluster

        Raises:
            ValueError: Si la lista de embeddings está vacía

        Examples:
            >>> service = ClusteringService(algorithm="kmeans", n_clusters=3)
            >>> embeddings = [
            ...     ("article-1", embedding1),
            ...     ("article-2", embedding2),
            ...     ("article-3", embedding3),
            ... ]
            >>> clusters = service.cluster_articles(embeddings)
            >>> len(clusters) <= 3
            True
        """
        if not embeddings:
            raise ValueError("Lista de embeddings no puede estar vacía")

        # Validar que todos los embeddings tengan la misma dimensión
        dimensions = set(emb.dimension for _, emb in embeddings)
        if len(dimensions) > 1:
            raise ValueError(
                f"Todos los embeddings deben tener la misma dimensión, "
                f"encontradas: {dimensions}"
            )

        # Preparar matriz de embeddings
        article_ids = [aid for aid, _ in embeddings]
        vectors = np.array([emb.vector for _, emb in embeddings])

        # Ejecutar clustering
        if self._algorithm == "kmeans":
            labels = self._cluster_kmeans(vectors)
        else:  # dbscan
            labels = self._cluster_dbscan(vectors)

        # Crear SemanticCluster objects
        clusters = self._create_clusters(
            article_ids, vectors, labels, embeddings[0][1].model
        )

        return clusters

    def _cluster_kmeans(self, vectors: np.ndarray) -> np.ndarray:
        """
        Ejecuta clustering con KMeans.

        Args:
            vectors: Matriz de vectores (n_samples, n_features)

        Returns:
            Array de labels (n_samples,)
        """
        # Ajustar n_clusters si hay menos samples
        n_clusters = min(self._n_clusters, len(vectors))

        clusterer = KMeans(
            n_clusters=n_clusters,
            random_state=self._random_state,
            n_init=10,
        )

        labels = clusterer.fit_predict(vectors)

        return labels

    def _cluster_dbscan(self, vectors: np.ndarray) -> np.ndarray:
        """
        Ejecuta clustering con DBSCAN.

        Args:
            vectors: Matriz de vectores (n_samples, n_features)

        Returns:
            Array de labels (n_samples,), -1 indica outliers
        """
        clusterer = DBSCAN(
            eps=self._dbscan_eps,
            min_samples=self._dbscan_min_samples,
            metric="cosine",
        )

        labels = clusterer.fit_predict(vectors)

        return labels

    def _create_clusters(
        self,
        article_ids: List[str],
        vectors: np.ndarray,
        labels: np.ndarray,
        model: str,
    ) -> List[SemanticCluster]:
        """
        Crea SemanticCluster objects desde labels.

        Args:
            article_ids: Lista de IDs de artículos
            vectors: Matriz de vectores
            labels: Array de labels de clustering
            model: Nombre del modelo de embeddings

        Returns:
            Lista de SemanticCluster
        """
        clusters = []
        unique_labels = set(labels)

        for label in unique_labels:
            # Saltar outliers de DBSCAN
            if label == -1:
                continue

            # Artículos en este cluster
            cluster_mask = labels == label
            cluster_article_ids = [
                article_ids[i] for i, mask in enumerate(cluster_mask) if mask
            ]

            # Calcular centroid
            cluster_vectors = vectors[cluster_mask]
            centroid_vector = cluster_vectors.mean(axis=0)

            # Normalizar centroid
            centroid_magnitude = np.linalg.norm(centroid_vector)
            if centroid_magnitude > 0:
                centroid_vector = centroid_vector / centroid_magnitude
            else:
                # Si el centroid es cero (caso raro), usar vector unitario
                centroid_vector = np.zeros_like(centroid_vector)
                centroid_vector[0] = 1.0

            centroid = VectorEmbedding(
                vector=centroid_vector,
                model=model,
                dimension=len(centroid_vector),
            )

            # Crear cluster con label temporal
            cluster = SemanticCluster.create(
                label=f"Cluster {label}",
                centroid=centroid,
            )

            # Agregar artículos
            for article_id in cluster_article_ids:
                cluster.add_article(article_id)

            clusters.append(cluster)

        return clusters

    def assign_cluster_labels(
        self,
        clusters: List[SemanticCluster],
        article_texts: Dict[str, str],
        max_features: int = 10,
        top_n_terms: int = 5,
    ) -> None:
        """
        Asigna labels descriptivos a clusters basados en términos frecuentes.

        Usa TF-IDF para encontrar los términos más importantes en cada cluster
        y actualiza el label del cluster con estos términos.

        Args:
            clusters: Lista de clusters a etiquetar
            article_texts: Diccionario {article_id: texto}
            max_features: Número máximo de features para TF-IDF
            top_n_terms: Número de términos top para el label

        Raises:
            ValueError: Si no hay textos disponibles

        Examples:
            >>> service = ClusteringService()
            >>> clusters = [cluster1, cluster2]
            >>> texts = {"article-1": "Bitcoin ETF approved", ...}
            >>> service.assign_cluster_labels(clusters, texts)
            >>> "Bitcoin" in clusters[0].label or "ETF" in clusters[0].label
            True
        """
        if not article_texts:
            raise ValueError("article_texts no puede estar vacío")

        if max_features < 1:
            raise ValueError(f"max_features debe ser >= 1, recibido: {max_features}")

        if top_n_terms < 1:
            raise ValueError(f"top_n_terms debe ser >= 1, recibido: {top_n_terms}")

        for cluster in clusters:
            # Obtener textos del cluster
            texts = [
                article_texts[aid]
                for aid in cluster.article_ids
                if aid in article_texts
            ]

            if not texts:
                # Si no hay textos, mantener label por defecto
                continue

            # TF-IDF para encontrar términos importantes
            try:
                vectorizer = TfidfVectorizer(
                    max_features=max_features,
                    stop_words="english",
                    ngram_range=(1, 2),
                    min_df=1,  # Mínimo 1 documento
                )

                tfidf_matrix = vectorizer.fit_transform(texts)
                feature_names = vectorizer.get_feature_names_out()

                # Calcular scores totales por término
                scores = tfidf_matrix.sum(axis=0).A1

                # Top términos
                top_indices = scores.argsort()[-top_n_terms:][::-1]
                top_terms = [(feature_names[i], float(scores[i])) for i in top_indices]

                # Crear label desde top términos
                label = " | ".join([term for term, _ in top_terms[:3]])

                # Actualizar cluster
                cluster.update_label(label, top_terms)

            except ValueError:
                # Si TF-IDF falla (ej: todos los textos vacíos), mantener label por defecto
                continue

    def calculate_cluster_quality_metrics(
        self,
        clusters: List[SemanticCluster],
        embeddings: List[Tuple[str, VectorEmbedding]],
    ) -> Dict[str, float]:
        """
        Calcula métricas de calidad del clustering.

        Args:
            clusters: Lista de clusters
            embeddings: Lista de (article_id, embedding)

        Returns:
            Diccionario con métricas:
            - silhouette_score: Cohesión y separación de clusters
            - avg_cluster_size: Tamaño promedio de clusters
            - num_clusters: Número de clusters
            - outlier_ratio: Proporción de outliers (solo DBSCAN)
        """
        from sklearn.metrics import silhouette_score

        # Preparar datos
        article_ids = [aid for aid, _ in embeddings]
        vectors = np.array([emb.vector for _, emb in embeddings])

        # Crear array de labels
        labels = np.full(len(article_ids), -1, dtype=int)
        for cluster_idx, cluster in enumerate(clusters):
            for article_id in cluster.article_ids:
                if article_id in article_ids:
                    idx = article_ids.index(article_id)
                    labels[idx] = cluster_idx

        # Calcular métricas
        metrics = {
            "num_clusters": len(clusters),
            "avg_cluster_size": (
                np.mean([c.size for c in clusters]) if clusters else 0.0
            ),
            "outlier_ratio": (
                float(np.sum(labels == -1)) / len(labels) if len(labels) > 0 else 0.0
            ),
        }

        # Silhouette score (solo si hay al menos 2 clusters y no todos son outliers)
        if len(clusters) >= 2 and np.sum(labels != -1) > 1:
            # Filtrar outliers para silhouette score
            non_outlier_mask = labels != -1
            if np.sum(non_outlier_mask) > 1:
                try:
                    score = silhouette_score(
                        vectors[non_outlier_mask],
                        labels[non_outlier_mask],
                        metric="cosine",
                    )
                    metrics["silhouette_score"] = float(score)
                except ValueError:
                    # Si falla el cálculo, no incluir la métrica
                    pass

        return metrics
