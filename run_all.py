# run_all.py

import asyncio
import time
from playwright.async_api import async_playwright

from config import INS_URL
from insera.auth import login_step1, login_step2
from services.db_service import get_all_incs
from automation.log_utils import enable_colored_logs
from automation.auto_resolve import (
    fetch_and_sync_parallel,
    BOOKMARK_CONFIG,
    run_bot3_all_worksheets_parallel,
    process_ticket_batch_bot1_parallel,
    run_bot2_cycle_parallel,
    goto_with_retry,
)
from automation.lock_utils import check_can_run_all, release_lock

SCRAPE_CYCLE_SECONDS = 40 * 60          # 10 menit kerja + sleep -> total 40 menit
TAKEOWNER_CYCLE_SECONDS = 90 * 60       # 1 jam 30 menit
ACTUALSOLUTION_CYCLE_SECONDS = 3 * 60 * 60   # 3 jam
IBOOSTER_CYCLE_SECONDS = 3 * 60 * 60         # 3 jam

TAKEOWNER_WORKSHEETS = ("Database", "Database2", "Database3")
BOT1_WORKSHEET = "Database3"
BOT2_WORKSHEET = "Database3"

SCRAPE_WORKERS = 2
BOT1_WORKERS = 3
TAKEOWNER_WORKERS = 3
IBOOSTER_WORKERS = 3


async def _new_logged_in_page(context):
    """Buka page baru dalam context yang sama -- otomatis ikut sesi login
    yang sudah ada (share cookie), tanpa perlu login ulang."""
    page = await context.new_page()
    await page.goto(INS_URL["home"], wait_until="load")
    await page.wait_for_load_state("networkidle")
    return page


async def _open_worker_pages(context, n_workers):
    """Buka n_workers page sekaligus, semua sudah login (share context)."""
    pages = []
    for _ in range(n_workers):
        pages.append(await _new_logged_in_page(context))
    return pages


async def run_scrape_pass(pages):
    """Satu putaran scrape penuh (Bookmark 1, 2, 3) -- Bookmark 3 pakai
    versi paralel karena datanya paling besar; Bookmark 1 & 2 tetap
    sekuensial (pakai page pertama saja) karena datanya relatif kecil."""
    from automation.auto_resolve import fetch_and_sync

    cfg1 = BOOKMARK_CONFIG["bookmark1"]
    cfg2 = BOOKMARK_CONFIG["bookmark2"]
    cfg3 = BOOKMARK_CONFIG["bookmark3"]

    print("=== Sync Bookmark 1 -> Database ===")
    await fetch_and_sync(pages[0], cfg1["url"], cfg1["page_prefix"], cfg1["table_id"], cfg1["worksheet"])

    print("\n=== Sync Bookmark 2 -> Database2 ===")
    await fetch_and_sync(pages[0], cfg2["url"], cfg2["page_prefix"], cfg2["table_id"], cfg2["worksheet"])

    print(f"\n=== Sync Bookmark 3 -> Database3 (Parallel, {len(pages)} worker) ===")
    await fetch_and_sync_parallel(pages, cfg3["url"], cfg3["page_prefix"], cfg3["table_id"], cfg3["worksheet"])


async def scrape_loop(pages):
    while True:
        cycle_start = time.monotonic()
        print("\n[Bot Scrape] === Mulai siklus baru ===")
        await run_scrape_pass(pages)

        elapsed = time.monotonic() - cycle_start
        remaining = SCRAPE_CYCLE_SECONDS - elapsed
        if remaining > 0:
            print(f"[Bot Scrape] Selesai dalam {elapsed/60:.1f} menit, sleep {remaining/60:.1f} menit.")
            await asyncio.sleep(remaining)
        else:
            print(f"[Bot Scrape] Siklus memakan {elapsed/60:.1f} menit (melebihi alokasi), lanjut tanpa sleep.")


