import os
import time
import threading
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
import tkinter.font as tkFont
import requests
from packaging import version
from sam_translate.sam_translate import set_root, set_sam_mini_chat_globals, create_sam_mini_chat
from config import load_config, save_config
import ctypes
from ctypes import wintypes

try:
    import psutil
except ImportError:
    psutil = None

from PIL import Image, ImageChops, ImageTk
from autoit_module import auto_it_function
from settings_dialog import open_settings, center_window

# Load cấu hình
config = load_config()
XAI_API_KEY = config.get("xai_api_key", "")
CHATGPT_API_KEY = config.get("chatgpt_api_key", "")
LLM_API_KEY = config.get("llm_api_key", "")
TRANSLATION_ONLY = config.get("translation_only", True)
DEFAULT_TARGET_LANG = config.get("default_target_lang", "vi")
DEFAULT_TELEGRAM_PATH = config.get("telegram_path", "")
MARKER_IMAGE_PATH = os.path.join(os.getcwd(), "marker_image.png")
arrange_width = config.get("arrange_width", 500)
arrange_height = config.get("arrange_height", 504)

# Thư viện Windows API
user32 = ctypes.windll.user32

# Hàm lấy handle cửa sổ từ PID
def get_window_handle_by_pid(pid):
    handles = []
    @ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_int, ctypes.c_int)
    def enum_callback(hwnd, lParam):
        if user32.IsWindow(hwnd) and user32.IsWindowVisible(hwnd):
            window_pid = wintypes.DWORD()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(window_pid))
            if window_pid.value == pid:
                handles.append(hwnd)
        return True
    user32.EnumWindows(enum_callback, 0)
    return handles[0] if handles else None

# Hàm chụp ảnh cửa sổ
def capture_window(hwnd):
    gdi32 = ctypes.windll.gdi32
    rect = wintypes.RECT()
    user32.GetWindowRect(hwnd, ctypes.byref(rect))
    width = rect.right - rect.left
    height = rect.bottom - rect.top
    hwindc = user32.GetWindowDC(hwnd)
    srcdc = gdi32.CreateCompatibleDC(hwindc)
    bmp = gdi32.CreateCompatibleBitmap(hwindc, width, height)
    gdi32.SelectObject(srcdc, bmp)
    result = user32.PrintWindow(hwnd, srcdc, 2)
    if result != 1:
        print("Consolog [WARNING]: PrintWindow không thành công hoặc chỉ chụp được 1 phần.")

    class BITMAPINFOHEADER(ctypes.Structure):
        _fields_ = [
            ("biSize", ctypes.c_uint32),
            ("biWidth", ctypes.c_int32),
            ("biHeight", ctypes.c_int32),
            ("biPlanes", ctypes.c_uint16),
            ("biBitCount", ctypes.c_uint16),
            ("biCompression", ctypes.c_uint32),
            ("biSizeImage", ctypes.c_uint32),
            ("biXPelsPerMeter", ctypes.c_int32),
            ("biYPelsPerMeter", ctypes.c_int32),
            ("biClrUsed", ctypes.c_uint32),
            ("biClrImportant", ctypes.c_uint32),
        ]

    bmi = BITMAPINFOHEADER()
    bmi.biSize = ctypes.sizeof(BITMAPINFOHEADER)
    bmi.biWidth = width
    bmi.biHeight = -height
    bmi.biPlanes = 1
    bmi.biBitCount = 32
    bmi.biCompression = 0

    buffer_len = width * height * 4
    buffer = ctypes.create_string_buffer(buffer_len)
    _ = gdi32.GetDIBits(srcdc, bmp, 0, height, buffer, ctypes.byref(bmi), 0)

    image = Image.frombuffer('RGBA', (width, height), buffer, 'raw', 'BGRA', 0, 1)

    gdi32.DeleteObject(bmp)
    gdi32.DeleteDC(srcdc)
    user32.ReleaseDC(hwnd, hwindc)
    return image

# Language dictionary
lang = {
    "title": "Telegram Auto Tool",
    "setting": "⚙️ Setting",
    "log_label": "Log:",
    "telegram_path_label": "Telegram Path:",
    "msg_error_path": "Invalid path!",
    "save_telegram_path": "💾 Save Telegram Path"
}

