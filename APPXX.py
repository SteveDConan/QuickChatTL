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
CURRENT_VERSION = "1.05"
GITHUB_USER = "nunerit"
GITHUB_REPO = "TelegramAuto"
VERSION_INFO = "Version 1.0.5 - Copyright SAMADS"
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
        "title": "Công cụ Tự động Telegram TData",
        "choose_folder": "Chọn thư mục",
        "save_path": "💾 Lưu đường dẫn",
        "login_all": "🔐 Telethon",
        "auto_it": "🤖 AutoIT",
        "check_live": "🔍 Check live",
        "setting": "⚙️ Setting",
        "copy_telegram": "📋 Copy Telegram Portable",
        "open_telegram": "🟢 Mở Telegram Copies",
        "close_telegram": "❌ Đóng All Telegram",
        "arrange_telegram": "🟣 Sắp xếp Telegram",
        "check_update": "🔄 Check for Updates",
        "stats_label": "Bảng thống kê thư mục con:",
        "account_summary": "Thống kê tài khoản:",
        "logged_accounts": "Tài khoản đã đăng nhập:",
        "log_label": "Tiến trình:",
        "telegram_path_label": "Đường dẫn Telegram:",
        "lang_select_title": "Chọn ngôn ngữ",
        "lang_vi": "Tiếng Việt",
        "lang_en": "English",
        "lang_zh": "中文",
        "msg_saved_path": "Đã lưu đường dẫn vào máy!",
        "msg_error_path": "Đường dẫn không hợp lệ!",
        "msg_copy_result": "Kết quả Copy",
        "msg_open_result": "Kết quả mở Telegram",
        "copy_success": "Copy telegram.exe thành công cho {phone}",
        "copy_skip": "{phone} đã có telegram.exe, bỏ qua.",
        "close_result": "Đóng All Telegram:\nĐã đóng: {closed}\nLỗi: {errors}",
        "arrange_result": "Đã sắp xếp {count} cửa sổ Telegram.",
        "update_available": "Phiên bản {version} có sẵn. Bạn có muốn cập nhật không?",
        "no_updates": "Bạn đã có phiên bản mới nhất.",
        "update_error": "Lỗi kiểm tra cập nhật.",
        "copy_inactive": "Copy Tdata không hoạt động",
        "delete_inactive": "Xóa Tdata không hoạt động",
        "copy_table": "Copy table",
        "not_checked": "Chưa check",
        "checking": "Đang check",
        "completed": "Hoàn thành",
        "exe_not_found": "Không tìm thấy exe",
        "not_active": "Không hoạt động",
        "live": "Live",
        "stt": "STT",
        "check_status": "Trạng thái check",
        "live_status": "Trạng thái Live",
        "start": "Bắt đầu",
        "pause": "Tạm dừng",
        "confirm": "Xác nhận",
        "check_live_title": "Check live - Danh sách TData",
        "invalid_source_exe": "Source telegram.exe không hợp lệ!",
        "close_result_title": "Kết quả đóng",
        "save_telegram_path": "💾 Lưu Telegram Path"
    },
    "en": {
        "title": "Telegram TData Auto Tool",
        "choose_folder": "Choose Folder",
        "save_path": "💾 Save Path",
        "login_all": "🔐 Telethon",
        "auto_it": "🤖 AutoIT",
        "check_live": "🔍 Check live",
        "setting": "⚙️ Setting",
        "copy_telegram": "📋 Copy Telegram Portable",
        "open_telegram": "🟢 Open Telegram Copies",
        "close_telegram": "❌ Close All Telegram",
        "arrange_telegram": "🟣 Arrange Telegram",
        "check_update": "🔄 Check for Updates",
        "stats_label": "Folder Statistics:",
        "account_summary": "Account Summary:",
        "logged_accounts": "Logged In Accounts:",
        "log_label": "Log:",
        "telegram_path_label": "Telegram Path:",
        "lang_select_title": "Select Language",
        "lang_vi": "Tiếng Việt",
        "lang_en": "English",
        "lang_zh": "中文",
        "msg_saved_path": "Path saved successfully!",
        "msg_error_path": "Invalid path!",
        "msg_copy_result": "Copy Result",
        "msg_open_result": "Telegram Open Result",
        "copy_success": "Copied telegram.exe successfully for {phone}",
        "copy_skip": "{phone} already has telegram.exe, skipped.",
        "close_result": "Close All Telegram:\nClosed: {closed}\nErrors: {errors}",
        "arrange_result": "Arranged {count} Telegram windows.",
        "update_available": "Version {version} is available. Do you want to update?",
        "no_updates": "You already have the latest version.",
        "update_error": "Error checking for updates.",
        "copy_inactive": "Copy Inactive TData",
        "delete_inactive": "Delete Inactive TData",
        "copy_table": "Copy table",
        "not_checked": "Not checked",
        "checking": "Checking",
        "completed": "Completed",
        "exe_not_found": "Exe not found",
        "not_active": "Not active",
        "live": "Live",
        "stt": "No.",
        "check_status": "Check Status",
        "live_status": "Live Status",
        "start": "Start",
        "pause": "Pause",
        "confirm": "Confirm",
        "check_live_title": "Check live - TData List",
        "invalid_source_exe": "Invalid source telegram.exe!",
        "close_result_title": "Close Result",
        "save_telegram_path": "💾 Save Telegram Path"
    },
    "zh": {
        "title": "Telegram TData 自动工具",
        "choose_folder": "选择文件夹",
        "save_path": "💾 保存路径",
        "login_all": "🔐 Telethon",
        "auto_it": "🤖 AutoIT",
        "check_live": "🔍 Check live",
        "setting": "⚙️ Setting",
        "copy_telegram": "📋 复制 Telegram Portable",
        "open_telegram": "🟢 打开 Telegram 副本",
        "close_telegram": "❌ 关闭所有 Telegram",
        "arrange_telegram": "🟣 排列 Telegram",
        "check_update": "🔄 检查更新",
        "stats_label": "Folder Statistics:",
        "account_summary": "Account Summary:",
        "logged_accounts": "Logged In Accounts:",
        "log_label": "Log:",
        "telegram_path_label": "Telegram Path:",
        "lang_select_title": "Select Language",
        "lang_vi": "Tiếng Việt",
        "lang_en": "English",
        "lang_zh": "中文",
        "msg_saved_path": "Path saved successfully!",
        "msg_error_path": "Invalid path!",
        "msg_copy_result": "Copy Result",
        "msg_open_result": "Telegram Open Result",
        "copy_success": "Copied telegram.exe successfully for {phone}",
        "copy_skip": "{phone} already has telegram.exe, skipped.",
        "close_result": "Close All Telegram:\nClosed: {closed}\nErrors: {errors}",
        "arrange_result": "Arranged {count} Telegram windows.",
        "update_available": "Version {version} is available. Do you want to update?",
        "no_updates": "You already have the latest version.",
        "update_error": "Error checking for updates.",
        "copy_inactive": "Copy Inactive TData",
        "delete_inactive": "Delete Inactive TData",
        "copy_table": "Copy table",
        "not_checked": "Not checked",
        "checking": "Checking",
        "completed": "Completed",
        "exe_not_found": "Exe not found",
        "not_active": "Not active",
        "live": "Live",
        "stt": "No.",
        "check_status": "Check Status",
        "live_status": "Live Status",
        "start": "Start",
        "pause": "Pause",
        "confirm": "Confirm",
        "check_live_title": "Check live - TData List",
        "invalid_source_exe": "Invalid source telegram.exe!",
        "close_result_title": "Close Result",
        "save_telegram_path": "💾 Save Telegram Path"
    }
}

