# run_actualsolution.py

import asyncio
import time
from playwright.async_api import async_playwright

from config import INS_URL
from insera.auth import login_step1, login_step2
from services.db_service import get_all_incs
from automation.log_utils import enable_colored_logs
from automation.auto_resolve import process_ticket_batch_bot1_parallel, goto_with_retry
from automation.lock_utils import check_can_run_standalone, release_lock

BOT_KEY = "actualsolution"
BOT_LABEL = "Bot Actual Solution (Bot-1)"
WORKSHEET = "Database3"
CYCLE_SECONDS = 3 * 60 * 60  # 3 jam
BOT1_WORKERS = 5


async def one_full_pass(pages):
    inc_numbers = await get_all_incs(WORKSHEET)
    print(f"[{BOT_LABEL}] {len(inc_numbers)} tiket di {WORKSHEET}, {len(pages)} worker.")
    if not inc_numbers:
        return
    results = await process_ticket_batch_bot1_parallel(pages, inc_numbers, worksheet_name=WORKSHEET)
    print(f"\n=== RINGKASAN {BOT_LABEL} ===")
    for r in results:
        print(r)


async def main():
    enable_colored_logs()
    
    if not check_can_run_standalone(BOT_KEY, BOT_LABEL):
        return

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(viewport={"width": 1600, "height": 900})

            pages = []
            for _ in range(BOT1_WORKERS):
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