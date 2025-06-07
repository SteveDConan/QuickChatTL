# gui/check_live_window.py
import tkinter as tk
from tkinter import ttk, messagebox
import os
import shutil
import subprocess
import threading
import time
from PIL import Image
import ctypes
from ctypes import wintypes
from config.config import load_window_size, save_window_size, MARKER_IMAGE_PATH
from config.language import lang
from telegram.tdata_utils import get_tdata_folders
from telegram.telegram_control import open_telegram_with_tdata, arrange_telegram_windows, auto_close_telegram
from utils.screenshot_utils import compare_screenshot_with_marker, show_marker_selection_popup, capture_window
from utils.window_utils import center_window, get_window_handle_by_pid

try:
    from send2trash import send2trash
except ImportError:
    send2trash = None

check_live_thread = None
check_live_pause_event = threading.Event()
check_live_status = {}  # Biến toàn cục
confirm_done = False
tdata_process_map = {}
TEMP_SCREENSHOT_FOLDER = None

def warn_check_live(root, entry_path, log_message):
    warning_msg = (
        "【Tiếng Việt】: Để đảm bảo tính năng Check live hoạt động chính xác và hiệu quả, vui lòng đóng tất cả các phiên bản Telegram đang chạy trên máy tính của bạn. Bạn có muốn đóng chúng ngay bây giờ?\n"
        "【English】: To ensure the Check live feature works accurately and efficiently, please close all running Telegram instances on your computer. Would you like to close them now?\n"
        "【中文】: 为了确保 'Check live' 功能准确高效地运行，请关闭您电脑上所有正在运行的 Telegram 程序。您是否希望立即关闭它们？"
    )
    res = messagebox.askyesno("Cảnh báo", warning_msg)
    if res:
        auto_close_telegram(log_message)
    check_live_window(root, entry_path, log_message)

def check_live_window(root, entry_path, log_message):
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

    load_check_live_status_file()  # Gọi hàm cục bộ

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
                    proc = open_telegram_with_tdata(folder, log_message)
                    if proc:
                        pid = proc.pid
                        if tdata_name not in tdata_process_map:
                            tdata_process_map[tdata_name] = []
                        tdata_process_map[tdata_name].append(pid)
                        print(f"Consolog: Lưu PID {pid} cho TData {tdata_name}")
                        time.sleep(1)
                        check_live_status[tdata_name]["check"] = lang["completed"]
                    else:
                        check_live_status[tdata_name]["check"] = lang["exe_failed"]
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
            arrange_telegram_windows(root, custom_width, custom_height, for_check_live=True)

            cl_win.after(
                0,
                lambda: messagebox.showinfo(
                    "Check live",
                    "Quá trình mở telegram hoàn tất.\nHệ thống sẽ tự động so sánh hình ảnh sau 2 giây."
                )
            )

            threading.Thread(target=lambda: screenshot_comparison_worker(root, cl_win, refresh_table_global), daemon=True).start()

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
        auto_close_telegram(log_message)

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

    def screenshot_comparison_worker(root, cl_win, refresh_table_global):
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
            show_marker_selection_popup(screenshot_paths, root)  # Truyền root vào
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