lang = {}

# Kiểm tra thư viện psutil
if not psutil:
    print("Consolog: Cảnh báo - psutil chưa được cài đặt! Vui lòng cài bằng 'pip install psutil' để check live qua PID.")

# Hàm cảnh báo trước khi check live
def warn_check_live():
    warning_msg = (
        "【Tiếng Việt】: Để đảm bảo tính năng Check live hoạt động chính xác và hiệu quả, vui lòng đóng tất cả các phiên bản Telegram đang chạy trên máy tính của bạn. Bạn có muốn đóng chúng ngay bây giờ?\n"
        "【English】: To ensure the Check live feature works accurately and efficiently, please close all running Telegram instances on your computer. Would you like to close them now?\n"
        "【中文】: 为了确保 'Check live' 功能准确高效地运行，请关闭您电脑上所有正在运行的 Telegram 程序。您是否希望立即关闭它们？"
    )
    res = messagebox.askyesno("Cảnh báo", warning_msg)
    if res:
        close_all_telegram_threaded()
    check_live_window()

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

# Sắp xếp cửa sổ Telegram
def arrange_telegram_windows(custom_width=500, custom_height=504, for_check_live=False):
    print(f"Consolog: Sắp xếp cửa sổ Telegram với kích thước {custom_width}x{custom_height}... For check live: {for_check_live}")
    my_hwnd = root.winfo_id()
    handles = []
    seen_pids = set()

    @ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_int, ctypes.c_int)
    def enum_callback(hwnd, lParam):
        if hwnd == my_hwnd:
            return True
        if user32.IsWindowVisible(hwnd):
            pid = ctypes.c_ulong()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            process_name = ""
            try:
                if psutil:
                    process = psutil.Process(pid.value)
                    process_name = process.name()
            except:
                pass
            if process_name.lower() == "telegram.exe":
                if for_check_live:
                    handles.append(hwnd)
                    print(f"Consolog: Thêm cửa sổ HWND {hwnd} từ PID {pid.value} (check live mode)")
                else:
                    if pid.value not in seen_pids:
                        seen_pids.add(pid.value)
                        handles.append(hwnd)
                        print(f"Consolog: Thêm cửa sổ HWND {hwnd} từ PID {pid.value}")
        return True

    user32.EnumWindows(enum_callback, 0)
    n = len(handles)
    print(f"Consolog: Tìm thấy {n} cửa sổ Telegram.")
    if n == 0:
        log_message("Không tìm thấy cửa sổ Telegram nào.")
        return

    screen_width = user32.GetSystemMetrics(0)
    screen_height = user32.GetSystemMetrics(1)
    SWP_NOZORDER = 0x0004
    SWP_SHOWWINDOW = 0x0040

    if for_check_live:
        max_cols = screen_width // custom_width
        max_rows = screen_height // custom_height
        if max_cols < 1:
            max_cols = 1
        if max_rows < 1:
            max_rows = 1
        capacity = max_cols * max_rows

        if n <= capacity:
            for index, hwnd in enumerate(handles):
                row = index // max_cols
                col = index % max_cols
                x = col * custom_width
                y = row * custom_height
                user32.SetWindowPos(hwnd, None, x, y, custom_width, custom_height, SWP_NOZORDER | SWP_SHOWWINDOW)
                print(f"Consolog: Di chuyển cửa sổ HWND {hwnd} đến vị trí ({x}, {y})")
        else:
            adjusted_width = screen_width // max_cols
            adjusted_height = screen_height // ((n + max_cols - 1) // max_cols)
            for index, hwnd in enumerate(handles):
                row = index // max_cols
                col = index % max_cols
                x = col * adjusted_width
                y = row * adjusted_height
                user32.SetWindowPos(hwnd, None, x, y, adjusted_width, adjusted_height, SWP_NOZORDER | SWP_SHOWWINDOW)
                print(f"Consolog: Di chuyển và thu nhỏ cửa sổ HWND {hwnd} đến vị trí ({x}, {y}) với kích thước {adjusted_width}x{adjusted_height}")

        RDW_INVALIDATE = 0x1
        RDW_UPDATENOW = 0x100
        RDW_ALLCHILDREN = 0x80
        for hwnd in handles:
            user32.RedrawWindow(hwnd, None, None, RDW_INVALIDATE | RDW_UPDATENOW | RDW_ALLCHILDREN)
            time.sleep(0.25)
    else:
        max_cols = screen_width // custom_width
        max_rows = screen_height // custom_height
        if max_cols < 1:
            max_cols = 1
        if max_rows < 1:
            max_rows = 1
        capacity = max_cols * max_rows

        if n <= capacity:
            for index, hwnd in enumerate(handles):
                row = index // max_cols
                col = index % max_cols
                x = col * custom_width
                y = row * custom_height
                user32.SetWindowPos(hwnd, None, x, y, custom_width, custom_height, SWP_NOZORDER | SWP_SHOWWINDOW)
                time.sleep(0.25)
                print(f"Consolog: Di chuyển cửa sổ HWND {hwnd} đến vị trí ({x}, {y})")
        else:
            offset_x = 30
            offset_y = 30
            for index, hwnd in enumerate(handles):
                x = (index % max_cols) * offset_x
                y = (index % max_rows) * offset_y
                if x + custom_width > screen_width:
                    x = screen_width - custom_width
                if y + custom_height > screen_height:
                    y = screen_height - custom_height
                user32.SetWindowPos(hwnd, None, x, y, custom_width, custom_height, SWP_NOZORDER | SWP_SHOWWINDOW)
                time.sleep(0.25)
                print(f"Consolog: (Cascade) Di chuyển cửa sổ HWND {hwnd} đến vị trí ({x}, {y})")

    log_message(lang["arrange_result"].format(count=n))

