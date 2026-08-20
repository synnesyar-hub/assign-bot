# helper.py

import asyncio
from playwright.async_api import async_playwright
from telethon import TelegramClient

from config import INS_URL, INS_TICKET_LIST_URL_1, INS_TICKET_LIST_URL_2
from insera.auth import login_step1, login_step2
from insera.ticket_list import fetch_ticket_list
from services.gsheet_service import append_tickets
from settings import settings

client = TelegramClient("helper", settings.TELE_API_ID, settings.TELE_API_HASH)

POLLING_INTERVAL_SECONDS = 300  # 5 menit

shared_page = None


async def ensure_logged_in(page):
    """
    Cek apakah masih login. Kalau tidak, login ulang otomatis pakai TOTP.
    """
    await page.goto(INS_URL["home"], wait_until="load")

    if "/login" in page.url:
        print("[INFO] Session habis, login ulang...")
        step1_ok = await login_step1(page)
        if not step1_ok:
            print("[ERR] Gagal login ulang (step 1).")
            return False

        step2_ok = await login_step2(page)
        if not step2_ok:
            print("[ERR] Gagal login ulang (step 2).")
            return False

        print("[OK] Login ulang berhasil.")

    return True


async def process_bookmark(page, url, worksheet_name, label):
    print(f"=== [{label}] Mengambil data ===")
    tickets = await fetch_ticket_list(page, url)
    print(f"[INFO] [{label}] {len(tickets)} tiket ditemukan.")
    append_tickets(tickets, worksheet_name=worksheet_name)


async def polling_loop(page):
    print(f"\n👷 Helper started, polling tiap {POLLING_INTERVAL_SECONDS} detik...\n")

    while True:
        try:
            logged_in = await ensure_logged_in(page)
            if not logged_in:
                print("[ERR] Tidak bisa login, coba lagi nanti.")
                await asyncio.sleep(POLLING_INTERVAL_SECONDS)
                continue

            await process_bookmark(page, INS_TICKET_LIST_URL_1, "Database", "Bookmark 1")
            await process_bookmark(page, INS_TICKET_LIST_URL_2, "Database2", "Bookmark 2")

        except Exception as e:
            print(f"[ERR] Terjadi kesalahan saat polling: {e}")

        print(f"[INFO] Menunggu {POLLING_INTERVAL_SECONDS} detik sebelum cek berikutnya...\n")
        await asyncio.sleep(POLLING_INTERVAL_SECONDS)


async def main():
    global shared_page

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        shared_page = await context.new_page()

        await client.start(bot_token=settings.TELE_BOT_TOKEN)
        print("[INFO] Telegram bot siap.")

        try:
            await polling_loop(shared_page)
        except asyncio.CancelledError:
            print("[STOP] Helper task cancelled.")
            raise


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("[STOP] Helper stopped by user (Ctrl+C).\n")