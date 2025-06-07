import json
import os
import tkinter as tk
from tkinter import messagebox

CONFIG_FILE = "config.json"

def load_config():
    print("Consolog: Đang tải cấu hình từ config.json")
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Consolog [ERROR]: Lỗi tải config.json: {e}")
            messagebox.showerror("Lỗi", f"Lỗi tải config.json: {e}")
    return {}

def save_config(config):
    print("Consolog: Lưu cấu hình vào config.json")
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"Consolog [ERROR]: Lỗi lưu config.json: {e}")
        messagebox.showerror("Lỗi", f"Lỗi lưu config.json: {e}")