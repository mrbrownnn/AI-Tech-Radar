from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(frozen=True)
class CollectedItem:
    source: str
    source_id: str | None
    payload: dict[str, Any]


class Collector(Protocol):
    async def collect(self) -> list[CollectedItem]:
        ...

