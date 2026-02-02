@echo off
title FishBot EXE Builder
color 0E

echo ========================================
echo    FishBot - EXE Olusturucu
echo ========================================
echo.

:: Sanal ortami aktive et
if not exist "venv\Scripts\activate.bat" (
    echo [HATA] Kurulum yapilmamis!
    echo Lutfen once INSTALL.bat dosyasini calistirin.
    pause
    exit /b 1
)

call venv\Scripts\activate.bat

:: PyInstaller kontrolu
pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo [1/3] PyInstaller yukleniyor...
    pip install pyinstaller -q
)
echo [OK] PyInstaller hazir
echo.

:: EXE olustur
echo [2/3] EXE olusturuluyor (bu 1-2 dakika surebilir)...
echo.

:: Icon varsa kullan
set ICON_OPT=
if exist "assets\icon.ico" (
    set ICON_OPT=--icon "assets\icon.ico"
)

pyinstaller --noconfirm --onefile --windowed ^
    --name "FishBot" ^
    %ICON_OPT% ^
    --add-data "assets;assets" ^
    --add-data "config;config" ^
    --hidden-import "pynput.keyboard._win32" ^
    --hidden-import "pynput.mouse._win32" ^
    --hidden-import "PIL._tkinter_finder" ^
    src/gui.py

echo.
echo [3/3] Temizlik yapiliyor...
rmdir /s /q build 2>nul
del /q *.spec 2>nul

echo.
echo ========================================
echo    EXE HAZIRLANDI!
echo    Konum: dist\FishBot.exe
echo ========================================
echo.

:: dist klasorune config ve assets kopyala
echo Dosyalar kopyalaniyor...
xcopy /E /I /Y assets dist\assets >nul
xcopy /E /I /Y config dist\config >nul

echo.
echo dist klasorundeki tum dosyalari istediginiz yere tasiyabilirsiniz.
echo.
pause
