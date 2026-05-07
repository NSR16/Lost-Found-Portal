"""
schemas.py
----------
Pydantic schemas for request validation and response serialization.
Keeps the API layer decoupled from the ORM models.
"""

from __future__ import annotations
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, field_validator
from app.models import ItemType, ItemStatus, ClaimStatus, UserRole


# ── Auth ──────────────────────────────────────────────────────────────────

class UserCreate(BaseModel):
    name:        str
    roll_number: str
    email:       EmailStr
    password:    str
    dept:        str

class UserOut(BaseModel):
    user_id:    int
    name:       str
    roll_number:str
    email:      str
    dept:       str
    role:       UserRole
    created_at: datetime

    model_config = {"from_attributes": True}

class Token(BaseModel):
    access_token: str
    token_type:   str = "bearer"

class LoginRequest(BaseModel):
    email:    EmailStr
    password: str


# ── Categories ────────────────────────────────────────────────────────────

class CategoryOut(BaseModel):
    category_id:   int
    category_name: str
    description:   Optional[str] = None

    model_config = {"from_attributes": True}


# ── Items ─────────────────────────────────────────────────────────────────

class ItemCreate(BaseModel):
    title:         str
    description:   Optional[str] = None
    type:          ItemType
    location:      Optional[str] = None
    image_url:     Optional[str] = None
    category_id:   int
    is_in_custody: Optional[bool] = None

class ItemUpdate(BaseModel):
    title:         Optional[str]       = None
    description:   Optional[str]       = None
    location:      Optional[str]       = None
    status:        Optional[ItemStatus] = None
    is_in_custody: Optional[bool]       = None

class ItemOut(BaseModel):
    item_id:        int
    title:          str
    description:    Optional[str] = None
    type:           ItemType
    location:       Optional[str] = None
    image_url:      Optional[str] = None
    status:         ItemStatus
    is_in_custody:  Optional[bool] = None
    is_deleted:     Optional[bool] = False
    posted_at:      datetime
    category_name:  str        = ""
    posted_by:      str        = ""

    model_config = {"from_attributes": True}

    @field_validator("status", mode="before")
    @classmethod
    def normalize_status(cls, value):
        if isinstance(value, str):
            return value.strip().upper()
        return value

    @field_validator("description", "location", "image_url", mode="before")
    @classmethod
    def normalize_optional_strings(cls, value):
        if value == "":
            return None
        return value


# ── Claims ────────────────────────────────────────────────────────────────

class ClaimCreate(BaseModel):
    item_id:           int
    proof_description: Optional[str] = None
    handoff_instructions: Optional[str] = None

class ClaimStatusUpdate(BaseModel):
    status:              ClaimStatus
    handoff_instructions: Optional[str] = None

    @field_validator("status", mode="before")
    @classmethod
    def normalize_status(cls, value):
        if isinstance(value, str):
            return value.strip().upper()
        return value

    @field_validator("handoff_instructions", mode="before")
    @classmethod
    def normalize_optional_strings(cls, value):
        if value == "":
            return None
        return value

# Simplified versions for nested responses in ClaimOut
class ItemSimplified(BaseModel):
    item_id:        int
    title:          str
    type:           ItemType
    status:         ItemStatus
    is_in_custody:  Optional[bool] = None
    image_url:      Optional[str] = None

    model_config = {"from_attributes": True}

    @field_validator("status", mode="before")
    @classmethod
    def normalize_status(cls, value):
        if isinstance(value, str):
            return value.strip().upper()
        return value

    @field_validator("image_url", mode="before")
    @classmethod
    def normalize_optional_strings(cls, value):
        if value == "":
            return None
        return value

class UserSimplified(BaseModel):
    user_id:     int
    name:        str
    roll_number: str

    model_config = {"from_attributes": True}

class ClaimOut(BaseModel):
    claim_id:            int
    item_id:             int
    claimer_id:          int
    proof_description:   Optional[str] = None
    handoff_instructions: Optional[str] = None
    owner_contact:       Optional[str] = None
    status:              ClaimStatus
    created_at:          datetime
    item:                Optional[ItemSimplified] = None
    claimer:             Optional[UserSimplified] = None

    model_config = {"from_attributes": True}

    @field_validator("status", mode="before")
    @classmethod
    def normalize_status(cls, value):
        if isinstance(value, str):
            return value.strip().upper()
        return value

    @field_validator("proof_description", "handoff_instructions", "owner_contact", mode="before")
    @classmethod
    def normalize_optional_strings(cls, value):
        if value == "":
            return None
        return value


# ── Activity Logs ─────────────────────────────────────────────────────────

class ActivityLogOut(BaseModel):
    log_id:       int
    item_id:      int
    action_taken: str
    timestamp:    datetime

    model_config = {"from_attributes": True}


# ── Matching Engine ───────────────────────────────────────────────────────

class MatchResult(BaseModel):
    item_id:       int
    title:         str
    description:   Optional[str]
    location:      Optional[str]
    image_url:     Optional[str]
    category_name: str
    found_by:      str
    posted_at:     datetime
