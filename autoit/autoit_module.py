import os
import random
import time
import threading
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk, ImageChops
import ctypes
from ctypes import wintypes
import sys
import json
import logging

# Cấu hình logging để ghi log vào file auto_it.log
logging.basicConfig(filename="auto_it.log", level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")
logging.info("Khởi động chương trình AutoIT")

# ---------------------------
# PHẦN MỚI: Hàm run_script_dynamic() để chạy file .py hoặc .txt động (không dùng subprocess)
def run_script_dynamic(script_path, args=None):
    if not os.path.exists(script_path):
        print(f"Consolog: Không tìm thấy script {script_path}")
        logging.error(f"Consolog: Không tìm thấy script {script_path}")
        return

    try:
        with open(script_path, "r", encoding="utf-8") as f:
            script_code = f.read()

        exec_globals = {
            "__name__": "__main__",
            "__file__": script_path,
            "sys": sys,
        }

        # Cập nhật sys.argv để tương thích với các script nếu cần dùng
        sys.argv = [script_path] + (args if args else [])

        print(f"Consolog: Đang thực hiện nội dung script {script_path}")
        logging.info(f"Consolog: Đang thực hiện nội dung script {script_path}")
        exec(script_code, exec_globals)

    except Exception as e:
        print(f"Consolog: Lỗi khi chạy file script {script_path}: {e}")
        logging.error(f"Consolog: Lỗi khi chạy file script {script_path}: {e}")

# ---------------------------
# PHẦN CODE CHÍNH (giữ nguyên các phần không liên quan)
import os
import random
import time
import threading
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk, ImageChops
import ctypes
from ctypes import wintypes
import sys
import json
import logging

# (Phần import, cấu hình logging đã có ở trên)

# ---------------------------
# PHẦN MỚI: Hàm chạy script từ file .txt ưu tiên, fallback sang .py
def run_script_multithread():
    print("Consolog: Bắt đầu chạy đa luồng cho script (ưu tiên .txt)")
    logging.info("Bắt đầu chạy đa luồng cho script (ưu tiên .txt)")

    def run_script(thread_id):
        print(f"Consolog: [Thread {thread_id}] Đang khởi động...")
        script_txt = "your_script.txt"
        script_py = "your_script.py"
        if os.path.exists(script_txt):
            print(f"Consolog: [Thread {thread_id}] Đang chạy nội dung từ '{script_txt}' (ưu tiên)")
            logging.info(f"[Thread {thread_id}] Chạy từ .txt: {script_txt}")
            try:
                with open(script_txt, "r", encoding="utf-8") as f:
                    code = f.read()
                exec_globals = {}
                exec(code, exec_globals)
                print(f"Consolog: [Thread {thread_id}] Đã hoàn thành script .txt")
            except Exception as e:
                print(f"Consolog: [Thread {thread_id}] Lỗi khi chạy .txt: {e}")
                logging.error(f"[Thread {thread_id}] Lỗi chạy .txt: {e}")
        elif os.path.exists(script_py):
            print(f"Consolog: [Thread {thread_id}] Không có .txt, fallback sang chạy '{script_py}' bằng subprocess")
            logging.info(f"[Thread {thread_id}] Fallback sang subprocess: {script_py}")
            try:
                process = subprocess.Popen(["python", script_py])
                print(f"Consolog: [Thread {thread_id}] Đang chạy subprocess PID: {process.pid}")
                process.wait()
                print(f"Consolog: [Thread {thread_id}] Subprocess kết thúc")
            except Exception as e:
                print(f"Consolog: [Thread {thread_id}] Lỗi subprocess: {e}")
                logging.error(f"[Thread {thread_id}] Lỗi subprocess: {e}")
        else:
            print(f"Consolog: [Thread {thread_id}] Không tìm thấy file script nào để chạy!")
            logging.warning(f"[Thread {thread_id}] Không tìm thấy .txt hoặc .py")

    num_threads = 3
    threads = []
    for i in range(num_threads):
        thread = threading.Thread(target=run_script, args=(i,))
        thread.start()
        threads.append(thread)
        time.sleep(0.1)
    for thread in threads:
        thread.join()

    print("Consolog: Hoàn thành chạy đa luồng cho script")
    logging.info("Hoàn thành chạy đa luồng cho script")

# --- CHỈNH SỬA: Đặt DPI về 100% cho chế độ AutoIT --- 
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)  # 1: PROCESS_SYSTEM_DPI_AWARE
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

# ---------------------------
# Đặt biến toàn cục MAIN_HWND ban đầu
MAIN_HWND = None

# Hàm center_window: center cửa sổ vào giữa màn hình
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

# Định nghĩa ULONG_PTR nếu chưa có trong ctypes.wintypes
if not hasattr(wintypes, 'ULONG_PTR'):
    if sys.maxsize > 2**32:
        wintypes.ULONG_PTR = ctypes.c_ulonglong
    else:
        wintypes.ULONG_PTR = ctypes.c_ulong

# ---------------------------
# Các biến toàn cục cho chế độ ghi tọa độ
RECORD_IN_WINDOW = True   # True: tọa độ dạng relative theo cửa sổ (client), False: tọa độ tuyệt đối (screen)
RECORDED_DPI = None       # Tạm thời không sử dụng

# Cấu hình ctypes cho Windows Input
input_lock = threading.Lock()
SendInput = ctypes.windll.user32.SendInput

class MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx", wintypes.LONG),
        ("dy", wintypes.LONG),
        ("mouseData", wintypes.DWORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", wintypes.ULONG_PTR)
    ]

class KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk", wintypes.WORD),
        ("wScan", wintypes.WORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", wintypes.ULONG_PTR)
    ]

class INPUT(ctypes.Structure):
    class _INPUT(ctypes.Union):
        _fields_ = [("mi", MOUSEINPUT),
                    ("ki", KEYBDINPUT)]
    _anonymous_ = ("_input",)
    _fields_ = [
        ("type", wintypes.DWORD),
        ("_input", _INPUT)
    ]

def click(x, y):
    """
    Click chuột theo tọa độ màn hình tuyệt đối (dùng SendInput).
    (Mặc định: click chuột trái 1 lần)
    """
    if x < 0 or y < 0:
        print(f"Consolog: Tọa độ không hợp lệ ({x}, {y}), bỏ qua thao tác click.")
        logging.warning(f"Tọa độ không hợp lệ ({x}, {y}), bỏ qua thao tác click.")
        return
    screen_w = ctypes.windll.user32.GetSystemMetrics(0)
    screen_h = ctypes.windll.user32.GetSystemMetrics(1)
    dx = int(x * 65535 / screen_w)
    dy = int(y * 65535 / screen_h)

    def do_event(dwFlags):
        inp = INPUT(type=0)  # INPUT_MOUSE
        inp.mi.dx = dx
        inp.mi.dy = dy
        inp.mi.mouseData = 0
        inp.mi.dwFlags = dwFlags | 0x8000  # ABSOLUTE
        inp.mi.time = 0
        inp.mi.dwExtraInfo = 0
        with input_lock:
            SendInput(1, ctypes.byref(inp), ctypes.sizeof(inp))

    do_event(0x0001)  # MOVE
    do_event(0x0002)  # LEFTDOWN
    do_event(0x0004)  # LEFTUP
    logging.info(f"Thực hiện click tại ({x}, {y}) bằng SendInput.")

def click_down(x, y):
    """
    Thực hiện nhấn chuột (LEFTDOWN) tại tọa độ màn hình tuyệt đối.
    """
    if x < 0 or y < 0:
        print(f"Consolog: Tọa độ không hợp lệ ({x}, {y}), bỏ qua thao tác nhấn chuột.")
        logging.warning(f"Tọa độ không hợp lệ ({x}, {y}), bỏ qua thao tác nhấn chuột.")
        return
    screen_w = ctypes.windll.user32.GetSystemMetrics(0)
    screen_h = ctypes.windll.user32.GetSystemMetrics(1)
    dx = int(x * 65535 / screen_w)
    dy = int(y * 65535 / screen_h)
    def do_event(dwFlags):
        inp = INPUT(type=0)
        inp.mi.dx = dx
        inp.mi.dy = dy
        inp.mi.mouseData = 0
        inp.mi.dwFlags = dwFlags | 0x8000
        inp.mi.time = 0
        inp.mi.dwExtraInfo = 0
        with input_lock:
            SendInput(1, ctypes.byref(inp), ctypes.sizeof(inp))
    do_event(0x0001)  # MOVE
    do_event(0x0002)  # LEFTDOWN
    logging.info(f"Thực hiện nhấn chuột tại ({x}, {y}) bằng SendInput.")

def click_up(x, y):
    """
    Thực hiện nhả chuột (LEFTUP) tại tọa độ màn hình tuyệt đối.
    """
    if x < 0 or y < 0:
        print(f"Consolog: Tọa độ không hợp lệ ({x}, {y}), bỏ qua thao tác nhả chuột.")
        logging.warning(f"Tọa độ không hợp lệ ({x}, {y}), bỏ qua thao tác nhả chuột.")
        return
    screen_w = ctypes.windll.user32.GetSystemMetrics(0)
    screen_h = ctypes.windll.user32.GetSystemMetrics(1)
    dx = int(x * 65535 / screen_w)
    dy = int(y * 65535 / screen_h)
    def do_event(dwFlags):
        inp = INPUT(type=0)
        inp.mi.dx = dx
        inp.mi.dy = dy
        inp.mi.mouseData = 0
        inp.mi.dwFlags = dwFlags | 0x8000
        inp.mi.time = 0
        inp.mi.dwExtraInfo = 0
        with input_lock:
            SendInput(1, ctypes.byref(inp), ctypes.sizeof(inp))
    do_event(0x0001)  # MOVE
    do_event(0x0004)  # LEFTUP
    logging.info(f"Thực hiện nhả chuột tại ({x}, {y}) bằng SendInput.")

def press_key(vk):
    """
    Nhấn phím theo mã virtual key (SendInput).
    """
    inp = INPUT(type=1)  # INPUT_KEYBOARD
    inp.ki = KEYBDINPUT(wVk=vk, wScan=0, dwFlags=0, time=0, dwExtraInfo=0)
    with input_lock:
        SendInput(1, ctypes.byref(inp), ctypes.sizeof(inp))
    logging.info(f"Nhấn phím với mã: {vk}")

