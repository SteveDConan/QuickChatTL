import os
import json
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading
import logging
import time

# Biến toàn cục từ main.py
RECORD_IN_WINDOW = True

# Đường dẫn thư mục Scripts
SCRIPTS_DIR = os.path.join(os.getcwd(), "Scripts")
if not os.path.exists(SCRIPTS_DIR):
    os.makedirs(SCRIPTS_DIR)
    print(f"Consolog: Đã tạo thư mục Scripts tại {SCRIPTS_DIR}")
    logging.info(f"Đã tạo thư mục Scripts tại {SCRIPTS_DIR}")

class ScriptEditor(tk.Toplevel):
    def __init__(self, master, script_name):
        super().__init__(master)
        self.script_name = script_name  # Tên cơ bản, không bao gồm hậu tố
        self.script_file = os.path.join(SCRIPTS_DIR, f"{script_name}_py.py")
        self.title(f"Script Editor: {script_name}")
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
        if os.path.exists(self.script_file):
            with open(self.script_file, "r", encoding="utf-8") as f:
                content = f.read()
            self.text.insert("1.0", content)
            print(f"Consolog: Đã tải nội dung từ {self.script_file}")
            logging.info(f"Đã tải nội dung từ {self.script_file}")
        else:
            self.text.insert("1.0", f"# Mã script mặc định cho {script_name}_py.py\n")
            print(f"Consolog: Tạo nội dung mặc định cho {self.script_file}")
            logging.info(f"Tạo nội dung mặc định cho {self.script_file}")
        self.update_line_numbers()

    def update_line_numbers(self, event=None):
        self.linenumbers.config(state='normal')
        self.linenumbers.delete("1.0", tk.END)
        total_lines = int(self.text.index('end-1c').split('.')[0])
        for i in range(1, total_lines + 1):
            self.linenumbers.insert(tk.END, f"{i}\n")
        self.linenumbers.config(state='disabled')

    def open_file(self):
        file_path = filedialog.askopenfilename(
            initialdir=SCRIPTS_DIR,
            filetypes=[("Python Files", "*_py.py"),
                      ("Text Files", "*_txt.txt"),
                      ("JSON Files", "*_json.json"),
                      ("All Files", "*.*")]
        )
        if file_path:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            self.text.delete("1.0", tk.END)
            self.text.insert("1.0", content)
            self.script_file = file_path
            self.script_name = os.path.basename(file_path).split('_')[0]
            self.title(f"Script Editor: {self.script_name}")
            self.update_line_numbers()
            print(f"Consolog: Đã mở file {file_path}")
            logging.info(f"Đã mở file {file_path}")

    def save_file(self):
        try:
            with open(self.script_file, "w", encoding="utf-8") as f:
                content = self.text.get("1.0", tk.END)
                f.write(content)
            messagebox.showinfo("Save", f"Script saved to {self.script_file}")
            print(f"Consolog: Đã lưu script vào {self.script_file}")
            logging.info(f"Đã lưu script vào {self.script_file}")
        except Exception as e:
            messagebox.showerror("Error", f"Lỗi khi lưu file: {str(e)}")
            logging.error(f"Lỗi khi lưu file: {e}")

    def save_as(self):
        file_path = filedialog.asksaveasfilename(
            initialdir=SCRIPTS_DIR,
            defaultextension=".py",
            filetypes=[("Python Files", "*_py.py"),
                      ("Text Files", "*_txt.txt"),
                      ("JSON Files", "*_json.json"),
                      ("All Files", "*.*")]
        )
        if file_path:
            self.script_file = file_path
            self.script_name = os.path.basename(file_path).split('_')[0]
            self.save_file()
            self.title(f"Script Editor: {self.script_name}")

def run_json_script(json_content):
    global RECORD_IN_WINDOW
    logging.info("Bắt đầu chạy JSON script với nội dung: %s", json_content)
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
    try:
        import win32gui
        import win32con
        import win32process
    except ImportError:
        win32gui = None
        win32process = None
        logging.error("Không import được win32 modules.")
        return

    def is_telegram_window(hwnd):
        if hwnd and win32gui and win32gui.IsWindow(hwnd):
            title = win32gui.GetWindowText(hwnd).lower()
            return "telegram" in title
        return False

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
    if "events" in json_content:
        events = json_content["events"]
        prev_time = 0
        for event in events:
            current_time = event.get("time", 0)
            delay_duration = current_time - prev_time
            if delay_duration > 0:
                wait_with_pause(delay_duration)
            event_type = event.get("type")
            print(f"Consolog: Xử lý sự kiện {event_type} (được xử lý bởi script ngoài)")
            logging.info(f"Xử lý sự kiện {event_type} (được xử lý bởi script ngoài)")
            prev_time = current_time
    else:
        for act in json_content.get("actions", []):
            if not isinstance(act, dict):
                logging.error(f"Action không hợp lệ (không phải dict): {act}")
                continue
            action_type = act.get("action") or act.get("type")
            logging.info(f"Thực hiện action: {act}")
            print(f"Consolog: Xử lý action {action_type} (được xử lý bởi script ngoài)")
            logging.info(f"Xử lý action {action_type} (được xử lý bởi script ngoài)")

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

