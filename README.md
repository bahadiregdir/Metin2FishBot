# 🎣 Metin2 FishBot

Görüntü işleme tabanlı otomatik balık tutma botu.

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![Platform](https://img.shields.io/badge/Platform-Windows-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## ✨ Özellikler

- 🎣 **Otomatik Balık Tutma** - Olta atma, balık algılama, yakalama
- 📊 **Detaylı İstatistikler** - Oturum ve toplam istatistikler
- 📱 **Telegram Entegrasyonu** - Uzaktan kontrol ve bildirimler
- 🔔 **Ses Uyarıları** - Nadir balık veya GM algılama
- ⏰ **Zamanlayıcı** - Otomatik başlat/durdur
- 📷 **Canlı Önizleme** - Gerçek zamanlı ekran görüntüsü
- 🎮 **Multi-Account** - Birden fazla hesap desteği
- 💾 **Ayar Profilleri** - Normal, Turbo, Gizli, Gece, AFK modları
- 🎮 **Hotkey Desteği** - F9/F10/F11/F12 kısayolları
- 📋 **Otomatik Raporlama** - Günlük ve oturum sonu raporları

## 🚀 Kurulum

### Yöntem 1: Kolay Kurulum (Önerilen)

1. Projeyi indirin veya klonlayın
2. `INSTALL.bat` dosyasını çift tıklayın
3. Kurulum tamamlandıktan sonra `run.bat` ile başlatın

### Yöntem 2: Manuel Kurulum

```bash
# Sanal ortam oluştur
python -m venv venv

# Aktive et
venv\Scripts\activate

# Paketleri yükle
pip install -r requirements.txt

# Çalıştır
python src/gui.py
```

### Yöntem 3: EXE Olarak Çalıştır

1. `INSTALL.bat` ile kurulum yapın
2. `build_exe.bat` çalıştırın
3. `dist\FishBot.exe` dosyasını kullanın

## 📱 Telegram Kurulumu

1. [@BotFather](https://t.me/BotFather) ile yeni bot oluşturun
2. Bot token'ı alın
3. [@userinfobot](https://t.me/userinfobot) ile Chat ID öğrenin
4. Gelişmiş ayarlardan girin

| F11 | Ekran Görüntüsü |
| F12 | 5 Dakika Mola |

## 🛡️ İleri Düzey Özellikler (Crash & Revive)

Botun **Otomatik Canlanma** ve **Crash Algılama** özelliklerini kullanabilmek için `src/assets/system/` içine aşağıdaki ekran görüntülerini eklemelisiniz:

1. **restart_here.png** → Karakter öldüğünde çıkan "Burada Yeniden Başla" butonu.
2. **disconnect.png** → "Sunucu Bağlantısı Koptu" veya hata penceresi.
3. **login_check.png** → Login ekranından sabit bir parça.

> **Not:** Windows'ta ekran görüntüsü alıp (Windows+Shift+S) sadece ilgili butonu/yazıyı kırparak ekleyin. Bot otomatik tanıyacaktır.

## 📁 Proje Yapısı

```
Metin2FishBot/
├── src/
│   ├── gui.py           # Ana arayüz
│   ├── bot_core.py      # Bot motoru
│   ├── telegram_bot.py  # Telegram
│   ├── inventory.py     # Envanter
│   ├── stats.py         # İstatistikler
│   ├── scheduler.py     # Zamanlayıcı
│   ├── sound_alert.py   # Ses uyarıları
│   ├── multi_account.py # Çoklu hesap
│   ├── profiles.py      # Profiller
│   ├── hotkeys.py       # Kısayollar
│   └── reports.py       # Raporlama
├── assets/              # Görseller
├── config/              # Ayarlar
├── INSTALL.bat          # Kurulum
├── run.bat              # Çalıştır
└── build_exe.bat        # EXE oluştur
```

## ⚠️ Uyarı

Bu bot eğitim amaçlıdır. Kullanımdan doğacak sonuçlar kullanıcının sorumluluğundadır.

## 📝 Lisans

MIT License
