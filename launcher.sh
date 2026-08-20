#!/usr/bin/env bash

set -e

# ==============================
# PASTIKAN PATH PROJECT
# ==============================
cd "$(dirname "$0")"

clear
echo "======================================"
echo "       APLIKASI SETUP & RUN"
echo "======================================"

# ==============================
# KONFIGURASI
# ==============================
VENV_DIR="venv"
VENV_PY="$VENV_DIR/bin/python"

# ==============================
# CEK PYTHON
# ==============================
if ! command -v python3 >/dev/null 2>&1; then
  echo "ERROR: Python3 tidak ditemukan."
  echo "Install Python dengan:"
  echo "brew install python"
  read -p "Tekan ENTER untuk keluar..."
  exit 1
fi

python3 --version

# ==============================
# BUAT VENV
# ==============================
if [ ! -f "$VENV_PY" ]; then
  echo "Membuat virtual environment..."
  python3 -m venv "$VENV_DIR"
fi

# ==============================
# CEK REQUIREMENTS
# ==============================
if [ ! -f "requirements.txt" ]; then
  echo "ERROR: requirements.txt tidak ditemukan!"
  read -p "Tekan ENTER untuk keluar..."
  exit 1
fi

# ==============================
# INSTALL DEPENDENCIES
# ==============================
echo "Menginstall dependencies..."
"$VENV_PY" -m pip install --upgrade pip
"$VENV_PY" -m pip install -r requirements.txt

echo "Dependencies berhasil diinstall."

# ==============================
# INSTALL PLAYWRIGHT
# ==============================
echo "Installing Playwright browser (Chromium)..."
"$VENV_PY" -m playwright install chromium

# ==============================
# SETUP .ENV
# ==============================
if [ ! -f ".env" ]; then
  echo "======================================"
  echo "KONFIGURASI PERTAMA KALI"
  echo "======================================"
  echo "Ambil API ID & HASH:"
  echo "https://my.telegram.org/auth"
  echo

  read -p "API ID: " TELE_API_ID
  read -p "API HASH: " TELE_API_HASH
  read -p "PHONE (+62): " TELE_PHONE_NO
  read -p "WFM USERNAME: " WFM_USERNAME
  read -s -p "WFM PASSWORD: " WFM_PASSWORD
  echo
  read -p "Environment (dev/prod): " ENV

  cat <<EOF > .env
TELE_API_ID=$TELE_API_ID
TELE_API_HASH=$TELE_API_HASH
TELE_PHONE_NO=$TELE_PHONE_NO
WFM_USERNAME=$WFM_USERNAME
WFM_PASSWORD=$WFM_PASSWORD
ENV=$ENV
EOF

  echo "Konfigurasi tersimpan."
fi

# ==============================
# CLEAN DB
# ==============================
if [ -f "jobs.db" ]; then
  rm -f jobs.db
fi

# ==============================
# START APP
# ==============================
echo "Menjalankan BOT & WORKER..."

"$VENV_PY" main.py &
BOT_PID=$!

sleep 5

"$VENV_PY" worker.py &
WORKER_PID=$!

echo "======================================"
echo "BOT & WORKER SEDANG BERJALAN"
echo "Tekan CTRL+C untuk STOP SEMUA"
echo "======================================"

# ==============================
# HANDLE STOP
# ==============================
trap "echo ''; echo 'Stopping...'; kill $BOT_PID $WORKER_PID; exit" INT
wait
