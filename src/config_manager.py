
import json
import os

CONFIG_FILE = "config.json"

class ConfigManager:
    """Uygulama ayarlarını ve tercihlerini yönetir"""
    
    DEFAULT_CONFIG = {
        "fish_preferences": {},  
        "bot_settings": {
            "cast_time": 2.0,
            "reaction_time": 0.1,
            "scan_area": {"top": 300, "left": 600, "width": 600, "height": 400},
            "fish_color_hsv": [0, 0, 200, 180, 50, 255],
            
            # --- YENİ DETAYLI AYARLAR ---
            "cast_delay_min": 2.0, "cast_delay_max": 2.5,  # Olta atma sonrası bekleme aralığı
            "wait_timeout": 10.0,                          # Balık gelmezse kaç sn sonra tekrar atsın?
            "restart_if_crash": False,                     # Oyun kapanırsa yeniden başlat?
            "gm_detect": True,                             # GM veya fısıltı gelirse dur?
        },
        "stop_conditions": {
            "max_time_min": 0,    # 0 = Devre dışı (Dakika cinsinden)
            "max_fish": 0,        # 0 = Devre dışı
        },
        "telegram": {
            "token": "8462617355:AAGzU7mm17QQdJsQ1kFDhde3JVWfgurEd_0",
            "chat_id": "626737464",
            "notify_on_stop": True,   # Bot durduğunda mesaj at
            "notify_on_gm": True,     # GM/Fısıltı gelince mesaj at
            "notify_on_catch": False  # Nadir balık yakalarsa (şimdilik opsiyonel)
        }
    }

    def __init__(self):
        self.config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), CONFIG_FILE)
        self.config = self.load_config()

    def load_config(self):
        if not os.path.exists(self.config_path):
            print("Config file not found, creating default.")
            config = self.DEFAULT_CONFIG.copy()
            self.save_config_direct(config) # İlk oluşturmada hemen kaydet
            return config
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Eksik anahtarlar varsa varsayılanlarla tamamla
                for key, val in self.DEFAULT_CONFIG.items():
                    if key not in data:
                        data[key] = val
                
                # Telegram objesi eksikse (eski config) onu da ekle
                if "telegram" not in data:
                    data["telegram"] = self.DEFAULT_CONFIG["telegram"]
                    
                return data
        except Exception as e:
            print(f"Error loading config: {e}")
            return self.DEFAULT_CONFIG.copy()

    def save_config_direct(self, config_data):
         try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=4)
         except: pass

    def save_config(self):
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4)
            print("Config saved successfully.")
        except Exception as e:
            print(f"Error saving config: {e}")

    # --- Yardımcı Metodlar ---
    
    def get_fish_action(self, fish_key, default_action="keep"):
        return self.config["fish_preferences"].get(fish_key, default_action)

    def set_fish_action(self, fish_key, action):
        self.config["fish_preferences"][fish_key] = action
        self.save_config()

    def get_bot_setting(self, key):
        return self.config["bot_settings"].get(key)
    
    def set_bot_setting(self, key, value):
        self.config["bot_settings"][key] = value
        self.save_config()
