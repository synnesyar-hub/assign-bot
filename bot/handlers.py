# bot/handlers.py

from telethon import events
from job_queue_pkg.job_queue import add_jobs
from config import TELE_GROUP_ID, PATTERN_INC, PATTERN_LABOR

def reg_handlers(client):

    @client.on(events.NewMessage)
    async def handle_msg(event):
        if event.chat_id != TELE_GROUP_ID:
            return
        
        text = event.raw_text.strip()

        if "#moban" not in text.lower():
            return
        
        tokens = []
        for line in event.raw_text.splitlines():
            tokens.extend(line.strip().split())

        incs = [t for t in tokens if PATTERN_INC.fullmatch(t)]
        labor = next(
            (t for t in tokens if PATTERN_LABOR.fullmatch(t) 
            and not PATTERN_INC.fullmatch(t)
            and t.lower() != "#moban"),
            None
        )

        if not incs or not labor:
            print("[WARN] INC and LABOR not valid...")
            return

        add_jobs(
            incs,
            labor,
            event.sender_id,
            event.chat_id,
            event.id
        )

        await event.reply(f"/wait") 