def release_key(vk):
    """
    Nhả phím theo mã virtual key (SendInput).
    """
    inp = INPUT(type=1)  # INPUT_KEYBOARD
    inp.ki = KEYBDINPUT(wVk=vk, wScan=0, dwFlags=0x0002, time=0, dwExtraInfo=0)
    with input_lock:
        SendInput(1, ctypes.byref(inp), ctypes.sizeof(inp))
    logging.info(f"Nhả phím với mã: {vk}")

# ---------------------------
# Import module win32 để điều chỉnh cửa sổ
try:
    import win32gui
    import win32con
    import win32process
    import win32api
except ImportError:
    win32gui = None
    win32con = None
    win32process = None
    win32api = None
    logging.error("Không import được win32 modules.")

# ---------------------------
# Hàm kiểm tra xem hwnd có thuộc cửa sổ Telegram hay không
def is_telegram_window(hwnd):
    if hwnd and win32gui and win32gui.IsWindow(hwnd):
        title = win32gui.GetWindowText(hwnd).lower()
        return "telegram" in title
    return False

def check_telegram_hwnd(hwnd):
    """
    Kiểm tra xem cửa sổ Telegram (bằng handle) có sẵn sàng để tự động hóa hay không.
    Thực hiện thử click vào vị trí trung tâm của cửa sổ.
    """
    if hwnd and is_telegram_window(hwnd):
        try:
            vi = VirtualInput(hwnd)
            rect = win32gui.GetWindowRect(hwnd)
            center_x = (rect[0] + rect[2]) // 2
            center_y = (rect[1] + rect[3]) // 2
            vi.mouse_click(center_x, center_y)
            logging.info(f"Consolog: Cửa sổ Telegram hwnd {hwnd} đã sẵn sàng.")
            return True
        except Exception as e:
            logging.error(f"Consolog: Lỗi kiểm tra cửa sổ Telegram: {e}")
            return False
    else:
        logging.warning("Consolog: Handle không hợp lệ hoặc không phải cửa sổ Telegram.")
        return False

# ---------------------------
# Lớp VirtualInput dùng PostMessage (nếu win32 có sẵn), fallback sang SendInput nếu hwnd không hợp lệ
class VirtualInput:
    def __init__(self, hwnd):
        self.hwnd = hwnd
        print(f"Consolog: VirtualInput - Khởi tạo cho cửa sổ có handle {self.hwnd}")
        logging.info(f"VirtualInput khởi tạo cho hwnd: {self.hwnd}")

    def send_key(self, vk_code):
        """
        Gửi phím vào cửa sổ bằng PostMessage, nếu hwnd hợp lệ.
        Fallback: SendInput nếu hwnd không hợp lệ.
        """
        if not self._is_hwnd_valid():
            press_key(vk_code)
            time.sleep(0.2)
            release_key(vk_code)
            return

        print(f"Consolog: VirtualInput - Gửi phím vk_code {vk_code} đến cửa sổ {self.hwnd}")
        logging.info(f"Gửi phím {vk_code} đến hwnd {self.hwnd}")
        try:
            win32gui.PostMessage(self.hwnd, win32con.WM_KEYDOWN, vk_code, 0)
            time.sleep(0.2)
            win32gui.PostMessage(self.hwnd, win32con.WM_KEYUP, vk_code, 0)
        except Exception as e:
            print(f"Consolog: Lỗi PostMessage send_key - fallback SendInput: {e}")
            logging.error(f"Lỗi PostMessage send_key: {e}, fallback SendInput.")
            press_key(vk_code)
            time.sleep(0.2)
            release_key(vk_code)

    def mouse_move(self, x, y):
        """
        Di chuyển chuột (PostMessage nếu hwnd hợp lệ, fallback SendInput).
        """
        if not self._is_hwnd_valid():
            self._move_absolute_screen(x, y)
            return

        print(f"Consolog: VirtualInput - mouse_move tới ({x}, {y}) cho hwnd {self.hwnd}")
        logging.info(f"mouse_move tới ({x}, {y}) cho hwnd {self.hwnd}")
        try:
            lParam = (y << 16) | (x & 0xFFFF)
            win32gui.PostMessage(self.hwnd, win32con.WM_MOUSEMOVE, 0, lParam)
        except Exception as e:
            print(f"Consolog: Lỗi PostMessage mouse_move - fallback SendInput: {e}")
            logging.error(f"Lỗi PostMessage mouse_move: {e}, fallback SendInput.")
            self._move_absolute_screen(x, y)

    def _move_absolute_screen(self, x, y):
        """
        Thực hiện di chuyển chuột trên toàn màn hình (SendInput).
        """
        screen_w = ctypes.windll.user32.GetSystemMetrics(0)
        screen_h = ctypes.windll.user32.GetSystemMetrics(1)
        dx = int(x * 65535 / screen_w)
        dy = int(y * 65535 / screen_h)

        inp = INPUT(type=0)  # INPUT_MOUSE
        inp.mi.dx = dx
        inp.mi.dy = dy
        inp.mi.mouseData = 0
        inp.mi.dwFlags = 0x0001 | 0x8000  # MOUSEEVENTF_MOVE | MOUSEEVENTF_ABSOLUTE
        inp.mi.time = 0
        inp.mi.dwExtraInfo = 0
        with input_lock:
            SendInput(1, ctypes.byref(inp), ctypes.sizeof(inp))

    def mouse_click(self, x, y, button="left", double=False):
        """
        Click chuột vào (x, y) - có thể là left / right / double click.
        Mặc định: button="left", double=False => single left click.
        """
        if x < 0 or y < 0:
            print("Consolog: Tọa độ không hợp lệ, bỏ qua thao tác click.")
            logging.warning("Tọa độ không hợp lệ, bỏ qua thao tác click.")
            return

        if not self._is_hwnd_valid():
            self._click_screen(x, y, button, double)
            time.sleep(0.2)
            return

        print(f"Consolog: VirtualInput - Gửi chuột click '{button}' tại ({x}, {y}), double={double}")
        logging.info(f"Gửi chuột click '{button}' tại ({x}, {y}) cho hwnd {self.hwnd}, double={double}")
        try:
            lParam = (y << 16) | (x & 0xFFFF)
            if button == "left":
                win32gui.PostMessage(self.hwnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, lParam)
                time.sleep(0.05)
                win32gui.PostMessage(self.hwnd, win32con.WM_LBUTTONUP, 0, lParam)
                if double:
                    time.sleep(0.05)
                    win32gui.PostMessage(self.hwnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, lParam)
                    time.sleep(0.05)
                    win32gui.PostMessage(self.hwnd, win32con.WM_LBUTTONUP, 0, lParam)
            elif button == "right":
                win32gui.PostMessage(self.hwnd, win32con.WM_RBUTTONDOWN, win32con.MK_RBUTTON, lParam)
                time.sleep(0.05)
                win32gui.PostMessage(self.hwnd, win32con.WM_RBUTTONUP, 0, lParam)
                if double:
                    time.sleep(0.05)
                    win32gui.PostMessage(self.hwnd, win32con.WM_RBUTTONDOWN, win32con.MK_RBUTTON, lParam)
                    time.sleep(0.05)
                    win32gui.PostMessage(self.hwnd, win32con.WM_RBUTTONUP, 0, lParam)
            else:
                pass
        except Exception as e:
            print(f"Consolog: Lỗi PostMessage mouse_click - fallback SendInput: {e}")
            logging.error(f"Lỗi PostMessage mouse_click: {e}, fallback SendInput.")
            self._click_screen(x, y, button, double)
            time.sleep(0.2)

    def _click_screen(self, x, y, button="left", double=False):
        screen_w = ctypes.windll.user32.GetSystemMetrics(0)
        screen_h = ctypes.windll.user32.GetSystemMetrics(1)
        dx = int(x * 65535 / screen_w)
        dy = int(y * 65535 / screen_h)

        def do_event(dwFlags):
            inp = INPUT(type=0)
            inp.mi.dx = dx
            inp.mi.dy = dy
            inp.mi.mouseData = 0
            inp.mi.dwFlags = dwFlags | 0x8000
            inp.mi.time = 0
            inp.mi.dwExtraInfo = 0
            with input_lock:
                SendInput(1, ctypes.byref(inp), ctypes.sizeof(inp))
        do_event(0x0001)  # MOVE

        if button == "left":
            do_event(0x0002)  # LEFTDOWN
            time.sleep(0.05)
            do_event(0x0004)  # LEFTUP
            if double:
                time.sleep(0.05)
                do_event(0x0002)
                time.sleep(0.05)
                do_event(0x0004)
        elif button == "right":
            do_event(0x0008)  # RIGHTDOWN
            time.sleep(0.05)
            do_event(0x0010)  # RIGHTUP
            if double:
                time.sleep(0.05)
                do_event(0x0008)
                time.sleep(0.05)
                do_event(0x0010)

    def mouse_drag(self, x1, y1, x2, y2, steps=20, interval=0.01):
        """
        Kéo chuột từ (x1, y1) đến (x2, y2).
        steps: số bước di chuột trung gian (cho chuyển động mượt).
        interval: thời gian dừng giữa mỗi bước.
        """
        if not self._is_hwnd_valid():
            print("Consolog: fallback drag = SendInput tuyệt đối màn hình")
            logging.info("fallback drag = SendInput tuyệt đối màn hình")
            self._drag_screen(x1, y1, x2, y2, steps, interval)
            return

        print(f"Consolog: VirtualInput - drag từ ({x1}, {y1}) -> ({x2}, {y2}) cho hwnd {self.hwnd}")
        logging.info(f"drag ({x1}, {y1}) -> ({x2}, {y2}) cho hwnd {self.hwnd}")
        try:
            lParam1 = (y1 << 16) | (x1 & 0xFFFF)
            win32gui.PostMessage(self.hwnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, lParam1)
            time.sleep(0.05)
            dx = (x2 - x1) / steps
            dy = (y2 - y1) / steps
            for i in range(steps):
                cx = int(x1 + dx * i)
                cy = int(y1 + dy * i)
                lParamMid = (cy << 16) | (cx & 0xFFFF)
                win32gui.PostMessage(self.hwnd, win32con.WM_MOUSEMOVE, win32con.MK_LBUTTON, lParamMid)
                time.sleep(interval)
            lParam2 = (y2 << 16) | (x2 & 0xFFFF)
            win32gui.PostMessage(self.hwnd, win32con.WM_MOUSEMOVE, win32con.MK_LBUTTON, lParam2)
            time.sleep(0.05)
            win32gui.PostMessage(self.hwnd, win32con.WM_LBUTTONUP, 0, lParam2)
            time.sleep(0.05)
        except Exception as e:
            print(f"Consolog: Lỗi PostMessage mouse_drag - fallback SendInput: {e}")
            logging.error(f"Lỗi PostMessage mouse_drag: {e}, fallback SendInput.")
            self._drag_screen(x1, y1, x2, y2, steps, interval)

    def _drag_screen(self, x1, y1, x2, y2, steps=20, interval=0.01):
        def move_abs(x, y, flags):
            screen_w = ctypes.windll.user32.GetSystemMetrics(0)
            screen_h = ctypes.windll.user32.GetSystemMetrics(1)
            dx = int(x * 65535 / screen_w)
            dy = int(y * 65535 / screen_h)
            inp = INPUT(type=0)
            inp.mi.dx = dx
            inp.mi.dy = dy
            inp.mi.mouseData = 0
            inp.mi.dwFlags = flags | 0x8000
            inp.mi.time = 0
            inp.mi.dwExtraInfo = 0
            with input_lock:
                SendInput(1, ctypes.byref(inp), ctypes.sizeof(inp))
        move_abs(x1, y1, 0x0001)
        move_abs(x1, y1, 0x0002)
        time.sleep(0.05)
        dx = (x2 - x1) / steps
        dy = (y2 - y1) / steps
        for i in range(steps):
            cx = x1 + dx * i
            cy = y1 + dy * i
            move_abs(cx, cy, 0x0001)
            time.sleep(interval)
        move_abs(x2, y2, 0x0001)
        time.sleep(0.05)
        move_abs(x2, y2, 0x0004)
        time.sleep(0.05)

    def mouse_scroll(self, amount=1, horizontal=False):
        """
        Cuộn chuột (dọc hoặc ngang), fallback SendInput nếu cần.
        amount > 0 => cuộn lên/ trái
        amount < 0 => cuộn xuống/ phải
        horizontal=True => cuộn ngang
        """
        if not self._is_hwnd_valid():
            self._scroll_screen(amount, horizontal)
            return

        print(f"Consolog: VirtualInput - mouse_scroll: {amount}, horizontal={horizontal}")
        logging.info(f"mouse_scroll: {amount}, horizontal={horizontal} cho hwnd {self.hwnd}")
        try:
            if not horizontal:
                delta = amount * 120
                wParam = (delta << 16)
                lParam = 0
                win32gui.PostMessage(self.hwnd, win32con.WM_MOUSEWHEEL, wParam, lParam)
            else:
                delta = amount * 120
                wParam = (delta << 16)
                lParam = 0
                win32gui.PostMessage(self.hwnd, 0x020E, wParam, lParam)
        except Exception as e:
            print(f"Consolog: Lỗi PostMessage mouse_scroll - fallback: {e}")
            logging.error(f"Lỗi mouse_scroll: {e}, fallback SendInput.")
            self._scroll_screen(amount, horizontal)

    def _scroll_screen(self, amount=1, horizontal=False):
        flags = 0x0800 if not horizontal else 0x1000
        delta = amount * 120

        inp = INPUT(type=0)
        inp.mi.dx = 0
        inp.mi.dy = 0
        inp.mi.mouseData = delta & 0xFFFFFFFF
        inp.mi.dwFlags = flags
        inp.mi.time = 0
        inp.mi.dwExtraInfo = 0
        with input_lock:
            SendInput(1, ctypes.byref(inp), ctypes.sizeof(inp))

    def send_text(self, text):
        """
        Gửi 1 chuỗi text (mô phỏng gõ bàn phím).
        - Mỗi ký tự chuyển thành WM_CHAR hoặc fallback SendInput (ASCII).
        """
        print(f"Consolog: VirtualInput - Gửi text: {text}")
        logging.info(f"Gửi text: {text} cho hwnd {self.hwnd}")
        for ch in text:
            self._send_char(ch)
            time.sleep(0.01)

    def _send_char(self, ch):
        if not self._is_hwnd_valid():
            self._send_char_screen(ch)
            return
        try:
            win32gui.PostMessage(self.hwnd, win32con.WM_CHAR, ord(ch), 0)
        except Exception as e:
            print(f"Consolog: Lỗi PostMessage send_char - fallback SendInput: {e}")
            logging.error(f"Lỗi PostMessage send_char: {e}, fallback SendInput.")
            self._send_char_screen(ch)

    def _send_char_screen(self, ch):
        if not win32api:
            return
        vk_code = win32api.VkKeyScan(ch) & 0xFF
        press_key(vk_code)
        time.sleep(0.01)
        release_key(vk_code)

    def _is_hwnd_valid(self):
        if not win32gui or not self.hwnd:
            return False
        if not win32gui.IsWindow(self.hwnd):
            return False
        if not win32gui.IsWindowVisible(self.hwnd):
            return False
        return True