def check_telegram_hwnd(hwnd):
    try:
        import win32gui
    except ImportError:
        logging.error("Không import được win32gui.")
        return False
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

def open_edit_script(script_name, master):
    print("Consolog: Mở Script Editor cho script:", script_name)
    logging.info(f"Mở Script Editor cho script: {script_name}")
    config_file = os.path.join(SCRIPTS_DIR, "config.json")
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
    editor_win.title(f"Edit Script: {script_name}")
    editor_win.geometry("800x650")
    mode_frame = tk.Frame(editor_win)
    mode_frame.pack(fill='x', padx=5, pady=5)
    tk.Label(mode_frame, text="Chọn chế độ chạy:").pack(side=tk.LEFT)
    run_mode = tk.StringVar(value=default_mode)
    rb_python = tk.Radiobutton(mode_frame, text="Python", variable=run_mode, value="python")
    rb_txt = tk.Radiobutton(mode_frame, text="Text", variable=run_mode, value="txt")
    rb_json = tk.Radiobutton(mode_frame, text="JSON", variable=run_mode, value="json")
    rb_python.pack(side=tk.LEFT, padx=10)
    rb_txt.pack(side=tk.LEFT, padx=10)
    rb_json.pack(side=tk.LEFT, padx=10)
    notebook = ttk.Notebook(editor_win)
    notebook.pack(fill='both', expand=True, padx=5, pady=5)
    py_frame = tk.Frame(notebook)
    txt_frame = tk.Frame(notebook)
    json_frame = tk.Frame(notebook)
    notebook.add(py_frame, text="Python Script (_py.py)")
    notebook.add(txt_frame, text="Text Script (_txt.txt)")
    notebook.add(json_frame, text="JSON Script (_json.json)")
    py_text = tk.Text(py_frame, wrap='none')
    py_text.pack(fill='both', expand=True)
    txt_text = tk.Text(txt_frame, wrap='none')
    txt_text.pack(fill='both', expand=True)
    json_text = tk.Text(json_frame, wrap='none')
    json_text.pack(fill='both', expand=True)
    py_file = os.path.join(SCRIPTS_DIR, f"{script_name}_py.py")
    if os.path.exists(py_file):
        with open(py_file, "r", encoding="utf-8") as f:
            content = f.read()
        py_text.insert("1.0", content)
        print(f"Consolog: Đã tải script Python từ {py_file}")
        logging.info(f"Đã tải script Python từ {py_file}")
    else:
        py_text.insert("1.0", f"# Mã script mặc định cho {script_name}_py.py\n")
        print(f"Consolog: Tạo nội dung mặc định cho {py_file}")
        logging.info(f"Tạo nội dung mặc định cho {py_file}")
    txt_file = os.path.join(SCRIPTS_DIR, f"{script_name}_txt.txt")
    if os.path.exists(txt_file):
        with open(txt_file, "r", encoding="utf-8") as f:
            txt_content = f.read()
        txt_text.insert("1.0", txt_content)
        print(f"Consolog: Đã tải script Text từ {txt_file}")
        logging.info(f"Đã tải script Text từ {txt_file}")
    json_file = os.path.join(SCRIPTS_DIR, f"{script_name}_json.json")
    if os.path.exists(json_file):
        with open(json_file, "r", encoding="utf-8") as f:
            json_content = f.read()
        json_text.insert("1.0", json_content)
        print(f"Consolog: Đã tải script JSON từ {json_file}")
        logging.info(f"Đã tải script JSON từ {json_file}")
    
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
            file_to_save = os.path.join(SCRIPTS_DIR, f"{script_name}_py.py")
            print("Consolog: Lưu script dạng Python (_py.py)")
            logging.info("Lưu script dạng Python (_py.py)")
        elif current_tab.startswith("Text"):
            content = txt_text.get("1.0", tk.END)
            file_to_save = os.path.join(SCRIPTS_DIR, f"{script_name}_txt.txt")
            print("Consolog: Lưu script dạng Text (_txt.txt)")
            logging.info("Lưu script dạng Text (_txt.txt)")
        else:
            content = json_text.get("1.0", tk.END)
            file_to_save = os.path.join(SCRIPTS_DIR, f"{script_name}_json.json")
            print("Consolog: Lưu script dạng JSON (_json.json)")
            logging.info("Lưu script dạng JSON (_json.json)")
        try:
            with open(file_to_save, "w", encoding="utf-8") as f:
                f.write(content)
            messagebox.showinfo("Save", f"Script saved to {file_to_save}")
            logging.info(f"Lưu script thành công: {file_to_save}")
        except Exception as e:
            messagebox.showerror("Error", f"Lỗi khi lưu file: {str(e)}")
            logging.error(f"Lỗi khi lưu file: {e}")

    btn_frame = tk.Frame(editor_win)
    btn_frame.pack(pady=5)
    btn_save = tk.Button(btn_frame, text="Save", command=save_script_edit)
    btn_save.pack(side=tk.LEFT, padx=5)