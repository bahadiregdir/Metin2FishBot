#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Metin2 FishBot - Live Color Picker (Freeze Özellikli)
Mouse'un altındaki pikselin HSV kodlarını gösterir.
SPACE = Değeri dondur ve kaydet
ENTER = Devam et
"""

import colorsys
import time
import sys
import os

try:
    import pyautogui
except ImportError:
    print("ERROR: pyautogui bulunamadı!")
    print("Yüklemek için: pip install pyautogui")
    input("Devam etmek için Enter'a bas...")
    sys.exit(1)

try:
    from pynput import keyboard
    HAS_KEYBOARD = True
except ImportError:
    HAS_KEYBOARD = False
    print("NOT: 'pynput' yüklü değil. Manuel freeze için CTRL+C kullan.")
    print("Otomatik freeze için: pip install pynput")
    print()

def rgb_to_hsv_opencv_format(r, g, b):
    """RGB'den HSV'ye dönüştürür (OpenCV formatında)"""
    h, s, v = colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)
    h_cv = int(h * 180)
    s_cv = int(s * 255)
    v_cv = int(v * 255)
    return h_cv, s_cv, v_cv

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

print("=" * 70)
print("METIN2 FISHBOT - RENK OKUYUCU (HSV)")
print("=" * 70)
print()
print("KULLANIM:")
print("1. Mouse'u KIRMIZI DAİRENİN üzerine götür.")
print("2. SPACE tuşuna bas (Değer donacak).")
print("3. Kaydet ve ENTER'a bas.")
print("4. Mouse'u BALIĞIN üzerine götür.")
print("5. SPACE + ENTER.")
print("6. Tüm değerleri bana gönder.")
print()
if HAS_KEYBOARD:
    print("KONTROLLER:")
    print("  SPACE  = Değeri dondur")
    print("  ENTER  = Devam et")
    print("  ESC    = Çıkış")
else:
    print("KONTROLLER:")
    print("  CTRL+C = Programı durdur")
print()
print("=" * 70)

saved_values = []
freeze = False
current_h, current_s, current_v = 0, 0, 0

if HAS_KEYBOARD:
    def on_press(key):
        global freeze
        try:
            if key == keyboard.Key.space:
                freeze = True
            elif key == keyboard.Key.esc:
                return False  # Stop listener
        except:
            pass
    
    listener = keyboard.Listener(on_press=on_press)
    listener.start()

print("\nProgram başladı... (Mouse'u hareket ettir)")
print()

try:
    while True:
        if not freeze:
            x, y = pyautogui.position()
            screenshot = pyautogui.screenshot(region=(x, y, 1, 1))
            r, g, b = screenshot.getpixel((0, 0))
            current_h, current_s, current_v = rgb_to_hsv_opencv_format(r, g, b)
            
            output = f"\r🔍 TARAMA... | RGB:({r:3},{g:3},{b:3}) | HSV:[H:{current_h:3}, S:{current_s:3}, V:{current_v:3}] <-- BURADA SPACE BAS"
            sys.stdout.write(output)
            sys.stdout.flush()
            
            time.sleep(0.1)
        else:
            # Freeze modu - Değer sabitlendi
            clear_screen()
            print("=" * 70)
            print("✅ DEĞER SABİTLENDİ!")
            print("=" * 70)
            print()
            print(f"  H (Hue):        {current_h}")
            print(f"  S (Saturation): {current_s}")
            print(f"  V (Value):      {current_v}")
            print()
            print("=" * 70)
            
            # Kullanıcıdan isim al
            name = input("Bu hangi nesne? (örn: 'Kırmızı Daire' veya 'Balık'): ").strip()
            if name:
                saved_values.append({
                    'name': name,
                    'h': current_h,
                    's': current_s,
                    'v': current_v
                })
                print(f"✅ '{name}' kaydedildi!")
            
            print()
            devam = input("Başka renk ölçmek ister misin? (e/h): ").strip().lower()
            
            if devam != 'e':
                break
            
            freeze = False
            print("\nDevam ediliyor...")
            time.sleep(1)
        
except KeyboardInterrupt:
    pass

# Sonuçları göster
clear_screen()
print("=" * 70)
print("📊 ÖLÇÜM SONUÇLARI")
print("=" * 70)
print()

if saved_values:
    for i, val in enumerate(saved_values, 1):
        print(f"{i}. {val['name']}:")
        print(f"   H: {val['h']}")
        print(f"   S: {val['s']}")
        print(f"   V: {val['v']}")
        print()
else:
    print("Hiçbir değer kaydedilmedi.")
    print()

print("=" * 70)
print("BU DEĞERLERE BANA GÖNDER (Kopyala-yapıştır yapabilirsin)")
print("=" * 70)
input("\nEnter'a basarak kapat...")
