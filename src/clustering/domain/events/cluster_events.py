"""Domain events para SemanticCluster aggregate."""

from dataclasses import dataclass, field
from datetime import datetime, timezone

from src.shared.kernel.domain_event import IDomainEvent


@dataclass(frozen=True)
class ArticleAddedToClusterEvent(IDomainEvent):
    """
    Evento emitido cuando se agrega un artículo a un cluster semántico.

    Attributes:
        cluster_id: ID del cluster
        article_id: ID del artículo agregado
        occurred_at: Timestamp del evento
    """

    cluster_id: str
    article_id: str
    occurred_at: datetime = field(default=None)

    def __post_init__(self):
        """Valida el evento y genera timestamp."""
        if not self.cluster_id:
            raise ValueError("cluster_id no puede estar vacío")
        if not self.article_id:
            raise ValueError("article_id no puede estar vacío")

        # Generar timestamp si no se proporciona
        if self.occurred_at is None:
            object.__setattr__(self, "occurred_at", datetime.now(timezone.utc))


@dataclass(frozen=True)
class ArticleRemovedFromClusterEvent(IDomainEvent):
    """
    Evento emitido cuando se remueve un artículo de un cluster semántico.

    Attributes:
        cluster_id: ID del cluster
        article_id: ID del artículo removido
        occurred_at: Timestamp del evento
    """

    cluster_id: str
    article_id: str
    occurred_at: datetime = field(default=None)

    def __post_init__(self):
        """Valida el evento y genera timestamp."""
        if not self.cluster_id:
            raise ValueError("cluster_id no puede estar vacío")
        if not self.article_id:
            raise ValueError("article_id no puede estar vacío")

        # Generar timestamp si no se proporciona
        if self.occurred_at is None:
            object.__setattr__(self, "occurred_at", datetime.now(timezone.utc))


@dataclass(frozen=True)
class ClusterCentroidUpdatedEvent(IDomainEvent):
    """
    Evento emitido cuando se actualiza el centroid de un cluster.

    Attributes:
        cluster_id: ID del cluster
        embedding_dimension: Dimensión del nuevo centroid
        occurred_at: Timestamp del evento
    """

    cluster_id: str
    embedding_dimension: int
    occurred_at: datetime = field(default=None)

    def __post_init__(self):
        """Valida el evento y genera timestamp."""
        if not self.cluster_id:
            raise ValueError("cluster_id no puede estar vacío")
        if self.embedding_dimension <= 0:
            raise ValueError("embedding_dimension debe ser > 0")

        # Generar timestamp si no se proporciona
        if self.occurred_at is None:
            object.__setattr__(self, "occurred_at", datetime.now(timezone.utc))


@dataclass(frozen=True)
class ClusterLabelUpdatedEvent(IDomainEvent):
    """
    Evento emitido cuando se actualiza el label de un cluster.

    Attributes:
        cluster_id: ID del cluster
        new_label: Nuevo label descriptivo
        top_terms_count: Número de términos frecuentes
        occurred_at: Timestamp del evento
    """

    cluster_id: str
    new_label: str
    top_terms_count: int
    occurred_at: datetime = field(default=None)

    def __post_init__(self):
        """Valida el evento y genera timestamp."""
        if not self.cluster_id:
            raise ValueError("cluster_id no puede estar vacío")
        if not self.new_label or not self.new_label.strip():
            raise ValueError("new_label no puede estar vacío")
        if self.top_terms_count < 0:
            raise ValueError("top_terms_count debe ser >= 0")

        # Generar timestamp si no se proporciona
        if self.occurred_at is None:
            object.__setattr__(self, "occurred_at", datetime.now(timezone.utc))


@dataclass(frozen=True)
class ArticleClusteredEvent(IDomainEvent):
    """
    Evento emitido cuando un artículo es asignado a un cluster semántico.

    Este es un evento de alto nivel que indica que el proceso de clustering
    para un artículo específico ha sido completado.

    Attributes:
        article_id: ID del artículo clusterizado
        cluster_id: ID del cluster al que fue asignado
        occurred_at: Timestamp del evento

    Requirements: 6.4
    """

    article_id: str
    cluster_id: str
    occurred_at: datetime = field(default=None)

    def __post_init__(self):
        """Valida el evento y genera timestamp."""
        if not self.article_id:
            raise ValueError("article_id no puede estar vacío")
        if not self.cluster_id:
            raise ValueError("cluster_id no puede estar vacío")

        # Generar timestamp si no se proporciona
        if self.occurred_at is None:
            object.__setattr__(self, "occurred_at", datetime.now(timezone.utc))
