"""
routers/items.py
----------------
CRUD for the Items table + image upload + matching engine.

GET    /api/items            – List all active items (filterable by type/category)
POST   /api/items            – Post a new lost/found item (auth required)
GET    /api/items/my         – Get user's own posted items
POST   /api/items/upload     – Upload an image, returns its URL
GET    /api/items/{id}/match – Matching engine: suggest FOUND items for a LOST item
PATCH  /api/items/{id}/delete – Soft delete (mark as deleted) own item
PATCH  /api/items/{id}/remove – Mark item as REMOVED (old endpoint)
GET    /api/items/{id}       – Get single item details
PATCH  /api/items/{id}       – Update title/description/location/status
DELETE /api/items/{id}       – Hard delete own item
"""

import os
import uuid
from typing import Optional, List

import aiofiles
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy import or_, func
from sqlalchemy.orm import Session

from app import models, schemas
from app.auth import get_current_user
from app.database import get_db

router = APIRouter(prefix="/api/items", tags=["Items"])

UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


# ── List items (query-based, matches "" route) ────────────────────────────

@router.get("", response_model=List[schemas.ItemOut])
def list_items(
    type:        Optional[str] = Query(None, description="LOST or FOUND"),
    category_id: Optional[int] = Query(None),
    status:      Optional[str] = Query(None, description="Filter by status, e.g. ACTIVE"),
    search:      Optional[str] = Query(None, description="Keyword search in title/description"),
    db:          Session       = Depends(get_db),
):
    q = db.query(models.Item)

    if type:
        q = q.filter(models.Item.type == type.upper())
    if category_id:
        q = q.filter(models.Item.category_id == category_id)
    if status:
        q = q.filter(models.Item.status == status.upper())
    else:
        q = q.filter(models.Item.status.notin_([models.ItemStatus.REMOVED, models.ItemStatus.RESOLVED]))
    
    # Filter out soft-deleted items
    q = q.filter(models.Item.is_deleted == False)
    
    if search:
        like = f"%{search}%"
        q = q.filter(
            or_(
                models.Item.title.ilike(like),
                models.Item.description.ilike(like),
            )
        )

    items = q.order_by(models.Item.posted_at.desc()).all()

    result = []
    for item in items:
        out = schemas.ItemOut.model_validate(item)
        out.category_name = item.category.category_name if item.category else ""
        out.posted_by     = item.poster.name if item.poster else ""
        result.append(out)
    return result


# ── Create item ────────────────────────────────────────────────────────────

@router.post("", response_model=schemas.ItemOut, status_code=201)
def create_item(
    payload:      schemas.ItemCreate,
    db:           Session      = Depends(get_db),
    current_user: models.User  = Depends(get_current_user),
):
    # Verify category exists
    cat = db.query(models.Category).filter(models.Category.category_id == payload.category_id).first()
    if not cat:
        raise HTTPException(404, "Category not found")

    item = models.Item(
        title          = payload.title,
        description    = payload.description,
        type           = payload.type,
        location       = payload.location,
        image_url      = payload.image_url,
        is_in_custody  = payload.is_in_custody if payload.is_in_custody is not None else (payload.type == models.ItemType.FOUND),
        category_id    = payload.category_id,
        user_id        = current_user.user_id,
    )
    db.add(item)
    db.flush()  # get item_id before committing

    # Auto-log the creation
    log = models.ActivityLog(
        item_id      = item.item_id,
        action_taken = f"Item posted as {item.type} by {current_user.name}",
        performed_by = current_user.user_id,
    )
    db.add(log)
    db.commit()
    db.refresh(item)

    out = schemas.ItemOut.model_validate(item)
    out.category_name = cat.category_name
    out.posted_by     = current_user.name
    return out


# ── STATIC ROUTES (before dynamic /{item_id}) ──────────────────────────────

