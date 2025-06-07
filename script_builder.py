import os
import time
import json
import threading
import subprocess
import tkinter as tk
from tkinter import messagebox, filedialog, ttk
import logging
import queue
import ctypes
from pynput import mouse as pmouse
from pynput import keyboard as pkeyboard

# ----------------- Xử lý DPI ---------------------
def set_process_dpi_awareness():
    """
    Thiết lập DPI Awareness để lấy DPI chính xác trên Windows.
    """
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)  # PROCESS_PER_MONITOR_DPI_AWARE
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass

def get_screen_dpi():
    """
    Lấy DPI hiện tại của màn hình chính.
    """
    set_process_dpi_awareness()
    hdc = ctypes.windll.user32.GetDC(0)
    dpi = ctypes.windll.gdi32.GetDeviceCaps(hdc, 88)  # 88: LOGPIXELSX
    ctypes.windll.user32.ReleaseDC(0, hdc)
    return dpi

def scale_coordinate(coord, recorded_dpi, current_dpi):
    """
    Tính lại tọa độ dựa trên DPI lúc ghi và DPI hiện tại.
    """
    scale = current_dpi / recorded_dpi
    x, y = coord
    return int(round(x * scale)), int(round(y * scale))

# ----------------- Cấu hình logging ---------------------
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s [%(levelname)s] %(message)s")

# Thư viện PIL dùng để xử lý ảnh
from PIL import Image, ImageTk

# File cấu hình để lưu giá trị Telegram path
CONFIG_FILE = "config.json"

# Biến toàn cục để tham chiếu đến đối tượng ScriptBuilder (giúp cập nhật UI hiển thị event)
SCRIPT_BUILDER_APP = None

try:
    PYNPUT_AVAILABLE = True
except ImportError:
    PYNPUT_AVAILABLE = False

recorded_events = []
recording = False
mouse_listener = None
keyboard_listener = None
recording_start_time = None

GLOBAL_TELEGRAM_HWND = None
GLOBAL_OFFSET_X = 0
GLOBAL_OFFSET_Y = 0

# Biến mới cho chế độ ghi & phát lại
# Nếu RECORD_IN_WINDOW = False, tức là tắt chế độ HWND, ta sẽ ghi và phát theo tọa độ tuyệt đối của màn hình.
RECORD_IN_WINDOW = True   # True: ghi theo relative (trong cửa sổ), False: ghi toàn màn hình
REPLAY_COUNT = 1          # Số lần phát lại
PLAYBACK_SPEED = 1.0      # Hệ số tốc độ phát lại

# --- Các biến cải tiến ---
LAST_MOUSE_POSITION = (0, 0)
MOUSE_MOVE_THRESHOLD = 5   # chỉ ghi sự kiện nếu di chuyển >5 pixel
UI_UPDATE_INTERVAL = 0.5   # chỉ cập nhật UI sau mỗi 0.5 giây
_last_ui_update_time = 0

# Thêm biến để lưu DPI lúc ghi nếu ghi toàn màn hình
RECORDED_DPI = None

# Queue để truyền sự kiện từ thread phụ sang UI thread
event_queue = queue.Queue()

def convert_to_relative(abs_x, abs_y):
    """
    Nếu RECORD_IN_WINDOW được bật và có GLOBAL_TELEGRAM_HWND, trả về tọa độ relative.
    Nếu không (full màn hình) thì trả về chính tọa độ tuyệt đối.
    """
    if RECORD_IN_WINDOW and GLOBAL_TELEGRAM_HWND:
        rel = (abs_x - GLOBAL_OFFSET_X, abs_y - GLOBAL_OFFSET_Y)
        logging.debug("convert_to_relative: abs=(%s,%s) -> rel=%s", abs_x, abs_y, rel)
        return rel
    else:
        logging.debug("convert_to_relative: sử dụng tọa độ tuyệt đối (%s,%s)", abs_x, abs_y)
        return (abs_x, abs_y)

def convert_to_absolute(rel_x, rel_y):
    """
    Nếu RECORD_IN_WINDOW được bật, cộng offset của cửa sổ; nếu không, trả về chính giá trị đã ghi.
    """
    if RECORD_IN_WINDOW and GLOBAL_TELEGRAM_HWND:
        abs_val = (GLOBAL_OFFSET_X + rel_x, GLOBAL_OFFSET_Y + rel_y)
        logging.debug("convert_to_absolute: rel=(%s,%s) -> abs=%s", rel_x, rel_y, abs_val)
        return abs_val
    else:
        logging.debug("convert_to_absolute: sử dụng tọa độ tuyệt đối (%s,%s)", rel_x, rel_y)
        return (rel_x, rel_y)

# Hàm kiểm tra xem tọa độ tuyệt đối có nằm trong cửa sổ Telegram hay không
def is_within_window(abs_x, abs_y):
    if RECORD_IN_WINDOW and GLOBAL_TELEGRAM_HWND:
        try:
            import win32gui
            left, top, right, bottom = win32gui.GetWindowRect(GLOBAL_TELEGRAM_HWND)
            within = left <= abs_x <= right and top <= abs_y <= bottom
            logging.debug("is_within_window: (%s,%s) trong (%s,%s,%s,%s): %s", abs_x, abs_y, left, top, right, bottom, within)
            return within
        except Exception as e:
            logging.error("Error checking window boundary: %s", e)
            return True
    else:
        return True

def _update_ui(event):
    """
    Đẩy event vào queue để cập nhật UI trong main thread.
    """
    global _last_ui_update_time
    now = time.perf_counter()
    if now - _last_ui_update_time >= UI_UPDATE_INTERVAL:
        _last_ui_update_time = now
        event_queue.put(event)

def process_event_queue():
    """
    Lấy các event từ queue và cập nhật UI (chạy trên main thread).
    """
    if SCRIPT_BUILDER_APP is not None:
        while not event_queue.empty():
            event = event_queue.get()
            SCRIPT_BUILDER_APP.append_record_event(event)
        SCRIPT_BUILDER_APP.record_display_text.after(100, process_event_queue)

# ----------------------------
# Các hàm ghi sự kiện chuột và bàn phím

def on_mouse_move(x, y):
    global LAST_MOUSE_POSITION
    if not recording:
        return
    # Nếu ghi theo cửa sổ và con trỏ ra ngoài, bỏ qua
    if RECORD_IN_WINDOW and GLOBAL_TELEGRAM_HWND:
        if not is_within_window(x, y):
            logging.info("Bỏ qua sự kiện vì con trỏ ra ngoài cửa sổ (move)")
            return
    # Throttling: chỉ ghi nếu di chuyển đủ xa
    if abs(x - LAST_MOUSE_POSITION[0]) < MOUSE_MOVE_THRESHOLD and abs(y - LAST_MOUSE_POSITION[1]) < MOUSE_MOVE_THRESHOLD:
        return
    LAST_MOUSE_POSITION = (x, y)
    pos = convert_to_relative(x, y)
    event = {
        "type": "move",
        "position": pos,
        "time": time.perf_counter() - recording_start_time
    }
    # Nếu full màn hình, lưu luôn DPI lúc ghi
    if not RECORD_IN_WINDOW:
        event["dpi"] = RECORDED_DPI
    logging.debug("Ghi sự kiện move: %s", event)
    recorded_events.append(event)
    _update_ui(event)

def on_mouse_click(x, y, button, pressed):
    if not recording:
        return
    if RECORD_IN_WINDOW and GLOBAL_TELEGRAM_HWND:
        if not is_within_window(x, y):
            logging.info("Bỏ qua sự kiện vì con trỏ ra ngoài cửa sổ (click)")
            return
    pos = convert_to_relative(x, y)
    event = {
        "type": "click",
        "position": pos,
        "button": str(button),  # Lưu dưới dạng chuỗi, ví dụ "Button.left"
        "pressed": pressed,
        "time": time.perf_counter() - recording_start_time
    }
    if not RECORD_IN_WINDOW:
        event["dpi"] = RECORDED_DPI
    logging.debug("Ghi sự kiện click: %s", event)
    recorded_events.append(event)
    _update_ui(event)