# ---------------------------
# Hàm lấy HWND theo PID
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

def create_virtual_input(hwnd):
    print(f"Consolog: Tạo đối tượng VirtualInput cho cửa sổ có handle: {hwnd}")
    logging.info(f"Tạo VirtualInput cho hwnd: {hwnd}")
    return VirtualInput(hwnd)

# ---------------------------
# Hàm lấy danh sách Tdata từ thư mục
def get_tdata_folders(tdata_dir):
    print("Consolog: Lấy danh sách Tdata từ thư mục:", tdata_dir)
    logging.info(f"Lấy danh sách Tdata từ thư mục: {tdata_dir}")
    if os.path.isdir(tdata_dir):
        return [os.path.join(tdata_dir, d) for d in os.listdir(tdata_dir) if os.path.isdir(os.path.join(tdata_dir, d))]
    return []

# ---------------------------
# *** THÊM HÀM CHECK_PAUSE ***
def check_pause(pause_event):
    """Nếu pause_event được set, chờ đến khi được clear."""
    if pause_event and pause_event.is_set():
        print("Consolog: [check_pause] Đang ở trạng thái tạm dừng, chờ tiếp...")
        while pause_event.is_set():
            time.sleep(0.1)
        print("Consolog: [check_pause] Tiếp tục sau khi tạm dừng.")

# ---------------------------
# Hàm delay có khả năng tạm dừng (CHỈNH SỬA: gọi check_pause)
def wait_with_pause(duration, local_pause_event=None, local_stop_event=None):
    print("Consolog: Bắt đầu wait_with_pause với thời gian:", duration)
    logging.info(f"Bắt đầu wait_with_pause trong {duration} giây")
    start_time = time.time()
    interval = 0.05
    while time.time() - start_time < duration:
        if local_stop_event and local_stop_event.is_set():
            print("Consolog: Nhận tín hiệu dừng trong wait_with_pause")
            logging.info("Nhận tín hiệu dừng trong wait_with_pause")
            break
        if local_pause_event:
            check_pause(local_pause_event)
        time.sleep(interval)
    print("Consolog: Kết thúc wait_with_pause")
    logging.info("Kết thúc wait_with_pause")

# ---------------------------
# Hàm kiểm tra và di chuyển cửa sổ về vị trí mặc định nếu chưa đúng.
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

# --- Các hàm bảo vệ cập nhật giao diện ---
def safe_get_tree_item(tree, row):
    try:
        if tree.winfo_exists():
            return tree.item(row, "values")
    except Exception as e:
        logging.error("Lỗi truy xuất Treeview item: %s", e)
    return None

def safe_update_row_status(row, status):
    try:
        if tree.winfo_exists() and row in tree.get_children():
            vals = list(tree.item(row, "values"))
            vals[5] = status
            tree.item(row, values=vals)
            print(f"Consolog: {vals[1]} - {status}")
            logging.info(f"{vals[1]} - {status}")
    except Exception as e:
        print("Consolog: Lỗi cập nhật row:", e)
        logging.error(f"Lỗi cập nhật row: {e}")

def safe_update_progress(progress):
    try:
        if lbl_progress_auto.winfo_exists():
            progress_var_auto.set(progress)
            lbl_progress_auto.config(text=f"{int(progress)}%")
    except Exception as e:
        print("Consolog: Lỗi cập nhật progress:", e)
        logging.error(f"Lỗi cập nhật progress: {e}")

# ---------------------------
# Lớp ScriptEditor (giữ nguyên)
class ScriptEditor(tk.Toplevel):
    def __init__(self, master, script_file):
        super().__init__(master)
        self.script_file = script_file
        self.title("Script Editor: " + script_file)
        self.geometry("800x600")

        menubar = tk.Menu(self)
        filemenu = tk.Menu(menubar, tearoff=0)
        filemenu.add_command(label="Open", command=self.open_file)
        filemenu.add_command(label="Save", command=self.save_file)
        filemenu.add_command(label="Save As", command=self.save_as)
        filemenu.add_separator()
        filemenu.add_command(label="Exit", command=self.destroy)
        menubar.add_cascade(label="File", menu=filemenu)
        self.config(menu=menubar)

        self.text_frame = tk.Frame(self)
        self.text_frame.pack(fill=tk.BOTH, expand=True)

        self.linenumbers = tk.Text(self.text_frame, width=4, padx=4, takefocus=0, border=0,
                                   background='lightgrey', state='disabled')
        self.linenumbers.pack(side=tk.LEFT, fill=tk.Y)

        self.scrollbar = tk.Scrollbar(self.text_frame)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.text = tk.Text(self.text_frame, wrap='none', yscrollcommand=self.scrollbar.set)
        self.text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.config(command=self.text.yview)

        self.text.bind("<KeyRelease>", self.update_line_numbers)
        self.text.bind("<MouseWheel>", self.update_line_numbers)
        self.text.bind("<Button-1>", self.update_line_numbers)

        if os.path.exists(script_file):
            with open(script_file, "r", encoding="utf-8") as f:
                content = f.read()
            self.text.insert("1.0", content)
        else:
            self.text.insert("1.0", "# Mã script mặc định cho " + script_file + "\n")
        self.update_line_numbers()

    def update_line_numbers(self, event=None):
        self.linenumbers.config(state='normal')
        self.linenumbers.delete("1.0", tk.END)
        total_lines = int(self.text.index('end-1c').split('.')[0])
        for i in range(1, total_lines + 1):
            self.linenumbers.insert(tk.END, f"{i}\n")
        self.linenumbers.config(state='disabled')

    def open_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("Python Files", "*.py"), ("All Files", "*.*")])
        if file_path:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            self.text.delete("1.0", tk.END)
            self.text.insert("1.0", content)
            self.script_file = file_path
            self.title("Script Editor: " + file_path)
            self.update_line_numbers()

    def save_file(self):
        try:
            with open(self.script_file, "w", encoding="utf-8") as f:
                content = self.text.get("1.0", tk.END)
                f.write(content)
            messagebox.showinfo("Save", "Script saved to " + self.script_file)
        except Exception as e:
            messagebox.showerror("Error", "Lỗi khi lưu file: " + str(e))

    def save_as(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".py",
                                                 filetypes=[("Python Files", "*.py"), ("All Files", "*.*")])
        if file_path:
            self.script_file = file_path
            self.save_file()
            self.title("Script Editor: " + file_path)

