# worker.py

import asyncio
from telethon import TelegramClient
from playwright.async_api import async_playwright
from job_queue_pkg.job_queue import get_pending_jobs
from automation.assign import find_inc
from automation.auth import login
from utils.message import reply_done_message
from config import WFM_URL
from settings import settings

client = TelegramClient("worker", settings.TELE_API_ID, settings.TELE_API_HASH)

async def worker(page):
    await client.start(phone=settings.TELE_PHONE_NO)
    print("\n👷 Worker started...\n")

    try:
        while True:
            jobs = get_pending_jobs()
            if not jobs:
                await asyncio.sleep(2)
                continue
            
            jobs_by_msg = {}
            for job in jobs:
                jobs_by_msg.setdefault(job["msg_id"], []).append(job)
            
            for msg_id, jobs_list in jobs_by_msg.items():
                inc_numbers = [j["inc"] for j in jobs_list]
                labor_number = jobs_list[0]["labor"]
                chat_id = jobs_list[0]["chat_id"]
                print(f"\n[REQ] From: {msg_id}, {len(inc_numbers)} ticket.")

                try:
                    await find_inc(inc_numbers, labor_number, chat_id, msg_id, page)

                    await reply_done_message(client, chat_id, msg_id)
                    
                except Exception as e:
                    print(f"[ERR] From msg_id {msg_id}: {e}")
            
            await asyncio.sleep(3)
    except asyncio.CancelledError:
        print("[STOP] Worker task cancelled.")
        raise

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        await page.goto(WFM_URL["loker"], wait_until="load")

        if WFM_URL["login"] in page.url:
            login_ok = await login(page)
            if not login_ok:
                print("[ERR] Login failed, exit.")
                return

        await worker(page)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("[STOP] Worker stopped by user (Ctrl+C).\n")   