CARA MENJALANKAN APLIKASI

1. Extract folder ini
2. Klik dua kali run.bat
3. Tunggu Python terinstall otomatis
4. Isi konfigurasi saat diminta
5. Bot & worker akan berjalan

CATATAN:
- Pastikan koneksi internet aktif
- Jangan hapus file .env setelah dibuat
- Tekan CTRL+C atau tutup window untuk stop
- Buat Venv terlebih dahulu jika belum ada :

    `python -m venv venv`

- Aktif Venv :

    Cmd:
    `venv\Scripts\activate.bat`

    Powershell:
    `venv\Scripts\Activate.ps1`

- Install semua dependency :

    `pip install -r requirements.txt`

- Install browser Playwright :

    `playwright install chromium`

# Assign-Bot — Automation OSS Incident (Insera)

Bot otomatisasi untuk memproses tiket incident di sistem Insera:
scrape data ke Google Sheets, ambil ownership tiket, isi Actual Solution,
dan cek status pengukuran (Ibooster).

## Struktur Program

Ada 5 program utama yang bisa dijalankan:

| File                       | Fungsi                                             | Worksheet         |
|----------------------------|----------------------------------------------------|-------------------|
| `run_all.py`               | Semua bot jalan sekaligus (all-in-one)             | Database, Database2, Database3 |
| `run_scrape.py`            | Scrape data tiket dari 3 bookmark ke Google Sheets | Database, Database2, Database3 |
| `run_takeowner.py`         | Ambil ownership tiket yang belum ada pemiliknya    | Database, Database2, Database3 |
| `run_actualsolution.py`    | Isi Actual Solution untuk tiket yang qualified     | Database3 |
| `run_ibooster.py`          | Cek Kategori Ukur / Status ONT / ONU RX saja       | Database3 |

Ditambah `test_fetch.py` — khusus untuk testing fitur baru & debugging,
bukan untuk pemakaian produksi sehari-hari.

## Cara Menjalankan

### Opsi 1 — Jalankan semuanya sekaligus (disarankan untuk pemakaian normal)


    `python run_all.py`


Ini akan:
1. Login sekali.
2. Scrape penuh (Database, Database2, Database3) sampai selesai.
3. Setelah itu, keempat bot (scrape, take owner, actual solution, ibooster)
   jalan **bersamaan terus-menerus**, masing-masing dengan siklus
   kerja + sleep sendiri:
   - Scrape : kerja ~10 menit, lalu sleep sampai total 40 menit per siklus.

   - Take Owner : kerja sampai semua tiket diproses, lalu sleep sampai
     total 1 jam 30 menit per siklus.

   - Actual Solution : kerja sampai semua tiket diproses, lalu sleep
     sampai total 3 jam per siklus.

   - Ibooster : kerja sampai semua tiket dicek, lalu sleep sampai
     total 3 jam per siklus.

Program ini tidak pernah berhenti sendiri — hentikan manual dengan
`Ctrl+C` kalau perlu.

### Opsi 2 — Jalankan satu bot saja (standalone)

Kalau cuma butuh satu fungsi tertentu jalan sendirian (misal cuma mau
scrape tanpa bot lain), jalankan salah satu:


    `python run_scrape.py`
    `python run_takeowner.py`
    `python run_actualsolution.py`
    `python run_ibooster.py`


Masing-masing juga jalan terus-menerus dengan siklus kerja+sleep sendiri
(sama seperti kalau dijalankan lewat `run_all.py`), sampai dihentikan
manual dengan `Ctrl+C`.

## Aturan Penting: Jangan Jalankan Bersamaan yang Bentrok

`run_all.py` dan file standalone TIDAK BOLEH jalan bersamaan.
Program sudah otomatis mendeteksi dan mencegah ini:

- Kalau `run_all.py` sedang aktif, mencoba menjalankan salah satu
  standalone (`run_scrape.py`, dst) akan langsung ditolak dengan
  pesan `[BLOCKED]`.

- Kalau salah satu standalone sedang aktif, mencoba menjalankan
  `run_all.py` juga akan ditolak, dengan pesan yang menyebutkan
  bot standalone mana yang sedang aktif.

- Menjalankan bot standalone yang sama dua kali (misal dua terminal
  sama-sama `python run_scrape.py`) juga akan ditolak di percobaan kedua.

Yang DIPERBOLEHKAN : menjalankan beberapa standalone yang berbeda
secara bersamaan, misalnya `run_scrape.py` dan `run_takeowner.py` di dua
terminal berbeda pada saat yang sama — ini aman dan didesain untuk bisa
saling berjalan independen.

Contoh pesan saat ditolak:

[BLOCKED] Tidak bisa menjalankan Bot Take Owner secara standalone.
Alasan: run_all.py sedang aktif (dimulai 2026-08-12 14:03:10).
Hentikan run_all.py terlebih dahulu sebelum menjalankan bot ini secara terpisah.

## Tentang Folder `locks/`

Folder `locks/` dibuat otomatis saat pertama kali program dijalankan —
berisi file penanda kecil (`.lock`) yang mencatat kapan sebuah bot mulai
berjalan. Folder ini:

- Tidak perlu dibuat manual.

- Tidak perlu di-commit ke git** (sudah masuk `.gitignore`).

- Bersifat sementara — file lock otomatis terhapus saat program berhenti
  dengan normal (termasuk lewat `Ctrl+C`).

### Kalau Program Ter-block Padahal Tidak Ada yang Berjalan

Ini bisa terjadi kalau program sebelumnya berhenti secara paksa (mati
listrik, `kill` proses, komputer crash) sehingga file lock sempat
tertinggal padahal prosesnya sudah tidak aktif. Program otomatis
mengabaikan lock yang berumur lebih dari 8 jam (dianggap basi), jadi
biasanya akan pulih sendiri.

Kalau butuh segera (tidak mau menunggu 8 jam), hapus manual file lock
yang bersangkutan di folder `locks/`, contoh:

locks/run_all.lock
locks/run_scrape.lock
locks/run_takeowner.lock
locks/run_actualsolution.lock
locks/run_ibooster.lock

Hapus hanya file lock milik bot yang memang sudah tidak berjalan —
jangan hapus kalau kamu tidak yakin proses sebelumnya benar-benar sudah
mati, karena bisa menyebabkan dua instance bot yang sama berjalan
bersamaan tanpa terdeteksi.

## Catatan Lain

- Semua bot berbagi worksheet Google Sheets yang sama secara real-time —
  perubahan dari satu bot akan langsung terlihat oleh bot lain di
  siklus berikutnya.

- Warning seperti `[WARN] INC ... tidak ditemukan, skip update` di log
  adalah hal wajar jika terjadi sesekali — biasanya karena data tiket
  berubah tepat di antara proses scrape dan proses bot lain (sistem
  Insera bersifat real-time). Ini bukan tanda error fatal.

- File `test_fetch.py` dipakai khusus untuk eksperimen/debugging fitur
  baru — jangan dipakai untuk pemakaian produksi sehari-hari.