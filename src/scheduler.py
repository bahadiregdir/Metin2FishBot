"""
Zamanlayıcı Modülü - Bot'u belirli saatlerde başlat/durdur
"""
import threading
import time
from datetime import datetime, timedelta

class BotScheduler:
    def __init__(self, bot_instance=None):
        self.bot = bot_instance
        self.enabled = False
        self.start_time = None  # "HH:MM" formatında
        self.stop_time = None   # "HH:MM" formatında
        self.running = False
        self.thread = None
        self.callback_start = None
        self.callback_stop = None
        self.callback_log = None
        
    def set_schedule(self, start_time: str, stop_time: str):
        """Zamanlama ayarla (HH:MM formatında)"""
        self.start_time = start_time
        self.stop_time = stop_time
        
    def set_callbacks(self, on_start=None, on_stop=None, on_log=None):
        """Callback fonksiyonlarını ayarla"""
        self.callback_start = on_start
        self.callback_stop = on_stop
        self.callback_log = on_log
        
    def log(self, message):
        if self.callback_log:
            self.callback_log(message)
        else:
            print(f"[Scheduler] {message}")
    
    def enable(self):
        """Zamanlayıcıyı etkinleştir"""
        if not self.start_time or not self.stop_time:
            self.log("⚠️ Başlama/Durma saati ayarlanmadı!")
            return False
            
        self.enabled = True
        self.running = True
        self.thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self.thread.start()
        self.log(f"⏰ Zamanlayıcı aktif: {self.start_time} - {self.stop_time}")
        return True
    
    def disable(self):
        """Zamanlayıcıyı devre dışı bırak"""
        self.enabled = False
        self.running = False
        self.log("⏰ Zamanlayıcı devre dışı")
    
    def _parse_time(self, time_str):
        """HH:MM stringini datetime objesine çevir (bugünün tarihi ile)"""
        try:
            hour, minute = map(int, time_str.split(":"))
            now = datetime.now()
            return now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        except:
            return None
    
    def _is_in_range(self, start_dt, stop_dt):
        """Şu an başlama ve durma saatleri arasında mı?"""
        now = datetime.now()
        
        # Gece geçişi kontrolü (örn: 23:00 - 06:00)
        if stop_dt < start_dt:
            # Gece yarısını geçiyor
            return now >= start_dt or now < stop_dt
        else:
            return start_dt <= now < stop_dt
    
    def _scheduler_loop(self):
        """Ana zamanlayıcı döngüsü"""
        bot_started_by_scheduler = False
        
        while self.running and self.enabled:
            try:
                start_dt = self._parse_time(self.start_time)
                stop_dt = self._parse_time(self.stop_time)
                
                if not start_dt or not stop_dt:
                    time.sleep(60)
                    continue
                
                in_range = self._is_in_range(start_dt, stop_dt)
                
                if in_range and not bot_started_by_scheduler:
                    # Başlama zamanı geldi
                    self.log(f"⏰ Zamanlı başlatma: {self.start_time}")
                    if self.callback_start:
                        self.callback_start()
                    bot_started_by_scheduler = True
                    
                elif not in_range and bot_started_by_scheduler:
                    # Durma zamanı geldi
                    self.log(f"⏰ Zamanlı durdurma: {self.stop_time}")
                    if self.callback_stop:
                        self.callback_stop()
                    bot_started_by_scheduler = False
                
                # Her 30 saniyede bir kontrol et
                time.sleep(30)
                
            except Exception as e:
                self.log(f"Zamanlayıcı hatası: {e}")
                time.sleep(60)
        
        self.log("Zamanlayıcı döngüsü sonlandı")
    
    def get_status(self):
        """Zamanlayıcı durumu"""
        if not self.enabled:
            return "Devre Dışı"
        
        now = datetime.now().strftime("%H:%M")
        return f"Aktif | Şu an: {now} | Aralık: {self.start_time}-{self.stop_time}"
    
    def get_next_action(self):
        """Bir sonraki eylem ne zaman?"""
        if not self.enabled or not self.start_time or not self.stop_time:
            return None
        
        now = datetime.now()
        start_dt = self._parse_time(self.start_time)
        stop_dt = self._parse_time(self.stop_time)
        
        in_range = self._is_in_range(start_dt, stop_dt)
        
        if in_range:
            # Şu an çalışıyor, durma zamanını göster
            if stop_dt < now:
                stop_dt += timedelta(days=1)
            diff = stop_dt - now
            return f"Duracak: {self.stop_time} ({int(diff.total_seconds() // 60)} dk sonra)"
        else:
            # Şu an durgun, başlama zamanını göster
            if start_dt < now:
                start_dt += timedelta(days=1)
            diff = start_dt - now
            return f"Başlayacak: {self.start_time} ({int(diff.total_seconds() // 60)} dk sonra)"
