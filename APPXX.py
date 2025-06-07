import os
import tkinter as tk
from tkinter import messagebox
from sam_translate.sam_translate import set_root, set_sam_mini_chat_globals, create_sam_mini_chat
from config import load_config
from settings_dialog import open_settings, center_window

# Load cấu hình
config = load_config()
XAI_API_KEY = config.get("xai_api_key", "")
CHATGPT_API_KEY = config.get("chatgpt_api_key", "")
LLM_API_KEY = config.get("llm_api_key", "")
DEFAULT_TARGET_LANG = config.get("default_target_lang", "vi")

# Đóng ứng dụng
def on_closing():
    print("Consolog: Đóng ứng dụng...")
    root.destroy()

# Khởi tạo giao diện chính
def init_main_ui():
    global root
    root = tk.Tk()
    root.title("Telegram Auto")
    root.geometry("800x600")
    center_window(root, 800, 600)

    print("Consolog: Kiểm tra API Keys")
    if not XAI_API_KEY or not CHATGPT_API_KEY or not LLM_API_KEY:
        messagebox.showerror("Error", "API Key chưa được thiết lập. Vui lòng nhập trong Settings!")
        open_settings(root)
        if not XAI_API_KEY or not CHATGPT_API_KEY or not LLM_API_KEY:
            messagebox.showerror("Error", "API Key là bắt buộc để tiếp tục!")
            return

    try:
        set_root(root)
        set_sam_mini_chat_globals(XAI_API_KEY, CHATGPT_API_KEY, LLM_API_KEY, DEFAULT_TARGET_LANG)
        create_sam_mini_chat()
        print("Consolog: Sam Translate và Sam Mini Chat đã được khởi động tự động khi ứng dụng bắt đầu.")
    except Exception as e:
        print(f"Consolog [ERROR]: Lỗi khi khởi động Sam Translate hoặc Sam Mini Chat: {e}")

    root.mainloop()

# Khởi chạy ứng dụng
print("Consolog: Ứng dụng khởi chạy.")
init_main_ui()