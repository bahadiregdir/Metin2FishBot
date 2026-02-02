@echo off
title Metin2 FishBot Guncelleme
color 0B
echo.
echo FishBot Guncelleniyor...
echo.

git pull
if %errorlevel% neq 0 (
    color 0C
    echo.
    echo [HATA] Guncelleme sirasinda bir sorun olustu.
    echo Internet baglantinizi kontrol edin veya manuel indirin.
    pause
    exit
)

echo.
echo [BASARILI] Bot guncellendi!
echo.
echo Simdi 'RUN.bat' ile calistirabilirsiniz.
pause