# Kiểm tra thư viện psutil
if not psutil:
    print("Consolog: Warning - psutil is not installed! Please install with 'pip install psutil' to check live via PID.")

# Ghi log
def log_message(msg):
    text_log.insert(tk.END, msg + "\n")
    text_log.see(tk.END)
    print(f"[LOG] {msg}")

# Lưu đường dẫn Telegram
def save_telegram_path():
    global DEFAULT_TELEGRAM_PATH
    telegram_path = telegram_path_entry.get().strip()
    print(f"Consolog: Lưu Telegram Path từ màn hình chính: {telegram_path}")
    if os.path.isfile(telegram_path):
        config["telegram_path"] = telegram_path
        DEFAULT_TELEGRAM_PATH = telegram_path
        save_config(config)
        log_message("Đã lưu đường dẫn Telegram!")
    else:
        log_message("Đường dẫn Telegram không hợp lệ!")

# Đóng ứng dụng
def on_closing():
    print("Consolog: Đóng ứng dụng...")
    root.destroy()

# Khởi tạo giao diện chính
def init_main_ui():
    global root, text_log, telegram_path_entry, DEFAULT_TELEGRAM_PATH, XAI_API_KEY, CHATGPT_API_KEY, LLM_API_KEY
    root = tk.Tk()
    root.title("Telegram Auto")
    root.geometry("800x600")
    center_window(root, 800, 600)

    # Tạo frame chính
    main_frame = tk.Frame(root)
    main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    # Tạo frame cho đường dẫn Telegram
    telegram_frame = tk.Frame(main_frame)
    telegram_frame.pack(fill=tk.X, pady=5)
    tk.Label(telegram_frame, text="Đường dẫn Telegram:").pack(side=tk.LEFT)
    telegram_path_entry = tk.Entry(telegram_frame, width=50)
    telegram_path_entry.pack(side=tk.LEFT, padx=5)
    telegram_path_entry.insert(0, DEFAULT_TELEGRAM_PATH)
    btn_browse = tk.Button(telegram_frame, text="Browse", command=save_telegram_path)
    btn_browse.pack(side=tk.LEFT)

    # Tạo frame cho log
    log_frame = tk.Frame(main_frame)
    log_frame.pack(fill=tk.BOTH, expand=True, pady=5)
    text_log = tk.Text(log_frame, height=20)
    text_log.pack(fill=tk.BOTH, expand=True)
    text_log.name = 'text_log'  # Đặt tên cho widget để có thể truy cập sau này

    # Tạo frame cho các nút
    button_frame = tk.Frame(main_frame)
    button_frame.pack(fill=tk.X, pady=5)
    btn_settings = tk.Button(button_frame, text="Settings", command=lambda: open_settings(root))
    btn_settings.pack(side=tk.LEFT, padx=5)

    print("Consolog: Kiểm tra Telegram Path từ màn hình chính thay vì Settings")
    
    if not DEFAULT_TELEGRAM_PATH:
        log_message("Đường dẫn Telegram chưa được thiết lập. Vui lòng nhập và lưu!")
        save_telegram_path()
        if not DEFAULT_TELEGRAM_PATH:
            log_message("Đường dẫn Telegram là bắt buộc để tiếp tục!")
            return

    print("Consolog: Kiểm tra API Keys")
    if not XAI_API_KEY or not CHATGPT_API_KEY or not LLM_API_KEY:
        log_message("API Key chưa được thiết lập. Vui lòng nhập trong Settings!")
        open_settings(root)
        if not XAI_API_KEY or not CHATGPT_API_KEY or not LLM_API_KEY:
            log_message("API Key là bắt buộc để tiếp tục!")
            return

    try:
        set_root(root)
        set_sam_mini_chat_globals(XAI_API_KEY, CHATGPT_API_KEY, LLM_API_KEY, DEFAULT_TARGET_LANG)
        create_sam_mini_chat()
        print("Consolog: Sam Translate và Sam Mini Chat đã được khởi động tự động khi ứng dụng bắt đầu.")
    except Exception as e:
        print(f"Consolog [ERROR]: Lỗi khi khởi động Sam Translate hoặc Sam Mini Chat: {e}")

    root.mainloop()

# Khởi chạy ứng dụng
print("Consolog: Ứng dụng khởi chạy.")
init_main_ui()