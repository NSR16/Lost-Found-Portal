"""
services/claim_service.py
-------------------------
Business logic for the claim workflow, extracted from routers/claims.py.

ClaimService owns the rules (availability checks, authorisation, status
transitions, cascade rejection, audit logging). The router only translates
HTTP <-> service calls. Behaviour is intentionally identical to the original
router code, including its message texts and status transitions.
"""

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app import models
from app.services.errors import (
    ConflictError,
    ForbiddenError,
    NotFoundError,
    ValidationError,
)


class ClaimService:
    """Submits claims and applies poster/admin decisions to them."""

    # ── Public operations ──────────────────────────────────────────────────

    def submit(
        self,
        db: Session,
        claimer: models.User,
        item_id: int,
        proof_description: Optional[str] = None,
    ) -> models.Claim:
        item = db.query(models.Item).filter(models.Item.item_id == item_id).first()
        if not item:
            raise NotFoundError("Item not found")
        if self._is_unavailable(item):
            raise ValidationError("Item is no longer available")
        if item.user_id == claimer.user_id:
            raise ValidationError("You cannot claim your own item")

        existing = db.query(models.Claim).filter(
            models.Claim.item_id == item_id,
            models.Claim.claimer_id == claimer.user_id,
        ).first()
        if existing:
            raise ConflictError("You have already submitted a claim for this item")

        claim = models.Claim(
            item_id=item_id,
            claimer_id=claimer.user_id,
            proof_description=proof_description,
        )
        db.add(claim)
        db.flush()

        self._log(db, item.item_id, f"Claim submitted by {claimer.name}", claimer.user_id)
        db.commit()
        db.refresh(claim)
        return claim

    def decide(
        self,
        db: Session,
        actor: models.User,
        claim_id: int,
        new_status: models.ClaimStatus,
        handoff_instructions: Optional[str] = None,
    ) -> models.Claim:
        claim = db.query(models.Claim).filter(models.Claim.claim_id == claim_id).first()
        if not claim:
            raise NotFoundError("Claim not found")

        if not self._may_manage(actor, claim.item):
            raise ForbiddenError("Not authorised to update this claim")

        has_handoff = bool(handoff_instructions and handoff_instructions.strip())

        # NOTE: kept from the original router: handoff text on any request
        # is treated as an approval.
        if new_status == models.ClaimStatus.APPROVED or has_handoff:
            self._approve(db, actor, claim, handoff_instructions if has_handoff else None)
        elif new_status == models.ClaimStatus.REJECTED:
            self._reject(db, actor, claim)
        elif new_status == models.ClaimStatus.PENDING:
            self._reopen(claim)

        db.commit()
        db.refresh(claim)
        return claim

    # ── State transitions (private) ────────────────────────────────────────

    def _approve(
        self,
        db: Session,
        actor: models.User,
        claim: models.Claim,
        handoff_instructions: Optional[str],
    ) -> None:
        if handoff_instructions is not None and not claim.item.is_in_custody:
            raise ValidationError("Handoff instructions are only needed for items in custody.")

        claim.status = models.ClaimStatus.APPROVED
        if handoff_instructions is not None:
            claim.handoff_instructions = handoff_instructions.strip()
        claim.resolved_at = datetime.now(timezone.utc)
        claim.item.status = models.ItemStatus.RESOLVED

        # Reject every other pending claim on the same item.
        db.query(models.Claim).filter(
            models.Claim.item_id == claim.item_id,
            models.Claim.claim_id != claim.claim_id,
            models.Claim.status == models.ClaimStatus.PENDING,
        ).update(
            {"status": models.ClaimStatus.REJECTED, "resolved_at": datetime.now(timezone.utc)},
            synchronize_session=False,
        )

        self._log(
            db,
            claim.item_id,
            f"Claim confirmed. Item marked RESOLVED and returned to {claim.claimer.name}.",
            actor.user_id,
        )

    def _reject(self, db: Session, actor: models.User, claim: models.Claim) -> None:
        claim.status = models.ClaimStatus.REJECTED
        claim.resolved_at = datetime.now(timezone.utc)
        self._log(db, claim.item_id, f"Claim rejected by {actor.name}.", actor.user_id)

    @staticmethod
    def _reopen(claim: models.Claim) -> None:
        claim.status = models.ClaimStatus.PENDING
        claim.resolved_at = None

    # ── Helpers (private) ──────────────────────────────────────────────────

    @staticmethod
    def _is_unavailable(item: models.Item) -> bool:
        return (
            item.status == models.ItemStatus.RESOLVED
            or item.status == models.ItemStatus.REMOVED
            or bool(item.is_deleted)
        )

    @staticmethod
    def _may_manage(actor: models.User, item: models.Item) -> bool:
        """Only the item's poster or an admin may decide on its claims."""
        return item.user_id == actor.user_id or actor.role == models.UserRole.admin

    @staticmethod
    def _log(db: Session, item_id: int, action: str, performed_by: int) -> None:
        db.add(models.ActivityLog(item_id=item_id, action_taken=action, performed_by=performed_by))
