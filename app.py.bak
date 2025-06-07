# app.py

# Consolog: MÃ GỐC, ĐÃ TÁCH PHẦN MINI CHAT SANG FILE mini_chat.py
# Consolog: Giữ nguyên các phần khác để tránh lỗi ngoài ý muốn.

import os
import time
import shutil
import subprocess
import asyncio
import math
import ctypes
import threading
import re
import random
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
from tkinter import ttk
import tkinter.font as tkFont

from telethon.sync import TelegramClient
from telethon import functions, types, events
from telethon.errors import SessionPasswordNeededError, PhoneCodeInvalidError, PhoneCodeExpiredError

import requests
from distutils.version import LooseVersion

# Thư viện để chuyển vào Thùng rác
try:
    from send2trash import send2trash
except ImportError:
    send2trash = None

# Thư viện kiểm tra tiến trình còn chạy hay không
try:
    import psutil
except ImportError:
    psutil = None

# Thêm thư viện Pillow để xử lý hình ảnh
from PIL import Image, ImageChops, ImageTk

# Cần dùng ctypes.wintypes để lấy tọa độ cửa sổ
from ctypes import wintypes

# Import module AutoIT đã tách riêng
from autoit_module import auto_it_function

# ===== THÊM THƯ VIỆN BỔ SUNG CHO MINI CHAT =====
# Consolog: Đã chuyển các import mini chat sang mini_chat.py

# NEW: Giữ lại phần config key ChatGPT để open_settings() có thể truy cập
CHATGPT_API_KEY_FILE = "chatgpt_api_key.txt"
def load_chatgpt_api_key():
    if os.path.exists(CHATGPT_API_KEY_FILE):
        with open(CHATGPT_API_KEY_FILE, "r", encoding="utf-8") as f:
            return f.read().strip()
    return ""

def save_chatgpt_api_key(key):
    with open(CHATGPT_API_KEY_FILE, "w", encoding="utf-8") as f:
        f.write(key)

# Consolog: Giữ các biến này ở app.py vì open_settings() cũng cần
CHATGPT_API_KEY = load_chatgpt_api_key()

# NEW: Biến kiểm tra chế độ chỉ dịch (không gửi tin nhắn)
TRANSLATION_ONLY = True
print("Consolog: Chế độ 'chỉ dịch' được bật (TRANSLATION_ONLY=True).")

# NEW: Biến mặc định cho ngôn ngữ dịch của đối phương (default là tiếng Việt)
DEFAULT_TARGET_LANG = "vi"

# --- CẤU HÌNH BAN ĐẦU (DEFAULT) ---
CONFIG_FILE = "config.txt"
DEFAULT_TELEGRAM_PATH = r"C:\Users\SAM\AppData\Roaming\Telegram Desktop\Telegram.exe"
API_ID = 22379547
API_HASH = '9fc2845bde4b64a6a51320a8045c8178'
CURRENT_VERSION = "1.05"
GITHUB_USER = "nunerit"
GITHUB_REPO = "TelegramAuto"

VERSION_INFO = "Version 1.0.5 - Copyright SAMADS"

# File lưu kích thước cửa sổ
WINDOW_SIZE_FILE = "window_size.txt"

# --- CẤU HÌNH CHO MARKER IMAGE ---
MARKER_IMAGE_PATH = os.path.join(os.getcwd(), "marker_image.png")
MARKER_CONFIG_FILE = os.path.join(os.getcwd(), "marker_config.txt")  # Vẫn giữ lại nếu cần

# Các giá trị cấu hình cho sắp xếp cửa sổ (Custom Width/Height)
arrange_width = 500
arrange_height = 504

##########################################################################
# BỔ SUNG: Hàm lấy HWND theo PID để chụp chính xác cửa sổ Telegram
##########################################################################
user32 = ctypes.windll.user32

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
    if handles:
        return handles[0]
    return None

##########################################################################
# SỬA: Hàm capture_window để chụp full content (PrintWindow(hwnd, srcdc, 2))
##########################################################################
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

    from PIL import Image
    image = Image.frombuffer('RGBA', (width, height), buffer, 'raw', 'BGRA', 0, 1)

    gdi32.DeleteObject(bmp)
    gdi32.DeleteDC(srcdc)
    user32.ReleaseDC(hwnd, hwindc)

    return image

languages = {
    "vi": {
        "title": "Công cụ Tự động Telegram TData",
        "choose_folder": "Chọn thư mục",
        "save_path": "💾 Lưu đường dẫn",
        "login_all": "🔐 Telethon",
        "auto_it": "🤖 AutoIT",
        "check_live": "🔍 Check live",
        "report": "📝 Report",
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
        "msg_login_complete": "Quá trình đăng nhập cho tất cả các tài khoản đã hoàn tất.",
        "msg_privacy_complete": "Đã cập nhật quyền riêng tư cho tất cả các tài khoản.",
        "already_logged": "Đã có session",
        "success": "Thành công",
        "failure": "Thất bại",
        "not_found": "Chưa có",
        "otp_prompt": "Nhập mã OTP gửi tới {phone}:",
        "phone_prompt": "Nhập số điện thoại cho tài khoản ở\n{folder}:",
        "2fa_error": "Không tìm thấy mật khẩu 2FA tự động cho {phone}.",
        "copy_success": "Copy telegram.exe thành công cho {phone}",
        "copy_skip": "{phone} đã có telegram.exe, bỏ qua.",
        "close_result": "Đóng All Telegram:\nĐã đóng: {closed}\nLỗi: {errors}",
        "arrange_result": "Đã sắp xếp {count} cửa sổ Telegram.",
        "update_available": "Phiên bản {version} có sẵn. Bạn có muốn cập nhật không?",
        "no_updates": "Bạn đã có phiên bản mới nhất.",
        "update_error": "Lỗi kiểm tra cập nhật.",
        "create_session": "Tạo session",
        "update_privacy": "Thay đổi Quyền riêng tư",
        "change_info": "Thay đổi Thông tin tài khoản",
        "popup_inactive_title": "Danh sách TData đã bị log out",
        "popup_inactive_copy": "Copy toàn bộ danh sách",
        "popup_inactive_delete": "Xóa tất cả thư mục không hoạt động",
        "copy_inactive": "Copy Tdata không hoạt động",
        "delete_inactive": "Xóa Tdata không hoạt động",
        "copy_table": "Copy table",
        "processing": "Đang xử lý",
        "skipped": "Bỏ qua",
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
        "login_window_title": "Tiến trình đăng nhập",
        "not_started": "Chưa chạy",
        "auto_it_in_development": "Chức năng AutoIT đang được phát triển.",
        "report_in_development": "Chức năng Report đang được phát triển.",
        "change_info_in_development": "Chức năng thay đổi thông tin tài khoản đang được phát triển.",
        "telethon_session_title": "Phiên Telethon - {phone}",
        "invalid_source_exe": "Source telegram.exe không hợp lệ!",
        "close_result_title": "Kết quả đóng"
    },
    "en": {
        "title": "Telegram TData Auto Tool",
        "choose_folder": "Choose Folder",
        "save_path": "💾 Save Path",
        "login_all": "🔐 Telethon",
        "auto_it": "🤖 AutoIT",
        "check_live": "🔍 Check live",
        "report": "📝 Report",
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
        "msg_login_complete": "Login process completed for all accounts.",
        "msg_privacy_complete": "Privacy updated for all accounts.",
        "already_logged": "Already Logged In",
        "success": "Success",
        "failure": "Failure",
        "not_found": "Not Found",
        "otp_prompt": "Enter OTP sent to {phone}:",
        "phone_prompt": "Enter phone number for account in\n{folder}:",
        "2fa_error": "No automatic 2FA password found for {phone}.",
        "copy_success": "Copied telegram.exe successfully for {phone}",
        "copy_skip": "{phone} already has telegram.exe, skipped.",
        "close_result": "Close All Telegram:\nClosed: {closed}\nErrors: {errors}",
        "arrange_result": "Arranged {count} Telegram windows.",
        "update_available": "Version {version} is available. Do you want to update?",
        "no_updates": "You already have the latest version.",
        "update_error": "Error checking for updates.",
        "create_session": "Create Session",
        "update_privacy": "Update Privacy",
        "change_info": "Change Account Info",
        "popup_inactive_title": "Inactive TData Folders",
        "popup_inactive_copy": "Copy All Inactive",
        "popup_inactive_delete": "Delete All Inactive Folders",
        "copy_inactive": "Copy Inactive TData",
        "delete_inactive": "Delete Inactive TData",
        "copy_table": "Copy table",
        "processing": "Processing",
        "skipped": "Skipped",
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
        "login_window_title": "Login Process",
        "not_started": "Not started",
        "auto_it_in_development": "AutoIT feature is under development.",
        "report_in_development": "Report feature is under development.",
        "change_info_in_development": "Change account info feature is under development.",
        "telethon_session_title": "Telethon Session - {phone}",
        "invalid_source_exe": "Invalid source telegram.exe!",
        "close_result_title": "Close Result"
    },
    "zh": {
        "title": "Telegram TData 自动工具",
        "choose_folder": "选择文件夹",
        "save_path": "💾 保存路径",
        "login_all": "🔐 Telethon",
        "auto_it": "🤖 AutoIT",
        "check_live": "🔍 Check live",
        "report": "📝 Report",
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
        "msg_login_complete": "Login process completed for all accounts.",
        "msg_privacy_complete": "Privacy updated for all accounts.",
        "already_logged": "Already Logged In",
        "success": "Success",
        "failure": "Failure",
        "not_found": "Not Found",
        "otp_prompt": "Enter OTP sent to {phone}:",
        "phone_prompt": "Enter phone number for account in\n{folder}:",
        "2fa_error": "No automatic 2FA password found for {phone}.",
        "copy_success": "Copied telegram.exe successfully for {phone}",
        "copy_skip": "{phone} already has telegram.exe, skipped.",
        "close_result": "Close All Telegram:\nClosed: {closed}\nErrors: {errors}",
        "arrange_result": "Arranged {count} Telegram windows.",
        "update_available": "Version {version} is available. Do you want to update?",
        "no_updates": "You already have the latest version.",
        "update_error": "Error checking for updates.",
        "create_session": "Create Session",
        "update_privacy": "Update Privacy",
        "change_info": "Change Account Info",
        "popup_inactive_title": "Inactive TData Folders",
        "popup_inactive_copy": "Copy All Inactive",
        "popup_inactive_delete": "Delete All Inactive Folders",
        "copy_inactive": "Copy Inactive TData",
        "delete_inactive": "Delete Inactive TData",
        "copy_table": "Copy table",
        "processing": "Processing",
        "skipped": "Skipped",
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
        "login_window_title": "登录进程",
        "not_started": "未开始",
        "auto_it_in_development": "AutoIT 功能正在开发中。",
        "report_in_development": "报告功能正在开发中。",
        "change_info_in_development": "更改账户信息功能正在开发中。",
        "telethon_session_title": "Telethon会话 - {phone}",
        "invalid_source_exe": "无效的 telegram.exe 源文件！",
        "close_result_title": "关闭结果"
    }
}

