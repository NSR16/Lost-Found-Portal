"""
database.py
-----------
SQLAlchemy engine, session factory, and Base declaration.
All models import Base from here so they share the same metadata.
"""

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

load_dotenv()

# ── Build the MySQL connection URL from environment variables ──────────────
DB_USER     = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_HOST     = os.getenv("DB_HOST", "localhost")
DB_PORT     = os.getenv("DB_PORT", "3306")
DB_NAME     = os.getenv("DB_NAME", "campuslink")

DATABASE_URL = (
    f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

engine = create_engine(
    DATABASE_URL,
    echo=False,          # set True to log every SQL statement (debug mode)
    pool_pre_ping=True,  # recycle stale connections automatically
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Shared declarative base for all ORM models."""
    pass


# ── Dependency injected into every route that needs a DB session ───────────
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