# Ghi log
def log_message(msg):
    text_log.insert(tk.END, msg + "\n")
    text_log.see(tk.END)
    print(f"[LOG] {msg}")

# Lưu đường dẫn thư mục
def save_path():
    folder_path = entry_path.get()
    print(f"Consolog: Lưu đường dẫn: {folder_path}")
    if os.path.exists(folder_path):
        config["folder_path"] = folder_path
        save_config(config)
        log_message(lang["msg_saved_path"])
        update_stats()
    else:
        log_message(lang["msg_error_path"])

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

# Tải đường dẫn đã lưu
def load_path():
    path = config.get("folder_path", "")
    print(f"Consolog: Đường dẫn tải được: {path}")
    return path

# Chọn thư mục
def browse_folder():
    folder_selected = filedialog.askdirectory()
    print(f"Consolog: Người dùng chọn folder: {folder_selected}")
    entry_path.delete(0, tk.END)
    entry_path.insert(0, folder_selected)

# Cập nhật thống kê thư mục
def update_stats():
    folder_path = entry_path.get()
    if not os.path.exists(folder_path):
        return
    try:
        subfolders = [d for d in os.listdir(folder_path) if os.path.isdir(os.path.join(folder_path, d))]
    except Exception as e:
        log_message(f"Không thể đọc thư mục: {e}")
        return
    info_list = []
    for sub in subfolders:
        sub_path = os.path.join(folder_path, sub)
        tdata_count = sum(
            1 for item in os.listdir(sub_path)
            if item.lower() == 'tdata' and os.path.isdir(os.path.join(sub_path, item))
        )
        info_list.append(f"- {sub}: có {tdata_count} tdata folder(s)")
    info_text = "\n".join(info_list) if info_list else "Không có thư mục con nào."
    text_stats.delete("1.0", tk.END)
    text_stats.insert(tk.END, info_text)
    print("Consolog: Cập nhật stats thành công.")

# Lấy danh sách thư mục TData
def get_tdata_folders(main_dir):
    if not os.path.exists(main_dir):
        return []
    folders = [
        os.path.join(main_dir, f) for f in os.listdir(main_dir)
        if os.path.isdir(os.path.join(main_dir, f))
    ]
    print(f"Consolog: Tìm thấy {len(folders)} thư mục TData trong {main_dir}")
    return folders

# Mở Telegram với TData
def open_telegram_with_tdata(tdata_folder):
    telegram_exe = os.path.join(tdata_folder, "telegram.exe")
    tdata_sub = os.path.join(tdata_folder, "tdata")
    print(f"Consolog: Mở telegram từ folder: {tdata_folder}")
    if not os.path.exists(telegram_exe):
        log_message(f"Không tìm thấy telegram.exe tại {telegram_exe}")
        return None
    if not os.path.exists(tdata_sub):
        log_message(f"Không tìm thấy thư mục tdata tại {tdata_sub}")
        return None
    log_message(f"🟢 Đang mở {telegram_exe} (cwd={tdata_folder})")
    proc = subprocess.Popen([telegram_exe], cwd=tdata_folder)
    time.sleep(0.25)
    return proc

# Đóng ứng dụng
def on_closing():
    print("Consolog: Đóng ứng dụng...")
    root.destroy()

# Biến toàn cục cho Check Live
check_live_thread = None
check_live_pause_event = threading.Event()
check_live_status = {}
confirm_done = False
tdata_process_map = {}
TEMP_SCREENSHOT_FOLDER = None

