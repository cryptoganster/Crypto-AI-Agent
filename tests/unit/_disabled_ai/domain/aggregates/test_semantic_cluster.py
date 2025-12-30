"""Tests unitarios para SemanticCluster aggregate."""

from datetime import datetime, timezone

import numpy as np
import pytest

from src.ai.domain.events import (
    ArticleAddedToClusterEvent,
    ArticleRemovedFromClusterEvent,
    ClusterCentroidUpdatedEvent,
    ClusterLabelUpdatedEvent,
)
from src.ai.domain.value_objects import ClusterId, VectorEmbedding
from src.clustering.domain.aggregates import SemanticCluster


class TestSemanticClusterCreation:
    """Tests para creación de SemanticCluster."""

    def test_create_with_defaults(self):
        """Debería crear SemanticCluster con valores por defecto."""
        # Arrange
        label = "Bitcoin ETF Regulation"
        centroid = VectorEmbedding.from_list([0.1] * 768, "nomic-embed-text")

        # Act
        cluster = SemanticCluster.create(
            label=label,
            centroid=centroid,
        )

        # Assert
        assert cluster.id is not None
        assert isinstance(cluster.id, ClusterId)
        assert cluster.label == label
        assert cluster.centroid == centroid
        assert cluster.size == 0
        assert len(cluster.article_ids) == 0
        assert len(cluster.top_terms) == 0
        assert isinstance(cluster.created_at, datetime)
        assert isinstance(cluster.updated_at, datetime)

    def test_create_with_custom_id(self):
        """Debería crear SemanticCluster con ID personalizado."""
        # Arrange
        label = "Bitcoin"
        centroid = VectorEmbedding.from_list([0.1] * 768, "nomic-embed-text")
        cluster_id = ClusterId.generate()

        # Act
        cluster = SemanticCluster.create(
            label=label,
            centroid=centroid,
            cluster_id=cluster_id,
        )

        # Assert
        assert cluster.id == cluster_id

    def test_create_with_top_terms(self):
        """Debería crear SemanticCluster con términos frecuentes."""
        # Arrange
        label = "Bitcoin"
        centroid = VectorEmbedding.from_list([0.1] * 768, "nomic-embed-text")
        top_terms = [("bitcoin", 0.8), ("regulation", 0.6), ("etf", 0.5)]

        # Act
        cluster = SemanticCluster.create(
            label=label,
            centroid=centroid,
            top_terms=top_terms,
        )

        # Assert
        assert len(cluster.top_terms) == 3
        assert cluster.top_terms[0] == ("bitcoin", 0.8)

    def test_create_with_empty_label_raises_error(self):
        """Debería lanzar error si label está vacío."""
        # Arrange
        centroid = VectorEmbedding.from_list([0.1] * 768, "nomic-embed-text")

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            SemanticCluster.create(
                label="",
                centroid=centroid,
            )

        assert "label no puede estar vacío" in str(exc_info.value)

    def test_create_with_invalid_centroid_dimension_raises_error(self):
        """Debería lanzar error si centroid no tiene dimensión 768."""
        # Arrange
        label = "Bitcoin"
        centroid = VectorEmbedding.from_list([0.1] * 512, "nomic-embed-text")

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            SemanticCluster.create(
                label=label,
                centroid=centroid,
            )

        assert "centroid debe tener dimensión 768" in str(exc_info.value)


