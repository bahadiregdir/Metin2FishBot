@echo off
cd /d "%~dp0"
title Metin2 FishBot
color 0E

if not exist "%~dp0venv" (
    color 0C
    echo [HATA] Kurulum yapilmamis!
    echo Lutfen once 'INSTALL.bat' dosyasini calistirin.
    pause
    exit
)

echo Bot baslatiliyor... Lutfen bekleyin...
echo Dizini: %~dp0
echo.

"%~dp0venv\Scripts\python.exe" "%~dp0src\gui.py"

if %errorlevel% neq 0 (
    color 0C
    echo.
    echo [HATA] Bot bir hata ile kapandi veya durduruldu.
    pause
)
