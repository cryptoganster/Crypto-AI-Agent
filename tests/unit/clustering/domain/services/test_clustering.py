"""Unit tests para ClusteringService."""

from typing import List, Tuple

import numpy as np
import pytest

from src.clustering.domain.aggregates.semantic_cluster import SemanticCluster
from src.clustering.domain.services import ClusteringService
from src.clustering.domain.value_objects import VectorEmbedding


class TestClusteringService:
    """Tests para ClusteringService."""

    @pytest.fixture
    def sample_embeddings(self) -> List[Tuple[str, VectorEmbedding]]:
        """Sample embeddings para testing."""
        embeddings = []

        # Crear 10 embeddings de prueba
        for i in range(10):
            # Crear vector aleatorio y normalizar
            vec = np.random.rand(768).astype(np.float32)
            vec = vec / np.linalg.norm(vec)

            embedding = VectorEmbedding(
                vector=vec,
                model="test-model",
                dimension=768,
            )

            embeddings.append((f"article-{i}", embedding))

        return embeddings

    @pytest.fixture
    def sample_article_texts(self) -> dict:
        """Sample article texts para testing."""
        return {
            "article-0": "Bitcoin price increased significantly today",
            "article-1": "Ethereum network upgrade completed successfully",
            "article-2": "Bitcoin ETF approved by SEC",
            "article-3": "Ethereum gas fees decreased after upgrade",
            "article-4": "Bitcoin mining difficulty reached new high",
            "article-5": "Ethereum staking rewards increased",
            "article-6": "Bitcoin adoption growing in Latin America",
            "article-7": "Ethereum layer 2 solutions gaining traction",
            "article-8": "Bitcoin halving event approaching",
            "article-9": "Ethereum developers announced new roadmap",
        }

    # Test initialization

    def test_init_with_valid_parameters(self):
        """Debería inicializar con parámetros válidos."""
        # Act
        service = ClusteringService(
            algorithm="kmeans",
            n_clusters=5,
            random_state=42,
        )

        # Assert
        assert service._algorithm == "kmeans"
        assert service._n_clusters == 5
        assert service._random_state == 42

    def test_init_with_dbscan_algorithm(self):
        """Debería inicializar con algoritmo DBSCAN."""
        # Act
        service = ClusteringService(
            algorithm="dbscan",
            dbscan_eps=0.3,
            dbscan_min_samples=2,
        )

        # Assert
        assert service._algorithm == "dbscan"
        assert service._dbscan_eps == 0.3
        assert service._dbscan_min_samples == 2

    def test_init_with_invalid_algorithm_raises_error(self):
        """Debería lanzar error con algoritmo inválido."""
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            ClusteringService(algorithm="invalid")

        assert "Algoritmo debe ser 'kmeans' o 'dbscan'" in str(exc_info.value)

    def test_init_with_invalid_n_clusters_raises_error(self):
        """Debería lanzar error con n_clusters inválido."""
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            ClusteringService(n_clusters=0)

        assert "n_clusters debe ser >= 1" in str(exc_info.value)

    def test_init_with_invalid_dbscan_eps_raises_error(self):
        """Debería lanzar error con dbscan_eps inválido."""
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            ClusteringService(algorithm="dbscan", dbscan_eps=0)

        assert "dbscan_eps debe ser > 0" in str(exc_info.value)

    def test_init_with_invalid_dbscan_min_samples_raises_error(self):
        """Debería lanzar error con dbscan_min_samples inválido."""
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            ClusteringService(algorithm="dbscan", dbscan_min_samples=0)

        assert "dbscan_min_samples debe ser >= 1" in str(exc_info.value)

    # Test clustering with KMeans

    def test_cluster_articles_with_kmeans(self, sample_embeddings):
        """Debería agrupar artículos con KMeans."""
        # Arrange
        service = ClusteringService(algorithm="kmeans", n_clusters=3)

        # Act
        clusters = service.cluster_articles(sample_embeddings)

        # Assert
        assert len(clusters) <= 3  # Puede ser menos si hay menos samples
        assert all(isinstance(c, SemanticCluster) for c in clusters)

        # Verificar que todos los artículos están asignados
        all_article_ids = set()
        for cluster in clusters:
            all_article_ids.update(cluster.article_ids)

        expected_ids = set(aid for aid, _ in sample_embeddings)
        assert all_article_ids == expected_ids

    def test_cluster_articles_with_dbscan(self, sample_embeddings):
        """Debería agrupar artículos con DBSCAN."""
        # Arrange
        service = ClusteringService(
            algorithm="dbscan",
            dbscan_eps=0.5,
            dbscan_min_samples=2,
        )

        # Act
        clusters = service.cluster_articles(sample_embeddings)

        # Assert
        assert isinstance(clusters, list)
        assert all(isinstance(c, SemanticCluster) for c in clusters)

        # DBSCAN puede crear cualquier número de clusters
        # (incluyendo 0 si todos son outliers)
        assert len(clusters) >= 0

    def test_cluster_articles_with_empty_list_raises_error(self):
        """Debería lanzar error con lista vacía."""
        # Arrange
        service = ClusteringService()

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            service.cluster_articles([])

        assert "Lista de embeddings no puede estar vacía" in str(exc_info.value)

    def test_cluster_articles_with_mismatched_dimensions_raises_error(self):
        """Debería lanzar error con dimensiones diferentes."""
        # Arrange
        service = ClusteringService()

        # Crear embeddings con dimensiones diferentes
        vec1 = np.array([1.0, 0.0, 0.0], dtype=np.float32)
        vec2 = np.array([1.0, 0.0], dtype=np.float32)

        emb1 = VectorEmbedding(vector=vec1, model="test", dimension=3)
        emb2 = VectorEmbedding(vector=vec2, model="test", dimension=2)

        embeddings = [("article-1", emb1), ("article-2", emb2)]

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            service.cluster_articles(embeddings)

        assert "misma dimensión" in str(exc_info.value)

    def test_cluster_articles_creates_valid_centroids(self, sample_embeddings):
        """Debería crear centroids válidos y normalizados."""
        # Arrange
        service = ClusteringService(algorithm="kmeans", n_clusters=2)

        # Act
        clusters = service.cluster_articles(sample_embeddings)

        # Assert
        for cluster in clusters:
            assert cluster.centroid.dimension == 768
            assert cluster.centroid.is_normalized()

    def test_cluster_articles_assigns_all_articles(self, sample_embeddings):
        """Debería asignar todos los artículos a clusters."""
        # Arrange
        service = ClusteringService(algorithm="kmeans", n_clusters=3)

        # Act
        clusters = service.cluster_articles(sample_embeddings)

        # Assert
        total_articles = sum(c.size for c in clusters)
        assert total_articles == len(sample_embeddings)

    def test_cluster_articles_with_fewer_samples_than_clusters(self):
        """Debería ajustar n_clusters si hay menos samples."""
        # Arrange
        service = ClusteringService(algorithm="kmeans", n_clusters=10)

        # Crear solo 3 embeddings
        embeddings = []
        for i in range(3):
            vec = np.random.rand(768).astype(np.float32)
            vec = vec / np.linalg.norm(vec)
            emb = VectorEmbedding(vector=vec, model="test", dimension=768)
            embeddings.append((f"article-{i}", emb))

        # Act
        clusters = service.cluster_articles(embeddings)

        # Assert
        # Debería crear máximo 3 clusters
        assert len(clusters) <= 3

    # Test centroid calculation

    def test_centroid_calculation_is_normalized(self, sample_embeddings):
        """Debería calcular centroids normalizados."""
        # Arrange
        service = ClusteringService(algorithm="kmeans", n_clusters=2)

        # Act
        clusters = service.cluster_articles(sample_embeddings)

        # Assert
        for cluster in clusters:
            magnitude = cluster.centroid.magnitude()
            assert np.isclose(magnitude, 1.0, atol=1e-5)

    # Test label assignment

    def test_assign_cluster_labels_updates_labels(
        self,
        sample_embeddings,
        sample_article_texts,
    ):
        """Debería asignar labels descriptivos a clusters."""
        # Arrange
        service = ClusteringService(algorithm="kmeans", n_clusters=2)
        clusters = service.cluster_articles(sample_embeddings)

        # Act
        service.assign_cluster_labels(clusters, sample_article_texts)

        # Assert
        for cluster in clusters:
            # Label no debería ser el default "Cluster X"
            assert not cluster.label.startswith("Cluster ")
            # Debería tener top terms
            assert len(cluster.top_terms) > 0

    def test_assign_cluster_labels_uses_tfidf(
        self,
        sample_embeddings,
        sample_article_texts,
    ):
        """Debería usar TF-IDF para encontrar términos importantes."""
        # Arrange
        service = ClusteringService(algorithm="kmeans", n_clusters=2)
        clusters = service.cluster_articles(sample_embeddings)

        # Act
        service.assign_cluster_labels(clusters, sample_article_texts, top_n_terms=3)

        # Assert
        for cluster in clusters:
            # Debería tener exactamente 3 top terms
            assert len(cluster.top_terms) == 3

            # Cada término debería tener frecuencia > 0
            for term, freq in cluster.top_terms:
                assert freq > 0

    def test_assign_cluster_labels_with_empty_texts_raises_error(
        self,
        sample_embeddings,
    ):
        """Debería lanzar error con textos vacíos."""
        # Arrange
        service = ClusteringService()
        clusters = service.cluster_articles(sample_embeddings)

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            service.assign_cluster_labels(clusters, {})

        assert "article_texts no puede estar vacío" in str(exc_info.value)

    def test_assign_cluster_labels_with_invalid_max_features_raises_error(
        self,
        sample_embeddings,
        sample_article_texts,
    ):
        """Debería lanzar error con max_features inválido."""
        # Arrange
        service = ClusteringService()
        clusters = service.cluster_articles(sample_embeddings)

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            service.assign_cluster_labels(
                clusters, sample_article_texts, max_features=0
            )

        assert "max_features debe ser >= 1" in str(exc_info.value)

    def test_assign_cluster_labels_with_invalid_top_n_terms_raises_error(
        self,
        sample_embeddings,
        sample_article_texts,
    ):
        """Debería lanzar error con top_n_terms inválido."""
        # Arrange
        service = ClusteringService()
        clusters = service.cluster_articles(sample_embeddings)

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            service.assign_cluster_labels(clusters, sample_article_texts, top_n_terms=0)

        assert "top_n_terms debe ser >= 1" in str(exc_info.value)

    def test_assign_cluster_labels_handles_missing_texts(
        self,
        sample_embeddings,
    ):
        """Debería manejar artículos sin texto disponible."""
        # Arrange
        service = ClusteringService(algorithm="kmeans", n_clusters=2)
        clusters = service.cluster_articles(sample_embeddings)

        # Textos solo para algunos artículos
        partial_texts = {
            "article-0": "Bitcoin price increased",
            "article-1": "Ethereum upgrade completed",
        }

        # Act
        service.assign_cluster_labels(clusters, partial_texts)

        # Assert
        # No debería lanzar error, algunos clusters pueden mantener label default
        assert all(isinstance(c, SemanticCluster) for c in clusters)

    def test_assign_cluster_labels_creates_meaningful_labels(
        self,
        sample_embeddings,
        sample_article_texts,
    ):
        """Debería crear labels significativos basados en contenido."""
        # Arrange
        service = ClusteringService(algorithm="kmeans", n_clusters=2)
        clusters = service.cluster_articles(sample_embeddings)

        # Act
        service.assign_cluster_labels(clusters, sample_article_texts)

        # Assert
        for cluster in clusters:
            # Label debería contener términos del dominio cripto
            label_lower = cluster.label.lower()
            # Al menos uno de estos términos debería aparecer
            crypto_terms = [
                "bitcoin",
                "ethereum",
                "btc",
                "eth",
                "price",
                "upgrade",
                "network",
            ]
            assert any(term in label_lower for term in crypto_terms)

    # Test quality metrics

    def test_calculate_cluster_quality_metrics(self, sample_embeddings):
        """Debería calcular métricas de calidad."""
        # Arrange
        service = ClusteringService(algorithm="kmeans", n_clusters=3)
        clusters = service.cluster_articles(sample_embeddings)

        # Act
        metrics = service.calculate_cluster_quality_metrics(clusters, sample_embeddings)

        # Assert
        assert "num_clusters" in metrics
        assert "avg_cluster_size" in metrics
        assert "outlier_ratio" in metrics

        assert metrics["num_clusters"] == len(clusters)
        assert metrics["avg_cluster_size"] > 0
        assert 0 <= metrics["outlier_ratio"] <= 1

    def test_calculate_cluster_quality_metrics_includes_silhouette_score(
        self,
        sample_embeddings,
    ):
        """Debería incluir silhouette score si hay suficientes clusters."""
        # Arrange
        service = ClusteringService(algorithm="kmeans", n_clusters=3)
        clusters = service.cluster_articles(sample_embeddings)

        # Act
        metrics = service.calculate_cluster_quality_metrics(clusters, sample_embeddings)

        # Assert
        if len(clusters) >= 2:
            assert "silhouette_score" in metrics
            # Silhouette score está en rango [-1, 1]
            assert -1 <= metrics["silhouette_score"] <= 1

    # Property 12: Cluster Assignment Uniqueness
    # **Validates: Requirements 6.1, 6.4**

    def test_property_cluster_assignment_uniqueness(self, sample_embeddings):
        """
        Property 12: Cluster Assignment Uniqueness.

        Para cualquier artículo, debería estar asignado a máximo un cluster.
        """
        # Arrange
        service = ClusteringService(algorithm="kmeans", n_clusters=3)

        # Act
        clusters = service.cluster_articles(sample_embeddings)

        # Assert
        # Recolectar todos los article_ids de todos los clusters
        all_article_ids = []
        for cluster in clusters:
            all_article_ids.extend(cluster.article_ids)

        # Verificar que no hay duplicados
        assert len(all_article_ids) == len(
            set(all_article_ids)
        ), "Cada artículo debe estar en máximo un cluster"

        # Verificar que cada artículo aparece exactamente una vez
        article_counts = {}
        for article_id in all_article_ids:
            article_counts[article_id] = article_counts.get(article_id, 0) + 1

        for article_id, count in article_counts.items():
            assert (
                count == 1
            ), f"Artículo {article_id} aparece {count} veces, debería aparecer 1 vez"


