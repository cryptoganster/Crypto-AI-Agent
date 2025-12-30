"""SemanticCluster aggregate root para clustering semántico de artículos."""

from datetime import datetime, timezone
from typing import List, Optional, Tuple

from src.clustering.domain.events.cluster_events import (
    ArticleAddedToClusterEvent,
    ArticleRemovedFromClusterEvent,
    ClusterCentroidUpdatedEvent,
    ClusterLabelUpdatedEvent,
)
from src.clustering.domain.value_objects import ClusterId, VectorEmbedding
from src.shared.kernel.aggregate_root import IAggregateRoot


class SemanticCluster(IAggregateRoot[ClusterId]):
    """
    Aggregate root para cluster semántico de artículos.

    Representa un grupo de artículos similares basado en
    embeddings semánticos. Mantiene el centroid del cluster
    y términos frecuentes para identificación.

    Responsabilidades:
    - Gestionar membresía de artículos en el cluster
    - Mantener centroid actualizado
    - Trackear términos frecuentes y label descriptivo
    - Mantener sincronizado el tamaño con article_ids

    Invariantes:
    - size == len(article_ids)
    - No duplicar article_ids
    - Centroid debe ser válido (768 dims, normalizado)
    - Label no puede estar vacío
    - Top terms deben tener frecuencia > 0

    Attributes:
        id: Identificador único del cluster
        label: Label descriptivo (ej: "Bitcoin ETF Regulation")
        article_ids: Lista de IDs de artículos en el cluster
        centroid: Centroid del cluster (embedding promedio)
        size: Número de artículos en el cluster
        top_terms: Términos más frecuentes con sus frecuencias
        created_at: Timestamp de creación
        updated_at: Timestamp de última actualización

    Examples:
        >>> cluster = SemanticCluster.create(
        ...     label="Bitcoin Regulation",
        ...     centroid=embedding,
        ... )
        >>> cluster.add_article("article-123")
        >>> cluster.size
        1
        >>> cluster.remove_article("article-123")
        >>> cluster.size
        0
    """

    def __init__(
        self,
        id: ClusterId,
        label: str,
        centroid: VectorEmbedding,
        article_ids: Optional[List[str]] = None,
        size: Optional[int] = None,
        top_terms: Optional[List[Tuple[str, float]]] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
    ):
        """
        Inicializa SemanticCluster aggregate.

        Args:
            id: Identificador único del cluster
            label: Label descriptivo del cluster
            centroid: Centroid del cluster (embedding promedio)
            article_ids: Lista de IDs de artículos (default: [])
            size: Número de artículos (default: len(article_ids))
            top_terms: Términos frecuentes con frecuencias (default: [])
            created_at: Timestamp de creación
            updated_at: Timestamp de última actualización

        Raises:
            ValueError: Si los parámetros son inválidos
        """
        super().__init__()

        self._id = id
        self._label = label
        self._centroid = centroid
        self._article_ids = article_ids or []
        self._size = size if size is not None else len(self._article_ids)
        self._top_terms = top_terms or []
        self._created_at = created_at or datetime.now(timezone.utc)
        self._updated_at = updated_at or datetime.now(timezone.utc)

        # Validar invariantes iniciales
        if not self._label or not self._label.strip():
            raise ValueError("label no puede estar vacío")

        if self._centroid.dimension != 768:
            raise ValueError("centroid debe tener dimensión 768")

        if self._size != len(self._article_ids):
            raise ValueError(
                f"size ({self._size}) debe ser igual a len(article_ids) ({len(self._article_ids)})"
            )

        if self._size < 0:
            raise ValueError("size no puede ser negativo")

        # Validar top_terms
        for term, freq in self._top_terms:
            if freq <= 0:
                raise ValueError(
                    f"Frecuencia de término debe ser > 0, recibido: {freq}"
                )

    @property
    def id(self) -> ClusterId:
        """ID único del cluster."""
        return self._id

    @property
    def label(self) -> str:
        """Label descriptivo del cluster."""
        return self._label

    @property
    def centroid(self) -> VectorEmbedding:
        """Centroid del cluster."""
        return self._centroid

    @property
    def article_ids(self) -> List[str]:
        """Lista de IDs de artículos en el cluster."""
        return self._article_ids.copy()

    @property
    def size(self) -> int:
        """Número de artículos en el cluster."""
        return self._size

    @property
    def top_terms(self) -> List[Tuple[str, float]]:
        """Términos más frecuentes con sus frecuencias."""
        return self._top_terms.copy()

    @property
    def created_at(self) -> datetime:
        """Timestamp de creación."""
        return self._created_at

    @property
    def updated_at(self) -> datetime:
        """Timestamp de última actualización."""
        return self._updated_at

    @classmethod
    def create(
        cls,
        label: str,
        centroid: VectorEmbedding,
        cluster_id: Optional[ClusterId] = None,
        top_terms: Optional[List[Tuple[str, float]]] = None,
    ) -> "SemanticCluster":
        """
        Factory method para crear un nuevo SemanticCluster.

        Args:
            label: Label descriptivo del cluster
            centroid: Centroid del cluster
            cluster_id: ID opcional (se genera si no se provee)
            top_terms: Términos frecuentes opcionales

        Returns:
            SemanticCluster nuevo y vacío

        Raises:
            ValueError: Si los parámetros son inválidos

        Examples:
            >>> cluster = SemanticCluster.create(
            ...     label="Bitcoin Regulation",
            ...     centroid=embedding,
            ... )
            >>> cluster.size
            0
            >>> len(cluster.article_ids)
            0
        """
        cluster_id = cluster_id or ClusterId.generate()

        return cls(
            id=cluster_id,
            label=label,
            centroid=centroid,
            top_terms=top_terms,
        )

    def add_article(self, article_id: str) -> None:
        """
        Agrega artículo al cluster.

        Invariantes:
        - No duplicar article_ids
        - Mantener size sincronizado
        - article_id no puede estar vacío

        Args:
            article_id: ID del artículo a agregar

        Raises:
            ValueError: Si el artículo ya está en el cluster o es inválido

        Examples:
            >>> cluster = SemanticCluster.create("Label", centroid)
            >>> cluster.add_article("article-123")
            >>> cluster.size
            1
            >>> "article-123" in cluster.article_ids
            True
        """
        # Validar parámetro
        if not article_id or not article_id.strip():
            raise ValueError("article_id no puede estar vacío")

        # Invariante: No duplicar article_ids
        if article_id in self._article_ids:
            raise ValueError(f"Article {article_id} ya está en el cluster")

        # Agregar artículo
        self._article_ids.append(article_id)
        self._size += 1
        self._updated_at = datetime.now(timezone.utc)

        # Emitir evento
        self._add_domain_event(
            ArticleAddedToClusterEvent(
                cluster_id=str(self._id),
                article_id=article_id,
            )
        )

    def remove_article(self, article_id: str) -> None:
        """
        Remueve artículo del cluster.

        Invariantes:
        - Artículo debe existir en el cluster
        - Mantener size sincronizado

        Args:
            article_id: ID del artículo a remover

        Raises:
            ValueError: Si el artículo no está en el cluster

        Examples:
            >>> cluster = SemanticCluster.create("Label", centroid)
            >>> cluster.add_article("article-123")
            >>> cluster.remove_article("article-123")
            >>> cluster.size
            0
            >>> "article-123" in cluster.article_ids
            False
        """
        # Invariante: Artículo debe existir
        if article_id not in self._article_ids:
            raise ValueError(f"Article {article_id} no está en el cluster")

        # Remover artículo
        self._article_ids.remove(article_id)
        self._size -= 1
        self._updated_at = datetime.now(timezone.utc)

        # Emitir evento
        self._add_domain_event(
            ArticleRemovedFromClusterEvent(
                cluster_id=str(self._id),
                article_id=article_id,
            )
        )

    def update_centroid(self, new_centroid: VectorEmbedding) -> None:
        """
        Actualiza centroid del cluster.

        Invariantes:
        - Centroid debe ser válido (768 dims, normalizado)

        Args:
            new_centroid: Nuevo centroid del cluster

        Raises:
            ValueError: Si el centroid es inválido

        Examples:
            >>> cluster = SemanticCluster.create("Label", old_centroid)
            >>> cluster.update_centroid(new_centroid)
            >>> cluster.centroid == new_centroid
            True
        """
        # Invariante: Centroid debe ser válido
        if new_centroid.dimension != 768:
            raise ValueError("Centroid debe tener dimensión 768")

        # Actualizar centroid
        self._centroid = new_centroid
        self._updated_at = datetime.now(timezone.utc)

        # Emitir evento
        self._add_domain_event(
            ClusterCentroidUpdatedEvent(
                cluster_id=str(self._id),
                embedding_dimension=new_centroid.dimension,
            )
        )

    def update_label(
        self,
        label: str,
        top_terms: List[Tuple[str, float]],
    ) -> None:
        """
        Actualiza label y términos del cluster.

        Invariantes:
        - Label no puede estar vacío
        - Top terms deben tener frecuencia > 0

        Args:
            label: Nuevo label descriptivo
            top_terms: Lista de (término, frecuencia)

        Raises:
            ValueError: Si el label o términos son inválidos

        Examples:
            >>> cluster = SemanticCluster.create("Old Label", centroid)
            >>> cluster.update_label(
            ...     "New Label",
            ...     [("bitcoin", 0.8), ("regulation", 0.6)]
            ... )
            >>> cluster.label
            'New Label'
            >>> len(cluster.top_terms)
            2
        """
        # Invariante: Label no puede estar vacío
        if not label or not label.strip():
            raise ValueError("Label no puede estar vacío")

        # Invariante: Top terms deben tener frecuencia > 0
        for term, freq in top_terms:
            if freq <= 0:
                raise ValueError(
                    f"Frecuencia de término debe ser > 0, recibido: {freq}"
                )

        # Actualizar label y términos
        self._label = label.strip()
        self._top_terms = top_terms.copy()
        self._updated_at = datetime.now(timezone.utc)

        # Emitir evento
        self._add_domain_event(
            ClusterLabelUpdatedEvent(
                cluster_id=str(self._id),
                new_label=self._label,
                top_terms_count=len(self._top_terms),
            )
        )

    def contains_article(self, article_id: str) -> bool:
        """
        Verifica si un artículo está en el cluster.

        Args:
            article_id: ID del artículo a verificar

        Returns:
            True si el artículo está en el cluster, False en caso contrario

        Examples:
            >>> cluster = SemanticCluster.create("Label", centroid)
            >>> cluster.add_article("article-123")
            >>> cluster.contains_article("article-123")
            True
            >>> cluster.contains_article("article-456")
            False
        """
        return article_id in self._article_ids

    def is_empty(self) -> bool:
        """
        Verifica si el cluster está vacío.

        Returns:
            True si no hay artículos en el cluster, False en caso contrario

        Examples:
            >>> cluster = SemanticCluster.create("Label", centroid)
            >>> cluster.is_empty()
            True
            >>> cluster.add_article("article-123")
            >>> cluster.is_empty()
            False
        """
        return self._size == 0

    def get_top_term_names(self) -> List[str]:
        """
        Obtiene solo los nombres de los términos frecuentes.

        Returns:
            Lista de nombres de términos (sin frecuencias)

        Examples:
            >>> cluster = SemanticCluster.create("Label", centroid)
            >>> cluster.update_label("Label", [("bitcoin", 0.8), ("eth", 0.6)])
            >>> cluster.get_top_term_names()
            ['bitcoin', 'eth']
        """
        return [term for term, _ in self._top_terms]
