# automation/lock_utils.py

import os
import time
import datetime

LOCK_DIR = "locks"
STALE_HOURS = 8

BOT_NAMES = {
    "all": "run_all",
    "scrape": "run_scrape",
    "takeowner": "run_takeowner",
    "actualsolution": "run_actualsolution",
    "ibooster": "run_ibooster",
    "log_sync": "run_log_sync",
}

STANDALONE_KEYS = ["scrape", "takeowner", "actualsolution", "ibooster"]


def _lock_path(key):
    os.makedirs(LOCK_DIR, exist_ok=True)
    return os.path.join(LOCK_DIR, f"{BOT_NAMES[key]}.lock")


def _read_lock_time(key):
    path = _lock_path(key)
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r") as f:
            return float(f.read().strip())
    except Exception:
        return None


def is_lock_active(key, stale_hours=STALE_HOURS):
    ts = _read_lock_time(key)
    if ts is None:
        return False, None
    age_hours = (time.time() - ts) / 3600
    if age_hours > stale_hours:
        print(f"[WARN] Lock '{BOT_NAMES[key]}' berumur {age_hours:.1f} jam (>{stale_hours} jam), dianggap basi & diabaikan.")
        return False, ts
    return True, ts


def acquire_lock(key):
    with open(_lock_path(key), "w") as f:
        f.write(str(time.time()))


def release_lock(key):
    path = _lock_path(key)
    try:
        if os.path.exists(path):
            os.remove(path)
    except Exception:
        pass


def _fmt_time(ts):
    return datetime.datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")


def check_can_run_standalone(key, label):
    """Dipanggil tiap bot standalone sebelum mulai. True = boleh jalan (lock sudah diambil)."""
    active, ts = is_lock_active("all")
    if active:
        print(f"[BLOCKED] Tidak bisa menjalankan {label} secara standalone.")
        print(f"Alasan: run_all.py sedang aktif (dimulai {_fmt_time(ts)}).")
        print("Hentikan run_all.py terlebih dahulu sebelum menjalankan bot ini secara terpisah.")
        return False

    active_self, ts_self = is_lock_active(key)
    if active_self:
        print(f"[BLOCKED] {label} sepertinya sudah berjalan (dimulai {_fmt_time(ts_self)}).")
        print(f"Kalau ini keliru (proses lama crash tanpa cleanup), hapus manual: {_lock_path(key)}")
        return False

    acquire_lock(key)
    return True


def check_can_run_all():
    """Dipanggil run_all.py sebelum mulai. True = boleh jalan (lock sudah diambil)."""
    blocking = []
    for key in STANDALONE_KEYS:
        active, ts = is_lock_active(key)
        if active:
            blocking.append((key, ts))

    if blocking:
        print("[BLOCKED] Tidak bisa menjalankan run_all.py.")
        print("Alasan: bot standalone berikut sedang aktif:")
        for key, ts in blocking:
            print(f"  - {BOT_NAMES[key]} ({_lock_path(key)}, dimulai {_fmt_time(ts)})")
        print("Hentikan bot-bot standalone tersebut terlebih dahulu sebelum menjalankan run_all.py.")
        return False

    active_self, ts_self = is_lock_active("all")
    if active_self:
        print(f"[BLOCKED] run_all.py sepertinya sudah berjalan (dimulai {_fmt_time(ts_self)}).")
        print(f"Kalau ini keliru (proses lama crash tanpa cleanup), hapus manual: {_lock_path('all')}")
        return False

    acquire_lock("all")
    return True