# services/db_service.py

import os
import asyncpg
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

_pool = None

WORKSHEET_TABLE_MAP = {
    "Database": "tickets_database",
    "Database2": "tickets_database2",
    "Database3": "tickets_database3",
}

COLUMN_MAP = {
    "INCIDENT": "incident",
    "TTR CUSTOMER": "ttr_customer",
    "SUMMARY": "summary",
    "REPORTED DATE": "reported_date",
    "OWNER GROUP": "owner_group",
    "OWNER": "owner",
    "CUSTOMER SEGMENT": "customer_segment",
    "SERVICE TYPE": "service_type",
    "WITEL": "witel",
    "WORKZONE": "workzone",
    "STATUS": "status",
    "STATUS DATE": "status_date",
    "TICKET ID GAMAS": "ticket_id_gamas",
    "REPORTED BY": "reported_by",
    "CONTACT PHONE": "contact_phone",
    "CONTACT NAME": "contact_name",
    "CONTACT EMAIL": "contact_email",
    "BOOKING DATE": "booking_date",
    "DESCRIPTION ASSIGMENT": "description_assignment",
    "REPORTED PRIORITY": "reported_priority",
    "SOURCE TICKET": "source_ticket",
    "SUBSIDIARY": "subsidiary",
    "EXTERNAL TICKET ID": "external_ticket_id",
    "CHANNEL": "channel",
    "CUSTOMER TYPE": "customer_type",
    "CLOSED BY": "closed_by",
    "CLOSED / REOPEN by": "closed_reopen_by",
    "CUSTOMER ID": "customer_id",
    "CUSTOMER NAME": "customer_name",
    "SERVICE ID": "service_id",
    "SERVICE NO": "service_no",
    "SLG": "slg",
    "TECHNOLOGY": "technology",
    "LAPUL": "lapul",
    "GAUL": "gaul",
    "ONU RX": "onu_rx",
    "PENDING REASON": "pending_reason",
    "DATEMODIFIED": "date_modified",
    "INCIDENT DOMAIN": "incident_domain",
    "REGION": "region",
    "SYMPTOM": "symptom",
    "HIERARCHY PATH": "hierarchy_path",
    "SOLUTION": "solution",
    "DESCRIPTION ACTUAL SOLUTION": "description_actual_solution",
    "KODE PRODUK": "kode_produk",
    "PERANGKAT": "perangkat",
    "TECHNICIAN": "technician",
    "DEVICE NAME": "device_name",
    "WORKLOG SUMMARY": "worklog_summary",
    "LAST UPDATE WORKLOG": "last_update_worklog",
    "CLASSIFICATION FLAG": "classification_flag",
    "REALM": "realm",
    "RELATED TO GAMAS": "related_to_gamas",
    "TSC RESULT": "tsc_result",
    "SCC RESULT": "scc_result",
    "TTR AGENT": "ttr_agent",
    "TTR MITRA": "ttr_mitra",
    "TTR NASIONAL": "ttr_nasional",
    "TTR PENDING": "ttr_pending",
    "TTR REGION": "ttr_region",
    "TTR WITEL": "ttr_witel",
    "TTR END TO END": "ttr_end_to_end",
    "NOTE": "note",
    "GUARANTE STATUS": "guarantee_status",
    "RESOLVE DATE": "resolve_date",
    "SN ONT": "sn_ont",
    "TIPE ONT": "tipe_ont",
    "MANUFACTURE ONT": "manufacture_ont",
    "IMPACTED SITE": "impacted_site",
    "CAUSE": "cause",
    "RESOLUTION": "resolution",
    "NOTES ESKALASI": "notes_eskalasi",
    "RK INFORMATION": "rk_information",
    "EXTERNAL TICKET TIER 3": "external_ticket_tier_3",
    "CUSTOMER CATEGORY": "customer_category",
    "CLASSIFICATION PATH": "classification_path",
    "TERITORY NEAR END": "teritory_near_end",
    "TERITORY FAR END": "teritory_far_end",
    "URGENCY": "urgency",
    "URGENCY DESCRIPTION": "urgency_description",
    "STATUS ONT": "status_ont",  # khusus tickets_database3
}


def _table_name(worksheet_name: str) -> str:
    table = WORKSHEET_TABLE_MAP.get(worksheet_name)
    if table is None:
        raise ValueError(f"Worksheet '{worksheet_name}' tidak dikenali. Pilihan: {list(WORKSHEET_TABLE_MAP.keys())}")
    return table


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


