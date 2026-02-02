
import os
import requests
from bs4 import BeautifulSoup
import re
import subprocess

# Balıkların listesi ve Wiki URL'leri
BASE_URL = "https://en-wiki.metin2.gameforge.com"
FISHING_PAGE = "/index.php/Fishing"
EVENT_PAGE = "/index.php/Fishing_Jigsaw"

# Kayıt edilecek klasör
SAVE_DIR = os.path.join(os.getcwd(), "assets/fish_icons")

# İndirilecek Balık Listesi
FISH_NAMES = [
    "Zander", "Mandarin Fish", "Large Zander", "Carp", "Salmon", 
    "Grass Carp", "Brook Trout", "Eel", "Rainbow Trout", "River Trout",
    "Rudd", "Perch", "Tenchi", "Catfish", "Lotus Fish", "Sweetfish",
    "Smelt", "Shiri", "Mirror Carp", "Goldfish", "Snakehead",
    "Skygazer", "Red King Crab", "Yabby", "Golden Tuna", "Minnow"
]

def download_with_curl(url, output_path=None):
    """Curl kullanarak web isteği yapar (Anti-bot bypass)"""
    cmd = ['curl', '-s', '-A', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)', '-L', url]
    if output_path:
        cmd.extend(['-o', output_path])
        subprocess.run(cmd)
        return True
    else:
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.stdout

def download_assets():
    # --- HAZIRLIK: Klasörleri Oluştur ---
    folders = {
        "live": os.path.join(SAVE_DIR, "live"),
        "dead": os.path.join(SAVE_DIR, "dead"),
        "grilled": os.path.join(SAVE_DIR, "grilled"),
        "misc": os.path.join(SAVE_DIR, "misc"),
        "event": os.path.join(SAVE_DIR, "event_jigsaw")
    }
    
    for f in folders.values():
        if not os.path.exists(f):
            os.makedirs(f)

    # --- PART 1: MAIN FISHING PAGE ---
    print(f"🎣 [1/2] Fetching Fishing Page: {BASE_URL + FISHING_PAGE}")
    try:
        html = download_with_curl(BASE_URL + FISHING_PAGE)
        if not html:
            print("❌ Main page download failed.")
        else:
            soup = BeautifulSoup(html, 'html.parser')
            imgs = soup.find_all('img')
            print(f"   -> Found {len(imgs)} images. Filtering...")
            
            count = 0
            for img in imgs:
                alt = img.get('alt', '').lower()
                src = img.get('src', '')
                if not src: continue
                if not src.startswith("http"): src = BASE_URL + src
                
                # Gereksizleri atla
                if "flag" in alt or "px" in alt: continue

                target = None
                clean_name = alt.replace("icon", "").strip()

                if "grilled" in alt: target = folders["grilled"]
                elif "dead" in alt: target = folders["dead"]
                
                # Misc kontrolü
                elif any(x in alt for x in ["worm", "paste", "clam", "pearl", "hair", "bleach", "key", "ring"]):
                    target = folders["misc"]
                
                # Canlı Balık kontrolü
                else:
                    is_live = False
                    for fish in FISH_NAMES:
                        if fish.lower() in alt:
                            is_live = True
                            clean_name = fish.lower()
                            target = folders["live"]
                            break
                    if not is_live and "fish" in alt: # Generic fish
                         target = folders["live"]

                if target:
                    safe_name = clean_name.replace(" ", "_")
                    ext = ".png" if ".png" in src else ".jpg"
                    file_path = os.path.join(target, f"{safe_name}{ext}")
                    
                    if not os.path.exists(file_path):
                        print(f"      -> Downloading: {safe_name}")
                        download_with_curl(src, file_path)
                        count += 1
            print(f"   ✅ Part 1 Done. {count} new files.")

    except Exception as e:
        print(f"❌ Error in Part 1: {e}")

    # --- PART 2: JIGSAW EVENT PAGE ---
    print(f"\n🧩 [2/2] Fetching Event Page: {BASE_URL + EVENT_PAGE}")
    try:
        html = download_with_curl(BASE_URL + EVENT_PAGE)
        if not html:
            print("❌ Event page download failed.")
        else:
            soup = BeautifulSoup(html, 'html.parser')
            imgs = soup.find_all('img')
            print(f"   -> Found {len(imgs)} images. Filtering for Jigsaw...")
            
            count = 0
            for img in imgs:
                alt = img.get('alt', '').lower()
                src = img.get('src', '')
                if not src: continue
                if not src.startswith("http"): src = BASE_URL + src
                
                if "chest" in alt or "piece" in alt or "jigsaw" in alt:
                    clean_name = alt.replace("icon", "").strip().replace(" ", "_")
                    ext = ".png" if ".png" in src else ".jpg"
                    file_path = os.path.join(folders["event"], f"{clean_name}{ext}")
                    
                    if not os.path.exists(file_path):
                        print(f"      -> Downloading: {clean_name}")
                        download_with_curl(src, file_path)
                        count += 1
            print(f"   ✅ Part 2 Done. {count} event assets.")

    except Exception as e:
        print(f"❌ Error in Part 2: {e}")

    print("\n🎉 All operations completed successfully.")

if __name__ == "__main__":
    download_assets()
