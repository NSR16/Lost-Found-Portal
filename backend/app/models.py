"""
models.py
---------
ORM models that mirror the 5 tables defined in schema.sql.
All foreign-key relationships are expressed via SQLAlchemy relationship().
"""

from datetime import datetime
from sqlalchemy import (
    Boolean, Column, Integer, String, Text, Enum, DateTime,
    ForeignKey, UniqueConstraint, func
)
from sqlalchemy.orm import relationship
from app.database import Base
import enum


# ── Python Enums (mirror MySQL ENUMs) ─────────────────────────────────────

class UserRole(str, enum.Enum):
    student = "student"
    admin   = "admin"

class ItemType(str, enum.Enum):
    LOST  = "LOST"
    FOUND = "FOUND"

class ItemStatus(str, enum.Enum):
    ACTIVE   = "ACTIVE"
    REMOVED  = "REMOVED"
    RESOLVED = "RESOLVED"
    LOST     = "LOST"   # ADD THIS
    FOUND    = "FOUND"  # ADD THIS

class ClaimStatus(str, enum.Enum):
    PENDING             = "PENDING"
    AWAITING_COLLECTION = "AWAITING_COLLECTION"
    APPROVED            = "APPROVED"
    REJECTED            = "REJECTED"


# ── Table 1: Users ────────────────────────────────────────────────────────

class User(Base):
    __tablename__ = "Users"

    user_id       = Column(Integer, primary_key=True, index=True)
    name          = Column(String(100), nullable=False)
    roll_number   = Column(String(20),  unique=True, nullable=False)
    email         = Column(String(150), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    dept          = Column(String(100), nullable=False)
    role          = Column(Enum(UserRole), default=UserRole.student)
    created_at    = Column(DateTime, default=func.now())

    # Relationships
    items         = relationship("Item",  back_populates="poster",  cascade="all, delete")
    claims        = relationship("Claim", back_populates="claimer", cascade="all, delete")
    activity_logs = relationship("ActivityLog", back_populates="actor")


# ── Table 2: Categories ───────────────────────────────────────────────────

class Category(Base):
    __tablename__ = "Categories"

    category_id   = Column(Integer, primary_key=True, index=True)
    category_name = Column(String(100), unique=True, nullable=False)
    description   = Column(String(255))

    # Relationships
    items         = relationship("Item", back_populates="category")


# ── Table 3: Items ────────────────────────────────────────────────────────

class Item(Base):
    __tablename__ = "Items"

    item_id     = Column(Integer, primary_key=True, index=True)
    title       = Column(String(150), nullable=False)
    description = Column(Text)
    type        = Column(Enum(ItemType), nullable=False)
    location    = Column(String(200))
    image_url   = Column(String(500))
    status        = Column(Enum(ItemStatus), default=ItemStatus.ACTIVE)
    is_in_custody = Column(Boolean, default=False)
    is_deleted    = Column(Boolean, default=False)
    user_id       = Column(Integer, ForeignKey("Users.user_id", ondelete="CASCADE"), nullable=False)
    category_id   = Column(Integer, ForeignKey("Categories.category_id", ondelete="RESTRICT"), nullable=False)
    posted_at     = Column(DateTime, default=func.now())
    updated_at    = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    poster        = relationship("User",     back_populates="items")
    category      = relationship("Category", back_populates="items")
    claims        = relationship("Claim",    back_populates="item", cascade="all, delete")
    activity_logs = relationship("ActivityLog", back_populates="item", cascade="all, delete")


# ── Table 4: Claims ───────────────────────────────────────────────────────

class Claim(Base):
    __tablename__ = "Claims"
    __table_args__ = (
        UniqueConstraint("item_id", "claimer_id", name="uq_claim_per_user"),
    )

    claim_id          = Column(Integer, primary_key=True, index=True)
    item_id           = Column(Integer, ForeignKey("Items.item_id", ondelete="CASCADE"), nullable=False)
    claimer_id        = Column(Integer, ForeignKey("Users.user_id", ondelete="CASCADE"), nullable=False)
    proof_description   = Column(Text)
    handoff_instructions = Column(Text, nullable=True)
    status              = Column(Enum(ClaimStatus), default=ClaimStatus.PENDING)
    created_at          = Column(DateTime, default=func.now())
    resolved_at         = Column(DateTime, nullable=True)

    # Relationships
    item    = relationship("Item", back_populates="claims")
    claimer = relationship("User", back_populates="claims")

    @property
    def owner_contact(self):
        if self.status in (ClaimStatus.AWAITING_COLLECTION, ClaimStatus.APPROVED):
            return self.item.poster.email if self.item and self.item.poster else None
        return None


# ── Table 5: Activity_Logs ────────────────────────────────────────────────

class ActivityLog(Base):
    __tablename__ = "Activity_Logs"

    log_id       = Column(Integer, primary_key=True, index=True)
    item_id      = Column(Integer, ForeignKey("Items.item_id", ondelete="CASCADE"), nullable=False)
    action_taken = Column(String(255), nullable=False)
    performed_by = Column(Integer, ForeignKey("Users.user_id", ondelete="SET NULL"), nullable=True)
    timestamp    = Column(DateTime, default=func.now())

    # Relationships
    item  = relationship("Item", back_populates="activity_logs")
    actor = relationship("User", back_populates="activity_logs")