# Load trạng thái Check Live từ file
def load_check_live_status_file():
    print("Consolog: Đang load trạng thái check live từ file...")
    if os.path.exists("check_live_status.txt"):
        try:
            with open("check_live_status.txt", "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if ": Check:" in line and "| Live:" in line:
                        name_part, rest = line.split(": Check:", 1)
                        tdata_name = name_part.strip()
                        if "| Live:" in rest:
                            check_part, live_part = rest.split("| Live:", 1)
                            check_live_status[tdata_name] = {
                                "check": check_part.strip(),
                                "live": live_part.strip()
                            }
            print("Consolog: Đã load trạng thái check live thành công.")
        except Exception as e:
            print(f"Consolog [ERROR]: Lỗi đọc file check_live_status.txt: {e}")

# Lưu trạng thái Check Live vào file
def save_check_live_status_file():
    print("Consolog: Lưu trạng thái check live vào file...")
    try:
        with open("check_live_status.txt", "w", encoding="utf-8") as f:
            for key, val in check_live_status.items():
                f.write(f"{key}: Check: {val['check']} | Live: {val['live']}\n")
        print("Consolog: Lưu trạng thái thành công.")
    except Exception as e:
        print(f"Consolog [ERROR]: Lỗi ghi file check_live_status.txt: {e}")

# So sánh ảnh chụp với marker
def compare_screenshot_with_marker(screenshot, marker_image, threshold=20):
    print("Consolog: So sánh ảnh chụp với marker image...")
    if screenshot.size != marker_image.size:
        marker_image = marker_image.resize(screenshot.size)
    diff = ImageChops.difference(screenshot, marker_image)
    h = diff.histogram()
    sq = (value * ((idx % 256) ** 2) for idx, value in enumerate(h))
    sum_sq = sum(sq)
    rms = math.sqrt(sum_sq / (screenshot.size[0] * screenshot.size[1]))
    print(f"Consolog: Giá trị RMS = {rms}")
    return rms < threshold

# Hiển thị popup chọn marker image
def show_marker_selection_popup(screenshot_paths):
    print("Consolog: Hiển thị popup chọn marker image...")
    popup = tk.Toplevel(root)
    popup.title("Chọn marker image")
    center_window(popup, 800, 600)
    instruction = tk.Label(
        popup,
        text="Hãy chỉ ra dấu hiệu nhận biết tài khoản telegram đã chết bằng cách chọn ảnh từ danh sách bên trái",
        font=("Arial Unicode MS", 10, "bold"),
        wraplength=780
    )
    instruction.pack(pady=10)

    selected_path = {"path": None}
    frame = tk.Frame(popup)
    frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    listbox = tk.Listbox(frame, width=40)
    listbox.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)
    for path in screenshot_paths:
        listbox.insert(tk.END, os.path.basename(path))

    preview_label = tk.Label(frame)
    preview_label.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)

    def on_select(event):
        selection = listbox.curselection()
        if selection:
            index = selection[0]
            file_path = screenshot_paths[index]
            selected_path["path"] = file_path
            try:
                img = Image.open(file_path)
                img.thumbnail((400, 400))
                photo = ImageTk.PhotoImage(img)
                preview_label.config(image=photo)
                preview_label.image = photo
            except Exception as e:
                print(f"Consolog [ERROR]: Lỗi mở ảnh {file_path}: {e}")

    listbox.bind("<<ListboxSelect>>", on_select)

    def on_confirm():
        if not selected_path["path"]:
            messagebox.showwarning("Warning", "Vui lòng chọn một ảnh!")
            return
        if os.path.exists(MARKER_IMAGE_PATH):
            try:
                os.remove(MARKER_IMAGE_PATH)
                print("Consolog: Xóa file marker cũ.")
            except Exception as e:
                print(f"Consolog [ERROR]: Lỗi xóa file marker cũ: {e}")
        try:
            shutil.copy(selected_path["path"], MARKER_IMAGE_PATH)
            print(f"Consolog: Đã lưu marker image tại {MARKER_IMAGE_PATH}")
        except Exception as e:
            print(f"Consolog [ERROR]: Lỗi lưu marker image: {e}")
        popup.destroy()

    confirm_button = tk.Button(popup, text="Xác nhận", command=on_confirm)
    confirm_button.pack(pady=10)
    popup.transient(root)
    popup.grab_set()
    root.wait_window(popup)

