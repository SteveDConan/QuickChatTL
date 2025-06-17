import os
import tkinter as tk
from tkinter import messagebox
from minichat.minichat_cpn import initialize_root_window, initialize_chat_config, create_chat_window
from config import load_config
from ttkthemes import ThemedTk
import customtkinter as ctk

class MiniChatApp:
    def __init__(self):
        self.root = None
        self.config = load_config()
        self.xai_api_key = self.config.get("xai_api_key", "")
        self.chatgpt_api_key = self.config.get("chatgpt_api_key", "")
        self.llm_api_key = self.config.get("llm_api_key", "")
        self.default_target_lang = self.config.get("default_target_lang", "vi")

    def validate_api_keys(self):
        if not all([self.xai_api_key, self.chatgpt_api_key, self.llm_api_key]):
            messagebox.showerror("Error", "API Key chưa được thiết lập. Vui lòng cập nhật trong file config.json!")
            return False
        return True

    def on_closing(self):
        print("Consolog: Đóng ứng dụng...")
        if self.root:
            self.root.destroy()

    def init_main_ui(self):
        print("Consolog: Kiểm tra API Keys")
        if not self.validate_api_keys():
            return

        try:
            # Tạo cửa sổ chính với theme
            self.root = ThemedTk(theme="arc")
            self.root.title("Sam Mini Chat")
            self.root.eval('tk::PlaceWindow . center')
            
            # Thiết lập root cho Sam Mini Chat
            initialize_root_window(self.root)
            
            # Thiết lập các biến toàn cục
            initialize_chat_config(
                self.xai_api_key,
                self.chatgpt_api_key,
                self.llm_api_key,
                self.default_target_lang
            )
            
            # Tạo widget Sam Mini Chat
            create_chat_window()
            
            # Thêm xử lý đóng cửa sổ
            self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
            print("Consolog: Sam Mini Chat đã được khởi động làm cửa sổ chính.")
            
            # Chạy vòng lặp chính
            self.root.mainloop()
                
        except Exception as e:
            print(f"Consolog [ERROR]: Lỗi khi khởi động Sam Mini Chat: {e}")
            if self.root:
                self.root.destroy()
            return

def main():
    print("Consolog: Ứng dụng khởi chạy.")
    app = MiniChatApp()
    app.init_main_ui()

if __name__ == "__main__":
    main()