"""
main.py
-------
FastAPI application entry point.
Run with:  uvicorn app.main:app --reload
"""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.database import engine, Base
from app.routers import auth, items, claims, categories, logs

# ── Create all tables if they don't exist (dev convenience) ───────────────
# In production, prefer running schema.sql directly in MySQL.
Base.metadata.create_all(bind=engine)

# ── App factory ────────────────────────────────────────────────────────────
app = FastAPI(
    title       = "CampusLink – Lost & Found API",
    description = "Backend API for the campus lost-and-found portal.",
    version     = "1.0.0",
    docs_url    = "/docs",
    redoc_url   = "/redoc",
)

# ── CORS (allow React dev server with credentials) ───────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins     = ["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials = True,
    allow_methods     = ["*"],
    allow_headers     = ["*"],
)

# ── Serve uploaded images as static files ─────────────────────────────────
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount("/static", StaticFiles(directory=UPLOAD_DIR), name="static")
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

# ── Register routers ───────────────────────────────────────────────────────
app.include_router(auth.router)
app.include_router(items.router)
app.include_router(claims.router)
app.include_router(categories.router)
app.include_router(logs.router)


@app.get("/", tags=["Health"])
def root():
    return {"status": "ok", "message": "CampusLink API is running 🎓"}
