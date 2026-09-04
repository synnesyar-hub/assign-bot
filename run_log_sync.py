# run_log_sync.py

import asyncio
import os
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone

from playwright.async_api import async_playwright
from supabase import acreate_client, AsyncClient

from config import INS_URL, SUPABASE_URL, SUPABASE_KEY
from insera.auth import login_step1, login_step2
from automation.auto_resolve import (
    resolve_inc_to_record_id,
    recover_to_find_incident_page,
    submit_worklog,
    TicketNotFoundError,
    goto_with_retry,
)
from automation.log_utils import enable_colored_logs
from automation.lock_utils import check_can_run_standalone, release_lock
from utils.session import save_session, load_session

BOT_KEY = "log_sync"
BOT_LABEL = "Bot Log Sync"
TABLES = ["wo_kendari", "wo_kolaka", "wo_baubau"]


@dataclass
class SyncJob:
    table: str
    incident: str
    log_html: str
    log_summary: str = ""
    photo_path: str | None = None


class SyncQueue:
    def __init__(self):
        self._queue: asyncio.Queue[SyncJob] = asyncio.Queue()
        self._seen_keys: set[str] = set()

    def push(self, job: SyncJob):
        key = f"{job.table}:{job.incident}"
        if key in self._seen_keys:
            return
        self._seen_keys.add(key)
        self._queue.put_nowait(job)
        print(f"[Queue] +{key} (total antrian: {self._queue.qsize()})")

    async def pop(self) -> SyncJob:
        job = await self._queue.get()
        self._seen_keys.discard(f"{job.table}:{job.incident}")
        return job

    def task_done(self):
        self._queue.task_done()