@router.get("/my", response_model=List[schemas.ItemOut])
def my_items(
    db:           Session     = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Get all active items posted by the current user (exclude deleted)."""
    items = (
        db.query(models.Item)
        .filter(models.Item.user_id == current_user.user_id)
        .filter(models.Item.is_deleted == False)
        .order_by(models.Item.posted_at.desc())
        .all()
    )

    result = []
    for item in items:
        out = schemas.ItemOut.model_validate(item)
        out.category_name = item.category.category_name if item.category else ""
        out.posted_by     = item.poster.name if item.poster else ""
        result.append(out)
    return result


@router.post("/upload", status_code=201)
async def upload_image(
    file:         UploadFile    = File(...),
    current_user: models.User   = Depends(get_current_user),
):
    """Upload an image and return its URL."""
    MAX_MB  = int(os.getenv("MAX_UPLOAD_SIZE_MB", "5"))
    content = await file.read()
    if len(content) > MAX_MB * 1024 * 1024:
        raise HTTPException(413, f"File too large. Max {MAX_MB} MB allowed.")

    ext      = os.path.splitext(file.filename or "file.jpg")[1]
    filename = f"{uuid.uuid4().hex}{ext}"
    path     = os.path.join(UPLOAD_DIR, filename)

    async with aiofiles.open(path, "wb") as f:
        await f.write(content)

    return {"image_url": filename}


# ── DYNAMIC ROUTES WITH SUFFIXES (before base /{item_id}) ──────────────────

@router.get("/{item_id}/match", response_model=List[schemas.MatchResult])
def match_item(item_id: int, db: Session = Depends(get_db)):
    """
    For a given LOST item, suggest FOUND items that share the same category.
    Items whose title/description overlap with the lost item's title are ranked first.
    """
    lost_item = db.query(models.Item).filter(
        models.Item.item_id == item_id,
        models.Item.type    == models.ItemType.LOST,
    ).first()
    if not lost_item:
        raise HTTPException(404, "Lost item not found")

    # Pull all active FOUND items in the same category (exclude deleted)
    candidates = (
        db.query(models.Item)
        .filter(
            models.Item.type        == models.ItemType.FOUND,
            models.Item.status      == models.ItemStatus.ACTIVE,
            models.Item.category_id == lost_item.category_id,
            models.Item.is_deleted  == False,
        )
        .all()
    )

    # Simple keyword scoring: count overlapping words in title
    lost_words = set(lost_item.title.lower().split())

    def score(candidate: models.Item) -> int:
        cand_words = set((candidate.title + " " + (candidate.description or "")).lower().split())
        return len(lost_words & cand_words)

    ranked = sorted(candidates, key=score, reverse=True)[:10]

    return [
        schemas.MatchResult(
            item_id       = i.item_id,
            title         = i.title,
            description   = i.description,
            location      = i.location,
            image_url     = i.image_url,
            category_name = i.category.category_name if i.category else "",
            found_by      = i.poster.name if i.poster else "",
            posted_at     = i.posted_at,
        )
        for i in ranked
    ]


@router.patch("/{item_id}/delete", response_model=schemas.ItemOut)
def soft_delete_item(
    item_id:      int,
    db:           Session     = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Soft delete: mark item as deleted without removing from database."""
    item = db.query(models.Item).filter(models.Item.item_id == item_id).first()
    if not item:
        raise HTTPException(404, "Item not found")
    if item.user_id != current_user.user_id and current_user.role != models.UserRole.admin:
        raise HTTPException(403, "Not authorised")

    item.is_deleted = True

    log = models.ActivityLog(
        item_id      = item.item_id,
        action_taken = "Item deleted by owner",
        performed_by = current_user.user_id,
    )
    db.add(log)
    db.commit()
    db.refresh(item)
    return item


@router.patch("/{item_id}/remove", response_model=schemas.ItemOut)
def remove_item(
    item_id:      int,
    db:           Session     = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Mark item status as REMOVED (legacy endpoint)."""
    item = db.query(models.Item).filter(models.Item.item_id == item_id).first()
    if not item:
        raise HTTPException(404, "Item not found")
    if item.user_id != current_user.user_id and current_user.role != models.UserRole.admin:
        raise HTTPException(403, "Not authorised")

    item.status = models.ItemStatus.REMOVED

    log = models.ActivityLog(
        item_id      = item.item_id,
        action_taken = "Item marked REMOVED by owner",
        performed_by = current_user.user_id,
    )
    db.add(log)
    db.commit()
    db.refresh(item)
    return item


# ── BASE DYNAMIC ROUTES (/{item_id}) ───────────────────────────────────────

@router.get("/{item_id}", response_model=schemas.ItemOut)
def get_item(item_id: int, db: Session = Depends(get_db)):
    """Get a single item by ID (only non-deleted items)."""
    item = db.query(models.Item).filter(
        models.Item.item_id == item_id,
        models.Item.is_deleted == False
    ).first()
    if not item:
        raise HTTPException(404, "Item not found")
    out = schemas.ItemOut.model_validate(item)
    out.category_name = item.category.category_name if item.category else ""
    out.posted_by     = item.poster.name if item.poster else ""
    return out


@router.patch("/{item_id}", response_model=schemas.ItemOut)
def update_item(
    item_id:      int,
    payload:      schemas.ItemUpdate,
    db:           Session     = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Update item details."""
    item = db.query(models.Item).filter(models.Item.item_id == item_id).first()
    if not item:
        raise HTTPException(404, "Item not found")
    if item.user_id != current_user.user_id and current_user.role != models.UserRole.admin:
        raise HTTPException(403, "Not authorised")

    update_data = payload.model_dump(exclude_unset=True)
    for key, val in update_data.items():
        setattr(item, key, val)

    log = models.ActivityLog(
        item_id      = item.item_id,
        action_taken = f"Item updated: {', '.join(update_data.keys())}",
        performed_by = current_user.user_id,
    )
    db.add(log)
    db.commit()
    db.refresh(item)
    return item


@router.delete("/{item_id}", status_code=204)
def delete_item(
    item_id:      int,
    db:           Session     = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Hard delete an item (permanent removal from database)."""
    item = db.query(models.Item).filter(models.Item.item_id == item_id).first()
    if not item:
        raise HTTPException(404, "Item not found")
    if item.user_id != current_user.user_id and current_user.role != models.UserRole.admin:
        raise HTTPException(403, "Not authorised")
    db.delete(item)
    db.commit()
