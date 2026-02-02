"""
Raporlama Modülü - Günlük ve oturum raporları
"""
import json
import os
import time
import threading
from datetime import datetime, timedelta

class ReportManager:
    def __init__(self, telegram_notifier=None, stats_manager=None):
        self.telegram = telegram_notifier
        self.stats = stats_manager
        self.inventory = None
        self.daily_report_enabled = True
        self.session_report_enabled = True
        self.daily_thread = None
        self.running = False
        self.last_daily_report = None
        self.daily_report_hour = 0  # Gece yarısı (00:00)
    
    def set_telegram(self, telegram_notifier):
        """Telegram notifier'ı ayarla"""
        self.telegram = telegram_notifier
    
    def set_stats(self, stats_manager):
        """Stats manager'ı ayarla"""
        self.stats = stats_manager
        
    def set_inventory(self, inventory_manager):
        """Inventory manager'ı ayarla (Fiyat hesabı için)"""
        self.inventory = inventory_manager
    
    def start_daily_scheduler(self):
        """Günlük rapor zamanlayıcısını başlat"""
        if self.running:
            return
        
        self.running = True
        self.daily_thread = threading.Thread(target=self._daily_loop, daemon=True)
        self.daily_thread.start()
    
    def stop_daily_scheduler(self):
        """Günlük rapor zamanlayıcısını durdur"""
        self.running = False
    
    def _daily_loop(self):
        """Günlük rapor döngüsü"""
        while self.running:
            now = datetime.now()
            
            # Gece yarısı kontrolü
            if now.hour == self.daily_report_hour and now.minute == 0:
                # Bugün zaten gönderildi mi?
                today = now.strftime("%Y-%m-%d")
                if self.last_daily_report != today:
                    self.send_daily_report()
                    self.last_daily_report = today
            
            # Her dakika kontrol et
            time.sleep(60)
    
    def send_daily_report(self):
        """Günlük raporu Telegram'a gönder"""
        if not self.telegram or not self.telegram.enabled:
            return
        
        if not self.daily_report_enabled:
            return
        
        try:
            stats = self.stats.total_stats if self.stats else {}
            
            today = datetime.now().strftime("%d.%m.%Y")
            
            # Bugünkü istatistikler (yaklaşık)
            total_fish = stats.get("total_fish", 0)
            total_sessions = stats.get("total_sessions", 0)
            best_session = stats.get("best_session_fish", 0)
            
            report = f"""📋 *Günlük FishBot Raporu*
📅 {today}

📊 *Genel İstatistikler:*
├ Toplam Balık: {total_fish}
├ Toplam Oturum: {total_sessions}
└ En İyi Oturum: {best_session} balık

🎣 Yarın da bol kazançlar! 💰
"""
            self.telegram.send_message(report)
            
        except Exception as e:
            print(f"Günlük rapor hatası: {e}")
    
    def send_session_report(self, session_summary: dict):
        """Oturum bittiğinde rapor gönder"""
        if not self.telegram or not self.telegram.enabled:
            return
        
        if not self.session_report_enabled:
            return
        
        try:
            now = datetime.now().strftime("%H:%M")
            
            fish_count = session_summary.get("session_fish", 0)
            duration = session_summary.get("session_duration", "0dk")
            fish_per_hour = session_summary.get("fish_per_hour", 0)
            total_fish = session_summary.get("total_fish", 0)
            
            # Oturum detayları
            breakdown = session_summary.get("session_breakdown", {})
            top_3 = sorted(breakdown.items(), key=lambda x: x[1], reverse=True)[:3]
            
            breakdown_text = ""
            if top_3:
                breakdown_text = "\n\n🐟 *En Çok Tutulan:*\n"
                for fish, count in top_3:
                    breakdown_text += f"├ {fish}: {count} adet\n"
            
            # Gelir Hesabı
            revenue_text = ""
            if self.inventory and session_summary.get("session_breakdown"):
                try:
                    total_rev = 0.0
                    for k, v in session_summary["session_breakdown"].items():
                        price = self.inventory.get_price(k)
                        if price > 0:
                            total_rev += float(v) * float(price)
                    
                    if total_rev > 0:
                        if total_rev >= 100:
                            revenue_text = f"\n💰 *Kazanç:* {total_rev/100:.2f} Won ({total_rev:.1f}m)"
                        else:
                            revenue_text = f"\n💰 *Kazanç:* {total_rev:.1f} m"
                except: pass

            report = f"""🏁 *Oturum Sona Erdi*
⏰ Saat: {now}

📊 *Bu Oturum:*
├ Balık: {fish_count} adet
├ Süre: {duration}
└ Hız: {fish_per_hour} balık/saat{revenue_text}{breakdown_text}

📈 *Toplam:* {total_fish} balık

💤 Bot durduruldu. İyi dinlenmeler!
"""
            self.telegram.send_message(report)
            
        except Exception as e:
            print(f"Oturum rapor hatası: {e}")
    
    def send_quick_stats(self):
        """Anlık istatistik gönder"""
        if not self.telegram or not self.stats:
            return
        
        try:
            summary = self.stats.get_summary()
            msg = self.stats.get_telegram_summary()
            self.telegram.send_message(msg)
        except Exception as e:
            print(f"Hızlı rapor hatası: {e}")
    
    def get_config(self):
        """Ayarları döndür"""
        return {
            "daily_report_enabled": self.daily_report_enabled,
            "session_report_enabled": self.session_report_enabled,
            "daily_report_hour": self.daily_report_hour
        }
    
    def load_config(self, config: dict):
        """Ayarları yükle"""
        self.daily_report_enabled = config.get("daily_report_enabled", True)
        self.session_report_enabled = config.get("session_report_enabled", True)
        self.daily_report_hour = config.get("daily_report_hour", 0)