class LogSyncWorker:
    def __init__(self):
        self.supabase: AsyncClient = None  # dibuat di run() karena butuh await
        self.queue = SyncQueue()
        self.page = None  # diisi setelah login di run()

    async def load_unsynced_backlog(self):
        for table in TABLES:
            res = await (
                self.supabase.table(table)
                .select("incident, log, log_summary, log_photo_path")
                .eq("log_synced", False)
                .execute()
            )
            for row in res.data or []:
                self.queue.push(SyncJob(
                    table=table,
                    incident=row["incident"],
                    log_html=row["log"] or "",
                    log_summary=row.get("log_summary") or "",
                    photo_path=row.get("log_photo_path"),
                ))
            print(f"[Backlog] {table}: {len(res.data or [])} baris perlu sync")

    async def start_realtime_listeners(self):
        for table in TABLES:
            channel = self.supabase.channel(f"log-sync-{table}")
            channel.on_postgres_changes(
                event="UPDATE",
                schema="public",
                table=table,
                callback=lambda payload, t=table: self._on_change(t, payload),
            )
            await channel.subscribe()
            print(f"[Realtime] Listening UPDATE di {table}")

    def _on_change(self, table, payload):
        new_row = payload.get("data", {}).get("record") or payload.get("new") or {}
        if new_row.get("log_synced") is False:
            self.queue.push(
                SyncJob(
                    table=table,
                    incident=new_row["incident"],
                    log_html=new_row.get("log") or "",
                    log_summary=new_row.get("log_summary") or "",
                    photo_path=new_row.get("log_photo_path"),
                )
            )

    async def _mark_synced(self, table, incident):
        await self.supabase.table(table).update(
            {
                "log_synced": True,
                "log_synced_at": datetime.now(timezone.utc).isoformat(),
                "log_sync_error": None,
            }
        ).eq("incident", incident).execute()

    async def _mark_failed(self, table, incident, error):
        await self.supabase.table(table).update({"log_sync_error": str(error)[:500]}).eq("incident", incident).execute()

    async def process_job(self, job: SyncJob):
        print(f"\n=== [LogSync] Memproses {job.incident} ({job.table}) ===")
        try:
            record_id = await resolve_inc_to_record_id(self.page, job.incident)
        except TicketNotFoundError as e:
            print(f"[ERR] {e}")
            await self._mark_failed(job.table, job.incident, "Ticket tidak ditemukan di Insera")
            return
        except Exception as e:
            print(f"[ERR] Resolve gagal untuk {job.incident}: {e}")
            await self._mark_failed(job.table, job.incident, f"Resolve gagal: {e}")
            await recover_to_find_incident_page(self.page)
            return

        local_photo_path = None
        try:
            if job.photo_path:
                data = await self.supabase.storage.from_("worklog-temp").download(job.photo_path)
                ext = os.path.splitext(job.photo_path)[1] or ".jpg"
                tmp = tempfile.NamedTemporaryFile(suffix=ext, delete=False)
                tmp.write(data)
                tmp.close()
                local_photo_path = tmp.name

            # photo_filename dipertahankan dari nama asli di Storage
            # (job.photo_path, mis. "INC24943102-1234567890.jpg"), BUKAN
            # dari nama file sementara hasil download lokal (tmp.name) --
            # supaya nama yang muncul di Insera tetap transparan/sesuai
            # asal, bukan nama acak seperti "tmpjosshhpx.jpg".
            photo_filename = os.path.basename(job.photo_path) if job.photo_path else None

            await submit_worklog(
                self.page,
                job.log_html,
                log_type="AGENTNOTE",
                summary=job.log_summary,
                photo_path=local_photo_path,
                photo_filename=photo_filename,
            )
            await self._mark_synced(job.table, job.incident)
            print(f"[OK] {job.incident} -> tersinkron ke Insera.")

            if job.photo_path:
                await self.supabase.storage.from_("worklog-temp").remove([job.photo_path])

        except Exception as e:
            print(f"[ERR] Submit WorkLog gagal untuk {job.incident}: {e}")
            import traceback
            traceback.print_exc()
            await self._mark_failed(job.table, job.incident, str(e))
            await recover_to_find_incident_page(self.page)
            # foto TIDAK dihapus di Storage kalau gagal -- biar retry berikutnya
            # (job masuk backlog lagi karena log_synced masih false) masih bisa pakai foto yang sama
        finally:
            if local_photo_path and os.path.exists(local_photo_path):
                os.remove(local_photo_path)  # file lokal sementara selalu dibersihkan, sukses atau gagal

    async def consume_loop(self):
        while True:
            job = await self.queue.pop()
            try:
                await self.process_job(job)
            finally:
                self.queue.task_done()

    async def run(self):
        if not check_can_run_standalone(BOT_KEY, BOT_LABEL):
            return

        try:
            self.supabase = await acreate_client(SUPABASE_URL, SUPABASE_KEY)

            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await load_session(browser)
                self.page = await context.new_page()

                await goto_with_retry(self.page, INS_URL["home"])

                # Kalau session hasil load_session masih valid, halaman home
                # akan langsung ter-render (bukan redirect ke halaman login).
                needs_login = INS_URL["login"] in self.page.url
                if needs_login:
                    print("[AUTH] Session tidak valid/tidak ada, login dari awal...")
                    if not await login_step1(self.page):
                        print("[ERR] Gagal sampai step OTP.")
                        return
                    if not await login_step2(self.page):
                        print("[ERR] Login gagal.")
                        return
                    print("[OK] Login berhasil.\n")
                else:
                    print("[AUTH] Session valid, skip login.")
                    await save_session(context)  # perpanjang/refresh file session

                await self.page.wait_for_timeout(2000)
                await self.page.locator("#findIncidentGlobal").wait_for(state="visible", timeout=15000)

                await self.load_unsynced_backlog()
                await self.start_realtime_listeners()
                await self.consume_loop()

                await browser.close()
        finally:
            release_lock(BOT_KEY)


if __name__ == "__main__":
    enable_colored_logs()
    worker = LogSyncWorker()
    try:
        asyncio.run(worker.run())
    except KeyboardInterrupt:
        print(f"\n[STOP] {BOT_LABEL} dihentikan paksa (Ctrl+C).")
        release_lock(BOT_KEY)