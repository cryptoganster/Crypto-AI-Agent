"""Mapper para SemanticCluster aggregate."""

import json
from typing import Optional

import numpy as np

from src.clustering.domain.aggregates.semantic_cluster import SemanticCluster
from src.clustering.domain.value_objects import ClusterId, VectorEmbedding
from src.clustering.infra.persistence.models import (
    ClusterMemberModel,
    SemanticClusterModel,
)


class SemanticClusterMapper:
    """
    Mapper entre SemanticCluster aggregate y SemanticClusterModel ORM.

    Responsabilidades:
    - Convertir aggregate → model (to_model)
    - Convertir model → aggregate (to_domain)
    - Actualizar model existente (update_model)
    - Mapear colección de ClusterMembers

    NO contiene lógica de negocio, solo transformación de datos.
    """

    @staticmethod
    def to_domain(model: SemanticClusterModel) -> SemanticCluster:
        """
        Convierte SemanticClusterModel a SemanticCluster aggregate.

        Args:
            model: Modelo ORM de SQLAlchemy

        Returns:
            SemanticCluster aggregate del dominio

        Examples:
            >>> model = SemanticClusterModel(id="cluster-123", ...)
            >>> cluster = SemanticClusterMapper.to_domain(model)
            >>> cluster.id.value
            'cluster-123'
        """
        # Deserializar centroid desde JSON
        centroid_list = json.loads(model.centroid) if model.centroid else None
        centroid = (
            VectorEmbedding(
                vector=np.array(centroid_list, dtype=np.float32),
                model="unknown",  # TODO: Agregar model al aggregate si se necesita
                dimension=len(centroid_list),
            )
            if centroid_list
            else None
        )

        # Extraer article_ids desde members
        article_ids = [member.article_id for member in model.members]

        # Deserializar top_terms (si existe, formato: "term1:freq1,term2:freq2")
        top_terms = []
        if hasattr(model, "top_terms") and model.top_terms:
            # Asumiendo formato simple por ahora
            # TODO: Agregar columna top_terms a modelo si se necesita
            pass

        return SemanticCluster(
            id=ClusterId.from_string(model.id),
            label=model.label,
            centroid=centroid,
            article_ids=article_ids,
            size=model.size,
            top_terms=top_terms,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    @staticmethod
    def to_model(cluster: SemanticCluster) -> SemanticClusterModel:
        """
        Convierte SemanticCluster aggregate a SemanticClusterModel.

        Args:
            cluster: Aggregate del dominio

        Returns:
            Modelo ORM de SQLAlchemy

        Examples:
            >>> cluster = SemanticCluster.create("Label", centroid)
            >>> model = SemanticClusterMapper.to_model(cluster)
            >>> model.id
            'cluster-...'
        """
        # Serializar centroid a JSON
        centroid_json = json.dumps(cluster.centroid.vector.tolist())

        # Crear modelo
        model = SemanticClusterModel(
            id=str(cluster.id),
            label=cluster.label,
            description=None,  # TODO: Agregar description al aggregate si se necesita
            size=cluster.size,
            centroid=centroid_json,
            algorithm="unknown",  # TODO: Agregar algorithm al aggregate
            created_at=cluster.created_at,
            updated_at=cluster.updated_at,
        )

        # Crear members
        model.members = [
            ClusterMemberModel(
                id=f"{cluster.id}-{article_id}",
                cluster_id=str(cluster.id),
                article_id=article_id,
                distance_to_centroid=None,  # TODO: Calcular si se necesita
            )
            for article_id in cluster.article_ids
        ]

        return model

    @staticmethod
    def update_model(
        model: SemanticClusterModel,
        cluster: SemanticCluster,
    ) -> None:
        """
        Actualiza modelo ORM existente con datos del aggregate.

        Args:
            model: Modelo ORM existente
            cluster: Aggregate con datos actualizados

        Examples:
            >>> model = SemanticClusterModel(id="cluster-123", ...)
            >>> cluster = SemanticCluster(...)
            >>> SemanticClusterMapper.update_model(model, cluster)
            >>> model.label == cluster.label
            True
        """
        # Actualizar campos básicos
        model.label = cluster.label
        model.size = cluster.size
        model.updated_at = cluster.updated_at

        # Actualizar centroid
        model.centroid = json.dumps(cluster.centroid.vector.tolist())

        # Actualizar members (remover todos y recrear)
        # Esto es más simple que hacer diff, y SQLAlchemy maneja el cascade
        model.members.clear()

        for article_id in cluster.article_ids:
            member = ClusterMemberModel(
                id=f"{cluster.id}-{article_id}",
                cluster_id=str(cluster.id),
                article_id=article_id,
                distance_to_centroid=None,
            )
            model.members.append(member)
