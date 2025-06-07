import os
import random
import time
import threading
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import ctypes
from ctypes import wintypes
import sys
import json
import logging
import psutil
import shutil
from datetime import datetime
from edit_script import ScriptEditor, open_edit_script, run_json_script

try:
    import win32gui
    import win32con
    import win32process
    import win32api
    import win32ui
except ImportError:
    win32gui = None
    win32con = None
    win32process = None
    win32api = None
    win32ui = None
    logging.error("Không import được win32 modules.")

logging.basicConfig(filename="auto_it.log", level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")
logging.info("Khởi động chương trình AutoIT")

# Kiểm tra random.shuffle sau khi cấu hình logging
test_list = [1, 2, 3, 4, 5]
random.shuffle(test_list)
print(f"Consolog: Kiểm tra random.shuffle: {test_list}")
logging.info(f"Kiểm tra random.shuffle: {test_list}")

def kill_all_telegram_processes():
    print("Consolog: Đang kiểm tra và kết thúc tất cả các tiến trình Telegram")
    logging.info("Đang kiểm tra và kết thúc tất cả các tiến trình Telegram")
    try:
        for proc in psutil.process_iter(['name']):
            if proc.info['name'].lower() == 'telegram.exe':
                try:
                    proc.terminate()
                    proc.wait(timeout=5)
                    print(f"Consolog: Đã kết thúc tiến trình Telegram (PID: {proc.pid})")
                    logging.info(f"Đã kết thúc tiến trình Telegram (PID: {proc.pid})")
                except Exception as e:
                    print(f"Consolog: Lỗi khi kết thúc tiến trình Telegram (PID: {proc.pid}): {e}")
                    logging.error(f"Lỗi khi kết thúc tiến trình Telegram (PID: {proc.pid}): {e}")
        print("Consolog: Hoàn thành kiểm tra và kết thúc các tiến trình Telegram")
        logging.info("Hoàn thành kiểm tra và kết thúc các tiến trình Telegram")
    except Exception as e:
        print(f"Consolog: Lỗi khi kiểm tra tiến trình: {e}")
        logging.error(f"Lỗi khi kiểm tra tiến trình: {e}")

def run_script_dynamic(script_base, args=None):
    """Chạy script động dựa trên chế độ chạy và option."""
    config_file = os.path.join(SCRIPTS_DIR, "config.json")
    run_mode = "python"  # Chế độ mặc định
    if os.path.exists(config_file):
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                config = json.load(f)
            run_mode = config.get("run_mode", "python")
        except Exception as e:
            print(f"Consolog: Lỗi đọc file config.json: {e}")
            logging.error(f"Lỗi đọc file config.json: {e}")

    # Xác định đường dẫn script dựa trên chế độ chạy và script_base
    if run_mode == "python":
        script_path = os.path.join(SCRIPTS_DIR, f"{script_base}_py.py")
    elif run_mode == "json":
        script_path = os.path.join(SCRIPTS_DIR, f"{script_base}_json.json")
    elif run_mode == "txt":
        script_path = os.path.join(SCRIPTS_DIR, f"{script_base}_txt.txt")
    else:
        print(f"Consolog: Chế độ chạy không hợp lệ: {run_mode}")
        logging.error(f"Chế độ chạy không hợp lệ: {run_mode}")
        return

    print(f"Consolog: Chuẩn bị chạy script từ {script_path} với chế độ {run_mode}")
    logging.info(f"Chuẩn bị chạy script từ {script_path} với chế độ {run_mode}")

    if not os.path.exists(script_path):
        print(f"Consolog: Không tìm thấy script {script_path}")
        logging.error(f"Không tìm thấy script {script_path}")
        return

    try:
        if run_mode == "python" or run_mode == "txt":  # Xử lý txt như python đơn giản
            with open(script_path, "r", encoding="utf-8") as f:
                script_code = f.read()
            exec_globals = {
                "__name__": "__main__",
                "__file__": script_path,
                "sys": sys,
            }
            sys.argv = [script_path] + (args if args else [])
            print(f"Consolog: Đang thực hiện script {script_path} với args: {sys.argv}")
            logging.info(f"Đang thực hiện script {script_path} với args: {sys.argv}")
            exec(script_code, exec_globals)
        elif run_mode == "json":
            with open(script_path, "r", encoding="utf-8") as f:
                json_content = json.load(f)
            print(f"Consolog: Đang chạy JSON script từ {script_path}")
            logging.info(f"Đang chạy JSON script từ {script_path}")
            run_json_script(json_content)
        print(f"Consolog: Đã hoàn thành chạy script {script_path}")
        logging.info(f"Đã hoàn thành chạy script {script_path}")
    except Exception as e:
        print(f"Consolog: Lỗi khi chạy script {script_path}: {e}")
        logging.error(f"Lỗi khi chạy script {script_path}: {e}")

try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
    print("Consolog: Đã đặt DPI về 100% bằng shcore.SetProcessDpiAwareness(1)")
    logging.info("Đã đặt DPI về 100% bằng shcore.SetProcessDpiAwareness(1)")
except Exception as e:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
        print("Consolog: Đã đặt DPI về 100% bằng user32.SetProcessDPIAware()")
        logging.info("Đã đặt DPI về 100% bằng user32.SetProcessDPIAware()")
    except Exception as e:
        print("Consolog: Không thể đặt DPI về 100%:", e)
        logging.error("Không thể đặt DPI về 100%: " + str(e))

MAIN_HWND = None

def center_window(win, width, height):
    win.update_idletasks()
    screen_width = win.winfo_screenwidth()
    screen_height = win.winfo_screenheight()
    x = (screen_width - width) // 2
    y = (screen_height - height) // 2
    geometry_str = f"{width}x{height}+{x}+{y}"
    win.geometry(geometry_str)
    print(f"Consolog: Đã center cửa sổ với kích thước {width}x{height} tại vị trí ({x}, {y})")
    logging.info(f"Đã center cửa sổ với kích thước {width}x{height} tại vị trí ({x}, {y})")

if not hasattr(wintypes, 'ULONG_PTR'):
    if sys.maxsize > 2**32:
        wintypes.ULONG_PTR = ctypes.c_ulonglong
    else:
        wintypes.ULONG_PTR = ctypes.c_ulong

RECORD_IN_WINDOW = True
RECORDED_DPI = None
SCRIPTS_DIR = os.path.join(os.getcwd(), "Scripts")
if not os.path.exists(SCRIPTS_DIR):
    os.makedirs(SCRIPTS_DIR)

def is_telegram_window(hwnd):
    if hwnd and win32gui and win32gui.IsWindow(hwnd):
        title = win32gui.GetWindowText(hwnd).lower()
        return "telegram" in title
    return False

def check_telegram_hwnd(hwnd):
    if hwnd and is_telegram_window(hwnd):
        try:
            logging.info(f"Consolog: Cửa sổ Telegram hwnd {hwnd} đã sẵn sàng.")
            return True
        except Exception as e:
            logging.error(f"Consolog: Lỗi kiểm tra cửa sổ Telegram: {e}")
            return False
    else:
        logging.warning("Consolog: Handle không hợp lệ hoặc không phải cửa sổ Telegram.")
        return False

def get_telegram_hwnd_by_pid(pid):
    hwnds = []
    def enum_handler(hwnd, lParam):
        if win32gui.IsWindowVisible(hwnd):
            try:
                _, found_pid = win32process.GetWindowThreadProcessId(hwnd)
            except Exception:
                return
            if found_pid == pid:
                title = win32gui.GetWindowText(hwnd).lower()
                if "telegram" in title:
                    hwnds.append(hwnd)
    win32gui.EnumWindows(enum_handler, None)
    if hwnds:
        return hwnds[0]
    return None

def wait_for_hwnd(process_pid, max_attempts=60, wait_interval=0.5, exclude_hwnd=None):
    hwnd = None
    for attempt in range(max_attempts):
        temp_hwnd = get_telegram_hwnd_by_pid(process_pid)
        if temp_hwnd and win32gui.IsWindow(temp_hwnd) and win32gui.IsWindowVisible(temp_hwnd):
            if exclude_hwnd and temp_hwnd == exclude_hwnd:
                temp_hwnd = None
            else:
                hwnd = temp_hwnd
                break
        time.sleep(wait_interval)
    return hwnd

def get_tdata_folders(tdata_dir):
    print("Consolog: Lấy danh sách Tdata từ thư mục:", tdata_dir)
    logging.info(f"Lấy danh sách Tdata từ thư mục: {tdata_dir}")
    if os.path.isdir(tdata_dir):
        return [os.path.join(tdata_dir, d) for d in os.listdir(tdata_dir) if os.path.isdir(os.path.join(tdata_dir, d))]
    return []

def wait_with_pause(duration, local_stop_event=None):
    print("Consolog: Bắt đầu wait_with_pause với thời gian:", duration)
    logging.info(f"Bắt đầu wait_with_pause trong {duration} giây")
    start_time = time.time()
    interval = 0.05
    while time.time() - start_time < duration:
        if local_stop_event and local_stop_event.is_set():
            print("Consolog: Nhận tín hiệu dừng trong wait_with_pause")
            logging.info("Nhận tín hiệu dừng trong wait_with_pause")
            break
        time.sleep(interval)
    print("Consolog: Kết thúc wait_with_pause")
    logging.info("Kết thúc wait_with_pause")

def check_and_move_window(hwnd, folder_name, default_x, default_y, default_width, default_height):
    if not win32gui.IsWindow(hwnd):
        print(f"Consolog: Handle {hwnd} không hợp lệ để di chuyển.")
        logging.warning(f"Handle {hwnd} không hợp lệ để di chuyển.")
        return False
    rect = win32gui.GetWindowRect(hwnd)
    cur_x, cur_y = rect[0], rect[1]
    width = rect[2] - rect[0]
    height = rect[3] - rect[1]
    if cur_x != default_x or cur_y != default_y or width != default_width or height != default_height:
        try:
            win32gui.MoveWindow(hwnd, default_x, default_y, default_width, default_height, True)
            time.sleep(0.2)
            new_rect = win32gui.GetWindowRect(hwnd)
            new_x, new_y = new_rect[0], new_rect[1]
            new_w = new_rect[2] - new_rect[0]
            new_h = new_rect[3] - new_rect[1]
            if new_x == default_x and new_y == default_y and new_w == default_width and new_h == default_height:
                print(f"Consolog: Cửa sổ {folder_name} đã được di chuyển về vị trí mặc định ({default_x}, {default_y}) với kích thước {default_width}x{default_height}.")
                logging.info(f"Cửa sổ {folder_name} di chuyển về vị trí mặc định thành công.")
                return True
            else:
                print(f"Consolog: Sau khi di chuyển, cửa sổ {folder_name} vẫn chưa đúng vị trí: ({new_x}, {new_y}) kích thước {new_w}x{new_h}.")
                logging.warning(f"Cửa sổ {folder_name} chưa đạt vị trí mặc định sau khi di chuyển.")
                return False
        except Exception as e:
            print(f"Consolog: Lỗi khi di chuyển cửa sổ {folder_name}: {e}")
            logging.error(f"Lỗi khi di chuyển cửa sổ {folder_name}: {e}")
            return False
    else:
        print(f"Consolog: Cửa sổ {folder_name} đã ở vị trí mặc định.")
        return True

def safe_get_tree_item(tree, row):
    try:
        if tree.winfo_exists():
            return tree.item(row, "values")
    except Exception as e:
        logging.error("Lỗi truy xuất Treeview item: %s", e)
    return None

def safe_update_row_status(tree, row, status, table_data, tdata_dir, save=True):
    try:
        if tree.winfo_exists() and row in tree.get_children():
            vals = list(tree.item(row, "values"))
            vals[5] = status
            if status == "Đang chạy":
                tree.item(row, values=vals, tags="running")
            elif status == "Hoàn thành":
                tree.item(row, values=vals, tags="completed")
            elif status == "Đã kết thúc":
                tree.item(row, values=vals, tags="stopped")
            elif status.startswith("Error") or status.startswith("Script Error"):
                tree.item(row, values=vals, tags="error")
            else:
                tree.item(row, values=vals, tags="")
            folder_name = vals[1]
            if folder_name in table_data:
                table_data[folder_name]["status"] = status
                if save:
                    save_table_data(table_data, tdata_dir)
            print(f"Consolog: Cập nhật trạng thái {folder_name} - {status}")
            logging.info(f"Cập nhật trạng thái {folder_name} - {status}")
    except Exception as e:
        print(f"Consolog: Lỗi cập nhật row: {e}")
        logging.error(f"Lỗi cập nhật row: {e}")

def safe_update_progress(total, progress, completed_count):
    try:
        if lbl_progress_auto.winfo_exists():
            if total > 0:
                progress = min(progress, 100.0)
                print(f"Consolog: Cập nhật thanh loading: completed_count={completed_count}/{total}, progress={progress:.2f}%")
                logging.info(f"Cập nhật thanh loading: completed_count={completed_count}/{total}, progress={progress:.2f}%")
                progress_var_auto.set(progress)
                lbl_progress_auto.config(text=f"{int(progress)}%")
            else:
                print("Consolog: Tổng số công việc bằng 0, đặt tiến độ về 0%")
                logging.warning("Tổng số công việc bằng 0, đặt tiến độ về 0%")
                progress_var_auto.set(0)
                lbl_progress_auto.config(text="0%")
        else:
            print("Consolog: lbl_progress_auto không tồn tại")
            logging.error("lbl_progress_auto không tồn tại")
    except Exception as e:
        print(f"Consolog: Lỗi cập nhật thanh loading: {e}")
        logging.error(f"Lỗi cập nhật thanh loading: {e}")

try:
    from script_builder import ScriptBuilder
except ImportError:
    ScriptBuilder = None
    print("Consolog: Không tìm thấy script_builder.py hoặc lỗi import ScriptBuilder.")
    logging.error("Không tìm thấy script_builder.py hoặc lỗi import ScriptBuilder.")

def save_table_data(table_data, tdata_dir):
    try:
        json_file = os.path.join(tdata_dir, "table_data.json")
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(table_data, f, ensure_ascii=False, indent=4)
        print(f"Consolog: Đã lưu trạng thái bảng vào {json_file}")
        logging.info(f"Đã lưu trạng thái bảng vào {json_file}")
    except Exception as e:
        print(f"Consolog: Lỗi khi lưu trạng thái bảng: {e}")
        logging.error(f"Lỗi khi lưu trạng thái bảng: {e}")

def load_table_data(tdata_dir):
    table_data = {}
    json_file = os.path.join(tdata_dir, "table_data.json")
    if os.path.exists(json_file):
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                table_data = json.load(f)
            print(f"Consolog: Đã tải trạng thái bảng từ {json_file}")
            logging.info(f"Đã tải trạng thái bảng từ {json_file}")
        except Exception as e:
            print(f"Consolog: Lỗi khi tải trạng thái bảng: {e}")
            logging.error(f"Lỗi khi tải trạng thái bảng: {e}")
    return table_data

def cleanup_batch(processes, hwnds, folder_name):
    print(f"Consolog: Bắt đầu dọn dẹp batch cho {folder_name}")
    logging.info(f"Bắt đầu dọn dẹp batch cho {folder_name}")
    for hwnd in hwnds:
        if hwnd and win32gui.IsWindow(hwnd):
            try:
                win32gui.PostMessage(hwnd, win32con.WM_CLOSE, 0, 0)
                print(f"Consolog: Đã đóng cửa sổ Telegram hwnd {hwnd}")
                logging.info(f"Đã đóng cửa sổ Telegram hwnd {hwnd}")
            except Exception as e:
                print(f"Consolog: Lỗi khi đóng cửa sổ hwnd {hwnd}: {e}")
                logging.error(f"Lỗi khi đóng cửa sổ hwnd {hwnd}: {e}")
    for proc in processes:
        try:
            proc.terminate()
            proc.wait(timeout=5)
            print(f"Consolog: Đã kết thúc tiến trình Telegram (PID: {proc.pid})")
            logging.info(f"Đã kết thúc tiến trình Telegram (PID: {proc.pid})")
        except Exception as e:
            print(f"Consolog: Lỗi khi kết thúc tiến trình Telegram (PID: {proc.pid}): {e}")
            logging.error(f"Lỗi khi kết thúc tiến trình Telegram (PID: {proc.pid}): {e}")
    print(f"Consolog: Hoàn thành dọn dẹp batch cho {folder_name}")
    logging.info(f"Hoàn thành dọn dẹp batch cho {folder_name}")

def capture_screenshot(hwnd, folder_name, status, tdata_dir):
    screenshot_path = None
    if os.path.exists("screenshot_path.txt"):
        with open("screenshot_path.txt", "r", encoding="utf-8") as f:
            screenshot_path = f.read().strip()
    if not screenshot_path or not os.path.isdir(screenshot_path):
        print(f"Consolog: Đường dẫn lưu ảnh chụp màn hình không hợp lệ: {screenshot_path}")
        logging.warning(f"Đường dẫn lưu ảnh chụp màn hình không hợp lệ: {screenshot_path}")
        return
    if hwnd and win32gui.IsWindow(hwnd):
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{timestamp}_{folder_name}_{status}.png"
            full_path = os.path.join(screenshot_path, filename)
            hwnd_dc = win32gui.GetWindowDC(hwnd)
            dc_obj = win32ui.CreateDCFromHandle(hwnd_dc)
            bitmap = win32ui.CreateBitmap()
            rect = win32gui.GetWindowRect(hwnd)
            width = rect[2] - rect[0]
            height = rect[3] - rect[1]
            bitmap.CreateCompatibleBitmap(dc_obj, width, height)
            mem_dc = dc_obj.CreateCompatibleDC()
            mem_dc.SelectObject(bitmap)
            mem_dc.BitBlt((0, 0), (width, height), dc_obj, (0, 0), win32con.SRCCOPY)
            bitmap.SaveBitmapFile(mem_dc, full_path)
            mem_dc.DeleteDC()
            win32gui.ReleaseDC(hwnd, hwnd_dc)
            dc_obj.DeleteDC()
            print(f"Consolog: Đã chụp màn hình cửa sổ {folder_name} và lưu tại {full_path}")
            logging.info(f"Đã chụp màn hình cửa sổ {folder_name} và lưu tại {full_path}")
        except Exception as e:
            print(f"Consolog: Lỗi khi chụp màn hình cửa sổ {folder_name}: {e}")
            logging.error(f"Lỗi khi chụp màn hình cửa sổ {folder_name}: {e}")

def auto_it_window(root, entry_path, lang, get_tdata_folders):
    print("Consolog: Khởi tạo cửa sổ AutoIT Feature")
    logging.info("Khởi tạo cửa sổ AutoIT Feature")
    auto_win = tk.Toplevel(root)
    auto_win.title("AutoIT Feature")
    center_window(auto_win, 1200, 960)

    global_stop = False
    window_events = {}
    running_processes = []
    session_start_time = None
    session_accounts = set()
    session_loops = 0
    session_messages = 0
    session_contacts = 0
    is_running = False
    completed_count = 0
    current_cycle_completed = 0
    progress_lock = threading.Lock()
    batch_event = threading.Event()
    batch_event.set()
    WINDOW_WIDTH = 500
    WINDOW_HEIGHT = 504
    MARGIN_X = 10
    MARGIN_Y = 10

    frame_paths = tk.LabelFrame(auto_win, text="Cài đặt Đường dẫn", padx=10, pady=10)
    frame_paths.pack(fill=tk.X, padx=10, pady=5)
    frame_avatar = tk.Frame(frame_paths)
    frame_avatar.grid(row=0, column=0, sticky="ew", pady=2)
    frame_avatar.columnconfigure(1, weight=1)
    tk.Label(frame_avatar, text="Đường dẫn thư mục chứa Ảnh Avatar:").grid(row=0, column=0, sticky="w")
    var_avatar = tk.StringVar()
    if os.path.exists("avatar_path.txt"):
        with open("avatar_path.txt", "r", encoding="utf-8") as f:
            var_avatar.set(f.read().strip())
    entry_avatar = tk.Entry(frame_avatar, textvariable=var_avatar, width=50)
    entry_avatar.grid(row=0, column=1, padx=5, sticky="ew")
    tk.Button(frame_avatar, text="Browse", command=lambda: var_avatar.set(filedialog.askdirectory())).grid(row=0, column=2, padx=5)
    tk.Button(frame_avatar, text="Lưu", command=lambda: save_avatar_path()).grid(row=0, column=3, padx=5)
    lbl_avatar_stat = tk.Label(frame_avatar, text="Số file: N/A", width=15)
    lbl_avatar_stat.grid(row=0, column=4, padx=5)

    def save_avatar_path():
        path = var_avatar.get()
        print("Consolog: Lưu avatar_path:", path)
        logging.info(f"Lưu avatar_path: {path}")
        if os.path.isdir(path):
            with open("avatar_path.txt", "w", encoding="utf-8") as f:
                f.write(path)
            allowed_extensions = (".jpg", ".jpeg", ".png", ".gif", ".bmp")
            files = [f for f in os.listdir(path) if f.lower().endswith(allowed_extensions)]
            if files:
                random_file = random.choice(files)
                messagebox.showinfo("Lưu", f"Đã lưu đường dẫn Avatar: {path}\nFile ảnh ngẫu nhiên: {random_file}")
            else:
                messagebox.showinfo("Lưu", f"Đã lưu đường dẫn Avatar: {path}\nKhông tìm thấy file ảnh hợp lệ.")
        else:
            messagebox.showerror("Lỗi", "Đường dẫn không hợp lệ: " + path)

    frame_name_change = tk.Frame(frame_paths)
    frame_name_change.grid(row=1, column=0, sticky="ew", pady=2)
    frame_name_change.columnconfigure(1, weight=1)
    tk.Label(frame_name_change, text="Đường dẫn file Text danh sách tên cần đổi:").grid(row=0, column=0, sticky="w")
    var_name_change = tk.StringVar()
    if os.path.exists("name_change_path.txt"):
        with open("name_change_path.txt", "r", encoding="utf-8") as f:
            var_name_change.set(f.read().strip())
    entry_name_change = tk.Entry(frame_name_change, textvariable=var_name_change, width=50)
    entry_name_change.grid(row=0, column=1, padx=5, sticky="ew")
    tk.Button(frame_name_change, text="Browse",
              command=lambda: var_name_change.set(filedialog.askopenfilename(filetypes=[("Text Files", "*.txt")])))\
              .grid(row=0, column=2, padx=5)
    tk.Button(frame_name_change, text="Lưu", command=lambda: save_name_change_path()).grid(row=0, column=3, padx=5)
    lbl_name_change_stat = tk.Label(frame_name_change, text="Số dòng: N/A", width=15)
    lbl_name_change_stat.grid(row=0, column=4, padx=5)

    def save_name_change_path():
        path = var_name_change.get()
        print("Consolog: Lưu name_change_path:", path)
        logging.info(f"Lưu name_change_path: {path}")
        if os.path.isfile(path):
            with open("name_change_path.txt", "w", encoding="utf-8") as f:
                f.write(path)
            messagebox.showinfo("Lưu", "Đã lưu đường dẫn file danh sách tên cần đổi: " + path)
        else:
            messagebox.showerror("Lỗi", "Đường dẫn không hợp lệ: " + path)

    frame_phone = tk.Frame(frame_paths)
    frame_phone.grid(row=2, column=0, sticky="ew", pady=2)
    frame_phone.columnconfigure(1, weight=1)
    tk.Label(frame_phone, text="Đường dẫn file Text số điện thoại cần thêm vào danh bạ:").grid(row=0, column=0, sticky="w")
    var_phone = tk.StringVar()
    if os.path.exists("phone_path.txt"):
        with open("phone_path.txt", "r", encoding="utf-8") as f:
            var_phone.set(f.read().strip())
    entry_phone = tk.Entry(frame_phone, textvariable=var_phone, width=50)
    entry_phone.grid(row=0, column=1, padx=5, sticky="ew")
    tk.Button(frame_phone, text="Browse",
              command=lambda: var_phone.set(filedialog.askopenfilename(filetypes=[("Text Files", "*.txt")])))\
              .grid(row=0, column=2, padx=5)
    tk.Button(frame_phone, text="Lưu", command=lambda: save_phone_path()).grid(row=0, column=3, padx=5)
    lbl_phone_stat = tk.Label(frame_phone, text="Số dòng: N/A", width=15)
    lbl_phone_stat.grid(row=0, column=4, padx=5)

    def save_phone_path():
        path = var_phone.get()
        print("Consolog: Lưu phone_path:", path)
        logging.info(f"Lưu phone_path: {path}")
        if os.path.isfile(path):
            with open("phone_path.txt", "w", encoding="utf-8") as f:
                f.write(path)
            messagebox.showinfo("Lưu", "Đã lưu đường dẫn file số điện thoại: " + path)
        else:
            messagebox.showerror("Lỗi", "Đường dẫn không hợp lệ: " + path)

    frame_desc = tk.Frame(frame_paths)
    frame_desc.grid(row=3, column=0, sticky="ew", pady=2)
    frame_desc.columnconfigure(1, weight=1)
    tk.Label(frame_desc, text="Đường dẫn file Text danh sách mô tả tài khoản Telegram:").grid(row=0, column=0, sticky="w")
    var_desc = tk.StringVar()
    if os.path.exists("desc_path.txt"):
        with open("desc_path.txt", "r", encoding="utf-8") as f:
            var_desc.set(f.read().strip())
    entry_desc = tk.Entry(frame_desc, textvariable=var_desc, width=50)
    entry_desc.grid(row=0, column=1, padx=5, sticky="ew")
    tk.Button(frame_desc, text="Browse",
              command=lambda: var_desc.set(filedialog.askopenfilename(filetypes=[("Text Files", "*.txt")])))\
              .grid(row=0, column=2, padx=5)
    tk.Button(frame_desc, text="Lưu", command=lambda: save_desc_path()).grid(row=0, column=3, padx=5)
    lbl_desc_stat = tk.Label(frame_desc, text="Số dòng: N/A", width=15)
    lbl_desc_stat.grid(row=0, column=4, padx=5)

    def save_desc_path():
        path = var_desc.get()
        print("Consolog: Lưu desc_path:", path)
        logging.info(f"Lưu desc_path: {path}")
        if os.path.isfile(path):
            with open("desc_path.txt", "w", encoding="utf-8") as f:
                f.write(path)
            messagebox.showinfo("Lưu", "Đã lưu đường dẫn file mô tả tài khoản: " + path)
        else:
            messagebox.showerror("Lỗi", "Đường dẫn không hợp lệ: " + path)

    def update_path_stats():
        avatar_path = var_avatar.get()
        if os.path.isdir(avatar_path):
            allowed_extensions = (".jpg", ".jpeg", ".png", ".gif", ".bmp")
            files = [f for f in os.listdir(avatar_path) if f.lower().endswith(allowed_extensions)]
            count_avatar = len(files)
            lbl_avatar_stat.config(text=f"Số file: {count_avatar}")
            print(f"Consolog: Cập nhật số file avatar: {count_avatar}")
            logging.info(f"Cập nhật số file avatar: {count_avatar}")
        else:
            lbl_avatar_stat.config(text="Không hợp lệ")
        name_change_file = var_name_change.get()
        if os.path.isfile(name_change_file):
            try:
                with open(name_change_file, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                count_name = len([line for line in lines if line.strip() != ""])
            except:
                count_name = 0
            lbl_name_change_stat.config(text=f"Số dòng: {count_name}")
            print(f"Consolog: Cập nhật số dòng tên cần đổi: {count_name}")
            logging.info(f"Cập nhật số dòng tên cần đổi: {count_name}")
        else:
            lbl_name_change_stat.config(text="Không hợp lệ")
        phone_file = var_phone.get()
        if os.path.isfile(phone_file):
            try:
                with open(phone_file, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                count_phone = len([line for line in lines if line.strip() != ""])
            except:
                count_phone = 0
            lbl_phone_stat.config(text=f"Số dòng: {count_phone}")
            print(f"Consolog: Cập nhật số dòng số điện thoại: {count_phone}")
            logging.info(f"Cập nhật số dòng số điện thoại: {count_phone}")
        else:
            lbl_phone_stat.config(text="Không hợp lệ")
        desc_file = var_desc.get()
        if os.path.isfile(desc_file):
            try:
                with open(desc_file, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                count_desc = len([line for line in lines if line.strip() != ""])
            except:
                count_desc = 0
            lbl_desc_stat.config(text=f"Số dòng: {count_desc}")
            print(f"Consolog: Cập nhật số dòng mô tả: {count_desc}")
            logging.info(f"Cập nhật số dòng mô tả: {count_desc}")
        else:
            lbl_desc_stat.config(text="Không hợp lệ")
        auto_win.after(1000, update_path_stats)

    auto_win.after(1000, update_path_stats)
    frame_options = tk.LabelFrame(auto_win, text="Tùy chọn", padx=10, pady=10)
    frame_options.pack(fill=tk.X, padx=10, pady=5)
    var_change_info = tk.BooleanVar()
    var_privacy = tk.BooleanVar()
    var_welcome = tk.BooleanVar()

    def update_checkboxes(changed):
        print("Consolog: Cập nhật checkbox, đã thay đổi:", changed)
        logging.info(f"Cập nhật checkbox: {changed}")
        if changed == 'change_info':
            if var_change_info.get():
                var_privacy.set(False)
                var_welcome.set(False)
        elif changed == 'privacy':
            if var_privacy.get():
                var_change_info.set(False)
                var_welcome.set(False)
        elif changed == 'welcome':
            if var_welcome.get():
                var_change_info.set(False)
                var_privacy.set(False)

    frame_option1 = tk.Frame(frame_options)
    frame_option1.pack(fill=tk.X, pady=2)
    chk_change_info = tk.Checkbutton(
        frame_option1,
        text="Thay đổi thông tin cá nhân (Thay đổi ảnh avatar, đổi tên, đổi mô tả)",
        variable=var_change_info,
        command=lambda: update_checkboxes('change_info')
    )
    chk_change_info.grid(row=0, column=0, sticky="w", padx=5)
    frame_option1.grid_columnconfigure(1, weight=1)
    lbl_time1 = tk.Label(frame_option1, text="Tổng thời gian hoàn thành (giây):")
    lbl_time1.grid(row=0, column=1, sticky="e", padx=5)
    var_total_time1 = tk.StringVar()
    if os.path.exists("completion_time_change_info.txt"):
        with open("completion_time_change_info.txt", "r", encoding="utf-8") as f:
            var_total_time1.set(f.read().strip())
    entry_time1 = tk.Entry(frame_option1, textvariable=var_total_time1, width=8)
    entry_time1.grid(row=0, column=2, sticky="e", padx=5)
    btn_edit_change_info = tk.Button(
        frame_option1,
        text="Edit Script",
        command=lambda: open_edit_script("script_change_info", auto_win)
    )
    btn_edit_change_info.grid(row=0, column=3, sticky="e", padx=5)

    def save_time1(*args):
        with open("completion_time_change_info.txt", "w", encoding="utf-8") as f:
            f.write(var_total_time1.get())
        print("Consolog: Lưu completion_time_change_info:", var_total_time1.get())
        logging.info(f"Lưu completion_time_change_info: {var_total_time1.get()}")

    var_total_time1.trace("w", save_time1)
    frame_option2 = tk.Frame(frame_options)
    frame_option2.pack(fill=tk.X, pady=2)
    chk_privacy = tk.Checkbutton(
        frame_option2,
        text="Thay đổi quyền riêng tư (Ẩn số điện thoại và chặn cuộc gọi từ người lạ)",
        variable=var_privacy,
        command=lambda: update_checkboxes('privacy')
    )
    chk_privacy.grid(row=0, column=0, sticky="w", padx=5)
    frame_option2.grid_columnconfigure(1, weight=1)
    lbl_time2 = tk.Label(frame_option2, text="Tổng thời gian hoàn thành (giây):")
    lbl_time2.grid(row=0, column=1, sticky="e", padx=5)
    var_total_time2 = tk.StringVar()
    if os.path.exists("completion_time_privacy.txt"):
        with open("completion_time_privacy.txt", "r", encoding="utf-8") as f:
            var_total_time2.set(f.read().strip())
    entry_time2 = tk.Entry(frame_option2, textvariable=var_total_time2, width=8)
    entry_time2.grid(row=0, column=2, sticky="e", padx=5)
    btn_edit_privacy = tk.Button(
        frame_option2,
        text="Edit Script",
        command=lambda: open_edit_script("script_privacy", auto_win)
    )
    btn_edit_privacy.grid(row=0, column=3, sticky="e", padx=5)

    def save_time2(*args):
        with open("completion_time_privacy.txt", "w", encoding="utf-8") as f:
            f.write(var_total_time2.get())
        print("Consolog: Lưu completion_time_privacy:", var_total_time2.get())
        logging.info(f"Lưu completion_time_privacy: {var_total_time2.get()}")

    var_total_time2.trace("w", save_time2)
    frame_option3 = tk.Frame(frame_options)
    frame_option3.pack(fill=tk.X, pady=2)
    chk_welcome = tk.Checkbutton(
        frame_option3,
        text="Gửi tin nhắn chào mừng tới những người trong danh bạ có tên chứa từ khóa",
        variable=var_welcome,
        command=lambda: update_checkboxes('welcome')
    )
    chk_welcome.grid(row=0, column=0, sticky="w", padx=5)
    frame_option3.grid_columnconfigure(1, weight=1)
    lbl_time3 = tk.Label(frame_option3, text="Tổng thời gian hoàn thành (giây):")
    lbl_time3.grid(row=0, column=1, sticky="e", padx=5)
    var_total_time3 = tk.StringVar()
    if os.path.exists("completion_time_welcome.txt"):
        with open("completion_time_welcome.txt", "r", encoding="utf-8") as f:
            var_total_time3.set(f.read().strip())
    entry_time3 = tk.Entry(frame_option3, textvariable=var_total_time3, width=8)
    entry_time3.grid(row=0, column=2, sticky="e", padx=5)
    btn_edit_welcome = tk.Button(
        frame_option3,
        text="Edit Script",
        command=lambda: open_edit_script("script_welcome", auto_win)
    )
    btn_edit_welcome.grid(row=0, column=3, sticky="e", padx=5)

    def save_time3(*args):
        with open("completion_time_welcome.txt", "w", encoding="utf-8") as f:
            f.write(var_total_time3.get())
        print("Consolog: Lưu completion_time_welcome:", var_total_time3.get())
        logging.info(f"Lưu completion_time_welcome: {var_total_time3.get()}")

    var_total_time3.trace("w", save_time3)
    frame_welcome_text = tk.Frame(frame_options)
    frame_welcome_text.pack(fill=tk.X, pady=2)
    tk.Label(frame_welcome_text, text="Đường dẫn file tin nhắn chào mừng:").grid(row=0, column=0, sticky="w")
    var_welcome_file = tk.StringVar()
    if os.path.exists("welcome_message_file.txt"):
        with open("welcome_message_file.txt", "r", encoding="utf-8") as f:
            var_welcome_file.set(f.read().strip())
    entry_welcome_file = tk.Entry(frame_welcome_text, textvariable=var_welcome_file, width=40)
    entry_welcome_file.grid(row=0, column=1, padx=5, sticky="w")
    tk.Button(frame_welcome_text, text="Browse",
              command=lambda: var_welcome_file.set(filedialog.askopenfilename(
                  filetypes=[("Text Files", "*.txt")]
              ))).grid(row=0, column=2, padx=5, sticky="w")
    tk.Button(frame_welcome_text, text="Lưu", command=lambda: save_welcome_message_file()).grid(row=0, column=3, padx=5)
    tk.Label(frame_welcome_text, text="Đường dẫn hình ảnh gửi kèm:").grid(row=1, column=0, sticky="w")
    var_welcome_image = tk.StringVar()
    if os.path.exists("welcome_image_path.txt"):
        with open("welcome_image_path.txt", "r", encoding="utf-8") as f:
            var_welcome_image.set(f.read().strip())
    entry_welcome_image = tk.Entry(frame_welcome_text, textvariable=var_welcome_image, width=40)
    entry_welcome_image.grid(row=1, column=1, padx=5, sticky="w")
    tk.Button(frame_welcome_text, text="Browse",
              command=lambda: var_welcome_image.set(filedialog.askopenfilename(
                  filetypes=[("Image Files", "*.jpg *.jpeg *.png *.gif *.bmp")]
              ))).grid(row=1, column=2, padx=5, sticky="w")
    tk.Button(frame_welcome_text, text="Lưu", command=lambda: save_welcome_image_path()).grid(row=1, column=3, padx=5)

    def save_welcome_message_file():
        file_path = var_welcome_file.get()
        print("Consolog: Lưu welcome_message_file:", file_path)
        logging.info(f"Lưu welcome_message_file: {file_path}")
        if os.path.isfile(file_path):
            try:
                with open("welcome_message_file.txt", "w", encoding="utf-8") as f:
                    f.write(file_path)
                messagebox.showinfo("Lưu", f"Đã lưu đường dẫn file tin nhắn chào mừng: {file_path}")
            except Exception as e:
                messagebox.showerror("Lỗi", f"Lỗi lưu đường dẫn file tin nhắn: {str(e)}")
                logging.error(f"Lỗi lưu welcome_message_file: {e}")
        else:
            messagebox.showerror("Lỗi", "Đường dẫn file không hợp lệ: " + file_path)

    def save_welcome_image_path():
        image_path = var_welcome_image.get()
        print("Consolog: Lưu welcome_image_path:", image_path)
        logging.info(f"Lưu welcome_image_path: {image_path}")
        if image_path:
            if os.path.isfile(image_path):
                try:
                    with open("welcome_image_path.txt", "w", encoding="utf-8") as f:
                        f.write(image_path)
                    messagebox.showinfo("Lưu", f"Đã lưu đường dẫn hình ảnh: {image_path}")
                except Exception as e:
                    messagebox.showerror("Lỗi", f"Lỗi lưu đường dẫn hình ảnh: {str(e)}")
                    logging.error(f"Lỗi lưu welcome_image_path: {e}")
            else:
                messagebox.showerror("Lỗi", "Đường dẫn hình ảnh không hợp lệ: " + image_path)
        else:
            try:
                with open("welcome_image_path.txt", "w", encoding="utf-8") as f:
                    f.write("")
                messagebox.showinfo("Lưu", "Đã xóa đường dẫn hình ảnh.")
            except Exception as e:
                messagebox.showerror("Lỗi", f"Lỗi lưu đường dẫn hình ảnh: {str(e)}")
                logging.error(f"Lỗi lưu welcome_image_path: {e}")

    frame_buttons = tk.Frame(frame_options)
    frame_buttons.pack(pady=10)
    if ScriptBuilder:
        btn_script_builder = tk.Button(
            frame_buttons,
            text="Script Builder",
            width=20,
            command=lambda: ScriptBuilder(auto_win)
        )
        btn_script_builder.pack(side=tk.LEFT, padx=5)
    else:
        tk.Label(frame_buttons, text="[Script Builder không khả dụng]").pack(side=tk.LEFT, padx=5)
    btn_setting = tk.Button(
        frame_buttons,
        text="Setting",
        width=20,
        command=lambda: open_settings_window(auto_win)
    )
    btn_setting.pack(side=tk.LEFT, padx=5)

    def open_settings_window(parent):
        print("Consolog: Nút Setting được nhấn")
        logging.info("Nút Setting được nhấn")
        settings_win = tk.Toplevel(parent)
        settings_win.title("Cài đặt")
        center_window(settings_win, 600, 400)
        print("Consolog: Đã mở cửa sổ cài đặt")
        logging.info("Đã mở cửa sổ cài đặt")
        tk.Label(settings_win, text="Cài đặt Proxy API (Demo)", font=("Arial", 12, "bold")).pack(pady=10)
        frame_proxy = tk.Frame(settings_win)
        frame_proxy.pack(fill=tk.X, padx=10, pady=5)
        tk.Label(frame_proxy, text="Proxy Host:").grid(row=0, column=0, sticky="w")
        var_proxy_host = tk.StringVar()
        tk.Entry(frame_proxy, textvariable=var_proxy_host, width=40).grid(row=0, column=1, padx=5)
        tk.Label(frame_proxy, text="Proxy Port:").grid(row=1, column=0, sticky="w")
        var_proxy_port = tk.StringVar()
        tk.Entry(frame_proxy, textvariable=var_proxy_port, width=40).grid(row=1, column=1, padx=5)
        tk.Label(frame_proxy, text="Proxy Username:").grid(row=2, column=0, sticky="w")
        var_proxy_user = tk.StringVar()
        tk.Entry(frame_proxy, textvariable=var_proxy_user, width=40).grid(row=2, column=1, padx=5)
        tk.Label(frame_proxy, text="Proxy Password:").grid(row=3, column=0, sticky="w")
        var_proxy_pass = tk.StringVar()
        tk.Entry(frame_proxy, textvariable=var_proxy_pass, width=40, show="*").grid(row=3, column=1, padx=5)
        tk.Button(frame_proxy, text="Lưu Proxy (Demo)", command=lambda: messagebox.showinfo("Demo", "Chức năng lưu proxy chưa được triển khai")).grid(row=4, column=1, pady=10)
        tk.Label(settings_win, text="Cài đặt Báo cáo", font=("Arial", 12, "bold")).pack(pady=10)
        frame_report = tk.Frame(settings_win)
        frame_report.pack(fill=tk.X, padx=10, pady=5)
        tk.Label(frame_report, text="Đường dẫn lưu ảnh chụp màn hình:").grid(row=0, column=0, sticky="w")
        var_screenshot_path = tk.StringVar()
        if os.path.exists("screenshot_path.txt"):
            with open("screenshot_path.txt", "r", encoding="utf-8") as f:
                var_screenshot_path.set(f.read().strip())
        entry_screenshot = tk.Entry(frame_report, textvariable=var_screenshot_path, width=40)
        entry_screenshot.grid(row=0, column=1, padx=5)
        tk.Button(frame_report, text="Browse", command=lambda: var_screenshot_path.set(filedialog.askdirectory())).grid(row=0, column=2, padx=5)
        tk.Button(frame_report, text="Lưu", command=lambda: save_screenshot_path(var_screenshot_path.get())).grid(row=0, column=3, padx=5)

        def save_screenshot_path(path):
            if os.path.isdir(path):
                with open("screenshot_path.txt", "w", encoding="utf-8") as f:
                    f.write(path)
                print(f"Consolog: Đã lưu đường dẫn ảnh chụp màn hình: {path}")
                logging.info(f"Đã lưu đường dẫn ảnh chụp màn hình: {path}")
                messagebox.showinfo("Lưu", f"Đã lưu đường dẫn: {path}")
            else:
                messagebox.showerror("Lỗi", "Đường dẫn không hợp lệ: " + path)

    frame_thread2 = tk.Frame(auto_win)
    frame_thread2.pack(fill=tk.X, padx=10, pady=5)
    tk.Label(frame_thread2, text="Số luồng:").pack(side=tk.LEFT)
    var_thread2 = tk.StringVar(value="1")
    if os.path.exists("thread_count.txt"):
        with open("thread_count.txt", "r") as f:
            count = f.read().strip()
            if count:
                var_thread2.set(count)
    entry_thread2 = tk.Entry(frame_thread2, textvariable=var_thread2, width=5)
    entry_thread2.pack(side=tk.LEFT, padx=5)
    tk.Label(frame_thread2, text="Số lần chạy:").pack(side=tk.LEFT, padx=(20,0))
    var_loop_count = tk.StringVar(value="1")
    if os.path.exists("loop_count.txt"):
        with open("loop_count.txt", "r") as f:
            lc = f.read().strip()
            if lc:
                var_loop_count.set(lc)
    entry_loop_count = tk.Entry(frame_thread2, textvariable=var_loop_count, width=5)
    entry_loop_count.pack(side=tk.LEFT, padx=5)
    var_random_run = tk.BooleanVar()
    if os.path.exists("random_run.txt"):
        with open("random_run.txt", "r") as f:
            state = f.read().strip()
            var_random_run.set(state.lower() == "true")
    else:
        with open("random_run.txt", "w") as f:
            f.write("False")
        var_random_run.set(False)
    chk_random_run = tk.Checkbutton(frame_thread2, text="Chạy ngẫu nhiên", variable=var_random_run, command=lambda: save_random_run())
    chk_random_run.pack(side=tk.LEFT, padx=(20,0))

    def save_random_run():
        try:
            with open("random_run.txt", "w") as f:
                f.write(str(var_random_run.get()))
            print(f"Consolog: Đã lưu trạng thái chạy ngẫu nhiên: {var_random_run.get()}")
            logging.info(f"Đã lưu trạng thái chạy ngẫu nhiên: {var_random_run.get()}")
        except Exception as e:
            print(f"Consolog: Lỗi khi lưu trạng thái chạy ngẫu nhiên: {e}")
            logging.error(f"Lỗi khi lưu trạng thái chạy ngẫu nhiên: {e}")

    def save_thread_count(*args):
        try:
            with open("thread_count.txt", "w") as f:
                f.write(var_thread2.get())
            print("Consolog: Thread count saved:", var_thread2.get())
            logging.info(f"Thread count saved: {var_thread2.get()}")
        except Exception as e:
            print("Consolog: Error saving thread count:", str(e))
            logging.error(f"Error saving thread count: {e}")

    var_thread2.trace("w", save_thread_count)

    def check_thread_count(*args):
        config_file = "run_mode_config.json"
        run_mode_config = "python"
        if os.path.exists(config_file):
            try:
                with open(config_file, "r", encoding="utf-8") as f:
                    config = json.load(f)
                run_mode_config = config.get("run_mode", "python")
            except Exception as e:
                run_mode_config = "python"
        if run_mode_config == "json" and var_thread2.get() != "1":
            messagebox.showwarning("Chú ý", "Bạn đang trong chế độ json , tối đa chỉ được 1 thread")
            var_thread2.set("1")

    var_thread2.trace("w", check_thread_count)

    def save_loop_count(*args):
        try:
            with open("loop_count.txt", "w") as f:
                f.write(var_loop_count.get())
            print("Consolog: Loop count saved:", var_loop_count.get())
            logging.info(f"Loop count saved: {var_loop_count.get()}")
        except Exception as e:
            print("Consolog: Error saving loop count:", str(e))
            logging.error(f"Error saving loop count: {e}")

    var_loop_count.trace("w", save_loop_count)

    def update_statistics():
        nonlocal session_messages, session_contacts
        session_messages = 0
        session_contacts = 0
        for folder_name in session_accounts:
            if folder_name in table_data:
                session_messages += table_data[folder_name].get("message_count", 0)
                session_contacts += table_data[folder_name].get("contact_count", 0)
        try:
            if lbl_stats_accounts.winfo_exists():
                lbl_stats_accounts.config(text=f"Tổng số tài khoản đã chạy: {len(session_accounts)}")
            if lbl_stats_loops.winfo_exists():
                lbl_stats_loops.config(text=f"Tổng số vòng植物 đã chạy: {session_loops}")
            if lbl_stats_messages.winfo_exists():
                lbl_stats_messages.config(text=f"Tổng số tin nhắn gửi được: {session_messages}")
            if lbl_stats_contacts.winfo_exists():
                lbl_stats_contacts.config(text=f"Tổng số SĐT thêm vào danh bạ: {session_contacts}")
        except Exception as e:
            print(f"Consolog: Lỗi cập nhật thống kê: {e}")
            logging.error(f"Lỗi cập nhật thống kê: {e}")

    def update_clock():
        nonlocal is_running
        if is_running and session_start_time:
            elapsed_time = int(time.time() - session_start_time)
            lbl_stats_time.config(text=f"Tổng thời gian chạy: {elapsed_time} giây")
            auto_win.after(1000, update_clock)
        elif not is_running:
            lbl_stats_time.config(text="Tổng thời gian chạy: 0 giây")

    frame_table = tk.Frame(auto_win)
    frame_table.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
    columns = ("stt", "tdata", "live_status", "so_lan_them_danh_ba", "so_tin_nhan_chu_dc", "trạng_thái")
    tree = ttk.Treeview(frame_table, columns=columns, show="headings")
    for col, text in zip(columns,
                         ["STT", "TData", "Live(Die)", "Số lần thêm vào danh bạ", "Số tin nhắn gửi dc", "Trạng thái"]):
        tree.heading(col, text=text)
        tree.column(col, width=100, anchor="center")
    tree.tag_configure("running", background="lightgreen")
    tree.tag_configure("completed", background="lightblue")
    tree.tag_configure("stopped", background="lightcoral")
    tree.tag_configure("error", background="lightyellow")
    tree.pack(fill=tk.BOTH, expand=True)
    table_data = load_table_data(entry_path.get())
    removed_tdata = set(table_data.get("removed_tdata", []))

    def populate_auto_it_table():
        print("Consolog: Đang populate bảng hiển thị Tdata")
        logging.info("Populate bảng hiển thị Tdata")
        tdata_dir = entry_path.get()
        folders = get_tdata_folders(tdata_dir)
        live_status_dict = {}
        check_live_file = "check_live_status.txt"
        if os.path.isfile(check_live_file):
            try:
                with open(check_live_file, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                for line in lines:
                    try:
                        phone_part, status_part = line.strip().split(": Check: Hoàn thành | Live: ")
                        phone_number = phone_part.strip()
                        live_status = status_part.strip()
                        live_status = "Live" if live_status == "Live" else "Die"
                        live_status_dict[phone_number] = live_status
                    except Exception as e:
                        print(f"Consolog: Lỗi khi xử lý dòng trong check_live_status.txt: {line.strip()} - {e}")
                        logging.error(f"Lỗi khi xử lý dòng trong check_live_status.txt: {line.strip()} - {e}")
            except Exception as e:
                print(f"Consolog: Lỗi khi đọc file check_live_status.txt: {e}")
                logging.error(f"Lỗi khi đọc file check_live_status.txt: {e}")
        for item in tree.get_children():
            tree.delete(item)
        idx = 0
        for folder in folders:
            folder_name = os.path.basename(folder)
            if folder_name in removed_tdata:
                continue
            idx += 1
            if folder_name not in table_data:
                table_data[folder_name] = {
                    "live_status": live_status_dict.get(f"+{folder_name}", "Chưa check"),
                    "contact_count": 0,
                    "message_count": 0,
                    "status": "Chưa chạy"
                }
                status_file = os.path.join(folder, "status.txt")
                if os.path.isfile(status_file):
                    try:
                        with open(status_file, "r", encoding="utf-8") as f:
                            table_data[folder_name]["status"] = f.read().strip()
                    except:
                        table_data[folder_name]["status"] = "Error"
                contact_file = os.path.join(folder, "contact_count.txt")
                if os.path.isfile(contact_file):
                    try:
                        table_data[folder_name]["contact_count"] = int(open(contact_file).read().strip())
                    except:
                        table_data[folder_name]["contact_count"] = 0
                message_file = os.path.join(folder, "message_count.txt")
                if os.path.isfile(message_file):
                    try:
                        table_data[folder_name]["message_count"] = int(open(message_file).read().strip())
                    except:
                        table_data[folder_name]["message_count"] = 0
            live_status = table_data[folder_name]["live_status"]
            contact_count = table_data[folder_name]["contact_count"]
            message_count = table_data[folder_name]["message_count"]
            status = table_data[folder_name]["status"]
            tag = ""
            if status == "Đang chạy":
                tag = "running"
            elif status == "Hoàn thành":
                tag = "completed"
            elif status == "Đã kết thúc":
                tag = "stopped"
            elif status.startswith("Error") or status.startswith("Script Error"):
                tag = "error"
            tree.insert("", tk.END, values=(idx, folder_name, live_status, contact_count, message_count, status), tags=tag)
            print(f"Consolog: Đã thêm {folder_name} vào bảng với trạng thái {status} và tag {tag}")
            logging.info(f"Đã thêm {folder_name} vào bảng với trạng thái {status} và tag {tag}")
        table_data["removed_tdata"] = list(removed_tdata)
        save_table_data(table_data, tdata_dir)
        print("Consolog: Hoàn thành populate bảng hiển thị")
        logging.info("Hoàn thành populate bảng hiển thị Tdata")

    def open_tdata_folder():
        print("Consolog: Nút 'Mở thư mục' được nhấn")
        logging.info("Nút 'Mở thư mục' được nhấn")
        selected_item = tree.selection()
        if not selected_item:
            messagebox.showwarning("Chú ý", "Vui lòng chọn một Tdata từ bảng!")
            return
        values = tree.item(selected_item[0], "values")
        folder_name = values[1]
        tdata_dir = entry_path.get()
        folder_path = os.path.join(tdata_dir, folder_name)
        if os.path.exists(folder_path):
            os.startfile(folder_path)
            print(f"Consolog: Đã mở thư mục: {folder_path}")
            logging.info(f"Đã mở thư mục: {folder_path}")
        else:
            messagebox.showerror("Lỗi", f"Thư mục {folder_path} không tồn tại!")
            print(f"Consolog: Thư mục không tồn tại: {folder_path}")
            logging.error(f"Thư mục không tồn tại: {folder_path}")

    def remove_tdata():
        print("Consolog: Nút 'Xóa Tdata' được nhấn")
        logging.info("Nút 'Xóa Tdata' được nhấn")
        selected_item = tree.selection()
        if not selected_item:
            messagebox.showwarning("Chú ý", "Vui lòng chọn một Tdata từ bảng để xóa!")
            return
        values = tree.item(selected_item[0], "values")
        folder_name = values[1]
        removed_tdata.add(folder_name)
        tree.delete(selected_item[0])
        for idx, item in enumerate(tree.get_children(), 1):
            vals = list(tree.item(item, "values"))
            vals[0] = idx
            tree.item(item, values=vals)
        table_data["removed_tdata"] = list(removed_tdata)
        save_table_data(table_data, entry_path.get())
        print(f"Consolog: Đã xóa Tdata {folder_name} khỏi bảng")
        logging.info(f"Đã xóa Tdata {folder_name} khỏi bảng")

    def reset_table_status():
        print("-AprConsolog: Nút 'Reset trạng thái' được nhấn")
        logging.info("Nút 'Reset trạng thái' được nhấn")
        tdata_dir = entry_path.get()
        folders = get_tdata_folders(tdata_dir)
        live_status_dict = {}
        check_live_file = "check_live_status.txt"
        if os.path.isfile(check_live_file):
            try:
                with open(check_live_file, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                for line in lines:
                    try:
                        phone_part, status_part = line.strip().split(": Check: Hoàn thành | Live: ")
                        phone_number = phone_part.strip()
                        live_status = status_part.strip()
                        live_status = "Live" if live_status == "Live" else "Die"
                        live_status_dict[phone_number] = live_status
                    except Exception as e:
                        print(f"Consolog: Lỗi khi xử lý dòng trong check_live_status.txt: {line.strip()} - {e}")
                        logging.error(f"Lỗi khi xử lý dòng trong check_live_status.txt: {line.strip()} - {e}")
            except Exception as e:
                print(f"Consolog: Lỗi khi đọc file check_live_status.txt: {e}")
                logging.error(f"Lỗi khi đọc file check_live_status.txt: {e}")
        for folder in folders:
            folder_name = os.path.basename(folder)
            table_data[folder_name] = {
                "live_status": live_status_dict.get(f"+{folder_name}", "Chưa check"),
                "contact_count": 0,
                "message_count": 0,
                "status": "Chưa chạy"
            }
        removed_tdata.clear()
        table_data["removed_tdata"] = list(removed_tdata)
        save_table_data(table_data, tdata_dir)
        populate_auto_it_table()
        print("Consolog: Đã reset trạng thái bảng")
        logging.info("Đã reset trạng thái bảng")

    populate_auto_it_table()
    frame_progress = tk.Frame(auto_win)
    frame_progress.pack(fill=tk.X, padx=10, pady=5)
    global progress_var_auto, lbl_progress_auto
    progress_var_auto = tk.DoubleVar(value=0)
    progress_bar_auto = ttk.Progressbar(frame_progress, variable=progress_var_auto, maximum=100)
    progress_bar_auto.pack(fill=tk.X, expand=True)
    lbl_progress_auto = tk.Label(frame_progress, text="0%")
    lbl_progress_auto.pack()

    def start_all_auto(start_clock=False):
        nonlocal completed_count, global_stop, session_start_time, session_loops, is_running, current_cycle_completed
        print("Consolog: Nút 'Bắt đầu tất cả' được nhấn")
        logging.info("Nút 'Bắt đầu tất cả' được nhấn")
        if global_stop:
            print("Consolog: Đã nhận tín hiệu dừng toàn cục, không khởi tạo tiến trình mới")
            logging.info("Đã nhận tín hiệu dừng toàn cục, không khởi tạo tiến trình mới")
            return
        print("Consolog: Bắt đầu chạy start_all_auto")
        logging.info("Bắt đầu chạy start_all_auto")
        kill_all_telegram_processes()
        selected_options = []
        if var_change_info.get():
            selected_options.append(("change_info", var_total_time1.get()))
        if var_privacy.get():
            selected_options.append(("privacy", var_total_time2.get()))
        if var_welcome.get():
            selected_options.append(("welcome", var_total_time3.get()))
        if not selected_options:
            messagebox.showwarning("Chú ý", "Không có checkbox nào được chọn!")
            return
        rows = tree.get_children()
        try:
            loop_count = int(var_loop_count.get())
        except:
            loop_count = 1
        total = len(rows) * loop_count * len(selected_options)  # Cập nhật total dựa trên số option
        print(f"Consolog: Tổng số công việc: {total} (rows={len(rows)}, loop_count={loop_count}, options={len(selected_options)})")
        logging.info(f"Tổng số công việc: {total} (rows={len(rows)}, loop_count={loop_count}, options={len(selected_options)})")
        if total == 0:
            messagebox.showwarning("Chú ý", "Không có tài khoản nào để chạy!")
            return
        completed_count = 0
        session_start_time = time.time()
        session_accounts.clear()
        current_cycle_completed = 0
        if start_clock:
            is_running = True
            update_clock()
        thread_positions = {}
        global_index = 0
        for option, total_time_str in selected_options:
            try:
                completion_time = int(total_time_str)
            except:
                completion_time = 1
            try:
                thread_count = int(var_thread2.get())
            except:
                thread_count = 1
            tdata_dir = entry_path.get()
            all_rows = list(rows)
            if var_random_run.get():
                random.shuffle(all_rows)
                print(f"Consolog: Danh sách hàng sau khi xáo trộn (start_all_auto): {[tree.item(row, 'values')[1] for row in all_rows]}")
                logging.info(f"Danh sách hàng sau khi xáo trộn (start_all_auto): {[tree.item(row, 'values')[1] for row in all_rows]}")
            for cycle in range(loop_count):
                print(f"Consolog: Bắt đầu chu kỳ {cycle+1}/{loop_count} cho option {option}")
                logging.info(f"Bắt đầu chu kỳ {cycle+1}/{loop_count} cho option {option}")
                current_cycle_completed = 0
                for i in range(0, len(all_rows), thread_count):
                    if global_stop:
                        print("Consolog: Dừng khởi động luồng mới do global_stop")
                        logging.info("Dừng khởi động luồng mới do global_stop")
                        return
                    print(f"Consolog: Bắt đầu batch {i//thread_count + 1} trong chu kỳ {cycle+1}")
                    logging.info(f"Bắt đầu batch {i//thread_count + 1} trong chu kỳ {cycle+1}")
                    batch_event.wait()
                    batch_event.clear()
                    batch = all_rows[i:i+thread_count]
                    threads = []
                    batch_processes = []
                    batch_hwnds = []
                    for j, row in enumerate(batch):
                        overall_index = global_index
                        global_index += 1
                        thread_id = j
                        if thread_id in thread_positions:
                            new_x, new_y = thread_positions[thread_id]
                        else:
                            new_x = MARGIN_X + thread_id * (WINDOW_WIDTH + MARGIN_X)
                            new_y = MARGIN_Y
                            thread_positions[thread_id] = (new_x, new_y)
                        t = threading.Thread(
                            target=process_window,
                            args=(row, overall_index, completion_time, tdata_dir,
                                  WINDOW_WIDTH, WINDOW_HEIGHT, new_x, new_y, thread_count, total,
                                  batch_processes, batch_hwnds, len(all_rows), option),
                            daemon=True
                        )
                        t.start()
                        print(f"Consolog: Đã khởi động thread {overall_index} cho cửa sổ tại vị trí ({new_x}, {new_y}) với option {option}")
                        logging.info(f"Đã khởi động thread {overall_index} cho cửa sổ tại vị trí ({new_x}, {new_y}) với option {option}")
                        time.sleep(1)
                        threads.append(t)
                    for t in threads:
                        t.join()
                    cleanup_batch(batch_processes, batch_hwnds, f"batch {i//thread_count + 1}")
                    batch_event.set()
                    print(f"Consolog: Hoàn thành batch {i//thread_count + 1} trong chu kỳ {cycle+1}")
                    logging.info(f"Hoàn thành batch {i//thread_count + 1} trong chu kỳ {cycle+1}")
                print(f"Consolog: Kết thúc chu kỳ {cycle+1}/{loop_count}, current_cycle_completed={current_cycle_completed}")
                logging.info(f"Kết thúc chu kỳ {cycle+1}/{loop_count}, current_cycle_completed={current_cycle_completed}")
                if current_cycle_completed >= len(all_rows):
                    session_loops += 1
                    print(f"Consolog: Hoàn thành chu kỳ {cycle+1}, tăng session_loops lên {session_loops}")
                    logging.info(f"Hoàn thành chu kỳ {cycle+1}, tăng session_loops lên {session_loops}")
                    auto_win.after(0, update_statistics)
        auto_win.after(0, lambda: btn_start_all.config(state=tk.NORMAL))
        update_statistics()
        print("Consolog: Quá trình chạy auto đã hoàn thành cho tất cả các checkbox đã chọn")
        logging.info("Quá trình chạy auto đã hoàn thành cho tất cả các checkbox đã chọn")

    def start_selected(start_clock=False):
        nonlocal completed_count, global_stop, session_start_time, session_loops, is_running, current_cycle_completed
        print("Consolog: Nút 'Bắt đầu tùy chọn' được nhấn")
        logging.info("Nút 'Bắt đầu tùy chọn' được nhấn")
        selected_item = tree.selection()
        if not selected_item:
            messagebox.showwarning("Chú ý", "Vui lòng chọn một dòng từ bảng để bắt đầu!")
            return
        if global_stop:
            print("Consolog: Đã nhận tín hiệu dừng toàn cục, không khởi tạo tiến trình mới")
            logging.info("Đã nhận tín hiệu dừng toàn cục, không khởi tạo tiến trình mới")
            return
        print(f"Consolog: Bắt đầu chạy start_selected, chạy ngẫu nhiên: {var_random_run.get()}")
        logging.info(f"Bắt đầu chạy start_selected, chạy ngẫu nhiên: {var_random_run.get()}")
        kill_all_telegram_processes()
        selected_options = []
        if var_change_info.get():
            selected_options.append(("change_info", var_total_time1.get()))
        if var_privacy.get():
            selected_options.append(("privacy", var_total_time2.get()))
        if var_welcome.get():
            selected_options.append(("welcome", var_total_time3.get()))
        if not selected_options:
            messagebox.showwarning("Chú ý", "Không có checkbox nào được chọn!")
            return
        rows = list(tree.get_children())
        selected_row = selected_item[0]
        selected_index = rows.index(selected_row)
        if var_random_run.get():
            messagebox.showinfo("Thông báo", "Chế độ chạy ngẫu nhiên đã được kích hoạt.")
            remaining_rows = rows[:selected_index] + rows[selected_index+1:]
            if len(remaining_rows) < 1:
                messagebox.showwarning("Chú ý", "Chỉ có một hàng, chạy ngẫu nhiên không có tác dụng!")
            print(f"Consolog: Số hàng còn lại để xáo trộn: {len(remaining_rows)}")
            logging.info(f"Số hàng còn lại để xáo trộn: {len(remaining_rows)}")
            random.shuffle(remaining_rows)
            ordered_rows = [selected_row] + remaining_rows
            print(f"Consolog: Danh sách sau khi xáo trộn: {[tree.item(row, 'values')[1] for row in ordered_rows]}")
            logging.info(f"Danh sách sau khi xáo trộn: {[tree.item(row, 'values')[1] for row in ordered_rows]}")
        else:
            ordered_rows = rows[selected_index:]
        try:
            loop_count = int(var_loop_count.get())
        except:
            loop_count = 1
        total = len(ordered_rows) * loop_count * len(selected_options)  # Cập nhật total dựa trên số option
        print(f"Consolog: Tổng số công việc: {total} (rows={len(ordered_rows)}, loop_count={loop_count}, options={len(selected_options)})")
        logging.info(f"Tổng số công việc: {total} (rows={len(ordered_rows)}, loop_count={loop_count}, options={len(selected_options)})")
        if total == 0:
            messagebox.showwarning("Chú ý", "Không có tài khoản nào để chạy!")
            return
        completed_count = 0
        session_start_time = time.time()
        session_accounts.clear()
        current_cycle_completed = 0
        if start_clock:
            is_running = True
            update_clock()
        thread_positions = {}
        global_index = 0
        for option, total_time_str in selected_options:
            try:
                completion_time = int(total_time_str)
            except:
                completion_time = 1
            try:
                thread_count = int(var_thread2.get())
            except:
                thread_count = 1
            tdata_dir = entry_path.get()
            for cycle in range(loop_count):
                print(f"Consolog: Bắt đầu chu kỳ {cycle+1}/{loop_count} cho option {option}")
                logging.info(f"Bắt đầu chu kỳ {cycle+1}/{loop_count} cho option {option}")
                current_cycle_completed = 0
                for i in range(0, len(ordered_rows), thread_count):
                    if global_stop:
                        print("Consolog: Dừng khởi động luồng mới do global_stop")
                        logging.info("Dừng khởi động luồng mới do global_stop")
                        return
                    print(f"Consolog: Bắt đầu batch {i//thread_count + 1} trong chu kỳ {cycle+1}")
                    logging.info(f"Bắt đầu batch {i//thread_count + 1} trong chu kỳ {cycle+1}")
                    batch_event.wait()
                    batch_event.clear()
                    batch = ordered_rows[i:i+thread_count]
                    threads = []
                    batch_processes = []
                    batch_hwnds = []
                    for j, row in enumerate(batch):
                        overall_index = global_index
                        global_index += 1
                        thread_id = j
                        if thread_id in thread_positions:
                            new_x, new_y = thread_positions[thread_id]
                        else:
                            new_x = MARGIN_X + thread_id * (WINDOW_WIDTH + MARGIN_X)
                            new_y = MARGIN_Y
                            thread_positions[thread_id] = (new_x, new_y)
                        t = threading.Thread(
                            target=process_window,
                            args=(row, overall_index, completion_time, tdata_dir,
                                  WINDOW_WIDTH, WINDOW_HEIGHT, new_x, new_y, thread_count, total,
                                  batch_processes, batch_hwnds, len(ordered_rows), option),
                            daemon=True
                        )
                        t.start()
                        time.sleep(1)
                        threads.append(t)
                    for t in threads:
                        t.join()
                    cleanup_batch(batch_processes, batch_hwnds, f"batch {i//thread_count + 1}")
                    batch_event.set()
                    print(f"Consolog: Hoàn thành batch {i//thread_count + 1} trong chu kỳ {cycle+1}")
                    logging.info(f"Hoàn thành batch {i//thread_count + 1} trong chu kỳ {cycle+1}")
                print(f"Consolog: Kết thúc chu kỳ {cycle+1}/{loop_count}, current_cycle_completed={current_cycle_completed}")
                logging.info(f"Kết thúc chu kỳ {cycle+1}/{loop_count}, current_cycle_completed={current_cycle_completed}")
                if current_cycle_completed >= len(ordered_rows):
                    session_loops += 1
                    print(f"Consolog: Hoàn thành chu kỳ {cycle+1}, tăng session_loops lên {session_loops}")
                    logging.info(f"Hoàn thành chu kỳ {cycle+1}, tăng session_loops lên {session_loops}")
                    auto_win.after(0, update_statistics)
        auto_win.after(0, lambda: btn_start_all.config(state=tk.NORMAL))
        update_statistics()
        print("Consolog: Quá trình chạy tùy chọn đã hoàn thành")
        logging.info("Quá trình chạy tùy chọn đã hoàn thành")

    def process_window(row, overall_index, completion_time, tdata_dir,
                       WINDOW_WIDTH, WINDOW_HEIGHT, new_x, new_y, thread_count, total,
                       batch_processes, batch_hwnds, total_rows, option):
        nonlocal completed_count, global_stop, session_accounts, current_cycle_completed
        if global_stop:
            values = safe_get_tree_item(tree, row)
            if values and values[5] == "Đang chạy":
                auto_win.after(0, lambda: safe_update_row_status(tree, row, "Đã kết thúc", table_data, tdata_dir))
            with progress_lock:
                completed_count += 1
                current_cycle_completed += 1
                progress = (completed_count / total) * 100
                print(f"Consolog: Cập nhật tiến độ cho global_stop: completed_count={completed_count}/{total}, progress={progress:.2f}%")
                logging.info(f"Cập nhật tiến độ cho global_stop: completed_count={completed_count}/{total}, progress={progress:.2f}%")
                auto_win.after(0, lambda: safe_update_progress(total, progress, completed_count))
            return
        values = safe_get_tree_item(tree, row)
        if values is None:
            with progress_lock:
                completed_count += 1
                current_cycle_completed += 1
                progress = (completed_count / total) * 100
                print(f"Consolog: Cập nhật tiến độ cho values=None: completed_count={completed_count}/{total}, progress={progress:.2f}%")
                logging.info(f"Cập nhật tiến độ cho values=None: completed_count={completed_count}/{total}, progress={progress:.2f}%")
                auto_win.after(0, lambda: safe_update_progress(total, progress, completed_count))
            return
        folder_name = values[1]
        session_accounts.add(folder_name)
        full_path = os.path.join(tdata_dir, folder_name)
        print(f"Consolog: Bắt đầu xử lý {folder_name} với option {option}")
        logging.info(f"Bắt đầu xử lý {folder_name} với option {option}")
        telegram_exe = os.path.join(full_path, "Telegram.exe")
        if not os.path.exists(telegram_exe):
            print(f"Consolog: Telegram.exe không tồn tại tại {folder_name}")
            logging.error(f"Telegram.exe không tồn tại tại {folder_name}")
            auto_win.after(0, lambda: safe_update_row_status(tree, row, "Error: Telegram.exe không tồn tại", table_data, tdata_dir))
            with progress_lock:
                completed_count += 1
                current_cycle_completed += 1
                progress = (completed_count / total) * 100
                print(f"Consolog: Cập nhật tiến độ cho Telegram.exe không tồn tại: completed_count={completed_count}/{total}, progress={progress:.2f}%")
                logging.info(f"Cập nhật tiến độ cho Telegram.exe không tồn tại: completed_count={completed_count}/{total}, progress={progress:.2f}%")
                auto_win.after(0, lambda: safe_update_progress(total, progress, completed_count))
            return
        local_stop = threading.Event()
        window_events[folder_name] = local_stop
        try:
            print(f"Consolog: Mở Telegram.exe tại {folder_name}")
            logging.info(f"Mở Telegram.exe tại {folder_name}")
            process = subprocess.Popen([telegram_exe])
            running_processes.append(process)
            batch_processes.append(process)
        except Exception as e:
            print(f"Consolog: Lỗi mở Telegram.exe tại {folder_name}: {e}")
            logging.error(f"Lỗi mở Telegram.exe tại {folder_name}: {e}")
            auto_win.after(0, lambda: safe_update_row_status(tree, row, f"Error: {e}", table_data, tdata_dir))
            with progress_lock:
                completed_count += 1
                current_cycle_completed += 1
                progress = (completed_count / total) * 100
                print(f"Consolog: Cập nhật tiến độ cho lỗi mở Telegram.exe: completed_count={completed_count}/{total}, progress={progress:.2f}%")
                logging.info(f"Cập nhật tiến độ cho lỗi mở Telegram.exe: completed_count={completed_count}/{total}, progress={progress:.2f}%")
                auto_win.after(0, lambda: safe_update_progress(total, progress, completed_count))
            return
        wait_with_pause(0.5, local_stop)
        if local_stop.is_set() or global_stop:
            print(f"Consolog: Nhận tín hiệu dừng trong {folder_name}")
            logging.info(f"Nhận tín hiệu dừng trong {folder_name}")
            process.terminate()
            if values[5] == "Đang chạy":
                auto_win.after(0, lambda: safe_update_row_status(tree, row, "Đã kết thúc", table_data, tdata_dir))
            with progress_lock:
                completed_count += 1
                current_cycle_completed += 1
                progress = (completed_count / total) * 100
                print(f"Consolog: Cập nhật tiến độ cho tín hiệu dừng: completed_count={completed_count}/{total}, progress={progress:.2f}%")
                logging.info(f"Cập nhật tiến độ cho tín hiệu dừng: completed_count={completed_count}/{total}, progress={progress:.2f}%")
                auto_win.after(0, lambda: safe_update_progress(total, progress, completed_count))
            return
        hwnd = None
        if win32gui is not None:
            hwnd = wait_for_hwnd(process.pid, max_attempts=60, wait_interval=0.5, exclude_hwnd=MAIN_HWND)
            if hwnd and win32gui.IsWindow(hwnd) and win32gui.IsWindowVisible(hwnd):
                batch_hwnds.append(hwnd)
                try:
                    win32gui.SetForegroundWindow(hwnd)
                    print(f"Consolog: Đã đưa cửa sổ {folder_name} lên foreground")
                    logging.info(f"Đã đưa cửa sổ {folder_name} lên foreground")
                except Exception as e:
                    print(f"Consolog: Lỗi SetForegroundWindow cho {folder_name}: {e}")
                    logging.error(f"Lỗi SetForegroundWindow cho {folder_name}: {e}")
                time.sleep(0.5)
                print(f"Consolog: Di chuyển cửa sổ {folder_name} tới vị trí ({new_x}, {new_y})")
                logging.info(f"Di chuyển cửa sổ {folder_name} tới ({new_x}, {new_y})")
                check_and_move_window(hwnd, folder_name, int(new_x), int(new_y), WINDOW_WIDTH, WINDOW_HEIGHT)
            else:
                print(f"Consolog: Không tìm thấy handle cửa sổ hợp lệ cho {folder_name}")
                logging.error(f"Không tìm thấy handle cửa sổ hợp lệ cho {folder_name}")
        auto_win.after(0, lambda: safe_update_row_status(tree, row, "Đang chạy", table_data, tdata_dir))
        wait_with_pause(3, local_stop)
        try:
            script_base = f"script_{option}"
            print(f"Consolog: Chạy script {script_base} cho {folder_name} với handle {str(hwnd)}")
            logging.info(f"Chạy script {script_base} cho {folder_name} với hwnd {hwnd}")
            start_script = time.time()
            run_script_dynamic(script_base, [full_path, str(hwnd), tdata_dir, folder_name])
            contact_file = os.path.join(full_path, "contact_count.txt")
            if os.path.isfile(contact_file):
                try:
                    contact_count = int(open(contact_file).read().strip())
                    table_data[folder_name]["contact_count"] = contact_count
                except:
                    table_data[folder_name]["contact_count"] = 0
            message_file = os.path.join(full_path, "message_count.txt")
            if os.path.isfile(message_file):
                try:
                    message_count = int(open(message_file).read().strip())
                    table_data[folder_name]["message_count"] = message_count
                except:
                    table_data[folder_name]["message_count"] = 0
            vals = list(tree.item(row, "values"))
            vals[3] = table_data[folder_name]["contact_count"]
            vals[4] = table_data[folder_name]["message_count"]
            tree.item(row, values=vals)
            save_table_data(table_data, tdata_dir)
            auto_win.after(0, update_statistics)
            elapsed = time.time() - start_script
            remaining = completion_time - elapsed
            if remaining > 0:
                print(f"Consolog: Đang chờ thêm {remaining:.2f} giây cho {folder_name} để đủ mốc thời gian")
                logging.info(f"Chờ thêm {remaining:.2f} giây cho {folder_name}")
                wait_with_pause(remaining, local_stop)
            if local_stop.is_set() or global_stop:
                print(f"Consolog: Nhận tín hiệu dừng sau khi chạy script cho {folder_name}")
                logging.info(f"Nhận tín hiệu dừng sau khi chạy script cho {folder_name}")
                process.terminate()
                if values[5] == "Đang chạy":
                    auto_win.after(0, lambda: safe_update_row_status(tree, row, "Đã kết thúc", table_data, tdata_dir))
                with progress_lock:
                    completed_count += 1
                    current_cycle_completed += 1
                    progress = (completed_count / total) * 100
                    print(f"Consolog: Cập nhật tiến độ cho dừng sau script: completed_count={completed_count}/{total}, progress={progress:.2f}%")
                    logging.info(f"Cập nhật tiến độ cho dừng sau script: completed_count={completed_count}/{total}, progress={progress:.2f}%")
                    auto_win.after(0, lambda: safe_update_progress(total, progress, completed_count))
                auto_win.after(0, update_statistics)
                return
            auto_win.after(0, lambda: capture_screenshot(hwnd, folder_name, "Hoàn thành", tdata_dir))
        except Exception as e:
            print(f"Consolog: Lỗi script cho {folder_name}: {e}")
            logging.error(f"Lỗi script cho {folder_name}: {e}")
            auto_win.after(0, lambda: safe_update_row_status(tree, row, f"Script Error: {e}", table_data, tdata_dir))
            start_script = time.time()
            elapsed = time.time() - start_script
            remaining = completion_time - elapsed
            if remaining > 0:
                wait_with_pause(remaining, local_stop)
            auto_win.after(0, lambda: capture_screenshot(hwnd, folder_name, "Script Error", tdata_dir))
        print(f"Consolog: Xong xử lý {folder_name}")
        logging.info(f"Xong xử lý {folder_name}")
        auto_win.after(0, lambda: safe_update_row_status(tree, row, "Hoàn thành", table_data, tdata_dir))
        with progress_lock:
            completed_count += 1
            current_cycle_completed += 1
            progress = (completed_count / total) * 100
            print(f"Consolog: Cập nhật tiến độ cho hoàn thành {folder_name}: completed_count={completed_count}/{total}, progress={progress:.2f}%")
            logging.info(f"Cập nhật tiến độ cho hoàn thành {folder_name}: completed_count={completed_count}/{total}, progress={progress:.2f}%")
            auto_win.after(0, lambda: safe_update_progress(total, progress, completed_count))
        auto_win.after(0, update_statistics)

    def end_all_auto():
        nonlocal global_stop, is_running
        print("Consolog: Nút 'Kết thúc tất cả' được nhấn")
        logging.info("Nút 'Kết thúc tất cả' được nhấn")
        global_stop = True
        is_running = False
        for key, s_event in window_events.items():
            s_event.set()
        for proc in running_processes:
            try:
                proc.terminate()
                print("Consolog: Đã kết thúc tiến trình", proc.pid)
                logging.info(f"Đã kết thúc tiến trình {proc.pid}")
            except Exception as e:
                print("Consolog: Lỗi khi kết thúc tiến trình:", e)
                logging.error(f"Lỗi khi kết thúc tiến trình: {e}")
        for row in tree.get_children():
            values = safe_get_tree_item(tree, row)
            if values and values[5] == "Đang chạy":
                safe_update_row_status(tree, row, "Đã kết thúc", table_data, entry_path.get())
        batch_event.set()
        print("Consolog: Đã kết thúc tất cả các quá trình")
        logging.info("Đã kết thúc tất cả các quá trình")
        auto_win.after(0, update_statistics)

    def restart_module():
        print("Consolog: Nút 'Khởi động lại toàn bộ' được nhấn")
        logging.info("Nút 'Khởi động lại toàn bộ' được nhấn")
        end_all_auto()
        auto_win.destroy()
        auto_it_function(root, entry_path, lang, get_tdata_folders)

    frame_bottom = tk.Frame(auto_win)
    frame_bottom.pack(fill=tk.X, padx=10, pady=(10, 20))
    frame_bottom.columnconfigure(0, weight=1)
    frame_bottom.columnconfigure(1, weight=1)
    frame_controls = tk.Frame(frame_bottom)
    frame_controls.grid(row=0, column=0, sticky="nsew", padx=5, pady=(15, 0))
    btn_start_all = tk.Button(frame_controls, text="Bắt đầu tất cả", width=15, command=lambda: threading.Thread(target=lambda: start_all_auto(True), daemon=True).start())
    btn_start_selected = tk.Button(frame_controls, text="Bắt đầu tùy chọn", width=15, command=lambda: threading.Thread(target=lambda: start_selected(True), daemon=True).start())
    btn_end = tk.Button(frame_controls, text="Kết thúc tất cả", width=15, command=end_all_auto)
    btn_open_tdata = tk.Button(frame_controls, text="Mở thư mục", width=15, command=open_tdata_folder)
    btn_remove_tdata = tk.Button(frame_controls, text="Xóa Tdata", width=15, command=remove_tdata)
    btn_reset_table = tk.Button(frame_controls, text="Reset trạng thái", width=15, command=reset_table_status)
    btn_start_all.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
    btn_start_selected.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")
    btn_end.grid(row=1, column=0, padx=5, pady=5, sticky="nsew")
    btn_open_tdata.grid(row=1, column=1, padx=5, pady=5, sticky="nsew")
    btn_remove_tdata.grid(row=2, column=0, padx=5, pady=5, sticky="nsew")
    btn_reset_table.grid(row=2, column=1, padx=5, pady=5, sticky="nsew")
    frame_controls.grid_columnconfigure(0, weight=1)
    frame_controls.grid_columnconfigure(1, weight=1)
    btn_restart = tk.Button(frame_controls, text="Khởi động lại toàn bộ", width=32, command=restart_module)
    btn_restart.grid(row=3, column=0, columnspan=2, padx=5, pady=5, sticky="nsew")
    frame_stats = tk.LabelFrame(frame_bottom, text="Thống kê phiên", padx=10, pady=10)
    frame_stats.grid(row=0, column=1, sticky="nsew", padx=5)
    lbl_stats_accounts = tk.Label(frame_stats, text="Tổng số tài khoản đã chạy: 0")
    lbl_stats_accounts.pack(anchor="w", pady=2)
    lbl_stats_loops = tk.Label(frame_stats, text="Tổng số vòng đã chạy: 0")
    lbl_stats_loops.pack(anchor="w", pady=2)
    lbl_stats_messages = tk.Label(frame_stats, text="Tổng số tin nhắn gửi được: 0")
    lbl_stats_messages.pack(anchor="w", pady=2)
    lbl_stats_contacts = tk.Label(frame_stats, text="Tổng số SĐT thêm vào danh bạ: 0")
    lbl_stats_contacts.pack(anchor="w", pady=2)
    lbl_stats_time = tk.Label(frame_stats, text="Tổng thời gian chạy: 0 giây")
    lbl_stats_time.pack(anchor="w", pady=2)

def auto_it_function(root, entry_path, lang, get_tdata_folders):
    print("Consolog: auto_it_function được gọi")
    logging.info("auto_it_function được gọi")
    auto_it_window(root, entry_path, lang, get_tdata_folders)

if __name__ == "__main__":
    print("Consolog: Khởi chạy chương trình AutoIT không dùng pywinauto")
    logging.info("Khởi chạy chương trình AutoIT không dùng pywinauto")
    root = tk.Tk()
    root.title("Chương trình AutoIT không dùng pywinauto")
    center_window(root, 600, 150)
    tk.Label(root, text="Đường dẫn chứa Tdata:").pack()
    entry_path = tk.Entry(root, width=50)
    entry_path.pack(pady=5)
    MAIN_HWND = root.winfo_id()

    def open_auto_it():
        print("Consolog: Mở AutoIT Feature từ cửa sổ chính")
        logging.info("Mở AutoIT Feature từ cửa sổ chính")
        auto_it_function(root, entry_path, None, get_tdata_folders)

    tk.Button(root, text="Mở AutoIT Feature", command=open_auto_it).pack(pady=10)
    root.mainloop()