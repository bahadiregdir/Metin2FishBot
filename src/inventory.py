
import os
import platform

# Windows'ta değilsek pydirectinput çalışmaz, mock (sahte) obje kullanalım
if platform.system() == "Windows":
    import pydirectinput
else:
    class MockInput:
        def click(self, *args, **kwargs): pass
        def moveTo(self, *args, **kwargs): pass
        def rightClick(self, *args, **kwargs): pass
        def mouseDown(self, *args, **kwargs): pass
        def mouseUp(self, *args, **kwargs): pass
    pydirectinput = MockInput()

class FishDatabase:
    """Metin2 Balık Veritabanı ve Özellikleri"""
    
    # Mock Database (Gerçekte bu veriler bir dosyadan veya DB'den gelir)
    # Metin2 Güncel Balık ve Eşya Listesi (2024 Jigsaw Dahil)
    FISH_DATA = {
        # --- Düşük Seviye / Yaygın ---
        "zander": {"name": "Sudak (Zander)", "icon": "zander.png", "desc": "Lvl 1 | Izgara: HP +180"},
        "minnow": {"name": "Minik Balık", "icon": "minnow.png", "desc": "Lvl 1 | Yem Olarak Kullanılır"},
        "mandarin": {"name": "Mandarin", "icon": "mandarin_fish.png", "desc": "Lvl 5 | Izgara: SP +180"},
        "large_goldfish": {"name": "Büyük Japon Balığı", "icon": "goldfish.png", "desc": "Lvl 10"}, # Dosya adı goldfish.png
        "carp": {"name": "Sazan (Carp)", "icon": "carp.png", "desc": "Lvl 20 | Izgara: Hız +20"},
        
        # --- Orta Seviye ---
        "salmon": {"name": "Somon (Salmon)", "icon": "salmon.png", "desc": "Lvl 30 | Izgara: SP +350"},
        "cod": {"name": "Morina (Cod)", "icon": "smelt.png", "desc": "Lvl 30 | Izgara: SP Yüklemesi"}, # Cod yoksa Smelt kullan (geçici)
        "catfish": {"name": "Yayın Balığı (Catfish)", "icon": "catfish.png", "desc": "Lvl 40 | Izgara: Anında MP"},
        "tench": {"name": "Kadife (Tench)", "icon": "tenchi.png", "desc": "Lvl 40 | Izgara: HP Yenileme"},
        "trout": {"name": "Alabalık (Trout)", "icon": "brook_trout.png", "desc": "Lvl 50 | Izgara: Anında HP"},
        
         # --- Yeni Eklenenler (Dosya Bazlı) ---
        "tekir": {"name": "Tekir Balığı", "icon": "rudd.png", "desc": "HP Yeniler (Rudd)"},
        "buyuk_sudak": {"name": "Büyük Sudak", "icon": "large_zander.png", "desc": "HP +350"},
        "lufer": {"name": "Lüfer", "icon": "skygazer.png", "desc": "HP +500 (Skygazer)"},
        "ringa": {"name": "Ringa", "icon": "shiri.png", "desc": "SP +180 (Shiri)"}, # Tahmini
        "nehir_alabaligi": {"name": "Nehir Alabalığı", "icon": "river_trout.png", "desc": "SP +230"},
        "dere_alabaligi": {"name": "Dere Alabalığı", "icon": "brook_trout.png", "desc": "HP +600"},
        "ot_sazani": {"name": "Ot Sazanı", "icon": "grass_carp.png", "desc": "Saldırı Hızı +20"},
        "zargana": {"name": "Zargana", "icon": "lotus_fish.png", "desc": "Güç +10 (Lotus?)"}, # Görsel yoksa en yakını
        "hamsi": {"name": "Hamsi", "icon": "minnow.png", "desc": "Çeviklik +10 (Minnow Benzeri)"}, 
        "aynali_sazan": {"name": "Aynalı Sazan", "icon": "mirror_carp.png", "desc": "HP +1000 (Nadir)"},
        "palamut": {"name": "Palamut", "icon": "sweetfish.png", "desc": "Canavarlara Karşı Güç"},
        "yilan_basi": {"name": "Yılan Başı", "icon": "snakehead.png", "desc": "Toprak Direnci"},
        "king_crab": {"name": "Kral Yengeci", "icon": "red_king_crab.png", "desc": "Karanlık Direnci"},
        "yabbie": {"name": "Kerevit (Yabbie)", "icon": "yabby.png", "desc": "Yengeç | Pasta Malzemesi"},

        # --- Yüksek Seviye / Nadir ---
        "eel": {"name": "Yılan Balığı (Eel)", "icon": "eel.png", "desc": "Nadirdir | Izgara: STR +10"},
        "rainbow_trout": {"name": "Gökkuşağı Alabalığı", "icon": "rainbow_trout.png", "desc": "Izgara: SP +600"},
        "perch": {"name": "Levrek (Perch)", "icon": "perch.png", "desc": "Lvl 70 | Negatif Etkileri Siler"},
        "golden_tuna": {"name": "Altın Ton (Golden Tuna)", "icon": "golden_tuna.png", "desc": "✨ EFSANEVİ | Çok Değerli!"},
        "crab": {"name": "Yengeç (Crab)", "icon": "yabby.png", "desc": "Değerli"},
        
        # --- Özel & Etkinlik ---
        "jigsaw_chest": {"name": "Balık Yapboz Sandığı", "icon": "goldfish.png", "desc": "Jigsaw Etkinlik Ödülü"},
        "clam": {"name": "İstiridye (Clam)", "icon": "lotus_fish.png", "desc": "İnci Çıkar | Çok Değerli"},
        # --- Çöp / Diğer ---
        "hair_dye": {"name": "Saç Boyası", "icon": "minnow.png", "desc": "Çöp | Yer Kaplar"},
        "worm": {"name": "Solucan (Yem)", "icon": "minnow.png", "desc": "Sistem: Otomatik Kısayola Atanır"},
        "bleach": {"name": "Renk Açıcı", "icon": "minnow.png", "desc": "Çöp"},
        "lucy_ring": {"name": "Lucy'nin Yüzüğü", "icon": "golden_tuna.png", "desc": "Nadir | Düşürmeyi Önler"},
        "symbol_wise": {"name": "Bilge Kralın Sembolü", "icon": "golden_tuna.png", "desc": "Nadir"},
        "glove_wise": {"name": "Bilge Kralın Eldiveni", "icon": "golden_tuna.png", "desc": "Nadir"},
    }
    
    # Kullanıcı Ayarları (Varsayılan)
    # Action: 'keep' (Sakla), 'drop' (At), 'open' (Aç/Sağ Tık), 'kill' (Öldür/Sağ Tık)
    DEFAULT_ACTIONS = {key: "keep" for key in FISH_DATA.keys()}
    DEFAULT_ACTIONS["worm"] = "assign" # Özel Aksiyon: Kısayola Ata
    
    # Çöpleri Otomatik Yere At
    DEFAULT_ACTIONS["minnow"] = "kill" # Genelde ölürse yem olur
    DEFAULT_ACTIONS["hair_dye"] = "drop"
    DEFAULT_ACTIONS["bleach"] = "drop"
    DEFAULT_ACTIONS["lucy_ring"] = "drop"
    
    # Özel Eşyalar
    DEFAULT_ACTIONS["clam"] = "open" # İstiridye açılır (inci için)
    DEFAULT_ACTIONS["jigsaw_chest"] = "keep"