class TestSemanticClusterAddArticle:
    """Tests para agregar artículos al cluster."""

    def test_add_article_success(self):
        """Debería agregar artículo correctamente."""
        # Arrange
        cluster = SemanticCluster.create(
            label="Bitcoin",
            centroid=VectorEmbedding.from_list([0.1] * 768, "nomic-embed-text"),
        )
        article_id = "article-123"

        # Act
        cluster.add_article(article_id)

        # Assert
        assert cluster.size == 1
        assert article_id in cluster.article_ids
        assert cluster.contains_article(article_id)
        assert not cluster.is_empty()

    def test_add_article_emits_event(self):
        """Debería emitir ArticleAddedToClusterEvent."""
        # Arrange
        cluster = SemanticCluster.create(
            label="Bitcoin",
            centroid=VectorEmbedding.from_list([0.1] * 768, "nomic-embed-text"),
        )
        article_id = "article-123"

        # Act
        cluster.add_article(article_id)

        # Assert
        events = cluster.get_uncommitted_events()
        assert len(events) == 1
        assert isinstance(events[0], ArticleAddedToClusterEvent)
        assert events[0].cluster_id == str(cluster.id)
        assert events[0].article_id == article_id

    def test_add_multiple_articles(self):
        """Debería agregar múltiples artículos."""
        # Arrange
        cluster = SemanticCluster.create(
            label="Bitcoin",
            centroid=VectorEmbedding.from_list([0.1] * 768, "nomic-embed-text"),
        )

        # Act
        cluster.add_article("article-1")
        cluster.add_article("article-2")
        cluster.add_article("article-3")

        # Assert
        assert cluster.size == 3
        assert len(cluster.article_ids) == 3
        assert "article-1" in cluster.article_ids
        assert "article-2" in cluster.article_ids
        assert "article-3" in cluster.article_ids

    def test_add_duplicate_article_raises_error(self):
        """Debería lanzar error al agregar artículo duplicado."""
        # Arrange
        cluster = SemanticCluster.create(
            label="Bitcoin",
            centroid=VectorEmbedding.from_list([0.1] * 768, "nomic-embed-text"),
        )
        article_id = "article-123"
        cluster.add_article(article_id)

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            cluster.add_article(article_id)

        assert "ya está en el cluster" in str(exc_info.value)

    def test_add_empty_article_id_raises_error(self):
        """Debería lanzar error si article_id está vacío."""
        # Arrange
        cluster = SemanticCluster.create(
            label="Bitcoin",
            centroid=VectorEmbedding.from_list([0.1] * 768, "nomic-embed-text"),
        )

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            cluster.add_article("")

        assert "article_id no puede estar vacío" in str(exc_info.value)

    def test_add_article_updates_timestamp(self):
        """Debería actualizar updated_at al agregar artículo."""
        # Arrange
        cluster = SemanticCluster.create(
            label="Bitcoin",
            centroid=VectorEmbedding.from_list([0.1] * 768, "nomic-embed-text"),
        )
        original_updated_at = cluster.updated_at

        # Act
        cluster.add_article("article-123")

        # Assert
        assert cluster.updated_at >= original_updated_at


class TestSemanticClusterRemoveArticle:
    """Tests para remover artículos del cluster."""

    def test_remove_article_success(self):
        """Debería remover artículo correctamente."""
        # Arrange
        cluster = SemanticCluster.create(
            label="Bitcoin",
            centroid=VectorEmbedding.from_list([0.1] * 768, "nomic-embed-text"),
        )
        article_id = "article-123"
        cluster.add_article(article_id)

        # Act
        cluster.remove_article(article_id)

        # Assert
        assert cluster.size == 0
        assert article_id not in cluster.article_ids
        assert not cluster.contains_article(article_id)
        assert cluster.is_empty()

    def test_remove_article_emits_event(self):
        """Debería emitir ArticleRemovedFromClusterEvent."""
        # Arrange
        cluster = SemanticCluster.create(
            label="Bitcoin",
            centroid=VectorEmbedding.from_list([0.1] * 768, "nomic-embed-text"),
        )
        article_id = "article-123"
        cluster.add_article(article_id)
        cluster.mark_events_as_committed()  # Limpiar eventos anteriores

        # Act
        cluster.remove_article(article_id)

        # Assert
        events = cluster.get_uncommitted_events()
        assert len(events) == 1
        assert isinstance(events[0], ArticleRemovedFromClusterEvent)
        assert events[0].cluster_id == str(cluster.id)
        assert events[0].article_id == article_id

    def test_remove_nonexistent_article_raises_error(self):
        """Debería lanzar error al remover artículo que no existe."""
        # Arrange
        cluster = SemanticCluster.create(
            label="Bitcoin",
            centroid=VectorEmbedding.from_list([0.1] * 768, "nomic-embed-text"),
        )

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            cluster.remove_article("article-123")

        assert "no está en el cluster" in str(exc_info.value)

    def test_remove_article_updates_timestamp(self):
        """Debería actualizar updated_at al remover artículo."""
        # Arrange
        cluster = SemanticCluster.create(
            label="Bitcoin",
            centroid=VectorEmbedding.from_list([0.1] * 768, "nomic-embed-text"),
        )
        cluster.add_article("article-123")
        original_updated_at = cluster.updated_at

        # Act
        cluster.remove_article("article-123")

        # Assert
        assert cluster.updated_at >= original_updated_at