# Luồng so sánh ảnh
def screenshot_comparison_worker():
    print("Consolog: Luồng so sánh ảnh bắt đầu, chờ 2 giây...")
    time.sleep(2)
    captured_screenshots = {}

    for tdata_name, pid_list in tdata_process_map.items():
        print(f"Consolog: === BẮT ĐẦU XỬ LÝ TDATA: {tdata_name} ===")
        window_handle = None
        for pid in pid_list:
            print(f"Consolog: -> Đang lấy HWND cho PID={pid}")
            try:
                hwnd = get_window_handle_by_pid(int(pid))
                print(f"Consolog: get_window_handle_by_pid({pid}) => {hwnd}")
            except Exception as e:
                print(f"Consolog [ERROR]: Lỗi get_window_handle_by_pid: {e}")
                hwnd = None
            if hwnd:
                window_handle = hwnd
                print(f"Consolog: -> Đã tìm thấy HWND={window_handle} cho PID={pid}")
                break

        if window_handle:
            try:
                SW_RESTORE = 9
                user32.ShowWindow(window_handle, SW_RESTORE)
                user32.SetForegroundWindow(window_handle)
                print(f"Consolog: -> Đã gọi ShowWindow/SetForegroundWindow cho HWND={window_handle}")
                time.sleep(0.5)

                rect = wintypes.RECT()
                user32.GetWindowRect(window_handle, ctypes.byref(rect))
                w = rect.right - rect.left
                h = rect.bottom - rect.top
                print(f"Consolog: Kích thước cửa sổ: {w}x{h}")

                screenshot = capture_window(window_handle)
                if screenshot:
                    if TEMP_SCREENSHOT_FOLDER:
                        file_path = os.path.join(TEMP_SCREENSHOT_FOLDER, f"{tdata_name}_screenshot.png")
                        screenshot.save(file_path)
                        print(f"Consolog: Đã lưu ảnh chụp của {tdata_name} tại {file_path}")
                        captured_screenshots[tdata_name] = file_path
            except Exception as e:
                print(f"Consolog [ERROR]: Lỗi chụp ảnh cho {tdata_name}: {e}")
        else:
            print(f"Consolog: Không tìm thấy HWND cho {tdata_name}, đánh dấu not_active.")
            check_live_status[tdata_name]["live"] = lang["not_active"]
        cl_win.after(0, refresh_table_global)

    screenshot_paths = list(captured_screenshots.values())
    if screenshot_paths:
        print(f"Consolog: Đã chụp được {len(screenshot_paths)} ảnh, mở popup chọn marker.")
        show_marker_selection_popup(screenshot_paths)
    else:
        print("Consolog: Không có ảnh chụp nào để chọn marker.")

    marker_image = None
    if os.path.exists(MARKER_IMAGE_PATH):
        try:
            marker_image = Image.open(MARKER_IMAGE_PATH)
            print("Consolog: Đã mở file marker_image.png để so sánh.")
        except Exception as e:
            print(f"Consolog [ERROR]: Lỗi mở marker image: {e}")

    for tdata_name, file_path in captured_screenshots.items():
        if marker_image is not None:
            try:
                screenshot = Image.open(file_path)
                print(f"Consolog: So sánh ảnh {file_path} với marker...")
                is_similar = compare_screenshot_with_marker(screenshot, marker_image)
                if is_similar:
                    check_live_status[tdata_name]["live"] = lang["not_active"]
                    print(f"Consolog: {tdata_name} => not_active")
                else:
                    check_live_status[tdata_name]["live"] = lang["live"]
                    print(f"Consolog: {tdata_name} => live")
            except Exception as e:
                print(f"Consolog [ERROR]: Lỗi so sánh ảnh cho {tdata_name}: {e}")
        else:
            check_live_status[tdata_name]["live"] = lang["live"]
            print(f"Consolog: Không có marker, đặt mặc định {tdata_name} => live.")

        cl_win.after(0, refresh_table_global)

    print("Consolog: So sánh ảnh hoàn thành.")
    cl_win.after(0, lambda: log_message("Đã hoàn thành kiểm tra qua so sánh hình ảnh."))