import cv2
import numpy as np
import time
from config_manager import ConfigManager

class InventoryManager:
    def __init__(self, telegram_callback=None):
        self.db = FishDatabase()
        self.config = ConfigManager()
        self.confidence_threshold = 0.8
        self.telegram_callback = telegram_callback # Eşleşme hassasiyeti
        
        # İlk açılışta varsayılanları kaydet
        for key, default_act in self.db.DEFAULT_ACTIONS.items():
            if not self.config.get_fish_action(key, None):
                self.config.set_fish_action(key, default_act)
        
    def set_action(self, fish_key, action):
        """Kullanıcının tercihini günceller ve kaydeder"""
        self.config.set_fish_action(fish_key, action)
            
    def get_action(self, fish_key):
        return self.config.get_fish_action(fish_key, self.db.DEFAULT_ACTIONS.get(fish_key, "keep"))

    def set_price(self, fish_key, price):
        """Balık fiyatını kaydeder (Milyon cinsinden)"""
        # Config manager'da 'market_prices' bölümü olmadığı için manuel json yönetimi yapalım
        # veya ConfigManager'a ekleyelim. ConfigManager daha temiz.
        self.config.set_config_value("market_prices", fish_key, price)

    def get_price(self, fish_key):
        """Balık fiyatını getir"""
        return self.config.get_config_value("market_prices", fish_key, 0.0)
        
    def scan_and_process(self, sct, inventory_region):
        """
        Envanter bölgesinin ekran görüntüsünü alır, bilinen balıkları/eşyaları arar 
        ve ayarlanan eylemleri gerçekleştirir.
        
        Args:
            sct: mss nesnesi
            inventory_region: {"top": int, "left": int, "width": int, "height": int}
        Return:
            int: İşlem yapılan eşya sayısı
        """
        if not platform.system() == "Windows":
            print("[Mock] Mac ortamında envanter tarama simüle ediliyor...")
            return 0

        # Ekran görüntüsü al
        img = np.array(sct.grab(inventory_region))
        img_gray = cv2.cvtColor(img, cv2.COLOR_BGRA2GRAY)
        
        processed_count = 0
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        assets_dir = os.path.join(base_dir, "assets", "fish_icons")
        
        # Her bilinen eşya için tarama yap
        for key, data in self.db.FISH_DATA.items():
            action = self.get_action(key)
            
            # Keep (Sakla) dışındaki veya Assign (Ata) olanları işle
            # AYRICA: 'keep' olsa bile Nadir balıksa (Worm değilse) ve bildirim açıksa bildir
            is_rare_keep = (action == "keep" and key != "worm")
            
            if action == "keep" and not is_rare_keep: continue 
                
            icon_name = data.get("icon", "")
            icon_path = os.path.join(assets_dir, icon_name)
            
            if not os.path.exists(icon_path):
                continue
                
            try:
                template = cv2.imread(icon_path, 0) # Grayscale oku
                if template is None: continue
                
                w, h = template.shape[::-1]
                
                # Template Matching
                res = cv2.matchTemplate(img_gray, template, cv2.TM_CCOEFF_NORMED)
                loc = np.where(res >= self.confidence_threshold)
                
                # Bulunan her nokta için
                # Aynı eşyayı defalarca tespit etmemek için maskeleme veya mesafe kontrolü gerekebilir
                # Basit yöntem: Bulunan noktaları listele ve yakın olanları ele.
                found_points = list(zip(*loc[::-1]))
                
                # Basit kümeleme (Aynı slotu tekrar tıklamasın)
                unique_slots = []
                for pt in found_points:
                    # Bu nokta mevcut benzersiz slotlardan herhangi birine yakın mı?
                    is_close = False
                    for slot in unique_slots:
                        if abs(pt[0] - slot[0]) < 10 and abs(pt[1] - slot[1]) < 10:
                            is_close = True
                            break
                    if not is_close:
                        # Koordinat dönüştürme (Envanter bölgesi + bulunan nokta)
                        screen_x = inventory_region["left"] + pt[0] + w//2
                        screen_y = inventory_region["top"] + pt[1] + h//2
                        unique_slots.append((screen_x, screen_y))
                
                # Aksiyonları Uygula
                for sx, sy in unique_slots:
                    if is_rare_keep:
                        # Sadece bildirim gönder (İşlem yapma)
                        if self.telegram_callback:
                            self.telegram_callback(f"🎉 Nadir Balık Tespit Edildi: {data['name']}")
                    elif action == "assign":
                         print(f"Yem bulundu ve atanıyor: {key}")
                         self.execute_action("assign", sx, sy)
                    else:
                         print(f"İşlem: {data['name']} -> {action.upper()}")
                         self.execute_action(action, sx, sy)
                         
                    if not is_rare_keep: # Sadece işlem yapılanları say
                        processed_count += 1
                        time.sleep(0.3) # İşlem arası bekleme
                    
            except Exception as e:
                print(f"Scan Hata ({key}): {e}")
                pass
                
        return processed_count

    def execute_action(self, action, x, y):
        """Belirlenen eylemi gerçekleştirir"""
        
        if action == "keep":
            return
            
        elif action == "open" or action == "kill":
            # Sağ Tıkla (Açar veya Öldürür)
            pydirectinput.moveTo(x, y)
            time.sleep(0.1)
            pydirectinput.rightClick()
            
        elif action == "assign":
            # CTRL + Tık ile kısayola ata
            pydirectinput.moveTo(x, y)
            time.sleep(0.1)
            pydirectinput.keyDown('ctrl')
            time.sleep(0.1)
            pydirectinput.click() # Sol tık
            time.sleep(0.1)
            pydirectinput.keyUp('ctrl')
            
        elif action == "drop":
            # Yere Atma (Sürükle Bırak)
            try:
                pydirectinput.moveTo(x, y)
                time.sleep(0.1)
                pydirectinput.mouseDown()
                time.sleep(0.2)
                # Envanter dışına sürükle (Örn: 400px sola)
                pydirectinput.moveTo(x - 400, y) 
                time.sleep(0.2)
                pydirectinput.mouseUp()
                time.sleep(0.2)
                
                # "Yere atmak istiyor musun?" onay penceresi çıkarsa
                # Genelde 'Enter' veya 'Evet' butonuna tıklamak gerekir.
                # Şimdilik Enter'a basalım
                pydirectinput.press('enter')
            except Exception as e:
                print(f"Drop hatası: {e}")
                pass
    def scan_unknown_items(self, inventory_img, region_offset):
        """
        Envanterdeki tanımlanamayan nesneleri bulur ve kaydeder.
        inventory_img: Envanter bölgesinin CV2 görüntüsü
        region_offset: (left, top) global koordinatları
        """
        # Standart Metin2 Envanter Izgarası (Yaklaşık Değerler)
        # 5 Sütun x 9 Satır
        # Slot Boyutu: 32x32
        # Aralık: Yok veya çok az
        
        # Basit Izgara Tarama
        rows, cols = 9, 5
        slot_w, slot_h = 32, 32
        
        # Envanter penceresinin iç kısmının (slotların olduğu yer) tam coordinatesini bilmemiz lazım.
        # Genelde inventory_area tüm pencereyi kapsar. Slotlar biraz içeridedir.
        # Varsayım: inventory_img SADECE slotların olduğu alanı içeriyor (kullanıcı doğru seçtiyse).
        
        unknowns = []
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        unknown_dir = os.path.join(base_dir, "assets", "unknown_items")
        if not os.path.exists(unknown_dir): os.makedirs(unknown_dir)
        
        img_h, img_w = inventory_img.shape[:2]
        step_x = img_w // cols
        step_y = img_h // rows
        
        for r in range(rows):
            for c in range(cols):
                x = c * step_x
                y = r * step_y
                
                # Slot Görüntüsü
                slot_img = inventory_img[y:y+slot_h, x:x+slot_w]
                
                # Doluluk Kontrolü (Basit Varyans/Renk Kontrolü)
                # Boş slot genelde koyu grid rengidir. Dolu slot renklidir.
                if np.std(slot_img) < 10: # Düşük varyans = Muhtemelen boş
                    continue
                    
                # Bilinen bir eşya mı? (Template Matching ile kontrol edilebilir ama pahalı)
                # Şimdilik sadece "Bu slot dolu" diye kaydedelim, kullanıcıya soracağız.
                
                # Dosya Adı: unknown_page1_r2_c3.png
                filename = f"unknown_{r}_{c}_{int(time.time())}.png"
                filepath = os.path.join(unknown_dir, filename)
                cv2.imwrite(filepath, slot_img)
                unknowns.append(filepath)
                
        return unknowns

    def learn_item(self, temp_path, item_key):
        """Bilinmeyen bir eşyayı (temp_path) asıl kütüphaneye (item_key) taşır"""
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        target_dir = os.path.join(base_dir, "assets", "fish_icons")
        if not os.path.exists(target_dir): os.makedirs(target_dir)
        
        # DB'den dosya adını al
        fish_info = self.db.FISH_DATA.get(item_key)
        if not fish_info: return False
        
        final_name = fish_info['icon']
        final_path = os.path.join(target_dir, final_name)
        
        # Taşı / Üzerine Yaz
        import shutil
        shutil.move(temp_path, final_path)
        print(f"Eşya Öğrenildi: {item_key} -> {final_name}")
        return True
