# telegram/tdata_utils.py
import os
import shutil
import tkinter as tk  # Thêm import này
from tkinter import messagebox
from config.language import lang

def get_tdata_folders(main_dir):
    if not os.path.exists(main_dir):
        return []
    folders = [
        os.path.join(main_dir, f) for f in os.listdir(main_dir)
        if os.path.isdir(os.path.join(main_dir, f))
    ]
    print(f"Consolog: Tìm thấy {len(folders)} thư mục TData trong {main_dir}")
    return folders

def update_stats(entry_path, text_stats):
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
    text_stats.delete("1.0", tk.END)  # Sử dụng tk.END
    text_stats.insert(tk.END, info_text)
    print("Consolog: Cập nhật stats thành công.")

def update_logged(entry_path, text_logged):
    tdata_dir = entry_path.get()
    logged_list = []
    for folder in get_tdata_folders(tdata_dir):
        session_file = os.path.join(folder, "session.session")
        session_folder = os.path.join(folder, "session")
        if os.path.exists(session_file) or os.path.exists(session_folder):
            logged_list.append(os.path.basename(folder))
    text_logged.delete("1.0", tk.END)  # Sử dụng tk.END
    if logged_list:
        text_logged.insert(tk.END, ", ".join(logged_list))
    else:
        text_logged.insert(tk.END, lang["not_found"])
    print("Consolog: Cập nhật logged sessions.")

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

def delete_all_sessions(entry_path):
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
    update_logged(entry_path, text_logged)