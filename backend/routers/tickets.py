# backend/routers/tickets.py

from fastapi import APIRouter, HTTPException
from backend.db import get_pool, resolve_table

router = APIRouter(prefix="/tickets", tags=["tickets"])


@router.get("/{worksheet}")
async def get_tickets(
    worksheet: str,
    limit: int = 50,
    offset: int = 0,
    status: str | None = None,
    owner: str | None = None,
):
    try:
        table = resolve_table(worksheet)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    conditions = []
    params = []
    param_idx = 1

    if status:
        conditions.append(f"status = ${param_idx}")
        params.append(status)
        param_idx += 1
    if owner:
        conditions.append(f"owner = ${param_idx}")
        params.append(owner)
        param_idx += 1

    where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

    try:
        pool = await get_pool()
        async with pool.acquire() as conn:
            query = f"SELECT * FROM {table} {where_clause} ORDER BY updated_at DESC LIMIT ${param_idx} OFFSET ${param_idx + 1}"
            rows = await conn.fetch(query, *params, limit, offset)

            count_query = f"SELECT COUNT(*) FROM {table} {where_clause}"
            total = await conn.fetchval(count_query, *params)

            return {
                "total": total,
                "limit": limit,
                "offset": offset,
                "data": [dict(r) for r in rows],
            }
    except (OSError, TimeoutError):
        raise HTTPException(status_code=503, detail="Database sedang tidak dapat diakses, coba lagi nanti.")


@router.get("/{worksheet}/{incident}")
async def get_ticket_detail(worksheet: str, incident: str):
    """Ambil satu tiket spesifik berdasarkan nomor INCIDENT."""
    try:
        table = resolve_table(worksheet)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    try:
        pool = await get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(f"SELECT * FROM {table} WHERE incident = $1", incident)
            if row is None:
                raise HTTPException(status_code=404, detail=f"Tiket {incident} tidak ditemukan di {worksheet}.")
            return dict(row)
    except (OSError, TimeoutError):
        raise HTTPException(status_code=503, detail="Database sedang tidak dapat diakses, coba lagi nanti.")