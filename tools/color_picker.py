#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Metin2 FishBot - Live Color Picker (OpenCV'siz Versiyon)
Mouse'un altındaki pikselin HSV kodlarını gösterir.
"""

import colorsys
import time
import sys

try:
    import pyautogui
except ImportError:
    print("ERROR: pyautogui bulunamadı!")
    print("Yüklemek için: pip install pyautogui")
    input("Devam etmek için Enter'a bas...")
    sys.exit(1)

def rgb_to_hsv_opencv_format(r, g, b):
    """
    RGB'den HSV'ye dönüştürür (OpenCV formatında)
    OpenCV HSV aralıkları:
    - H: 0-180 (Hue)
    - S: 0-255 (Saturation)
    - V: 0-255 (Value)
    """
    # colorsys 0-1 arası değer kullanır
    h, s, v = colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)
    
    # OpenCV formatına çevir
    h_cv = int(h * 180)  # 0-180
    s_cv = int(s * 255)  # 0-255
    v_cv = int(v * 255)  # 0-255
    
    return h_cv, s_cv, v_cv

print("=" * 60)
print("METIN2 FISHBOT - RENK OKUYUCU (HSV)")
print("=" * 60)
print()
print("KULLANIM:")
print("1. Bu programı çalıştır.")
print("2. Oyunu aç ve Minigame'e git.")
print("3. Mouse'u KIRMIZI DAİRENİN üzerine getir.")
print("   -> Terminal'de H, S, V değerlerini not et.")
print("4. Mouse'u BALIĞIN üzerine getir.")
print("   -> Terminal'de H, S, V değerlerini not et.")
print("5. Çıkmak için Ctrl+C bas.")
print()
print("=" * 60)
print()
print("Başlatılıyor...")
time.sleep(2)

try:
    while True:
        # Mouse pozisyonu al
        x, y = pyautogui.position()
        
        # Ekran görüntüsü (sadece 1x1 piksel)
        screenshot = pyautogui.screenshot(region=(x, y, 1, 1))
        
        # RGB renk
        r, g, b = screenshot.getpixel((0, 0))
        
        # HSV'ye çevir (OpenCV formatında)
        h, s, v = rgb_to_hsv_opencv_format(r, g, b)
        
        # Terminale yazdır (üzerine yaz)
        output = f"\rMOUSE: ({x:4}, {y:4}) | RGB: ({r:3}, {g:3}, {b:3}) | HSV: [H:{h:3}, S:{s:3}, V:{v:3}] <-- BU KODLARI KAYDET"
        sys.stdout.write(output)
        sys.stdout.flush()
        
        time.sleep(0.05)  # 50ms bekle
        
except KeyboardInterrupt:
    print("\n")
    print("=" * 60)
    print("Program kapatıldı.")
    print("=" * 60)
    print()
    print("NOT ETTİĞİN DEĞERLERİ BENİMLE PAYLAŞ:")
    print()
    print("Kırmızı Daire için:")
    print("- H: ...")
    print("- S: ...")
    print("- V: ...")
    print()
    print("Balık için:")
    print("- H: ...")
    print("- S: ...")
    print("- V: ...")
    print()
    print("=" * 60)
    input("Enter'a basarak kapat...")
    sys.exit(0)
