# Renk Okuyucu Kullanım Kılavuzu

## Kurulum

Eğer `pyautogui` yüklü değilse:
```bash
pip install pyautogui
```

## Kullanım

1. **Aracı Çalıştır:**
   ```bash
   python tools/color_picker.py
   ```

2. **Oyunu Aç:**
   - Metin2'yi aç.
   - Minigame (Balıkçılık) penceresini görünür yap.

3. **Renkleri Oku:**
   - Mouse'u **KIRMIZI DAİRENİN** üzerine getir.
   - Terminal'deki `HSV: [H:..., S:..., V:...]` değerlerini bir yere not et.
   - Mouse'u **BALIĞIN** üzerine getir.
   - HSV değerlerini tekrar not et.

4. **Çıkış:**
   - Terminal'de `Ctrl+C` bas.

## Sonuçları Bildirme

Not ettiğin değerleri şu formatta yaz:

**Kırmızı Daire için:**
- H: 175
- S: 80
- V: 200

**Balık için:**
- H: 100
- S: 20
- V: 60

Bu sayıları bana gönder, ben botun ayarlarını ona göre yapacağım.

---

**Not:** Birkaç farklı noktadan (dairenin farklı kısımları, balığın farklı yerleri) ölçüm yaparsan daha iyi sonuç alırız.
