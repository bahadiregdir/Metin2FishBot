"""
Ses Uyarısı Modülü - Belirli balıklar tutulduğunda ses çalar
"""
import os
import threading
import platform

class SoundAlert:
    def __init__(self):
        self.enabled = True
        self.alert_fish = set()  # Ses çalınacak balık türleri
        self.sound_file = None   # Özel ses dosyası (None = sistem sesi)
        
    def set_alert_fish(self, fish_keys: list):
        """Ses uyarısı verilecek balıkları ayarla"""
        self.alert_fish = set(fish_keys)
    
    def add_alert_fish(self, fish_key: str):
        """Listeye balık ekle"""
        self.alert_fish.add(fish_key)
    
    def remove_alert_fish(self, fish_key: str):
        """Listeden balık çıkar"""
        self.alert_fish.discard(fish_key)
    
    def should_alert(self, fish_key: str) -> bool:
        """Bu balık için ses çalınmalı mı?"""
        return fish_key in self.alert_fish
    
    def play_alert(self, fish_key: str = None):
        """Ses çal (arka planda)"""
        if not self.enabled:
            return
            
        # Eğer fish_key verilmişse ve listede değilse çalma
        if fish_key and fish_key not in self.alert_fish:
            return
        
        # Arka planda ses çal
        thread = threading.Thread(target=self._play_sound, daemon=True)
        thread.start()
    
    def _play_sound(self):
        """Platforma göre ses çal"""
        try:
            system = platform.system()
            
            if self.sound_file and os.path.exists(self.sound_file):
                # Özel ses dosyası
                if system == "Windows":
                    import winsound
                    winsound.PlaySound(self.sound_file, winsound.SND_FILENAME)
                elif system == "Darwin":  # macOS
                    os.system(f"afplay '{self.sound_file}'")
                else:  # Linux
                    os.system(f"aplay '{self.sound_file}' 2>/dev/null || paplay '{self.sound_file}' 2>/dev/null")
            else:
                # Sistem sesi (beep)
                if system == "Windows":
                    import winsound
                    # Üç kısa bip
                    for _ in range(3):
                        winsound.Beep(1000, 200)
                elif system == "Darwin":  # macOS
                    os.system("afplay /System/Library/Sounds/Glass.aiff")
                else:  # Linux
                    os.system("echo -e '\\a'")  # Terminal beep
                    
        except Exception as e:
            print(f"Ses çalma hatası: {e}")
    
    def play_gm_alert(self):
        """GM algılandığında özel uyarı"""
        if not self.enabled:
            return
            
        thread = threading.Thread(target=self._play_gm_sound, daemon=True)
        thread.start()
    
    def _play_gm_sound(self):
        """GM için acil ses (daha uzun/yoğun)"""
        try:
            system = platform.system()
            
            if system == "Windows":
                import winsound
                # Uzun uyarı sesi
                for _ in range(5):
                    winsound.Beep(2000, 300)
                    winsound.Beep(1500, 300)
            elif system == "Darwin":
                # macOS - 3 kez çal
                for _ in range(3):
                    os.system("afplay /System/Library/Sounds/Sosumi.aiff")
            else:
                for _ in range(5):
                    os.system("echo -e '\\a'")
                    
        except Exception as e:
            print(f"GM ses hatası: {e}")
    
    def test_sound(self):
        """Test için ses çal"""
        self._play_sound()
        
    def get_config(self):
        """Ayarları döndür"""
        return {
            "enabled": self.enabled,
            "alert_fish": list(self.alert_fish),
            "sound_file": self.sound_file
        }
    
    def load_config(self, config: dict):
        """Ayarları yükle"""
        self.enabled = config.get("enabled", True)
        self.alert_fish = set(config.get("alert_fish", []))
        self.sound_file = config.get("sound_file", None)
