@echo off
cd /d "%~dp0"
title Metin2 FishBot Kurulumu
color 0A
echo ===================================================
echo Metin2 FishBot - Otomatik Kurulum Sihirbazi
echo ===================================================
echo.

echo [1/4] Python kontrol ediliyor...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    color 0C
    echo [HATA] Python bulunamadi!
    echo Lutfen https://www.python.org/downloads/ adresinden Python 3.10+ indirin.
    echo Kurulum sirasinda "Add Python to PATH" secenegini isaretlemeyi UNUTMAYIN.
    pause
    exit
)
echo Python bulundu.
echo.

echo [2/4] Sanal ortam (venv) olusturuluyor...
if not exist "venv" (
    python -m venv venv
    echo Venv olusturuldu.
) else (
    echo Venv zaten mevcut.
)
echo.

echo [3/4] Gerekli kutuphaneler yukleniyor (Biraz sürebilir)...
call venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
if %errorlevel% neq 0 (
    color 0C
    echo [HATA] Kutuphaneler yuklenirken sorun olustu.
    pause
    exit
)
echo.

echo [4/4] Kurulum basariyla tamamlandi!
echo.
echo ===================================================
echo Artik 'RUN.bat' dosyasina cift tiklayarak botu acabilirsiniz.
echo ===================================================
pause
