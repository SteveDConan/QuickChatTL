import os
import time
import shutil
import subprocess
import math
import ctypes
import threading
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
import tkinter.font as tkFont
import requests
from packaging import version
from sam_translate.sam_translate import set_root, set_sam_translate_globals, create_sam_translate, create_sam_mini_chat
from config import load_config, save_config

try:
    from send2trash import send2trash
except ImportError:
    send2trash = None

try:
    import psutil
except ImportError:
    psutil = None

from PIL import Image, ImageChops, ImageTk
from ctypes import wintypes
from autoit_module import auto_it_function

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
    "close_telegram": "❌ Close All Telegram",
    "log_label": "Log:",
    "telegram_path_label": "Telegram Path:",
    "msg_error_path": "Invalid path!",
    "close_result": "Close All Telegram:\nClosed: {closed}\nErrors: {errors}",
    "close_result_title": "Close Result",
    "save_telegram_path": "💾 Save Telegram Path"
}

# Kiểm tra thư viện psutil
if not psutil:
    print("Consolog: Warning - psutil is not installed! Please install with 'pip install psutil' to check live via PID.")

# Hàm tự động đóng Telegram
def auto_close_telegram():
    print("Consolog: Đang lấy danh sách tiến trình Telegram...")
    try:
        result = subprocess.run(
            ["tasklist", "/FI", "IMAGENAME eq Telegram.exe", "/FO", "CSV"],
            capture_output=True, text=True
        )
        output = result.stdout.strip().splitlines()
        pids = []
        for line in output[1:]:
            parts = line.replace('"', '').split(',')
            if len(parts) >= 2:
                pid = parts[1].strip()
                pids.append(pid)
                print(f"Consolog: Tìm thấy tiến trình Telegram với PID: {pid}")
        for pid in pids:
            print(f"Consolog: Đang đóng tiến trình với PID: {pid}")
            subprocess.run(["taskkill", "/F", "/PID", pid], capture_output=True, text=True)
            time.sleep(0.25)
        while True:
            result = subprocess.run(
                ["tasklist", "/FI", "IMAGENAME eq Telegram.exe", "/FO", "CSV"],
                capture_output=True, text=True
            )
            lines = result.stdout.strip().splitlines()
            if len(lines) <= 1:
                print("Consolog: Tất cả tiến trình Telegram đã được đóng.")
                break
            print("Consolog: Vẫn còn tiến trình Telegram, chờ 0.25 giây...")
            time.sleep(0.25)
        return True
    except Exception as e:
        print(f"Consolog [ERROR]: Lỗi khi tự động tắt Telegram: {e}")
        return False

# Đóng Telegram trong luồng riêng
def close_all_telegram_threaded():
    threading.Thread(target=auto_close_telegram, daemon=True).start()

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

