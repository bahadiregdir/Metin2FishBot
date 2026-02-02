
@echo off
title Metin2 FishBot Yukleyicisi
color 0A

echo ==========================================
echo    Metin2 Jigsaw FishBot - Kurulum
echo ==========================================
echo.
echo [1/3] Python kontrol ediliyor...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [HATA] Python bulunamadi! Lutfen Python 3.x yukleyin.
    echo (Yuklerken "Add Python to PATH" secenegini isaretlemeyi unutmayin!)
    pause
    exit
)

echo [2/3] Gerekli kutuphaneler yukleniyor...
pip install -r requirements.txt

echo.
echo [3/3] Bot baslatiliyor...
echo.
python main_app.py

pause
