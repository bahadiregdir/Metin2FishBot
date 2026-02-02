"""
Otomatik Güncelleme Kontrol Modülü
"""
import requests
import os
import threading

GITHUB_USER = "bahadiregdir"
REPO_NAME = "Metin2FishBot"
BRANCH = "main"
VERSION_URL = f"https://raw.githubusercontent.com/{GITHUB_USER}/{REPO_NAME}/{BRANCH}/version.txt"

def get_local_version():
    """Yerel versiyonu oku"""
    try:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        version_path = os.path.join(base_dir, "version.txt")
        with open(version_path, "r") as f:
            return f.read().strip()
    except:
        return "Unknown"

def check_for_updates(callback):
    """Güncellemeleri asenkron kontrol et"""
    def worker():
        try:
            current_ver = get_local_version()
            if current_ver == "Unknown":
                return

            response = requests.get(VERSION_URL, timeout=5)
            if response.status_code == 200:
                remote_ver = response.text.strip()
                
                # Versiyon karşılaştırma (basit string olarak)
                if remote_ver != current_ver:
                    callback(True, remote_ver) # Update var
                else:
                    callback(False, current_ver) # Güncel
        except Exception as e:
            print(f"Update check error: {e}")

    threading.Thread(target=worker, daemon=True).start()