lang = {}
successful_sessions = set()

if not psutil:
    print("Consolog: Cảnh báo - psutil chưa được cài đặt! Vui lòng cài bằng 'pip install psutil' để check live qua PID.")

############################################
# ĐỊNH NGHĨA HÀM WARN_CHECK_LIVE (KHÔNG BỊ LỖI)
############################################
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

############################################
# HÀM KIỂM TRA SESSION ĐÃ ỦY QUYỀN CHƯA
############################################
async def check_authorization(session_path, phone):
    print(f"Consolog: Kiểm tra authorization cho {phone} từ session: {session_path}")
    client = TelegramClient(session_path, API_ID, API_HASH)
    try:
        await client.connect()
        authorized = await client.is_user_authorized()
        await client.disconnect()
        print(f"Consolog: Authorization cho {phone}: {authorized}")
        return authorized
    except Exception as e:
        print(f"Consolog [ERROR]: Lỗi kiểm tra authorization cho {phone}: {e}")
        return False

############################################
# HÀM TỰ ĐÓNG TELEGRAM
############################################
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
            time.sleep(1)
        while True:
            result = subprocess.run(
                ["tasklist", "/FI", "IMAGENAME eq Telegram.exe", "/FO", "CSV"],
                capture_output=True, text=True
            )
            lines = result.stdout.strip().splitlines()
            if len(lines) <= 1:
                print("Consolog: Tất cả tiến trình Telegram đã được đóng.")
                break
            print("Consolog: Vẫn còn tiến trình Telegram, chờ 1 giây...")
            time.sleep(1)
        return True
    except Exception as e:
        print(f"Consolog [ERROR]: Lỗi khi tự động tắt Telegram: {e}")
        return False

def close_all_telegram_threaded():
    threading.Thread(target=close_all_telegram, daemon=True).start()

############################################
# PHẦN NHẬP OTP
############################################
def get_otp(phone):
    print(f"Consolog: Yêu cầu nhập OTP cho {phone}")
    otp_result = [None]
    event = threading.Event()
    def ask():
        otp_result[0] = simpledialog.askstring("OTP", lang["otp_prompt"].format(phone=phone), parent=root)
        print(f"Consolog: OTP đã được nhập: {otp_result[0]}")
        event.set()
    root.after(0, ask)
    event.wait()
    return otp_result[0]

############################################
# PARSE 2FA: LẤY FILE CHỨA MẬT KHẨU
############################################
def parse_2fa_info(tdata_folder):
    print(f"Consolog: Đang parse thông tin 2FA từ folder: {tdata_folder}")
    for root_dir, dirs, files in os.walk(tdata_folder):
        for file in files:
            if file.lower().endswith('.txt') and "2fa" in file.lower():
                path = os.path.join(root_dir, file)
                print(f"Consolog: Kiểm tra candidate 2FA file: {path}")
                try:
                    with open(path, "r", encoding="utf-8-sig") as f:
                        lines = [line.strip() for line in f if line.strip()]
                    if len(lines) == 1:
                        print(f"Consolog: Tìm thấy mật khẩu 2FA: {lines[0]}")
                        return {"password": lines[0]}
                    else:
                        print(f"Consolog: File {path} chứa {len(lines)} dòng, không hợp lệ")
                except Exception as e:
                    print(f"Consolog [ERROR]: Lỗi đọc file {path}: {e}")
    for root_dir, dirs, files in os.walk(tdata_folder):
        for file in files:
            if file.lower().endswith('.txt') and "2fa" not in file.lower():
                path = os.path.join(root_dir, file)
                print(f"Consolog: Kiểm tra candidate file: {path}")
                try:
                    with open(path, "r", encoding="utf-8-sig") as f:
                        lines = [line.strip() for line in f if line.strip()]
                    if len(lines) == 1:
                        print(f"Consolog: Tìm thấy mật khẩu: {lines[0]}")
                        return {"password": lines[0]}
                    else:
                        print(f"Consolog: File {path} chứa {len(lines)} dòng, không hợp lệ")
                except Exception as e:
                    print(f"Consolog [ERROR]: Lỗi đọc file {path}: {e}")
    return {}

############################################
# HÀM DỌN DẸP SESSION
############################################
def cleanup_session_files(session_base):
    session_file = session_base + ".session"
    print(f"Consolog: Đang dọn dẹp session từ: {session_base}")
    if os.path.exists(session_file):
        try:
            os.remove(session_file)
            print(f"Consolog: Đã xóa file session {session_file}")
        except Exception as e:
            print(f"Consolog [ERROR]: Lỗi xóa file session {session_file}: {e}")
    if os.path.exists(session_base) and os.path.isdir(session_base):
        try:
            shutil.rmtree(session_base)
            print(f"Consolog: Đã xóa thư mục session {session_base}")
        except Exception as e:
            print(f"Consolog [ERROR]: Lỗi xóa thư mục {session_base}: {e}")

def delete_all_sessions():
    tdata_dir = ""
    try:
        tdata_dir = entry_path.get()
    except:
        pass
    if not os.path.exists(tdata_dir):
        messagebox.showerror("Lỗi", lang["msg_error_path"])
        return
    tdata_folders = get_tdata_folders(tdata_dir)
    deleted_accounts = []
    for folder in tdata_folders:
        session_folder = os.path.join(folder, "session")
        session_file = os.path.join(folder, "session.session")
        if os.path.exists(session_file):
            try:
                os.remove(session_file)
                print(f"Consolog: Đã xóa file session {session_file}")
            except Exception as e:
                print(f"Consolog [ERROR]: Lỗi xóa file {session_file}: {e}")
        if os.path.exists(session_folder) and os.path.isdir(session_folder):
            try:
                shutil.rmtree(session_folder)
                print(f"Consolog: Đã xóa thư mục session {session_folder}")
            except Exception as e:
                print(f"Consolog [ERROR]: Lỗi xóa thư mục {session_folder}: {e}")
        deleted_accounts.append(os.path.basename(folder))
    messagebox.showinfo(lang["popup_inactive_title"], "Đã xóa session của các tài khoản: " + ", ".join(deleted_accounts))
    update_logged()

