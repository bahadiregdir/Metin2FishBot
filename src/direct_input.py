import ctypes
import time

# Windows API Yapıları
SendInput = ctypes.windll.user32.SendInput

# C Tipi Yapılar
PUL = ctypes.POINTER(ctypes.c_ulong)
class KeyBdInput(ctypes.Structure):
    _fields_ = [("wVk", ctypes.c_ushort),
                ("wScan", ctypes.c_ushort),
                ("dwFlags", ctypes.c_ulong),
                ("time", ctypes.c_ulong),
                ("dwExtraInfo", PUL)]

class HardwareInput(ctypes.Structure):
    _fields_ = [("uMsg", ctypes.c_ulong),
                ("wParamL", ctypes.c_short),
                ("wParamH", ctypes.c_ushort)]

class MouseInput(ctypes.Structure):
    _fields_ = [("dx", ctypes.c_long),
                ("dy", ctypes.c_long),
                ("mouseData", ctypes.c_ulong),
                ("dwFlags", ctypes.c_ulong),
                ("time", ctypes.c_ulong),
                ("dwExtraInfo", PUL)]

class Input_I(ctypes.Union):
    _fields_ = [("ki", KeyBdInput),
                ("mi", MouseInput),
                ("hi", HardwareInput)]

class Input(ctypes.Structure):
    _fields_ = [("type", ctypes.c_ulong),
                ("ii", Input_I)]

# DirectX Scan Codes (Donanım Kodları)
# https://www.win.tue.nl/~aeb/linux/kbd/scancodes-1.html
SCAN_CODE = {
    "1": 0x02, "2": 0x03, "3": 0x04, "4": 0x05, 
    "space": 0x39,
    "f1": 0x3B, "f2": 0x3C, "f3": 0x3D, "f4": 0x3E,
    "i": 0x17, "z": 0x2C, "esc": 0x01
}

def PressKey(hexKeyCode):
    extra = ctypes.c_ulong(0)
    ii_ = Input_I()
    ii_.ki = KeyBdInput(0, hexKeyCode, 0x0008, 0, ctypes.pointer(extra))
    x = Input(ctypes.c_ulong(1), ii_)
    ctypes.windll.user32.SendInput(1, ctypes.pointer(x), ctypes.sizeof(x))

def ReleaseKey(hexKeyCode):
    extra = ctypes.c_ulong(0)
    ii_ = Input_I()
    ii_.ki = KeyBdInput(0, hexKeyCode, 0x0008 | 0x0002, 0, ctypes.pointer(extra))
    x = Input(ctypes.c_ulong(1), ii_)
    ctypes.windll.user32.SendInput(1, ctypes.pointer(x), ctypes.sizeof(x))

def send_key(key_name, duration=0.1):
    """Belirtilen tuşa basar ve bırakır (Donanım seviyesi)"""
    key = key_name.lower()
    if key in SCAN_CODE:
        code = SCAN_CODE[key]
        PressKey(code)
        time.sleep(duration)
        ReleaseKey(code)
        return True
    else:
        print(f"Bilinmeyen tus kodu: {key}")
        return False

# --- MOUSE FONKSİYONLARI ---

MOUSEEVENTF_MOVE = 0x0001
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
MOUSEEVENTF_ABSOLUTE = 0x8000

def move_mouse(x, y):
    """Mouse'u belirtilen X, Y koordinatlarına taşır (Absolute, SendInput ile)"""
    # Windows SendInput absolute koordinatları 0-65535 arasına normalize eder.
    # Ekran çözünürlüğünü almamız lazım.
    user32 = ctypes.windll.user32
    screen_width = user32.GetSystemMetrics(0)
    screen_height = user32.GetSystemMetrics(1)
    
    # Normalize Et (65535 üzerinden)
    norm_x = int(x * 65535 / screen_width)
    norm_y = int(y * 65535 / screen_height)
    
    extra = ctypes.c_ulong(0)
    ii_ = Input_I()
    ii_.mi = MouseInput(0, 0, 0, MOUSEEVENTF_MOVE | MOUSEEVENTF_ABSOLUTE, 0, ctypes.pointer(extra))
    
    # MouseInput struct'ında dx ve dy alanları long tipindedir.
    # Ancak MOUSEEVENTF_ABSOLUTE kullanırken bu alanlara normalize edilmiş koordinatlar verilir.
    ii_.mi.dx = norm_x
    ii_.mi.dy = norm_y
    
    x_input = Input(ctypes.c_ulong(0), ii_)
    ctypes.windll.user32.SendInput(1, ctypes.pointer(x_input), ctypes.sizeof(x_input))

def click_mouse():
    """Sol Tık Yapar"""
    extra = ctypes.c_ulong(0)
    ii_ = Input_I()
    
    # Bas
    ii_.mi = MouseInput(0, 0, 0, MOUSEEVENTF_LEFTDOWN, 0, ctypes.pointer(extra))
    x = Input(ctypes.c_ulong(0), ii_)
    ctypes.windll.user32.SendInput(1, ctypes.pointer(x), ctypes.sizeof(x))
    
    time.sleep(0.05) # Küçük bir basılı tutma süresi
    
    # Çek
    ii_.mi = MouseInput(0, 0, 0, MOUSEEVENTF_LEFTUP, 0, ctypes.pointer(extra))
    x = Input(ctypes.c_ulong(0), ii_)
    ctypes.windll.user32.SendInput(1, ctypes.pointer(x), ctypes.sizeof(x))