class TestSemanticClusterUpdateCentroid:
    """Tests para actualizar centroid del cluster."""

    def test_update_centroid_success(self):
        """Debería actualizar centroid correctamente."""
        # Arrange
        # Crear vectores diferentes que no se normalicen al mismo valor
        old_vector = [1.0] + [0.0] * 767  # Vector apuntando en dirección x
        new_vector = [0.0] + [1.0] + [0.0] * 766  # Vector apuntando en dirección y

        old_centroid = VectorEmbedding.from_list(old_vector, "nomic-embed-text")
        cluster = SemanticCluster.create(
            label="Bitcoin",
            centroid=old_centroid,
        )
        new_centroid = VectorEmbedding.from_list(new_vector, "nomic-embed-text")

        # Act
        cluster.update_centroid(new_centroid)

        # Assert
        assert cluster.centroid == new_centroid
        # Verificar que son diferentes comparando los vectores
        assert not np.allclose(cluster.centroid.vector, old_centroid.vector)

    def test_update_centroid_emits_event(self):
        """Debería emitir ClusterCentroidUpdatedEvent."""
        # Arrange
        cluster = SemanticCluster.create(
            label="Bitcoin",
            centroid=VectorEmbedding.from_list([0.1] * 768, "nomic-embed-text"),
        )
        new_centroid = VectorEmbedding.from_list([0.2] * 768, "nomic-embed-text")

        # Act
        cluster.update_centroid(new_centroid)

        # Assert
        events = cluster.get_uncommitted_events()
        assert len(events) == 1
        assert isinstance(events[0], ClusterCentroidUpdatedEvent)
        assert events[0].cluster_id == str(cluster.id)
        assert events[0].embedding_dimension == 768

    def test_update_centroid_with_invalid_dimension_raises_error(self):
        """Debería lanzar error si centroid no tiene dimensión 768."""
        # Arrange
        cluster = SemanticCluster.create(
            label="Bitcoin",
            centroid=VectorEmbedding.from_list([0.1] * 768, "nomic-embed-text"),
        )
        invalid_centroid = VectorEmbedding.from_list([0.2] * 512, "nomic-embed-text")

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            cluster.update_centroid(invalid_centroid)

        assert "Centroid debe tener dimensión 768" in str(exc_info.value)

    def test_update_centroid_updates_timestamp(self):
        """Debería actualizar updated_at al actualizar centroid."""
        # Arrange
        cluster = SemanticCluster.create(
            label="Bitcoin",
            centroid=VectorEmbedding.from_list([0.1] * 768, "nomic-embed-text"),
        )
        original_updated_at = cluster.updated_at
        new_centroid = VectorEmbedding.from_list([0.2] * 768, "nomic-embed-text")

        # Act
        cluster.update_centroid(new_centroid)

        # Assert
        assert cluster.updated_at >= original_updated_at


