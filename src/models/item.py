from sqlalchemy import Column, DateTime, Index, String, Text

from src.models.base import Base, JSON_TYPE, UUID_TYPE, new_uuid, utcnow


class Item(Base):
    __tablename__ = "items"

    id = Column(UUID_TYPE, primary_key=True, default=new_uuid)
    source = Column(String(50), nullable=False)
    type = Column(String(50), nullable=False)
    title = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    url = Column(Text, nullable=True)
    tags = Column(JSON_TYPE, nullable=False, default=list)
    metadata_json = Column("metadata", JSON_TYPE, nullable=False, default=dict)
    published_at = Column(DateTime(timezone=False), nullable=True)
    created_at = Column(DateTime(timezone=False), nullable=False, default=utcnow)
    updated_at = Column(
        DateTime(timezone=False),
        nullable=False,
        default=utcnow,
        onupdate=utcnow,
    )

    __table_args__ = (
        Index("idx_items_source", "source"),
        Index("idx_items_type", "type"),
        Index("idx_items_published_at", "published_at"),
        Index("idx_items_title", "title"),
        Index("idx_items_source_type", "source", "type"),
        Index("idx_items_url", "url"),
    )
