# gui/login_window.py
import tkinter as tk
from tkinter import ttk, messagebox
import os
import asyncio
import threading
import re
from telegram.tdata_utils import get_tdata_folders, parse_2fa_info
from telegram.telethon_utils import login_account, update_privacy, TelegramClient
from telegram.telegram_control import open_telegram_with_tdata, close_all_telegram_threaded
from config.language import lang
from config.config import API_ID, API_HASH
from utils.window_utils import center_window

def login_all_accounts(root, entry_path, log_message):
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
            open_telethon_terminal(root, selected_session["path"])
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
    btn_update_privacy = tk.Button(frame_buttons_new, text=lang["update_privacy"], font=("Arial Unicode MS", 10, "bold"))
    btn_change_info = tk.Button(frame_buttons_new, text=lang["change_info"], font=("Arial Unicode MS", 10, "bold"))

    btn_create_session.pack(side=tk.LEFT, padx=5)
    btn_update_privacy.pack(side=tk.LEFT, padx=5)
    btn_change_info.pack(side=tk.LEFT, padx=5)

    btn_delete_all = tk.Button(login_window, text=lang["popup_inactive_delete"], font=("Arial Unicode MS", 10, "bold"))
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
        login_window.after(0, close_all_telegram_threaded, log_message)

    def start_login_process():
        btn_create_session.config(state=tk.DISABLED)
        threading.Thread(target=process_accounts, daemon=True).start()

    def run_tool():
        print("Consolog: Bắt đầu chạy tính năng cập nhật quyền riêng tư cho tất cả tài khoản.")
        tdata_dir = entry_path.get()
        if not os.path.exists(tdata_dir):
            messagebox.showerror("Lỗi", lang["msg_error_path"])
            return
        tdata_folders = get_tdata_folders(tdata_dir)
        for folder in tdata_folders:
            open_telegram_with_tdata(folder, log_message)
        time.sleep(10)
        for folder in tdata_folders:
            session_path = os.path.join(folder, "session")
            try:
                asyncio.run(update_privacy(session_path))
            except Exception as e:
                log_message(f"Consolog [ERROR]: Lỗi cập nhật quyền riêng tư cho {folder}: {e}")
        messagebox.showinfo("Hoàn thành", lang["msg_privacy_complete"])
        log_message("Consolog: Đã hoàn tất cập nhật quyền riêng tư.")

    def change_account_settings():
        print("Consolog: Yêu cầu thay đổi thông tin tài khoản.")
        messagebox.showinfo("Thông báo", lang["change_info_in_development"])

    def delete_all_sessions():
        print("Consolog: Yêu cầu xóa tất cả sessions...")
        tdata_dir = entry_path.get()
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
                    print(f"Consolog [ERROR]: Lỗi xóa file session {session_file}: {e}")
            if os.path.exists(session_folder) and os.path.isdir(session_folder):
                try:
                    shutil.rmtree(session_folder)
                    print(f"Consolog: Đã xóa thư mục session {session_folder}")
                except Exception as e:
                    print(f"Consolog [ERROR]: Lỗi xóa thư mục {session_folder}: {e}")
            deleted_accounts.append(os.path.basename(folder))
        messagebox.showinfo(lang["popup_inactive_title"], "Đã xóa session của các tài khoản: " + ", ".join(deleted_accounts))
        update_already_table()

    btn_create_session.config(command=start_login_process)
    btn_update_privacy.config(command=run_tool)
    btn_change_info.config(command=change_account_settings)
    btn_delete_all.config(command=delete_all_sessions)

def open_telethon_terminal(root, session_folder):
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
    btn_copy_phone = tk.Button(frame_phone, text="Copy", command=lambda: copy_to_clipboard(root, phone))
    btn_copy_phone.pack(side=tk.RIGHT)

    frame_pass = tk.Frame(term_win)
    frame_pass.pack(pady=5, fill=tk.X)
    lbl_pass = tk.Label(frame_pass, text=f"Password: {password}", anchor="w")
    lbl_pass.pack(side=tk.LEFT, expand=True, fill=tk.X)
    btn_copy_pass = tk.Button(frame_pass, text="Copy", command=lambda: copy_to_clipboard(root, password))
    btn_copy_pass.pack(side=tk.RIGHT)

    frame_otp = tk.Frame(term_win)
    frame_otp.pack(pady=5, fill=tk.X, padx=10)
    otp_var = tk.StringVar(value="OTP: ")
    lbl_otp = tk.Label(frame_otp, textvariable=otp_var, anchor="w")
    lbl_otp.pack(side=tk.LEFT, expand=True, fill=tk.X)
    btn_copy_otp = tk.Button(frame_otp, text="Copy", command=lambda: copy_to_clipboard(root, otp_var.get().replace('OTP: ', '')))
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

def copy_to_clipboard(root, text):
    root.clipboard_clear()
    root.clipboard_append(text)
    root.update()
    messagebox.showinfo("Copied", f"Đã copy: {text}")
    print(f"Consolog: Đã copy: {text}")