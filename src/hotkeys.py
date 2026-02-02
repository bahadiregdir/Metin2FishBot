"""
Hotkey Modülü - Klavye kısayolları ile bot kontrolü
"""
import threading
import platform

class HotkeyManager:
    def __init__(self):
        self.enabled = False
        self.listener = None
        self.callbacks = {
            "toggle": None,      # F9 - Başlat/Durdur
            "stop": None,        # F10 - Acil Durdur
            "screenshot": None,  # F11 - Ekran görüntüsü
            "pause": None        # F12 - 5dk Mola
        }
        self.hotkeys = {
            "f9": "toggle",
            "f10": "stop",
            "f11": "screenshot",
            "f12": "pause"
        }
        self.log_callback = None
    
    def set_callbacks(self, toggle=None, stop=None, screenshot=None, pause=None, log=None):
        """Callback fonksiyonlarını ayarla"""
        if toggle: self.callbacks["toggle"] = toggle
        if stop: self.callbacks["stop"] = stop
        if screenshot: self.callbacks["screenshot"] = screenshot
        if pause: self.callbacks["pause"] = pause
        if log: self.log_callback = log
    
    def log(self, message):
        if self.log_callback:
            self.log_callback(message)
        else:
            print(f"[Hotkey] {message}")
    
    def start(self):
        """Hotkey dinlemeyi başlat"""
        if self.enabled:
            return
        
        try:
            # pynput kütüphanesini kullan
            from pynput import keyboard
            
            def on_press(key):
                try:
                    # F tuşlarını kontrol et
                    if hasattr(key, 'name'):
                        key_name = key.name.lower()
                        
                        if key_name in self.hotkeys:
                            action = self.hotkeys[key_name]
                            callback = self.callbacks.get(action)
                            
                            if callback:
                                self.log(f"🎮 Hotkey: {key_name.upper()} -> {action}")
                                # Ana thread'de çalıştır
                                threading.Thread(target=callback, daemon=True).start()
                except:
                    pass
            
            self.listener = keyboard.Listener(on_press=on_press)
            self.listener.start()
            self.enabled = True
            self.log("🎮 Hotkey'ler aktif: F9=Başlat/Durdur, F10=Acil Dur, F11=SS, F12=Mola")
            
        except ImportError:
            self.log("⚠️ pynput yüklü değil. Hotkey devre dışı.")
            self.log("   Yüklemek için: pip install pynput")
        except Exception as e:
            self.log(f"Hotkey hatası: {e}")
    
    def stop(self):
        """Hotkey dinlemeyi durdur"""
        if self.listener:
            self.listener.stop()
            self.listener = None
        self.enabled = False
        self.log("🎮 Hotkey'ler devre dışı")
    
    def is_available(self):
        """pynput kullanılabilir mi kontrol et"""
        try:
            from pynput import keyboard
            return True
        except ImportError:
            return False
    
    def get_status(self):
        """Durum bilgisi"""
        if not self.is_available():
            return "pynput yüklü değil"
        return "Aktif" if self.enabled else "Devre Dışı"