def on_mouse_scroll(x, y, dx, dy):
    if not recording:
        return
    if RECORD_IN_WINDOW and GLOBAL_TELEGRAM_HWND:
        if not is_within_window(x, y):
            logging.info("Bỏ qua sự kiện vì con trỏ ra ngoài cửa sổ (scroll)")
            return
    pos = convert_to_relative(x, y)
    event = {
        "type": "scroll",
        "position": pos,
        "dx": dx,
        "dy": dy,
        "time": time.perf_counter() - recording_start_time
    }
    if not RECORD_IN_WINDOW:
        event["dpi"] = RECORDED_DPI
    logging.debug("Ghi sự kiện scroll: %s", event)
    recorded_events.append(event)
    _update_ui(event)

def on_key_press(key):
    if not recording:
        return
    try:
        k = key.char
    except:
        k = str(key)
    event = {
        "type": "key_press",
        "key": k,
        "time": time.perf_counter() - recording_start_time
    }
    logging.debug("Ghi sự kiện key_press: %s", event)
    recorded_events.append(event)
    _update_ui(event)

def on_key_release(key):
    if not recording:
        return
    try:
        k = key.char
    except:
        k = str(key)
    event = {
        "type": "key_release",
        "key": k,
        "time": time.perf_counter() - recording_start_time
    }
    logging.debug("Ghi sự kiện key_release: %s", event)
    recorded_events.append(event)
    _update_ui(event)

def start_recording():
    global recording, recording_start_time, mouse_listener, keyboard_listener, recorded_events, _last_ui_update_time, GLOBAL_TELEGRAM_HWND, RECORDED_DPI
    logging.info("Bắt đầu ghi thao tác")
    if not PYNPUT_AVAILABLE:
        messagebox.showerror("Lỗi", "Chưa cài đặt module pynput. Vui lòng chạy: pip install pynput")
        return
    if recording:
        messagebox.showwarning("Recording", "Đang ghi, không thể bắt đầu lại!")
        return
    recorded_events = []
    if SCRIPT_BUILDER_APP is not None:
        SCRIPT_BUILDER_APP.clear_record_display()
    recording = True
    recording_start_time = time.perf_counter()
    _last_ui_update_time = recording_start_time

    # Nếu tắt chế độ HWND (full màn hình), lưu DPI lúc ghi
    if not RECORD_IN_WINDOW:
        GLOBAL_TELEGRAM_HWND = None
        RECORDED_DPI = get_screen_dpi()
        logging.debug("Full màn hình: RECORDED_DPI = %s", RECORDED_DPI)
    else:
        logging.debug("Ghi theo cửa sổ, không dùng DPI chuyển đổi.")

    try:
        mouse_listener = pmouse.Listener(on_move=on_mouse_move, on_click=on_mouse_click, on_scroll=on_mouse_scroll)
        keyboard_listener = pkeyboard.Listener(on_press=on_key_press, on_release=on_key_release)
        mouse_listener.start()
        keyboard_listener.start()
        logging.info("Mouse và Keyboard listeners khởi động thành công.")
        if SCRIPT_BUILDER_APP is not None:
            SCRIPT_BUILDER_APP.record_display_text.after(100, process_event_queue)
    except Exception as e:
        logging.error("Lỗi khi khởi động listeners: %s", e)
        messagebox.showerror("Recording Error", f"Lỗi khi khởi động ghi thao tác: {e}")

def stop_recording():
    global recording, mouse_listener, keyboard_listener
    logging.info("Dừng ghi thao tác")
    if not recording:
        messagebox.showwarning("Recording", "Chưa bắt đầu ghi!")
        return
    recording = False
    try:
        if mouse_listener:
            mouse_listener.stop()
        if keyboard_listener:
            keyboard_listener.stop()
        logging.info("Dừng ghi thao tác thành công.")
    except Exception as e:
        logging.error("Lỗi khi dừng ghi thao tác: %s", e)
        messagebox.showerror("Recording Stop Error", f"Lỗi khi dừng ghi thao tác: {e}")

# Mapping cho các nút chuột thay vì sử dụng eval
button_mapping = {
    "Button.left": pmouse.Button.left,
    "Button.right": pmouse.Button.right,
    "Button.middle": pmouse.Button.middle
}

def play_recording():
    if not PYNPUT_AVAILABLE:
        messagebox.showerror("Lỗi", "Chưa cài đặt module pynput. Vui lòng chạy: pip install pynput")
        return
    if not recorded_events:
        messagebox.showinfo("Play", "Chưa có thao tác ghi nào.")
        return

    # Cập nhật offset nếu ghi trong cửa sổ
    if RECORD_IN_WINDOW and GLOBAL_TELEGRAM_HWND:
        try:
            import win32gui
            rect = win32gui.GetWindowRect(GLOBAL_TELEGRAM_HWND)
            global GLOBAL_OFFSET_X, GLOBAL_OFFSET_Y
            GLOBAL_OFFSET_X = rect[0]
            GLOBAL_OFFSET_Y = rect[1]
            logging.info("Cập nhật offset mới: (%s, %s)", GLOBAL_OFFSET_X, GLOBAL_OFFSET_Y)
        except Exception as e:
            messagebox.showwarning("Warning", f"Lỗi cập nhật vị trí cửa sổ: {e}")

    # Lấy giá trị số lần replay và tốc độ phát lại từ giao diện (nếu có)
    global REPLAY_COUNT, PLAYBACK_SPEED
    if SCRIPT_BUILDER_APP:
        try:
            REPLAY_COUNT = int(SCRIPT_BUILDER_APP.var_replay_count.get())
            PLAYBACK_SPEED = float(SCRIPT_BUILDER_APP.var_playback_speed.get())
        except:
            REPLAY_COUNT = 1
            PLAYBACK_SPEED = 1.0

    mouse_controller = pmouse.Controller()
    keyboard_controller = pkeyboard.Controller()

    for replay_index in range(REPLAY_COUNT):
        base_time = recorded_events[0]["time"]
        for i, event in enumerate(recorded_events):
            delay = event["time"] - base_time if i > 0 else 0
            time.sleep(delay / PLAYBACK_SPEED)
            base_time = event["time"]

            # Xử lý các event có tọa độ
            if event["type"] in ("move", "click", "scroll"):
                if RECORD_IN_WINDOW and GLOBAL_TELEGRAM_HWND:
                    abs_x, abs_y = convert_to_absolute(*event["position"])
                else:
                    current_dpi = get_screen_dpi()
                    recorded_dpi = event.get("dpi", current_dpi)
                    abs_x, abs_y = scale_coordinate(event["position"], recorded_dpi, current_dpi)
                logging.debug("Phát lại event %s: recorded pos=%s, calculated abs pos=(%s, %s)", 
                              event["type"], event["position"], abs_x, abs_y)
                if RECORD_IN_WINDOW and GLOBAL_TELEGRAM_HWND and not is_within_window(abs_x, abs_y):
                    logging.info("Bỏ qua event %s vì tọa độ ngoài cửa sổ", event["type"])
                    continue

            if event["type"] == "move":
                mouse_controller.position = (abs_x, abs_y)
            elif event["type"] == "click":
                mouse_controller.position = (abs_x, abs_y)
                btn = button_mapping.get(event["button"], pmouse.Button.left)
                if event["pressed"]:
                    mouse_controller.press(btn)
                else:
                    mouse_controller.release(btn)
            elif event["type"] == "scroll":
                mouse_controller.position = (abs_x, abs_y)
                mouse_controller.scroll(event["dx"], event["dy"])
            elif event["type"] == "key_press":
                try:
                    keyboard_controller.press(event["key"])
                except Exception as e:
                    logging.error("Lỗi key_press: %s", e)
            elif event["type"] == "key_release":
                try:
                    keyboard_controller.release(event["key"])
                except Exception as e:
                    logging.error("Lỗi key_release: %s", e)
    messagebox.showinfo("Play", "Đã hoàn thành việc mô phỏng thao tác.")

