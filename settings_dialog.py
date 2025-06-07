import tkinter as tk
from tkinter import messagebox
from config import load_config, save_config

def center_window(win, width, height):
    win.update_idletasks()
    screen_width = win.winfo_screenwidth()
    screen_height = win.winfo_screenheight()
    x = (screen_width - width) // 2
    y = (screen_height - height) // 2
    win.geometry(f"{width}x{height}+{x}+{y}")

def open_settings(root, callback=None):
    if root is None:
        print("Consolog [ERROR]: Root window is None")
        return
        
    config = load_config()
    XAI_API_KEY = config.get("xai_api_key", "")
    CHATGPT_API_KEY = config.get("chatgpt_api_key", "")
    LLM_API_KEY = config.get("llm_api_key", "")
    arrange_width = config.get("arrange_width", 500)
    arrange_height = config.get("arrange_height", 504)

    def log_message(msg):
        print(f"[LOG] {msg}")
        try:
            text_log = root.nametowidget('text_log')
            text_log.insert(tk.END, msg + "\n")
            text_log.see(tk.END)
        except Exception:
            pass

    popup = tk.Toplevel(root)
    popup.title("Setting - Tùy chỉnh sắp xếp & API Keys")
    center_window(popup, 550, 450)
    popup.attributes("-topmost", True)  # Đảm bảo cửa sổ luôn hiển thị trên cùng

    lbl_info = tk.Label(popup, text="Nhập kích thước cửa sổ sắp xếp:\nx = (số cột) × Custom Width, y = (số hàng) × Custom Height", wraplength=530)
    lbl_info.pack(pady=10)

    frame_entries = tk.Frame(popup)
    frame_entries.pack(pady=5)
    tk.Label(frame_entries, text="Custom Width:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
    entry_width = tk.Entry(frame_entries, width=10)
    entry_width.insert(0, str(arrange_width))
    entry_width.grid(row=0, column=1, padx=5, pady=5)
    tk.Label(frame_entries, text="Custom Height:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
    entry_height = tk.Entry(frame_entries, width=10)
    entry_height.insert(0, str(arrange_height))
    entry_height.grid(row=1, column=1, padx=5, pady=5)

    tk.Label(popup, text="xAI API Key:").pack(pady=5)
    xai_key_entry = tk.Entry(popup, width=50)
    xai_key_entry.insert(0, XAI_API_KEY)
    xai_key_entry.pack(pady=5)

    tk.Label(popup, text="ChatGPT API Key:").pack(pady=5)
    chatgpt_key_entry = tk.Entry(popup, width=50)
    chatgpt_key_entry.insert(0, CHATGPT_API_KEY)
    chatgpt_key_entry.pack(pady=5)

    tk.Label(popup, text="LLM API Key:").pack(pady=5)
    llm_key_entry = tk.Entry(popup, width=50)
    llm_key_entry.insert(0, LLM_API_KEY)
    llm_key_entry.pack(pady=5)

    def validate_api_keys():
        xai_key = xai_key_entry.get().strip()
        chatgpt_key = chatgpt_key_entry.get().strip()
        llm_key = llm_key_entry.get().strip()

        if xai_key and not xai_key.startswith("xai-"):
            messagebox.showerror("Lỗi", "XAI API Key phải bắt đầu bằng 'xai-'")
            return False
        
        if chatgpt_key and not chatgpt_key.startswith("sk-"):
            messagebox.showerror("Lỗi", "ChatGPT API Key phải bắt đầu bằng 'sk-'")
            return False
        
        if llm_key and not llm_key.startswith("llm-"):
            messagebox.showerror("Lỗi", "LLM API Key phải bắt đầu bằng 'llm-'")
            return False

        return True

    def save_settings():
        try:
            if not validate_api_keys():
                return

            arrange_width = int(entry_width.get())
            arrange_height = int(entry_height.get())
            config["arrange_width"] = arrange_width
            config["arrange_height"] = arrange_height

            XAI_API_KEY = xai_key_entry.get().strip()
            CHATGPT_API_KEY = chatgpt_key_entry.get().strip()
            LLM_API_KEY = llm_key_entry.get().strip()

            if not LLM_API_KEY:
                log_message("LLM API Key không được để trống!")
                return

            config["xai_api_key"] = XAI_API_KEY
            config["chatgpt_api_key"] = CHATGPT_API_KEY
            config["llm_api_key"] = LLM_API_KEY
            save_config(config)
            print("Consolog: Đã lưu cấu hình Setting")
            log_message("Đã lưu cấu hình!")
            
            if callback:
                callback(config)
                
            popup.destroy()
        except Exception as e:
            log_message(f"Giá trị không hợp lệ: {e}")
            print(f"Consolog [ERROR]: Lỗi lưu cấu hình Setting: {e}")

    btn_save = tk.Button(popup, text="Save", command=save_settings)
    btn_save.pack(pady=10)
    popup.transient(root)
    popup.grab_set()
    root.wait_window(popup) 