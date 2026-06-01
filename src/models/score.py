from sqlalchemy import Column, DateTime, Float, ForeignKey, Index

from src.models.base import Base, UUID_TYPE, new_uuid, utcnow


class Score(Base):
    __tablename__ = "scores"

    id = Column(UUID_TYPE, primary_key=True, default=new_uuid)
    item_id = Column(UUID_TYPE, ForeignKey("items.id", ondelete="CASCADE"), nullable=False)
    popularity_score = Column(Float, nullable=False)
    activity_score = Column(Float, nullable=False)
    recency_score = Column(Float, nullable=False)
    relevance_score = Column(Float, nullable=False)
    final_score = Column(Float, nullable=False)
    created_at = Column(DateTime(timezone=False), nullable=False, default=utcnow)

    __table_args__ = (
        Index("idx_scores_item_id", "item_id"),
        Index("idx_scores_final_score", "final_score"),
        Index("idx_scores_created_at", "created_at"),
    )

