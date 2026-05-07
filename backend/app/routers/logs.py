"""
routers/logs.py
---------------
Activity log endpoints (admin or item owner access).

GET /api/logs/item/{item_id} – Audit trail for a specific item
GET /api/logs/recent         – Last N logs across the portal (admin only)
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app import models, schemas
from app.auth import get_current_user, require_admin
from app.database import get_db

router = APIRouter(prefix="/api/logs", tags=["Activity Logs"])


@router.get("/item/{item_id}", response_model=List[schemas.ActivityLogOut])
def logs_for_item(
    item_id:      int,
    db:           Session     = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    item = db.query(models.Item).filter(models.Item.item_id == item_id).first()
    if not item:
        raise HTTPException(404, "Item not found")
    if item.user_id != current_user.user_id and current_user.role != models.UserRole.admin:
        raise HTTPException(403, "Not authorised")

    return (
        db.query(models.ActivityLog)
        .filter(models.ActivityLog.item_id == item_id)
        .order_by(models.ActivityLog.timestamp.desc())
        .all()
    )


@router.get("/recent", response_model=List[schemas.ActivityLogOut])
def recent_logs(
    limit:        int         = Query(50, ge=1, le=200),
    db:           Session     = Depends(get_db),
    _admin:       models.User = Depends(require_admin),
):
    return (
        db.query(models.ActivityLog)
        .order_by(models.ActivityLog.timestamp.desc())
        .limit(limit)
        .all()
    )
