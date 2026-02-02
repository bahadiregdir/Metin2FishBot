@echo off
title FishBot
color 0B

:: Sanal ortami aktive et ve calistir
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
    python src/gui.py
) else (
    echo [HATA] Kurulum yapilmamis!
    echo Lutfen once INSTALL.bat dosyasini calistirin.
    pause
)
