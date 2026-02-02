#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Metin2 FishBot - Live Color Picker
Mouse'un altındaki pikselin HSV kodlarını gösterir.
"""

import cv2
import numpy as np
import time
import sys

try:
    import pyautogui
except ImportError:
    print("ERROR: pyautogui bulunamadı!")
    print("Yüklemek için: pip install pyautogui")
    sys.exit(1)

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
        
        # RGB renk (PIL Image)
        r, g, b = screenshot.getpixel((0, 0))
        
        # OpenCV için BGR -> HSV dönüşümü
        # pyautogui RGB döner, OpenCV BGR bekler
        pixel_bgr = np.uint8([[[b, g, r]]])  # BGR formatı
        pixel_hsv = cv2.cvtColor(pixel_bgr, cv2.COLOR_BGR2HSV)
        h, s, v = pixel_hsv[0][0]
        
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
    sys.exit(0)
