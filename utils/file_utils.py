import os
import shutil
from tkinter import messagebox
from config.language import lang

try:
    from send2trash import send2trash
except ImportError:
    send2trash = None

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