# =====================================================================
# UPDATE PROCESS: KIỂM TRA & TẢI CẬP NHẬT
# =====================================================================

def check_for_updates():
    print("Consolog: Kiểm tra cập nhật phiên bản...")
    try:
        url = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/releases/latest"
        response = requests.get(url)
        if response.status_code == 200:
            release_info = response.json()
            latest_version = release_info["tag_name"].lstrip("v")
            print(f"Consolog: Phiên bản mới nhất từ GitHub: {latest_version}")
            if LooseVersion(latest_version) > LooseVersion(CURRENT_VERSION):
                if messagebox.askyesno("Cập nhật", lang.get("update_available", "Phiên bản {version} có sẵn. Bạn có muốn cập nhật không?").format(version=latest_version)):
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
                        messagebox.showerror("Error", "Không tìm thấy file cập nhật trên GitHub.")
                        print("Consolog [UPDATE ERROR]: Không tìm thấy asset cập nhật.")
                else:
                    print("Consolog [UPDATE]: Người dùng không cập nhật.")
            else:
                print("Consolog: Bạn đang dùng phiên bản mới nhất.")
        else:
            print("Consolog: Lỗi kiểm tra cập nhật.")
    except Exception as e:
        print(f"Consolog [ERROR]: Lỗi kiểm tra cập nhật: {e}")

def download_update_with_progress(download_url):
    local_filename = download_url.split("/")[-1]
    print(f"Consolog [UPDATE]: Đang tải xuống file: {local_filename}")

    progress_win = tk.Toplevel(root)
    progress_win.title("Đang tải cập nhật")
    # Cài đặt kích thước cửa sổ cập nhật
    progress_win.geometry("550x130")

    # Tạo style tùy chỉnh cho progress bar với độ dày mong muốn
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
            messagebox.showerror("Error", "Không xác định được kích thước file cập nhật.")
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
                messagebox.showerror("Error", f"Lỗi mở thư mục: {e}")

        tk.Button(notify_win, text="Mở vị trí file cập nhật", command=open_update_folder).pack(pady=5)
        tk.Button(notify_win, text="Close", command=notify_win.destroy).pack(pady=5)
        print("Consolog [UPDATE]: Tải về cập nhật hoàn tất.")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to download update: {e}")
        print(f"Consolog [UPDATE ERROR]: Lỗi tải cập nhật: {e}")
        progress_win.destroy()

############################################
# HÀM SẮP XẾP CỬA SỔ TELEGRAM KIỂU MA TRẬN
############################################
def arrange_telegram_windows(custom_width=500, custom_height=504, for_check_live=False):
    print(f"Consolog: [CHANGE] Sắp xếp cửa sổ Telegram (mái ngói) với kích thước {custom_width}x{custom_height}... For check live: {for_check_live}")
    my_hwnd = root.winfo_id()
    handles = []
    seen_pids = set()

    @ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_int, ctypes.c_int)
    def enum_callback(hwnd, lParam):
        if hwnd == my_hwnd:
            return True
        if user32.IsWindowVisible(hwnd):
            length = user32.GetWindowTextLengthW(hwnd)
            buff = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buff, length + 1)
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
                    # Consolog: [CHANGE] Không loại trừ các cửa sổ cùng PID khi check live
                    handles.append(hwnd)
                    print(f"Consolog: [CHANGE] Thêm cửa sổ HWND {hwnd} từ PID {pid.value} (check live mode)")
                else:
                    if pid.value not in seen_pids:
                        seen_pids.add(pid.value)
                        handles.append(hwnd)
                        print(f"Consolog: [CHANGE] Thêm cửa sổ HWND {hwnd} từ PID {pid.value}")
        return True

    user32.EnumWindows(enum_callback, 0)
    n = len(handles)
    print(f"Consolog: [CHANGE] Tìm thấy {n} cửa sổ Telegram.")
    if n == 0:
        messagebox.showinfo("Arrange", "Không tìm thấy cửa sổ Telegram nào.")
        return

    screen_width = user32.GetSystemMetrics(0)
    screen_height = user32.GetSystemMetrics(1)
    max_cols = screen_width // custom_width
    max_rows = screen_height // custom_height
    if max_cols < 1:
        max_cols = 1
    if max_rows < 1:
        max_rows = 1
    capacity = max_cols * max_rows
    SWP_NOZORDER = 0x0004
    SWP_SHOWWINDOW = 0x0040

    # Nếu số cửa sổ <= capacity thì sắp xếp theo dạng lưới
    if n <= capacity:
        for index, hwnd in enumerate(handles):
            row = index // max_cols
            col = index % max_cols
            x = col * custom_width
            y = row * custom_height
            user32.SetWindowPos(hwnd, None, x, y, custom_width, custom_height, SWP_NOZORDER | SWP_SHOWWINDOW)
            RDW_INVALIDATE = 0x1
            RDW_UPDATENOW = 0x100
            RDW_ALLCHILDREN = 0x80
            user32.RedrawWindow(hwnd, None, None, RDW_INVALIDATE | RDW_UPDATENOW | RDW_ALLCHILDREN)
            time.sleep(0.1)
            print(f"Consolog: [CHANGE] Di chuyển cửa sổ HWND {hwnd} đến vị trí ({x}, {y}) với kích thước {custom_width}x{custom_height}")
    else:
        # Nếu số cửa sổ vượt quá capacity, sử dụng sắp xếp kiểu cascade (mái ngói) để đảm bảo mỗi cửa sổ được hiển thị một phần (tiêu đề)
        offset_x = 30   # Khoảng cách dời ngang giữa các cửa sổ
        offset_y = 30   # Khoảng cách dời dọc giữa các cửa sổ
        base_x = 0
        base_y = 0
        for index, hwnd in enumerate(handles):
            # Tính vị trí dựa trên dạng cascade – sử dụng (index % capacity) để giới hạn độ dời
            x = base_x + (index % capacity) * offset_x
            y = base_y + (index % capacity) * offset_y
            # Điều chỉnh nếu cửa sổ vượt ra ngoài màn hình
            if x + custom_width > screen_width:
                x = screen_width - custom_width
            if y + custom_height > screen_height:
                y = screen_height - custom_height
            user32.SetWindowPos(hwnd, None, x, y, custom_width, custom_height, SWP_NOZORDER | SWP_SHOWWINDOW)
            RDW_INVALIDATE = 0x1
            RDW_UPDATENOW = 0x100
            RDW_ALLCHILDREN = 0x80
            user32.RedrawWindow(hwnd, None, None, RDW_INVALIDATE | RDW_UPDATENOW | RDW_ALLCHILDREN)
            time.sleep(0.1)
            print(f"Consolog: [CHANGE] (Cascade) Di chuyển cửa sổ HWND {hwnd} đến vị trí ({x}, {y}) với kích thước {custom_width}x{custom_height}")

    messagebox.showinfo("Arrange", lang["arrange_result"].format(count=n))

def log_message(msg):
    text_log.insert(tk.END, msg + "\n")
    text_log.see(tk.END)
    print(f"[LOG] {msg}")

def save_path():
    folder_path = entry_path.get()
    print(f"Consolog: Lưu đường dẫn: {folder_path}")
    if os.path.exists(folder_path):
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            f.write(folder_path)
        messagebox.showinfo("Lưu thành công", lang["msg_saved_path"])
        update_stats()
        update_logged()
    else:
        messagebox.showerror("Lỗi", lang["msg_error_path"])

def load_path():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            path = f.read().strip()
            print(f"Consolog: Đường dẫn tải được: {path}")
            return path
    return ""

def browse_folder():
    folder_selected = filedialog.askdirectory()
    print(f"Consolog: Người dùng chọn folder: {folder_selected}")
    entry_path.delete(0, tk.END)
    entry_path.insert(0, folder_selected)

def update_stats():
    folder_path = entry_path.get()
    if not os.path.exists(folder_path):
        return
    try:
        subfolders = [d for d in os.listdir(folder_path) if os.path.isdir(os.path.join(folder_path, d))]
    except Exception as e:
        messagebox.showerror("Lỗi", f"Không thể đọc thư mục: {e}")
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

def update_logged():
    tdata_dir = entry_path.get()
    logged_list = []
    for folder in get_tdata_folders(tdata_dir):
        session_file = os.path.join(folder, "session.session")
        session_folder = os.path.join(folder, "session")
        if os.path.exists(session_file) or os.path.exists(session_folder):
            logged_list.append(os.path.basename(folder))
    text_logged.delete("1.0", tk.END)
    if logged_list:
        text_logged.insert(tk.END, ", ".join(logged_list))
    else:
        text_logged.insert(tk.END, lang["not_found"])
    print("Consolog: Cập nhật logged sessions.")

