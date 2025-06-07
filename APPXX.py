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

# Từ điển ngôn ngữ
languages = {
    "vi": {
        "title": "Công cụ Tự động Telegram",
        "setting": "⚙️ Setting",
        "close_telegram": "❌ Đóng All Telegram",
        "arrange_telegram": "🟣 Sắp xếp Telegram",
        "log_label": "Tiến trình:",
        "telegram_path_label": "Đường dẫn Telegram:",
        "lang_select_title": "Chọn ngôn ngữ",
        "lang_vi": "Tiếng Việt",
        "lang_en": "English",
        "lang_zh": "中文",
        "msg_error_path": "Đường dẫn không hợp lệ!",
        "close_result": "Đóng All Telegram:\nĐã đóng: {closed}\nLỗi: {errors}",
        "arrange_result": "Đã sắp xếp {count} cửa sổ Telegram.",
        "close_result_title": "Kết quả đóng",
        "save_telegram_path": "💾 Lưu Telegram Path"
    },
    "en": {
        "title": "Telegram Auto Tool",
        "setting": "⚙️ Setting",
        "close_telegram": "❌ Close All Telegram",
        "arrange_telegram": "🟣 Arrange Telegram",
        "log_label": "Log:",
        "telegram_path_label": "Telegram Path:",
        "lang_select_title": "Select Language",
        "lang_vi": "Tiếng Việt",
        "lang_en": "English",
        "lang_zh": "中文",
        "msg_error_path": "Invalid path!",
        "close_result": "Close All Telegram:\nClosed: {closed}\nErrors: {errors}",
        "arrange_result": "Arranged {count} Telegram windows.",
        "close_result_title": "Close Result",
        "save_telegram_path": "💾 Save Telegram Path"
    },
    "zh": {
        "title": "Telegram 自动工具",
        "setting": "⚙️ Setting",
        "close_telegram": "❌ 关闭所有 Telegram",
        "arrange_telegram": "🟣 排列 Telegram",
        "log_label": "Log:",
        "telegram_path_label": "Telegram Path:",
        "lang_select_title": "Select Language",
        "lang_vi": "Tiếng Việt",
        "lang_en": "English",
        "lang_zh": "中文",
        "msg_error_path": "Invalid path!",
        "close_result": "Close All Telegram:\nClosed: {closed}\nErrors: {errors}",
        "arrange_result": "Arranged {count} Telegram windows.",
        "close_result_title": "Close Result",
        "save_telegram_path": "💾 Save Telegram Path"
    }
}

lang = {}

# Kiểm tra thư viện psutil
if not psutil:
    print("Consolog: Cảnh báo - psutil chưa được cài đặt! Vui lòng cài bằng 'pip install psutil' để check live qua PID.")

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

# Kiểm tra cập nhật
def check_for_updates():
    print("Consolog: Kiểm tra cập nhật phiên bản...")
    try:
        url = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/releases/latest"
        response = requests.get(url)
        if response.status_code == 200:
            release_info = response.json()
            latest_version = release_info["tag_name"].lstrip("v")
            print(f"Consolog: Phiên bản mới nhất từ GitHub: {latest_version}")
            if version.parse(latest_version) > version.parse(CURRENT_VERSION):
                log_message(lang.get("update_available").format(version=latest_version))
                if messagebox.askyesno("Cập nhật", lang.get("update_available").format(version=latest_version)):
                    print("Consolog [UPDATE]: Người dùng chọn cập nhật phiên bản mới.")
                    assets = release_info.get("assets", [])
                    download_url = None
                    for asset in assets:
                        if asset["name"].lower().endswith(".exe"):
                            download_url = asset["browser_download_url"]
                            break
                    if not download_url and assets:
                        download_url = assets[0]["browser_download_url"]
                    if download_url:
                        print(f"Consolog [UPDATE]: Bắt đầu tải file cập nhật từ {download_url}")
                        download_update_with_progress(download_url)
                    else:
                        log_message("Không tìm thấy file cập nhật trên GitHub.")
                        print("Consolog [UPDATE ERROR]: Không tìm thấy asset cập nhật.")
                else:
                    print("Consolog [UPDATE]: Người dùng không cập nhật.")
            else:
                log_message(lang.get("no_updates"))
                print("Consolog: Bạn đang dùng phiên bản mới nhất.")
        else:
            log_message(lang.get("update_error"))
            print("Consolog: Lỗi kiểm tra cập nhật.")
    except Exception as e:
        log_message(f"Lỗi kiểm tra cập nhật: {e}")
        print(f"Consolog [ERROR]: Lỗi kiểm tra cập nhật: {e}")

