"""
Ayar Profilleri Modülü - Hazır ayar setleri
"""
import json
import os

# Hazır Profiller
PRESET_PROFILES = {
    "normal": {
        "name": "🎯 Normal Mod",
        "description": "Dengeli ayarlar, günlük kullanım için ideal",
        "settings": {
            "cast_delay_min": 2.0,
            "cast_delay_max": 3.0,
            "wait_timeout": 10.0,
            "gm_detect": True,
            "anti_afk": True,
            "scan_delay": 0.05
        }
    },
    "turbo": {
        "name": "⚡ Turbo Mod",
        "description": "Maksimum hız, daha fazla risk",
        "settings": {
            "cast_delay_min": 1.0,
            "cast_delay_max": 1.5,
            "wait_timeout": 8.0,
            "gm_detect": True,
            "anti_afk": False,
            "scan_delay": 0.03
        }
    },
    "stealth": {
        "name": "🥷 Gizli Mod",
        "description": "Yavaş ama güvenli, GM riski düşük",
        "settings": {
            "cast_delay_min": 3.5,
            "cast_delay_max": 5.0,
            "wait_timeout": 15.0,
            "gm_detect": True,
            "anti_afk": True,
            "scan_delay": 0.08
        }
    },
    "night": {
        "name": "🌙 Gece Modu",
        "description": "Gece botlaması için optimize edilmiş",
        "settings": {
            "cast_delay_min": 2.5,
            "cast_delay_max": 4.0,
            "wait_timeout": 12.0,
            "gm_detect": True,
            "anti_afk": True,
            "scan_delay": 0.06
        }
    },
    "afk": {
        "name": "💤 AFK Mod",
        "description": "Çok yavaş, minimum kaynak kullanımı",
        "settings": {
            "cast_delay_min": 5.0,
            "cast_delay_max": 8.0,
            "wait_timeout": 20.0,
            "gm_detect": True,
            "anti_afk": True,
            "scan_delay": 0.1
        }
    }
}

class ProfileManager:
    def __init__(self, config_path="config/profiles.json"):
        self.config_path = config_path
        self.custom_profiles = self.load_custom_profiles()
        self.current_profile = "normal"
    
    def load_custom_profiles(self):
        """Kullanıcı tanımlı profilleri yükle"""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                pass
        return {}
    
    def save_custom_profiles(self):
        """Kullanıcı profillerini kaydet"""
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(self.custom_profiles, f, indent=2, ensure_ascii=False)
    
    def get_all_profiles(self):
        """Tüm profilleri döndür (hazır + özel)"""
        all_profiles = dict(PRESET_PROFILES)
        all_profiles.update(self.custom_profiles)
        return all_profiles
    
    def get_profile(self, profile_id):
        """Belirli bir profili getir"""
        all_profiles = self.get_all_profiles()
        return all_profiles.get(profile_id)
    
    def get_profile_names(self):
        """Profil isimlerini listele (dropdown için)"""
        result = []
        for pid, profile in self.get_all_profiles().items():
            result.append((pid, profile["name"]))
        return result
    
    def apply_profile(self, profile_id, config_manager):
        """Profili config'e uygula"""
        profile = self.get_profile(profile_id)
        if not profile:
            return False
        
        settings = profile.get("settings", {})
        for key, value in settings.items():
            config_manager.set_bot_setting(key, value)
        
        self.current_profile = profile_id
        return True
    
    def create_custom_profile(self, name, description, settings):
        """Yeni özel profil oluştur"""
        profile_id = name.lower().replace(" ", "_")
        self.custom_profiles[profile_id] = {
            "name": f"⭐ {name}",
            "description": description,
            "settings": settings
        }
        self.save_custom_profiles()
        return profile_id
    
    def delete_custom_profile(self, profile_id):
        """Özel profil sil"""
        if profile_id in self.custom_profiles:
            del self.custom_profiles[profile_id]
            self.save_custom_profiles()
            return True
        return False
    
    def get_current_profile_name(self):
        """Aktif profil adını döndür"""
        profile = self.get_profile(self.current_profile)
        if profile:
            return profile["name"]
        return "Bilinmiyor"
