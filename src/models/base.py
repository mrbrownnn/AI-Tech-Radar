import uuid
from datetime import datetime

from sqlalchemy import DateTime, JSON, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase


UUID_TYPE = UUID(as_uuid=False).with_variant(String(36), "sqlite")
JSON_TYPE = JSONB().with_variant(JSON(), "sqlite")


def new_uuid() -> str:
    return str(uuid.uuid4())


def utcnow() -> datetime:
    return datetime.utcnow()


class Base(DeclarativeBase):
    pass


CREATED_AT = DateTime(timezone=False)

