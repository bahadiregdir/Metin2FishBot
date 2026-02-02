
import time
import random
import math
import platform
import threading
import cv2
import numpy as np

# İşletim sistemi kontrolü
IS_WINDOWS = platform.system() == "Windows"

if IS_WINDOWS:
    import mss
    import pydirectinput
    import pygetwindow as gw
else:
    # Sahte (Mock) Kütüphaneler - Test/Mac Amaçlı
    class MockMSS:
        def __enter__(self): return self
        def __exit__(self, exc_type, exc_val, exc_tb): pass
        def grab(self, monitor):
            img = np.zeros((monitor['height'], monitor['width'], 4), dtype=np.uint8)
            # Rastgele bir balık çiz (test için)
            fish_x = random.randint(50, monitor['width']-50)
            fish_y = random.randint(50, monitor['height']-50)
            cv2.circle(img, (fish_x, fish_y), 10, (255, 255, 255, 255), -1) 
            return img
            
    mss = MockMSS # type: ignore
    
    class MockInput:
        def click(self): pass
        def moveTo(self, x, y): pass 
        def press(self, key): pass
        
    pydirectinput = MockInput()
    gw = None 


# ==========================================
# SABİT DEĞERLER VE AYARLAR (Magic Numbers Yok!)
# ==========================================
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from telegram_bot import TelegramNotifier

class BotSettings:
    # Oyun Kuralları (Sabit)
    FISHING_HIT_LIMIT = 3        # Bir turda max tıklama
    FISHING_ROUND_DURATION = 15  # Bir balık tutma turu max süre (sn)
    SCAN_DELAY = 0.04            # Görüntü tarama gecikmesi (25 FPS)
    
    # Bot Davranış (Güvenlik için Randomize Edilecek Bazlar)
    DROP_DRAG_DISTANCE = 400     # Eşyayı yere atarken sürükleme mesafesi (px)
    ANIMATION_WAIT_BASE = 2.0    # Olta atma animasyonu temel süre
    REACTION_DELAY_MIN = 0.4     # Tıklama sonrası bekleme min
    REACTION_DELAY_MAX = 0.8     # Tıklama sonrası bekleme max
    WORM_REFILL_THRESHOLD = 180  # Kaç olta atışında bir yem yenilensin (1 Paket = 200)
    
    # Varsayılanlar
    DEFAULT_MONITOR = {"top": 0, "left": 0, "width": 800, "height": 600}
    DEFAULT_WINDOW_TITLE = "Metin2"

