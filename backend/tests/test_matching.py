"""Matching strategy tests. The reference function below is the ORIGINAL inline
logic from routers/items.py match_item(); the refactored strategy must rank
identically."""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import models
from app.database import Base
from app.services.errors import NotFoundError
from app.services.matching import (
    KeywordOverlapStrategy, MatchingService, StoredProcedureStrategy, get_matching_service,
)


@pytest.fixture()
def db():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    s = sessionmaker(bind=engine, autoflush=False)()
    s.add_all([models.Category(category_id=1, category_name="Electronics"),
               models.Category(category_id=2, category_name="Keys")])
    s.add(models.User(user_id=1, name="U", roll_number="R1", email="u@x.com", password_hash="x", dept="CSE"))
    F, L = models.ItemType.FOUND, models.ItemType.LOST
    rows = [  # id, type, title, description, category, status, deleted
        (1, L, "blue jbl earbuds", "lost near library", 1, "ACTIVE", False),
        (2, F, "jbl earbuds blue", "found in canteen", 1, "ACTIVE", False),
        (3, F, "black phone", "earbuds case inside", 1, "ACTIVE", False),
        (4, F, "silver watch", None, 1, "ACTIVE", False),
        (5, F, "blue jbl earbuds", "resolved one", 1, "RESOLVED", False),
        (6, F, "blue jbl earbuds", "deleted one", 1, "ACTIVE", True),
        (7, F, "blue jbl earbuds", "other category", 2, "ACTIVE", False),
        (8, F, "Blue EARBUDS", "uppercase", 1, "ACTIVE", False),
    ]
    for i, t, title, desc, cat, st, dele in rows:
        s.add(models.Item(item_id=i, title=title, description=desc, type=t, category_id=cat,
                          status=models.ItemStatus(st), is_deleted=dele, user_id=1))
    s.commit()
    yield s
    s.close()


def original_match(db, item_id):  # verbatim logic from the original endpoint
    lost_item = db.query(models.Item).filter(
        models.Item.item_id == item_id, models.Item.type == models.ItemType.LOST).first()
    candidates = (db.query(models.Item).filter(
        models.Item.type == models.ItemType.FOUND, models.Item.status == models.ItemStatus.ACTIVE,
        models.Item.category_id == lost_item.category_id, models.Item.is_deleted == False).all())
    lost_words = set(lost_item.title.lower().split())
    def score(candidate):
        cand_words = set((candidate.title + " " + (candidate.description or "")).lower().split())
        return len(lost_words & cand_words)
    return sorted(candidates, key=score, reverse=True)[:10]


def test_keyword_strategy_matches_original_ranking(db):
    expected = [i.item_id for i in original_match(db, 1)]
    actual = [i.item_id for i in MatchingService(KeywordOverlapStrategy()).suggest(db, 1)]
    assert actual == expected
    assert actual[0] == 2                      # best keyword overlap first
    assert set(actual) == {2, 3, 4, 8}         # excludes resolved, deleted, other category


def test_limit_is_respected(db):
    assert len(MatchingService(KeywordOverlapStrategy()).suggest(db, 1, limit=2)) == 2


def test_unknown_or_found_item_raises_not_found(db):
    svc = get_matching_service()
    with pytest.raises(NotFoundError):
        svc.suggest(db, 999)
    with pytest.raises(NotFoundError):
        svc.suggest(db, 2)                     # item 2 is FOUND, not LOST


def test_strategy_is_swappable(db):
    class Reverse(KeywordOverlapStrategy):
        def rank(self, db, lost_item, limit=10):
            return list(reversed(super().rank(db, lost_item, limit)))
    default = [i.item_id for i in MatchingService(KeywordOverlapStrategy()).suggest(db, 1)]
    swapped = [i.item_id for i in MatchingService(Reverse()).suggest(db, 1)]
    assert swapped == list(reversed(default))


def test_stored_procedure_strategy_keeps_procedure_order(db):
    """MySQL is not available here: the CALL result is simulated, so this checks
    only the strategy's own logic (ordering, limit, empty result), not the SQL."""
    class Row:  # mimics a result row
        def __init__(self, item_id): self.item_id = item_id
    class FakeResult:
        def __init__(self, rows): self._rows = rows
        def fetchall(self): return self._rows
    lost = db.get(models.Item, 1)
    calls = []
    real_execute = db.execute
    returned = {"rows": [Row(3), Row(2), Row(8)]}

    def fake_execute(stmt, *args, **kwargs):
        if str(stmt).startswith("CALL"):           # only intercept the procedure call
            calls.append((str(stmt), args[0] if args else None))
            return FakeResult(returned["rows"])
        return real_execute(stmt, *args, **kwargs)  # ORM queries run for real

    db.execute = fake_execute
    result = StoredProcedureStrategy().rank(db, lost, limit=2)
    assert [i.item_id for i in result] == [3, 2]
    assert calls == [("CALL sp_match_lost_item(:item_id)", {"item_id": 1})]
    returned["rows"] = []
    assert StoredProcedureStrategy().rank(db, lost) == []
