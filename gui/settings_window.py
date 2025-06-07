import tkinter as tk
from tkinter import messagebox
from config.config import load_xai_api_key, save_xai_api_key
from utils.window_utils import center_window

arrange_width = 500
arrange_height = 504
DEFAULT_TARGET_LANG = "vi"

def open_settings(root):  # Thêm tham số root
    popup = tk.Toplevel(root)
    popup.title("Setting - Tùy chỉnh sắp xếp & xAI")
    center_window(popup, 400, 350)

    lbl_info = tk.Label(popup, text="Nhập kích thước cửa sổ sắp xếp:\nx = (số cột) × Custom Width, y = (số hàng) × Custom Height", wraplength=380)
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
    xai_key_entry.insert(0, load_xai_api_key())
    xai_key_entry.pack(pady=5)

    tk.Label(popup, text="Default Translation Language (Target):").pack(pady=5)
    translation_lang_var = tk.StringVar(value=DEFAULT_TARGET_LANG)
    translation_lang_menu = tk.OptionMenu(popup, translation_lang_var, "vi", "en", "zh")
    translation_lang_menu.pack(pady=5)

    def save_settings():
        global arrange_width, arrange_height, DEFAULT_TARGET_LANG
        try:
            w = int(entry_width.get())
            h = int(entry_height.get())
            arrange_width = w
            arrange_height = h

            save_xai_api_key(xai_key_entry.get().strip())

            DEFAULT_TARGET_LANG = translation_lang_var.get()

            messagebox.showinfo("Setting", "Đã lưu cấu hình sắp xếp, xAI API Key và ngôn ngữ dịch mặc định!")
            popup.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Giá trị không hợp lệ: {e}")

    btn_save = tk.Button(popup, text="Save", command=save_settings)
    btn_save.pack(pady=10)

    popup.transient(root)
    popup.grab_set()
    root.wait_window(popup)