def get_tdata_folders(main_dir):
    if not os.path.exists(main_dir):
        return []
    folders = [
        os.path.join(main_dir, f) for f in os.listdir(main_dir)
        if os.path.isdir(os.path.join(main_dir, f))
    ]
    print(f"Consolog: Tìm thấy {len(folders)} thư mục TData trong {main_dir}")
    return folders

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
    time.sleep(1)
    return proc

async def async_login(session_path, phone, tdata_folder):
    print(f"Consolog: Bắt đầu đăng nhập cho {phone} với session: {session_path}")
    client = TelegramClient(session_path, API_ID, API_HASH)
    try:
        await client.connect()
    except Exception as e:
        log_message(f"Consolog [ERROR]: Lỗi kết nối cho {phone}: {e}")
        cleanup_session_files(session_path)
        return False
    if not await client.is_user_authorized():
        try:
            await client.send_code_request(phone)
            log_message(f"Consolog: Đã gửi OTP cho {phone}")
        except Exception as e:
            messagebox.showerror("Lỗi", f"Gửi mã OTP thất bại cho {phone}: {e}")
            await client.disconnect()
            cleanup_session_files(session_path)
            return False
        otp = get_otp(phone)
        if not otp:
            messagebox.showerror("Lỗi", "Không nhập OTP.")
            await client.disconnect()
            cleanup_session_files(session_path)
            return False
        auto_close_telegram()
        log_message("Consolog: Đợi 0.5 giây sau khi đóng Telegram Portable...")
        await asyncio.sleep(1)
        log_message("Consolog: Bắt đầu tiến trình đăng nhập với OTP.")
        try:
            await client.sign_in(phone, otp)
            if not await client.is_user_authorized():
                raise Exception("Đăng nhập OTP không thành công, cần 2FA")
            log_message(f"Consolog: Đăng nhập thành công cho {phone} (không 2FA)")
        except SessionPasswordNeededError:
            twofa_info = parse_2fa_info(tdata_folder)
            if "password" not in twofa_info:
                messagebox.showerror("Lỗi", lang["2fa_error"].format(phone=phone))
                await client.disconnect()
                cleanup_session_files(session_path)
                return False
            password_2fa = twofa_info["password"]
            try:
                await client.sign_in(password=password_2fa)
                if not await client.is_user_authorized():
                    raise Exception("Đăng nhập không thành công sau khi nhập mật khẩu 2FA.")
                log_message(f"Consolog: Đăng nhập thành công cho {phone} (2FA)")
            except Exception as e2:
                log_message(f"Consolog [ERROR]: Lỗi đăng nhập 2FA cho {phone}: {e2}")
                messagebox.showerror("Lỗi", f"Đăng nhập 2FA thất bại cho {phone}: {e2}")
                await client.disconnect()
                cleanup_session_files(session_path)
                return False
        except PhoneCodeInvalidError:
            messagebox.showerror("Lỗi", f"Mã OTP không đúng cho {phone}!")
            await client.disconnect()
            cleanup_session_files(session_path)
            return False
        except PhoneCodeExpiredError:
            messagebox.showerror("Lỗi", f"Mã OTP đã hết hạn cho {phone}!")
            await client.disconnect()
            cleanup_session_files(session_path)
            return False
        except Exception as e:
            messagebox.showerror("Lỗi", f"Đăng nhập thất bại cho {phone}: {e}")
            await client.disconnect()
            cleanup_session_files(session_path)
            return False
    log_message(f"Consolog: Session cho {phone} đã được lưu tại {session_path}")
    await client.disconnect()
    return True

def login_account(tdata_folder, update_item_callback):
    session_file = os.path.join(tdata_folder, "session.session")
    session_folder = os.path.join(tdata_folder, "session")
    phone = os.path.basename(tdata_folder)
    print(f"Consolog: Đang đăng nhập tài khoản: {phone}")
    _ = open_telegram_with_tdata(tdata_folder)
    if os.path.exists(session_file) or os.path.exists(session_folder):
        authorized = asyncio.run(check_authorization(session_folder, phone))
        if authorized:
            update_item_callback(phone, lang["skipped"])
            successful_sessions.add(phone)
            print(f"Consolog: {phone} session đã có, bỏ qua đăng nhập.")
            return True
        else:
            cleanup_session_files(session_folder)
    result = asyncio.run(async_login(os.path.join(tdata_folder, "session"), phone, tdata_folder))
    if result:
        update_item_callback(phone, lang["success"])
        successful_sessions.add(phone)
    else:
        update_item_callback(phone, lang["failure"])
    return result

def change_account_settings():
    print("Consolog: Yêu cầu thay đổi thông tin tài khoản.")
    messagebox.showinfo("Thông báo", lang["change_info_in_development"])

def copy_to_clipboard(text):
    root.clipboard_clear()
    root.clipboard_append(text)
    messagebox.showinfo("Copied", f"Đã copy: {text}")
    print(f"Consolog: Đã copy: {text}")

def open_telethon_terminal(session_folder):
    phone = os.path.basename(session_folder)
    twofa = parse_2fa_info(session_folder)
    password = twofa.get("password", "N/A")
    print(f"Consolog: Mở phiên Telethon cho {phone} từ session folder: {session_folder}")

    term_win = tk.Toplevel(root)
    term_win.title(lang["telethon_session_title"].format(phone=phone))
    center_window(term_win, 400, 250)

    frame_phone = tk.Frame(term_win)
    frame_phone.pack(pady=5, fill=tk.X)
    lbl_phone = tk.Label(frame_phone, text=f"Phone: {phone}", anchor="w")
    lbl_phone.pack(side=tk.LEFT, expand=True, fill=tk.X)
    btn_copy_phone = tk.Button(frame_phone, text="Copy", command=lambda: copy_to_clipboard(phone))
    btn_copy_phone.pack(side=tk.RIGHT)

    frame_pass = tk.Frame(term_win)
    frame_pass.pack(pady=5, fill=tk.X)
    lbl_pass = tk.Label(frame_pass, text=f"Password: {password}", anchor="w")
    lbl_pass.pack(side=tk.LEFT, expand=True, fill=tk.X)
    btn_copy_pass = tk.Button(frame_pass, text="Copy", command=lambda: copy_to_clipboard(password))
    btn_copy_pass.pack(side=tk.RIGHT)

    frame_otp = tk.Frame(term_win)
    frame_otp.pack(pady=5, fill=tk.X, padx=10)
    otp_var = tk.StringVar(value="OTP: ")
    lbl_otp = tk.Label(frame_otp, textvariable=otp_var, anchor="w")
    lbl_otp.pack(side=tk.LEFT, expand=True, fill=tk.X)
    btn_copy_otp = tk.Button(frame_otp, text="Copy", command=lambda: copy_to_clipboard(otp_var.get().replace('OTP: ', '')))
    btn_copy_otp.pack(side=tk.RIGHT)

    def update_otp(new_otp):
        print(f"Consolog: Cập nhật OTP: {new_otp}")
        otp_var.set(f"OTP: {new_otp}")

    def run_telethon():
        async def telethon_session():
            print(f"Consolog: Khởi tạo client từ session folder: {session_folder}")
            client = TelegramClient(os.path.join(session_folder, "session"), API_ID, API_HASH)
            try:
                await client.connect()
                authorized = await client.is_user_authorized()
                print(f"Consolog: Authorized: {authorized}")
                if not authorized:
                    term_win.after(0, update_otp, "Session is NOT authorized!")
                    return

                term_win.after(0, update_otp, "Session authorized - waiting for OTP messages...")

                @client.on(events.NewMessage)
                async def handler(event):
                    text_msg = event.message.message
                    print(f"Consolog: Tin nhắn mới nhận được: {text_msg}")
                    m = re.search(r'\b\d{5,6}\b', text_msg)
                    if m:
                        found_otp = m.group(0)
                        print(f"Consolog: OTP tìm thấy: {found_otp}")
                        term_win.after(0, update_otp, found_otp)

                await client.run_until_disconnected()
            except Exception as e:
                print(f"Consolog [ERROR]: {e}")
                term_win.after(0, update_otp, f"Error: {e}")
            finally:
                await client.disconnect()
                print("Consolog: Client đã ngắt kết nối.")

        asyncio.run(telethon_session())

    threading.Thread(target=run_telethon, daemon=True).start()