class TestSemanticClusterUpdateLabel:
    """Tests para actualizar label y términos del cluster."""

    def test_update_label_success(self):
        """Debería actualizar label y términos correctamente."""
        # Arrange
        cluster = SemanticCluster.create(
            label="Old Label",
            centroid=VectorEmbedding.from_list([0.1] * 768, "nomic-embed-text"),
        )
        new_label = "Bitcoin ETF Regulation"
        new_terms = [("bitcoin", 0.8), ("etf", 0.7), ("regulation", 0.6)]

        # Act
        cluster.update_label(new_label, new_terms)

        # Assert
        assert cluster.label == new_label
        assert len(cluster.top_terms) == 3
        assert cluster.top_terms[0] == ("bitcoin", 0.8)
        assert cluster.top_terms[1] == ("etf", 0.7)
        assert cluster.top_terms[2] == ("regulation", 0.6)

    def test_update_label_emits_event(self):
        """Debería emitir ClusterLabelUpdatedEvent."""
        # Arrange
        cluster = SemanticCluster.create(
            label="Old Label",
            centroid=VectorEmbedding.from_list([0.1] * 768, "nomic-embed-text"),
        )
        new_label = "New Label"
        new_terms = [("term1", 0.5)]

        # Act
        cluster.update_label(new_label, new_terms)

        # Assert
        events = cluster.get_uncommitted_events()
        assert len(events) == 1
        assert isinstance(events[0], ClusterLabelUpdatedEvent)
        assert events[0].cluster_id == str(cluster.id)
        assert events[0].new_label == new_label
        assert events[0].top_terms_count == 1

    def test_update_label_with_empty_label_raises_error(self):
        """Debería lanzar error si label está vacío."""
        # Arrange
        cluster = SemanticCluster.create(
            label="Old Label",
            centroid=VectorEmbedding.from_list([0.1] * 768, "nomic-embed-text"),
        )

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            cluster.update_label("", [])

        assert "Label no puede estar vacío" in str(exc_info.value)

    def test_update_label_with_invalid_term_frequency_raises_error(self):
        """Debería lanzar error si frecuencia de término es <= 0."""
        # Arrange
        cluster = SemanticCluster.create(
            label="Old Label",
            centroid=VectorEmbedding.from_list([0.1] * 768, "nomic-embed-text"),
        )
        invalid_terms = [("term1", 0.5), ("term2", 0.0)]

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            cluster.update_label("New Label", invalid_terms)

        assert "Frecuencia de término debe ser > 0" in str(exc_info.value)

    def test_update_label_strips_whitespace(self):
        """Debería eliminar espacios en blanco del label."""
        # Arrange
        cluster = SemanticCluster.create(
            label="Old Label",
            centroid=VectorEmbedding.from_list([0.1] * 768, "nomic-embed-text"),
        )

        # Act
        cluster.update_label("  New Label  ", [])

        # Assert
        assert cluster.label == "New Label"

    def test_update_label_updates_timestamp(self):
        """Debería actualizar updated_at al actualizar label."""
        # Arrange
        cluster = SemanticCluster.create(
            label="Old Label",
            centroid=VectorEmbedding.from_list([0.1] * 768, "nomic-embed-text"),
        )
        original_updated_at = cluster.updated_at

        # Act
        cluster.update_label("New Label", [])

        # Assert
        assert cluster.updated_at >= original_updated_at