# Mở cửa sổ Settings
def open_settings():
    print("Consolog: Mở cửa sổ Setting")
    popup = tk.Toplevel(root)
    popup.title("Setting - Tùy chỉnh sắp xếp & API Keys")
    center_window(popup, 550, 450)

    lbl_info = tk.Label(popup, text="Nhập kích thước cửa sổ sắp xếp:\nx = (số cột) × Custom Width, y = (số hàng) × Custom Height", wraplength=530)
    lbl_info.pack(pady=10)

    frame_entries = tk.Frame(popup)
    frame_entries.pack(pady=5)
    tk.Label(frame_entries, text="Custom Width:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
    entry_width = tk.Entry(frame_entries, width=10)
    entry_width.insert(0, str(arrange_width))
    entry_width.grid(row=0, column=1, padx=5, pady=5)
    tk.Label(frame_entries, text="Custom Height:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
    entry_height = tk.Entry(frame_entries, width=10)
    entry_height.insert(0, str(arrange_height))
    entry_height.grid(row=1, column=1, padx=5, pady=5)

    tk.Label(popup, text="xAI API Key:").pack(pady=5)
    xai_key_entry = tk.Entry(popup, width=50)
    xai_key_entry.insert(0, XAI_API_KEY)
    xai_key_entry.pack(pady=5)

    tk.Label(popup, text="ChatGPT API Key:").pack(pady=5)
    chatgpt_key_entry = tk.Entry(popup, width=50)
    chatgpt_key_entry.insert(0, CHATGPT_API_KEY)
    chatgpt_key_entry.pack(pady=5)

    tk.Label(popup, text="LLM API Key:").pack(pady=5)
    llm_key_entry = tk.Entry(popup, width=50)
    llm_key_entry.insert(0, LLM_API_KEY)
    llm_key_entry.pack(pady=5)

    def save_settings():
        global arrange_width, arrange_height, XAI_API_KEY, CHATGPT_API_KEY, LLM_API_KEY
        try:
            arrange_width = int(entry_width.get())
            arrange_height = int(entry_height.get())
            config["arrange_width"] = arrange_width
            config["arrange_height"] = arrange_height

            XAI_API_KEY = xai_key_entry.get().strip()
            CHATGPT_API_KEY = chatgpt_key_entry.get().strip()
            LLM_API_KEY = llm_key_entry.get().strip()

            if not LLM_API_KEY:
                log_message("LLM API Key không được để trống!")
                return

            config["xai_api_key"] = XAI_API_KEY
            config["chatgpt_api_key"] = CHATGPT_API_KEY
            config["llm_api_key"] = LLM_API_KEY
            save_config(config)
            print("Consolog: Đã lưu cấu hình Setting")
            log_message("Đã lưu cấu hình!")
            popup.destroy()
        except Exception as e:
            log_message(f"Giá trị không hợp lệ: {e}")
            print(f"Consolog [ERROR]: Lỗi lưu cấu hình Setting: {e}")

    btn_save = tk.Button(popup, text="Save", command=save_settings)
    btn_save.pack(pady=10)
    popup.transient(root)
    popup.grab_set()
    root.wait_window(popup)

# Căn giữa cửa sổ
def center_window(win, width, height):
    win.update_idletasks()
    screen_width = win.winfo_screenwidth()
    screen_height = win.winfo_screenheight()
    x = (screen_width - width) // 2
    y = (screen_height - height) // 2
    win.geometry(f"{width}x{height}+{x}+{y}")

# Hiển thị splash screen
def show_splash_screen():
    splash = tk.Tk()
    splash.overrideredirect(True)
    width = 400
    height = 200
    screen_width = splash.winfo_screenwidth()
    screen_height = splash.winfo_screenheight()
    x = (screen_width - width) // 2
    y = (screen_height - height) // 2
    splash.geometry(f"{width}x{height}+{x}+{y}")
    
    tk.Label(splash, text="Loading, please wait...", font=("Arial Unicode MS", 12)).pack(pady=20)
    progress_var = tk.DoubleVar(value=0)
    progress_bar = ttk.Progressbar(splash, variable=progress_var, maximum=100, length=300)
    progress_bar.pack(pady=20)
    percent_label = tk.Label(splash, text="0%", font=("Arial Unicode MS", 10))
    percent_label.pack(pady=10)
    
    print("Consolog: Splash screen hiển thị.")
    threading.Thread(target=lambda: load_tool(splash, progress_var, percent_label), daemon=True).start()
    splash.mainloop()

# Load tool trong splash screen
def load_tool(splash, progress_var, percent_label):
    start_time = time.time()
    print("Consolog: Bắt đầu load tool...")
    steps = ["Kiểm tra cấu hình", "Tải dữ liệu", "Khởi tạo giao diện"]
    for i, step in enumerate(steps):
        print(f"Consolog: Đang thực hiện: {step}")
        time.sleep(1.67)
        progress = (i + 1) / len(steps) * 100
        splash.after(0, lambda p=progress: progress_var.set(p))
        splash.after(0, lambda p=progress: percent_label.config(text=f"{int(p)}%"))
    end_time = time.time()
    print(f"Consolog: Tool đã load xong sau {end_time - start_time:.2f} giây.")
    splash.after(0, lambda: finish_splash(splash))

# Kết thúc splash screen
def finish_splash(splash):
    splash.destroy()
    print("Consolog: Splash screen kết thúc, khởi tạo giao diện chính.")
    init_main_ui()

# Khởi tạo giao diện chính
def init_main_ui():
    global root, text_log, telegram_path_entry, DEFAULT_TELEGRAM_PATH, XAI_API_KEY, CHATGPT_API_KEY, LLM_API_KEY
    root = tk.Tk()
    root.title(lang["title"])
    center_window(root, 650, 800)

    default_font = tkFont.nametofont("TkDefaultFont")
    default_font.configure(family="Arial Unicode MS", size=10)
    root.option_add("*Font", default_font)

    print("Consolog: Kiểm tra Telegram Path từ màn hình chính thay vì Settings")
    tk.Label(root, text=lang["title"], font=("Arial Unicode MS", 14, "bold")).pack(pady=10)

    frame_telegram_path = tk.Frame(root)
    frame_telegram_path.pack(pady=5)
    tk.Label(frame_telegram_path, text=lang["telegram_path_label"]).pack(side=tk.LEFT, padx=5)
    telegram_path_entry = tk.Entry(frame_telegram_path, width=50)
    telegram_path_entry.insert(0, DEFAULT_TELEGRAM_PATH)
    telegram_path_entry.pack(side=tk.LEFT, padx=5)
    print("Consolog [ĐÃ CHỈNH SỬA]: Đã ẩn nút Save Telegram Path trên giao diện chính")

    if not telegram_path_entry.get():
        log_message("Đường dẫn Telegram chưa được thiết lập. Vui lòng nhập và lưu!")
        save_telegram_path()
        if not telegram_path_entry.get():
            log_message("Đường dẫn Telegram là bắt buộc để tiếp tục!")
            return

    print("Consolog: Kiểm tra API Keys")
    if not XAI_API_KEY or not CHATGPT_API_KEY or not LLM_API_KEY:
        log_message("API Key chưa được thiết lập. Vui lòng nhập trong Settings!")
        open_settings()
        if not XAI_API_KEY or not CHATGPT_API_KEY or not LLM_API_KEY:
            log_message("API Key là bắt buộc để tiếp tục!")
            return

    frame_buttons = tk.Frame(root)
    frame_buttons.pack(pady=5)

    tk.Button(frame_buttons, text=lang["close_telegram"], command=close_all_telegram_threaded, width=18).grid(row=0, column=0, padx=5, pady=5)
    tk.Button(frame_buttons, text=lang["setting"], command=open_settings, width=18).grid(row=0, column=1, padx=5, pady=5)

    frame_log = tk.Frame(root)
    frame_log.pack(pady=10)
    tk.Label(frame_log, text=lang["log_label"]).pack()
    text_log = tk.Text(frame_log, width=70, height=10)
    text_log.pack()

    root.protocol("WM_DELETE_WINDOW", on_closing)

    try:
        set_root(root)
        set_sam_translate_globals(XAI_API_KEY, CHATGPT_API_KEY, LLM_API_KEY, TRANSLATION_ONLY, DEFAULT_TARGET_LANG)
        create_sam_translate()
        create_sam_mini_chat()
        print("Consolog: Sam Translate và Sam Mini Chat đã được khởi động tự động khi ứng dụng bắt đầu.")
    except Exception as e:
        print(f"Consolog [ERROR]: Lỗi khi khởi động Sam Translate hoặc Sam Mini Chat: {e}")

    root.mainloop()

# Khởi chạy ứng dụng
print("Consolog: Ứng dụng khởi chạy, hiển thị splash screen.")
show_splash_screen()