# Cửa sổ Check Live
def check_live_window():
    global cl_win, refresh_table_global
    cl_win = tk.Toplevel(root)
    cl_win.title(lang["check_live_title"])
    center_window(cl_win, 1200, 500)

    size_frame = tk.Frame(cl_win)
    size_frame.pack(pady=5)
    tk.Label(size_frame, text="Window Width:").grid(row=0, column=0, padx=5)
    entry_width = tk.Entry(size_frame, width=6)
    entry_width.insert(0, str(arrange_width))
    entry_width.grid(row=0, column=1, padx=5)
    tk.Label(size_frame, text="Window Height:").grid(row=0, column=2, padx=5)
    entry_height = tk.Entry(size_frame, width=6)
    entry_height.insert(0, str(arrange_height))
    entry_height.grid(row=0, column=3, padx=5)

    load_check_live_status_file()
    columns = ("stt", "tdata", "check_status", "live_status")
    tree = ttk.Treeview(cl_win, columns=columns, show="headings", height=15)
    tree.heading("stt", text=lang["stt"])
    tree.heading("tdata", text="TData")
    tree.heading("check_status", text=lang["check_status"])
    tree.heading("live_status", text=lang["live_status"])
    tree.column("stt", width=50, anchor="center")
    tree.column("tdata", width=200, anchor="center")
    tree.column("check_status", width=200, anchor="center")
    tree.column("live_status", width=200, anchor="center")
    tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    def refresh_table():
        tree.delete(*tree.get_children())
        tdata_dir = entry_path.get()
        folders = get_tdata_folders(tdata_dir)
        for idx, folder in enumerate(folders, start=1):
            tdata_name = os.path.basename(folder)
            if tdata_name not in check_live_status:
                check_live_status[tdata_name] = {"check": lang["not_checked"], "live": lang["not_checked"]}
            row_data = check_live_status[tdata_name]
            item = tree.insert("", tk.END, values=(idx, tdata_name, row_data["check"], row_data["live"]))
            if row_data["check"] == lang["checking"]:
                tree.item(item, tags=("checking",))
        tree.tag_configure("checking", background="yellow")

    refresh_table_global = refresh_table
    refresh_table()

    def switch_button_states(running):
        if running:
            btn_start.config(state=tk.DISABLED)
            btn_pause.config(state=tk.NORMAL)
        else:
            btn_start.config(state=tk.NORMAL)
            btn_pause.config(state=tk.DISABLED)

    def start_check_live():
        global check_live_thread, tdata_process_map, TEMP_SCREENSHOT_FOLDER
        tdata_process_map = {}
        print("Consolog: Bắt đầu quy trình check live...")
        TEMP_SCREENSHOT_FOLDER = os.path.join(os.getcwd(), "temp_screenshots")
        if os.path.exists(TEMP_SCREENSHOT_FOLDER):
            shutil.rmtree(TEMP_SCREENSHOT_FOLDER)
        os.makedirs(TEMP_SCREENSHOT_FOLDER, exist_ok=True)
        print(f"Consolog: Tạo thư mục tạm để lưu ảnh chụp tại {TEMP_SCREENSHOT_FOLDER}")

        if check_live_thread and check_live_pause_event.is_set():
            check_live_pause_event.clear()
            switch_button_states(running=True)
            return

        switch_button_states(running=True)

        def worker():
            tdata_dir = entry_path.get()
            folders = get_tdata_folders(tdata_dir)
            for folder in folders:
                while check_live_pause_event.is_set():
                    time.sleep(0.3)
                tdata_name = os.path.basename(folder)
                check_live_status[tdata_name] = {
                    "check": lang["checking"],
                    "live": check_live_status[tdata_name].get("live", lang["not_checked"])
                }
                cl_win.after(0, refresh_table_global)

                exe_path = os.path.join(folder, "telegram.exe")
                if os.path.exists(exe_path):
                    print(f"Consolog: Mở telegram cho TData {tdata_name}")
                    proc = subprocess.Popen([exe_path])
                    pid = proc.pid
                    if tdata_name not in tdata_process_map:
                        tdata_process_map[tdata_name] = []
                    tdata_process_map[tdata_name].append(pid)
                    print(f"Consolog: Lưu PID {pid} cho TData {tdata_name}")
                    time.sleep(0.25)
                    check_live_status[tdata_name]["check"] = lang["completed"]
                else:
                    check_live_status[tdata_name]["check"] = lang["exe_not_found"]

                cl_win.after(0, refresh_table_global)

            try:
                custom_width = int(entry_width.get())
                custom_height = int(entry_height.get())
            except:
                custom_width, custom_height = arrange_width, arrange_height
            print(f"Consolog: Sử dụng kích thước cửa sổ: {custom_width}x{custom_height}")
            config["arrange_width"] = custom_width
            config["arrange_height"] = custom_height
            save_config(config)
            arrange_telegram_windows(custom_width, custom_height, for_check_live=True)
            threading.Thread(target=screenshot_comparison_worker, daemon=True).start()
            global check_live_thread
            check_live_thread = None

        check_live_thread = threading.Thread(target=worker, daemon=True)
        check_live_thread.start()

    def pause_check_live():
        print("Consolog: Tạm dừng quy trình check live.")
        check_live_pause_event.set()
        switch_button_states(running=False)

    def confirm_check_live():
        print("Consolog: Xác nhận trạng thái check live và lưu vào file.")
        save_check_live_status_file()
        log_message("Đã lưu trạng thái check live vào file check_live_status.txt")
        global confirm_done
        confirm_done = True
        btn_copy_inactive.config(state=tk.NORMAL)
        btn_delete_inactive.config(state=tk.NORMAL)
        btn_copy_table.config(state=tk.NORMAL)
        global TEMP_SCREENSHOT_FOLDER
        if TEMP_SCREENSHOT_FOLDER and os.path.exists(TEMP_SCREENSHOT_FOLDER):
            shutil.rmtree(TEMP_SCREENSHOT_FOLDER)
            print(f"Consolog: Đã xóa thư mục tạm {TEMP_SCREENSHOT_FOLDER}")
            TEMP_SCREENSHOT_FOLDER = None

    def copy_table():
        if not confirm_done:
            log_message("Vui lòng bấm '" + lang["confirm"] + "' trước.")
            return
        table_text = ""
        for child in tree.get_children():
            values = tree.item(child, "values")
            table_text += "\t".join(str(v) for v in values) + "\n"
        root.clipboard_clear()
        root.clipboard_append(table_text)
        root.update()
        log_message("Đã copy toàn bộ nội dung bảng vào clipboard.")
        print("Consolog: Copy bảng check live thành công.")

    def copy_inactive():
        if not confirm_done:
            log_message("Vui lòng bấm '" + lang["confirm"] + "' trước.")
            return
        inactive_list = []
        for child in tree.get_children():
            values = tree.item(child, "values")
            if len(values) >= 4 and values[3] == lang["not_active"]:
                inactive_list.append(values[1])
        if not inactive_list:
            log_message("Không có TData nào ở trạng thái không hoạt động.")
            return
        text_inactive = "\n".join(inactive_list)
        print(f"Consolog: Copy danh sách TData không hoạt động: {text_inactive}")
        root.clipboard_clear()
        root.clipboard_append(text_inactive)
        root.update()
        log_message("Đã copy danh sách TData không hoạt động:\n" + text_inactive)

    def delete_inactive():
        if not confirm_done:
            log_message("Vui lòng bấm '" + lang["confirm"] + "' trước.")
            return
        print("Consolog: Đang xóa các TData không hoạt động...")
        auto_close_telegram()
        tdata_dir = entry_path.get()
        folders = get_tdata_folders(tdata_dir)
        deleted = []
        for folder in folders:
            tdata_name = os.path.basename(folder)
            if check_live_status.get(tdata_name, {}).get("live") == lang["not_active"]:
                normalized_folder = os.path.normpath(folder)
                if os.path.exists(normalized_folder):
                    try:
                        print(f"Consolog: Xóa TData không hoạt động: {normalized_folder}")
                        if send2trash:
                            send2trash(normalized_folder)
                        else:
                            shutil.rmtree(normalized_folder)
                        deleted.append(tdata_name)
                        check_live_status.pop(tdata_name, None)
                    except Exception as e:
                        log_message(f"Consolog [ERROR]: Lỗi xóa {normalized_folder}: {e}")
                else:
                    log_message(f"Consolog [ERROR]: Thư mục không tồn tại: {normalized_folder}")

        refresh_table_global()
        log_message(f"Đã xóa {len(deleted)} thư mục không hoạt động:\n" + ", ".join(deleted))
        save_check_live_status_file()
        print("Consolog: Xóa TData không hoạt động hoàn tất.")

    frame_buttons = tk.Frame(cl_win)
    frame_buttons.pack(pady=5)
    btn_start = tk.Button(frame_buttons, text=lang["start"], command=start_check_live, width=20)
    btn_pause = tk.Button(frame_buttons, text=lang["pause"], command=pause_check_live, width=20, state=tk.DISABLED)
    btn_confirm = tk.Button(frame_buttons, text=lang["confirm"], command=confirm_check_live, width=20)
    btn_copy_inactive = tk.Button(frame_buttons, text=lang["copy_inactive"], command=copy_inactive, width=25, state=tk.DISABLED)
    btn_delete_inactive = tk.Button(frame_buttons, text=lang["delete_inactive"], command=delete_inactive, width=25, state=tk.DISABLED)
    btn_copy_table = tk.Button(frame_buttons, text=lang["copy_table"], command=copy_table, width=20, state=tk.DISABLED)

    btn_start.grid(row=0, column=0, padx=5)
    btn_pause.grid(row=0, column=1, padx=5)
    btn_confirm.grid(row=0, column=2, padx=5)
    btn_copy_inactive.grid(row=0, column=3, padx=5)
    btn_delete_inactive.grid(row=0, column=4, padx=5)
    btn_copy_table.grid(row=0, column=5, padx=5)