# ---------------------------
# Hàm run_json_script đã được sửa để xử lý file JSON với khóa "events" theo định dạng nguyên bản
# CHỈNH SỬA: Thêm đối tượng pause_event để hỗ trợ tạm dừng toàn bộ vòng lặp JSON
def run_json_script(json_content, pause_event=None):
    logging.info("Bắt đầu chạy JSON script với nội dung: %s", json_content)
    
    global RECORD_IN_WINDOW
    # Cấu hình coord_mode
    if "coord_mode" in json_content:
        coord_mode = json_content.get("coord_mode")
        if coord_mode == "client":
            RECORD_IN_WINDOW = True
            print("Consolog: Đang sử dụng tọa độ tương đối (client).")
            logging.info("Đang sử dụng tọa độ tương đối (client).")
        elif coord_mode == "screen":
            RECORD_IN_WINDOW = False
            print("Consolog: Đang sử dụng tọa độ tuyệt đối (screen).")
            logging.info("Đang sử dụng tọa độ tuyệt đối (screen).")
    else:
        RECORD_IN_WINDOW = True
        print("Consolog: Không tìm thấy 'coord_mode' trong JSON, sử dụng mặc định: client.")
        logging.info("Không tìm thấy 'coord_mode' trong JSON, sử dụng mặc định: client.")
    
    target_hwnd = json_content.get("window_handle")
    if not target_hwnd or not is_telegram_window(target_hwnd):
        if win32gui:
            target_hwnd = get_telegram_hwnd_by_pid(
                win32process.GetWindowThreadProcessId(
                    win32gui.GetForegroundWindow()
                )[1]
            )
        else:
            target_hwnd = None

    if not is_telegram_window(target_hwnd):
        print("Consolog: Cửa sổ mục tiêu không phải Telegram, không thực hiện auto.")
        logging.warning("Cửa sổ mục tiêu không phải Telegram.")
        return

    if not check_telegram_hwnd(target_hwnd):
        print("Consolog: Cửa sổ Telegram chưa sẵn sàng, dừng chạy JSON script.")
        logging.warning("Cửa sổ Telegram chưa sẵn sàng.")
        return

    vi = VirtualInput(target_hwnd) if target_hwnd else None

    # Nếu JSON có khóa "events", sử dụng định dạng nguyên bản
    if "events" in json_content:
        events = json_content["events"]
        prev_time = 0
        for event in events:
            # CHỈNH SỬA: Kiểm tra trạng thái pause trước khi xử lý mỗi event
            if pause_event and pause_event.is_set():
                print("Consolog: JSON script đang tạm dừng, chờ...")
                logging.info("JSON script đang tạm dừng, chờ...")
            while pause_event and pause_event.is_set():
                print("Consolog: JSON script đang ở trạng thái tạm dừng, chờ tiếp...")
                logging.info("JSON script ở trạng thái tạm dừng")
                time.sleep(0.1)
            current_time = event.get("time", 0)
            delay_duration = current_time - prev_time
            if delay_duration > 0:
                wait_with_pause(delay_duration, pause_event, None)
            # Sau delay, lại kiểm tra pause
            if pause_event:
                check_pause(pause_event)
            event_type = event.get("type")
            if event_type == "move":
                pos = event.get("position", [0, 0])
                print(f"Consolog: Di chuyển chuột tới {pos}")
                if RECORD_IN_WINDOW and vi:
                    vi.mouse_move(pos[0], pos[1])
            elif event_type == "click":
                pos = event.get("position", [0, 0])
                pressed = event.get("pressed", True)
                if pressed:
                    print(f"Consolog: Nhấn chuột tại {pos}")
                    if RECORD_IN_WINDOW and vi:
                        click_down(pos[0], pos[1])
                    else:
                        click_down(pos[0], pos[1])
                else:
                    print(f"Consolog: Nhả chuột tại {pos}")
                    if RECORD_IN_WINDOW and vi:
                        click_up(pos[0], pos[1])
                    else:
                        click_up(pos[0], pos[1])
            elif event_type == "keypress":
                key = event.get("key")
                if key is not None:
                    print(f"Consolog: Nhấn và nhả phím với mã: {key}")
                    logging.info(f"Nhấn và nhả phím với mã: {key}")
                    if vi:
                        vi.send_key(key)
                    else:
                        press_key(key)
                        time.sleep(0.1)
                        release_key(key)
            elif event_type == "key_press":
                key = event.get("key")
                if key is not None:
                    print(f"Consolog: Nhấn phím (down) với mã: {key}")
                    logging.info(f"Nhấn phím (down) với mã: {key}")
                    try:
                        vk = int(key)
                    except ValueError:
                        if win32api:
                            vk = win32api.VkKeyScan(key) & 0xFF
                        else:
                            vk = ord(key)
                    if vi:
                        press_key(vk)
                    else:
                        press_key(vk)
            elif event_type == "key_release":
                key = event.get("key")
                if key is not None:
                    print(f"Consolog: Nhả phím (up) với mã: {key}")
                    logging.info(f"Nhả phím (up) với mã: {key}")
                    try:
                        vk = int(key)
                    except ValueError:
                        if win32api:
                            vk = win32api.VkKeyScan(key) & 0xFF
                        else:
                            vk = ord(key)
                    if vi:
                        release_key(vk)
                    else:
                        release_key(vk)
            elif event_type == "send_text":
                text = event.get("text", "")
                print(f"Consolog: Gửi text: {text}")
                if vi:
                    vi.send_text(text)
                else:
                    if win32api:
                        for ch in text:
                            vk_code = win32api.VkKeyScan(ch) & 0xFF
                            press_key(vk_code)
                            time.sleep(0.01)
                            release_key(vk_code)
            elif event_type == "scroll":
                dx = event.get("dx", 0)
                dy = event.get("dy", 0)
                print(f"Consolog: Cuộn chuột với dx={dx}, dy={dy}")
                if vi:
                    if dy != 0:
                        vi.mouse_scroll(dy, horizontal=False)
                    if dx != 0:
                        vi.mouse_scroll(dx, horizontal=True)
            elif event_type == "delay":
                duration = event.get("duration", 1)
                print(f"Consolog: Thực hiện delay {duration} giây")
                time.sleep(duration)
            else:
                print("Consolog: Bỏ qua event không xác định:", event)
                logging.info(f"Bỏ qua event không xác định: {event}")
            prev_time = current_time
    else:
        for act in json_content.get("actions", []):
            if not isinstance(act, dict):
                logging.error(f"Action không hợp lệ (không phải dict): {act}")
                continue

            action_type = act.get("action") or act.get("type")
            logging.info(f"Thực hiện action: {act}")

            if action_type == "click":
                x = act.get("x", 0)
                y = act.get("y", 0)
                print(f"Consolog: Thực hiện click tại ({x}, {y})")
                if RECORD_IN_WINDOW and vi:
                    vi.mouse_click(x, y, button="left", double=False)
                else:
                    click(x, y)
            elif action_type == "double_click":
                x = act.get("x", 0)
                y = act.get("y", 0)
                print(f"Consolog: Double click tại ({x}, {y})")
                if RECORD_IN_WINDOW and vi:
                    vi.mouse_click(x, y, button="left", double=True)
                else:
                    click(x, y)
                    time.sleep(0.05)
                    click(x, y)
            elif action_type == "right_click":
                x = act.get("x", 0)
                y = act.get("y", 0)
                print(f"Consolog: Right click tại ({x}, {y})")
                if RECORD_IN_WINDOW and vi:
                    vi.mouse_click(x, y, button="right", double=False)
            elif action_type == "move":
                x = act.get("x", 0)
                y = act.get("y", 0)
                print(f"Consolog: Di chuyển chuột tới ({x}, {y})")
                if RECORD_IN_WINDOW and vi:
                    vi.mouse_move(x, y)
            elif action_type == "drag":
                start = act.get("start", [0, 0])
                end = act.get("end", [0, 0])
                print(f"Consolog: Kéo thả từ {start} -> {end}")
                if RECORD_IN_WINDOW and vi:
                    vi.mouse_drag(start[0], start[1], end[0], end[1], steps=20, interval=0.01)
            elif action_type == "scroll":
                amount = act.get("amount", 1)
                horizontal = act.get("horizontal", False)
                print(f"Consolog: Cuộn chuột amount={amount}, horizontal={horizontal}")
                if vi:
                    vi.mouse_scroll(amount, horizontal)
            elif action_type == "keypress":
                key = act.get("key")
                if key is not None:
                    print(f"Consolog: Nhấn phím với mã: {key}")
                    if vi:
                        vi.send_key(key)
                    else:
                        press_key(key)
                        time.sleep(0.1)
                        release_key(key)
            elif action_type == "send_text":
                text = act.get("text", "")
                print(f"Consolog: Gửi text: {text}")
                if vi:
                    vi.send_text(text)
                else:
                    if win32api:
                        for ch in text:
                            vk_code = win32api.VkKeyScan(ch) & 0xFF
                            press_key(vk_code)
                            time.sleep(0.01)
                            release_key(vk_code)
            elif action_type == "delay":
                duration = act.get("duration", 1)
                print(f"Consolog: Thực hiện delay {duration} giây")
                time.sleep(duration)
            else:
                print("Consolog: Bỏ qua action không xác định:", act)
                logging.info(f"Bỏ qua action không xác định: {act}")