def play_recording_in_thread():
    threading.Thread(target=play_recording, daemon=True).start()

LAST_RECORDING_FILE = None

# ------------------- CHỈNH SỬA HÀM SAVE_RECORDING -------------------
def save_recording():
    global LAST_RECORDING_FILE
    if not recorded_events:
        messagebox.showinfo("Save", "Không có dữ liệu ghi để lưu.")
        return
    base_dir = os.getcwd()
    save_dir = os.path.join(base_dir, "Scripts", "json")
    os.makedirs(save_dir, exist_ok=True)
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    file_path = os.path.join(save_dir, f"recording_{timestamp}.json")
    
    # Xác định coord_mode dựa vào chế độ ghi
    coord_mode = "client" if RECORD_IN_WINDOW else "screen"
    
    # Đóng gói dữ liệu lưu gồm coord_mode, recorded_dpi (nếu có) và các sự kiện đã ghi
    data_to_save = {
        "coord_mode": coord_mode,
        "recorded_dpi": RECORDED_DPI if not RECORD_IN_WINDOW else None,
        "events": recorded_events
    }
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data_to_save, f, indent=4)
        messagebox.showinfo("Save", f"Đã lưu dữ liệu ghi tại {file_path}")
        LAST_RECORDING_FILE = file_path
    except Exception as e:
        messagebox.showerror("Lỗi", f"Lỗi khi lưu file: {e}")
# ---------------------------------------------------------------------

def clear_recording():
    global recorded_events
    recorded_events = []
    if SCRIPT_BUILDER_APP is not None:
        SCRIPT_BUILDER_APP.clear_record_display()
    messagebox.showinfo("Clear", "Đã xóa dữ liệu ghi.")

def open_recorded_file():
    global LAST_RECORDING_FILE
    if LAST_RECORDING_FILE and os.path.exists(LAST_RECORDING_FILE):
        os.startfile(LAST_RECORDING_FILE)
    else:
        messagebox.showwarning("File", "Chưa có file record nào hoặc file đã bị xóa.")

