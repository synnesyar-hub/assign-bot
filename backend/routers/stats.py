# backend/routers/stats.py

from fastapi import APIRouter, HTTPException
from backend.db import get_pool, resolve_table

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("/{worksheet}")
async def get_stats(worksheet: str):
    """Hitung jumlah tiket per status -- buat kartu ringkasan di dashboard."""
    try:
        table = resolve_table(worksheet)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    try:
        pool = await get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                f"SELECT status, COUNT(*) as count FROM {table} GROUP BY status ORDER BY count DESC"
            )
            total = await conn.fetchval(f"SELECT COUNT(*) FROM {table}")
            return {
                "total": total,
                "by_status": [dict(r) for r in rows],
            }
    except (OSError, TimeoutError):
        raise HTTPException(status_code=503, detail="Database sedang tidak dapat diakses, coba lagi nanti.")