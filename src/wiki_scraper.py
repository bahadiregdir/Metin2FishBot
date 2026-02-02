
import os
import requests
import re
from PIL import Image
from io import BytesIO

# Wiki URL ve Base
BASE_URL = "https://tr-wiki.metin2.gameforge.com"

# Balık Anahtarı Eşleştirme Sözlüğü (Wiki Adı -> Bizim Key)
# Otomatik eşleşmeyenler için manuel harita
NAME_MAP = {
    "Sudak Balığı": "zander",
    "Minik Balık": "minnow",
    "Mandarin Balığı": "mandarin",
    "Büyük Japon Balığı": "large_goldfish",
    "Sazan Balığı": "carp",
    "Sazan": "carp",
    "Som Balığı": "salmon",
    "Morina Balığı": "cod",
    "Yayın Balığı": "catfish",
    "Kadife Balığı": "tench",
    "Alabalık": "trout",
    "Dere Alabalığı": "trout", # Benzer
    "Yılan Balığı": "eel",
    "Gökkuşağı Alabalığı": "rainbow_trout",
    "Levrek": "perch",
    "Altın Ton": "golden_tuna",
    "Kerevit": "yabbie",
    "Yengeç": "crab",
    "Karides": "shrimp",
    "İstiridye": "clam",
    "Ringa Balığı": "ringa", # Bizde yoksa ekleriz
    "Tekir Balığı": "tekir",
    "Palamut Balığı": "palamut",
    "Lüfer Balığı": "lufer",
    "Hamsi": "hamsi",
    "Aynalı Sazan": "aynali_sazan",
    "Altın Sudak Balığı": "gold_zander", # Farklı bir tür
    "Kral Yengeci": "king_crab",
    "Yabbie Yengeci": "yabbie", # Tekrar
}

# HTML İçeriği (Senin verdiğin tablonun özeti + tüm sayfa yapısını simüle eden regex)
# Tam HTML parse etmek yerine Regex ile img src ve title avlayacağız.
# Çünkü requests ile sayfayı çekmek daha temiz.

def download_wiki_images():
    print("🎣 Wiki'den Balık İkonları İndiriliyor...")
    
    # Hedef Klasör
    base_dir = os.path.dirname(os.path.abspath(__file__))
    target_dir = os.path.join(base_dir, "assets", "fish_icons")
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)

    # Wiki Sayfası
    url = "https://tr-wiki.metin2.gameforge.com/index.php/Bal%C4%B1k%C3%A7%C4%B1l%C4%B1k"
    
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36'}
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        html_content = response.text
        
        # Regex ile Balık Adı ve Resim URL'sini bul
        # Kalıp: <a href="..." title="Balık Adı"><img alt="..." src="/images/..." ...>
        # Not: Metin2 Wiki'de genellikle link title'ı balık adını verir.
        
        # Basit Regex: title="([^"]+)"\s*><img\s*alt="[^"]*"\s*src="([^"]+)"
        # Bu kalıp sayfadaki diğer ikonları da alabilir ama filtreleyeceğiz.
        
        pattern = re.compile(r'title="([^"]+)"[^>]*>\s*<img[^>]+src="([^"]+)"')
        matches = pattern.findall(html_content)
        
        print(f"🔎 {len(matches)} olası görsel bulundu.")
        
        count = 0
        for name, src in matches:
            # Gereksizleri atla
            if "Dosya:" in name or "Izgara" in name or "Ölü" in name or "Kılavuz" in name:
                continue
                
            clean_name = name.replace(" Balığı", "").strip() # "Sudak Balığı" -> "Sudak"
            full_name = name.strip()
            
            # Eşleştirme
            file_key = None
            
            # 1. Tam Eşleşme (Map)
            if full_name in NAME_MAP:
                file_key = NAME_MAP[full_name]
            # 2. Kısmi Eşleşme (Sudak -> zander)
            elif clean_name in NAME_MAP:
                 file_key = NAME_MAP[clean_name]
            else:
                # Bilinmeyenleri de indirelim, belki lazım olur
                # Türkçe karakterleri düzelt: ş->s, ı->i vs.
                file_key = clean_name.lower().replace("ş","s").replace("ı","i").replace("ğ","g").replace("ü","u").replace("ö","o").replace("ç","c").replace(" ","_")
            
            if not file_key: continue
            
            # URL Düzeltme
            if src.startswith("/"):
                img_url = BASE_URL + src
            else:
                img_url = src
                
            # İndir
            try:
                # Dosya zaten varsa atla
                save_path = os.path.join(target_dir, f"{file_key}.png")
                
                # Ama biz icon.png bekliyoruz, Wiki'deki ham görseli indirelim.
                # Önemli: Bizim inventory.py'deki tanımlarda 'icon': 'zander.png' gibi.
                # O yüzden file_key tam uymalı.
                
                print(f"   ⬇️ İndiriliyor: {full_name} -> {file_key}.png")
                
                img_data = requests.get(img_url, headers=headers).content
                img = Image.open(BytesIO(img_data))
                
                # 32x32 Resize (Wiki görselleri genelde 32x32 ama garanti olsun)
                img = img.resize((32, 32), Image.LANCZOS)
                
                img.save(save_path)
                count += 1
                
            except Exception as e:
                print(f"   ❌ Hata ({full_name}): {e}")
                
        print(f"✅ Toplam {count} yeni ikon indirildi ve kaydedildi!")
        print(f"📂 Klasör: {target_dir}")
        
    except Exception as e:
        print(f"🚨 Bağlantı Hatası: {e}")

if __name__ == "__main__":
    download_wiki_images()
