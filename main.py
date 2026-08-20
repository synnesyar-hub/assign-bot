# main.py

import asyncio
from playwright.async_api import async_playwright, expect # todo
from telethon import TelegramClient
from settings import settings

from job_queue_pkg.job_queue import init_db
init_db()

from bot.handlers import reg_handlers

client = TelegramClient("user", settings.TELE_API_ID, settings.TELE_API_HASH)

async def main():
    await client.start(phone=settings.TELE_PHONE_NO)
    reg_handlers(client=client)

    print(f"\n🤖 Bot is running...\n")
    try:
        await client.run_until_disconnected()
    except asyncio.CancelledError:
        print("[STOP] Bot task cancelled.")
        raise

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("[STOP] Bot stopped by user (Crtl+C)\n")