# Property-Based Tests using Hypothesis

from hypothesis import assume, given, settings
from hypothesis import strategies as st


class TestClusteringServiceProperties:
    """Property-based tests para ClusteringService usando Hypothesis."""

    @given(
        n_articles=st.integers(min_value=2, max_value=50),
        n_clusters=st.integers(min_value=1, max_value=10),
    )
    @settings(max_examples=100, deadline=None)
    def test_property_cluster_assignment_uniqueness_hypothesis(
        self,
        n_articles: int,
        n_clusters: int,
    ):
        """
        **Feature: ai-content-processing-bounded-context, Property 12: Cluster Assignment Uniqueness**
        **Validates: Requirements 6.1, 6.4**

        Para cualquier conjunto de artículos y configuración de clustering,
        cada artículo debe estar asignado a exactamente un cluster.

        Esta propiedad debe mantenerse independientemente de:
        - Número de artículos
        - Número de clusters
        - Algoritmo usado (KMeans o DBSCAN)

        Nota: Usa dimensión 768 (nomic-embed-text) según diseño del sistema.
        """
        # Arrange - Generar embeddings aleatorios con dimensión 768
        dimension = 768
        embeddings = []
        for i in range(n_articles):
            # Crear vector aleatorio y normalizar
            vec = np.random.rand(dimension).astype(np.float32)
            vec = vec / np.linalg.norm(vec)

            embedding = VectorEmbedding(
                vector=vec,
                model="test-model",
                dimension=dimension,
            )

            embeddings.append((f"article-{i}", embedding))

        # Ajustar n_clusters si es mayor que n_articles
        effective_n_clusters = min(n_clusters, n_articles)

        service = ClusteringService(
            algorithm="kmeans",
            n_clusters=effective_n_clusters,
            random_state=42,
        )

        # Act
        clusters = service.cluster_articles(embeddings)

        # Assert - Propiedad de unicidad
        # 1. Recolectar todos los article_ids
        all_article_ids = []
        for cluster in clusters:
            all_article_ids.extend(cluster.article_ids)

        # 2. Verificar que no hay duplicados
        assert len(all_article_ids) == len(set(all_article_ids)), (
            f"Cada artículo debe estar en máximo un cluster. "
            f"Total IDs: {len(all_article_ids)}, Únicos: {len(set(all_article_ids))}"
        )

        # 3. Verificar que todos los artículos están asignados
        expected_ids = set(aid for aid, _ in embeddings)
        actual_ids = set(all_article_ids)
        assert actual_ids == expected_ids, (
            f"Todos los artículos deben estar asignados. "
            f"Esperados: {len(expected_ids)}, Asignados: {len(actual_ids)}"
        )

        # 4. Verificar que cada artículo aparece exactamente una vez
        article_counts = {}
        for article_id in all_article_ids:
            article_counts[article_id] = article_counts.get(article_id, 0) + 1

        for article_id, count in article_counts.items():
            assert (
                count == 1
            ), f"Artículo {article_id} aparece {count} veces, debería aparecer 1 vez"

    @given(
        n_articles=st.integers(min_value=5, max_value=30),
        dbscan_eps=st.floats(min_value=0.1, max_value=0.9),
        dbscan_min_samples=st.integers(min_value=2, max_value=5),
    )
    @settings(max_examples=50, deadline=None)
    def test_property_cluster_assignment_uniqueness_dbscan(
        self,
        n_articles: int,
        dbscan_eps: float,
        dbscan_min_samples: int,
    ):
        """
        **Feature: ai-content-processing-bounded-context, Property 12: Cluster Assignment Uniqueness**
        **Validates: Requirements 6.1, 6.4**

        Para DBSCAN, cada artículo debe estar en máximo un cluster
        (excluyendo outliers que tienen label -1).
        """
        # Arrange
        embeddings = []
        for i in range(n_articles):
            vec = np.random.rand(768).astype(np.float32)
            vec = vec / np.linalg.norm(vec)

            embedding = VectorEmbedding(
                vector=vec,
                model="test-model",
                dimension=768,
            )

            embeddings.append((f"article-{i}", embedding))

        service = ClusteringService(
            algorithm="dbscan",
            dbscan_eps=dbscan_eps,
            dbscan_min_samples=dbscan_min_samples,
        )

        # Act
        clusters = service.cluster_articles(embeddings)

        # Assert - Propiedad de unicidad (excluyendo outliers)
        all_article_ids = []
        for cluster in clusters:
            all_article_ids.extend(cluster.article_ids)

        # Verificar que no hay duplicados en clusters
        assert len(all_article_ids) == len(
            set(all_article_ids)
        ), "Cada artículo debe estar en máximo un cluster"

        # Verificar que cada artículo en clusters aparece exactamente una vez
        article_counts = {}
        for article_id in all_article_ids:
            article_counts[article_id] = article_counts.get(article_id, 0) + 1

        for article_id, count in article_counts.items():
            assert (
                count == 1
            ), f"Artículo {article_id} aparece {count} veces en clusters"

    @given(
        n_articles=st.integers(min_value=3, max_value=20),
        n_clusters=st.integers(min_value=2, max_value=5),
    )
    @settings(max_examples=50, deadline=None)
    def test_property_all_articles_assigned(
        self,
        n_articles: int,
        n_clusters: int,
    ):
        """
        Propiedad: Todos los artículos deben ser asignados a algún cluster.

        Para KMeans, todos los artículos deben estar en algún cluster.
        """
        # Arrange
        embeddings = []
        for i in range(n_articles):
            vec = np.random.rand(768).astype(np.float32)
            vec = vec / np.linalg.norm(vec)

            embedding = VectorEmbedding(
                vector=vec,
                model="test-model",
                dimension=768,
            )

            embeddings.append((f"article-{i}", embedding))

        effective_n_clusters = min(n_clusters, n_articles)

        service = ClusteringService(
            algorithm="kmeans",
            n_clusters=effective_n_clusters,
            random_state=42,
        )

        # Act
        clusters = service.cluster_articles(embeddings)

        # Assert
        all_article_ids = set()
        for cluster in clusters:
            all_article_ids.update(cluster.article_ids)

        expected_ids = set(aid for aid, _ in embeddings)

        assert all_article_ids == expected_ids, (
            f"Todos los artículos deben estar asignados. "
            f"Esperados: {len(expected_ids)}, Asignados: {len(all_article_ids)}"
        )

    @given(
        n_articles=st.integers(min_value=3, max_value=20),
        n_clusters=st.integers(min_value=2, max_value=5),
    )
    @settings(max_examples=50, deadline=None)
    def test_property_centroids_are_normalized(
        self,
        n_articles: int,
        n_clusters: int,
    ):
        """
        Propiedad: Todos los centroids deben estar normalizados (magnitud = 1).
        """
        # Arrange
        embeddings = []
        for i in range(n_articles):
            vec = np.random.rand(768).astype(np.float32)
            vec = vec / np.linalg.norm(vec)

            embedding = VectorEmbedding(
                vector=vec,
                model="test-model",
                dimension=768,
            )

            embeddings.append((f"article-{i}", embedding))

        effective_n_clusters = min(n_clusters, n_articles)

        service = ClusteringService(
            algorithm="kmeans",
            n_clusters=effective_n_clusters,
            random_state=42,
        )

        # Act
        clusters = service.cluster_articles(embeddings)

        # Assert
        for cluster in clusters:
            magnitude = cluster.centroid.magnitude()
            assert np.isclose(
                magnitude, 1.0, atol=1e-5
            ), f"Centroid debe estar normalizado. Magnitud: {magnitude}"