# ------------------- CHỨC NĂNG CHẠY JSON -------------------
def run_json_events(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        # Kiểm tra xem file JSON có chứa thông tin về chế độ toạ độ không
        if isinstance(data, dict) and "coord_mode" in data:
            coord_mode = data.get("coord_mode", "client")
            global RECORD_IN_WINDOW, RECORDED_DPI
            # Nếu coord_mode là "client" tức ghi trong cửa sổ
            RECORD_IN_WINDOW = True if coord_mode == "client" else False
            RECORDED_DPI = data.get("recorded_dpi", None)
            events = data.get("events", [])
        else:
            # Trường hợp file JSON cũ chỉ có danh sách sự kiện
            events = data
    except Exception as e:
        messagebox.showerror("Lỗi", f"Lỗi khi đọc file JSON: {e}")
        return

    # Nếu ghi trong cửa sổ, cập nhật offset của cửa sổ
    if RECORD_IN_WINDOW and GLOBAL_TELEGRAM_HWND:
        try:
            import win32gui
            rect = win32gui.GetWindowRect(GLOBAL_TELEGRAM_HWND)
            global GLOBAL_OFFSET_X, GLOBAL_OFFSET_Y
            GLOBAL_OFFSET_X = rect[0]
            GLOBAL_OFFSET_Y = rect[1]
        except Exception as e:
            messagebox.showwarning("Warning", f"Lỗi cập nhật vị trí cửa sổ: {e}")

    global REPLAY_COUNT, PLAYBACK_SPEED
    if SCRIPT_BUILDER_APP:
        try:
            REPLAY_COUNT = int(SCRIPT_BUILDER_APP.var_replay_count.get())
            PLAYBACK_SPEED = float(SCRIPT_BUILDER_APP.var_playback_speed.get())
        except:
            REPLAY_COUNT = 1
            PLAYBACK_SPEED = 1.0

    from pynput.mouse import Controller as MouseController, Button as MouseButton
    from pynput.keyboard import Controller as KeyboardController
    mouse_controller = MouseController()
    keyboard_controller = KeyboardController()

    for replay_index in range(REPLAY_COUNT):
        base_time = events[0]["time"]
        for i, event in enumerate(events):
            delay = event["time"] - base_time if i > 0 else 0
            time.sleep(delay / PLAYBACK_SPEED)
            base_time = event["time"]
            if event["type"] in ("move", "click", "scroll"):
                if RECORD_IN_WINDOW and GLOBAL_TELEGRAM_HWND:
                    abs_x, abs_y = convert_to_absolute(*event["position"])
                else:
                    current_dpi = get_screen_dpi()
                    recorded_dpi = event.get("dpi", current_dpi)
                    abs_x, abs_y = scale_coordinate(event["position"], recorded_dpi, current_dpi)
                if RECORD_IN_WINDOW and GLOBAL_TELEGRAM_HWND and not is_within_window(abs_x, abs_y):
                    continue
            if event["type"] == "move":
                mouse_controller.position = (abs_x, abs_y)
            elif event["type"] == "click":
                mouse_controller.position = (abs_x, abs_y)
                btn = button_mapping.get(event["button"], MouseButton.left)
                if event["pressed"]:
                    mouse_controller.press(btn)
                else:
                    mouse_controller.release(btn)
            elif event["type"] == "scroll":
                mouse_controller.position = (abs_x, abs_y)
                mouse_controller.scroll(event["dx"], event["dy"])
            elif event["type"] == "key_press":
                try:
                    keyboard_controller.press(event["key"])
                except Exception as e:
                    logging.error("Lỗi key_press: %s", e)
            elif event["type"] == "key_release":
                try:
                    keyboard_controller.release(event["key"])
                except Exception as e:
                    logging.error("Lỗi key_release: %s", e)
    messagebox.showinfo("Chạy JSON", "Đã hoàn thành phát lại các sự kiện từ JSON.")

def run_json_in_thread(file_path):
    threading.Thread(target=run_json_events, args=(file_path,), daemon=True).start()

# ------------------- Phần còn lại của mã (các hàm capture, VisualBuilder, ScriptBuilder, ...) -------------------
# Đoạn mã dưới đây không thay đổi so với phiên bản ban đầu, trừ các chỗ gọi save_recording và run_json_events đã được cập nhật.

# --- BEGIN: THÊM CHỨC NĂNG DRAG & DROP CROP ---
def drag_crop_window(screenshot_img, entry_widget):
    logging.info("consolog: Khởi tạo cửa sổ kéo thả để cắt ảnh.")
    crop_win = tk.Toplevel()
    crop_win.title("Drag and Drop Cropper")
    crop_win.grab_set()  # Chiếm quyền nhận sự kiện chuột
    tk_img = ImageTk.PhotoImage(screenshot_img)
    canvas = tk.Canvas(crop_win, width=tk_img.width(), height=tk_img.height(), cursor="cross")
    canvas.pack()
    # Giữ tham chiếu hình ảnh cho canvas và cửa sổ để tránh bị thu gom rác
    canvas.image = tk_img
    crop_win.tk_img = tk_img
    # Hiển thị ảnh lên canvas
    canvas.create_image(0, 0, anchor="nw", image=tk_img)
    # Đưa focus về canvas
    canvas.focus_set()

    rect = None
    start_x = None
    start_y = None

    def on_button_press(event):
        nonlocal start_x, start_y, rect
        start_x, start_y = event.x, event.y
        rect = canvas.create_rectangle(start_x, start_y, start_x, start_y, outline="red")
        logging.debug(f"consolog: Bắt đầu kéo từ ({start_x}, {start_y})")

    def on_move(event):
        nonlocal rect
        canvas.coords(rect, start_x, start_y, event.x, event.y)
        logging.debug(f"consolog: Di chuyển đến ({event.x}, {event.y})")

    def on_button_release(event):
        nonlocal start_x, start_y, rect
        end_x, end_y = event.x, event.y
        x1, y1 = min(start_x, end_x), min(start_y, end_y)
        x2, y2 = max(start_x, end_x), max(start_y, end_y)
        logging.info(f"consolog: Kết thúc kéo, tọa độ cắt: ({x1}, {y1}, {x2}, {y2})")
        cropped = screenshot_img.crop((x1, y1, x2, y2))
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        folder_base = os.path.join(os.getcwd(), "cropped_images")
        os.makedirs(folder_base, exist_ok=True)
        file_path = os.path.join(folder_base, f"cropped_{timestamp}.png")
        try:
            cropped.save(file_path)
            logging.info(f"consolog: Đã lưu ảnh cắt tại {file_path}")
            messagebox.showinfo("Crop", f"Đã cắt và lưu ảnh tại {file_path}")
            entry_widget.delete(0, tk.END)
            entry_widget.insert(0, file_path)
        except Exception as e:
            logging.error(f"consolog: Lỗi lưu ảnh cắt: {e}")
            messagebox.showerror("Crop Error", f"Lỗi lưu ảnh: {e}")
        crop_win.destroy()

    canvas.bind("<ButtonPress-1>", on_button_press)
    canvas.bind("<B1-Motion>", on_move)
    canvas.bind("<ButtonRelease-1>", on_button_release)
# --- END: THÊM CHỨC NĂNG DRAG & DROP CROP ---

def preview_window(entry_widget, pieces, parent=None):
    if parent is None:
        parent = entry_widget.winfo_toplevel()

    for child in parent.winfo_children():
        if hasattr(child, "is_preview_frame") and child.is_preview_frame:
            child.destroy()

    preview_frame = tk.Frame(parent, bd=2, relief="groove")
    preview_frame.is_preview_frame = True
    preview_frame.pack(fill="both", expand=True, pady=5)

    tk.Label(preview_frame, text="Preview Sliced Images (168 mảnh)").pack()

    grid_frame = tk.Frame(preview_frame)
    grid_frame.pack(fill="both", expand=True)

    selected_piece = tk.StringVar()

    def on_select(piece_path):
        selected_piece.set(piece_path)
        logging.info("Đã chọn ảnh: %s", piece_path)

    thumbnails = []
    for index, p in enumerate(pieces):
        try:
            img = Image.open(p)
            img.thumbnail((100, 100))
            photo = ImageTk.PhotoImage(img)
            thumbnails.append(photo)
            btn = tk.Button(grid_frame, image=photo, command=lambda p=p: on_select(p))
            row = index // 12
            col = index % 12
            btn.grid(row=row, column=col, padx=2, pady=2)
        except Exception as e:
            logging.error("Lỗi hiển thị ảnh %s: %s", p, e)

    preview_frame.thumbnails = thumbnails

    def finalize_selection():
        piece_path = selected_piece.get()
        if piece_path:
            entry_widget.delete(0, tk.END)
            entry_widget.insert(0, piece_path)
            logging.info("Đã lưu ảnh điều kiện: %s", piece_path)
        else:
            messagebox.showwarning("Chọn ảnh", "Chưa chọn ảnh nào.")
        preview_frame.destroy()

    btn_finalize = tk.Button(preview_frame, text="Chọn và Lưu ảnh điều kiện", command=finalize_selection)
    btn_finalize.pack(pady=5)

def capture_telegram_window(entry_widget):
    import pyautogui
    try:
        import win32gui, win32con
    except ImportError:
        messagebox.showerror("Lỗi", "Chưa cài đặt module cần thiết: pywin32")
        return

    global GLOBAL_TELEGRAM_HWND
    if not GLOBAL_TELEGRAM_HWND:
        messagebox.showwarning("Warning", "Chưa set HWND của Telegram.")
        return

    try:
        win32gui.SetForegroundWindow(GLOBAL_TELEGRAM_HWND)
        rect = win32gui.GetWindowRect(GLOBAL_TELEGRAM_HWND)
        x, y, x2, y2 = rect
        logging.info("Kích thước ban đầu của Telegram: %s", rect)
        win32gui.MoveWindow(GLOBAL_TELEGRAM_HWND, x, y, 500, 504, True)
        time.sleep(0.5)
        rect = win32gui.GetWindowRect(GLOBAL_TELEGRAM_HWND)
        x, y, x2, y2 = rect
        w = x2 - x
        h = y2 - y

        if w != 500 or h != 504:
            win32gui.MoveWindow(GLOBAL_TELEGRAM_HWND, x, y, 500, 504, True)
            time.sleep(0.5)
            rect = win32gui.GetWindowRect(GLOBAL_TELEGRAM_HWND)
            x, y, x2, y2 = rect
            w = x2 - x
            h = y2 - y
        logging.info("Kích thước cập nhật của Telegram: (%s, %s, %s, %s)", x, y, w, h)
    except Exception as e:
        messagebox.showerror("Lỗi", f"Lỗi khi đưa cửa sổ lên top hoặc thay đổi kích thước: {e}")
        return

    screenshot_img = pyautogui.screenshot(region=(x, y, w, h))
    logging.info("Đã chụp ảnh cửa sổ Telegram.")

    # --- BEGIN: CHUYỂN SANG CHẾ ĐỘ KÉO THẢ ĐỂ CẮT ẢNH ---
    logging.debug("consolog: Chuyển sang chế độ kéo thả cắt ảnh.")
    drag_crop_window(screenshot_img, entry_widget)
    # --- END: CHUYỂN SANG CHẾ ĐỘ KÉO THẢ ĐỂ CẮT ẢNH ---

    # Các đoạn mã cắt vụn theo lưới tự động dưới đây được comment để không gây xung đột
    """
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    folder_base = os.path.join(os.getcwd(), "sliced_images")
    if not os.path.exists(folder_base):
        os.makedirs(folder_base)
    folder = os.path.join(folder_base, timestamp)
    os.makedirs(folder, exist_ok=True)

    rows, cols = 14, 12
    img_width, img_height = screenshot_img.size
    piece_width = img_width // cols
    piece_height = img_height // rows
    pieces = []
    for r in range(rows):
        for c in range(cols):
            left = c * piece_width
            upper = r * piece_height
            right = img_width if c == cols - 1 else left + piece_width
            lower = img_height if r == rows - 1 else upper + piece_height
            piece = screenshot_img.crop((left, upper, right, lower))
            piece_filename = os.path.join(folder, f"piece_{r}_{c}.png")
            try:
                piece.save(piece_filename)
            except Exception as e:
                logging.error("Lỗi lưu ảnh %s: %s", piece_filename, e)
            pieces.append(piece_filename)
    logging.info("Chụp và cắt vụn thành %s ảnh tại %s.", len(pieces), folder)

    entry_widget.delete(0, tk.END)
    entry_widget.insert(0, folder)
    parent = entry_widget.winfo_toplevel()
    preview_window(entry_widget, pieces, parent=parent)
    """
    
def find_image(img_path):
    import pyautogui
    try:
        loc = pyautogui.locateOnScreen(img_path, confidence=0.8)
    except pyautogui.ImageNotFoundException:
        loc = None
    return loc is not None

# Lớp VisualBuilder và ScriptBuilder dưới đây giữ nguyên phần lớn cấu trúc ban đầu.
# Chúng giúp xây dựng script, hiển thị UI và các thao tác liên quan.

class VisualBuilder(tk.Frame):
    def __init__(self, master, update_script_callback):
        super().__init__(master)
        self.update_script_callback = update_script_callback
        self.command_list = []
        self.available_commands = [
            "Mouse Click",
            "Delay",
            "Keyboard Input",
            "If - Else",
            "Loop",
            "Break",
            "UI Check",
            "Find Image and Click",
            "Screenshot",
            "If Image Found",
            "If Image Found (No Else)",
            "Scroll Up",
            "Scroll Down",
            "Read File",
            "Write File"
        ]
        self.create_widgets()

        self.mouse_click_x = tk.StringVar(value="100")
        self.mouse_click_y = tk.StringVar(value="200")

        self.bind_all("<F1>", self.capture_f1_coord)

    def capture_f1_coord(self, event):
        try:
            import win32api
            abs_x, abs_y = win32api.GetCursorPos()
        except:
            messagebox.showwarning("Warning", "win32api chưa sẵn sàng hoặc bị thiếu.")
            return
        rel_x, rel_y = convert_to_relative(abs_x, abs_y)
        self.mouse_click_x.set(str(rel_x))
        self.mouse_click_y.set(str(rel_y))
        messagebox.showinfo("F1", f"Đã chụp tọa độ Mouse Click = ({rel_x}, {rel_y}).")

    def create_widgets(self):
        frm_left = tk.Frame(self)
        frm_left.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)

        tk.Label(frm_left, text="Available Commands").pack()
        self.lb_available = tk.Listbox(frm_left, height=12)
        for cmd in self.available_commands:
            self.lb_available.insert(tk.END, cmd)
        self.lb_available.pack(fill=tk.BOTH, expand=True)

        btn_add = tk.Button(frm_left, text="Add >>", command=self.add_command)
        btn_add.pack(pady=5)

        frm_right = tk.Frame(self)
        frm_right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        tk.Label(frm_right, text="Script Steps").pack()
        self.lb_steps = tk.Listbox(frm_right, height=15)
        self.lb_steps.pack(fill=tk.BOTH, expand=True)

        frm_btn = tk.Frame(frm_right)
        frm_btn.pack(fill=tk.X)

        tk.Button(frm_btn, text="Up", command=self.move_up).pack(side=tk.LEFT, padx=2)
        tk.Button(frm_btn, text="Down", command=self.move_down).pack(side=tk.LEFT, padx=2)
        tk.Button(frm_btn, text="Remove", command=self.remove_command).pack(side=tk.LEFT, padx=2)

        tk.Button(frm_btn, text="Generate Script", command=self.generate_script).pack(side=tk.RIGHT, padx=2)
        tk.Button(frm_btn, text="General (xuất .py)", command=self.generate_full_script_file).pack(side=tk.RIGHT, padx=2)

    def add_command(self):
        try:
            selection = self.lb_available.curselection()[0]
        except IndexError:
            messagebox.showwarning("Chọn lệnh", "Vui lòng chọn 1 lệnh từ danh sách bên trái.")
            return
        cmd = self.available_commands[selection]
        params = self.configure_command(cmd)
        if params is not None:
            self.command_list.append({"command": cmd, "params": params})
            self.lb_steps.insert(tk.END, f"{cmd} {params}")

    def remove_command(self):
        try:
            index = self.lb_steps.curselection()[0]
        except IndexError:
            return
        del self.command_list[index]
        self.lb_steps.delete(index)

    def move_up(self):
        try:
            index = self.lb_steps.curselection()[0]
        except IndexError:
            return
        if index == 0:
            return
        self.command_list[index-1], self.command_list[index] = self.command_list[index], self.command_list[index-1]
        self.refresh_steps()
        self.lb_steps.selection_set(index-1)

    def move_down(self):
        try:
            index = self.lb_steps.curselection()[0]
        except IndexError:
            return
        if index >= len(self.command_list) - 1:
            return
        self.command_list[index+1], self.command_list[index] = self.command_list[index], self.command_list[index+1]
        self.refresh_steps()
        self.lb_steps.selection_set(index+1)

    def refresh_steps(self):
        self.lb_steps.delete(0, tk.END)
        for item in self.command_list:
            self.lb_steps.insert(tk.END, f"{item['command']} {item['params']}")

    def configure_command(self, cmd):
        dlg = tk.Toplevel(self)
        dlg.grab_set()
        dlg.title(f"Configure: {cmd}")
        entries = {}
        result = {}

        def add_field(label_text, default=""):
            row = tk.Frame(dlg)
            row.pack(side=tk.TOP, fill=tk.X, padx=5, pady=2)
            lbl = tk.Label(row, text=label_text, width=20, anchor='w')
            lbl.pack(side=tk.LEFT)
            ent = tk.Entry(row)
            ent.pack(side=tk.RIGHT, expand=True, fill=tk.X)
            ent.insert(0, str(default))
            entries[label_text] = ent

        def paste_clip():
            try:
                clip_data = dlg.clipboard_get()
                if ',' in clip_data:
                    cx, cy = clip_data.split(',', 1)
                    cx, cy = cx.strip(), cy.strip()
                    if "x" in entries and "y" in entries:
                        entries["x"].delete(0, tk.END)
                        entries["x"].insert(0, cx)
                        entries["y"].delete(0, tk.END)
                        entries["y"].insert(0, cy)
            except:
                pass

        def capture_3s_in_dialog():
            messagebox.showinfo("Chụp Tọa Độ (Mouse Click)",
                                "Hãy di chuột đến vị trí muốn lấy.\nSau 3 giây sẽ tự động chụp.")
            dlg.after(3000, do_capture_in_dialog)

        def do_capture_in_dialog():
            try:
                import win32api
                abs_x, abs_y = win32api.GetCursorPos()
                rx, ry = convert_to_relative(abs_x, abs_y)
                if "x" in entries and "y" in entries:
                    entries["x"].delete(0, tk.END)
                    entries["x"].insert(0, str(rx))
                    entries["y"].delete(0, tk.END)
                    entries["y"].insert(0, str(ry))
                messagebox.showinfo("Kết Quả",
                                    f"Toạ độ tuyệt đối: ({abs_x}, {abs_y})\n"
                                    f"Toạ độ tương đối: ({rx}, {ry})\n"
                                    f"(Đã điền vào trường x,y.)")
            except:
                messagebox.showwarning("Lỗi", "Không lấy được toạ độ.")

        if cmd == "Mouse Click":
            add_field("x", self.mouse_click_x.get())
            add_field("y", self.mouse_click_y.get())
            btn_paste = tk.Button(dlg, text="Paste from Clipboard", command=paste_clip)
            btn_paste.pack(pady=5)
            btn_3s = tk.Button(dlg, text="Chụp Tọa Độ (3s)", command=capture_3s_in_dialog)
            btn_3s.pack(pady=5)
        elif cmd == "Delay":
            add_field("seconds", 1)
        elif cmd == "Keyboard Input":
            add_field("key", "vk")
            add_field("action", "press")
        elif cmd == "If - Else":
            add_field("condition", "a == b")
            add_field("then", "print('True')")
            add_field("else", "print('False')")
        elif cmd == "Loop":
            add_field("count", 5)
            add_field("body", "print(i)")
        elif cmd == "Break":
            pass
        elif cmd == "UI Check":
            add_field("window_title", "MyWindow")
        elif cmd == "Find Image and Click":
            add_field("image_path", "path_to_image.png")
            btn_cap = tk.Button(
                dlg,
                text="Chụp & Cắt vụn cửa sổ Telegram",
                command=lambda: capture_telegram_window(entries["image_path"])
            )
            btn_cap.pack(pady=5)
        elif cmd == "Screenshot":
            add_field("filename", "screenshot.png")
            add_field("region_x", 0)
            add_field("region_y", 0)
            add_field("region_width", 300)
            add_field("region_height", 200)
        elif cmd == "If Image Found":
            add_field("image_path", "path_to_image.png")
            add_field("if_found", "print('found image')")
            add_field("if_not_found", "# do nothing")
            btn_cap = tk.Button(
                dlg,
                text="Chụp & Cắt vụn cửa sổ Telegram",
                command=lambda: capture_telegram_window(entries["image_path"])
            )
            btn_cap.pack(pady=5)
        elif cmd == "If Image Found (No Else)":
            add_field("image_path", "path_to_image.png")
            add_field("if_found", "print('found image')")
            btn_cap = tk.Button(
                dlg,
                text="Chụp & Cắt vụn cửa sổ Telegram",
                command=lambda: capture_telegram_window(entries["image_path"])
            )
            btn_cap.pack(pady=5)
        elif cmd == "Scroll Up":
            add_field("steps", 3)
        elif cmd == "Scroll Down":
            add_field("steps", 3)
        elif cmd == "Read File":
            add_field("file_path", "myfile.txt")
            add_field("var_name", "file_content")
            def do_browse_open():
                fpath = filedialog.askopenfilename(title="Chọn file",
                                                   filetypes=[("All files", "*.*")])
                if fpath:
                    entries["file_path"].delete(0, tk.END)
                    entries["file_path"].insert(0, fpath)
            btn = tk.Button(dlg, text="Browse...", command=do_browse_open)
            btn.pack(pady=5)
        elif cmd == "Write File":
            add_field("file_path", "output.txt")
            add_field("content", "Hello world")
            def do_browse_save():
                fpath = filedialog.asksaveasfilename(title="Chọn nơi lưu file",
                                                     defaultextension=".txt",
                                                     filetypes=[("All files", "*.*")])
                if fpath:
                    entries["file_path"].delete(0, tk.END)
                    entries["file_path"].insert(0, fpath)
            btn = tk.Button(dlg, text="Browse...", command=do_browse_save)
            btn.pack(pady=5)

        def on_ok():
            for k, ent in entries.items():
                result[k.lower()] = ent.get()
            dlg.destroy()
        tk.Button(dlg, text="OK", command=on_ok).pack(pady=5)
        dlg.wait_window()
        return result

    def generate_script(self):
        lines = [
            "# Script được sinh tự động từ Visual Builder",
            "import pyautogui",
            "import time",
            "",
            "def screenshot(filename, region=(0,0,300,200)):",
            "    pyautogui.screenshot(filename, region=region)",
            "",
            "def find_image(img_path):",
            "    try:",
            "        loc = pyautogui.locateOnScreen(img_path, confidence=0.8)",
            "    except pyautogui.ImageNotFoundException:",
            "        loc = None",
            "    return loc is not None",
            ""
        ]
        for item in self.command_list:
            cmd = item["command"]
            params = item["params"]
            if cmd == "Mouse Click":
                line = f"pyautogui.click({params.get('x', 0)}, {params.get('y', 0)})"
            elif cmd == "Delay":
                line = f"time.sleep({params.get('seconds', 1)})  # Delay"
            elif cmd == "Keyboard Input":
                action = params.get("action", "press")
                key = params.get("key", "")
                if action == "press":
                    line = f"pyautogui.press('{key}')  # press"
                elif action == "release":
                    line = f"pyautogui.keyUp('{key}')   # release"
                else:
                    line = f"pyautogui.press('{key}')   # press+release"
            elif cmd == "If - Else":
                condition = params.get("condition", "condition")
                then_part = params.get("then", "# do something")
                else_part = params.get("else", "# do something else")
                line = f"if {condition}:\n    {then_part}\nelse:\n    {else_part}"
            elif cmd == "Loop":
                count = params.get("count", 1)
                body = params.get("body", "# loop body")
                line = f"for i in range({count}):\n    {body}"
            elif cmd == "Break":
                line = "break"
            elif cmd == "UI Check":
                window_title = params.get("window_title", "Window Title")
                line = f"# if check_window('{window_title}'):\n#     # do something"
            elif cmd == "Find Image and Click":
                image_path = params.get("image_path", "path_to_image.png")
                line = (
                    "try:\n"
                    f"    loc = pyautogui.locateOnScreen(r'{image_path}', confidence=0.8)\n"
                    "except pyautogui.ImageNotFoundException:\n"
                    "    loc = None\n"
                    "if loc:\n"
                    "    pyautogui.click(loc.left, loc.top)"
                )
            elif cmd == "Screenshot":
                filename = params.get("filename", "screenshot.png")
                rx = params.get("region_x", "0")
                ry = params.get("region_y", "0")
                rw = params.get("region_width", "300")
                rh = params.get("region_height", "200")
                line = f"screenshot('{filename}', region=({rx}, {ry}, {rw}, {rh}))"
            elif cmd == "If Image Found":
                img = params.get("image_path", "path_to_image.png")
                if_found = params.get("if_found", "print('found image')")
                if_not = params.get("if_not_found", "# do nothing")
                line = (
                    "try:\n"
                    f"    loc = pyautogui.locateOnScreen(r'{img}', confidence=0.8)\n"
                    "except pyautogui.ImageNotFoundException:\n"
                    "    loc = None\n"
                    "if loc:\n"
                    f"    {if_found}\n"
                    "else:\n"
                    f"    {if_not}"
                )
            elif cmd == "If Image Found (No Else)":
                img = params.get("image_path", "path_to_image.png")
                if_found = params.get("if_found", "print('found image')")
                line = (
                    "try:\n"
                    f"    loc = pyautogui.locateOnScreen(r'{img}', confidence=0.8)\n"
                    "except pyautogui.ImageNotFoundException:\n"
                    "    loc = None\n"
                    "if loc:\n"
                    f"    {if_found}"
                )
            elif cmd == "Scroll Up":
                steps = params.get("steps", 1)
                line = f"pyautogui.scroll({steps})  # Scroll Up"
            elif cmd == "Scroll Down":
                steps = params.get("steps", 1)
                line = f"pyautogui.scroll(-{steps})  # Scroll Down"
            elif cmd == "Read File":
                fpath = params.get("file_path", "myfile.txt")
                var_name = params.get("var_name", "file_content")
                line = (
                    f"# Read File:\n"
                    f"with open(r'{fpath}', 'r', encoding='utf-8') as f:\n"
                    f"    {var_name} = f.read()\n"
                    f"print({var_name})  # hoặc xử lý tiếp\n"
                )
            elif cmd == "Write File":
                fpath = params.get("file_path", "output.txt")
                content = params.get("content", "Hello")
                line = (
                    f"# Write File:\n"
                    f"with open(r'{fpath}', 'w', encoding='utf-8') as f:\n"
                    f"    f.write('{content}')\n"
                    f"print('Đã ghi xong vào {fpath}')\n"
                )
            else:
                line = "# Unknown command"
            lines.append(line)

        script = "\n".join(lines)
        self.update_script_callback(script)
        messagebox.showinfo("Script Generated", "Đã sinh mã script từ Visual Builder.")

    def generate_full_script_file(self):
        self.generate_script()

    def open_script_editor(self):
        editor_win = tk.Toplevel(self)
        editor_win.title("Edit Script")
        editor_win.geometry("1200x900")

        text_widget = tk.Text(editor_win, wrap='none')
        text_widget.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        text_widget.insert("1.0", self.script_text.get("1.0", tk.END))

        def save_script_edit():
            content = text_widget.get("1.0", tk.END)
            with open(self.script_file, "w", encoding="utf-8") as f:
                f.write(content)
            messagebox.showinfo("Save", f"Script đã được lưu vào {self.script_file}")

        def run_script():
            save_script_edit()
            try:
                subprocess.run(["python", self.script_file], check=True)
                messagebox.showinfo("Run", "Script chạy thành công!")
            except Exception as e:
                messagebox.showerror("Run Error", f"Lỗi khi chạy script: {str(e)}")

        btn_frame = tk.Frame(editor_win)
        btn_frame.pack(pady=5)
        btn_save = tk.Button(btn_frame, text="Save", command=save_script_edit)
        btn_save.pack(side=tk.LEFT, padx=5)
        btn_run = tk.Button(btn_frame, text="Run Script", command=run_script)
        btn_run.pack(side=tk.LEFT, padx=5)
        
        btn_run_json = tk.Button(btn_frame, text="Run JSON", command=self.run_json_from_file)
        btn_run_json.pack(side=tk.LEFT, padx=5)

    def run_json_from_file(self):
        file_path = filedialog.askopenfilename(title="Chọn file JSON", filetypes=[("JSON files", "*.json"), ("All files", "*.*")])
        if file_path:
            run_json_in_thread(file_path)

    def update_script_text(self, new_script):
        self.script_text.delete("1.0", tk.END)
        self.script_text.insert("1.0", new_script)

    def clear_record_display(self):
        self.record_display_text.delete("1.0", tk.END)

    def append_record_event(self, event):
        self.record_display_text.insert(tk.END, f"{event}\n")
        self.record_display_text.see(tk.END)

