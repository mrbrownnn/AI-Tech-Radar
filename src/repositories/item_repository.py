from datetime import datetime
from typing import Any

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from src.models.item import Item
from src.models.score import Score


class ItemRepository:
    def __init__(self, db: Session):
        self.db = db

    def upsert_item(self, data: dict[str, Any]) -> Item:
        model_data = self._to_model_data(data)
        existing = self._find_existing_item(data)
        if existing is None:
            item = Item(**model_data)
            self.db.add(item)
            self.db.flush()
            return item

        for field in (
            "source",
            "type",
            "title",
            "description",
            "url",
            "tags",
            "published_at",
        ):
            if field in model_data:
                setattr(existing, field, model_data[field])
        if "metadata_json" in model_data:
            existing.metadata_json = model_data["metadata_json"]
        self.db.flush()
        return existing

    def save_score(self, item_id: str, score_data: dict[str, float]) -> Score:
        existing = self.db.scalar(select(Score).where(Score.item_id == item_id))
        if existing is None:
            score = Score(item_id=item_id, **score_data)
            self.db.add(score)
            self.db.flush()
            return score

        for field, value in score_data.items():
            setattr(existing, field, value)
        self.db.flush()
        return existing

    def list_ranked_items(
        self,
        *,
        source: str | None = None,
        item_type: str | None = None,
        published_from: datetime | None = None,
        published_to: datetime | None = None,
        limit: int = 100,
    ) -> list[tuple[Item, Score | None]]:
        query = select(Item, Score).outerjoin(Score, Score.item_id == Item.id)
        if source:
            query = query.where(Item.source == source)
        if item_type:
            query = query.where(Item.type == item_type)
        if published_from:
            query = query.where(Item.published_at >= published_from)
        if published_to:
            query = query.where(Item.published_at < published_to)
        query = query.order_by(desc(Score.final_score), desc(Item.published_at)).limit(limit)
        return list(self.db.execute(query).all())

    def list_items_for_digest(
        self,
        *,
        published_from: datetime | None = None,
        published_to: datetime | None = None,
        limit: int = 500,
    ) -> list[tuple[Item, Score | None]]:
        query = select(Item, Score).outerjoin(Score, Score.item_id == Item.id)
        if published_from:
            query = query.where(Item.published_at >= published_from)
        if published_to:
            query = query.where(Item.published_at < published_to)
        query = query.order_by(desc(Score.final_score), desc(Item.published_at)).limit(limit)
        return list(self.db.execute(query).all())

    def _find_existing_item(self, data: dict[str, Any]) -> Item | None:
        url = data.get("url")
        if url:
            found = self.db.scalar(select(Item).where(Item.url == url))
            if found:
                return found

        title = data.get("title")
        source = data.get("source")
        if title and source:
            return self.db.scalar(
                select(Item).where(Item.source == source, Item.title == title)
            )
        return None

    @staticmethod
    def _to_model_data(data: dict[str, Any]) -> dict[str, Any]:
        model_data = dict(data)
        if "metadata" in model_data:
            model_data["metadata_json"] = model_data.pop("metadata")
        return model_data
