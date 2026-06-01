from datetime import date, datetime

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from src.models.digest import DeliveryLog, Digest


class DigestRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_digest(self, *, digest_date: date, content: str, channel: str) -> Digest:
        digest = Digest(digest_date=digest_date, content=content, channel=channel)
        self.db.add(digest)
        self.db.flush()
        return digest

    def latest_digest(self, *, channel: str | None = None) -> Digest | None:
        query = select(Digest)
        if channel:
            query = query.where(Digest.channel == channel)
        query = query.order_by(desc(Digest.created_at)).limit(1)
        return self.db.scalar(query)

    def create_delivery_log(
        self,
        *,
        digest_id: str,
        channel: str,
        status: str,
        error_message: str | None = None,
        sent_at: datetime | None = None,
    ) -> DeliveryLog:
        log = DeliveryLog(
            digest_id=digest_id,
            channel=channel,
            status=status,
            error_message=error_message,
            sent_at=sent_at,
        )
        self.db.add(log)
        self.db.flush()
        return log

