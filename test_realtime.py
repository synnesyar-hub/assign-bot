# test_realtime.py

import asyncio
from supabase import acreate_client, AsyncClient
from config import SUPABASE_URL, SUPABASE_KEY

TABLES = ["wo_kendari", "wo_kolaka", "wo_baubau"]


def on_change(table, payload):
    new_row = payload.get("data", {}).get("record") or payload.get("new") or {}
    print(f"\n[EVENT] UPDATE di {table}")
    print(f"        incident     = {new_row.get('incident')}")
    print(f"        log_synced   = {new_row.get('log_synced')}")
    print(f"        log (preview)= {(new_row.get('log') or '')[:60]!r}")

    if new_row.get("log_synced") is False:
        print(f"        -> AKAN masuk queue (log_synced=false terdeteksi)")
    else:
        print(f"        -> diabaikan (log_synced bukan false, event UPDATE lain)")


async def load_backlog(supabase: AsyncClient):
    print("\n=== Cek backlog (baris log_synced=false yang SUDAH ADA) ===")
    total = 0
    for table in TABLES:
        res = await (
            supabase.table(table)
            .select("incident, log, log_synced")
            .eq("log_synced", False)
            .execute()
        )
        rows = res.data or []
        total += len(rows)
        print(f"[Backlog] {table}: {len(rows)} baris")
        for row in rows:
            print(f"    - {row['incident']}")
    print(f"Total backlog: {total} baris\n")


async def start_listeners(supabase: AsyncClient):
    print("=== Mulai listen Realtime UPDATE ===")
    for table in TABLES:
        channel = supabase.channel(f"test-log-sync-{table}")
        channel.on_postgres_changes(
            event="UPDATE",
            schema="public",
            table=table,
            callback=lambda payload, t=table: on_change(t, payload),
        )
        await channel.subscribe()
        print(f"[Realtime] Listening di {table}")
    print("\nSemua listener aktif. Silakan ubah kolom 'log' dari dashboard atau SQL Editor.")
    print("Tekan Ctrl+C untuk berhenti.\n")


async def main():
    supabase: AsyncClient = await acreate_client(SUPABASE_URL, SUPABASE_KEY)

    await load_backlog(supabase)
    await start_listeners(supabase)

    while True:
        await asyncio.sleep(3600)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[STOP] Test dihentikan.")