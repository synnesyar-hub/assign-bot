# backend/db.py

import os
import asyncpg
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

_pool = None

VALID_TABLES = {
    "database": "tickets_database",
    "database2": "tickets_database2",
    "database3": "tickets_database3",
}


async def get_pool():
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(DATABASE_URL, min_size=1, max_size=10)
    return _pool


async def close_pool():
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None


def resolve_table(worksheet: str) -> str:
    table = VALID_TABLES.get(worksheet.lower())
    if table is None:
        raise ValueError(f"Worksheet '{worksheet}' tidak dikenali. Pilihan: {list(VALID_TABLES.keys())}")
    return table