# ---------------------------
# Hàm open_edit_script (đã chỉnh sửa)
def open_edit_script(script_file, master):
    print("Consolog: Mở Script Editor cho file:", script_file)
    logging.info(f"Mở Script Editor cho file: {script_file}")
    
    config_file = "run_mode_config.json"
    default_mode = "python"
    if os.path.exists(config_file):
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                config = json.load(f)
            default_mode = config.get("run_mode", "python")
        except Exception as e:
            print("Consolog: Lỗi đọc file config:", e)
            logging.error(f"Lỗi đọc file config: {e}")
    
    editor_win = tk.Toplevel(master)
    editor_win.title("Edit Script: " + script_file)
    editor_win.geometry("800x650")
    
    mode_frame = tk.Frame(editor_win)
    mode_frame.pack(fill='x', padx=5, pady=5)
    tk.Label(mode_frame, text="Chọn chế độ chạy:").pack(side=tk.LEFT)
    run_mode = tk.StringVar(value=default_mode)
    rb_python = tk.Radiobutton(mode_frame, text="Python", variable=run_mode, value="python")
    rb_json = tk.Radiobutton(mode_frame, text="JSON", variable=run_mode, value="json")
    rb_python.pack(side=tk.LEFT, padx=10)
    rb_json.pack(side=tk.LEFT, padx=10)
    
    notebook = ttk.Notebook(editor_win)
    notebook.pack(fill='both', expand=True, padx=5, pady=5)
    
    py_frame = tk.Frame(notebook)
    json_frame = tk.Frame(notebook)
    
    # CHỈNH SỬA: Đổi nhãn của tab Python từ (.py) sang (.txt)
    notebook.add(py_frame, text="Python Script (.txt)")
    notebook.add(json_frame, text="JSON Script")
    
    py_text = tk.Text(py_frame, wrap='none')
    py_text.pack(fill='both', expand=True)
    json_text = tk.Text(json_frame, wrap='none')
    json_text.pack(fill='both', expand=True)
    
    if os.path.exists(script_file):
        with open(script_file, "r", encoding="utf-8") as f:
            content = f.read()
        py_text.insert("1.0", content)
    else:
        py_text.insert("1.0", "# Mã script mặc định cho " + script_file + "\n")
    json_file = os.path.splitext(script_file)[0] + ".json"
    if os.path.exists(json_file):
        with open(json_file, "r", encoding="utf-8") as f:
            json_content = f.read()
        json_text.insert("1.0", json_content)
    
    def save_script_edit():
        try:
            with open(config_file, "w", encoding="utf-8") as f:
                json.dump({"run_mode": run_mode.get()}, f)
            print("Consolog: Đã lưu run_mode =", run_mode.get())
            logging.info(f"Đã lưu run_mode = {run_mode.get()}")
        except Exception as e:
            print("Consolog: Lỗi khi lưu run_mode:", e)
            logging.error(f"Lỗi khi lưu run_mode: {e}")

        current_tab = notebook.tab(notebook.select(), "text")
        if current_tab.startswith("Python"):
            content = py_text.get("1.0", tk.END)
            # CHỈNH SỬA: Lưu file script dạng text (.txt) thay vì .py
            file_to_save = os.path.splitext(script_file)[0] + ".txt"
            print("Consolog: Lưu script dạng TEXT với định dạng (.txt)")
            logging.info("Lưu script dạng TEXT với định dạng (.txt)")
        else:
            content = json_text.get("1.0", tk.END)
            file_to_save = os.path.splitext(script_file)[0] + ".json"
        try:
            with open(file_to_save, "w", encoding="utf-8") as f:
                f.write(content)
            messagebox.showinfo("Save", "Script saved to " + file_to_save)
            logging.info(f"Lưu script thành công: {file_to_save}")
        except Exception as e:
            messagebox.showerror("Error", "Lỗi khi lưu file: " + str(e))
            logging.error(f"Lỗi khi lưu file: {e}")
    
    def run_script():
        save_script_edit()
        base_name = os.path.splitext(script_file)[0]
        current_tab = notebook.tab(notebook.select(), "text")
        if current_tab.startswith("Python"):
            # CHỈNH SỬA: Chạy file script dạng text (.txt) thay vì .py
            file_to_run = base_name + ".txt"
            print("Consolog: Chọn chạy file script dạng TEXT (.txt)")
            logging.info("Chọn chạy file script dạng TEXT (.txt)")
        else:
            file_to_run = base_name + ".json"

        if file_to_run.endswith(".txt"):
            try:
                # SỬ DỤNG RUN_SCRIPT_DYNAMIC thay vì subprocess.run
                print(f"Consolog: Đang thực thi script {file_to_run} cho HWND không xác định")
                run_script_dynamic(file_to_run)
                messagebox.showinfo("Run", "Python script chạy thành công!")
                logging.info(f"Chạy Python script thành công: {file_to_run}")
            except Exception as e:
                messagebox.showerror("Run Error", f"Lỗi khi chạy Python script: {str(e)}")
                logging.error(f"Lỗi khi chạy Python script {file_to_run}: {e}")
        elif file_to_run.endswith(".json"):
            try:
                with open(file_to_run, "r", encoding="utf-8") as f:
                    json_data = json.load(f)
                if isinstance(json_data, list):
                    json_data = {"events": json_data}
                threading.Thread(target=run_json_script, args=(json_data,), daemon=True).start()
                messagebox.showinfo("Run", "JSON script chạy thành công!")
                logging.info(f"Khởi chạy thread cho JSON script: {file_to_run}")
            except Exception as e:
                messagebox.showerror("Run Error", f"Lỗi khi chạy JSON script: {str(e)}")
                logging.error(f"Lỗi khi chạy JSON script: {file_to_run}: {e}")
    
    btn_frame = tk.Frame(editor_win)
    btn_frame.pack(pady=5)
    btn_save = tk.Button(btn_frame, text="Save", command=save_script_edit)
    btn_save.pack(side=tk.LEFT, padx=5)
    btn_run = tk.Button(btn_frame, text="Run Script", command=run_script)
    btn_run.pack(side=tk.LEFT, padx=5)

# ---------------------------
# Các hàm và module phía dưới giữ nguyên
try:
    from script_builder import ScriptBuilder
except ImportError:
    ScriptBuilder = None
    print("Consolog: Không tìm thấy script_builder.py hoặc lỗi import ScriptBuilder.")
    logging.error("Không tìm thấy script_builder.py hoặc lỗi import ScriptBuilder.")

# ---------------------------
# Dùng pynput cho tính năng 'Chụp Tọa độ'
try:
    from pynput import mouse as pmouse, keyboard as pkeyboard
    PYNPUT_AVAILABLE = True
except ImportError:
    PYNPUT_AVAILABLE = False

GLOBAL_TELEGRAM_HWND = None
GLOBAL_OFFSET_X = 0
GLOBAL_OFFSET_Y = 0

def convert_to_relative(abs_x, abs_y):
    """
    Chuyển (abs_x, abs_y) -> tọa độ so với cửa sổ Telegram
    """
    if GLOBAL_TELEGRAM_HWND and win32gui:
        return (abs_x - GLOBAL_OFFSET_X, abs_y - GLOBAL_OFFSET_Y)
    else:
        return (abs_x, abs_y)

CAPTURING_COORDINATE = False
CAPTURE_RESULT = None
def capture_coordinate():
    """
    Bật chế độ 'chụp' 1 lần click rồi lấy tọa độ
    """
    global CAPTURING_COORDINATE, CAPTURE_RESULT
    if not PYNPUT_AVAILABLE:
        messagebox.showerror("Lỗi", "Chưa cài đặt module pynput. Vui lòng cài pynput.")
        return
    CAPTURING_COORDINATE = True
    CAPTURE_RESULT = None

    def on_click(x, y, button, pressed):
        global CAPTURING_COORDINATE, CAPTURE_RESULT
        if CAPTURING_COORDINATE and pressed:
            rel = convert_to_relative(x, y)
            CAPTURE_RESULT = rel
            CAPTURING_COORDINATE = False
            m_listener.stop()
            messagebox.showinfo("Tọa độ", f"Tọa độ (theo cửa sổ Telegram): {rel}\nĐã copy vào clipboard.")
            try:
                import pyperclip
                pyperclip.copy(f"{rel[0]}, {rel[1]}")
            except:
                pass

    m_listener = pmouse.Listener(on_click=on_click)
    m_listener.start()
    messagebox.showinfo("Chụp Tọa độ", "Hãy click chuột vào điểm cần lấy tọa độ (trong cửa sổ Telegram).")

# Tính năng tìm & click hình ảnh (naive)
def screenshot_window(hwnd):
    """
    Chụp ảnh cửa sổ hwnd, trả về PIL Image.
    """
    if not win32gui or not hwnd:
        return None
    rect = win32gui.GetWindowRect(hwnd)
    w = rect[2] - rect[0]
    h = rect[3] - rect[1]
    try:
        import win32ui
        import win32.lib.win32con as win32con_mod
        hwin = win32gui.GetDesktopWindow()
        left, top, right, bot = rect
        width = right - left
        height = bot - top

        hdc = win32gui.GetWindowDC(hwnd)
        new_dc = win32ui.CreateDCFromHandle(hdc)
        mem_dc = new_dc.CreateCompatibleDC()
        screenshot = win32ui.CreateBitmap()
        screenshot.CreateCompatibleBitmap(new_dc, width, height)
        mem_dc.SelectObject(screenshot)
        mem_dc.BitBlt((0, 0), (width, height), new_dc, (0, 0), win32con_mod.SRCCOPY)

        bmpinfo = screenshot.GetInfo()
        bmpstr = screenshot.GetBitmapBits(True)
        im = Image.frombuffer(
            'RGB',
            (bmpinfo['bmWidth'], bmpinfo['bmHeight']),
            bmpstr, 'raw', 'BGRX', 0, 1
        )

        win32gui.ReleaseDC(hwnd, hdc)
        mem_dc.DeleteDC()
        new_dc.DeleteDC()
        win32gui.DeleteObject(screenshot.GetHandle())

        return im
    except:
        return None

def find_image_in_image(haystack, needle):
    """
    Tìm needle (PIL Image) trong haystack (PIL Image).
    Trả về (x, y) hoặc None nếu không tìm thấy.
    """
    H, W = haystack.size
    h, w = needle.size
    haystack_pixels = haystack.load()
    needle_pixels = needle.load()

    for y in range(H - h + 1):
        for x in range(W - w + 1):
            match = True
            for ny in range(h):
                for nx in range(w):
                    if haystack_pixels[x + nx, y + ny] != needle_pixels[nx, ny]:
                        match = False
                        break
                if not match:
                    break
            if match:
                return (x, y)
    return None

