"""SQLAlchemy model for ClusterMember entity."""

from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Index, String
from sqlalchemy.orm import relationship

from src.shared.infra.persistence.sqlalchemy_base_model import Base


class ClusterMemberModel(Base):
    """
    ORM model for cluster_members table.

    Representa la membresía de un artículo en un cluster.
    """

    __tablename__ = "cluster_members"

    # Primary key
    id = Column(String, primary_key=True)

    # Foreign keys
    cluster_id = Column(
        String, ForeignKey("semantic_clusters.id", ondelete="CASCADE"), nullable=False
    )
    article_id = Column(String, nullable=False, index=True)

    # Member properties
    distance_to_centroid = Column(Float, nullable=True)

    # Timestamps
    added_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    cluster = relationship("SemanticClusterModel", back_populates="members")

    # Indexes
    __table_args__ = (
        Index("ix_cluster_members_cluster_id", "cluster_id"),
        Index("ix_cluster_members_article_id", "article_id"),
        Index(
            "ix_cluster_members_cluster_article",
            "cluster_id",
            "article_id",
            unique=True,
        ),
    )

    def __repr__(self) -> str:
        return f"<ClusterMemberModel(id={self.id}, cluster_id={self.cluster_id}, article_id={self.article_id})>"
