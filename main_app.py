
import os
import sys

# src modülünü path'e ekle
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from gui import App

if __name__ == "__main__":
    print("Starting Metin2 FishBot Launcher...")
    app = App()
    app.mainloop()
