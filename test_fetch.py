# test_fetch.py

import asyncio
from playwright.async_api import async_playwright

from config import INS_URL
from insera.auth import login_step1, login_step2
from services.db_service import get_all_incs
from insera.ticket_list import fetch_ticket_list_paginated
from automation.log_utils import enable_colored_logs
from automation.auto_resolve import (
    fetch_bookmark1,
    fetch_bookmark2,
    fetch_bookmark3,
    fetch_bookmark4, 
    fetch_bookmark5,
    fetch_and_sync_parallel,
    BOOKMARK_CONFIG,
    process_ticket_batch_bot1,
    process_ticket_batch_bot1_parallel,
    run_bot2_forever,
    run_bot3_all_worksheets,
    resolve_inc_to_record_id,
    check_measurement_only,
    recover_to_find_incident_page,
)

# Scrape (True/False, tinggal ganti sesuai kebutuhan)
RUN_SCRAPE_BOOKMARK1 = False    # -> Database
RUN_SCRAPE_BOOKMARK2 = False   # -> Database2
RUN_SCRAPE_BOOKMARK3 = False   # -> Database3 (sekuensial biasa)

RUN_SCRAPE_BOOKMARK4 = True    # -> Database4 (SQM)
RUN_SCRAPE_BOOKMARK5 = True    # -> Database5 (UNSPEC)

# Scrape paralel khusus Bookmark 3 -- kalau True, RUN_SCRAPE_BOOKMARK3 di
# atas diabaikan (pakai yang paralel ini saja).
RUN_SCRAPE_BOOKMARK3_PARALLEL = False
SCRAPE_PARALLEL_WORKERS = 2

# Debug: bandingkan isi tabel Database3 vs hasil scrape terbaru dari
# website -- untuk audit selisih jumlah tiket yang tidak masuk akal.
RUN_DEBUG_COMPARE_SHEET_VS_SCRAPE = False

RUN_BOT1 = False
RUN_BOT1_PARALLEL = False
BOT1_PARALLEL_WORKERS = 3   # jumlah tab/page yang dipakai bersamaan

# Sementara: batasi jumlah tiket untuk uji throughput dulu (bukan full batch).
# Set None untuk proses semua tiket seperti biasa.
BOT1_PARALLEL_SAMPLE_LIMIT = None

RUN_BOT2_FOREVER = False
RUN_BOT3 = False

RUN_DEBUG_SPECIFIC_TICKETS = False
DEBUG_TICKET_LIST = ["INC51686696", "INC51629211"]

# Debug: proses Bot-1 (Actual Solution) untuk RENTANG index tertentu saja
# dari daftar tiket di tabel -- dipakai untuk reproduce bug pada
# tiket spesifik tanpa perlu proses semua tiket dari awal.
RUN_DEBUG_BOT1_RANGE = False
DEBUG_BOT1_WORKSHEET = "Database3"
DEBUG_BOT1_START_INDEX = 405   # index awal (0-based, inklusif)
DEBUG_BOT1_END_INDEX = 410     # index akhir (0-based, eksklusif)

BOT1_WORKSHEET = "Database3"
BOT3_WORKSHEETS = ("Database", "Database2", "Database3")


async def debug_compare_sheet_vs_scrape(page, cfg, worksheet_name):
    """
    Bandingkan INC yang ada di tabel vs INC yang barusan di-scrape dari
    website -- untuk audit selisih jumlah yang tidak masuk akal.
    """
    tickets = await fetch_ticket_list_paginated(
        page, cfg["url"], page_prefix=cfg["page_prefix"], table_id=cfg["table_id"]
    )
    scraped_incs = set(t.get("INCIDENT", "") for t in tickets if t.get("INCIDENT"))
    sheet_incs = set(await get_all_incs(worksheet_name))

    only_in_sheet = sheet_incs - scraped_incs
    only_in_scrape = scraped_incs - sheet_incs

    print(f"\n[DEBUG] Total di tabel: {len(sheet_incs)}")
    print(f"[DEBUG] Total hasil scrape barusan: {len(scraped_incs)}")
    print(f"[DEBUG] Ada di tabel TAPI TIDAK ada di scrape (harusnya sudah kehapus): {len(only_in_sheet)}")
    if only_in_sheet:
        print(f"         Contoh: {list(only_in_sheet)[:10]}")
    print(f"[DEBUG] Ada di scrape TAPI TIDAK ada di tabel (harusnya baru ditambah): {len(only_in_scrape)}")
    if only_in_scrape:
        print(f"         Contoh: {list(only_in_scrape)[:10]}")

    return only_in_sheet, only_in_scrape


