# run_scrape.py

import asyncio
import time
from playwright.async_api import async_playwright

from config import INS_URL
from insera.auth import login_step1, login_step2
from automation.log_utils import enable_colored_logs
from automation.auto_resolve import fetch_and_sync, fetch_and_sync_parallel,goto_with_retry, BOOKMARK_CONFIG
from automation.lock_utils import check_can_run_standalone, release_lock

BOT_KEY = "scrape"
BOT_LABEL = "Bot Scrape"
CYCLE_SECONDS = 40 * 60  # kerja ~10 menit + sleep sisa hingga total 40 menit
SCRAPE_WORKERS = 2


async def one_full_pass(pages):
    cfg1 = BOOKMARK_CONFIG["bookmark1"]
    cfg2 = BOOKMARK_CONFIG["bookmark2"]
    cfg3 = BOOKMARK_CONFIG["bookmark3"]

    print("=== Sync Bookmark 1 -> Database ===")
    await fetch_and_sync(pages[0], cfg1["url"], cfg1["page_prefix"], cfg1["table_id"], cfg1["worksheet"])

    print("\n=== Sync Bookmark 2 -> Database2 ===")
    await fetch_and_sync(pages[0], cfg2["url"], cfg2["page_prefix"], cfg2["table_id"], cfg2["worksheet"])

    print(f"\n=== Sync Bookmark 3 -> Database3 (Parallel, {len(pages)} worker) ===")
    await fetch_and_sync_parallel(pages, cfg3["url"], cfg3["page_prefix"], cfg3["table_id"], cfg3["worksheet"])


async def main():
    enable_colored_logs()
    
    if not check_can_run_standalone(BOT_KEY, BOT_LABEL):
        return

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(viewport={"width": 1600, "height": 900})

            pages = []
            for _ in range(SCRAPE_WORKERS):
                pg = await context.new_page()
                await goto_with_retry(pg, INS_URL["home"])
                pages.append(pg)

            if not await login_step1(pages[0]):
                print("[ERR] Gagal sampai step OTP.")
                return
            if not await login_step2(pages[0]):
                print("[ERR] Login gagal.")
                return
            print("[OK] Login berhasil.\n")
            await pages[0].wait_for_timeout(3000)

            for pg in pages[1:]:
                await goto_with_retry(pg, INS_URL["home"])
                await pg.wait_for_load_state("networkidle")
                try:
                    await pg.locator("#findIncidentGlobal").wait_for(state="visible", timeout=15000)
                except Exception as e:
                    print(f"[WARN] #findIncidentGlobal belum siap setelah goto ulang: {e}")

            while True:
                cycle_start = time.monotonic()
                print(f"\n[{BOT_LABEL}] === Mulai siklus baru ===")
                await one_full_pass(pages)

                elapsed = time.monotonic() - cycle_start
                remaining = CYCLE_SECONDS - elapsed
                if remaining > 0:
                    print(f"[{BOT_LABEL}] Selesai dalam {elapsed/60:.1f} menit, sleep {remaining/60:.1f} menit.")
                    await asyncio.sleep(remaining)
                else:
                    print(f"[{BOT_LABEL}] Siklus memakan {elapsed/60:.1f} menit (melebihi alokasi), lanjut tanpa sleep.")

            await browser.close()
    finally:
        release_lock(BOT_KEY)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n[STOP] {BOT_LABEL} dihentikan paksa (Ctrl+C).")
        release_lock(BOT_KEY)