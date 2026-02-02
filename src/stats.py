"""
İstatistik Modülü - Balık tutma istatistiklerini takip eder
"""
import json
import os
import time
from datetime import datetime, timedelta
from collections import defaultdict

class FishStats:
    def __init__(self, config_path="config/stats.json"):
        self.config_path = config_path
        self.session_start = None
        self.session_fish = defaultdict(int)  # Bu oturumdaki balıklar
        self.total_stats = self.load_stats()
        
    def load_stats(self):
        """Kayıtlı istatistikleri yükle"""
        stats = {
            "total_fish": 0,
            "total_sessions": 0,
            "total_time_seconds": 0,
            "fish_by_type": {},
            "best_session_fish": 0,
            "last_session_date": None,
            "hourly_stats": {str(h): 0 for h in range(24)} # Saatlik döküm (0-23)
        }
        
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    stats.update(data)
                    
                    # Eski kayıtlarda hourly_stats yoksa ekle
                    if "hourly_stats" not in stats:
                        stats["hourly_stats"] = {str(h): 0 for h in range(24)}
                        
                    return stats
            except:
                pass
        
        return stats

    def record_fish(self, fish_type: str):
        """Tutulan balığı kaydet"""
        self.session_fish[fish_type] += 1
        self.total_stats["total_fish"] += 1
        
        if fish_type not in self.total_stats["fish_by_type"]:
            self.total_stats["fish_by_type"][fish_type] = 0
        self.total_stats["fish_by_type"][fish_type] += 1
        
        # Saatlik İstatistik
        current_hour = str(datetime.now().hour)
        if "hourly_stats" not in self.total_stats:
            self.total_stats["hourly_stats"] = {str(h): 0 for h in range(24)}
        
        if current_hour not in self.total_stats["hourly_stats"]:
             self.total_stats["hourly_stats"][current_hour] = 0
             
        self.total_stats["hourly_stats"][current_hour] += 1
        
        # Her 10 balıkta bir kaydet
        if self.total_stats["total_fish"] % 10 == 0:
            self.save_stats()
            
    def get_hourly_data(self):
        """Saatlik verileri döndür (En yoğundan aza doğru sıralı)"""
        if "hourly_stats" not in self.total_stats:
             return []
             
        data = self.total_stats["hourly_stats"]
        # (Saat, Adet) listesi
        result = [{"hour": int(k), "count": v} for k, v in data.items()]
        result.sort(key=lambda x: x["hour"]) # Saate göre sırala
        return result
    
    def save_stats(self):
        """İstatistikleri kaydet"""
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(self.total_stats, f, indent=2, ensure_ascii=False)
    
    def start_session(self):
        """Yeni oturum başlat"""
        self.session_start = time.time()
        self.session_fish = defaultdict(int)
        self.total_stats["total_sessions"] += 1
        self.total_stats["last_session_date"] = datetime.now().strftime("%Y-%m-%d %H:%M")
        self.save_stats()
    
    def end_session(self):
        """Oturumu bitir ve kaydet"""
        if self.session_start:
            duration = time.time() - self.session_start
            self.total_stats["total_time_seconds"] += duration
            
            session_total = sum(self.session_fish.values())
            if session_total > self.total_stats["best_session_fish"]:
                self.total_stats["best_session_fish"] = session_total
            
            self.save_stats()
            self.session_start = None
    

    
    def get_session_duration(self):
        """Bu oturumun süresi (saniye)"""
        if self.session_start:
            return time.time() - self.session_start
        return 0
    
    def get_session_fish_count(self):
        """Bu oturumdaki toplam balık"""
        return sum(self.session_fish.values())
    
    def get_fish_per_hour(self):
        """Saatlik balık oranı"""
        duration = self.get_session_duration()
        if duration > 0:
            return (self.get_session_fish_count() / duration) * 3600
        return 0
    
    def get_summary(self):
        """Özet istatistikler"""
        session_count = self.get_session_fish_count()
        session_duration = self.get_session_duration()
        fish_per_hour = self.get_fish_per_hour()
        
        # En çok tutulan balık
        top_fish = "Yok"
        if self.total_stats["fish_by_type"]:
            top_fish = max(self.total_stats["fish_by_type"], key=self.total_stats["fish_by_type"].get)
        
        return {
            "session_fish": session_count,
            "session_duration": self.format_duration(session_duration),
            "fish_per_hour": round(fish_per_hour, 1),
            "total_fish": self.total_stats["total_fish"],
            "total_sessions": self.total_stats["total_sessions"],
            "total_time": self.format_duration(self.total_stats["total_time_seconds"]),
            "best_session": self.total_stats["best_session_fish"],
            "top_fish": top_fish,
            "session_breakdown": dict(self.session_fish)
        }
    
    def format_duration(self, seconds):
        """Süreyi okunabilir formatta göster"""
        if seconds < 60:
            return f"{int(seconds)}sn"
        elif seconds < 3600:
            return f"{int(seconds // 60)}dk {int(seconds % 60)}sn"
        else:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            return f"{hours}sa {minutes}dk"
    
    def get_telegram_summary(self):
        """Telegram için formatlı özet"""
        s = self.get_summary()
        
        text = f"""📊 *FishBot İstatistikleri*

🎣 *Bu Oturum:*
├ Balık: {s['session_fish']} adet
├ Süre: {s['session_duration']}
└ Hız: {s['fish_per_hour']} balık/saat

📈 *Toplam:*
├ Balık: {s['total_fish']} adet
├ Oturum: {s['total_sessions']} kez
├ Süre: {s['total_time']}
└ Rekor: {s['best_session']} balık/oturum

🏆 En Çok: {s['top_fish']}
"""
        return text
