@echo off
title FishBot Guncelleyici
color 0D

echo ========================================
echo    FishBot - Guncelleme Baslatiliyor
echo ========================================
echo.

:: Git kontrolu
git --version >nul 2>&1
if errorlevel 1 (
    echo [HATA] Git bulunamadi!
    echo Lutfen Git'i kurun: https://git-scm.com/download/win
    pause
    exit /b 1
)

:: Guncellemeleri cek
echo [1/2] GitHub'dan son surum cekiliyor...
git pull origin main

:: Sanal ortami kontrol et
if exist "venv\Scripts\activate.bat" (
    echo.
    echo [2/2] Kutuphaneler guncelleniyor...
    call venv\Scripts\activate.bat
    pip install -r requirements.txt -q
) else (
    echo.
    echo [UYARI] Sanal ortam bulunamadi, sadece kodlar guncellendi.
)

echo.
echo ========================================
echo    GUNCELLEME TAMAMLANDI!
echo ========================================
echo.
pause
