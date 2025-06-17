import os
import time
import shutil
import subprocess
import math
import threading
import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
from PIL import Image, ImageChops, ImageTk

# Biến toàn cục cho Check Live
check_live_thread = None
check_live_pause_event = threading.Event()
check_live_status = {}
confirm_done = False
tdata_process_map = {}
TEMP_SCREENSHOT_FOLDER = None
MARKER_IMAGE_PATH = os.path.join(os.getcwd(), "marker_image.png")

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
def show_marker_selection_popup(screenshot_paths, root):
    print("Consolog: Hiển thị popup chọn marker image...")
    popup = tk.Toplevel(root)
    popup.title("Chọn marker image")
    popup.geometry("800x600")
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

    tk.Button(popup, text="Xác nhận", command=on_confirm).pack(pady=10)
    popup.transient(root)
    popup.grab_set()
    root.wait_window(popup)

# Luồng so sánh ảnh
def screenshot_comparison_worker(root, entry_path, lang, arrange_telegram_windows):
    from appxx import get_window_handle_by_pid, capture_window, user32, wintypes, ctypes
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
        show_marker_selection_popup(screenshot_paths, root)
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
def check_live_window(root, entry_path, lang, arrange_telegram_windows):
    from app import log_message, get_tdata_folders, config, save_config, arrange_width, arrange_height, send2trash
    global cl_win, refresh_table_global
    cl_win = tk.Toplevel(root)
    cl_win.title(lang["check_live_title"])
    cl_win.geometry("1200x500")

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
            threading.Thread(target=screenshot_comparison_worker, args=(root, entry_path, lang, arrange_telegram_windows), daemon=True).start()
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

# Hàm cảnh báo trước khi check live
def warn_check_live(root, entry_path, lang, close_all_telegram, arrange_telegram_windows):
    warning_msg = (
        "【Tiếng Việt】: Để đảm bảo tính năng Check live hoạt động chính xác và hiệu quả, vui lòng đóng tất cả các phiên bản Telegram đang chạy trên máy tính của bạn. Bạn có muốn đóng chúng ngay bây giờ?\n"
        "【English】: To ensure the Check live feature works accurately and efficiently, please close all running Telegram instances on your computer. Would you like to close them now?\n"
        "【中文】: 为了确保 'Check live' 功能准确高效地运行，请关闭您电脑上所有正在运行的 Telegram 程序。您是否希望立即关闭它们？"
    )
    res = messagebox.askyesno("Cảnh báo", warning_msg)
    if res:
        close_all_telegram()
    check_live_window(root, entry_path, lang, arrange_telegram_windows)