# Cảnh báo AutoIT
def warn_auto_it():
    try:
        from sam_translate.sam_translate import destroy_sam_mini_chat
        destroy_sam_mini_chat()
        print("Consolog: Mini chat đã được đóng khi bật chức năng AutoIT.")
    except Exception as e:
        print(f"Consolog [WARNING]: Không thể đóng mini chat: {e}")
    warning_msg = (
        "【Tiếng Việt】: Trước khi khởi chạy AutoIT, kiểm tra trạng thái tài khoản Telegram để tối ưu hóa hiệu suất.\n"
        "【English】: Before initiating AutoIT, check Telegram accounts' status to optimize performance.\n"
        "【中文】: 在启动 AutoIT 之前，检查 Telegram 账户状态以优化性能。"
    )
    log_message(warning_msg)
    auto_it_function(root, entry_path, lang, get_tdata_folders)

# Mở các bản sao Telegram
def open_telegram_copies():
    def worker():
        results = []
        tdata_dir = entry_path.get()
        if not os.path.exists(tdata_dir):
            root.after(0, lambda: log_message(lang["msg_error_path"]))
            return
        tdata_folders = get_tdata_folders(tdata_dir)
        for folder in tdata_folders:
            exe_path = os.path.join(folder, "telegram.exe")
            if os.path.exists(exe_path):
                try:
                    subprocess.Popen([exe_path])
                    results.append(f"Mở thành công: {folder}")
                except Exception as e:
                    results.append(f"Lỗi mở {folder}: {e}")
            else:
                results.append(f"Không tìm thấy exe: {folder}")
            time.sleep(0.25)
        root.after(0, lambda: log_message("\n".join(results)))
        time.sleep(0.25)
        root.after(0, lambda: arrange_telegram_windows(arrange_width, arrange_height))
    threading.Thread(target=worker, daemon=True).start()

# Copy Telegram Portable
def copy_telegram_portable():
    print("Consolog: Đang copy telegram.exe cho các tài khoản...")
    tdata_dir = entry_path.get()
    if not os.path.exists(tdata_dir):
        log_message(lang["msg_error_path"])
        return
    tdata_folders = get_tdata_folders(tdata_dir)
    results = []
    copied = []
    skipped = []
    errors = []

    source_exe = telegram_path_entry.get()
    if not os.path.isfile(source_exe):
        log_message(lang["invalid_source_exe"])
        return

    for folder in tdata_folders:
        target_path = os.path.join(folder, "telegram.exe")
        phone = os.path.basename(folder)
        if not os.path.exists(target_path):
            try:
                shutil.copy(source_exe, target_path)
                copied.append(phone)
                log_message(f"Consolog: {lang['copy_success'].format(phone=phone)}")
            except Exception as e:
                errors.append(f"{phone}: {str(e)}")
                log_message(f"Consolog [ERROR]: Lỗi copy telegram.exe cho {phone}: {e}")
        else:
            skipped.append(phone)
            log_message(lang["copy_skip"].format(phone=phone))

    summary = f"Đã copy: {len(copied)}\nBỏ qua: {len(skipped)}\nLỗi: {len(errors)}\n"
    if copied:
        summary += "Đã copy: " + ", ".join(copied) + "\n"
    if skipped:
        summary += "Bỏ qua: " + ", ".join(skipped) + "\n"
    if errors:
        summary += "Lỗi: " + "; ".join(errors)

    log_message(summary)
    print("Consolog: Hoàn thành copy telegram.exe.")

# Đóng tất cả Telegram
def close_all_telegram():
    print("Consolog: Đang đóng tất cả tiến trình Telegram...")
    try:
        result = subprocess.run(["tasklist", "/FI", "IMAGENAME eq Telegram.exe", "/FO", "CSV"], capture_output=True, text=True)
        output = result.stdout.strip().splitlines()
        pids = []
        for line in output[1:]:
            parts = line.replace('"','').split(',')
            if len(parts) >= 2:
                pids.append(parts[1])
        closed = []
        errors = []
        for pid in pids:
            try:
                subprocess.run(["taskkill", "/F", "/PID", pid], capture_output=True, text=True)
                closed.append(pid)
                time.sleep(0.25)
            except Exception as e:
                errors.append(f"PID {pid}: {e}")
        summary = lang["close_result"].format(
            closed=", ".join(closed) if closed else "None",
            errors="; ".join(errors) if errors else "None"
        )
        log_message(summary)
        print("Consolog: Đóng tiến trình Telegram hoàn tất.")
    except Exception as e:
        log_message(f"Không thể đóng các tiến trình Telegram: {e}")

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

    startup_var = tk.BooleanVar(value=config.get("startup", False))
    tk.Checkbutton(popup, text="Khởi động cùng Windows", variable=startup_var).pack(pady=5)

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
            config["startup"] = startup_var.get()
            print("Consolog: Lưu cấu hình Settings")
            save_config(config)
            print("Consolog: Đã lưu cấu hình Setting")
            log_message("Đã lưu cấu hình!")
            popup.destroy()
            if config["startup"]:
                add_to_startup()
            else:
                remove_from_startup()
        except Exception as e:
            log_message(f"Giá trị không hợp lệ: {e}")
            print(f"Consolog [ERROR]: Lỗi lưu cấu hình Setting: {e}")

    btn_save = tk.Button(popup, text="Save", command=save_settings)
    btn_save.pack(pady=10)
    popup.transient(root)
    popup.grab_set()
    root.wait_window(popup)

