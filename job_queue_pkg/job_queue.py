# queue/job_queue.py

import sqlite3
from datetime import datetime
from config import DB_PATH

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                inc TEXT,
                labor TEXT,
                labor_status TEXT,
                sender_id INTEGER,
                chat_id INTEGER,
                msg_id INTEGER,
                inc_status TEXT,
                wo_status TEXT,
                status TEXT,
                created_at TEXT
            )
        """)

def add_jobs(incs, labor, sender_id, chat_id, msg_id):
    with sqlite3.connect(DB_PATH) as conn:
        for inc in incs:
            conn.execute("""
                INSERT INTO jobs (inc, labor, labor_status, sender_id, chat_id, msg_id, inc_status, wo_status, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                inc, 
                labor,
                "FOUND",    # labor_status
                sender_id, 
                chat_id, 
                msg_id, 
                "PENDING",  # inc_status
                "OPEN",     # wo_status
                "PENDING",  # status
                datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                ))

def get_jobs_msg(chat_id, msg_id):
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute("SELECT * FROM jobs WHERE chat_id=? AND msg_id=?", (chat_id, msg_id)).fetchall()
        return [dict(r) for r in rows]

def update_job_status(inc, chat_id, msg_id, **statuses):
    if not statuses:
        return
    
    set_clause = ", ".join([f"{col}=?" for col in statuses.keys()])
    values = list(statuses.values()) + [inc, chat_id, msg_id]

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(f"""
            UPDATE jobs
            SET {set_clause}
            WHERE inc=? AND chat_id=? AND msg_id=?
        """, values)

def get_pending_jobs():
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute("SELECT * FROM jobs WHERE status='PENDING' AND labor_status!='NOT_FOUND' AND wo_status !='CANCELED'").fetchall()
        return [dict(r) for r in rows]
    
def get_pending_wos():
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute("SELECT * FROM jobs WHERE status='PENDING' AND labor_status!='NOT_FOUND' AND wo_status !='CANCELED'").fetchall()
        return [dict(r) for r in rows]
