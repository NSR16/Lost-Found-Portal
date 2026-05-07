"""
routers/categories.py
---------------------
Read-only category endpoints (seeded via schema.sql).

GET /api/categories      – List all categories
GET /api/categories/{id} – Get a single category
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db

router = APIRouter(prefix="/api/categories", tags=["Categories"])


@router.get("", response_model=List[schemas.CategoryOut])
def list_categories(db: Session = Depends(get_db)):
    return db.query(models.Category).order_by(models.Category.category_name).all()


@router.get("/{category_id}", response_model=schemas.CategoryOut)
def get_category(category_id: int, db: Session = Depends(get_db)):
    cat = db.query(models.Category).filter(models.Category.category_id == category_id).first()
    if not cat:
        raise HTTPException(404, "Category not found")
    return cat
