# run_scrape_gha.py
#
# Versi single-run khusus GitHub Actions Scheduled Workflow.
# HANYA scrape Bookmark 1 (-> Database) dan Bookmark 2 (-> Database2).
# Bookmark 3 (-> Database3) sengaja TIDAK disentuh di sini -- itu
# domain Bot-1/Bot-2/Bot-3 yang belum dijadwalkan otomatis.
#
# Tidak ada loop while True / sleep -- satu kali jalan, satu kali
# scrape, lalu keluar. Penjadwalan interval diserahkan penuh ke
# cron di workflow YAML (.github/workflows/scrape.yml).

import asyncio
import sys
from playwright.async_api import async_playwright

from config import INS_URL
from insera.auth import login_step1, login_step2
from automation.log_utils import enable_colored_logs
from automation.auto_resolve import fetch_and_sync, BOOKMARK_CONFIG, goto_with_retry


async def run_once(page):
    cfg1 = BOOKMARK_CONFIG["bookmark1"]
    cfg2 = BOOKMARK_CONFIG["bookmark2"]

    print("=== Sync Bookmark 1 -> Database ===")
    await fetch_and_sync(page, cfg1["url"], cfg1["page_prefix"], cfg1["table_id"], cfg1["worksheet"])

    print("\n=== Sync Bookmark 2 -> Database2 ===")
    await fetch_and_sync(page, cfg2["url"], cfg2["page_prefix"], cfg2["table_id"], cfg2["worksheet"])


async def main():
    enable_colored_logs()

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1600, "height": 900})
        page = await context.new_page()

        await goto_with_retry(page, INS_URL["home"])

        if not await login_step1(page):
            print("[ERR] Gagal sampai step OTP.")
            await browser.close()
            sys.exit(1)

        if not await login_step2(page):
            print("[ERR] Login gagal.")
            await browser.close()
            sys.exit(1)

        print("[OK] Login berhasil.\n")
        await page.wait_for_timeout(2000)

        try:
            await run_once(page)
        except Exception as e:
            print(f"[ERR] Scrape gagal: {e}")
            await browser.close()
            sys.exit(1)

        await browser.close()
        print("\n[OK] Satu putaran scrape selesai.")


if __name__ == "__main__":
    asyncio.run(main())