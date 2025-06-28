import tkinter as tk
import customtkinter as ctk
from typing import Callable, Any, Optional
import json
from settings_manager import save_config


class LanguageAndApiSelector:
    """Class containing dialog selection functions for API and language selection"""
    
    def __init__(self, parent_window: tk.Tk, config: Any, window_state: Any):
        self.parent_window = parent_window
        self.config = config
        self.window_state = window_state
    
    def prompt_for_firebase_url(self) -> Optional[str]:
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

        def save_firebase_url() -> None:
            firebase_url = url_entry.get().strip()
            if not firebase_url:
                tk.messagebox.showerror(
                    dialog_config.get("error_title", "Lỗi"),
                    dialog_config.get("error_empty", "URL không được để trống!"),
                )
                return

            try:
                self.config.firebase_url = firebase_url
                self.config.config["firebase_url"] = firebase_url
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
            dialog, text=dialog_config.get("button_text", "OK"), command=save_firebase_url
        ).pack(pady=dialog_config.get("button_pady", 10))
        dialog.wait_window()
        return self.config.firebase_url
    
    def show_api_selection_dialog(self, api_variable: tk.StringVar, update_api_callback: Callable[[str], None], styles: dict) -> None:
        """Open API selection dialog"""
        available_apis = styles.get("api_values", ["XAI", "ChatGPT", "LLM"])
        dialog = tk.Toplevel(self.parent_window)
        dialog.title("Chọn API")
        dialog.attributes("-topmost", True)
        dialog.grab_set()
        dialog.update_idletasks()
        
        dialog_width, dialog_height = 250, 50 + 40 * len(available_apis)
        screen_width = dialog.winfo_screenwidth()
        screen_height = dialog.winfo_screenheight()
        dialog_x = (screen_width // 2) - (dialog_width // 2)
        dialog_y = (screen_height // 2) - (dialog_height // 2)
        dialog.geometry(f"{dialog_width}x{dialog_height}+{dialog_x}+{dialog_y}")
        
        current_api = api_variable.get()
        for api_name in available_apis:
            is_currently_selected = api_name == current_api
            api_button = ctk.CTkButton(
                dialog,
                text=api_name,
                width=200,
                fg_color="#2E7D32" if is_currently_selected else "#E8F5E9",
                text_color="white" if is_currently_selected else "#2E7D32",
                hover_color="#388E3C" if is_currently_selected else "#C8E6C9",
                border_color="#1B5E20" if is_currently_selected else "#C8E6C9",
                border_width=2 if is_currently_selected else 1,
                font=("Segoe UI", 13, "bold" if is_currently_selected else "normal"),
                command=lambda a=api_name: self.handle_api_selection(a, dialog, api_variable, update_api_callback),
            )
            api_button.pack(pady=5, padx=10, fill="x")
    
    def handle_api_selection(self, selected_api: str, dialog: tk.Toplevel, api_variable: tk.StringVar, update_api_callback: Callable[[str], None]) -> None:
        """Handle API selection"""
        api_variable.set(selected_api)
        update_api_callback(selected_api)
        dialog.destroy()
    
    def show_language_selection_dialog(self, target_language_variable: tk.StringVar, update_target_language_callback: Callable[[str], None]) -> None:
        """Open language selection dialog"""
        language_config = self.config.config.get("language_config", {})
        available_languages = language_config.get(
            "available_languages", list(self.config.language_mapping.keys())
        )
        language_names = language_config.get("language_names", self.config.language_mapping)
        
        # Create dialog
        dialog = tk.Toplevel(self.parent_window)
        dialog.title("Chọn ngôn ngữ")
        dialog.attributes("-topmost", True)
        dialog.grab_set()
        
        # Calculate center position
        dialog.update_idletasks()
        dialog_width, dialog_height = 260, min(600, 50 + 40 * len(available_languages))
        screen_width = dialog.winfo_screenwidth()
        screen_height = dialog.winfo_screenheight()
        dialog_x = (screen_width // 2) - (dialog_width // 2)
        dialog_y = (screen_height // 2) - (dialog_height // 2)
        dialog.geometry(f"{dialog_width}x{dialog_height}+{dialog_x}+{dialog_y}")
        
        # Display language list
        current_language = target_language_variable.get()
        for language_code in available_languages:
            language_label = language_names.get(language_code, language_code)
            is_currently_selected = language_label == current_language
            language_button = ctk.CTkButton(
                dialog,
                text=language_label,
                width=280,
                fg_color="#2196F3" if is_currently_selected else "#E3F2FD",
                text_color="white" if is_currently_selected else "#1976D2",
                hover_color="#1976D2" if is_currently_selected else "#BBDEFB",
                border_color="#1976D2" if is_currently_selected else "#90CAF9",
                border_width=2 if is_currently_selected else 1,
                font=("Segoe UI", 13, "bold" if is_currently_selected else "normal"),
                command=lambda l=language_label: self.handle_language_selection(l, dialog, target_language_variable, update_target_language_callback),
            )
            language_button.pack(pady=4, padx=10, fill="x")
    
    def handle_language_selection(self, selected_language: str, dialog: tk.Toplevel, target_language_variable: tk.StringVar, update_target_language_callback: Callable[[str], None]) -> None:
        """Handle language selection"""
        target_language_variable.set(selected_language)
        update_target_language_callback(selected_language)
        dialog.destroy() 