def search_and_click_image(hwnd, image_path):
    """
    Chụp ảnh cửa sổ hwnd -> tìm image_path -> nếu thấy thì click.
    """
    if not os.path.isfile(image_path):
        print(f"Consolog: Không tìm thấy file ảnh {image_path}")
        logging.error(f"Không tìm thấy file ảnh: {image_path}")
        return

    haystack = screenshot_window(hwnd)
    if haystack is None:
        print("Consolog: Không chụp được ảnh cửa sổ.")
        logging.error("Không chụp được ảnh cửa sổ.")
        return

    needle = Image.open(image_path)
    pos = find_image_in_image(haystack, needle)
    if pos is not None:
        nx = pos[0] + needle.size[0]//2
        ny = pos[1] + needle.size[1]//2
        vi = create_virtual_input(hwnd)
        vi.mouse_click(nx, ny)
        print(f"Consolog: Đã click vào hình {image_path} tại tọa độ {nx}, {ny} trong cửa sổ.")
        logging.info(f"Đã click vào {image_path} tại ({nx}, {ny}) cho hwnd {hwnd}")
    else:
        print(f"Consolog: Không tìm thấy hình {image_path} trong cửa sổ.")
        logging.warning(f"Không tìm thấy {image_path} trong cửa sổ hwnd {hwnd}")

# -----------------------------------------------------------
try:
    from script_builder import ScriptBuilder
except ImportError:
    ScriptBuilder = None
    print("Consolog: Không tìm thấy script_builder.py hoặc lỗi import ScriptBuilder.")
    logging.error("Không tìm thấy script_builder.py hoặc lỗi import ScriptBuilder.")