async def debug_check_specific_tickets(page, inc_numbers, worksheet_name):
    print(f"\n=== [DEBUG] Cek ulang {len(inc_numbers)} tiket spesifik ===")
    results = []
    for inc_number in inc_numbers:
        print(f"\n--- [DEBUG] Memproses {inc_number} ---")
        try:
            record_id = await resolve_inc_to_record_id(page, inc_number)
        except Exception as e:
            print(f"[ERR] Resolve gagal untuk {inc_number}: {e}")
            results.append({"ticket_id": None, "inc_number": inc_number, "final": "RESOLVE_FAILED"})
            await recover_to_find_incident_page(page)
            continue

        try:
            result = await check_measurement_only(page, record_id, worksheet_name)
            print(f"[DEBUG RESULT] {inc_number} -> {result}")
            results.append(result)
        except Exception as e:
            print(f"[ERR] Cek gagal untuk {inc_number}: {e}")
            import traceback
            traceback.print_exc()
            results.append({"ticket_id": record_id, "inc_number": inc_number, "final": "FLOW_ERROR"})
            await recover_to_find_incident_page(page)
            continue

    print("\n=== [DEBUG] RINGKASAN ===")
    for r in results:
        print(r)
    return results


async def debug_run_bot1_range(page, worksheet_name, start_index, end_index):
    all_incs = await get_all_incs(worksheet_name)
    subset = all_incs[start_index:end_index]

    print(f"\n=== [DEBUG Bot-1] Range index {start_index}-{end_index} "
          f"({len(subset)} tiket dari total {len(all_incs)}) ===")
    if not subset:
        print("[DEBUG] Rentang index ini kosong (di luar jangkauan daftar tiket).")
        return []

    results = await process_ticket_batch_bot1(page, subset, worksheet_name=worksheet_name)

    print("\n=== [DEBUG Bot-1] RINGKASAN ===")
    for r in results:
        print(r)
    return results


