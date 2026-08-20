# backend/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.routers import tickets
from backend.db import close_pool
from backend.routers import tickets, stats

app = FastAPI(title="Assign-Bot Monitoring API")

# CORS -- sementara izinkan semua origin untuk memudahkan development.
# Nanti sebelum production, ganti allow_origins ke domain frontend
# (Vercel) yang spesifik supaya lebih aman.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(tickets.router)
app.include_router(tickets.router)
app.include_router(stats.router)

@app.get("/")
async def root():
    return {"status": "ok", "message": "Assign-Bot Monitoring API is running."}


@app.get("/health")
async def health():
    """Endpoint sederhana untuk cek server hidup -- TIDAK menyentuh
    database sama sekali, jadi tetap merespons meski database down."""
    return {"status": "healthy"}


@app.on_event("shutdown")
async def shutdown():
    await close_pool()