class TestSemanticClusterHelperMethods:
    """Tests para métodos helper del cluster."""

    def test_contains_article_returns_true_when_present(self):
        """Debería retornar True si artículo está en el cluster."""
        # Arrange
        cluster = SemanticCluster.create(
            label="Bitcoin",
            centroid=VectorEmbedding.from_list([0.1] * 768, "nomic-embed-text"),
        )
        cluster.add_article("article-123")

        # Act & Assert
        assert cluster.contains_article("article-123") is True

    def test_contains_article_returns_false_when_absent(self):
        """Debería retornar False si artículo no está en el cluster."""
        # Arrange
        cluster = SemanticCluster.create(
            label="Bitcoin",
            centroid=VectorEmbedding.from_list([0.1] * 768, "nomic-embed-text"),
        )

        # Act & Assert
        assert cluster.contains_article("article-123") is False

    def test_is_empty_returns_true_when_no_articles(self):
        """Debería retornar True si no hay artículos."""
        # Arrange
        cluster = SemanticCluster.create(
            label="Bitcoin",
            centroid=VectorEmbedding.from_list([0.1] * 768, "nomic-embed-text"),
        )

        # Act & Assert
        assert cluster.is_empty() is True

    def test_is_empty_returns_false_when_has_articles(self):
        """Debería retornar False si hay artículos."""
        # Arrange
        cluster = SemanticCluster.create(
            label="Bitcoin",
            centroid=VectorEmbedding.from_list([0.1] * 768, "nomic-embed-text"),
        )
        cluster.add_article("article-123")

        # Act & Assert
        assert cluster.is_empty() is False

    def test_get_top_term_names_returns_only_names(self):
        """Debería retornar solo nombres de términos sin frecuencias."""
        # Arrange
        cluster = SemanticCluster.create(
            label="Bitcoin",
            centroid=VectorEmbedding.from_list([0.1] * 768, "nomic-embed-text"),
            top_terms=[("bitcoin", 0.8), ("etf", 0.6), ("regulation", 0.5)],
        )

        # Act
        term_names = cluster.get_top_term_names()

        # Assert
        assert term_names == ["bitcoin", "etf", "regulation"]

    def test_get_top_term_names_returns_empty_list_when_no_terms(self):
        """Debería retornar lista vacía si no hay términos."""
        # Arrange
        cluster = SemanticCluster.create(
            label="Bitcoin",
            centroid=VectorEmbedding.from_list([0.1] * 768, "nomic-embed-text"),
        )

        # Act
        term_names = cluster.get_top_term_names()

        # Assert
        assert term_names == []


class TestSemanticClusterInvariants:
    """Tests para invariantes del cluster."""

    def test_size_equals_article_ids_length(self):
        """Debería mantener size == len(article_ids)."""
        # Arrange
        cluster = SemanticCluster.create(
            label="Bitcoin",
            centroid=VectorEmbedding.from_list([0.1] * 768, "nomic-embed-text"),
        )

        # Act & Assert - Inicialmente
        assert cluster.size == len(cluster.article_ids)

        # Agregar artículos
        cluster.add_article("article-1")
        assert cluster.size == len(cluster.article_ids)

        cluster.add_article("article-2")
        assert cluster.size == len(cluster.article_ids)

        # Remover artículo
        cluster.remove_article("article-1")
        assert cluster.size == len(cluster.article_ids)

    def test_article_ids_immutability_via_property(self):
        """Debería retornar copia de article_ids para prevenir mutación externa."""
        # Arrange
        cluster = SemanticCluster.create(
            label="Bitcoin",
            centroid=VectorEmbedding.from_list([0.1] * 768, "nomic-embed-text"),
        )
        cluster.add_article("article-123")

        # Act
        article_ids = cluster.article_ids
        article_ids.append("article-456")  # Intentar mutar

        # Assert - No debería afectar el cluster
        assert "article-456" not in cluster.article_ids
        assert cluster.size == 1

    def test_top_terms_immutability_via_property(self):
        """Debería retornar copia de top_terms para prevenir mutación externa."""
        # Arrange
        cluster = SemanticCluster.create(
            label="Bitcoin",
            centroid=VectorEmbedding.from_list([0.1] * 768, "nomic-embed-text"),
            top_terms=[("bitcoin", 0.8)],
        )

        # Act
        top_terms = cluster.top_terms
        top_terms.append(("fake", 0.5))  # Intentar mutar

        # Assert - No debería afectar el cluster
        assert len(cluster.top_terms) == 1
        assert ("fake", 0.5) not in cluster.top_terms