class BotCore:
    def __init__(self, update_log_callback=None, api_key=None, inventory_manager=None):
        self.is_running = False
        self.log_callback = update_log_callback
        self.state = "IDLE" 
        
        # Tarama Alanı
        self.monitor = BotSettings.DEFAULT_MONITOR.copy()
        self.window_title = BotSettings.DEFAULT_WINDOW_TITLE
        
        # Balık Rengi (HSV) - SİMSİYAH MODU
        # Su dokusunu (koyu mavi) elemek için sadece ÇOK KOYU (Siyah) alanları al.
        self.fish_lower = np.array([0, 0, 0])      # Tam Siyah
        self.fish_upper = np.array([180, 255, 45]) # Value 45'in altı (Simsiyah)
        
        # Minigame Tetikleyicisi (Kırmızı Daire) için kullanılan değerler detect_red_trigger içinde tanımlı.
        
        self.stats = {"caught": 0, "missed": 0, "casts": 0}
        self.start_timestamp = 0
        self.next_inv_check = random.randint(4, 7)
        self.worm_counter = 0  # Yem Sayacı

        # Config Yükleme (Telegram Dahil)
        self.telegram = TelegramNotifier(None, None)
        
        # GUI Entegrasyonu (dışardan set edilir)
        self.fish_stats = None      # FishStats referansı
        self.sound_alert = None     # SoundAlert referansı
        self.inventory_manager = inventory_manager # Inventory Manager referansı (Yem için)
        self.gui_start_callback = None  # Telegram /start komutu için
        
        self.reload_config()

        # Balık Balonu Şablonunu Yükle
        try:
            assets_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")
            bubble_path = os.path.join(assets_dir, "bubble.png")
            if os.path.exists(bubble_path):
                self.bubble_template = cv2.imread(bubble_path, 0) # Grayscale
                if self.bubble_template is not None:
                     self.log("✅ Balık balonu şablonu yüklendi.")
                else:
                     self.log("⚠️ Balık balonu şablonu okunamadı.")
                     self.bubble_template = None
            else:
                self.log("⚠️ assets/bubble.png bulunamadı. Renk tespiti kullanılacak.")
                self.bubble_template = None
        except Exception as e:
            self.log(f"Şablon yükleme hatası: {e}")
            self.bubble_template = None
            
    def reload_config(self):
        """Ayarları dosyadan yeniler"""
        if not hasattr(self, 'inventory_manager') or self.inventory_manager is None:
            from inventory import InventoryManager
            self.inventory_manager = InventoryManager(telegram_callback=self.on_inventory_event)
            
        try:
            cfg = self.inventory_manager.config.config
            bs = cfg.get("bot_settings", {})
            sc = cfg.get("stop_conditions", {})
            tg = cfg.get("telegram", {})
            
            # Dinamik Ayarlar
            self.cast_min = bs.get("cast_delay_min", 2.0)
            self.cast_max = bs.get("cast_delay_max", 2.5)
            self.wait_timeout = bs.get("wait_timeout", 10.0)
            self.gm_detect = bs.get("gm_detect", True)
            self.bait_key = bs.get("bait_key", "F1")
            
            self.max_time = sc.get("max_time_min", 0) * 60
            self.max_fish = sc.get("max_fish", 0)
            
            # Telegram Güncelle
            token = tg.get("token", "")
            chat_id = tg.get("chat_id", "")
            self.telegram.update_credentials(token, chat_id)
            
            # Bildirim Ayarları
            self.tg_notify_stop = tg.get("notify_on_stop", True)
            self.tg_notify_gm = tg.get("notify_on_gm", True)
            self.tg_notify_catch = tg.get("notify_on_catch", False)
            
            if self.telegram.enabled:
                self.log("📱 Telegram Aktif")
                # Komutları Kaydet
                self.telegram.register_handler("/stop", self.tg_cmd_stop)
                self.telegram.register_handler("/status", self.tg_cmd_status)
                self.telegram.register_handler("/ss", self.tg_cmd_ss)
                self.telegram.register_handler("/help", self.tg_cmd_help)
                self.telegram.register_handler("/log", self.tg_cmd_log)
                self.telegram.register_handler("/ayar", self.tg_cmd_config)
                self.telegram.register_handler("/envanter", self.tg_cmd_inventory)
                # Yeni Komutlar
                self.telegram.register_handler("/stats", self.tg_cmd_stats)
                self.telegram.register_handler("/start", self.tg_cmd_start)
                self.telegram.register_handler("/pause", self.tg_cmd_pause)

            self.log(f"Ayarlar Yenilendi. Timeout: {self.wait_timeout}s | Yem: {self.bait_key}")
        except Exception as e:
            self.log(f"Ayarlar yüklenirken hata: {e}")

    # --- Telegram Komutları ---
    def tg_cmd_help(self, text=None):
        self.telegram.show_menu() # Butonları gönder
        msg = (
            "🤖 **FishBot Komut Merkezi**\n\n"
            "🔹 `/status` - Bot durumu\n"
            "🔹 `/stats` - Detaylı istatistikler\n"
            "🔹 `/ss` - Anlık ekran görüntüsü\n"
            "🔹 `/envanter` - Envanter fotoğrafı\n"
            "🔹 `/start` - Botu başlat\n"
            "🔹 `/stop` - Botu durdur\n"
            "🔹 `/pause [dk]` - Mola ver (örn: /pause 30)\n"
            "🔹 `/ayar` - Ayarları göster/değiştir\n"
            "🔹 `/log` - Son loglar\n"
        )
        self.telegram_msg(msg)

    def tg_cmd_log(self, text=None):
        logs = "\n".join(self.log_buffer[-15:])
        self.telegram_msg(f"📜 **Son Loglar:**\n{logs}")
    
    def tg_cmd_stats(self, text=None):
        """Detaylı istatistikleri gönderir"""
        try:
            from stats import FishStats
            stats = FishStats()
            msg = stats.get_telegram_summary()
            self.telegram_msg(msg)
        except Exception as e:
            self.telegram_msg(f"❌ İstatistik hatası: {e}")
    
    def tg_cmd_start(self, text=None):
        """Botu Telegram'dan başlatır"""
        if self.running:
            self.telegram_msg("⚠️ Bot zaten çalışıyor!")
        else:
            self.telegram_msg("▶️ Bot başlatılıyor...")
            # GUI callback ile başlat
            if hasattr(self, 'gui_start_callback') and self.gui_start_callback:
                self.gui_start_callback()
            else:
                self.telegram_msg("❌ GUI bağlantısı yok, manuel başlatın.")
    
    def tg_cmd_pause(self, text=None):
        """Botu belirli süre duraklatır"""
        import threading
        
        duration = 30  # Varsayılan 30 dakika
        if text:
            args = text.split()
            if len(args) >= 2:
                try:
                    duration = int(args[1])
                except:
                    pass
        
        if not self.running:
            self.telegram_msg("⚠️ Bot zaten durmuş!")
            return
        
        self.telegram_msg(f"⏸️ Bot {duration} dakika mola veriyor...")
        self.running = False
        self.log(f"Telegram'dan {duration}dk mola verildi")
        
        # Belirtilen süre sonra yeniden başlat
        def resume_after_pause():
            import time
            time.sleep(duration * 60)
            if not self.running:
                self.telegram_msg("▶️ Mola bitti, bot devam ediyor...")
                if hasattr(self, 'gui_start_callback') and self.gui_start_callback:
                    self.gui_start_callback()
        
        threading.Thread(target=resume_after_pause, daemon=True).start()


    def tg_cmd_config(self, message):
        """Ayarları değiştirir veya gösterir. Örn: /ayar timeout 15"""
        args = message.split()
        
        if len(args) < 3:
            # Sadece listele
            msg = (
                f"⚙️ **Mevcut Ayarlar:**\n"
                f"• Timeout: {self.wait_timeout}s\n"
                f"• Cast Delay: {self.cast_min}-{self.cast_max}s\n"
                f"• Yem Tuşu: {self.bait_key}\n"
                f"• Max Süre: {self.max_time/60}dk\n"
                f"• Max Balık: {self.max_fish}\n\n"
                f"📝 **Değiştirmek için:**\n"
                f"/ayar timeout 12\n"
                f"/ayar cast_min 2.0\n"
                f"/ayar cast_max 3.5\n"
                f"/ayar max_fish 100\n"
                f"/ayar yem F2"
            )
            self.telegram_msg(msg)
            return

        # Ayar değiştirme
        key = args[1].lower()
        val = args[2]
        
        try:
            cfg_mgr = self.inventory_manager.config
            
            if key == "timeout":
                cfg_mgr.set_bot_setting("wait_timeout", float(val))
            elif key == "cast_min":
                cfg_mgr.set_bot_setting("cast_delay_min", float(val))
            elif key == "cast_max":
                cfg_mgr.set_bot_setting("cast_delay_max", float(val))
            elif key == "yem":
                cfg_mgr.set_bot_setting("bait_key", str(val))
            elif key == "max_fish":
                sc = cfg_mgr.config.get("stop_conditions", {})
                sc["max_fish"] = int(val)
                cfg_mgr.config["stop_conditions"] = sc
                cfg_mgr.save_config()
            elif key == "max_time":
                sc = cfg_mgr.config.get("stop_conditions", {})
                sc["max_time_min"] = int(val)
                cfg_mgr.config["stop_conditions"] = sc
                cfg_mgr.save_config()
            else:
                self.telegram_msg("⚠️ Geçersiz parametre.")
                return

            self.reload_config()
            self.telegram_msg(f"✅ Ayar güncellendi: {key} -> {val}")
            
        except Exception as e:
            self.telegram_msg(f"⚠️ Hata: {e}")

    def tg_cmd_inventory(self, text=None):
        self.telegram_msg("🎒 Envanter taranıyor, lütfen bekleyin...")
        was_running = self.is_running
        
        # Bot çalışıyorsa duraklat
        if was_running:
            self.is_paused = True
            time.sleep(2) # Mevcut işlemin bitmesini bekle
            
        try:
            import mss
            # Envanteri Aç (I)
            pydirectinput.press('i')
            time.sleep(1)
            
            with mss.mss() as sct:
                # 4 Sayfayı Gez
                for i in range(1, 5):
                     # Sayfa butonunu bulup tıkla (InventoryManager'daki page_btn mantığı lazım ama burası BotCore)
                     # Basitçe: Sayfa 1'e tıkla -> Çek.
                     # Şimdilik sadece "I"ya basıp mevcut sayfanın görüntüsünü alalım.
                     # Çok sayfalı gezme için InventoryManager'ı remote çağırmak lazım.
                     
                     # 1. Envanter bölgesini bul (InventoryManager'dan)
                     region = self.inventory_manager.config.config.get("bot_settings", {}).get("inventory_area", {"top":100, "left":600, "width":180, "height":450})
                     # Sadece mevcut görünümü çek
                     self.capture_screenshot(sct, reason=f"inventory_page_{i}")
                     # (Sayfa değiştirme mantığı karmaşık olduğu için şimdilik tek SS)
                     break 
            
            pydirectinput.press('i') # Kapat
            
        except Exception as e:
            self.log(f"Envanter komutu hatası: {e}")
            self.telegram_msg(f"⚠️ Hata: {e}")
            
        # Botu devam ettir
        if was_running:
            self.is_paused = False
            self.log("▶️ Bot kaldığı yerden devam ediyor...")

    def tg_cmd_stop(self, text=None):
        self.stop()
        self.telegram_msg("🛑 Bot uzaktan durduruldu.")

    def tg_cmd_status(self, text=None):
        state_msg = "🟢 Çalışıyor" if self.is_running else "🔴 Durdu"
        stats = f"🎣 Tutulan: {self.stats['caught']} | ❌ Kaçan: {self.stats['missed']}"
        uptime = int(time.time() - self.start_timestamp) if self.start_timestamp > 0 else 0
        self.telegram_msg(f"{state_msg}\n{stats}\n⏱ Süre: {uptime//60}dk")

    def tg_cmd_ss(self, text=None):
        import mss
        with mss.mss() as sct:
            self.capture_screenshot(sct, reason="manual_request")

    def capture_screenshot(self, sct, reason="screenshot"):
        """Ekran görüntüsü alır ve kaydeder"""
        try:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            ss_dir = os.path.join(base_dir, "screenshots")
            if not os.path.exists(ss_dir): os.makedirs(ss_dir)
            
            filename = f"{reason}_{int(time.time())}.png"
            filepath = os.path.join(ss_dir, filename)
            
            # Tüm ekranı veya sadece oyun alanını al
            # Eğer 'inventory' ise envanterin yaklaşık bölgesini almayı dene
            monitor_area = self.monitor
            if "inventory" in reason:
                # Envanter genellikle sağ alttadır ama kullanıcı config'den okuyalım
                # Şimdilik tüm oyun penceresini al, kullanıcı zoom yapabilir
                pass
                
            img = np.array(sct.grab(monitor_area))
            cv2.imwrite(filepath, img)
            
            self.log(f"📸 Ekran görüntüsü alındı: {filename}")
            
            # Telegram'dan gönder (Filtreleme)
            if self.telegram.enabled:
                should_send = True
                
                # GM / Güvenlik durumunda ayara bak
                if "gm" in reason.lower() or "security" in reason.lower():
                     if not getattr(self, "tg_notify_gm", True): should_send = False
                
                if should_send:
                     self.telegram.send_photo(filepath, caption=f"FishBot: {reason}")
                
        except Exception as e:
            print(f"SS Hatası: {e}")
            
    def telegram_msg(self, msg):
        self.telegram.send_message(f"🎣 FishBot: {msg}")

    def sleep_random(self, min_t, max_t):
        """Güvenli rastgele bekleme"""
        time.sleep(random.uniform(min_t, max_t))

    def check_stop_conditions(self):
        """Limitlere ulaşıldı mı kontrol et"""
        if self.max_fish > 0 and self.stats["caught"] >= self.max_fish:
            self.log(f"🛑 Hedef balık sayısına ulaşıldı ({self.max_fish}). Bot duruyor.")
            if getattr(self, "tg_notify_stop", True):
                 self.telegram_msg(f"🛑 Hedef balık sayısına ulaşıldı! ({self.max_fish})")
            self.stop()
            return True
            
        if self.max_time > 0 and (time.time() - self.start_timestamp) >= self.max_time:
            self.log(f"🛑 Süre doldu ({self.max_time/60} dk). Bot duruyor.")
            if getattr(self, "tg_notify_stop", True):
                 self.telegram_msg(f"🛑 Süre doldu! ({self.max_time/60} dk)")
            self.stop()
            return True
            
        return False

    def log(self, message):
        """Arayüze log gönderir"""
        if self.log_callback:
            self.log_callback(message)
        print(f"[BOT]: {message}")

    def on_inventory_event(self, message):
        """InventoryManager'dan gelen bildirimleri işler"""
        if getattr(self, "tg_notify_catch", False):
            self.telegram_msg(message)
    def update_window_position(self):
        """Oyun penceresini bulur ve tarama alanını günceller"""
        if not IS_WINDOWS:
            self.log("[Mock] Mac ortamında pencere konumu sabit (0,0).")
            self.monitor = {"top": 100, "left": 100, "width": 800, "height": 600}
            return True

        try:
            # Tüm eşleşenleri al
            windows = gw.getWindowsWithTitle(self.window_title)
            
            target_win = None
            # Botun kendi başlığı (tahmini) - GUI'den set edilmediyse varsayılan
            # Not: BotCore GUI'ye erişemez ama kendi başlığının ne olabileceğini bilir
            possible_bot_titles = ["Metin2 Smart FishBot", "FishBot", "Bot"]

            if windows:
                # Filtreleme Mantığı
                for w in windows:
                    # Pencere başlığında bot kelimeleri geçiyorsa ve tam eşleşme değilse şüphelen
                    title = w.title
                    is_bot = False
                    for bt in possible_bot_titles:
                        if bt in title:
                            is_bot = True
                            break
                    
                    # Eğer aradığımız şey tam olarak "Metin2" ise ve bulduğumuz şey "Metin2 Smart FishBot" ise, bu bizizdir.
                    # Ama aradığımız şey "Metin2 Smart FishBot" ise, o zaman bizizdir (kullanıcı botu seçmişse hata ondadır ama handle edelim)
                    
                    if self.window_title == title:
                        # Tam eşleşme her zaman önceliklidir
                        target_win = w
                        break
                    
                    if not is_bot:
                        target_win = w
                        break
                
                # Hala bulamadıysak ilkini al (Fallback)
                if not target_win:
                    target_win = windows[0]

                win = target_win
                # Pencere varsa, oyun alanı olarak ayarla
                # Not: Tam ekran değilse başlık çubuğunu hesaba katmak gerekebilir.
                self.monitor = {
                    "top": win.top + 30, # Başlık çubuğu payı
                    "left": win.left + 8, # Sol kenar payı
                    "width": win.width - 16, 
                    "height": win.height - 38
                }
                # self.log(f"Oyun penceresi güncellendi: {win.title}")
                
                # Pencereyi aktif yap (Öne getir)
                try:
                    if not win.isActive:
                        win.activate()
                except:
                    pass
                return True
            else:
                self.log(f"'{self.window_title}' pencerisi bulunamadı!")
                return False
        except Exception as e:
            self.log(f"Pencere bulma hatası: {e}")
            return False

    def find_fish(self, img):
        """Görüntüde balığı (parlak objeyi) bulur"""
        if IS_WINDOWS:
             # MSS alpha kanalıyla (BGRA) döndürür, OpenCV BGR ister
            frame = cv2.cvtColor(np.array(img), cv2.COLOR_BGRA2BGR)
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        else:
            frame = np.array(img)[:, :, :3]
            hsv = cv2.cvtColor(frame, cv2.COLOR_RGB2HSV)

        mask = cv2.inRange(hsv, self.fish_lower, self.fish_upper)
        
        # Gürültü temizleme
        kernel = np.ones((3,3), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if contours:
            largest = max(contours, key=cv2.contourArea)
            if cv2.contourArea(largest) > 20: # Çok küçük gürültüleri atla
                M = cv2.moments(largest)
                if M["m00"] != 0:
                    cX = int(M["m10"] / M["m00"])
                    cY = int(M["m01"] / M["m00"])
                    return (cX, cY)
        return None

    def bezier_curve(self, start, end, control_points, steps=20):
        """Bézier eğrisi üzerinde noktalar üretir"""
        path = []
        for t in np.linspace(0, 1, steps):
            # De Casteljau algoritması veya basit formül
            # Quadratic Bezier: B(t) = (1-t)^2 P0 + 2(1-t)t P1 + t^2 P2
            # Cubic de olabilir ama Quadratic yeterli
            
            # Tek kontrol noktası ile (Quadratic)
            if len(control_points) == 1:
                P0 = np.array(start)
                P1 = np.array(control_points[0])
                P2 = np.array(end)
                point = (1-t)**2 * P0 + 2*(1-t)*t * P1 + t**2 * P2
            else:
                # Düz çizgi (yedek)
                point = np.array(start) * (1-t) + np.array(end) * t
                
            path.append(point.astype(int))
        return path

    def human_move(self, target_x, target_y):
        """İnsan benzeri kavisli mouse hareketi"""
        if not IS_WINDOWS: return

        # Mevcut mouse konumu
        current_x, current_y = pydirectinput.position()
        
        # Hedef koordinatlar (Ekranın sol üstüne göre, monitor offset eklenmeli)
        abs_target_x = self.monitor["left"] + target_x
        abs_target_y = self.monitor["top"] + target_y
        
        # Pydirectinput bazen tam kordinatı vermeyebilir o yüzden güvenli yaklaşım:
        # Pydirectinput position'ı doğru vermezse pyautogui kullanılabilir ama oyunlar pyautogui engeller.
        # Bu yüzden başlangıç noktası olarak 'varsayılan' bir nokta veya son bilinen nokta alırız.
        # Ancak pydirectinput.position() çalışır.
        
        start = (current_x, current_y)
        end = (abs_target_x, abs_target_y)
        
        # Kontrol noktası: Başlangıç ile bitiş arasında rastgele bir sapma noktası
        mid_x = (start[0] + end[0]) / 2
        mid_y = (start[1] + end[1]) / 2
        
        # Sapma miktarı
        offset_x = random.randint(-100, 100)
        offset_y = random.randint(-100, 100)
        
        control_point = (mid_x + offset_x, mid_y + offset_y)
        
        # Yolu oluştur
        steps = random.randint(15, 25) # Adım sayısı değişkenliği
        path = self.bezier_curve(start, end, [control_point], steps)
        
        # Hareket et
        for point in path:
            pydirectinput.moveTo(point[0], point[1])
            # Çok kısa bekleme (hız kontrolü)
            time.sleep(random.uniform(0.001, 0.005)) 
            
    def worker_loop(self):
        """Botun ana döngüsü"""
        self.log("Bot servisi başlatıldı.")
        self.start_timestamp = time.time()
        
        # Pencere konumunu al
        if not self.update_window_position():
            self.log("Pencere bulunamadığı için durduruldu.")
            self.is_running = False
            return

        # MSS Başlat
        if IS_WINDOWS:
            sct_manager = mss.mss
        else:
            sct_manager = mss

        with sct_manager() as sct:
            while self.is_running:
                
                if IS_WINDOWS:
                    # Görseli al
                    try:
                        screenshot = sct.grab(self.monitor)
                        img = np.array(screenshot)
                        img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
                    except Exception as e:
                        self.log(f"Ekran alma hatası: {e}")
                        time.sleep(1)
                        continue

                    # --- SİSTEM KONTROLLERİ (Ölüm, Crash) ---
                    if self.check_system_events(img):
                        time.sleep(2) # Olay olduysa bekle
                        continue
                    # ----------------------------------------

                if self.check_stop_conditions():
                    break
                    
                if self.state == "IDLE":
                    # Olta atma öncesi rastgele bekleme
                    self.sleep_random(self.cast_min, self.cast_max)
                    
                    # --- YEM YENİLEME (HER ATIŞTA) ---
                    if IS_WINDOWS:
                        import direct_input
                        self.log("🪱 Yem takılıyor...")
                        direct_input.send_key(self.bait_key)
                        time.sleep(1.0) # Yem takma animasyon payı
                    
                    # ------------------------------------

                    self.log("Olta atılıyor...")
                    if IS_WINDOWS:
                        # Olta At (Space)
                        # Space tuşuna biraz daha uzun basalım
                        direct_input.send_key("space", duration=0.2)
                    
                    self.stats["casts"] += 1
                    
                    # KRİTİK DÜZELTME: State değişimi
                    self.state = "WAITING_FISH"
                    self.wait_start_time = time.time()
                    # self.log("Balık/Minigame bekleniyor...")
                    
                    # Eski Yem Mantığı (Paket Sayacı - Opsiyonel Log için)
                    self.worm_counter += 1
                    if self.inventory_manager and self.worm_counter >= 200:
                        self.log("ℹ️ Bir kutu yem bitmiş olabilir.")
                        self.worm_counter = 0

                    # Olta atma animasyonu bekleme
                    base = BotSettings.ANIMATION_WAIT_BASE
                    wait_time = random.uniform(base, base + 0.5)
                    # self.sleep_random(...) yerine time.sleep kullanalim, bloklanmasin
                    time.sleep(wait_time) 

                elif self.state == "WAITING_FISH":
                    # --- MİNİGAME MODU: KIRMIZI GÖR -> SİYAHA VUR ---
                    
                    # 1. Timeout Kontrolü
                    if (time.time() - self.wait_start_time) > self.wait_timeout:
                          self.log("⚠️ Zaman aşımı! Sıradaki...")
                          self.state = "IDLE"
                          self.anti_afk_routine()
                          continue
                    
                    # 2. Görüntü Al
                    img = sct.grab(self.monitor)
                    
                    # 3. Kırmızı Daire Kontrolü (Tetikleyici)
                    red_center = self.detect_red_trigger(img)
                    
                    if red_center:
                         # Kırmızıyı gördük! Sadece bu dairenin içinde balık ara.
                         # red_center -> (x, y)
                         fish_pos = self.find_fish(img, roi_center=red_center, roi_radius=70) 
                         
                         if fish_pos:
                             self.log(f"🔴 KIRMIZI ! -> 🐟 Hedef: {fish_pos}")
                             
                             if IS_WINDOWS:
                                 import direct_input
                                 
                                 # Balığın konumuna git
                                 tx, ty = fish_pos # Balığın merkezi
                                 abs_x = int(self.monitor["left"] + tx)
                                 abs_y = int(self.monitor["top"] + ty)
                                 
                                 self.log(f"📍 Mouse taşınıyor: {abs_x}, {abs_y}")
                                 
                                 # 1. Fareyi oraya götür (Donanım Seviyesi)
                                 direct_input.move_mouse(abs_x, abs_y)
                                 
                                 # Kısa bir bekleme (Oyunun mouse'un geldiğini anlaması için)
                                 time.sleep(0.05)
                                 
                                 # 2. VUR! (Sadece Mouse Click - Kullanıcı isteği)
                                 # direct_input.send_key("space") # Space'i şimdilik kapattık
                                 direct_input.click_mouse()
                                 
                                 self.stats["caught"] += 1
                                 self.log("✅ Tıklandı!")
                                 
                                 # Minigame bitişini bekle ve başa dön
                                 time.sleep(1.5)
                                 self.state = "IDLE"
                         else:
                             self.log("⚠️ Kırmızı var, Balık YOK! (Siyah nesne bulunamadı)")

                    time.sleep(0.01) # Çok hızlı tarama (Refleks için)

    def detect_red_trigger(self, img):
        """Görüntüde Kırmızı Daire/Halka var mı? Varsa merkezini döndür."""
        try:
            frame = np.array(img)
            if frame.shape[2] == 4:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            
            # Kırmızı Renk Maskeleme (Private Server Ayarı)
            lower1 = np.array([0, 100, 100])
            upper1 = np.array([10, 255, 255])
            lower2 = np.array([170, 100, 100])
            upper2 = np.array([180, 255, 255])
            mask = cv2.addWeighted(cv2.inRange(hsv, lower1, upper1), 1.0, cv2.inRange(hsv, lower2, upper2), 1.0, 0.0)
            
            kernel = np.ones((3,3), np.uint8)
            mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
            
            # Kontur bul (Merkez için şart)
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            if contours:
                largest = max(contours, key=cv2.contourArea)
                if cv2.contourArea(largest) > 200: # Yeterli büyüklükte kırmızı
                    M = cv2.moments(largest)
                    if M["m00"] != 0:
                        cX = int(M["m10"] / M["m00"])
                        cY = int(M["m01"] / M["m00"])
                        return (cX, cY)
            return None
        except:
            return None

    def find_fish(self, img, roi_center=None, roi_radius=60):
        """Balığı (Maskelenmiş alanı) bulur. roi_center verilirse sadece oraya bakar."""
        try:
            frame = np.array(img)
            # Eğer ROI verildiyse görüntüyü kırp (Sanal olarak)
            offset_x, offset_y = 0, 0
            
            if roi_center:
                cx, cy = roi_center
                x1 = max(0, cx - roi_radius)
                y1 = max(0, cy - roi_radius)
                x2 = min(frame.shape[1], cx + roi_radius)
                y2 = min(frame.shape[0], cy + roi_radius)
                
                frame = frame[y1:y2, x1:x2]
                offset_x, offset_y = x1, y1

            if frame.shape[2] == 4:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
            
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            mask = cv2.inRange(hsv, self.fish_lower, self.fish_upper)
            
            # Gürültü ve yumuşatma
            kernel = np.ones((3,3), np.uint8)
            mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
            
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            if contours:
                largest = max(contours, key=cv2.contourArea)
                
                # Su dalgalarını elemek için boyutu artırıyoruz (Balık bayağı büyük)
                if cv2.contourArea(largest) > 120: 
                    M = cv2.moments(largest)
                    if M["m00"] != 0:
                        cX = int(M["m10"] / M["m00"]) + offset_x
                        cY = int(M["m01"] / M["m00"]) + offset_y
                        return (cX, cY)
            return None
        except Exception as e:
            return None


    def process_inventory(self, sct):
        """Envanteri tarar ve işlemleri yapar (Çok sayfalı destek)"""
        self.log("🧹 Envanter kontrol ediliyor...")
        
        # Envanteri aç (I tuşu)
        pydirectinput.press('i')
        time.sleep(1.0) 
        
        # Tarama Alanı
        inv_region = {
            "top": self.monitor["top"], 
            "left": self.monitor["left"] + int(self.monitor["width"] * 0.4), # Sağ %60
            "width": int(self.monitor["width"] * 0.6), 
            "height": self.monitor["height"]
        }
        
        if not hasattr(self, 'inventory_manager'):
            from inventory import InventoryManager
            # Callback fonksiyonunu bağla
            self.inventory_manager = InventoryManager(telegram_callback=self.on_inventory_event)
        else:
             # Varolan manager'ın callback'ini güncelle (Config reload sonrası değişmiş olabilir)
             self.inventory_manager.telegram_callback = self.on_inventory_event

        assets_dir = os.path.join(os.path.dirname(__file__), "..", "assets")
        total_processed = 0

        # Sayfa 1'den 4'e kadar dolaş (Görsel varsa)
        for page_num in range(1, 5):
            # Sayfaya geçiş yap (Sayfa 1 zaten açık varsayılır ama emin olmak için tıklanabilir)
            # Sayfa butonunu bulmaya çalış: 'page_1.png', 'page_2.png'...
            page_icon = f"page_{page_num}.png"
            page_path = os.path.join(assets_dir, page_icon)
            
            page_switched = False
            
            # Eğer sayfa butonu görseli varsa, onu bul ve tıkla
            if os.path.exists(page_path):
                try:
                    # Tüm ekranda butonu ara (veya inv_region içinde)
                    full_ss = np.array(sct.grab(inv_region))
                    full_gray = cv2.cvtColor(full_ss, cv2.COLOR_BGRA2GRAY)
                    template = cv2.imread(page_path, 0)
                    
                    res = cv2.matchTemplate(full_gray, template, cv2.TM_CCOEFF_NORMED)
                    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
                    
                    if max_val > 0.85: # Bulundu!
                        # Butona tıkla
                        click_x = inv_region["left"] + max_loc[0] + template.shape[1] // 2
                        click_y = inv_region["top"] + max_loc[1] + template.shape[0] // 2
                        
                        pydirectinput.moveTo(click_x, click_y)
                        time.sleep(0.2)
                        pydirectinput.click()
                        time.sleep(0.5) # Sayfa yüklenme beklemesi
                        page_switched = True
                        # self.log(f"Sayfa {page_num}'e geçildi.")
                except Exception as e:
                    print(f"Sayfa {page_num} geçiş hatası: {e}")
            
            # Eğer 1. sayfa hariç diğer sayfalara geçemediysek (görsel yoksa), döngüyü kır
            # (Yani kullanıcı sadece page_1 ve page_2 yüklediyse 3'e bakma)
            if page_num > 1 and not page_switched:
                break

            # Mevcut sayfayı tara
            count = self.inventory_manager.scan_and_process(sct, inv_region)
            total_processed += count
            time.sleep(0.2)

        if total_processed > 0:
            self.log(f"♻️ Toplam {total_processed} eşya işlendi.")
            
        # Envanteri kapat
        pydirectinput.press('i')
        time.sleep(0.5)

    def detect_fish_bubble(self, sct):
        """Karakterin üzerinde balık balonu çıkıp çıkmadığını kontrol eder"""
        # Mock Ortam
        if not IS_WINDOWS:
            return random.random() < 0.05

        # Tarama Alanı: Ekranın tam ortası (Karakterin kafasının üstü)
        # Genişlik: %20, Yükseklik: %20 (Ortalanmış)
        mw, mh = self.monitor["width"], self.monitor["height"]
        mx, my = self.monitor["left"], self.monitor["top"]
        
        search_area = {
            "top": my + int(mh * 0.3),  # Üstten %30 aşağıda başla
            "left": mx + int(mw * 0.4), # Soldan %40 içeride
            "width": int(mw * 0.2),     # Genişlik %20
            "height": int(mh * 0.25)    # Yükseklik %25
        }
        
        img = np.array(sct.grab(search_area))
        
        # 1. Yöntem: Template Matching (Eğer şablon varsa)
        if hasattr(self, 'bubble_template') and self.bubble_template is not None:
            gray_img = cv2.cvtColor(img, cv2.COLOR_BGRA2GRAY)
            res = cv2.matchTemplate(gray_img, self.bubble_template, cv2.TM_CCOEFF_NORMED)
            conf = np.max(res)
            if conf > 0.7: # %70 Güvenilirlik
                # self.log(f"Debug: Balon bulundu (Skor: {conf:.2f})")
                return True
                
        # 2. Yöntem: Parlaklık/Beyazlık Kontrolü (Fallback)
        # Balık balonu bembeyazdır. Bölgedeki beyaz piksel yoğunluğuna bak.
        hsv = cv2.cvtColor(img, cv2.COLOR_BGRA2HSV)
        # Beyaz renk maskesi (Düşük doygunluk, yüksek parlaklık)
        lower_white = np.array([0, 0, 200])
        upper_white = np.array([180, 50, 255])
        mask = cv2.inRange(hsv, lower_white, upper_white)
        
        white_pixels = cv2.countNonZero(mask)
        total_pixels = search_area["width"] * search_area["height"]
        ratio = white_pixels / total_pixels
        
        # Eğer alanın %3'ünden fazlası aniden beyaz olduysa balondur
        # (Normalde karakterin ismi vs. de beyaz olabilir, threshold ayarı gerekebilir)
        if ratio > 0.03: 
            # self.log(f"Debug: Beyazlık algılandı (Oran: {ratio:.3f})")
            return True
            
        return False

    def check_bait(self):
        """Yem kontrolü ve yenileme"""
        # Kullanıcının seçtiği tuşa göre tazele
        if self.stats["casts"] % 20 == 0:
            key = getattr(self, 'bait_key', 'F1')
            self.log(f"🪱 Yem tazeleniyor... (Tuş: {key})")
            pydirectinput.press(key)
            time.sleep(0.5)

    def post_catch_routine(self):
        """Balık tutulduktan sonra yapılacak işlemler"""
        # Yem kontrolü
        self.check_bait()
        
        # Envanter Doluluk Kontrolü (Görüntü işleme ile yapılmalı)
        # Şimdilik basitçe loglayalım
        # self.scan_inventory_and_clean() yapısı buraya gelecek

    def anti_afk_routine(self):
        """Robot gibi görünmemek için rastgele hareketler"""
        if random.random() < 0.1: # %10 şansla
            action = random.choice(["camera", "move", "wait"])
            
            if action == "camera":
                key = random.choice(['q', 'e'])
                duration = random.uniform(0.1, 0.3)
                self.log(f"Anti-AFK: Kamera dönüşü ({key})")
                pydirectinput.keyDown(key)
                time.sleep(duration)
                pydirectinput.keyUp(key)
                
            elif action == "move":
                key = random.choice(['w', 's', 'a', 'd'])
                self.log(f"Anti-AFK: Küçük adım ({key})")
                pydirectinput.keyDown(key)
                time.sleep(0.05) # Çok kısa bas
                pydirectinput.keyUp(key)
                
            elif action == "wait":
                wait_time = random.uniform(2.0, 5.0)
                self.log(f"Anti-AFK: Dinleniyor ({wait_time:.1f}s)...")
                time.sleep(wait_time)

    def start(self):
        if not self.is_running:
            self.is_running = True
            self.thread = threading.Thread(target=self.worker_loop)
            self.thread.daemon = True
            self.thread.start()

    def stop(self):
        self.is_running = False
        self.log("Bot durduruldu.")

    def check_system_events(self, img):
        """Kritik sistem olaylarını kontrol et (Ölüm, Crash, Login)"""
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            sys_dir = os.path.join(current_dir, "assets", "system")
            
            # 1. Ölüm Kontrolü (restart_here.png)
            restart_path = os.path.join(sys_dir, "restart_here.png")
            if os.path.exists(restart_path):
                template = cv2.imread(restart_path, cv2.IMREAD_COLOR)
                if template is not None:
                    res = cv2.matchTemplate(img, template, cv2.TM_CCOEFF_NORMED)
                    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
                    
                    if max_val > 0.8:
                        self.log("💀 KARAKTER ÖLDÜ! 15sn soğuma süresi bekleniyor...")
                        time.sleep(15) # Soğuma süresi
                        
                        # Butonun ortasına tıkla
                        h, w = template.shape[:2]
                        cx = self.monitor["left"] + max_loc[0] + w // 2
                        cy = self.monitor["top"] + max_loc[1] + h // 2
                        
                        pydirectinput.click(cx, cy)
                        self.log("❤️ Karakter canlandırıldı.")
                        
                        if hasattr(self, 'telegram') and self.telegram and self.telegram.enabled:
                            self.telegram.send_message("💀 Karakter Öldü! Otomatik canlandırıldı.")
                            
                        time.sleep(5) # Ayağa kalkma süresi
                        return True

            # 2. Crash/Disconnect Kontrolü (disconnect.png)
            disc_path = os.path.join(sys_dir, "disconnect.png")
            if os.path.exists(disc_path):
                template = cv2.imread(disc_path, cv2.IMREAD_COLOR)
                if template is not None:
                    res = cv2.matchTemplate(img, template, cv2.TM_CCOEFF_NORMED)
                    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
                    
                    if max_val > 0.8:
                        self.log("⚠️ KRİTİK: Oyun Bağlantısı Koptu!")
                        if hasattr(self, 'telegram') and self.telegram and self.telegram.enabled:
                            self.telegram.send_message("⚠️ Oyun Bağlantısı Koptu! Bot durduruluyor.")
                        self.stop()
                        return True
                        
            # 3. Login Ekranı Kontrolü (login_check.png)
            login_path = os.path.join(sys_dir, "login_check.png")
            if os.path.exists(login_path):
                template = cv2.imread(login_path, cv2.IMREAD_COLOR)
                if template is not None:
                    res = cv2.matchTemplate(img, template, cv2.TM_CCOEFF_NORMED)
                    _, max_val, _, _ = cv2.minMaxLoc(res)
                    if max_val > 0.8:
                        self.log("⚠️ KRİTİK: Login ekranına düşüldü!")
                        self.stop()
                        return True

        except Exception as e:
            pass # Hata olursa botu durdurma, devam et
            
        return False
        
    def _refill_bait_routine(self):
        """Envanteri açıp yem yeniler ve kapatır"""
        try:
            # Envanteri Aç (I tuşu standarttır)
            pydirectinput.press('i')
            time.sleep(1.0) # Animasyon bekle
            
            # Inventory Manager ile işlem yap
            # Tüm ekranın monitör bilgisini veriyoruz
            if self.inventory_manager:
                success = self.inventory_manager.replenish_bait(self.monitor)
                if not success:
                    self.log("⚠️ Yem bulunamadı veya işlem yapılamadı.")
            
            # Envanteri Kapat
            pydirectinput.press('i')
            time.sleep(0.5)
            
        except Exception as e:
            self.log(f"Yem yenileme hatası: {e}")
            
        return False

if __name__ == "__main__":
    # Test
    bot = BotCore()
    bot.start()
    time.sleep(5)
    bot.stop()