# -----------------------------------------------------------
# PHẦN AUTOIT (Giao diện Tkinter)
def auto_it_window(root, entry_path, lang, get_tdata_folders):
    print("Consolog: Khởi tạo cửa sổ AutoIT Feature")
    logging.info("Khởi tạo cửa sổ AutoIT Feature")
    auto_win = tk.Toplevel(root)
    auto_win.title("AutoIT Feature")
    # Sửa: Center cửa sổ AutoIT Feature vào giữa màn hình với kích thước 1200x840
    center_window(auto_win, 1200, 840)
    paused = False
    global_stop = False
    window_events = {}
    running_processes = []

    frame_paths = tk.LabelFrame(auto_win, text="Cài đặt Đường dẫn", padx=10, pady=10)
    frame_paths.pack(fill=tk.X, padx=10, pady=5)

    # ---- (Quản lý đường dẫn avatar)
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
    # **CHỈNH SỬA**: Thêm nhãn thống kê cho Avatar (số file ảnh)
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

    # ---- (Quản lý file text tên đổi)
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
    # **CHỈNH SỬA**: Thêm nhãn thống kê cho file tên đổi (số dòng)
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

    # ---- (Quản lý file text số điện thoại)
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
    # **CHỈNH SỬA**: Thêm nhãn thống kê cho file số điện thoại (số dòng)
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

    # ---- (Quản lý file text mô tả tài khoản)
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
    # **CHỈNH SỬA**: Thêm nhãn thống kê cho file mô tả (số dòng)
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

    # **CHỈNH SỬA**: Hàm cập nhật thống kê đường dẫn theo thời gian thực
    def update_path_stats():
        # Avatar (đếm số file ảnh)
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
        
        # File tên đổi (đếm số dòng)
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
        
        # File số điện thoại (đếm số dòng)
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
        
        # File mô tả (đếm số dòng)
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

    # Bắt đầu cập nhật thống kê theo thời gian thực
    auto_win.after(1000, update_path_stats)

    # Frame tùy chọn
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

    # ----- Check Thay đổi thông tin
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
        command=lambda: open_edit_script("script_change_info.py", auto_win)
    )
    btn_edit_change_info.grid(row=0, column=3, sticky="e", padx=5)
    def save_time1(*args):
        with open("completion_time_change_info.txt", "w", encoding="utf-8") as f:
            f.write(var_total_time1.get())
        print("Consolog: Lưu completion_time_change_info:", var_total_time1.get())
        logging.info(f"Lưu completion_time_change_info: {var_total_time1.get()}")
    var_total_time1.trace("w", save_time1)

    # ----- Check Thay đổi privacy
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
        command=lambda: open_edit_script("script_privacy.py", auto_win)
    )
    btn_edit_privacy.grid(row=0, column=3, sticky="e", padx=5)
    def save_time2(*args):
        with open("completion_time_privacy.txt", "w", encoding="utf-8") as f:
            f.write(var_total_time2.get())
        print("Consolog: Lưu completion_time_privacy:", var_total_time2.get())
        logging.info("Lưu completion_time_privacy: %s", var_total_time2.get())
    var_total_time2.trace("w", save_time2)

    # ----- Check Gửi tin nhắn chào
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
        command=lambda: open_edit_script("script_welcome.py", auto_win)
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
    tk.Label(frame_welcome_text, text="Nhập tin nhắn chào mừng:").grid(row=0, column=0, sticky="w")
    var_welcome_text = tk.StringVar()
    if os.path.exists("welcome_message.txt"):
        with open("welcome_message.txt", "r", encoding="utf-8") as f:
            var_welcome_text.set(f.read().strip())
    entry_welcome_text = tk.Entry(frame_welcome_text, textvariable=var_welcome_text, width=40)
    entry_welcome_text.grid(row=0, column=1, padx=5, sticky="w")
    tk.Button(frame_welcome_text, text="Lưu", command=lambda: save_welcome_message()).grid(row=0, column=2, padx=5)
    def save_welcome_message():
        message = var_welcome_text.get()
        print("Consolog: Lưu welcome_message:", message)
        logging.info(f"Lưu welcome_message: {message}")
        try:
            with open("welcome_message.txt", "w", encoding="utf-8") as f:
                f.write(message)
            messagebox.showinfo("Lưu", "Đã lưu tin nhắn chào mừng: " + message)
        except Exception as e:
            messagebox.showerror("Lỗi", "Lỗi lưu tin nhắn: " + str(e))
            logging.error(f"Lỗi lưu welcome_message: {e}")

    if ScriptBuilder:
        btn_script_builder = tk.Button(
            frame_options,
            text="Script Builder",
            width=20,
            command=lambda: ScriptBuilder(auto_win)
        )
        btn_script_builder.pack(pady=10)
    else:
        tk.Label(frame_options, text="[Script Builder không khả dụng]").pack(pady=10)

    # ---- PHẦN THAY ĐỔI CHẾ ĐỘ JSON: nếu chế độ JSON thì thread mặc định là 1
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

    # ---- BÔ XUNG THÊM: Ô nhập số lần chạy
    tk.Label(frame_thread2, text="Số lần chạy:").pack(side=tk.LEFT, padx=(20,0))
    var_loop_count = tk.StringVar(value="1")
    if os.path.exists("loop_count.txt"):
        with open("loop_count.txt", "r") as f:
            lc = f.read().strip()
            if lc:
                var_loop_count.set(lc)
    entry_loop_count = tk.Entry(frame_thread2, textvariable=var_loop_count, width=5)
    entry_loop_count.pack(side=tk.LEFT, padx=5)

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

    # ---- BÔ XUNG THÊM: Lưu số lần chạy vào file config (sử dụng file loop_count.txt)
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

    frame_table = tk.Frame(auto_win)
    frame_table.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
    columns = ("stt", "tdata", "live_status", "so_lan_them_danh_ba", "so_tin_nhan_chu_dc", "trạng_thái")
    tree = ttk.Treeview(frame_table, columns=columns, show="headings")
    for col, text in zip(columns,
                         ["STT", "TData", "Live(Die)", "Số lần thêm vào danh bạ", "Số tin nhắn gửi dc", "Trạng thái"]):
         tree.heading(col, text=text)
         tree.column(col, width=100, anchor="center")
    tree.pack(fill=tk.BOTH, expand=True)

    def populate_auto_it_table():
        print("Consolog: Đang populate bảng hiển thị Tdata")
        logging.info("Populate bảng hiển thị Tdata")
        tdata_dir = entry_path.get()
        folders = get_tdata_folders(tdata_dir)
        for item in tree.get_children():
            tree.delete(item)
        for idx, folder in enumerate(folders, start=1):
            folder_name = os.path.basename(folder)
            status = "Chưa check"
            status_file = os.path.join(folder, "status.txt")
            if os.path.isfile(status_file):
                try:
                    with open(status_file, "r", encoding="utf-8") as f:
                        status = f.read().strip()
                except:
                    status = "Error"
            contact_count = 0
            contact_file = os.path.join(folder, "contact_count.txt")
            if os.path.isfile(contact_file):
                try:
                    contact_count = int(open(contact_file).read().strip())
                except:
                    contact_count = 0
            message_count = 0
            message_file = os.path.join(folder, "message_count.txt")
            if os.path.isfile(message_file):
                try:
                    message_count = int(open(message_file).read().strip())
                except:
                    message_count = 0
            tree.insert("", tk.END, values=(idx, folder_name, status, contact_count, message_count, "Chưa chạy"))
        print("Consolog: Hoàn thành populate bảng hiển thị")
        logging.info("Hoàn thành populate bảng hiển thị Tdata")
    populate_auto_it_table()

    def safe_update_row_status(row, status):
        try:
            if tree.winfo_exists() and row in tree.get_children():
                vals = list(tree.item(row, "values"))
                vals[5] = status
                tree.item(row, values=vals)
                print(f"Consolog: {vals[1]} - {status}")
                logging.info(f"{vals[1]} - {status}")
        except Exception as e:
            print("Consolog: Lỗi cập nhật row:", e)
            logging.error(f"Lỗi cập nhật row: {e}")

    def safe_update_progress(progress):
        try:
            if lbl_progress_auto.winfo_exists():
                progress_var_auto.set(progress)
                lbl_progress_auto.config(text=f"{int(progress)}%")
        except Exception as e:
            print("Consolog: Lỗi cập nhật progress:", e)
            logging.error(f"Lỗi cập nhật progress: {e}")

    frame_progress = tk.Frame(auto_win)
    frame_progress.pack(fill=tk.X, padx=10, pady=5)
    progress_var_auto = tk.DoubleVar(value=0)
    progress_bar_auto = ttk.Progressbar(frame_progress, variable=progress_var_auto, maximum=100)
    progress_bar_auto.pack(fill=tk.X, expand=True)
    lbl_progress_auto = tk.Label(frame_progress, text="0%")
    lbl_progress_auto.pack()
    progress_lock = threading.Lock()
    completed_count = 0

    WINDOW_WIDTH = 500
    WINDOW_HEIGHT = 504
    MARGIN_X = 10
    MARGIN_Y = 10

    # ---------------------------
    # CHỈNH SỬA PHẦN START_ALL: kiểm tra checkbox và chạy script tương ứng theo chế độ python/json
    def start_all_auto():
        nonlocal completed_count, global_stop
        if global_stop:
            print("Consolog: Đã nhận tín hiệu dừng toàn cục, không khởi tạo tiến trình mới")
            logging.info("Đã nhận tín hiệu dừng toàn cục, không khởi tạo tiến trình mới")
            return
        print("Consolog: Bắt đầu chạy start_all_auto")
        logging.info("Bắt đầu chạy start_all_auto")
        
        # Đọc cấu hình chế độ chạy (python/json)
        config_file = "run_mode_config.json"
        default_mode = "python"
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                config = json.load(f)
            default_mode = config.get("run_mode", "python")
            print("Consolog: Chế độ chạy được cấu hình:", default_mode)
            logging.info("Chế độ chạy được cấu hình: %s", default_mode)
        except Exception as e:
            print("Consolog: Lỗi đọc file config:", e)
            logging.error("Lỗi đọc file config: %s", e)
            default_mode = "python"
        
        # Lấy danh sách các checkbox đã được chọn
        selected_options = []
        if var_change_info.get():
            selected_options.append(("script_change_info", var_total_time1.get()))
        if var_privacy.get():
            selected_options.append(("script_privacy", var_total_time2.get()))
        if var_welcome.get():
            selected_options.append(("script_welcome", var_total_time3.get()))
        if not selected_options:
            messagebox.showwarning("Chú ý", "Không có checkbox nào được chọn!")
            return
        
        # CHỈNH SỬA: Khởi tạo dictionary lưu vị trí ban đầu cho từng thread (theo chỉ số trong batch)
        thread_positions = {}
        # Sửa: Khởi tạo biến global_index để duy trì chỉ số liên tục qua các option
        global_index = 0

        # BÔ XUNG THÊM: Lấy số lần chạy từ ô nhập (và ép kiểu)
        try:
            loop_count = int(var_loop_count.get())
        except:
            loop_count = 1
        print(f"Consolog: Số lần chạy được cài đặt: {loop_count}")
        logging.info(f"Số lần chạy được cài đặt: {loop_count}")

        rows = tree.get_children()
        # Tổng số tác vụ = số dòng * số lần chạy
        total = len(rows) * loop_count
        completed_count = 0

        # Với mỗi option đã chọn, chạy script tương ứng theo số lần chạy
        for option in selected_options:
            base_name, total_time_str = option
            try:
                completion_time = int(total_time_str)
            except:
                completion_time = 1
            file_py = base_name + ".py"
            file_txt = base_name + ".txt"  # CHỈNH SỬA: thêm file .txt
            file_json = base_name + ".json"
            # Chọn file script theo cấu hình
            if default_mode == "json" and os.path.exists(file_json):
                script_file_to_run = file_json
            elif os.path.exists(file_txt):
                script_file_to_run = file_txt
            elif os.path.exists(file_py):
                script_file_to_run = file_py
            elif os.path.exists(file_json):
                script_file_to_run = file_json
            else:
                script_file_to_run = None
            print(f"Consolog: Chọn script cho {base_name}: {script_file_to_run} với completion_time={completion_time}")
            logging.info("Chọn script cho %s: %s với completion_time=%d", base_name, script_file_to_run, completion_time)
            # Xác định số thread: nếu chạy JSON thì bắt buộc 1 thread
            if script_file_to_run and script_file_to_run.endswith(".json"):
                messagebox.showinfo("Thông báo", "Bạn đang chạy JSON nên tối đa chỉ được 1 thread cho " + base_name)
                thread_count = 1
            else:
                try:
                    thread_count = int(var_thread2.get())
                except:
                    thread_count = 1
            
            tdata_dir = entry_path.get()
            all_rows = list(rows)
            # Lặp theo số lần chạy
            for cycle in range(loop_count):
                print(f"Consolog: Bắt đầu chu kỳ thứ {cycle+1} cho option {base_name}.")
                logging.info(f"Bắt đầu chu kỳ thứ {cycle+1} cho option {base_name}.")
                # CHỈNH SỬA: sử dụng global_index để tính toán vị trí của mỗi cửa sổ.
                # Mỗi batch, các thread sẽ được đặt ở vị trí ban đầu dựa theo chỉ số của thread trong batch.
                for i in range(0, len(all_rows), thread_count):
                    batch = all_rows[i:i+thread_count]
                    threads = []
                    for j, row in enumerate(batch):
                        overall_index = global_index
                        global_index += 1  # tăng biến toàn cục
                        # CHỈNH SỬA: sử dụng batch_index (j) làm thread_id.
                        thread_id = j
                        # Nếu vị trí cho thread này đã được lưu từ batch đầu tiên thì dùng lại, nếu chưa có thì tính mới.
                        if thread_id in thread_positions:
                            new_x, new_y = thread_positions[thread_id]
                        else:
                            new_x = MARGIN_X + thread_id * (WINDOW_WIDTH + MARGIN_X)
                            new_y = MARGIN_Y
                            thread_positions[thread_id] = (new_x, new_y)
                        t = threading.Thread(
                            target=process_window,
                            args=(row, overall_index, script_file_to_run, completion_time, tdata_dir,
                                  WINDOW_WIDTH, WINDOW_HEIGHT, new_x, new_y, thread_count, total),
                            daemon=True
                        )
                        t.start()
                        print(f"Consolog: Đã khởi động thread {overall_index} cho cửa sổ tại vị trí ({new_x}, {new_y}).")
                        logging.info(f"Đã khởi động thread {overall_index} cho cửa sổ tại vị trí ({new_x}, {new_y}).")
                        # CHỈNH SỬA: Delay 1 giây trước khi khởi động thread tiếp theo trong batch
                        time.sleep(1)
                        threads.append(t)
                    for t in threads:
                        t.join()
            print(f"Consolog: Hoàn thành chạy script cho option {base_name}.")
            logging.info("Hoàn thành chạy script cho option %s.", base_name)
        auto_win.after(0, lambda: btn_start_all.config(state=tk.NORMAL))
        print("Consolog: Quá trình chạy auto đã hoàn thành cho tất cả các checkbox đã chọn.")
        logging.info("Quá trình chạy auto đã hoàn thành cho tất cả các checkbox đã chọn.")

    # CHỈNH SỬA: Hàm process_window – sửa lại vị trí cửa sổ theo tọa độ đã được truyền (new_x, new_y)
    def process_window(row, overall_index, script_file, completion_time, tdata_dir,
                       WINDOW_WIDTH, WINDOW_HEIGHT, new_x, new_y, thread_count, total):
        nonlocal completed_count, global_stop
        if global_stop:
            auto_win.after(0, lambda: safe_update_row_status(row, "Đã kết thúc"))
            with progress_lock:
                completed_count += 1
                progress = (completed_count / total) * 100
                auto_win.after(0, lambda: safe_update_progress(progress))
            return

        values = safe_get_tree_item(tree, row)
        if values is None:
            return
        folder_name = values[1]
        full_path = os.path.join(tdata_dir, folder_name)
        print(f"Consolog: Bắt đầu xử lý {folder_name}")
        logging.info(f"Bắt đầu xử lý {folder_name}")
        telegram_exe = os.path.join(full_path, "Telegram.exe")
        if not os.path.exists(telegram_exe):
            print(f"Consolog: Telegram.exe không tồn tại tại {folder_name}")
            logging.error(f"Telegram.exe không tồn tại tại {folder_name}")
            auto_win.after(0, lambda: safe_update_row_status(row, "Error: Telegram.exe không tồn tại"))
            with progress_lock:
                completed_count += 1
                progress = (completed_count / total) * 100
                auto_win.after(0, lambda: safe_update_progress(progress))
            return

        local_pause = threading.Event()
        local_stop = threading.Event()
        window_events[folder_name] = (local_pause, local_stop)

        try:
            print(f"Consolog: Mở Telegram.exe tại {folder_name}")
            logging.info(f"Mở Telegram.exe tại {folder_name}")
            process = subprocess.Popen([telegram_exe])
            running_processes.append(process)
        except Exception as e:
            print(f"Consolog: Lỗi mở Telegram.exe tại {folder_name}: {e}")
            logging.error(f"Lỗi mở Telegram.exe tại {folder_name}: {e}")
            auto_win.after(0, lambda: safe_update_row_status(row, f"Error: {e}"))
            with progress_lock:
                completed_count += 1
                progress = (completed_count / total) * 100
                auto_win.after(0, lambda: safe_update_progress(progress))
            return

        wait_with_pause(0.5, local_pause, local_stop)
        if local_stop.is_set():
            print(f"Consolog: Nhận tín hiệu dừng trong {folder_name}")
            logging.info(f"Nhận tín hiệu dừng trong {folder_name}")
            process.terminate()
            auto_win.after(0, lambda: safe_update_row_status(row, "Đã kết thúc"))
            with progress_lock:
                completed_count += 1
                progress = (completed_count / total) * 100
                auto_win.after(0, lambda: safe_update_progress(progress))
            return

        hwnd = None
        if win32gui is not None:
            hwnd = wait_for_hwnd(process.pid, max_attempts=60, wait_interval=0.5, exclude_hwnd=MAIN_HWND)
            if hwnd and win32gui.IsWindow(hwnd) and win32gui.IsWindowVisible(hwnd):
                try:
                    win32gui.SetForegroundWindow(hwnd)
                    print(f"Consolog: Đã đưa cửa sổ {folder_name} lên foreground")
                    logging.info(f"Đã đưa cửa sổ {folder_name} lên foreground")
                except Exception as e:
                    print(f"Consolog: Lỗi SetForegroundWindow cho {folder_name}: {e}")
                    logging.error(f"Lỗi SetForegroundWindow cho {folder_name}: {e}")
                time.sleep(0.5)
                print(f"Consolog: [CHỈNH SỬA] Di chuyển cửa sổ {folder_name} tới vị trí ({new_x}, {new_y})")
                logging.info(f"Di chuyển cửa sổ {folder_name} tới ({new_x}, {new_y})")
                check_and_move_window(hwnd, folder_name, int(new_x), int(new_y), WINDOW_WIDTH, WINDOW_HEIGHT)
                virtual_input = create_virtual_input(hwnd)
            else:
                print(f"Consolog: Không tìm thấy handle cửa sổ hợp lệ cho {folder_name}")
                logging.error(f"Không tìm thấy handle cửa sổ hợp lệ cho {folder_name}")
                virtual_input = None
        else:
            virtual_input = None

        auto_win.after(0, lambda: safe_update_row_status(row, "Đang chạy"))
        # Trước khi thực hiện thao tác, kiểm tra pause
        check_pause(local_pause)
        wait_with_pause(3, local_pause, local_stop)
        # Sau delay, kiểm tra lại pause
        check_pause(local_pause)
        if script_file is not None:
            try:
                print(f"Consolog: Chạy script {script_file} cho {folder_name} với handle {str(hwnd)}")
                logging.info(f"Chạy script {script_file} cho {folder_name} với hwnd {hwnd}")
                start_script = time.time()
                check_pause(local_pause)  # Kiểm tra trước khi chạy script
                if script_file.endswith(".py") or script_file.endswith(".txt"):
                    # CHỈNH SỬA: Thêm log Consolog trước khi gọi và gọi run_script_dynamic thay vì subprocess.run
                    print(f"Consolog: Đang thực thi script {script_file} cho HWND {hwnd}")
                    run_script_dynamic(script_file, [full_path, str(hwnd)])
                elif script_file.endswith(".json"):
                    with open(script_file, "r", encoding="utf-8") as f:
                        json_data = json.load(f)
                    if isinstance(json_data, list):
                        json_data = {"events": json_data}
                    if hwnd is not None:
                        json_data["window_handle"] = hwnd
                    json_thread = threading.Thread(target=run_json_script, args=(json_data, local_pause), daemon=True)
                    json_thread.start()
                    json_thread.join()
                    logging.info(f"JSON script đã chạy cho {folder_name}")
                else:
                    logging.warning(f"Script không xác định định dạng cho {folder_name}")
            except Exception as e:
                print(f"Consolog: Lỗi script cho {folder_name}: {e}")
                logging.error(f"Lỗi script cho {folder_name}: {e}")
                auto_win.after(0, lambda: safe_update_row_status(row, f"Script Error: {e}"))
                start_script = time.time()
            elapsed = time.time() - start_script
            remaining = completion_time - elapsed
            if remaining > 0:
                print(f"Consolog: Đang chờ thêm {remaining:.2f} giây cho {folder_name} để đủ mốc thời gian.")
                logging.info(f"Chờ thêm {remaining:.2f} giây cho {folder_name}")
                wait_with_pause(remaining, local_pause, local_stop)
            if local_stop.is_set():
                print(f"Consolog: Nhận tín hiệu dừng sau khi chạy script cho {folder_name}")
                logging.info(f"Nhận tín hiệu dừng sau khi chạy script cho {folder_name}")
                process.terminate()
                auto_win.after(0, lambda: safe_update_row_status(row, "Đã kết thúc"))
                with progress_lock:
                    completed_count += 1
                    progress = (completed_count / total) * 100
                    auto_win.after(0, lambda: safe_update_progress(progress))
                return
        else:
            print(f"Consolog: Không chọn script nào, chờ {completion_time} giây cho {folder_name}")
            logging.info(f"Không chọn script, chờ {completion_time} giây cho {folder_name}")
            wait_with_pause(completion_time, local_pause, local_stop)
            if local_stop.is_set():
                print(f"Consolog: Nhận tín hiệu dừng trong thời gian chờ cho {folder_name}")
                logging.info(f"Nhận tín hiệu dừng trong thời gian chờ cho {folder_name}")
                process.terminate()
                auto_win.after(0, lambda: safe_update_row_status(row, "Đã kết thúc"))
                with progress_lock:
                    completed_count += 1
                    progress = (completed_count / total) * 100
                    auto_win.after(0, lambda: safe_update_progress(progress))
                return

        if hwnd is not None and win32gui.IsWindow(hwnd):
            try:
                win32gui.PostMessage(hwnd, win32con.WM_CLOSE, 0, 0)
                logging.info(f"Đã gửi lệnh đóng cửa sổ cho {folder_name}")
            except Exception as e:
                logging.error(f"Lỗi khi gửi lệnh đóng cửa sổ cho {folder_name}: {e}")
        time.sleep(1)
        try:
            process.terminate()
            process.wait(timeout=10)
            print(f"Consolog: Đóng Telegram.exe tại {folder_name}")
            logging.info(f"Đóng Telegram.exe tại {folder_name}")
        except Exception as e:
            print(f"Consolog: Lỗi khi đóng Telegram.exe tại {folder_name}: {e}")
            logging.error(f"Lỗi khi đóng Telegram.exe tại {folder_name}: {e}")
        print(f"Consolog: Xong xử lý {folder_name}")
        logging.info(f"Xong xử lý {folder_name}")
        auto_win.after(0, lambda: safe_update_row_status(row, "Hoàn thành"))
        with progress_lock:
            completed_count += 1
            progress = (completed_count / total) * 100
            auto_win.after(0, lambda: safe_update_progress(progress))

    # =========================
    # PHẦN CHÍNH: THỰC HIỆN TẠM DỪNG/TIẾP TỤC TOÀN BỘ
    # =========================
    # Hàm toggle_pause_all để tạm dừng hoặc tiếp tục toàn bộ các thread đang chạy.
    def toggle_pause_all():
        nonlocal paused
        if not paused:
            # Khi bấm pause, set (đặt trạng thái pause) cho tất cả các event của từng cửa sổ
            for key, (p_event, _) in window_events.items():
                p_event.set()
                print(f"Consolog: Đặt trạng thái tạm dừng cho cửa sổ: {key}")
                logging.info(f"Đặt trạng thái tạm dừng cho cửa sổ: {key}")
            paused = True
            btn_pause_all.config(text="Tiếp tục tất cả")
            print("Consolog: Đã tạm dừng tất cả các thread")
            logging.info("Tạm dừng tất cả các thread")
        else:
            # Khi bấm continue, clear (bỏ trạng thái pause) của tất cả các event để tiếp tục chạy
            for key, (p_event, _) in window_events.items():
                p_event.clear()
                print(f"Consolog: Hủy trạng thái tạm dừng cho cửa sổ: {key}")
                logging.info(f"Hủy trạng thái tạm dừng cho cửa sổ: {key}")
            paused = False
            btn_pause_all.config(text="Tạm dừng tất cả")
            print("Consolog: Đã tiếp tục tất cả các thread")
            logging.info("Tiếp tục tất cả các thread")

    def end_all_auto():
        nonlocal global_stop
        print("Consolog: Kết thúc tất cả các quá trình")
        logging.info("Kết thúc tất cả các quá trình")
        global_stop = True
        for key, (_, s_event) in window_events.items():
            s_event.set()
        for proc in running_processes:
            try:
                proc.terminate()
                print("Consolog: Đã kết thúc tiến trình", proc.pid)
                logging.info(f"Đã kết thúc tiến trình {proc.pid}")
            except Exception as e:
                print("Consolog: Lỗi khi kết thúc tiến trình:", e)
                logging.error(f"Lỗi khi kết thúc tiến trình: {e}")
        print("Consolog: Đã kết thúc tất cả các quá trình.")
        logging.info("Đã kết thúc tất cả các quá trình.")

    frame_controls = tk.Frame(auto_win)
    frame_controls.pack(padx=10, pady=5)
    btn_start_all = tk.Button(frame_controls, text="Bắt đầu tất cả", width=15, command=lambda: threading.Thread(target=start_all_auto, daemon=True).start())
    btn_pause_all = tk.Button(frame_controls, text="Tạm dừng tất cả", width=15, command=toggle_pause_all)
    btn_end = tk.Button(frame_controls, text="Kết thúc quá trình", width=15, command=end_all_auto)

    btn_start_all.pack(side=tk.LEFT, padx=5, pady=5)
    btn_pause_all.pack(side=tk.LEFT, padx=5, pady=5)
    btn_end.pack(side=tk.LEFT, padx=5, pady=5)

    frame_additional = tk.Frame(auto_win)
    frame_additional.pack(fill=tk.X, padx=10, pady=5)
    btn_open_tdata = tk.Button(frame_additional, text="Mở Tdata chưa hoàn thành", width=20,
                               command=lambda: messagebox.showinfo("Mở Tdata", "Chức năng mở Tdata chưa hoàn thành"))
    btn_change_info = tk.Button(frame_additional, text="Thay đổi thông tin tài khoản", width=20,
                                command=lambda: messagebox.showinfo("Thay đổi thông tin", "Chức năng thay đổi thông tin tài khoản chưa hoàn thành"))
    btn_change_privacy = tk.Button(frame_additional, text="Thay đổi quyền riêng tư", width=20,
                                   command=lambda: messagebox.showinfo("Thay đổi quyền", "Chức năng thay đổi quyền riêng tư chưa hoàn thành"))

    btn_open_tdata.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
    btn_change_info.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")
    btn_change_privacy.grid(row=0, column=2, padx=5, pady=5, sticky="nsew")
    frame_additional.grid_columnconfigure(0, weight=1)
    frame_additional.grid_columnconfigure(1, weight=1)
    frame_additional.grid_columnconfigure(2, weight=1)

    frame_bottom_spacer = tk.Frame(auto_win)
    frame_bottom_spacer.pack(fill=tk.X, pady=20)

