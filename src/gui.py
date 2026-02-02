
import customtkinter as ctk
import threading
import time
import os
import shutil
from tkinter import filedialog, simpledialog
from PIL import Image

# Modüllerimizi içe aktaralım
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from bot_core import BotCore
from inventory import InventoryManager
from stats import FishStats
from scheduler import BotScheduler
from sound_alert import SoundAlert
from multi_account import MultiAccountManager
from profiles import ProfileManager
from hotkeys import HotkeyManager
from reports import ReportManager
import updater

ctk.set_appearance_mode("Dark")  # Modes: "System" (standard), "Dark", "Light"
ctk.set_default_color_theme("blue")  # Themes: "blue" (standard), "green", "dark-blue"

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        print("DEBUG: App.__init__ başladı.")

        # --- MODÜL BAŞLATMA (ÖNCELİKLİ) ---
        try:
            print("DEBUG: InventoryManager oluşturuluyor...")
            self.inventory_manager = InventoryManager() 
            print(f"DEBUG: InventoryManager oluşturuldu: {self.inventory_manager}")
            print(f"DEBUG: ConfigManager: {getattr(self.inventory_manager, 'config', 'YOK')}")
        except Exception as e:
            print(f"DEBUG: InventoryManager oluşturma HATASI: {e}")

        self.bot = BotCore(update_log_callback=self.update_log)
        self.fish_stats = FishStats()
        self.sound_alert = SoundAlert()
        self.profile_manager = ProfileManager()
        self.hotkey_manager = HotkeyManager()
        
        self.scheduler = BotScheduler()
        self.scheduler.set_callbacks(
            on_start=self.start_bot_scheduled,
            on_stop=self.stop_bot_scheduled,
            on_log=self.update_log
        )
        
        self.account_manager = MultiAccountManager()
        self.current_account_id = self.account_manager.create_session(
            name="Varsayılan",
            bot_instance=self.bot,
            monitor=self.bot.monitor
        )
        
        self.report_manager = ReportManager()
        self.report_manager.set_stats(self.fish_stats)
        self.report_manager.set_inventory(self.inventory_manager)
        
        self.hotkey_manager.set_callbacks(
            toggle=self.toggle_bot,
            stop=self.emergency_stop,
            screenshot=self.take_screenshot,
            pause=self.pause_5min,
            log=self.update_log
        )

        
        # Bot Entegrasyon
        self.bot.fish_stats = self.fish_stats
        self.bot.sound_alert = self.sound_alert
        self.bot.inventory_manager = self.inventory_manager
        self.bot.gui_start_callback = self.toggle_bot
        # ---------------------------------

        # Pencere Ayarları
        self.title("Metin2 Smart FishBot - Pro Version")
        self.geometry("900x650")
        
        # Grid Layout (2 Sütun)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- SOL PANEL (Sidebar) ---
        self.sidebar_frame = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(7, weight=1)

        self.title_label = ctk.CTkLabel(self.sidebar_frame, text="🎣 FishBot v2.0", font=ctk.CTkFont(size=20, weight="bold"))
        self.title_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        # Başlat / Durdur
        self.start_button = ctk.CTkButton(self.sidebar_frame, text="BAŞLAT", fg_color="green", hover_color="darkgreen", command=self.toggle_bot)
        self.start_button.grid(row=1, column=0, padx=20, pady=10)
        
        # Alan Seçimi (Kalibrasyon)
        self.calibrate_btn = ctk.CTkButton(self.sidebar_frame, text="[+] Alan Seç (Manuel)", fg_color="gray", command=self.calibrate_area)
        self.calibrate_btn.grid(row=2, column=0, padx=20, pady=(10, 5))
        
        # Pencere Seçimi
        self.win_btn = ctk.CTkButton(self.sidebar_frame, text="🖥 Pencere Seç", fg_color="#445566", command=self.select_window_dialog)
        self.win_btn.grid(row=3, column=0, padx=20, pady=5)
        
        # --- Multi-Account Bölümü (Opsiyonel) ---
        self.account_frame = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        self.account_frame.grid(row=4, column=0, padx=10, pady=10, sticky="ew")
        
        ctk.CTkLabel(self.account_frame, text="📋 Hesaplar", font=ctk.CTkFont(size=11, weight="bold")).pack(anchor="w")
        
        # Hesap Seçici
        self.account_list = ["Varsayılan"]
        self.account_selector = ctk.CTkOptionMenu(self.account_frame, values=self.account_list, 
                                                   command=self.switch_account, width=140)
        self.account_selector.pack(pady=5, fill="x")
        
        # Hesap Ekle Butonu
        self.btn_add_account = ctk.CTkButton(self.account_frame, text="➕ Hesap Ekle", width=140,
                                              fg_color="#607D8B", command=self.add_account_dialog)
        self.btn_add_account.pack(pady=2)

        # İstatistikler
        self.stats_label = ctk.CTkLabel(self.sidebar_frame, text="Caught: 0\nMissed: 0", justify="left")
        self.stats_label.grid(row=7, column=0, padx=20, pady=20, sticky="s")

        # --- SAĞ PANEL (Tabview) ---
        self.main_view = ctk.CTkTabview(self, width=650)
        self.main_view.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        
        self.tab_dashboard = self.main_view.add("Dashboard")
        self.tab_settings = self.main_view.add("Balık Ayarları")
        self.tab_stats = self.main_view.add("📊 İstatistik")
        self.tab_scheduler = self.main_view.add("⏰ Zamanlayıcı")
        self.tab_assets = self.main_view.add("Görseller")
        self.tab_advanced = self.main_view.add("Gelişmiş")

        # --> TAB 1: DASHBOARD
        self.log_textbox = ctk.CTkTextbox(self.tab_dashboard, width=600, height=180)
        self.log_textbox.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.log_textbox.insert("0.0", "Bot Hazır. Başlamak için 'Pencere Seç' yapın veya alan belirleyin.\n")
        
        # Canlı Önizleme Alanı
        preview_frame = ctk.CTkFrame(self.tab_dashboard)
        preview_frame.grid(row=1, column=0, pady=10, padx=10, sticky="nsew")
        
        preview_header = ctk.CTkFrame(preview_frame, fg_color="transparent")
        preview_header.pack(fill="x", padx=5, pady=5)
        ctk.CTkLabel(preview_header, text="📷 Canlı Önizleme", font=ctk.CTkFont(size=12, weight="bold")).pack(side="left")
        
        self.preview_active = False
        self.btn_preview_toggle = ctk.CTkButton(preview_header, text="▶️ Başlat", width=80,
                                                  command=self.toggle_preview, fg_color="#2196F3")
        self.btn_preview_toggle.pack(side="right", padx=5)
        
        # Önizleme Görüntüsü
        self.preview_label = ctk.CTkLabel(preview_frame, text="[Önizleme için 'Başlat' butonuna tıklayın]", 
                                           fg_color="black", width=400, height=220, corner_radius=10)
        self.preview_label.pack(pady=5)
        
        # FPS Göstergesi
        self.preview_fps_label = ctk.CTkLabel(preview_frame, text="FPS: -", text_color="gray")
        self.preview_fps_label.pack()
        
        self.monitor_info = ctk.CTkLabel(self.tab_dashboard, text="Seçili Alan: Yok")
        self.monitor_info.grid(row=2, column=0)

        # --> TAB 2: BALIK AYARLARI (Scrollable Fish List)
        self.scroll_frame = ctk.CTkScrollableFrame(self.tab_settings, label_text="Ne Yapılsın?", width=600, height=450)
        self.scroll_frame.pack(fill="both", expand=True)
        
        # --> TAB 3: İSTATİSTİK
        self.create_stats_tab()
        
        # --> TAB 4: ZAMANLAYICI
        self.create_scheduler_tab()
        
        # --> TAB 5: Görseller (ASSETS)
        self.create_assets_content()

        # --> TAB 4: GELİŞMİŞ (Ayarlar)
        # Scrollable Frame ekleyelim ki sığsın
        self.adv_scroll = ctk.CTkScrollableFrame(self.tab_advanced, width=600, height=500)
        self.adv_scroll.pack(fill="both", expand=True)

        # === HIZLI PROFİL SEÇİCİ ===
        profile_frame = ctk.CTkFrame(self.adv_scroll, fg_color="#1a1a2e")
        profile_frame.pack(fill="x", padx=10, pady=(10, 5))
        
        ctk.CTkLabel(profile_frame, text="⚡ Hızlı Profil", font=ctk.CTkFont(size=14, weight="bold")).pack(side="left", padx=10, pady=10)
        
        # Profil listesi
        profile_names = ["🎯 Normal", "⚡ Turbo", "🥷 Gizli", "🌙 Gece", "💤 AFK"]
        profile_ids = ["normal", "turbo", "stealth", "night", "afk"]
        
        self.profile_var = ctk.StringVar(value="🎯 Normal")
        self.profile_dropdown = ctk.CTkOptionMenu(profile_frame, values=profile_names, variable=self.profile_var,
                                                   command=self.apply_profile, width=150)
        self.profile_dropdown.pack(side="left", padx=10)
        
        # Profil açıklaması
        self.profile_desc_label = ctk.CTkLabel(profile_frame, text="Dengeli ayarlar, günlük kullanım için ideal", 
                                                text_color="gray", font=ctk.CTkFont(size=11))
        self.profile_desc_label.pack(side="left", padx=10)
        
        # === HOTKEY DURUMU ===
        hotkey_frame = ctk.CTkFrame(self.adv_scroll, fg_color="#1a2e1a")
        hotkey_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(hotkey_frame, text="🎮 Kısayollar", font=ctk.CTkFont(size=12, weight="bold")).pack(side="left", padx=10, pady=8)
        ctk.CTkLabel(hotkey_frame, text="F9=Başlat/Durdur | F10=Acil Dur | F11=Ekran Görüntüsü | F12=5dk Mola", 
                     text_color="lightgreen", font=ctk.CTkFont(size=10)).pack(side="left", padx=5)
        
        self.hotkey_status_label = ctk.CTkLabel(hotkey_frame, text="⏳ Yükleniyor...", text_color="yellow")
        self.hotkey_status_label.pack(side="right", padx=10)

        ctk.CTkLabel(self.adv_scroll, text="⏱ Zamanlama ve Gecikmeler", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
        


        # Ayarları Yükle
        try:
            defaults = self.inventory_manager.config.DEFAULT_CONFIG["bot_settings"]
            current_config = getattr(self.inventory_manager.config, 'config', {})
            if current_config is None: current_config = {}
            
            cfg = current_config.get("bot_settings", defaults)
            limits = current_config.get("stop_conditions", {"max_time_min": 0, "max_fish": 0})
        except Exception as e:
            print(f"⚠️ Ayar yükleme hatası: {e}")
            cfg = defaults
            limits = {"max_time_min": 0, "max_fish": 0}

        # Cast Range
        self.cast_min = cfg.get("cast_delay_min", 2.0)
        self.cast_max = cfg.get("cast_delay_max", 2.5)
        
        frame_cast = ctk.CTkFrame(self.adv_scroll)
        frame_cast.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(frame_cast, text="Olta Atma Animasyon Bekleme (Min-Max sn):").pack(anchor="w", padx=10)
        
        cast_row = ctk.CTkFrame(frame_cast)
        cast_row.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(cast_row, text="Min:").pack(side="left", padx=5)
        self.entry_cast_min = ctk.CTkEntry(cast_row, width=60, placeholder_text="1.5")
        self.entry_cast_min.insert(0, str(self.cast_min))
        self.entry_cast_min.pack(side="left", padx=5)
        
        ctk.CTkLabel(cast_row, text="Max:").pack(side="left", padx=15)
        self.entry_cast_max = ctk.CTkEntry(cast_row, width=60, placeholder_text="3.0")
        self.entry_cast_max.insert(0, str(self.cast_max))
        self.entry_cast_max.pack(side="left", padx=5)


        ctk.CTkLabel(self.adv_scroll, text="Yem Tuşu & Hassasiyet", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(20, 5))
        
        frame_keys = ctk.CTkFrame(self.adv_scroll)
        frame_keys.pack(fill="x", padx=10, pady=5)
        
        # Timeout Entry
        self.timeout_val = cfg.get("wait_timeout", 10.0)
        timeout_row = ctk.CTkFrame(frame_keys)
        timeout_row.pack(fill="x", padx=5, pady=5)
        ctk.CTkLabel(timeout_row, text="Balık Gelmezse Timeout (sn):").pack(side="left", padx=5)
        self.entry_timeout = ctk.CTkEntry(timeout_row, width=60, placeholder_text="10")
        self.entry_timeout.insert(0, str(self.timeout_val))
        self.entry_timeout.pack(side="left", padx=5)
        
        # GM Detect
        self.var_gm = ctk.BooleanVar(value=cfg.get("gm_detect", True))
        ctk.CTkCheckBox(frame_keys, text="GM / Fısıltı Algılayınca Dur", variable=self.var_gm).pack(pady=5, anchor="w", padx=10)

        # Stop Conditions
        ctk.CTkLabel(self.adv_scroll, text="🛑 Durdurma Koşulları (0 = Devre Dışı)", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=(20, 5))
        ctk.CTkLabel(self.adv_scroll, text="Bot belirlenen süre veya balık sayısına ulaşınca otomatik durur.", 
                     text_color="gray", font=ctk.CTkFont(size=11)).pack(anchor="w", padx=15)
        
        frame_stop = ctk.CTkFrame(self.adv_scroll)
        frame_stop.pack(fill="x", padx=10, pady=5)
        
        # Süre Girişi
        stop_time_frame = ctk.CTkFrame(frame_stop, fg_color="transparent")
        stop_time_frame.pack(side="left", padx=10, pady=5, expand=True)
        ctk.CTkLabel(stop_time_frame, text="⏱️ Maks Süre (Dakika):", font=ctk.CTkFont(size=12)).pack(anchor="w")
        self.entry_max_min = ctk.CTkEntry(stop_time_frame, placeholder_text="örn: 60", width=80)
        self.entry_max_min.insert(0, str(limits.get("max_time_min", 0)))
        self.entry_max_min.pack(anchor="w", pady=2)
        
        # Balık Sayısı Girişi
        stop_fish_frame = ctk.CTkFrame(frame_stop, fg_color="transparent")
        stop_fish_frame.pack(side="left", padx=10, pady=5, expand=True)
        ctk.CTkLabel(stop_fish_frame, text="🐟 Maks Balık Sayısı:", font=ctk.CTkFont(size=12)).pack(anchor="w")
        self.entry_max_fish = ctk.CTkEntry(stop_fish_frame, placeholder_text="örn: 100", width=80)
        self.entry_max_fish.insert(0, str(limits.get("max_fish", 0)))
        self.entry_max_fish.pack(anchor="w", pady=2)

        # Yem Tuşu Seçimi
        current_bait = cfg.get("bait_key", "F1")
        ctk.CTkLabel(frame_keys, text="Yem Tuşu:").pack(side="left", padx=5)
        self.combo_bait_key = ctk.CTkComboBox(frame_keys, values=["1", "2", "3", "4", "F1", "F2", "F3", "F4"])
        self.combo_bait_key.set(current_bait)
        self.combo_bait_key.pack(side="right", padx=10)

        # Telegram Ayarları
        ctk.CTkLabel(self.adv_scroll, text="📱 Telegram Bildirim Ayarları", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=(20, 5))
        frame_tg = ctk.CTkFrame(self.adv_scroll)
        frame_tg.pack(fill="x", padx=10, pady=5)
        
        tg_conf = self.inventory_manager.config.config.get("telegram", {})
        
        self.entry_tg_token = ctk.CTkEntry(frame_tg, placeholder_text="Bot Token")
        self.entry_tg_token.insert(0, tg_conf.get("token", ""))
        self.entry_tg_token.pack(fill="x", padx=5, pady=2)
        
        self.entry_tg_chat = ctk.CTkEntry(frame_tg, placeholder_text="Chat ID")
        self.entry_tg_chat.insert(0, tg_conf.get("chat_id", ""))
        self.entry_tg_chat.pack(fill="x", padx=5, pady=2)
        
        # Bildirim Seçenekleri
        self.check_tg_stop = ctk.CTkCheckBox(frame_tg, text="Bot Durduğunda Bildir")
        if tg_conf.get("notify_on_stop", True): self.check_tg_stop.select()
        self.check_tg_stop.pack(pady=2, anchor="w", padx=5)
        
        self.check_tg_gm = ctk.CTkCheckBox(frame_tg, text="GM / Fısıltı Gelirse Bildir")
        if tg_conf.get("notify_on_gm", True): self.check_tg_gm.select()
        self.check_tg_gm.pack(pady=2, anchor="w", padx=5)

        self.check_tg_catch = ctk.CTkCheckBox(frame_tg, text="Nadir Balık Yakalayınca Bildir")
        if tg_conf.get("notify_on_catch", False): self.check_tg_catch.select()
        self.check_tg_catch.pack(pady=2, anchor="w", padx=5)

        # Kaydet Butonu
        self.save_settings_btn = ctk.CTkButton(self.adv_scroll, text="💾 TÜM AYARLARI KAYDET", height=40, font=ctk.CTkFont(size=14, weight="bold"), command=self.save_advanced_settings)
        self.save_settings_btn.pack(pady=30)


        # Balık Listesini Yükle (sound_alert tanımlı olmalı)
        self.load_fish_list()
        
        # Telegram bağlantısı varsa rapor yöneticisine de bağla
        if hasattr(self.bot, 'telegram') and self.bot.telegram:
            self.report_manager.set_telegram(self.bot.telegram)
            self.report_manager.start_daily_scheduler()
        
        # Hotkey'leri başlat (opsiyonel)
        try:
            self.hotkey_manager.start()
        except:
            self.update_log("⚠️ Hotkey başlatılamadı (pynput gerekli)")
        
        self.update_stats()
        
        # Güncelleme Kontrolü
        updater.check_for_updates(self.on_update_check)

    def on_update_check(self, has_update, version):
        """Güncelleme kontrolü sonucu"""
        if has_update:
            msg = f"🚀 YENİ GÜNCELLEME MEVCUT! (v{version})"
            self.update_log(msg)
            
            # Güncelle butonunu görünür yap veya renkli uyar
            if hasattr(self, 'title_label'):
                self.title_label.configure(text=f"Metin2 FishBot v2.1 (Update: v{version})", text_color="#FF5722")
            
            # Telegram'a da bildir
            if hasattr(self.bot, 'telegram') and self.bot.telegram and self.bot.telegram.enabled:
                self.bot.telegram.send_message(f"📢 Yeni güncelleme (v{version}) mevcut! Lütfen botu güncelleyin.")
        else:
            self.update_log(f"✅ Bot Güncel (v{version})")

    def create_stats_tab(self):
        """İstatistik sekmesini oluştur"""
        frame = ctk.CTkFrame(self.tab_stats)
        frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Başlık
        ctk.CTkLabel(frame, text="📊 Balık Tutma İstatistikleri", 
                     font=ctk.CTkFont(size=20, weight="bold")).pack(pady=(10, 20))
        
        # Bu Oturum
        session_frame = ctk.CTkFrame(frame)
        session_frame.pack(fill="x", padx=20, pady=10)
        ctk.CTkLabel(session_frame, text="🎣 Bu Oturum", 
                     font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=10, pady=5)
        
        self.stat_session_fish = ctk.CTkLabel(session_frame, text="Tutulan Balık: 0", font=ctk.CTkFont(size=12))
        self.stat_session_fish.pack(anchor="w", padx=20)
        self.stat_session_time = ctk.CTkLabel(session_frame, text="Süre: 0dk", font=ctk.CTkFont(size=12))
        self.stat_session_time.pack(anchor="w", padx=20)
        self.stat_fish_per_hour = ctk.CTkLabel(session_frame, text="Hız: 0 balık/saat", font=ctk.CTkFont(size=12))
        self.stat_fish_per_hour.pack(anchor="w", padx=20)
        
        self.stat_session_revenue = ctk.CTkLabel(session_frame, text="💰 Kazanç: 0 m", font=ctk.CTkFont(size=12, weight="bold"), text_color="#FFD700")
        self.stat_session_revenue.pack(anchor="w", padx=20, pady=(0, 10))
        
        # Toplam
        total_frame = ctk.CTkFrame(frame)
        total_frame.pack(fill="x", padx=20, pady=10)
        ctk.CTkLabel(total_frame, text="📈 Toplam (Tüm Zamanlar)", 
                     font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=10, pady=5)
        
        self.stat_total_fish = ctk.CTkLabel(total_frame, text="Toplam Balık: 0", font=ctk.CTkFont(size=12))
        self.stat_total_fish.pack(anchor="w", padx=20)
        self.stat_total_sessions = ctk.CTkLabel(total_frame, text="Toplam Oturum: 0", font=ctk.CTkFont(size=12))
        self.stat_total_sessions.pack(anchor="w", padx=20)
        self.stat_best_session = ctk.CTkLabel(total_frame, text="En İyi Oturum: 0 balık", font=ctk.CTkFont(size=12))
        self.stat_best_session.pack(anchor="w", padx=20)
        self.stat_top_fish = ctk.CTkLabel(total_frame, text="🏆 En Çok: -", font=ctk.CTkFont(size=12))
        self.stat_top_fish.pack(anchor="w", padx=20, pady=(0, 10))
        
        # Saatlik Verimlilik
        hourly_frame = ctk.CTkFrame(frame)
        hourly_frame.pack(fill="x", padx=20, pady=10)
        ctk.CTkLabel(hourly_frame, text="🕒 Saatlik Verimlilik (Heatmap)", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=5)
        
        self.hourly_text = ctk.CTkTextbox(hourly_frame, height=100)
        self.hourly_text.pack(fill="x", padx=10, pady=5)
        self.hourly_text.insert("0.0", "Veri toplanıyor...")
        self.hourly_text.configure(state="disabled")

        # Yenile Butonu
        ctk.CTkButton(frame, text="🔄 Yenile", command=self.refresh_stats_display).pack(pady=20)
    
    def create_scheduler_tab(self):
        """Zamanlayıcı sekmesini oluştur"""
        frame = ctk.CTkFrame(self.tab_scheduler)
        frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Başlık
        ctk.CTkLabel(frame, text="⏰ Otomatik Zamanlayıcı", 
                     font=ctk.CTkFont(size=20, weight="bold")).pack(pady=(10, 5))
        ctk.CTkLabel(frame, text="Bot belirlenen saatlerde otomatik başlar ve durur.", 
                     text_color="gray").pack(pady=(0, 20))
        
        # Zaman Girişleri
        time_frame = ctk.CTkFrame(frame)
        time_frame.pack(fill="x", padx=20, pady=10)
        
        # Başlama Saati
        start_row = ctk.CTkFrame(time_frame, fg_color="transparent")
        start_row.pack(fill="x", pady=10)
        ctk.CTkLabel(start_row, text="▶️ Başlama Saati (HH:MM):", width=180).pack(side="left", padx=10)
        self.entry_start_time = ctk.CTkEntry(start_row, width=80, placeholder_text="02:00")
        self.entry_start_time.pack(side="left", padx=10)
        
        # Durma Saati
        stop_row = ctk.CTkFrame(time_frame, fg_color="transparent")
        stop_row.pack(fill="x", pady=10)
        ctk.CTkLabel(stop_row, text="⏹️ Durma Saati (HH:MM):", width=180).pack(side="left", padx=10)
        self.entry_stop_time = ctk.CTkEntry(stop_row, width=80, placeholder_text="06:00")
        self.entry_stop_time.pack(side="left", padx=10)
        
        # Durum
        self.scheduler_status = ctk.CTkLabel(frame, text="Durum: Devre Dışı", 
                                              font=ctk.CTkFont(size=12), text_color="orange")
        self.scheduler_status.pack(pady=10)
        
        # Butonlar
        btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
        btn_frame.pack(pady=20)
        
        self.btn_scheduler_enable = ctk.CTkButton(btn_frame, text="✅ Etkinleştir", 
                                                   fg_color="green", command=self.enable_scheduler)
        self.btn_scheduler_enable.pack(side="left", padx=10)
        
        ctk.CTkButton(btn_frame, text="❌ Devre Dışı", fg_color="gray", 
                      command=self.disable_scheduler).pack(side="left", padx=10)
        
        # Bilgi
        ctk.CTkLabel(frame, text="💡 İpucu: Gece geçişi için örn: Başla=23:00, Dur=06:00 yazın.", 
                     text_color="gray", font=ctk.CTkFont(size=11)).pack(pady=20)
    
    def refresh_stats_display(self):
        """İstatistik ekranını güncelle"""
        s = self.fish_stats.get_summary()
        self.stat_session_fish.configure(text=f"Tutulan Balık: {s['session_fish']}")
        self.stat_session_time.configure(text=f"Süre: {s['session_duration']}")
        self.stat_fish_per_hour.configure(text=f"Hız: {s['fish_per_hour']} balık/saat")
        self.stat_total_fish.configure(text=f"Toplam Balık: {s['total_fish']}")
        self.stat_total_sessions.configure(text=f"Toplam Oturum: {s['total_sessions']}")
        self.stat_best_session.configure(text=f"En İyi Oturum: {s['best_session']} balık")
        self.stat_top_fish.configure(text=f"🏆 En Çok: {s['top_fish']}")
        
        # --- Gelir Hesabı ---
        total_revenue = 0.0
        # s['session_breakdown'] -> {'zander': 5, 'worm': 100}
        try:
            for fish_key, count in s.get('session_breakdown', {}).items():
                price = self.inventory_manager.get_price(fish_key)
                if price > 0:
                    total_revenue += float(count) * float(price)
        except: pass
            
        # Formatlama (100m = 1 Won)
        if total_revenue >= 100:
            won = total_revenue / 100
            self.stat_session_revenue.configure(text=f"💰 Kazanç: {won:.2f} Won ({total_revenue:.1f}m)")
        else:
            self.stat_session_revenue.configure(text=f"💰 Kazanç: {total_revenue:.1f} m")

        # Saatlik veri
        try:
            hourly_data = self.fish_stats.get_hourly_data()
            if hourly_data:
                txt = "Saat  | Balık Sayısı\n" + "-"*30 + "\n"
                has_data = False
                for item in hourly_data:
                     if item["count"] > 0:
                         hour_str = f"{item['hour']:02d}:00 - {item['hour']+1:02d}:00"
                         txt += f"{hour_str} -> {item['count']} balık\n"
                         has_data = True
                
                if not has_data: txt = "Henüz yeterli veri yok."
                
                self.hourly_text.configure(state="normal")
                self.hourly_text.delete("0.0", "end")
                self.hourly_text.insert("0.0", txt)
                self.hourly_text.configure(state="disabled")
        except: pass
    
    def enable_scheduler(self):
        """Zamanlayıcıyı etkinleştir"""
        start = self.entry_start_time.get().strip()
        stop = self.entry_stop_time.get().strip()
        
        if not start or not stop:
            self.update_log("⚠️ Başlama ve durma saatlerini girin!")
            return
        
        self.scheduler.set_schedule(start, stop)
        if self.scheduler.enable():
            self.scheduler_status.configure(text=f"Durum: Aktif ({start} - {stop})", text_color="green")
            self.update_log(f"⏰ Zamanlayıcı aktif: {start} - {stop}")
    
    def disable_scheduler(self):
        """Zamanlayıcıyı devre dışı bırak"""
        self.scheduler.disable()
        self.scheduler_status.configure(text="Durum: Devre Dışı", text_color="orange")
    
    def start_bot_scheduled(self):
        """Zamanlayıcı tarafından bot başlatma"""
        if not self.bot.running:
            self.toggle_bot()
    
    def stop_bot_scheduled(self):
        """Zamanlayıcı tarafından bot durdurma"""
        if self.bot.running:
            self.toggle_bot()

    def create_assets_content(self):
        """Assettler sekmesini doldur"""
        frame = ctk.CTkScrollableFrame(self.tab_assets, width=600, height=450)
        frame.pack(fill="both", expand=True)

        ctk.CTkLabel(frame, text="📁 Görsel Yönetimi", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
        ctk.CTkLabel(frame, text="Çok sayfalı envanter için sayfa numaralarını buraya yükleyin.", text_color="gray").pack(pady=5)

        assets_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")
        if not os.path.exists(assets_dir): os.makedirs(assets_dir)

        # Listelenecek dosyalar
        targets = [
            ("page_1.png", "Envanter Sayfa 1 Butonu"),
            ("page_2.png", "Envanter Sayfa 2 Butonu"),
            ("page_3.png", "Envanter Sayfa 3 Butonu"),
            ("page_4.png", "Envanter Sayfa 4 Butonu"),
            ("bait.png", "Yem İkonu (Worm)"),
            ("bubble.png", "Balık Baloncuğu")
        ]

        for filename, desc in targets:
            sub = ctk.CTkFrame(frame)
            sub.pack(fill="x", padx=10, pady=5)
            
            ctk.CTkLabel(sub, text=desc, anchor="w", width=200).pack(side="left", padx=10)
            
            filepath = os.path.join(assets_dir, filename)
            status_text = "✅ Mevcut" if os.path.exists(filepath) else "❌ Yok"
            status_color = "green" if os.path.exists(filepath) else "red"
            
            lbl_status = ctk.CTkLabel(sub, text=status_text, text_color=status_color, width=80)
            lbl_status.pack(side="left", padx=10)
            
            btn_upload = ctk.CTkButton(sub, text="Yükle", width=80, command=lambda f=filename, l=lbl_status: self.upload_asset(f, l))
            btn_upload.pack(side="right", padx=10)

    def upload_asset(self, target_filename, label_widget):
        file_path = filedialog.askopenfilename(filetypes=[("Image Files", "*.png;*.jpg;*.jpeg")])
        if file_path:
            try:
                assets_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")
                target_path = os.path.join(assets_dir, target_filename)
                
                # Resmi kopyala ve gerekirse dönüştür
                img = Image.open(file_path)
                img.save(target_path) # PNG olarak kaydeder
                
                label_widget.configure(text="✅ Yüklendi", text_color="green")
                self.update_log(f"Dosya yüklendi: {target_filename}")
            except Exception as e:
                self.update_log(f"Yükleme hatası: {e}")

    def select_window_dialog(self):
        """Açık pencereleri listeler ve seçtirir"""
        try:
            import pygetwindow as gw
            titles = [t for t in gw.getAllTitles() if t.strip()]
            
            if not titles:
                self.update_log("⚠️ Pencere listesi boş! (İzin gerekebilir)")
                titles = ["Metin2", "Game"] # Fallback
            
            dialog = ctk.CTkInputDialog(text="Hedef Pencere Başlığını Yazın (Tam Adı):", title="Pencere Seç")
            # Not: CTkInputDialog basit bir input box'dır. Combobox'lı pop-up yapmak daha uzun sürer, şimdilik manuel giriş veya basit seçim yeterli.
            # Kullanıcı kolaylığı için en yaygın olanı titles'dan seçtirebilirdik ama CTk'da hazır Listbox Dialog yok.
            # Basit Input Dialog ile başlayalım, kullanıcı pencere adını yazsın.
            
            user_input = dialog.get_input()
            
            if user_input:
                try:
                    wins = gw.getWindowsWithTitle(user_input)
                    if wins:
                        win = wins[0]
                        # Pencereyi bulduk
                        monitor = {
                            "top": win.top + 30, # Title bar payı
                            "left": win.left,
                            "width": win.width,
                            "height": win.height - 30
                        }
                        
                        # Bot monitorünü güncelle
                        if self.bot:
                            self.bot.monitor = monitor
                        
                        self.monitor_info.configure(text=f"Seçili: {win.title}\n{monitor['width']}x{monitor['height']}")
                        self.update_log(f"✅ Pencere seçildi: {win.title}")
                        
                        # Config'e kaydet
                        self.inventory_manager.config.config["bot_settings"]["scan_area"] = monitor
                        self.inventory_manager.config.save_config()
                    else:
                        self.update_log("❌ Pencere bulunamadı!")
                except Exception as e:
                    self.update_log(f"Hata: {e}")

        except ImportError:
            self.update_log("❌ pygetwindow modülü eksik!")
        except Exception as e:
            self.update_log(f"Genel Hata: {e}")

    def save_advanced_settings(self):
        try:
            # Bot Settings - Entry'lerden değer al
            try:
                c_min = round(float(self.entry_cast_min.get()), 2)
                c_max = round(float(self.entry_cast_max.get()), 2)
            except ValueError:
                c_min, c_max = 1.5, 3.0  # Varsayılan
            
            # Mantık hatası önlemi (Min > Max ise düzelt)
            if c_min > c_max: c_min, c_max = c_max, c_min
            
            try:
                to_val = round(float(self.entry_timeout.get()), 1)
            except ValueError:
                to_val = 10.0
            gm_val = self.var_gm.get()
            bait_key = self.combo_bait_key.get()
            
            self.inventory_manager.config.set_bot_setting("cast_delay_min", c_min)
            self.inventory_manager.config.set_bot_setting("cast_delay_max", c_max)
            self.inventory_manager.config.set_bot_setting("wait_timeout", to_val)
            self.inventory_manager.config.set_bot_setting("gm_detect", gm_val)
            self.inventory_manager.config.set_bot_setting("bait_key", bait_key)
            
            # Stop Conditions
            try:
                m_time = int(self.entry_max_min.get())
            except: m_time = 0
            
            try:
                m_fish = int(self.entry_max_fish.get())
            except: m_fish = 0
            
            # Stop conditions için set metodu yok, manuel erişelim
            self.inventory_manager.config.config["stop_conditions"] = {
                "max_time_min": m_time,
                "max_fish": m_fish
            }
            # Telegram Ayarları
            tg_token = self.entry_tg_token.get().strip()
            tg_chat = self.entry_tg_chat.get().strip()
            
            self.inventory_manager.config.config["telegram"] = {
                "token": tg_token,
                "chat_id": tg_chat,
                "notify_on_stop": bool(self.check_tg_stop.get()),
                "notify_on_gm": bool(self.check_tg_gm.get()),
                "notify_on_catch": bool(self.check_tg_catch.get())
            }

            self.inventory_manager.config.save_config()
            
            self.update_log(f"✅ Ayarlar Güncellendi!\nYem Tuşu: {bait_key} | Cast: {c_min}-{c_max}s\nStop: {m_time}dk / {m_fish} balık")
            
            # Bot çalışıyorsa canlı güncelle
            if self.bot and self.bot.is_running:
                self.bot.reload_config()
                
        except Exception as e:
            self.update_log(f"❌ Hata: {str(e)}")
        
    def load_fish_list(self):
        """Balık listesini ve ayarları arayüze döker"""
        # Temizle
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()

        # Üst Bar: Tara Butonu
        top_frame = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        top_frame.pack(fill="x", padx=5, pady=5)
        
        ctk.CTkLabel(top_frame, text="Balık Eylem Listesi", font=("Arial", 16, "bold")).pack(side="left")
        ctk.CTkButton(top_frame, text="🔍 Bilinmeyenleri Tara & Öğren", command=self.open_unknown_scanner, width=180, fg_color="#E91E63", hover_color="#C2185B").pack(side="right")
        
        fish_data = self.inventory_manager.db.FISH_DATA
        
        # İkon Yolu
        # Bir üst klasördeki assets/fish_icons'a gitmeli
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        assets_dir = os.path.join(base_dir, "assets", "fish_icons")
        
        row = 0
        for key, data in fish_data.items():
            # Satır Konteyner
            frame = ctk.CTkFrame(self.scroll_frame)
            frame.pack(fill="x", padx=5, pady=5)
            
            # İkon
            # İkon (Tıklanabilir Buton)
            icon_path = os.path.join(assets_dir, data['icon'])
            icon_image = None
            
            if os.path.exists(icon_path):
                try:
                    pil_img = Image.open(icon_path)
                    icon_image = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(32, 32))
                except: pass
            
            # İkonu Buton Olarak Ekle (Resim Seçmek İçin)
            btn_text = "" if icon_image else "[+]"
            icon_btn = ctk.CTkButton(frame, text=btn_text, image=icon_image, width=40, height=40,
                                     fg_color="transparent", border_width=1, border_color="gray",
                                     command=lambda k=key: self.upload_fish_icon(k))
            icon_btn.pack(side="left", padx=10)

            # İsim ve Açıklama
            info_text = f"{data['name']}\n({data['desc']})"
            ctk.CTkLabel(frame, text=info_text, anchor="w", width=200).pack(side="left", padx=10)
            
            # Seçenekler (Dropdown)
            current_action = self.inventory_manager.get_action(key)
            
            # Seçenekler Listesi (Tr)
            options = ["Sakla (Keep)", "Yere At (Drop)", "Aç (Open)", "Öldür (Kill)"]
            
            option_menu = ctk.CTkOptionMenu(frame, values=options,
                                            command=lambda choice, k=key: self.change_fish_pref(k, choice))
            
            # Varsayılanı Seç
            map_val = {"keep": "Sakla (Keep)", "drop": "Yere At (Drop)", "open": "Aç (Open)", "kill": "Öldür (Kill)"}
            
            # Kayıtlı ayarı ui metnine çevir
            ui_text = map_val.get(current_action, "Sakla (Keep)")
            option_menu.set(ui_text)
            option_menu.pack(side="right", padx=10)
            
            # Fiyat Girişi (Yanına 'm' yazısı ile)
            price_val = self.inventory_manager.get_price(key)
            price_var = ctk.StringVar(value=str(price_val) if price_val > 0 else "")
            
            price_entry = ctk.CTkEntry(frame, width=50, placeholder_text="Fiyat", textvariable=price_var)
            price_entry.pack(side="right", padx=5)
            
            # Kaydetme eventi
            def save_p(event, k=key, v=price_var):
                try:
                    val = v.get().replace(",", ".").strip()
                    if not val: val = "0"
                    self.inventory_manager.set_price(k, float(val))
                    # self.update_log(f"💰 {k} fiyatı güncellendi: {val}m") # Çok spam yaratmasın
                    self.update_stats() # Anlık güncelle
                except: pass

            price_entry.bind('<Return>', save_p)
            price_entry.bind('<FocusOut>', save_p)

            ctk.CTkLabel(frame, text="m", text_color="gray").pack(side="right", padx=(0,5))

            # Ses Çal Checkbox
            sound_var = ctk.BooleanVar(value=key in self.sound_alert.alert_fish)
            sound_cb = ctk.CTkCheckBox(frame, text="🔔", width=40, variable=sound_var,
                                        command=lambda k=key, v=sound_var: self.toggle_fish_sound(k, v))
            sound_cb.pack(side="right", padx=5)
            
            row += 1
    
    def toggle_fish_sound(self, fish_key, var):
        """Balık için ses uyarısını aç/kapa"""
        if var.get():
            self.sound_alert.add_alert_fish(fish_key)
            self.update_log(f"🔔 {fish_key} için ses uyarısı açıldı")
        else:
            self.sound_alert.remove_alert_fish(fish_key)
            self.update_log(f"🔕 {fish_key} için ses uyarısı kapatıldı")

    def open_unknown_scanner(self):
        """Bilinmeyen eşyaları tarar ve popup açar"""
        if not self.bot or not self.bot.monitor:
             self.update_log("⚠️ Önce 'Pencere Seç' işlemi yapmalısınız!")
             return

        self.update_log("🔍 Envanter taranıyor...")
        
        # Ekran görüntüsü al
        import mss
        import cv2
        import numpy as np
        
        with mss.mss() as sct:
            # Envanter bölgesi (Config'den veya varsayılan)
            # Şimdilik monitor'ün sağ tarafını alalım (Tahmini)
            # Daha iyisi: Kullanıcı monitörünü tam kullanalım.
            # InventoryManager.scan_unknown_items bizden cv2 image bekliyor.
            
            monitor = self.bot.monitor
            img = np.array(sct.grab(monitor))
            # RGB dönüşümü (mss BGRA verir)
            img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
            
            # Envanter bölgesini kırp (Tahmini: Sağ alt çeyrek)
            # Kullanıcıya "Envanter Alanı" seçtirmek en doğrusu ama şimdilik "Auto Inventory Detect" yapalım.
            # Veya tüm ekranı gönderelim, scan algorithm slot bulsun.
            
            # scan_unknown_items çağır
            # Not: Bu işlem biraz sürebilir, UI donabilir. Thread'e almak lazım ama basitlik için direkt yapalım.
            unknowns = self.inventory_manager.scan_unknown_items(img, (monitor["left"], monitor["top"]))
            
            if not unknowns:
                self.update_log("✅ Yeni bilinmeyen eşya bulunamadı.")
                return
                
            self.update_log(f"⚠️ {len(unknowns)} adet bilinmeyen eşya bulundu!")
            self.show_learning_dialog(unknowns)

    def show_learning_dialog(self, unknown_files):
        """Eşya öğretme penceresi"""
        dialog = ctk.CTkToplevel(self)
        dialog.title("Eşya Öğretici")
        dialog.geometry("400x500")
        
        scroll = ctk.CTkScrollableFrame(dialog)
        scroll.pack(fill="both", expand=True, padx=10, pady=10)
        
        fish_keys = list(self.inventory_manager.db.FISH_DATA.keys())
        
        for fpath in unknown_files:
            row = ctk.CTkFrame(scroll)
            row.pack(fill="x", pady=5)
            
            # Resim
            try:
                pil_img = Image.open(fpath)
                ctk_img = ctk.CTkImage(pil_img, size=(32, 32))
                ctk.CTkLabel(row, image=ctk_img, text="").pack(side="left", padx=5)
            except: pass
            
            # Combobox
            combo = ctk.CTkComboBox(row, values=fish_keys, width=150)
            combo.set("Seçiniz...")
            combo.pack(side="left", padx=5)
            
    def upload_fish_icon(self, key):
        """Kullanıcının bilgisayarından ikon seçmesini sağlar"""
        from tkinter import filedialog
        
        file_path = filedialog.askopenfilename(
            title=f"{key} için İkon Seç",
            filetypes=[("Resim Dosyaları", "*.png;*.jpg;*.jpeg;*.bmp")]
        )
        
        if file_path:
            # Öğrenme fonksiyonunu kullanarak taşı ve kaydet
            if self.inventory_manager.learn_item(file_path, key):
                self.update_log(f"✅ İkon güncellendi: {key}")
                self.load_fish_list() # Listeyi yenile
            else:
                self.update_log("❌ İkon yüklenirken hata oluştu.")
            
            # Kaydet Butonu
            def save_item(fp=fpath, cb=combo, r=row):
                key = cb.get()
                if key == "Seçiniz...": return
                
                if self.inventory_manager.learn_item(fp, key):
                    r.destroy() # Satırı sil
                    self.update_log(f"✅ Öğrenildi: {key}")
                    # Ana listeyi yenile (ikonu göstermek için)
                    self.load_fish_list()
            
            ctk.CTkButton(row, text="Kaydet", command=save_item, width=60).pack(side="right", padx=5)

    def change_fish_pref(self, key, choice):
        # Arayüzdeki "Sakla (Keep)" -> "keep" dönüşümü
        inv_map = {"Sakla (Keep)": "keep", "Yere At (Drop)": "drop", "Aç (Open)": "open", "Öldür (Kill)": "kill"}
        action_code = inv_map.get(choice, "keep")
        
        self.inventory_manager.set_action(key, action_code)
        # print(f"Updated preference for {key}: {action_code}")

    def update_log(self, message):
        """Thread güvenli log güncelleme"""
        # Tkinter'da GUI güncellemeleri main thread'de olmalı, after ile kuyruğa atıyoruz
        self.after(0, lambda: self._append_log(message))
        
    def _append_log(self, message):
        self.log_textbox.insert("end", f"{message}\n")
        self.log_textbox.see("end")

    def toggle_bot(self):
        if not self.bot.is_running:
            self.bot.start()
            self.start_button.configure(text="DURDUR", fg_color="red", hover_color="darkred")
            self.update_log(">>> BOT BAŞLATILDI <<<")
            # İstatistik oturumu başlat
            self.fish_stats.start_session()
        else:
            self.bot.stop()
            self.start_button.configure(text="BAŞLAT", fg_color="green", hover_color="darkgreen")
            self.update_log(">>> BOT DURDURULDU <<<")
            # İstatistik oturumu bitir
            self.fish_stats.end_session()
            self.refresh_stats_display()
            
            # Oturum sonu raporu gönder (Telegram)
            try:
                summary = self.fish_stats.get_summary()
                self.report_manager.send_session_report(summary)
            except Exception as e:
                self.update_log(f"⚠️ Rapor gönderilemedi: {e}")
    
    def emergency_stop(self):
        """Acil durdurma (F10) - Her şeyi durdur"""
        self.update_log("🚨 ACİL DURDURMA!")
        if self.bot.is_running:
            self.bot.stop()
            self.start_button.configure(text="BAŞLAT", fg_color="green", hover_color="darkgreen")
            self.fish_stats.end_session()
            # Telegram bildir
            if hasattr(self.bot, 'telegram') and self.bot.telegram and self.bot.telegram.enabled:
                self.bot.telegram.send_message("🚨 ACİL DURDURMA! Bot manuel olarak durduruldu.")
    
    def take_screenshot(self):
        """Ekran görüntüsü al (F11)"""
        try:
            import mss
            from PIL import Image as PILImage
            
            with mss.mss() as sct:
                monitor = self.bot.monitor if self.bot.monitor else sct.monitors[1]
                screenshot = sct.grab(monitor)
                
                # Kaydet
                filename = f"screenshot_{int(time.time())}.png"
                filepath = os.path.join("screenshots", filename)
                os.makedirs("screenshots", exist_ok=True)
                
                img = PILImage.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
                img.save(filepath)
                
                self.update_log(f"📸 Ekran görüntüsü kaydedildi: {filepath}")
                
                # Telegram'a da gönder
                if hasattr(self.bot, 'telegram') and self.bot.telegram and self.bot.telegram.enabled:
                    self.bot.telegram.send_photo(filepath, "📸 Hotkey ile alınan ekran görüntüsü")
        except Exception as e:
            self.update_log(f"📸 Ekran görüntüsü hatası: {e}")
    
    def pause_5min(self):
        """5 dakika mola (F12)"""
        if not self.bot.is_running:
            self.update_log("⏸️ Bot zaten durmuş!")
            return
        
        self.update_log("⏸️ 5 dakika mola veriliyor...")
        self.bot.stop()
        self.start_button.configure(text="MOLA (5dk)", fg_color="orange")
        
        if hasattr(self.bot, 'telegram') and self.bot.telegram and self.bot.telegram.enabled:
            self.bot.telegram.send_message("⏸️ Bot 5 dakika mola veriyor...")
        
        # 5 dakika sonra devam et
        def resume():
            time.sleep(300)  # 5 dakika
            self.update_log("▶️ Mola bitti, devam ediliyor...")
            self.toggle_bot()
        
        threading.Thread(target=resume, daemon=True).start()
    
    def apply_profile(self, profile_name: str):
        """Profil ayarlarını uygula"""
        # Profil ID'sini bul
        profile_map = {
            "🎯 Normal": "normal",
            "⚡ Turbo": "turbo",
            "🥷 Gizli": "stealth",
            "🌙 Gece": "night",
            "💤 AFK": "afk"
        }
        
        profile_id = profile_map.get(profile_name, "normal")
        profile = self.profile_manager.get_profile(profile_id)
        
        if profile:
            settings = profile.get("settings", {})
            
            # GUI slider'larını güncelle
            if "cast_delay_min" in settings:
                self.entry_cast_min.delete(0, "end")
                self.entry_cast_min.insert(0, str(settings["cast_delay_min"]))
            
            if "cast_delay_max" in settings:
                self.entry_cast_max.delete(0, "end")
                self.entry_cast_max.insert(0, str(settings["cast_delay_max"]))
            
            if "wait_timeout" in settings:
                self.entry_wait_timeout.delete(0, "end")
                self.entry_wait_timeout.insert(0, str(settings["wait_timeout"]))
            
            # Profil açıklamasını güncelle
            self.profile_desc_label.configure(text=profile.get("description", ""))
            
            self.update_log(f"⚡ Profil uygulandı: {profile_name}")
            self.profile_manager.current_profile = profile_id
    
    def update_hotkey_status(self):
        """Hotkey durumunu güncelle"""
        if hasattr(self, 'hotkey_status_label'):
            if self.hotkey_manager.enabled:
                self.hotkey_status_label.configure(text="✅ Aktif", text_color="lightgreen")
            elif self.hotkey_manager.is_available():
                self.hotkey_status_label.configure(text="❌ Devre Dışı", text_color="red")
            else:
                self.hotkey_status_label.configure(text="⚠️ pynput yok", text_color="orange")

    def calibrate_area(self):
        """Kullanıcının alan seçmesi için şeffaf bir pencere açar"""
        self.update_log(">>> Kalibrasyon Modu Başlatıldı <<<")
        self.update_log("Lütfen açılan pencerede 'Oyun Alanını' seçin...")
        
        # Ana pencereyi gizle (daha temiz seçim için)
        self.withdraw()
        
        # Overlay Penceresi
        self.overlay = ctk.CTkToplevel()
        # Tam Ekran ve Şeffaf (Sisteme göre değişir)
        # Windows'ta attributes('-alpha') çalışır ama tam şeffaflık zor olabilir.
        # Alternatif: Yarı saydam beyaz bir pencere.
        
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        self.overlay.geometry(f"{screen_width}x{screen_height}+0+0")
        self.overlay.overrideredirect(True) # Çerçevesiz
        self.overlay.attributes("-topmost", True)
        self.overlay.attributes("-alpha", 0.3) # %30 Görünürlük
        self.overlay.configure(fg_color="white")
        
        # Mouse olayları
        self.start_x = 0
        self.start_y = 0
        self.cur_rect = None
        self.canvas = ctk.CTkCanvas(self.overlay, width=screen_width, height=screen_height, cursor="cross", bg="grey11", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        # Canvas şeffaflığı tkinter'da zordur, o yüzden basit çizgi kullanacağız.
        
        self.canvas.bind("<ButtonPress-1>", self.on_calib_press)
        self.canvas.bind("<B1-Motion>", self.on_calib_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_calib_release)
        
        # İptal için ESC
        self.overlay.bind("<Escape>", lambda e: self.cancel_calibration())

    def on_calib_press(self, event):
        self.start_x = event.x
        self.start_y = event.y
        if self.cur_rect:
            self.canvas.delete(self.cur_rect)
        self.cur_rect = self.canvas.create_rectangle(self.start_x, self.start_y, self.start_x, self.start_y, outline="red", width=3)

    def on_calib_drag(self, event):
        cur_x, cur_y = (event.x, event.y)
        self.canvas.coords(self.cur_rect, self.start_x, self.start_y, cur_x, cur_y)

    def on_calib_release(self, event):
        end_x, end_y = (event.x, event.y)
        
        # Koordinatları normalize et (Sol-Üst, Sağ-Alt)
        x1 = min(self.start_x, end_x)
        y1 = min(self.start_y, end_y)
        x2 = max(self.start_x, end_x)
        y2 = max(self.start_y, end_y)
        
        width = x2 - x1
        height = y2 - y1
        
        if width > 50 and height > 50:
            # Seçim Başarılı
            self.overlay.destroy()
            self.deiconify() # Ana pencereyi geri getir
            
            # Konfigürasyonu Güncelle (Şimdilik sadece Oyun Alanı)
            # İleride "Şimdi Envanteri Seç" diyerek adım adım yaptırılabilir.
            new_monitor = {"top": y1, "left": x1, "width": width, "height": height}
            
            # Botun canlı configini güncelle
            if self.bot:
                self.bot.monitor = new_monitor
                self.inventory_manager.config.config["bot_settings"]["scan_area"] = new_monitor
                self.inventory_manager.config.save_config()
            
            self.update_log(f"✅ Alan Seçildi: {x1},{y1} ({width}x{height})")
            self.update_log("NOT: Envanter alanı bu seçimin sağ yarısı olarak varsayılacaktır.")
        else:
            self.update_log("⚠️ Seçim çok küçük! Lütfen tekrar deneyin.")
            self.cancel_calibration()

    def cancel_calibration(self):
        if hasattr(self, 'overlay') and self.overlay:
            self.overlay.destroy()
        self.deiconify()
        self.update_log("Kalibrasyon iptal edildi.")

    def switch_account(self, account_name: str):
        """Hesaplar arasında geçiş yap"""
        # Hesap adından session ID bul
        for sid, session in self.account_manager.sessions.items():
            if session.name == account_name:
                self.account_manager.set_active_session(sid)
                self.current_account_id = sid
                self.bot = session.bot_instance
                
                # UI güncelle
                if session.is_active:
                    self.start_button.configure(text="DURDUR", fg_color="red")
                else:
                    self.start_button.configure(text="BAŞLAT", fg_color="green")
                
                self.update_log(f"🔄 Aktif hesap: {account_name}")
                break
    
    def add_account_dialog(self):
        """Yeni hesap ekleme diyalogu"""
        # Basit isim girişi
        name = simpledialog.askstring("Yeni Hesap", "Hesap adını girin:", parent=self)
        
        if not name:
            return
        
        # Yeni BotCore instance oluştur
        new_bot = BotCore(update_log_callback=self.update_log)
        new_bot.fish_stats = self.fish_stats
        new_bot.sound_alert = self.sound_alert
        
        # Session oluştur
        session_id = self.account_manager.create_session(
            name=name,
            bot_instance=new_bot,
            monitor={"top": 0, "left": 0, "width": 800, "height": 600}
        )
        
        # Dropdown'u güncelle
        self.account_list.append(name)
        self.account_selector.configure(values=self.account_list)
        self.account_selector.set(name)
        
        # Yeni hesaba geç
        self.switch_account(name)
        
        self.update_log(f"➕ Yeni hesap eklendi: {name}")
        self.update_log("⚠️ Yeni hesap için 'Pencere Seç' yapın!")
    
    def remove_current_account(self):
        """Aktif hesabı sil (varsayılan silinemez)"""
        session = self.account_manager.get_active_session()
        if not session:
            return
        
        if session.name == "Varsayılan":
            self.update_log("⚠️ Varsayılan hesap silinemez!")
            return
        
        # Hesabı kaldır
        self.account_manager.remove_session(self.current_account_id)
        self.account_list.remove(session.name)
        self.account_selector.configure(values=self.account_list)
        
        # Varsayılana dön
        self.account_selector.set("Varsayılan")
        self.switch_account("Varsayılan")
        self.update_log(f"🗑️ Hesap silindi: {session.name}")

    def toggle_preview(self):
        """Canlı önizlemeyi başlat/durdur"""
        if not self.preview_active:
            if not self.bot or not self.bot.monitor:
                self.update_log("⚠️ Önce 'Pencere Seç' ile alan belirleyin!")
                return
            
            self.preview_active = True
            self.btn_preview_toggle.configure(text="⏹️ Durdur", fg_color="#F44336")
            self.preview_last_time = time.time()
            self.preview_frame_count = 0
            self.update_preview()
            self.update_log("📷 Canlı önizleme başlatıldı")
        else:
            self.preview_active = False
            self.btn_preview_toggle.configure(text="▶️ Başlat", fg_color="#2196F3")
            self.preview_label.configure(image=None, text="[Önizleme durduruldu]")
            self.preview_fps_label.configure(text="FPS: -")
            self.update_log("📷 Canlı önizleme durduruldu")
    
    def update_preview(self):
        """Ekran görüntüsü al ve önizlemeye göster"""
        if not self.preview_active:
            return
        
        try:
            import mss
            from PIL import Image as PILImage
            
            with mss.mss() as sct:
                monitor = self.bot.monitor
                screenshot = sct.grab(monitor)
                
                # PIL Image'e çevir
                img = PILImage.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
                
                # Önizleme boyutuna küçült (performans için)
                preview_size = (400, 220)
                img = img.resize(preview_size, PILImage.Resampling.LANCZOS)
                
                # CTkImage'e çevir
                ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=preview_size)
                
                # Label'a yerleştir
                self.preview_label.configure(image=ctk_img, text="")
                self.preview_label.image = ctk_img  # Referans tut
                
                # FPS Hesapla
                self.preview_frame_count += 1
                now = time.time()
                if now - self.preview_last_time >= 1.0:
                    fps = self.preview_frame_count / (now - self.preview_last_time)
                    self.preview_fps_label.configure(text=f"FPS: {fps:.1f}")
                    self.preview_frame_count = 0
                    self.preview_last_time = now
        
        except Exception as e:
            self.preview_label.configure(text=f"Hata: {e}")
        
        # Bir sonraki frame (yaklaşık 10 FPS için 100ms)
        if self.preview_active:
            self.after(100, self.update_preview)

    def update_stats(self):
        """Her 1 saniyede bir istatistikleri yenile"""
        if self.bot:
            caught = self.bot.stats['caught']
            missed = self.bot.stats['missed']
            casts = self.bot.stats['casts']
            
            # Süre Hesabı
            duration_str = "00:00"
            if self.bot.is_running and self.bot.start_timestamp > 0:
                elapsed = int(time.time() - self.bot.start_timestamp)
                mins, secs = divmod(elapsed, 60)
                hours, mins = divmod(mins, 60)
                duration_str = f"{hours:02}:{mins:02}:{secs:02}"
            
            txt = f"🎣 Balık İstatistikleri\n\n✅ Yakalanan: {caught}\n❌ Kaçırılan: {missed}\n🏹 Atış Sayısı: {casts}\n\n⏱ Süre: {duration_str}"
            self.stats_label.configure(text=txt)
        
        self.after(1000, self.update_stats)

    def on_closing(self):
        if self.bot:
            self.bot.stop()
        self.destroy()

    def load_asset_manager(self):
        """Görseller sekmesini doldurur"""
        self.asset_scroll = ctk.CTkScrollableFrame(self.tab_assets, width=600, height=450)
        self.asset_scroll.pack(fill="both", expand=True, padx=5, pady=5)
        
        ctk.CTkLabel(self.asset_scroll, text="Oyun İçi Görseller (Asset Manager)", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
        ctk.CTkLabel(self.asset_scroll, text="Buradan botun kullandığı referans resimleri yükleyebilirsiniz.", text_color="gray").pack()
        
        # Kritik Sistem Dosyaları
        ctk.CTkLabel(self.asset_scroll, text="--- Sistem ---", font=ctk.CTkFont(weight="bold")).pack(pady=5)
        self.add_asset_row("Balık Balonu (Space İkonu)", "bubble.png", critical=True)
        self.add_asset_row("Solucan / Yem İkonu", "worm.png")
        
        # Envanter Sayfaları (Opsiyonel)
        ctk.CTkLabel(self.asset_scroll, text="--- Envanter Sayfaları (Çoklu Sayfa) ---", font=ctk.CTkFont(weight="bold")).pack(pady=5)
        self.add_asset_row("Sayfa 1 Butonu (I)", "page_1.png")
        self.add_asset_row("Sayfa 2 Butonu (II)", "page_2.png")
        self.add_asset_row("Sayfa 3 Butonu (III)", "page_3.png")
        self.add_asset_row("Sayfa 4 Butonu (IV)", "page_4.png")
        
        # Balıklar
        ctk.CTkLabel(self.asset_scroll, text="--- Balıklar ---", font=ctk.CTkFont(weight="bold")).pack(pady=5)
        for key, data in self.inventory_manager.db.FISH_DATA.items():
            db_icon_name = data.get("icon", f"{key}.png")
            self.add_asset_row(f"{data['name']} ({db_icon_name})", db_icon_name)

    def add_asset_row(self, label_text, filename, critical=False):
        row = ctk.CTkFrame(self.asset_scroll)
        row.pack(fill="x", padx=5, pady=2)
        
        # Etiket
        lbl = ctk.CTkLabel(row, text=label_text, width=250, anchor="w")
        if critical: lbl.configure(text_color="orange")
        lbl.pack(side="left", padx=10)
        
        # Önizleme (Varsa)
        assets_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")
        filepath = os.path.join(assets_dir, filename)
        
        preview_lbl = ctk.CTkLabel(row, text="[Yok]", width=40, font=ctk.CTkFont(size=10))
        
        if os.path.exists(filepath):
            try:
                pil_img = Image.open(filepath)
                ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(32, 32))
                preview_lbl = ctk.CTkLabel(row, text="", image=ctk_img)
            except:
                preview_lbl.configure(text="[Hata]")
                
        preview_lbl.pack(side="left", padx=10)
        
        # Yükle Butonu
        btn = ctk.CTkButton(row, text="Yükle / Değiştir", width=100, 
                            command=lambda: self.upload_asset(filename, preview_lbl))
        btn.pack(side="right", padx=10)
        
    def upload_asset(self, target_filename, preview_label):
        file_path = filedialog.askopenfilename(
            title=f"{target_filename} için görsel seç",
            filetypes=[("Image Files", "*.png;*.jpg;*.jpeg;*.bmp")]
        )
        
        if file_path:
            try:
                assets_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")
                if not os.path.exists(assets_dir):
                    os.makedirs(assets_dir)
                    
                target_path = os.path.join(assets_dir, target_filename)
                
                # Resmi kopyala ve dönüştür (PNG'ye çevirmek en garantisi)
                img = Image.open(file_path)
                img.save(target_path)
                
                # UI Güncelle
                ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(32, 32))
                preview_label.configure(text="", image=ctk_img)
                
                self.update_log(f"Görsel güncellendi: {target_filename}")
                
                # Botun template'ini canlı yenile (Sadece bubble için gerekli)
                if "bubble" in target_filename and self.bot:
                    self.bot.reload_config() # Bu metot template'i de yeniden okuyor
                
            except Exception as e:
                self.update_log(f"Görsel yükleme hatası: {e}")

if __name__ == "__main__":
    app = App()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()
