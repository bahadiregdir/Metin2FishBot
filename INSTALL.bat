@echo off
title FishBot Installer
color 0A

echo ========================================
echo    Metin2 FishBot - Kurulum
echo ========================================
echo.

:: Python kontrolu
python --version >nul 2>&1
if errorlevel 1 (
    echo [HATA] Python bulunamadi!
    echo.
    echo Python 3.10+ indirin: https://www.python.org/downloads/
    echo Kurulum sirasinda "Add Python to PATH" secenegini isaretleyin!
    echo.
    pause
    exit /b 1
)

echo [OK] Python bulundu
echo.

:: Virtual environment olustur
echo [1/4] Sanal ortam olusturuluyor...
if not exist "venv" (
    python -m venv venv
)
echo [OK] Sanal ortam hazir
echo.

:: Aktive et
echo [2/4] Sanal ortam aktive ediliyor...
call venv\Scripts\activate.bat

:: Paketleri yukle
echo [3/4] Gerekli paketler yukleniyor...
pip install -r requirements.txt -q

echo.
echo [4/4] Kurulum tamamlandi!
echo.
echo ========================================
echo    Calistirmak icin: run.bat
echo    EXE olusturmak icin: build_exe.bat
echo ========================================
echo.
pause
