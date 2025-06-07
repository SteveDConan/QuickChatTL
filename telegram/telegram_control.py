# telegram/telegram_control.py
import subprocess
import threading
import time
import ctypes
from ctypes import wintypes
import psutil
from tkinter import messagebox
import os
import shutil
from utils.window_utils import get_window_handle_by_pid
from config.language import lang
from telegram.tdata_utils import get_tdata_folders

user32 = ctypes.windll.user32

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

def close_all_telegram_threaded(log_message):
    threading.Thread(target=lambda: auto_close_telegram(log_message), daemon=True).start()

def auto_close_telegram(log_message):
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

def open_telegram_with_tdata(tdata_folder, log_message):
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

def open_telegram_copies(entry_path, root):
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
        root.after(0, lambda: arrange_telegram_windows(root, arrange_width, arrange_height))
    threading.Thread(target=worker, daemon=True).start()

def copy_telegram_portable(entry_path, telegram_path_entry, log_message):
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

def arrange_telegram_windows(root, custom_width=500, custom_height=504, for_check_live=False):
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
        offset_x = 30
        offset_y = 30
        base_x = 0
        base_y = 0
        for index, hwnd in enumerate(handles):
            x = base_x + (index % capacity) * offset_x
            y = base_y + (index % capacity) * offset_y
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