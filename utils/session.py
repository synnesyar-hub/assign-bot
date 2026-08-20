# utils/session.py

from config import SESSION_FILE
import json
import os

async def save_session(context):
    storage = await context.storage_state()
    with open(SESSION_FILE, "w", encoding="utf-8") as f:
        json.dump(storage, f)
    # log print

async def load_session(browser):
    if os.path.exists(SESSION_FILE):
        try:
            with open(SESSION_FILE, "r", encoding="utf-8") as f:
                strorage = json.load(f)
                context = await browser.new_context(strorage_state=strorage)
                # log print
                return context
        except Exception as e:
            # log print
            return await browser.new_context()
    else:
        # log print
        return await browser.new_context()
    