async def get_all_incs(worksheet_name: str) -> list[str]:
    table = _table_name(worksheet_name)
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(f"SELECT incident FROM {table} WHERE incident IS NOT NULL AND incident != ''")
        return [r["incident"] for r in rows]


async def update_ticket_fields(worksheet_name: str, inc_number: str, fields: dict) -> bool:
    """
    Update kolom tertentu untuk satu tiket. `fields` pakai nama kolom
    versi scrape (mis. "STATUS ONT", "ONU RX") -- otomatis dipetakan ke
    nama kolom database lewat COLUMN_MAP.
    """
    table = _table_name(worksheet_name)

    db_fields = {}
    for k, v in fields.items():
        col = COLUMN_MAP.get(k, k.lower().replace(" ", "_"))
        db_fields[col] = v

    if not db_fields:
        return False

    set_clauses = []
    values = []
    for i, (col, val) in enumerate(db_fields.items(), start=1):
        set_clauses.append(f"{col} = ${i}")
        values.append(val)
    set_clauses.append(f"updated_at = now()")

    inc_param_idx = len(values) + 1
    values.append(inc_number)

    query = f"UPDATE {table} SET {', '.join(set_clauses)} WHERE incident = ${inc_param_idx}"

    pool = await get_pool()
    async with pool.acquire() as conn:
        result = await conn.execute(query, *values)
        # result contoh: "UPDATE 1" atau "UPDATE 0"
        updated_count = int(result.split(" ")[-1])
        if updated_count == 0:
            print(f"[WARN] [{worksheet_name}] INC {inc_number} tidak ditemukan, skip update.")
            return False
        return True


async def upsert_tickets(tickets: list[dict], worksheet_name: str):
    """
    Insert tiket baru, atau update tiket lama HANYA untuk kolom yang ada
    di data scrape (kolom hasil bot seperti status_ont/note TIDAK
    tersentuh, sama seperti perilaku upsert_tickets versi gspread lama).
    """
    if not tickets:
        print(f"[INFO] [{worksheet_name}] Tidak ada tiket untuk diproses.")
        return

    table = _table_name(worksheet_name)
    scrape_headers = list(tickets[0].keys())
    db_columns = [COLUMN_MAP.get(h, h.lower().replace(" ", "_")) for h in scrape_headers]

    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.transaction():
            inserted = 0
            updated = 0
            for ticket in tickets:
                inc_number = ticket.get("INCIDENT", "")
                if not inc_number:
                    continue

                values = [ticket.get(h, "") for h in scrape_headers]

                col_list = ", ".join(db_columns)
                placeholders = ", ".join(f"${i+1}" for i in range(len(db_columns)))
                update_set = ", ".join(f"{col} = EXCLUDED.{col}" for col in db_columns if col != "incident")

                query = f"""
                    INSERT INTO {table} ({col_list})
                    VALUES ({placeholders})
                    ON CONFLICT (incident) DO UPDATE SET {update_set}, updated_at = now()
                """
                result = await conn.execute(query, *values)
                if "INSERT" in result:
                    inserted += 1

            print(f"[OK] [{worksheet_name}] Upsert selesai: {len(tickets)} tiket diproses.")


async def sync_tickets(tickets: list[dict], worksheet_name: str):
    """
    upsert_tickets, lalu hapus baris yang tidak lagi muncul di hasil
    scrape terbaru -- setara sync_tickets versi gspread lama.
    """
    if not tickets:
        print(f"[INFO] [{worksheet_name}] Tidak ada tiket hasil scrape, skip sync (tidak menghapus apa pun).")
        return

    table = _table_name(worksheet_name)
    await upsert_tickets(tickets, worksheet_name)

    current_incs = [t.get("INCIDENT", "") for t in tickets if t.get("INCIDENT")]

    pool = await get_pool()
    async with pool.acquire() as conn:
        result = await conn.execute(
            f"DELETE FROM {table} WHERE incident != ALL($1::text[])",
            current_incs
        )
        deleted_count = int(result.split(" ")[-1])
        if deleted_count > 0:
            print(f"[OK] [{worksheet_name}] {deleted_count} tiket dihapus karena sudah tidak relevan dengan filter.")
        else:
            print(f"[INFO] [{worksheet_name}] Tidak ada tiket yang perlu dihapus.")

    return True