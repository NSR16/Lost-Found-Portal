"""
routers/claims.py
-----------------
Claim workflow — users submit claims, finders/admins approve or reject.

POST   /api/claims                      – Submit a new claim
GET    /api/claims/my                   – Claims submitted by the logged-in user
GET    /api/claims/received             – Claims on items I posted (I'm the finder)
PATCH  /api/claims/{claim_id}/status   – Approve or reject (finder/admin only)
"""

from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models, schemas
from app.auth import get_current_user
from app.database import get_db
from sqlalchemy.orm import joinedload

router = APIRouter(prefix="/api/claims", tags=["Claims"])


@router.post("", response_model=schemas.ClaimOut, status_code=201)
def submit_claim(
    payload:      schemas.ClaimCreate,
    db:           Session     = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    item = db.query(models.Item).filter(models.Item.item_id == payload.item_id).first()
    if not item:
        raise HTTPException(404, "Item not found")
    if item.status == models.ItemStatus.RESOLVED or item.status == models.ItemStatus.REMOVED or item.is_deleted:
        raise HTTPException(400, "Item is no longer available")
    if item.user_id == current_user.user_id:
        raise HTTPException(400, "You cannot claim your own item")

    # Prevent duplicate claims
    existing = db.query(models.Claim).filter(
        models.Claim.item_id    == payload.item_id,
        models.Claim.claimer_id == current_user.user_id,
    ).first()
    if existing:
        raise HTTPException(409, "You have already submitted a claim for this item")

    claim = models.Claim(
        item_id           = payload.item_id,
        claimer_id        = current_user.user_id,
        proof_description = payload.proof_description,
    )
    db.add(claim)
    db.flush()

    log = models.ActivityLog(
        item_id      = item.item_id,
        action_taken = f"Claim submitted by {current_user.name}",
        performed_by = current_user.user_id,
    )
    db.add(log)
    db.commit()
    db.refresh(claim)
    return claim


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
    db:           Session     = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    claim = db.query(models.Claim).filter(models.Claim.claim_id == claim_id).first()
    if not claim:
        raise HTTPException(404, "Claim not found")

    # Only the item's poster or an admin may change claim status
    if claim.item.user_id != current_user.user_id and current_user.role != models.UserRole.admin:
        raise HTTPException(403, "Not authorised to update this claim")

    payload_status = payload.status
    has_handoff_instructions = bool(payload.handoff_instructions and payload.handoff_instructions.strip())

    if payload_status == models.ClaimStatus.APPROVED or has_handoff_instructions:
        if has_handoff_instructions and not claim.item.is_in_custody:
            raise HTTPException(400, "Handoff instructions are only needed for items in custody.")

        claim.status = models.ClaimStatus.APPROVED
        if has_handoff_instructions:
            claim.handoff_instructions = payload.handoff_instructions.strip()
        claim.resolved_at = datetime.now(timezone.utc)
        claim.item.status = models.ItemStatus.RESOLVED

        # Reject other pending claims for this item
        db.query(models.Claim).filter(
            models.Claim.item_id == claim.item_id,
            models.Claim.claim_id != claim.claim_id,
            models.Claim.status == models.ClaimStatus.PENDING
        ).update({
            "status": models.ClaimStatus.REJECTED,
            "resolved_at": datetime.now(timezone.utc)
        }, synchronize_session=False)

        log = models.ActivityLog(
            item_id      = claim.item_id,
            action_taken = f"Claim confirmed. Item marked RESOLVED and returned to {claim.claimer.name}.",
            performed_by = current_user.user_id,
        )
        db.add(log)

    elif payload_status == models.ClaimStatus.REJECTED:
        claim.status = models.ClaimStatus.REJECTED
        claim.resolved_at = datetime.now(timezone.utc)

        log = models.ActivityLog(
            item_id      = claim.item_id,
            action_taken = f"Claim rejected by {current_user.name}.",
            performed_by = current_user.user_id,
        )
        db.add(log)

    else:
        if payload_status == models.ClaimStatus.PENDING:
            claim.status = models.ClaimStatus.PENDING
            claim.resolved_at = None

    db.commit()
    db.refresh(claim)

    # Final safety guard before responding: ensure claim.status is valid and not empty.
    if not claim.status or str(claim.status).strip() == "":
        claim.status = models.ClaimStatus.PENDING
        claim.resolved_at = None
        db.commit()
        db.refresh(claim)

    return claim
