@echo off
setlocal EnableExtensions

title BOT CONTROLLER

REM ======================================
REM KONFIGURASI
REM ======================================
set VENV_DIR=venv
set VENV_PY=%VENV_DIR%\Scripts\python.exe

echo ======================================
echo        APLIKASI SETUP & RUN
echo ======================================

REM ======================================
REM CEK PYTHON (PY LAUNCHER)
REM ======================================
py -3 --version >nul 2>&1
IF ERRORLEVEL 1 (
    echo ERROR: Python 3 tidak ditemukan.
    echo Install Python dari:
    echo https://www.python.org/ftp/python/3.14.2/python-3.14.2-amd64.exe
    pause
    exit /b
)

REM ======================================
REM BUAT VENV
REM ======================================
IF NOT EXIST "%VENV_PY%" (
    echo Membuat virtual environment...
    py -3 -m venv "%VENV_DIR%"
    IF ERRORLEVEL 1 (
        echo Gagal membuat virtualenv
        pause
        exit /b
    )
)

REM ======================================
REM CEK REQUIREMENTS
REM ======================================
IF NOT EXIST requirements.txt (
    echo requirements.txt tidak ditemukan!
    pause
    exit /b
)

REM ======================================
REM INSTALL DEPENDENCIES
REM ======================================
echo Menginstall dependencies...
"%VENV_PY%" -m pip install --upgrade pip
IF ERRORLEVEL 1 (
    echo Gagal upgrade pip
    pause
    exit /b
)

"%VENV_PY%" -m pip install -r requirements.txt
IF ERRORLEVEL 1 (
    echo ERROR install dependencies
    pause
    exit /b
)

echo Dependencies berhasil diinstall.
pause

REM ======================================
REM INSTALL PLAYWRIGHT BROWSER
REM ======================================
echo Installing Playwright browser (Chromium)...
"%VENV_PY%" -m playwright install chromium
IF ERRORLEVEL 1 (
    echo ERROR: Gagal install Playwright browser
    pause
    exit /b
)

REM ======================================
REM SETUP .ENV
REM ======================================
IF EXIST .env GOTO START_APP

echo ======================================
echo KONFIGURASI PERTAMA KALI
echo ======================================
echo Ambil API ID & HASH:
echo https://my.telegram.org/auth
pause

set /p TELE_API_ID=API ID:
set /p TELE_API_HASH=API HASH:
set /p TELE_PHONE_NO=PHONE (+62):
set /p WFM_USERNAME=WFM USERNAME:
set /p WFM_PASSWORD=WFM PASSWORD:
set /p ENV=Environment (dev/prod):

echo TELE_API_ID=%TELE_API_ID%>.env
echo TELE_API_HASH=%TELE_API_HASH%>>.env
echo TELE_PHONE_NO=%TELE_PHONE_NO%>>.env
echo WFM_USERNAME=%WFM_USERNAME%>>.env
echo WFM_PASSWORD=%WFM_PASSWORD%>>.env
echo ENV=%ENV%>>.env

echo Konfigurasi tersimpan.
pause

:START_APP
REM ======================================
REM CLEAN DB
REM ======================================
IF EXIST jobs.db del /f /q jobs.db

REM ======================================
REM START APP
REM ======================================
echo Menjalankan BOT & WORKER...

start "BOT_PROCESS" cmd /k "%VENV_PY%" main.py
timeout /t 5 >nul
start "WORKER_PROCESS" cmd /k "%VENV_PY%" worker.py

echo ======================================
echo BOT & WORKER SEDANG BERJALAN
echo Tutup window ini untuk STOP SEMUA
echo ======================================
pause

taskkill /FI "WINDOWTITLE eq BOT_PROCESS*" /T /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq WORKER_PROCESS*" /T /F >nul 2>&1

endlocal
exit /b