class ScriptBuilder(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("Script Builder")
        self.geometry("900x700")
        self.script_file = "built_script.py"

        global SCRIPT_BUILDER_APP
        SCRIPT_BUILDER_APP = self

        self.var_hwnd = tk.StringVar(value="")
        self.var_telegram_path = tk.StringVar(value=self.load_config().get("telegram_path", r"C:\Program Files\Telegram Desktop\Telegram.exe"))
        self.var_telegram_path.trace_add("write", self.on_telegram_path_change)

        self.create_widgets()

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logging.error("Error loading config: %s", e)
        return {}

    def save_config(self, config):
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=4)
        except Exception as e:
            logging.error("Error saving config: %s", e)

    def on_telegram_path_change(self, *args):
        config = self.load_config()
        config["telegram_path"] = self.var_telegram_path.get()
        self.save_config(config)
        logging.info("Telegram path updated and saved: %s", self.var_telegram_path.get())

    def create_widgets(self):
        notebook = ttk.Notebook(self)
        notebook.pack(fill=tk.BOTH, expand=True)

        self.tab_record = tk.Frame(notebook)
        notebook.add(self.tab_record, text="Ghi - Phát")

        frm_rec = tk.Frame(self.tab_record)
        frm_rec.pack(fill=tk.X, pady=5)

        btn_record = tk.Button(frm_rec, text="Ghi (Record)", command=start_recording)
        btn_record.pack(side=tk.LEFT, padx=5)
        btn_stop = tk.Button(frm_rec, text="Dừng (Stop)", command=stop_recording)
        btn_stop.pack(side=tk.LEFT, padx=5)
        btn_play = tk.Button(frm_rec, text="Phát (Play)", command=play_recording_in_thread)
        btn_play.pack(side=tk.LEFT, padx=5)
        btn_save_rec = tk.Button(frm_rec, text="Lưu (Save)", command=save_recording)
        btn_save_rec.pack(side=tk.LEFT, padx=5)
        btn_clear = tk.Button(frm_rec, text="Clear", command=clear_recording)
        btn_clear.pack(side=tk.LEFT, padx=5)

        btn_open_file = tk.Button(frm_rec, text="Mở file đã ghi", command=open_recorded_file)
        btn_open_file.pack(side=tk.LEFT, padx=5)

        tk.Label(self.tab_record, text="F9 = Ghi, F10 = Dừng (nhớ để cửa sổ Main App có focus)").pack(pady=5)

        text_frame = tk.Frame(self.tab_record)
        text_frame.pack(fill=tk.BOTH, expand=True)

        scrollbar_y = tk.Scrollbar(text_frame, orient="vertical")
        scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
        scrollbar_x = tk.Scrollbar(text_frame, orient="horizontal")
        scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)

        self.record_display_text = tk.Text(text_frame, wrap="none",
                                           xscrollcommand=scrollbar_x.set,
                                           yscrollcommand=scrollbar_y.set)
        self.record_display_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar_y.config(command=self.record_display_text.yview)
        scrollbar_x.config(command=self.record_display_text.xview)

        frm_extra = tk.Frame(self.tab_record)
        frm_extra.pack(fill=tk.X, pady=5)

        tk.Label(frm_extra, text="Số lần phát lại:").pack(side=tk.LEFT, padx=5)
        self.var_replay_count = tk.IntVar(value=1)
        entry_replay_count = tk.Entry(frm_extra, textvariable=self.var_replay_count, width=5)
        entry_replay_count.pack(side=tk.LEFT, padx=5)

        tk.Label(frm_extra, text="Tốc độ phát lại:").pack(side=tk.LEFT, padx=5)
        self.var_playback_speed = tk.DoubleVar(value=1.0)
        slider_speed = tk.Scale(frm_extra, variable=self.var_playback_speed, from_=0.5, to=2.0, resolution=0.1, orient=tk.HORIZONTAL)
        slider_speed.pack(side=tk.LEFT, padx=5)

        self.var_record_mode = tk.BooleanVar(value=True)
        chk_record_mode = tk.Checkbutton(frm_extra, text="Ghi trong của sổ (nếu tắt thì ghi toàn màn hình)", variable=self.var_record_mode, command=self.update_record_mode)
        chk_record_mode.pack(side=tk.LEFT, padx=5)

        self.tab_edit = tk.Frame(notebook)
        notebook.add(self.tab_edit, text="Chỉnh sửa Script")

        self.script_text = tk.Text(self.tab_edit, wrap='none')
        self.script_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        if os.path.exists(self.script_file):
            with open(self.script_file, "r", encoding="utf-8") as f:
                self.script_text.insert("1.0", f.read())
        else:
            self.script_text.insert("1.0", "# Đây là script của bạn\n")

        frm_save = tk.Frame(self.tab_edit)
        frm_save.pack(fill=tk.X, pady=5)

        btn_save_script = tk.Button(frm_save, text="Save Script", command=self.save_script)
        btn_save_script.pack(side=tk.LEFT, padx=5)

        btn_edit_script = tk.Button(frm_save, text="Edit Script (cửa sổ đầy đủ)", command=self.open_script_editor)
        btn_edit_script.pack(side=tk.LEFT, padx=5)

        self.tab_visual = tk.Frame(notebook)
        notebook.add(self.tab_visual, text="Visual Builder")

        self.visual_builder = VisualBuilder(self.tab_visual, self.update_script_text)
        self.visual_builder.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        frm_snippet = tk.Frame(self.tab_edit)
        frm_snippet.pack(fill=tk.X, pady=5)

        btn_if_else = tk.Button(
            frm_snippet, text="If - Else",
            command=lambda: self.insert_snippet("if condition:\n    # do something\nelse:\n    # do something else\n")
        )
        btn_if_else.pack(side=tk.LEFT, padx=5)

        btn_loop = tk.Button(
            frm_snippet, text="Loop",
            command=lambda: self.insert_snippet("for i in range(N):\n    # loop body\n")
        )
        btn_loop.pack(side=tk.LEFT, padx=5)

        btn_break = tk.Button(
            frm_snippet, text="Break",
            command=lambda: self.insert_snippet("break\n")
        )
        btn_break.pack(side=tk.LEFT, padx=5)

        btn_mouse_click = tk.Button(
            frm_snippet, text="Mouse Click",
            command=lambda: self.insert_snippet("# Mouse click at (x, y)\npyautogui.click(x, y)\n")
        )
        btn_mouse_click.pack(side=tk.LEFT, padx=5)

        btn_keyboard = tk.Button(
            frm_snippet, text="Keyboard Input",
            command=lambda: self.insert_snippet("# Keyboard input example\npyautogui.press('a')\n")
        )
        btn_keyboard.pack(side=tk.LEFT, padx=5)

        btn_delay = tk.Button(
            frm_snippet, text="Delay",
            command=lambda: self.insert_snippet("time.sleep(X)  # Delay\n")
        )
        btn_delay.pack(side=tk.LEFT, padx=5)

        btn_ui_check = tk.Button(
            frm_snippet, text="UI Check",
            command=lambda: self.insert_snippet("# Kiểm tra tên cửa sổ\nif check_window('Window Title'):\n    # do something\n")
        )
        btn_ui_check.pack(side=tk.LEFT, padx=5)

        btn_scroll_up = tk.Button(
            frm_snippet, text="Scroll Up",
            command=lambda: self.insert_snippet("pyautogui.scroll(5)\n")
        )
        btn_scroll_up.pack(side=tk.LEFT, padx=5)

        btn_scroll_down = tk.Button(
            frm_snippet, text="Scroll Down",
            command=lambda: self.insert_snippet("pyautogui.scroll(-5)\n")
        )
        btn_scroll_down.pack(side=tk.LEFT, padx=5)

        btn_read_file = tk.Button(
            frm_snippet, text="Read File",
            command=lambda: self.insert_snippet(
                "# Read File Example\n"
                "with open('myfile.txt', 'r', encoding='utf-8') as f:\n"
                "    data = f.read()\n"
                "print(data)\n"
            )
        )
        btn_read_file.pack(side=tk.LEFT, padx=5)

        btn_write_file = tk.Button(
            frm_snippet, text="Write File",
            command=lambda: self.insert_snippet(
                "# Write File Example\n"
                "with open('output.txt', 'w', encoding='utf-8') as f:\n"
                "    f.write('some content')\n"
            )
        )
        btn_write_file.pack(side=tk.LEFT, padx=5)

        frm_hwnd = tk.Frame(self.tab_record)
        frm_hwnd.pack(fill=tk.X, pady=5)

        tk.Label(frm_hwnd, text="HWND Telegram:").pack(side=tk.LEFT)
        entry_hwnd = tk.Entry(frm_hwnd, textvariable=self.var_hwnd, width=10)
        entry_hwnd.pack(side=tk.LEFT, padx=5)

        btn_set_hwnd = tk.Button(frm_hwnd, text="Áp dụng HWND", command=self.apply_hwnd)
        btn_set_hwnd.pack(side=tk.LEFT, padx=5)

        btn_capture_coord = tk.Button(frm_hwnd, text="Chụp Tọa Độ (3s)", command=self.capture_coordinate_after_3s)
        btn_capture_coord.pack(side=tk.LEFT, padx=5)

        frm_tele = tk.Frame(self.tab_record)
        frm_tele.pack(fill=tk.X, pady=5)

        tk.Label(frm_tele, text="Telegram Path:").pack(side=tk.LEFT)
        entry_tele = tk.Entry(frm_tele, textvariable=self.var_telegram_path, width=40)
        entry_tele.pack(side=tk.LEFT, padx=5)

        btn_open_tele = tk.Button(frm_tele, text="Mở Telegram & Lấy HWND", command=self.open_telegram_and_get_hwnd)
        btn_open_tele.pack(side=tk.LEFT, padx=5)

    def capture_coordinate_after_3s(self):
        messagebox.showinfo("Chụp Tọa Độ",
                            "Hãy di chuột đến vị trí muốn lấy.\nSau 3 giây sẽ tự động chụp.")
        self.after(3000, self.do_capture_coordinate)

    def do_capture_coordinate(self):
        import win32api
        x, y = win32api.GetCursorPos()
        rx, ry = convert_to_relative(x, y)
        self.clipboard_clear()
        self.clipboard_append(f"{rx},{ry}")
        messagebox.showinfo("Kết Quả",
                            f"Toạ độ tuyệt đối: ({x}, {y})\n"
                            f"Toạ độ tương đối: ({rx}, {ry})\n"
                            f"(Đã copy vào clipboard)")

    def update_record_mode(self):
        global RECORD_IN_WINDOW
        RECORD_IN_WINDOW = self.var_record_mode.get()

    def apply_hwnd(self):
        global GLOBAL_TELEGRAM_HWND, GLOBAL_OFFSET_X, GLOBAL_OFFSET_Y
        hwnd_str = self.var_hwnd.get().strip()
        if not hwnd_str.isdigit():
            messagebox.showwarning("HWND", "HWND không hợp lệ.")
            return
        h = int(hwnd_str)
        GLOBAL_TELEGRAM_HWND = h
        if PYNPUT_AVAILABLE:
            try:
                import win32gui
                if win32gui.IsWindow(h):
                    rect = win32gui.GetWindowRect(h)
                    GLOBAL_OFFSET_X = rect[0]
                    GLOBAL_OFFSET_Y = rect[1]
                    messagebox.showinfo("HWND", f"Đã thiết lập HWND={h}, offset=({GLOBAL_OFFSET_X},{GLOBAL_OFFSET_Y}).")
                else:
                    messagebox.showwarning("HWND", "HWND này không phải cửa sổ hợp lệ.")
            except:
                messagebox.showwarning("win32gui", "win32gui chưa khả dụng.")
        else:
            messagebox.showwarning("pynput", "pynput chưa khả dụng, offset sẽ không chính xác.")

    def open_telegram_and_get_hwnd(self):
        telegram_path = self.var_telegram_path.get().strip()
        if not telegram_path:
            messagebox.showwarning("Path", "Vui lòng nhập đường dẫn Telegram.exe")
            return
        try:
            subprocess.Popen(telegram_path)
        except FileNotFoundError:
            messagebox.showerror("Telegram", "Không tìm thấy file Telegram. Kiểm tra lại đường dẫn.")
            return

        time.sleep(3)

        import win32gui
        found = []
        def enum_handler(hwnd, results):
            wtext = win32gui.GetWindowText(hwnd)
            if "Telegram" in wtext:
                results.append(hwnd)
        win32gui.EnumWindows(enum_handler, found)

        if found:
            hwnd_telegram = found[0]
            self.var_hwnd.set(str(hwnd_telegram))
            self.apply_hwnd()
            messagebox.showinfo("Telegram", f"Đã mở Telegram, HWND={hwnd_telegram}")
        else:
            messagebox.showwarning("Telegram", "Không tìm thấy cửa sổ Telegram.")

    def insert_snippet(self, snippet):
        self.script_text.insert(tk.INSERT, snippet)

    def save_script(self):
        with open(self.script_file, "w", encoding="utf-8") as f:
            f.write(self.script_text.get("1.0", tk.END))
        messagebox.showinfo("Save", f"Script đã được lưu vào {self.script_file}")

    def open_script_editor(self):
        editor_win = tk.Toplevel(self)
        editor_win.title("Edit Script")
        editor_win.geometry("1200x900")

        text_widget = tk.Text(editor_win, wrap='none')
        text_widget.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        text_widget.insert("1.0", self.script_text.get("1.0", tk.END))

        def save_script_edit():
            content = text_widget.get("1.0", tk.END)
            with open(self.script_file, "w", encoding="utf-8") as f:
                f.write(content)
            messagebox.showinfo("Save", f"Script đã được lưu vào {self.script_file}")

        def run_script():
            save_script_edit()
            try:
                subprocess.run(["python", self.script_file], check=True)
                messagebox.showinfo("Run", "Script chạy thành công!")
            except Exception as e:
                messagebox.showerror("Run Error", f"Lỗi khi chạy script: {str(e)}")

        btn_frame = tk.Frame(editor_win)
        btn_frame.pack(pady=5)
        btn_save = tk.Button(btn_frame, text="Save", command=save_script_edit)
        btn_save.pack(side=tk.LEFT, padx=5)
        btn_run = tk.Button(btn_frame, text="Run Script", command=run_script)
        btn_run.pack(side=tk.LEFT, padx=5)
        
        btn_run_json = tk.Button(btn_frame, text="Run JSON", command=self.run_json_from_file)
        btn_run_json.pack(side=tk.LEFT, padx=5)

    def run_json_from_file(self):
        file_path = filedialog.askopenfilename(title="Chọn file JSON", filetypes=[("JSON files", "*.json"), ("All files", "*.*")])
        if file_path:
            run_json_in_thread(file_path)

    def update_script_text(self, new_script):
        self.script_text.delete("1.0", tk.END)
        self.script_text.insert("1.0", new_script)

    def clear_record_display(self):
        self.record_display_text.delete("1.0", tk.END)

    def append_record_event(self, event):
        self.record_display_text.insert(tk.END, f"{event}\n")
        self.record_display_text.see(tk.END)

if __name__ == "__main__":
    root = tk.Tk()
    root.title("Main App")
    app = ScriptBuilder(root)
    
    root.bind_all("<F9>", lambda e: start_recording())
    root.bind_all("<F10>", lambda e: stop_recording())
    
    root.mainloop()
