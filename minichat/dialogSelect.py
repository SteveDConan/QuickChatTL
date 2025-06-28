import tkinter as tk
import customtkinter as ctk
from typing import Callable, Any, Optional
import json
from config import save_config


class DialogSelect:
    """Class containing dialog selection functions for API and language selection"""
    
    def __init__(self, parent_window: tk.Tk, config: Any, window_state: Any):
        self.parent_window = parent_window
        self.config = config
        self.window_state = window_state
    
    def request_firebase_url(self) -> Optional[str]:
        """Prompt user for Firebase URL"""
        if self.config.firebase_url:
            return self.config.firebase_url

        dialog_config = self.config.config.get("dialog_config", {}).get("firebase_url", {})
        dialog = tk.Toplevel(self.parent_window)
        dialog.title(dialog_config.get("title", "Nhập Firebase URL"))
        dialog.geometry(dialog_config.get("geometry", "400x150"))
        dialog.attributes("-topmost", True)
        dialog.grab_set()

        tk.Label(
            dialog, text=dialog_config.get("label_text", "Vui lòng nhập Firebase URL:")
        ).pack(pady=dialog_config.get("label_pady", 10))
        url_entry = tk.Entry(dialog, width=dialog_config.get("entry_width", 50))
        url_entry.pack(pady=dialog_config.get("entry_pady", 5))

        def save_url() -> None:
            url = url_entry.get().strip()
            if not url:
                tk.messagebox.showerror(
                    dialog_config.get("error_title", "Lỗi"),
                    dialog_config.get("error_empty", "URL không được để trống!"),
                )
                return

            try:
                self.config.firebase_url = url
                self.config.config["firebase_url"] = url
                if save_config(self.config.config):
                    dialog.destroy()
                else:
                    tk.messagebox.showerror(
                        dialog_config.get("error_title", "Lỗi"),
                        dialog_config.get("error_save", "Không thể lưu URL"),
                    )
            except Exception as e:
                tk.messagebox.showerror(
                    dialog_config.get("error_title", "Lỗi"),
                    dialog_config.get("error_save", "Không thể lưu URL: {}").format(e),
                )

        tk.Button(
            dialog, text=dialog_config.get("button_text", "OK"), command=save_url
        ).pack(pady=dialog_config.get("button_pady", 10))
        dialog.wait_window()
        return self.config.firebase_url
    
    def show_api_selection_dialog(self, api_var: tk.StringVar, update_api_callback: Callable[[str], None], styles: dict) -> None:
        """Open API selection dialog"""
        apis = styles.get("api_values", ["XAI", "ChatGPT", "LLM"])
        dialog = tk.Toplevel(self.parent_window)
        dialog.title("Chọn API")
        dialog.attributes("-topmost", True)
        dialog.grab_set()
        dialog.update_idletasks()
        
        w, h = 250, 50 + 40 * len(apis)
        ws = dialog.winfo_screenwidth()
        hs = dialog.winfo_screenheight()
        x = (ws // 2) - (w // 2)
        y = (hs // 2) - (h // 2)
        dialog.geometry(f"{w}x{h}+{x}+{y}")
        
        current_api = api_var.get()
        for api in apis:
            is_selected = api == current_api
            btn = ctk.CTkButton(
                dialog,
                text=api,
                width=200,
                fg_color="#2E7D32" if is_selected else "#E8F5E9",
                text_color="white" if is_selected else "#2E7D32",
                hover_color="#388E3C" if is_selected else "#C8E6C9",
                border_color="#1B5E20" if is_selected else "#C8E6C9",
                border_width=2 if is_selected else 1,
                font=("Segoe UI", 13, "bold" if is_selected else "normal"),
                command=lambda a=api: self.handle_api_selection(a, dialog, api_var, update_api_callback),
            )
            btn.pack(pady=5, padx=10, fill="x")
    
    def handle_api_selection(self, api: str, dialog: tk.Toplevel, api_var: tk.StringVar, update_api_callback: Callable[[str], None]) -> None:
        """Handle API selection"""
        api_var.set(api)
        update_api_callback(api)
        dialog.destroy()
    
    def show_language_selection_dialog(self, target_lang_var: tk.StringVar, update_target_lang_callback: Callable[[str], None]) -> None:
        """Open language selection dialog"""
        lang_cfg = self.config.config.get("language_config", {})
        available_langs = lang_cfg.get(
            "available_languages", list(self.config.lang_map.keys())
        )
        lang_names = lang_cfg.get("language_names", self.config.lang_map)
        
        # Tạo dialog
        dialog = tk.Toplevel(self.parent_window)
        dialog.title("Chọn ngôn ngữ")
        dialog.attributes("-topmost", True)
        dialog.grab_set()
        
        # Tính toán vị trí giữa màn hình
        dialog.update_idletasks()
        w, h = 260, min(600, 50 + 40 * len(available_langs))
        ws = dialog.winfo_screenwidth()
        hs = dialog.winfo_screenheight()
        x = (ws // 2) - (w // 2)
        y = (hs // 2) - (h // 2)
        dialog.geometry(f"{w}x{h}+{x}+{y}")
        
        # Hiển thị danh sách ngôn ngữ
        current_lang = target_lang_var.get()
        for lang_code in available_langs:
            lang_label = lang_names.get(lang_code, lang_code)
            is_selected = lang_label == current_lang
            btn = ctk.CTkButton(
                dialog,
                text=lang_label,
                width=280,
                fg_color="#2196F3" if is_selected else "#E3F2FD",
                text_color="white" if is_selected else "#1976D2",
                hover_color="#1976D2" if is_selected else "#BBDEFB",
                border_color="#1976D2" if is_selected else "#90CAF9",
                border_width=2 if is_selected else 1,
                font=("Segoe UI", 13, "bold" if is_selected else "normal"),
                command=lambda l=lang_label: self.handle_language_selection(l, dialog, target_lang_var, update_target_lang_callback),
            )
            btn.pack(pady=4, padx=10, fill="x")
    
    def handle_language_selection(self, lang: str, dialog: tk.Toplevel, target_lang_var: tk.StringVar, update_target_lang_callback: Callable[[str], None]) -> None:
        """Handle language selection"""
        target_lang_var.set(lang)
        update_target_lang_callback(lang)
        dialog.destroy() 