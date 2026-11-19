"""Runs an identical request sequence against the ORIGINAL claims router and the
refactored (ClaimService) router, each on its own fresh SQLite database, and
asserts identical HTTP responses and identical final database state."""
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from app import models
from app.auth import get_current_user
from app.database import Base, get_db
import claims_original_reference as original
import app.routers.claims as refactored

POSTER, A, B, ADMIN, OTHER = 1, 2, 3, 4, 5


def make_client(router):
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    Maker = sessionmaker(bind=engine, autoflush=False)
    state = {"uid": None}
    app = FastAPI()
    app.include_router(router)

    def _db():
        db = Maker()
        try:
            yield db
        finally:
            db.close()

    def _user(db: Session = Depends(get_db)):
        return db.get(models.User, state["uid"])

    app.dependency_overrides[get_db] = _db
    app.dependency_overrides[get_current_user] = _user

    s = Maker()
    s.add(models.Category(category_id=1, category_name="Accessories"))
    for uid, name, role in [(POSTER, "Poster", "student"), (A, "Alice", "student"),
                            (B, "Bob", "student"), (ADMIN, "Admin", "admin"), (OTHER, "Other", "student")]:
        s.add(models.User(user_id=uid, name=name, roll_number=f"R{uid}", email=f"u{uid}@x.com",
                          password_hash="x", dept="CSE", role=models.UserRole(role)))
    def item(i, typ, status=models.ItemStatus.ACTIVE, custody=False, deleted=False):
        s.add(models.Item(item_id=i, title=f"item {i}", type=typ, status=status, is_in_custody=custody,
                          is_deleted=deleted, user_id=POSTER, category_id=1))
    F, L = models.ItemType.FOUND, models.ItemType.LOST
    item(1, F, custody=True); item(2, L); item(3, F, status=models.ItemStatus.RESOLVED)
    item(4, F, deleted=True); item(5, F, status=models.ItemStatus.REMOVED); item(6, F, custody=True)
    s.commit(); s.close()
    return TestClient(app), state, Maker


def snapshot(Maker):
    s = Maker()
    out = {
        "claims": [(c.claim_id, c.item_id, c.claimer_id, c.status.value, c.handoff_instructions,
                    c.resolved_at is not None) for c in s.query(models.Claim).order_by(models.Claim.claim_id)],
        "items": [(i.item_id, i.status.value) for i in s.query(models.Item).order_by(models.Item.item_id)],
        "logs": [(l.item_id, l.action_taken, l.performed_by) for l in s.query(models.ActivityLog).order_by(models.ActivityLog.log_id)],
    }
    s.close()
    return out


def clean(obj):
    if isinstance(obj, dict):
        return {k: clean(v) for k, v in obj.items() if k not in ("created_at", "resolved_at")}
    if isinstance(obj, list):
        return [clean(x) for x in obj]
    return obj


def post(uid, item_id, proof="mine"):
    return (uid, "POST", "/api/claims", {"item_id": item_id, "proof_description": proof})

def patch(uid, claim_id, status, handoff=None):
    body = {"status": status}
    if handoff is not None:
        body["handoff_instructions"] = handoff
    return (uid, "PATCH", f"/api/claims/{claim_id}/status", body)

def get(uid, url):
    return (uid, "GET", url, None)


SEQUENCE = [
    post(A, 99), post(A, 3), post(A, 4), post(A, 5), post(POSTER, 1),
    post(A, 1), post(A, 1), post(B, 1),
    patch(OTHER, 1, "APPROVED"), patch(POSTER, 99, "APPROVED"),
    patch(POSTER, 1, "APPROVED", "meet at library"),
    get(A, "/api/claims/my"), get(POSTER, "/api/claims/received"), get(B, "/api/claims/my"),
    patch(POSTER, 2, "PENDING"),
    post(A, 2), patch(POSTER, 3, "APPROVED", "bring id"), patch(POSTER, 3, "REJECTED"),
    post(A, 6), patch(POSTER, 4, "REJECTED", "quirk: handoff text on a reject"),
    patch(ADMIN, 3, "approved"), patch(POSTER, 3, "PENDING"), patch(POSTER, 3, "BOGUS"),
    patch(POSTER, 2, "REJECTED"),
]


def run(router):
    client, state, Maker = make_client(router)
    results = []
    for uid, method, url, body in SEQUENCE:
        state["uid"] = uid
        r = client.request(method, url, json=body)
        results.append((r.status_code, clean(r.json())))
    return results, snapshot(Maker)


def test_identical_responses_and_database_state():
    orig_results, orig_db = run(original.router)
    new_results, new_db = run(refactored.router)
    for step, (o, n) in enumerate(zip(orig_results, new_results)):
        assert o == n, f"step {step} {SEQUENCE[step][1:3]} differs:\n original={o}\n refactored={n}"
    assert orig_db == new_db


def test_sequence_exercises_every_branch():
    codes = [c for c, _ in run(refactored.router)[0]]
    assert {201, 200, 400, 403, 404, 409, 422} <= set(codes)
