"""
routers/claims.py
-----------------
Claim workflow — users submit claims, finders/admins approve or reject.
Business rules now live in app/services/claim_service.py; this module only
maps HTTP requests/responses to ClaimService calls.

POST   /api/claims                      – Submit a new claim
GET    /api/claims/my                   – Claims submitted by the logged-in user
GET    /api/claims/received             – Claims on items I posted (I'm the finder)
PATCH  /api/claims/{claim_id}/status   – Approve or reject (finder/admin only)
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app import models, schemas
from app.auth import get_current_user
from app.database import get_db
from app.services.claim_service import ClaimService
from app.services.errors import (
    ConflictError,
    ForbiddenError,
    NotFoundError,
    ServiceError,
    ValidationError,
)

router = APIRouter(prefix="/api/claims", tags=["Claims"])

_HTTP_STATUS = {
    NotFoundError: 404,
    ForbiddenError: 403,
    ValidationError: 400,
    ConflictError: 409,
}


def get_claim_service() -> ClaimService:
    """FastAPI dependency; override in tests to inject a fake service."""
    return ClaimService()


def _to_http(exc: ServiceError) -> HTTPException:
    return HTTPException(_HTTP_STATUS.get(type(exc), 400), exc.message)


@router.post("", response_model=schemas.ClaimOut, status_code=201)
def submit_claim(
    payload:      schemas.ClaimCreate,
    db:           Session       = Depends(get_db),
    current_user: models.User   = Depends(get_current_user),
    service:      ClaimService  = Depends(get_claim_service),
):
    try:
        return service.submit(db, current_user, payload.item_id, payload.proof_description)
    except ServiceError as exc:
        raise _to_http(exc)

@router.get("/my", response_model=List[schemas.ClaimOut])
def my_claims(
    db:           Session     = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    claims = (
        db.query(models.Claim)
        .options(
            joinedload(models.Claim.item).joinedload(models.Item.poster),
            joinedload(models.Claim.claimer),
        )
        .join(models.Item, models.Claim.item_id == models.Item.item_id)
        .filter(
            models.Claim.claimer_id == current_user.user_id,
            models.Item.is_deleted == False,
        )
        .order_by(models.Claim.created_at.desc())
        .all()
    )

    return [schemas.ClaimOut.model_validate(claim) for claim in claims]


@router.get("/received", response_model=List[schemas.ClaimOut])
def received_claims(
    db:           Session     = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Claims on items that the current user posted (they are the finder/loser)."""
    claims = (
        db.query(models.Claim)
        .options(
            joinedload(models.Claim.item).joinedload(models.Item.poster),
            joinedload(models.Claim.claimer),
        )
        .join(models.Item, models.Claim.item_id == models.Item.item_id)
        .filter(
            models.Item.user_id == current_user.user_id,
            models.Item.is_deleted == False,
        )
        .order_by(models.Claim.created_at.desc())
        .all()
    )

    return [schemas.ClaimOut.model_validate(claim) for claim in claims]


@router.patch("/{claim_id}/status", response_model=schemas.ClaimOut)
def update_claim_status(
    claim_id:     int,
    payload:      schemas.ClaimStatusUpdate,
    db:           Session       = Depends(get_db),
    current_user: models.User   = Depends(get_current_user),
    service:      ClaimService  = Depends(get_claim_service),
):
    try:
        return service.decide(
            db, current_user, claim_id, payload.status, payload.handoff_instructions
        )
    except ServiceError as exc:
        raise _to_http(exc)