async def takeowner_loop(context):
    pages = await _open_worker_pages(context, TAKEOWNER_WORKERS)
    while True:
        cycle_start = time.monotonic()
        print("\n[Bot Take Owner] === Mulai siklus baru ===")
        await run_bot3_all_worksheets_parallel(pages, TAKEOWNER_WORKSHEETS)

        elapsed = time.monotonic() - cycle_start
        remaining = TAKEOWNER_CYCLE_SECONDS - elapsed
        if remaining > 0:
            print(f"[Bot Take Owner] Selesai dalam {elapsed/60:.1f} menit, sleep {remaining/60:.1f} menit.")
            await asyncio.sleep(remaining)
        else:
            print(f"[Bot Take Owner] Siklus memakan {elapsed/60:.1f} menit (melebihi alokasi), lanjut tanpa sleep.")


async def actualsolution_loop(context):
    pages = await _open_worker_pages(context, BOT1_WORKERS)
    while True:
        cycle_start = time.monotonic()
        print("\n[Bot Actual Solution] === Mulai siklus baru ===")
        inc_numbers = await get_all_incs(BOT1_WORKSHEET)
        print(f"[Bot Actual Solution] {len(inc_numbers)} tiket di {BOT1_WORKSHEET}, {len(pages)} worker.")
        if inc_numbers:
            results = await process_ticket_batch_bot1_parallel(pages, inc_numbers, worksheet_name=BOT1_WORKSHEET)
            print("\n=== RINGKASAN Bot Actual Solution ===")
            for r in results:
                print(r)

        elapsed = time.monotonic() - cycle_start
        remaining = ACTUALSOLUTION_CYCLE_SECONDS - elapsed
        if remaining > 0:
            print(f"[Bot Actual Solution] Selesai dalam {elapsed/60:.1f} menit, sleep {remaining/60:.1f} menit.")
            await asyncio.sleep(remaining)
        else:
            print(f"[Bot Actual Solution] Siklus memakan {elapsed/60:.1f} menit (melebihi alokasi), lanjut tanpa sleep.")


async def ibooster_loop(context):
    pages = await _open_worker_pages(context, IBOOSTER_WORKERS)
    while True:
        cycle_start = time.monotonic()
        print("\n[Bot IBooster] === Mulai siklus baru ===")
        await run_bot2_cycle_parallel(pages, BOT2_WORKSHEET)

        elapsed = time.monotonic() - cycle_start
        remaining = IBOOSTER_CYCLE_SECONDS - elapsed
        if remaining > 0:
            print(f"[Bot IBooster] Selesai dalam {elapsed/60:.1f} menit, sleep {remaining/60:.1f} menit.")
            await asyncio.sleep(remaining)
        else:
            print(f"[Bot IBooster] Siklus memakan {elapsed/60:.1f} menit (melebihi alokasi), lanjut tanpa sleep.")


async def main():
    enable_colored_logs()
    
    if not check_can_run_all():
        return

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(viewport={"width": 1600, "height": 900})

            # Login SEKALI di page pertama.
            login_page = await context.new_page()
            await login_page.goto(INS_URL["home"], wait_until="load")
            if not await login_step1(login_page):
                print("[ERR] Gagal sampai step OTP.")
                return
            if not await login_step2(login_page):
                print("[ERR] Login gagal.")
                return
            print("[OK] Login berhasil.\n")
            await login_page.wait_for_timeout(3000)

            scrape_pages = [login_page]
            for _ in range(SCRAPE_WORKERS - 1):
                pg = await context.new_page()
                await goto_with_retry(pg, INS_URL["home"])
                await pg.wait_for_load_state("networkidle")
                scrape_pages.append(pg)

            print(f"=== [Awal] Scrape penuh sebelum bot lain mulai ({len(scrape_pages)} worker) ===")
            await run_scrape_pass(scrape_pages)
            print("\n=== [Awal] Scrape penuh selesai, mulai keempat loop bersamaan ===\n")

            await asyncio.gather(
                scrape_loop(scrape_pages),
                takeowner_loop(context),
                actualsolution_loop(context),
                ibooster_loop(context),
            )

            await browser.close()
    finally:
        release_lock("all")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[STOP] run_all.py dihentikan paksa (Ctrl+C).")
        release_lock("all")