# Thêm vào startup
def add_to_startup():
    try:
        import winshell
        startup_folder = winshell.startup()
        shortcut_path = os.path.join(startup_folder, "TelegramAuto.lnk")
        target = os.path.abspath(__file__)
        winshell.CreateShortcut(
            Path=shortcut_path,
            Target=target,
            Icon=(target, 0),
            Description="TelegramAuto Startup"
        )
        print("Consolog: Đã thêm ứng dụng vào startup.")
    except Exception as e:
        log_message(f"Lỗi khi thêm vào startup: {e}")

# Xóa khỏi startup
def remove_from_startup():
    try:
        import winshell
        startup_folder = winshell.startup()
        shortcut_path = os.path.join(startup_folder, "TelegramAuto.lnk")
        if os.path.exists(shortcut_path):
            os.remove(shortcut_path)
            print("Consolog: Đã xóa ứng dụng khỏi startup.")
    except Exception as e:
        log_message(f"Lỗi khi xóa khỏi startup: {e}")

# Căn giữa cửa sổ
def center_window(win, width, height):
    win.update_idletasks()
    screen_width = win.winfo_screenwidth()
    screen_height = win.winfo_screenheight()
    x = (screen_width - width) // 2
    y = (screen_height - height) // 2
    win.geometry(f"{width}x{height}+{x}+{y}")

# Load cấu hình marker
def load_marker_config():
    config = load_config()
    dont_ask = config.get("dont_ask", False)
    print(f"Consolog: Load marker config: dont_ask={dont_ask}")
    return {"dont_ask": dont_ask}

# Lưu cấu hình marker
def save_marker_config(marker_config):
    config["dont_ask"] = marker_config.get("dont_ask", False)
    save_config(config)
    print(f"Consolog: Lưu marker config: dont_ask={config['dont_ask']}")

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

    tk.Label(lang_window, text=VERSION_INFO, font=("Arial Unicode MS", 8)).pack(pady=5)
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
    global root, entry_path, text_stats, text_log, telegram_path_entry, DEFAULT_TELEGRAM_PATH, XAI_API_KEY, CHATGPT_API_KEY, LLM_API_KEY
    root = tk.Tk()
    root.title(lang["title"])
    center_window(root, 650, 800)

    default_font = tkFont.nametofont("TkDefaultFont")
    default_font.configure(family="Arial Unicode MS", size=10)
    root.option_add("*Font", default_font)

    threading.Thread(target=check_for_updates, daemon=True).start()

    print("Consolog: Kiểm tra Telegram Path từ màn hình chính thay vì Settings")
    tk.Label(root, text=lang["title"], font=("Arial Unicode MS", 14, "bold")).pack(pady=10)

    frame_path = tk.Frame(root)
    frame_path.pack(pady=5)
    entry_path = tk.Entry(frame_path, width=50)
    entry_path.pack(side=tk.LEFT, padx=5)
    tk.Button(frame_path, text=lang["choose_folder"], command=browse_folder).pack(side=tk.LEFT)

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

    tk.Button(root, text=lang["save_path"], command=save_path, width=20).pack(pady=5)

    frame_buttons = tk.Frame(root)
    frame_buttons.pack(pady=5)

    def warn_telethon():
        print("Consolog: Người dùng nhấn nút Telethon")
        log_message("Chức năng ẩn, vui lòng liên hệ admin!")

    tk.Button(frame_buttons, text=lang["login_all"], command=warn_telethon, width=18).grid(row=0, column=0, padx=5, pady=5)
    tk.Button(frame_buttons, text=lang["copy_telegram"], command=copy_telegram_portable, width=18).grid(row=0, column=1, padx=5, pady=5)
    tk.Button(frame_buttons, text=lang["open_telegram"], command=open_telegram_copies, width=18).grid(row=0, column=2, padx=5, pady=5)

    tk.Button(frame_buttons, text=lang["close_telegram"], command=close_all_telegram_threaded, width=18).grid(row=1, column=0, padx=5, pady=5)
    tk.Button(frame_buttons, text=lang["arrange_telegram"], command=lambda: arrange_telegram_windows(arrange_width, arrange_height), width=18).grid(row=1, column=1, padx=5, pady=5)
    tk.Button(frame_buttons, text=lang["auto_it"], command=warn_auto_it, width=18).grid(row=1, column=2, padx=5, pady=5)

    tk.Button(frame_buttons, text=lang["check_live"], command=warn_check_live, width=18).grid(row=2, column=0, padx=5, pady=5)
    tk.Button(frame_buttons, text=lang["setting"], command=open_settings, width=18).grid(row=2, column=1, padx=5, pady=5)
    tk.Button(frame_buttons, text=lang["check_update"], command=check_for_updates, width=18).grid(row=2, column=2, padx=5, pady=5)

    frame_stats = tk.Frame(root)
    frame_stats.pack(pady=10)
    tk.Label(frame_stats, text=lang["stats_label"]).pack()
    text_stats = tk.Text(frame_stats, width=70, height=10)
    text_stats.pack()

    frame_log = tk.Frame(root)
    frame_log.pack(pady=10)
    tk.Label(frame_log, text=lang["log_label"]).pack()
    text_log = tk.Text(frame_log, width=70, height=10)
    text_log.pack()

    saved_path = load_path()
    if saved_path:
        entry_path.insert(0, saved_path)
        update_stats()

    tk.Label(root, text=VERSION_INFO, font=("Arial Unicode MS", 8)).pack(side="bottom", fill="x", pady=5)
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