async def main():
    enable_colored_logs()

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(viewport={"width": 1600, "height": 900})
        page = await context.new_page()

        await page.goto(INS_URL["home"], wait_until="load")

        step1_ok = await login_step1(page)
        if not step1_ok:
            print("[ERR] Gagal sampai step OTP.")
            return

        step2_ok = await login_step2(page)
        if not step2_ok:
            print("[ERR] Login gagal.")
            return

        print("[OK] Login berhasil.\n")
        await page.wait_for_timeout(3000)

        if RUN_SCRAPE_BOOKMARK1:
            print("=== Sync Bookmark 1 -> Database ===")
            await fetch_bookmark1(page)

        if RUN_SCRAPE_BOOKMARK2:
            print("\n=== Sync Bookmark 2 -> Database2 ===")
            await fetch_bookmark2(page)

        if RUN_SCRAPE_BOOKMARK3_PARALLEL:
            cfg = BOOKMARK_CONFIG["bookmark3"]
            extra_scrape_pages = []
            for _ in range(SCRAPE_PARALLEL_WORKERS - 1):
                p_new = await context.new_page()
                extra_scrape_pages.append(p_new)
            scrape_pages = [page] + extra_scrape_pages

            print(f"\n=== Sync Bookmark 3 -> Database3 (Parallel, {SCRAPE_PARALLEL_WORKERS} worker) ===")
            await fetch_and_sync_parallel(
                scrape_pages, cfg["url"], cfg["page_prefix"], cfg["table_id"], cfg["worksheet"]
            )

            for p_extra in extra_scrape_pages:
                await p_extra.close()
        elif RUN_SCRAPE_BOOKMARK3:
            print("\n=== Sync Bookmark 3 -> Database3 ===")
            await fetch_bookmark3(page)

        if RUN_SCRAPE_BOOKMARK4:
            print("\n=== Sync Bookmark 4 -> Database4 (SQM) ===")
            await fetch_bookmark4(page)

        if RUN_SCRAPE_BOOKMARK5:
            print("\n=== Sync Bookmark 5 -> Database5 (UNSPEC) ===")
            await fetch_bookmark5(page)

        if RUN_DEBUG_COMPARE_SHEET_VS_SCRAPE:
            cfg = BOOKMARK_CONFIG["bookmark3"]
            await debug_compare_sheet_vs_scrape(page, cfg, worksheet_name="Database3")

        if RUN_DEBUG_SPECIFIC_TICKETS:
            await debug_check_specific_tickets(page, DEBUG_TICKET_LIST, worksheet_name=BOT1_WORKSHEET)

        if RUN_DEBUG_BOT1_RANGE:
            await debug_run_bot1_range(
                page, DEBUG_BOT1_WORKSHEET, DEBUG_BOT1_START_INDEX, DEBUG_BOT1_END_INDEX
            )

        if RUN_BOT1:
            inc_numbers = await get_all_incs(BOT1_WORKSHEET)
            print(f"\n[Bot-1] {len(inc_numbers)} tiket di {BOT1_WORKSHEET}.")
            if inc_numbers:
                results = await process_ticket_batch_bot1(page, inc_numbers, worksheet_name=BOT1_WORKSHEET)
                print("\n=== RINGKASAN Bot-1 ===")
                for r in results:
                    print(r)

        if RUN_BOT1_PARALLEL:
            inc_numbers = await get_all_incs(BOT1_WORKSHEET)
            if BOT1_PARALLEL_SAMPLE_LIMIT is not None:
                inc_numbers = inc_numbers[:BOT1_PARALLEL_SAMPLE_LIMIT]
                print(f"\n[Bot-1][Parallel] Mode sampel aktif -- dibatasi ke {len(inc_numbers)} tiket pertama.")

            print(f"\n[Bot-1][Parallel] {len(inc_numbers)} tiket di {BOT1_WORKSHEET}, "
                  f"{BOT1_PARALLEL_WORKERS} worker.")
            if inc_numbers:
                extra_pages = []
                for _ in range(BOT1_PARALLEL_WORKERS - 1):
                    p_new = await context.new_page()
                    await p_new.goto(INS_URL["home"], wait_until="load")
                    await p_new.wait_for_load_state("networkidle")
                    extra_pages.append(p_new)

                all_pages = [page] + extra_pages

                results = await process_ticket_batch_bot1_parallel(
                    all_pages, inc_numbers, worksheet_name=BOT1_WORKSHEET
                )
                print("\n=== RINGKASAN Bot-1 (Parallel) ===")
                for r in results:
                    print(r)

                for p_extra in extra_pages:
                    await p_extra.close()

        if RUN_BOT2_FOREVER:
            await run_bot2_forever(page, worksheet_name=BOT1_WORKSHEET, sleep_seconds=1800)

        if RUN_BOT3:
            print(f"\n[Bot-3] Jalan di worksheet: {BOT3_WORKSHEETS}")
            bot3_results = await run_bot3_all_worksheets(page, worksheet_names=BOT3_WORKSHEETS)
            print("\n=== RINGKASAN Bot-3 ===")
            for ws, results in bot3_results.items():
                print(f"\n--- {ws} ---")
                for r in results:
                    print(r)

        input("\nTekan ENTER untuk menutup browser...")
        await browser.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[STOP] Program dihentikan paksa (Ctrl+C).")