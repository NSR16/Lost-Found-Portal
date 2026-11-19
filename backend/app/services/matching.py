"""
services/matching.py
--------------------
Strategy pattern for suggesting FOUND items that may match a LOST item.

    MatchingStrategy (interface)
      ├── KeywordOverlapStrategy   – Python keyword scoring (the logic that used
      │                              to live inside routers/items.py)
      └── StoredProcedureStrategy  – delegates to MySQL sp_match_lost_item
                                      (FULLTEXT relevance), defined in schema.sql

MatchingService is the context: it looks up the LOST item and delegates ranking
to whichever strategy it was given. This is keyword matching, not AI/ML.
"""

from abc import ABC, abstractmethod
from typing import List

from sqlalchemy import text
from sqlalchemy.orm import Session

from app import models
from app.services.errors import NotFoundError


class MatchingStrategy(ABC):
    """Ranks candidate FOUND items for a given LOST item."""

    @abstractmethod
    def rank(self, db: Session, lost_item: models.Item, limit: int = 10) -> List[models.Item]:
        """Return up to `limit` FOUND items, best match first."""


class KeywordOverlapStrategy(MatchingStrategy):
    """Same category, ACTIVE, not deleted; score = shared words with the lost title."""

    def rank(self, db: Session, lost_item: models.Item, limit: int = 10) -> List[models.Item]:
        candidates = (
            db.query(models.Item)
            .filter(
                models.Item.type == models.ItemType.FOUND,
                models.Item.status == models.ItemStatus.ACTIVE,
                models.Item.category_id == lost_item.category_id,
                models.Item.is_deleted == False,  # noqa: E712
            )
            .all()
        )
        lost_words = set(lost_item.title.lower().split())

        def score(candidate: models.Item) -> int:
            words = set((candidate.title + " " + (candidate.description or "")).lower().split())
            return len(lost_words & words)

        return sorted(candidates, key=score, reverse=True)[:limit]


class StoredProcedureStrategy(MatchingStrategy):
    """Uses the existing MySQL procedure sp_match_lost_item (FULLTEXT relevance).

    Requires MySQL with the procedure from schema.sql installed.
    """

    def rank(self, db: Session, lost_item: models.Item, limit: int = 10) -> List[models.Item]:
        rows = db.execute(
            text("CALL sp_match_lost_item(:item_id)"), {"item_id": lost_item.item_id}
        ).fetchall()
        ids = [row.item_id for row in rows][:limit]
        if not ids:
            return []
        by_id = {
            item.item_id: item
            for item in db.query(models.Item).filter(models.Item.item_id.in_(ids)).all()
        }
        return [by_id[i] for i in ids if i in by_id]  # keep the procedure's ranking


class MatchingService:
    """Context class: finds the LOST item and delegates ranking to a strategy."""

    def __init__(self, strategy: MatchingStrategy):
        self._strategy = strategy

    def suggest(self, db: Session, item_id: int, limit: int = 10) -> List[models.Item]:
        lost_item = db.query(models.Item).filter(
            models.Item.item_id == item_id,
            models.Item.type == models.ItemType.LOST,
        ).first()
        if not lost_item:
            raise NotFoundError("Lost item not found")
        return self._strategy.rank(db, lost_item, limit)


def get_matching_service() -> MatchingService:
    """FastAPI dependency. Swap the strategy here to change the matching algorithm."""
    return MatchingService(KeywordOverlapStrategy())
