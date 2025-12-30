"""SQLAlchemy model for SemanticCluster aggregate."""

from datetime import datetime
from typing import List

from sqlalchemy import Column, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import relationship

from src.shared.infra.persistence.sqlalchemy_base_model import Base


class SemanticClusterModel(Base):
    """
    ORM model for semantic_clusters table.

    Representa un cluster semántico de artículos relacionados.
    """

    __tablename__ = "semantic_clusters"

    # Primary key
    id = Column(String, primary_key=True)

    # Cluster properties
    label = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    size = Column(Integer, nullable=False, default=0)

    # Centroid (stored as JSON array of floats)
    centroid = Column(Text, nullable=True)  # JSON serialized list of floats

    # Algorithm metadata
    algorithm = Column(String(50), nullable=False)  # "kmeans", "dbscan", etc.

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    members = relationship(
        "ClusterMemberModel",
        back_populates="cluster",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<SemanticClusterModel(id={self.id}, label={self.label}, size={self.size})>"