def on_closing():
    print("Consolog: Kiểm tra và xóa session chưa hoàn thành trước khi tắt tool...")
    tdata_dir = entry_path.get()
    if os.path.exists(tdata_dir):
        folders = get_tdata_folders(tdata_dir)
        for folder in folders:
            phone = os.path.basename(folder)
            if phone not in successful_sessions:
                print(f"Consolog: Xóa session chưa hoàn thành cho {phone}")
                cleanup_session_files(os.path.join(folder, "session"))
                session_file = os.path.join(folder, "session.session")
                if os.path.exists(session_file):
                    try:
                        os.remove(session_file)
                        print(f"Consolog: Đã xóa file session {session_file}")
                    except Exception as e:
                        print(f"Consolog [ERROR]: Lỗi xóa file session {session_file}: {e}")
    root.destroy()

def login_all_accounts():
    print("Consolog: Khởi tạo cửa sổ đăng nhập cho tất cả tài khoản...")
    login_window = tk.Toplevel(root)
    login_window.title(lang["login_window_title"])
    center_window(login_window, 550, 600)

    frame_already = tk.Frame(login_window)
    frame_already.pack(padx=10, pady=5, fill=tk.BOTH, expand=False)

    tk.Label(frame_already, text=lang["logged_accounts"], font=("Arial Unicode MS", 10, "bold")).pack(anchor="w")
    already_tree = ttk.Treeview(frame_already, columns=("account",), show="headings", height=5)
    already_tree.heading("account", text=lang["logged_accounts"])
    already_tree.column("account", width=300)
    already_tree.pack(fill=tk.BOTH, expand=True)

    def update_already_table():
        print("Consolog: Cập nhật bảng tài khoản đã đăng nhập...")
        already_tree.delete(*already_tree.get_children())
        tdata_dir = entry_path.get()
        for folder in get_tdata_folders(tdata_dir):
            session_file = os.path.join(folder, "session.session")
            session_folder = os.path.join(folder, "session")
            if os.path.exists(session_file) or os.path.exists(session_folder):
                already_tree.insert("", tk.END, values=(os.path.basename(folder),))

    update_already_table()

    btn_open_telethon = tk.Button(login_window, text="Open Telethon", state=tk.DISABLED, font=("Arial Unicode MS", 10, "bold"))
    btn_open_telethon.pack(pady=5)

    selected_session = {"path": None}

    def on_session_select(event):
        selected = already_tree.selection()
        if selected:
            session_name = str(already_tree.item(selected[0])["values"][0])
            tdata_dir = entry_path.get()
            session_path = os.path.join(tdata_dir, session_name)
            selected_session["path"] = session_path
            btn_open_telethon.config(state=tk.NORMAL)
        else:
            btn_open_telethon.config(state=tk.DISABLED)
            selected_session["path"] = None

    already_tree.bind("<<TreeviewSelect>>", on_session_select)

    def open_telethon_action():
        if selected_session["path"]:
            print(f"Consolog: Mở phiên Telethon cho session: {selected_session['path']}")
            open_telethon_terminal(selected_session["path"])
        else:
            messagebox.showwarning("Warning", "Chưa chọn session nào.")

    btn_open_telethon.config(command=open_telethon_action)

    tdata_dir = entry_path.get()
    all_tdata_folders = get_tdata_folders(tdata_dir)
    login_tdata_folders = [
        folder for folder in all_tdata_folders
        if not (os.path.exists(os.path.join(folder, "session.session")) or os.path.exists(os.path.join(folder, "session")))
    ]
    accounts = [os.path.basename(folder) for folder in login_tdata_folders]
    total = len(accounts)
    print(f"Consolog: Có {total} tài khoản cần đăng nhập.")

    frame_table = tk.Frame(login_window)
    frame_table.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)

    columns = ("account", "status")
    tree = ttk.Treeview(frame_table, columns=columns, show="headings", height=10)
    tree.heading("account", text="TData")
    tree.heading("status", text=lang["not_started"])
    tree.column("account", width=200, anchor="center")
    tree.column("status", width=150, anchor="center")
    tree.pack(fill=tk.BOTH, expand=True)

    for acc in accounts:
        tree.insert("", tk.END, iid=acc, values=(acc, lang["not_started"]))

    progress_frame = tk.Frame(login_window)
    progress_frame.pack(padx=10, pady=5, fill=tk.X)

    progress_var = tk.DoubleVar(value=0)
    progress_bar = ttk.Progressbar(progress_frame, variable=progress_var, maximum=100)
    progress_bar.pack(fill=tk.X, expand=True)
    progress_label = tk.Label(progress_frame, text="0%")
    progress_label.pack()

    frame_buttons_new = tk.Frame(login_window)
    frame_buttons_new.pack(pady=5)
    btn_create_session = tk.Button(frame_buttons_new, text=lang["create_session"], font=("Arial Unicode MS", 10, "bold"))
    btn_update_privacy = tk.Button(frame_buttons_new, text=lang["update_privacy"], font=("Arial Unicode MS", 10, "bold"), command=run_tool)
    btn_change_info = tk.Button(frame_buttons_new, text=lang["change_info"], font=("Arial Unicode MS", 10, "bold"), command=change_account_settings)

    btn_create_session.pack(side=tk.LEFT, padx=5)
    btn_update_privacy.pack(side=tk.LEFT, padx=5)
    btn_change_info.pack(side=tk.LEFT, padx=5)

    btn_delete_all = tk.Button(login_window, text=lang["popup_inactive_delete"], font=("Arial Unicode MS", 10, "bold"), command=delete_all_sessions)
    btn_delete_all.pack(pady=5)

    def update_item(account, status):
        tree.item(account, values=(account, status))
        if status == lang["processing"]:
            tree.tag_configure("processing", background="yellow")
            tree.item(account, tags=("processing",))
        elif status == lang["success"]:
            tree.tag_configure("success", background="lightgreen")
            tree.item(account, tags=("success",))
        elif status == lang["failure"]:
            tree.tag_configure("failed", background="tomato")
            tree.item(account, tags=("failed",))
        elif status == lang["skipped"]:
            tree.tag_configure("skipped", background="lightblue")
            tree.item(account, tags=("skipped",))
        login_window.update_idletasks()

    def process_accounts():
        print("Consolog: Bắt đầu xử lý đăng nhập các tài khoản...")
        processed = 0
        login_success = []
        login_failure = []
        for folder in login_tdata_folders:
            acc = os.path.basename(folder)
            if os.path.exists(os.path.join(folder, "session.session")) or os.path.exists(os.path.join(folder, "session")):
                update_item(acc, lang["skipped"])
                processed += 1
                percent = (processed / total) * 100
                login_window.after(0, progress_var.set, percent)
                login_window.after(0, progress_label.config, {"text": f"{int(percent)}%"})
                continue

            login_window.after(0, update_item, acc, lang["processing"])
            result = login_account(folder, update_item)
            if result:
                login_success.append(acc)
            else:
                login_failure.append(acc)

            processed += 1
            percent = (processed / total) * 100
            login_window.after(0, progress_var.set, percent)
            login_window.after(0, progress_label.config, {"text": f"{int(percent)}%"})
            time.sleep(0.5)

        login_window.after(0, update_already_table)

        summary = (
            f"{lang['already_logged']}: {len([a for a in accounts if tree.item(a)['values'][1]==lang['skipped']])}\n"
            f"{lang['success']}: {len(login_success)}\n"
            f"{lang['failure']}: {len(login_failure)}\n"
        )
        print("Consolog: Hoàn thành đăng nhập, tổng kết:")
        print(summary)

        login_window.after(0, messagebox.showinfo, "Hoàn thành", lang["msg_login_complete"])
        login_window.after(0, close_all_telegram_threaded)

    def start_login_process():
        btn_create_session.config(state=tk.DISABLED)
        threading.Thread(target=process_accounts, daemon=True).start()

    btn_create_session.config(command=start_login_process)

def update_privacy(session_path):
    async def run_update():
        print(f"Consolog: Đang cập nhật quyền riêng tư cho session: {session_path}")
        client = TelegramClient(session_path, API_ID, API_HASH)
        try:
            await client.connect()
        except Exception as e:
            log_message(f"Consolog [ERROR]: Lỗi kết nối cho {session_path}: {e}")
            return
        try:
            await client(functions.account.SetPrivacyRequest(
                key=types.InputPrivacyKeyPhoneNumber(),
                rules=[types.InputPrivacyValueDisallowAll()]
            ))
            if hasattr(types, "InputPrivacyKeyCalls"):
                await client(functions.account.SetPrivacyRequest(
                    key=types.InputPrivacyKeyCalls(),
                    rules=[types.InputPrivacyValueDisallowAll()]
                ))
            else:
                log_message("Consolog: InputPrivacyKeyCalls không khả dụng, bỏ qua.")
            log_message(f"Consolog: Cập nhật quyền riêng tư thành công cho session {session_path}")
        except Exception as e:
            log_message(f"Consolog [ERROR]: Lỗi cập nhật quyền riêng tư cho session {session_path}: {e}")
        await client.disconnect()

    asyncio.run(run_update())

