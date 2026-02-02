import requests
import threading
import os
import time

class TelegramNotifier:
    def __init__(self, token, chat_id):
        self.token = token
        self.chat_id = chat_id
        if self.token:
             self.base_url = f"https://api.telegram.org/bot{self.token}"
        else:
             self.base_url = ""
             
        self.enabled = bool(token and chat_id)
        self.polling = False
        self.last_update_id = 0
        self.command_handlers = {} # '/cmd': callback_func

    def send_message(self, message, keyboard=None):
        """Metin mesajı gönderir (Asenkron)"""
        if not self.enabled: return
        
        def _send():
            try:
                url = f"{self.base_url}/sendMessage"
                data = {"chat_id": self.chat_id, "text": message}
                if keyboard:
                    import json
                    data["reply_markup"] = json.dumps(keyboard)
                requests.post(url, data=data, timeout=10)
            except Exception as e:
                print(f"Telegram Hatası: {e}")

        threading.Thread(target=_send, daemon=True).start()

    def show_menu(self):
        """Kalıcı menü butonlarını gösterir"""
        if not self.enabled: return
        
        keyboard = {
            "keyboard": [
                [{"text": "/status 📊"}, {"text": "/stats 📈"}],
                [{"text": "/ss 📸"}, {"text": "/envanter 🎒"}],
                [{"text": "/start ▶️"}, {"text": "/stop 🛑"}],
                [{"text": "/pause ⏸️"}, {"text": "/help ℹ️"}]
            ],
            "resize_keyboard": True,
            "persistent": True
        }
        self.send_message("🎛 **Kontrol Paneli**", keyboard=keyboard)

    def send_photo(self, photo_path, caption=""):
        """Fotoğraf gönderir (Asenkron)"""
        if not self.enabled or not os.path.exists(photo_path): return
        
        def _send():
            try:
                url = f"{self.base_url}/sendPhoto"
                with open(photo_path, "rb") as photo:
                    files = {"photo": photo}
                    data = {"chat_id": self.chat_id, "caption": caption}
                    requests.post(url, files=files, data=data, timeout=20)
            except Exception as e:
                print(f"Telegram Foto Hatası: {e}")

        threading.Thread(target=_send, daemon=True).start()

    def update_credentials(self, token, chat_id):
        self.token = token
        self.chat_id = chat_id
        if self.token:
             self.base_url = f"https://api.telegram.org/bot{self.token}"
        self.enabled = bool(token and chat_id)
        
        # Eğer aktifse ve polling başlamadıysa başlat
        if self.enabled and not self.polling:
            self.start_polling()

    def register_handler(self, command, callback):
        """Komut için fonksiyon kaydeder (örn: '/stop' -> stop_bot_func)"""
        self.command_handlers[command] = callback

    def start_polling(self):
        """Telegram'dan gelen mesajları dinlemeye başlar"""
        if self.polling: return
        self.polling = True
        
        def _poll_loop():
            print("📡 Telegram dinlemeye başladı...")
            while self.polling and self.enabled:
                try:
                    url = f"{self.base_url}/getUpdates"
                    params = {"offset": self.last_update_id + 1, "timeout": 30}
                    resp = requests.get(url, params=params, timeout=35)
                    
                    if resp.status_code == 200:
                        data = resp.json()
                        result = data.get("result", [])
                        
                        for update in result:
                            self.last_update_id = update["update_id"]
                            
                            # Mesaj içeriği
                            if "message" in update and "text" in update["message"]:
                                text = update["message"]["text"].strip()
                                sender_id = str(update["message"]["chat"]["id"])
                                
                                # Sadece yetkili chat_id'den gelenleri kabul et
                                if sender_id == str(self.chat_id):
                                    cmd = text.split()[0].lower() # /stop
                                    if cmd in self.command_handlers:
                                        # Callback'i çağır (Argümanları ilet)
                                        # Not: Callback, argüman kabul etmiyorsa (örn: ss) bunu handle etmeliyiz
                                        try:
                                            self.command_handlers[cmd](text)
                                        except TypeError:
                                            # Argüman kabul etmeyen eski fonksiyonlar için fallback
                                            self.command_handlers[cmd]()
                                    else:
                                        # Bilinmeyen komut
                                        pass
                                        
                except Exception as e:
                    # print(f"Polling Hatası: {e}")
                    time.sleep(5)
                
                time.sleep(1)

        threading.Thread(target=_poll_loop, daemon=True).start()

    def stop_polling(self):
        self.polling = False