# Tải cập nhật với thanh tiến trình
def download_update_with_progress(download_url):
    local_filename = download_url.split("/")[-1]
    print(f"Consolog [UPDATE]: Đang tải xuống file: {local_filename}")
    progress_win = tk.Toplevel(root)
    progress_win.title("Đang tải cập nhật")
    progress_win.geometry("550x130")

    style = ttk.Style(progress_win)
    style.configure("Custom.Horizontal.TProgressbar", troughcolor="white", background="blue", thickness=20)

    tk.Label(progress_win, text=f"Đang tải: {local_filename}").pack(pady=5)
    progress_var = tk.DoubleVar(value=0)
    progress_bar = ttk.Progressbar(progress_win, variable=progress_var, maximum=100, length=500, style="Custom.Horizontal.TProgressbar")
    progress_bar.pack(pady=5)
    percent_label = tk.Label(progress_win, text="0%")
    percent_label.pack(pady=5)
    progress_win.update()

    try:
        response = requests.get(download_url, stream=True)
        total_length = response.headers.get('content-length')
        if total_length is None:
            log_message("Không xác định được kích thước file cập nhật.")
            print("Consolog [UPDATE ERROR]: Không xác định được content-length.")
            progress_win.destroy()
            return
        total_length = int(total_length)
        downloaded = 0
        with open(local_filename, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    percent = (downloaded / total_length) * 100
                    progress_var.set(percent)
                    percent_label.config(text=f"{int(percent)}%")
                    progress_win.update_idletasks()

        progress_win.destroy()
        notify_win = tk.Toplevel(root)
        notify_win.title("Tải cập nhật thành công")
        tk.Label(notify_win, text=f"Đã tải xong {local_filename}").pack(pady=10)

        def open_update_folder():
            folder = os.path.abspath(os.getcwd())
            try:
                os.startfile(folder)
            except Exception as e:
                log_message(f"Lỗi mở thư mục: {e}")

        tk.Button(notify_win, text="Mở vị trí file cập nhật", command=open_update_folder).pack(pady=5)
        tk.Button(notify_win, text="Close", command=notify_win.destroy).pack(pady=5)
        print("Consolog [UPDATE]: Tải về cập nhật hoàn tất.")
    except Exception as e:
        log_message(f"Failed to download update: {e}")
        print(f"Consolog [UPDATE ERROR]: Lỗi tải cập nhật: {e}")
        progress_win.destroy()

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

# Chọn ngôn ngữ
def select_language():
    lang_window = tk.Tk()
    lang_window.title(languages["en"]["lang_select_title"])
    center_window(lang_window, 400, 200)

    tk.Label(lang_window, text="Select Language / 选择语言 / Chọn ngôn ngữ:", font=("Arial Unicode MS", 12)).pack(pady=10)
    language_var = tk.StringVar(value="en")
    for code in ["vi", "en", "zh"]:
        tk.Radiobutton(
            lang_window,
            text=languages[code]["lang_" + code],
            variable=language_var,
            value=code,
            font=("Arial Unicode MS", 10)
        ).pack(anchor="w", padx=20)

    tk.Button(lang_window, text="OK", command=lambda: set_language(language_var, lang_window), font=("Arial Unicode MS", 10)).pack(pady=10)
    lang_window.mainloop()

# Thiết lập ngôn ngữ
def set_language(language_var, window):
    global lang
    selected = language_var.get()
    lang = languages[selected]
    window.destroy()
    print("Consolog: Người dùng chọn ngôn ngữ xong, khởi tạo giao diện chính.")
    init_main_ui()

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
    print("Consolog: Splash screen kết thúc, hiển thị giao diện chọn ngôn ngữ.")
    select_language()

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
    tk.Button(frame_buttons, text=lang["arrange_telegram"], command=lambda: arrange_telegram_windows(arrange_width, arrange_height), width=18).grid(row=0, column=1, padx=5, pady=5)
    tk.Button(frame_buttons, text=lang["setting"], command=open_settings, width=18).grid(row=0, column=2, padx=5, pady=5)

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