from sqlalchemy import Column, Date, DateTime, ForeignKey, Index, String, Text

from src.models.base import Base, UUID_TYPE, new_uuid, utcnow


class Digest(Base):
    __tablename__ = "digests"

    id = Column(UUID_TYPE, primary_key=True, default=new_uuid)
    digest_date = Column(Date, nullable=False)
    content = Column(Text, nullable=False)
    channel = Column(String(20), nullable=False)
    created_at = Column(DateTime(timezone=False), nullable=False, default=utcnow)

    __table_args__ = (
        Index("idx_digests_digest_date", "digest_date"),
        Index("idx_digests_channel", "channel"),
        Index("idx_digests_created_at", "created_at"),
    )


class DeliveryLog(Base):
    __tablename__ = "delivery_logs"

    id = Column(UUID_TYPE, primary_key=True, default=new_uuid)
    digest_id = Column(UUID_TYPE, ForeignKey("digests.id", ondelete="CASCADE"), nullable=False)
    channel = Column(String(20), nullable=False)
    status = Column(String(20), nullable=False)
    error_message = Column(Text, nullable=True)
    sent_at = Column(DateTime(timezone=False), nullable=True)

    __table_args__ = (
        Index("idx_delivery_logs_digest_id", "digest_id"),
        Index("idx_delivery_logs_channel", "channel"),
        Index("idx_delivery_logs_status", "status"),
        Index("idx_delivery_logs_sent_at", "sent_at"),
    )