def run_tool():
    print("Consolog: Bắt đầu chạy tính năng cập nhật quyền riêng tư cho tất cả tài khoản.")
    tdata_dir = entry_path.get()
    if not os.path.exists(tdata_dir):
        messagebox.showerror("Lỗi", lang["msg_error_path"])
        return
    tdata_folders = get_tdata_folders(tdata_dir)
    for folder in tdata_folders:
        open_telegram_with_tdata(folder)
    time.sleep(10)
    for folder in tdata_folders:
        session_path = os.path.join(folder, "session")
        try:
            asyncio.run(update_privacy(session_path))
        except Exception as e:
            log_message(f"Consolog [ERROR]: Lỗi cập nhật quyền riêng tư cho {folder}: {e}")
    messagebox.showinfo("Hoàn thành", lang["msg_privacy_complete"])
    log_message("Consolog: Đã hoàn tất cập nhật quyền riêng tư.")

############################################
# Consolog: PHẦN CHECK LIVE VẪN GIỮ NGUYÊN
############################################
check_live_thread = None
check_live_pause_event = threading.Event()
check_live_status = {}
confirm_done = False
tdata_process_map = {}
TEMP_SCREENSHOT_FOLDER = None

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

def save_check_live_status_file():
    print("Consolog: Lưu trạng thái check live vào file...")
    try:
        with open("check_live_status.txt", "w", encoding="utf-8") as f:
            for key, val in check_live_status.items():
                f.write(f"{key}: Check: {val['check']} | Live: {val['live']}\n")
        print("Consolog: Lưu trạng thái thành công.")
    except Exception as e:
        print(f"Consolog [ERROR]: Lỗi ghi file check_live_status.txt: {e}")

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