def auto_it_function(root, entry_path, lang, get_tdata_folders):
    print("Consolog: auto_it_function được gọi.")
    logging.info("auto_it_function được gọi.")
    auto_it_window(root, entry_path, lang, get_tdata_folders)

# ---------------------------
# Chạy chương trình chính (demo)
if __name__ == "__main__":
    print("Consolog: Khởi chạy chương trình AutoIT không dùng pywinauto")
    logging.info("Khởi chạy chương trình AutoIT không dùng pywinauto")
    root = tk.Tk()
    root.title("Chương trình AutoIT không dùng pywinauto")
    # Sửa: Center cửa sổ chính vào giữa màn hình với kích thước 600x150
    center_window(root, 600, 150)
    tk.Label(root, text="Đường dẫn chứa Tdata:").pack(pady=5)
    entry_path = tk.Entry(root, width=50)
    entry_path.pack(pady=5)
    MAIN_HWND = root.winfo_id()
    def open_auto_it():
        print("Consolog: Mở AutoIT Feature từ cửa sổ chính")
        logging.info("Mở AutoIT Feature từ cửa sổ chính")
        auto_it_function(root, entry_path, None, get_tdata_folders)
    tk.Button(root, text="Mở AutoIT Feature", command=open_auto_it).pack(pady=10)
    
    # PHẦN MỚI: Ví dụ chạy đa luồng cho script "your_script.py"
    # Bạn có thể gọi hàm run_script_multithread() tại đây để kiểm tra
    # run_script_multithread()
    
    root.mainloop()
