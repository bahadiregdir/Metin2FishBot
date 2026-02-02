@echo off
title Metin2 FishBot
color 0E

if not exist "venv" (
    color 0C
    echo [HATA] Kurulum yapilmamis!
    echo Lutfen once 'INSTALL.bat' dosyasini calistirin.
    pause
    exit
)

echo Bot baslatiliyor... Lutfen bekleyin...
call venv\Scripts\activate
python src/gui.py

if %errorlevel% neq 0 (
    color 0C
    echo.
    echo [HATA] Bot bir hata ile kapandi veya durduruldu.
    pause
)