def show_marker_selection_popup(screenshot_paths):
    print("Consolog: Hiển thị popup chọn marker image...")
    popup = tk.Toplevel(root)
    popup.title("Chọn marker image")
    center_window(popup, 800, 600)
    instruction = tk.Label(
        popup,
        text="Hãy chỉ ra cho tôi đâu là dấu hiệu nhận biết tài khoản telegram đã chết bằng cách chọn ảnh từ danh sách bên trái",
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

def screenshot_comparison_worker():
    print("Consolog: Luồng so sánh ảnh bắt đầu, chờ 2 giây...")
    time.sleep(2)
    user32 = ctypes.windll.user32
    captured_screenshots = {}

    for tdata_name, pid_list in tdata_process_map.items():
        print(f"Consolog: === BẮT ĐẦU XỬ LÝ TDATA: {tdata_name} ===")
        window_handle = None
        for pid in pid_list:
            print(f"Consolog: -> Đang lấy HWND cho PID={pid} (TData={tdata_name})")
            try:
                hwnd = get_window_handle_by_pid(int(pid))
                print(f"Consolog: get_window_handle_by_pid({pid}) => {hwnd}")
            except Exception as e:
                print(f"Consolog [ERROR]: Lỗi get_window_handle_by_pid: {e}")
                hwnd = None
            if hwnd:
                window_handle = hwnd
                print(f"Consolog: -> Đã tìm thấy HWND={window_handle} cho PID={pid}, bỏ qua các PID khác.")
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
                print(f"Consolog: Kích thước cửa sổ (HWND={window_handle}): ({rect.left}, {rect.top}, {rect.right}, {rect.bottom}) => {w}x{h}")

                screenshot = capture_window(window_handle)
                if screenshot is None:
                    print("Consolog [ERROR]: capture_window trả về None, không chụp được ảnh!")
                else:
                    print(f"Consolog: Đã chụp ảnh thành công (size={screenshot.size}).")

                if screenshot:
                    if TEMP_SCREENSHOT_FOLDER:
                        file_path = os.path.join(TEMP_SCREENSHOT_FOLDER, f"{tdata_name}_screenshot.png")
                        screenshot.save(file_path)
                        print(f"Consolog: Đã lưu ảnh chụp của {tdata_name} tại {file_path}")
                        captured_screenshots[tdata_name] = file_path
            except Exception as e:
                print(f"Consolog [ERROR]: Lỗi chụp ảnh cho {tdata_name} - HWND={window_handle}: {e}")
        else:
            print(f"Consolog: -> Không tìm thấy HWND cho {tdata_name}, đánh dấu not_active.")
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
                    print(f"Consolog: {tdata_name} => not_active (gần giống marker).")
                else:
                    check_live_status[tdata_name]["live"] = lang["live"]
                    print(f"Consolog: {tdata_name} => live (khác marker).")
            except Exception as e:
                print(f"Consolog [ERROR]: Lỗi so sánh ảnh cho {tdata_name}: {e}")
        else:
            check_live_status[tdata_name]["live"] = lang["live"]
            print(f"Consolog: Không có marker, đặt mặc định {tdata_name} => live.")

        cl_win.after(0, refresh_table_global)

    print("Consolog: So sánh ảnh hoàn thành.")
    cl_win.after(0, lambda: messagebox.showinfo("Check live", "Đã hoàn thành kiểm tra qua so sánh hình ảnh."))

    cl_win.after(0, lambda: messagebox.showinfo("Check live", "Quá trình mở telegram hoàn tất. Hệ thống sẽ tự động so sánh hình ảnh sau 2 giây."))

def check_live_window():
    global cl_win, refresh_table_global
    cl_win = tk.Toplevel(root)
    cl_win.title(lang["check_live_title"])
    center_window(cl_win, 1200, 500)

    size_frame = tk.Frame(cl_win)
    size_frame.pack(pady=5)

    tk.Label(size_frame, text="Window Width:").grid(row=0, column=0, padx=5)
    entry_width = tk.Entry(size_frame, width=6)
    default_width, default_height = load_window_size()
    entry_width.insert(0, str(default_width))
    entry_width.grid(row=0, column=1, padx=5)

    tk.Label(size_frame, text="Window Height:").grid(row=0, column=2, padx=5)
    entry_height = tk.Entry(size_frame, width=6)
    entry_height.insert(0, str(default_height))
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
            tree.insert("", tk.END, values=(idx, tdata_name, row_data["check"], row_data["live"]))

        print("Consolog: Cập nhật bảng check live.")

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
                    time.sleep(1)
                    check_live_status[tdata_name]["check"] = lang["completed"]
                else:
                    check_live_status[tdata_name]["check"] = lang["exe_not_found"]

                cl_win.after(0, refresh_table_global)

            try:
                custom_width = int(entry_width.get())
            except:
                custom_width = 500
            try:
                custom_height = int(entry_height.get())
            except:
                custom_height = 300
            print(f"Consolog: Sử dụng kích thước cửa sổ tùy chỉnh: {custom_width}x{custom_height}")
            save_window_size(custom_width, custom_height)
            print("Consolog: Đã lưu kích thước cửa sổ.")

            print("Consolog: Đã mở xong tất cả cửa sổ Telegram. Tiến hành sắp xếp cửa sổ...")
            # Consolog: [CHANGE] Gọi hàm arrange_telegram_windows với for_check_live=True để sắp xếp tất cả cửa sổ không loại bỏ các cửa sổ cùng PID.
            arrange_telegram_windows(custom_width, custom_height, for_check_live=True)

            cl_win.after(
                0,
                lambda: messagebox.showinfo(
                    "Check live",
                    "Quá trình mở telegram hoàn tất.\nHệ thống sẽ tự động so sánh hình ảnh sau 2 giây."
                )
            )

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
        messagebox.showinfo("Check live", f"Đã lưu trạng thái check live vào file check_live_status.txt")
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
            messagebox.showwarning("Copy Table", "Vui lòng bấm '" + lang["confirm"] + "' trước.")
            return
        table_text = ""
        for child in tree.get_children():
            values = tree.item(child, "values")
            table_text += "\t".join(str(v) for v in values) + "\n"
        root.clipboard_clear()
        root.clipboard_append(table_text)
        root.update()
        messagebox.showinfo("Copy Table", "Đã copy toàn bộ nội dung bảng vào clipboard.")
        print("Consolog: Copy bảng check live thành công.")

    def copy_inactive():
        if not confirm_done:
            messagebox.showwarning("Copy Inactive", "Vui lòng bấm '" + lang["confirm"] + "' trước.")
            return
        inactive_list = []
        for child in tree.get_children():
            values = tree.item(child, "values")
            if len(values) >= 4 and values[3] == lang["not_active"]:
                inactive_list.append(values[1])
        if not inactive_list:
            messagebox.showinfo("Copy Inactive", "Không có TData nào ở trạng thái không hoạt động.")
            return
        text_inactive = "\n".join(inactive_list)
        print(f"Consolog: Copy danh sách TData không hoạt động: {text_inactive}")
        root.clipboard_clear()
        root.clipboard_append(text_inactive)
        root.update()
        messagebox.showinfo("Copy Inactive", "Đã copy vào clipboard danh sách TData không hoạt động:\n" + text_inactive)

    def delete_inactive():
        if not confirm_done:
            messagebox.showwarning("Xóa TData", "Vui lòng bấm '" + lang["confirm"] + "' trước.")
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
        messagebox.showinfo("Check live", f"Đã xóa {len(deleted)} thư mục không hoạt động:\n" + ", ".join(deleted))
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

def warn_auto_it():
    # Consolog [CHANGE]: Đóng cửa sổ mini chat khi bật chức năng AutoIT.
    try:
        from mini_chat import destroy_mini_chat
        destroy_mini_chat()  # Đóng cửa sổ mini chat
        print("Consolog: Mini chat đã được đóng khi bật chức năng AutoIT.")
    except Exception as e:
        print("Consolog [WARNING]: Không thể đóng mini chat:", e)
    warning_msg = (
        "【Tiếng Việt】: Trước khi khởi chạy chức năng AutoIT, chúng tôi khuyến nghị bạn kiểm tra trạng thái trực tiếp của các tài khoản Telegram. "
        "Điều này sẽ đảm bảo tất cả các tài khoản đều hoạt động bình thường, từ đó tối ưu hóa hiệu suất của quá trình tự động.\n"
        "【English】: Before initiating the AutoIT function, we strongly recommend performing a live check on your Telegram accounts. "
        "This will ensure that all accounts are active and optimize the automation process.\n"
        "【中文】: 在启动 AutoIT 功能之前，我们强烈建议您先对所有 Telegram 账户进行实时检查，确保它们均处于活跃状态，从而优化自动化过程的效率。"
    )
    messagebox.showinfo("Khuyến cáo", warning_msg)
    auto_it_function(root, entry_path, lang, get_tdata_folders)

def report_function():
    print("Consolog: Report function được gọi.")
    messagebox.showinfo("Report", lang["report_in_development"])

############################################
# CHỨC NĂNG open_telegram_copies GIỮ NGUYÊN
############################################
def open_telegram_copies():
    def worker():
        results = []
        tdata_dir = entry_path.get()
        if not os.path.exists(tdata_dir):
            root.after(0, lambda: messagebox.showerror("Lỗi", lang["msg_error_path"]))
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
            time.sleep(1)
        root.after(0, lambda: messagebox.showinfo(lang["msg_open_result"], "\n".join(results)))
        time.sleep(1)
        root.after(0, lambda: arrange_telegram_windows(arrange_width, arrange_height))
    threading.Thread(target=worker, daemon=True).start()

def copy_telegram_portable():
    print("Consolog: Đang copy telegram.exe cho các tài khoản...")
    tdata_dir = entry_path.get()
    if not os.path.exists(tdata_dir):
        messagebox.showerror("Lỗi", lang["msg_error_path"])
        return
    tdata_folders = get_tdata_folders(tdata_dir)
    results = []
    copied = []
    skipped = []
    errors = []

    source_exe = telegram_path_entry.get()
    if not os.path.isfile(source_exe):
        messagebox.showerror("Error", lang["invalid_source_exe"])
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

    messagebox.showinfo(lang["msg_copy_result"], summary)
    print("Consolog: Hoàn thành copy telegram.exe.")

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
                time.sleep(1)
            except Exception as e:
                errors.append(f"PID {pid}: {e}")
        summary = lang["close_result"].format(
            closed=", ".join(closed) if closed else "None",
            errors="; ".join(errors) if errors else "None"
        )
        log_message(summary)
        messagebox.showinfo(lang["close_result_title"], summary)
        print("Consolog: Đóng tiến trình Telegram hoàn tất.")
    except Exception as e:
        messagebox.showerror("Lỗi", f"Không thể đóng các tiến trình Telegram: {e}")

############################################
# CHỨC NĂNG SETTING – TÙY CHỈNH KÍCH THƯỚC CỬA SỔ VÀ CHATGPT API KEY
############################################
def open_settings():
    popup = tk.Toplevel(root)
    popup.title("Setting - Tùy chỉnh sắp xếp & ChatGPT")
    center_window(popup, 400, 350)

    lbl_info = tk.Label(popup, text="Nhập kích thước cửa sổ sắp xếp:\nx = (số cột) × Custom Width, y = (số hàng) × Custom Height", wraplength=380)
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

    tk.Label(popup, text="ChatGPT API Key:").pack(pady=5)
    chatgpt_key_entry = tk.Entry(popup, width=50)
    chatgpt_key_entry.insert(0, load_chatgpt_api_key())
    chatgpt_key_entry.pack(pady=5)

    tk.Label(popup, text="Default Translation Language (Target):").pack(pady=5)
    translation_lang_var = tk.StringVar(value=DEFAULT_TARGET_LANG)
    translation_lang_menu = tk.OptionMenu(popup, translation_lang_var, "vi", "en", "zh")
    translation_lang_menu.pack(pady=5)

    def save_settings():
        global arrange_width, arrange_height, CHATGPT_API_KEY, DEFAULT_TARGET_LANG
        try:
            w = int(entry_width.get())
            h = int(entry_height.get())
            arrange_width = w
            arrange_height = h

            save_chatgpt_api_key(chatgpt_key_entry.get().strip())
            CHATGPT_API_KEY = chatgpt_key_entry.get().strip()

            DEFAULT_TARGET_LANG = translation_lang_var.get()

            messagebox.showinfo("Setting", "Đã lưu cấu hình sắp xếp, ChatGPT API Key và ngôn ngữ dịch mặc định!")
            popup.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Giá trị không hợp lệ: {e}")

    btn_save = tk.Button(popup, text="Save", command=save_settings)
    btn_save.pack(pady=10)

    popup.transient(root)
    popup.grab_set()
    root.wait_window(popup)

def center_window(win, width, height):
    win.update_idletasks()
    screen_width = win.winfo_screenwidth()
    screen_height = win.winfo_screenheight()
    x = (screen_width - width) // 2
    y = (screen_height - height) // 2
    win.geometry(f"{width}x{height}+{x}+{y}")

def load_window_size():
    if os.path.exists(WINDOW_SIZE_FILE):
        try:
            with open(WINDOW_SIZE_FILE, "r") as f:
                line = f.read().strip()
                parts = line.split(",")
                if len(parts) == 2:
                    width = int(parts[0])
                    height = int(parts[1])
                    print(f"Consolog: Load kích thước cửa sổ từ file: {width}x{height}")
                    return width, height
        except Exception as e:
            print(f"Consolog [ERROR]: Lỗi load kích thước cửa sổ: {e}")
    return 500, 504

def save_window_size(width, height):
    try:
        with open(WINDOW_SIZE_FILE, "w") as f:
            f.write(f"{width},{height}")
        print(f"Consolog: Lưu kích thước cửa sổ: {width}x{height}")
    except Exception as e:
        print(f"Consolog [ERROR]: Lỗi lưu kích thước cửa sổ: {e}")

def load_marker_config():
    config = {"dont_ask": False}
    if os.path.exists(MARKER_CONFIG_FILE):
        try:
            with open(MARKER_CONFIG_FILE, "r", encoding="utf-8") as f:
                line = f.read().strip()
                if line.lower() == "dont_ask=true":
                    config["dont_ask"] = True
        except Exception as e:
            print(f"Consolog [ERROR]: Lỗi đọc marker config: {e}")
    return config

def save_marker_config(config):
    try:
        with open(MARKER_CONFIG_FILE, "w", encoding="utf-8") as f:
            f.write("dont_ask=true" if config.get("dont_ask") else "dont_ask=false")
    except Exception as e:
        print(f"Consolog [ERROR]: Lỗi ghi marker config: {e}")

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

def set_language(language_var, window):
    global lang
    selected = language_var.get()
    lang = languages[selected]
    window.destroy()
    # Consolog: Sau khi chọn ngôn ngữ, khởi tạo giao diện chính.
    print("Consolog: Người dùng chọn ngôn ngữ xong, khởi tạo giao diện chính.")
    init_main_ui()

# NEW: Hàm hiển thị splash screen (loading) ngay khi ứng dụng khởi chạy.
# Điều chỉnh: Thay vì delay cố định, chúng ta dùng một thread để load tool (các quá trình cần load) và splash sẽ xuất hiện trong đúng thời gian load.
def show_splash_screen():
    splash = tk.Tk()
    splash.overrideredirect(True)
    width = 300
    height = 150
    screen_width = splash.winfo_screenwidth()
    screen_height = splash.winfo_screenheight()
    x = (screen_width - width) // 2
    y = (screen_height - height) // 2
    splash.geometry(f"{width}x{height}+{x}+{y}")
    label = tk.Label(splash, text="Loading, please wait...", font=("Arial Unicode MS", 12))
    label.pack(expand=True)
    print("Consolog: Splash screen hiển thị.")

    # Start thread load tool để biết thời gian load thực
    threading.Thread(target=lambda: load_tool(splash), daemon=True).start()
    splash.mainloop()

# NEW: Hàm load_tool() thực hiện các bước load cần thiết.
def load_tool(splash):
    start_time = time.time()
    print("Consolog: Bắt đầu load tool...")
    # Ở đây bạn thay thế bằng các hàm load thực sự của tool, ví dụ:
    time.sleep(5)  # Giả lập thời gian load tool, ví dụ 5 giây.
    end_time = time.time()
    print("Consolog: Tool đã load xong sau {:.2f} giây.".format(end_time - start_time))
    # Sau khi load xong, gọi finish_splash để chuyển giao diện.
    splash.after(0, lambda: finish_splash(splash))

# NEW: Hàm finish_splash() sẽ đóng splash và gọi giao diện chọn ngôn ngữ.
def finish_splash(splash):
    splash.destroy()
    print("Consolog: Splash screen kết thúc, hiển thị giao diện chọn ngôn ngữ.")
    select_language()

##################################################
# Consolog: BẮT ĐẦU HÀM init_main_ui (màn hình chính)
##################################################
def init_main_ui():
    global root, entry_path, text_stats, text_logged, text_summary, text_log, telegram_path_entry

    # Tạo cửa sổ chính
    root = tk.Tk()
    root.title(lang["title"])
    center_window(root, 650, 800)

    default_font = tkFont.nametofont("TkDefaultFont")
    default_font.configure(family="Arial Unicode MS", size=10)
    root.option_add("*Font", default_font)

    threading.Thread(target=check_for_updates, daemon=True).start()

    label_title = tk.Label(root, text=lang["title"], font=("Arial Unicode MS", 14, "bold"))
    label_title.pack(pady=10)

    frame_path = tk.Frame(root)
    frame_path.pack(pady=5)

    entry_path = tk.Entry(frame_path, width=50)
    entry_path.pack(side=tk.LEFT, padx=5)

    btn_browse = tk.Button(frame_path, text=lang["choose_folder"], command=browse_folder)
    btn_browse.pack(side=tk.LEFT)

    frame_telegram_path = tk.Frame(root)
    frame_telegram_path.pack(pady=5)

    tk.Label(frame_telegram_path, text=lang["telegram_path_label"]).pack(side=tk.LEFT, padx=5)
    telegram_path_entry = tk.Entry(frame_telegram_path, width=50)
    telegram_path_entry.insert(0, DEFAULT_TELEGRAM_PATH)
    telegram_path_entry.pack(side=tk.LEFT, padx=5)

    btn_save = tk.Button(root, text=lang["save_path"], command=save_path, width=20)
    btn_save.pack(pady=5)

    frame_buttons = tk.Frame(root)
    frame_buttons.pack(pady=5)

    def warn_telethon():
        warning_msg = (
            "【Tiếng Việt】: Chức năng Telethon hiện đang trong giai đoạn thử nghiệm. Vui lòng lưu ý rằng có thể xảy ra một số sự cố hoặc hoạt động không ổn định.\n"
            "【English】: The Telethon feature is currently experimental. Please note that it may encounter issues or operate unpredictably.\n"
            "【中文】: Telegram 功能目前处于实验阶段，请注意可能存在一些问题或不稳定的情况。"
        )
        messagebox.showwarning("Cảnh báo", warning_msg)
        login_all_accounts()

    btn_login_all = tk.Button(frame_buttons, text=lang["login_all"], command=warn_telethon, width=18)
    btn_copy = tk.Button(frame_buttons, text=lang["copy_telegram"], command=lambda: copy_telegram_portable(), width=18)
    btn_open = tk.Button(frame_buttons, text=lang["open_telegram"], command=lambda: open_telegram_copies(), width=18)

    btn_login_all.grid(row=0, column=0, padx=5, pady=5)
    btn_copy.grid(row=0, column=1, padx=5, pady=5)
    btn_open.grid(row=0, column=2, padx=5, pady=5)

    btn_close = tk.Button(frame_buttons, text=lang["close_telegram"], command=close_all_telegram_threaded, width=18)
    btn_arrange = tk.Button(frame_buttons, text=lang["arrange_telegram"], command=lambda: arrange_telegram_windows(arrange_width, arrange_height), width=18)
    btn_auto_it = tk.Button(frame_buttons, text=lang["auto_it"], command=warn_auto_it, width=18)

    btn_close.grid(row=1, column=0, padx=5, pady=5)
    btn_arrange.grid(row=1, column=1, padx=5, pady=5)
    btn_auto_it.grid(row=1, column=2, padx=5, pady=5)

    btn_check_live = tk.Button(frame_buttons, text=lang["check_live"], command=lambda: warn_check_live(), width=18)
    btn_setting = tk.Button(frame_buttons, text="⚙️ Setting", command=open_settings, width=18)
    btn_update = tk.Button(frame_buttons, text=lang["check_update"], command=check_for_updates, width=18)

    btn_check_live.grid(row=2, column=0, padx=5, pady=5)
    btn_setting.grid(row=2, column=1, padx=5, pady=5)
    btn_update.grid(row=2, column=2, padx=5, pady=5)

    frame_stats = tk.Frame(root)
    frame_stats.pack(pady=10)
    label_stats = tk.Label(frame_stats, text=lang["stats_label"])
    label_stats.pack()
    text_stats = tk.Text(frame_stats, width=70, height=10)
    text_stats.pack()

    frame_summary = tk.Frame(root)
    frame_summary.pack(pady=10)
    text_summary = tk.Text(frame_summary, width=70, height=5)
    frame_summary.pack_forget()

    frame_logged = tk.Frame(root)
    frame_logged.pack(pady=10)
    global text_logged
    text_logged = tk.Text(frame_logged, width=70, height=5)
    frame_logged.pack_forget()

    frame_log = tk.Frame(root)
    frame_log.pack(pady=10)
    label_log = tk.Label(frame_log, text=lang["log_label"])
    label_log.pack()
    global text_log
    text_log = tk.Text(frame_log, width=70, height=10)
    text_log.pack()

    saved_path = load_path()
    if saved_path:
        entry_path.insert(0, saved_path)
        update_stats()
        update_logged()

    footer = tk.Label(root, text=VERSION_INFO, font=("Arial Unicode MS", 8))
    footer.pack(side="bottom", fill="x", pady=5)

    root.protocol("WM_DELETE_WINDOW", on_closing)

    # Consolog: Đã tách phần mini chat. Dưới đây import và gọi hàm từ mini_chat.py
    print("Consolog: Moved mini chat code to mini_chat.py")
    from mini_chat import set_root, set_mini_chat_globals, create_mini_chat, create_mini_chatgpt, start_mini_chat_monitor

    set_root(root)
    set_mini_chat_globals(CHATGPT_API_KEY, TRANSLATION_ONLY, DEFAULT_TARGET_LANG)

    create_mini_chat()
    print("Consolog: Mini Chat lớn đã được khởi tạo tự động.")
    create_mini_chatgpt()
    print("Consolog: Widget Mini Chat nhỏ (gắn vào cửa sổ Telegram) đã được khởi tạo tự động.")
    start_mini_chat_monitor()

    print("Consolog: Giao diện chính được khởi tạo thành công.")
    root.mainloop()

# Chạy khởi tạo – Bắt đầu bằng hiển thị splash screen trước khi chọn ngôn ngữ.
print("Consolog: Ứng dụng khởi chạy, hiển thị splash screen để load tool theo thời gian load thực.")
show_splash_screen()
