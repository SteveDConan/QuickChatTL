import threading
import time
import tkinter as tk
import customtkinter as ctk
from ttkthemes import ThemedTk
import ctypes
from ctypes import wintypes
from config import load_config
from typing import Optional, Tuple, Dict, Any
from minichat.utils import remove_think_tags, fetch_ngrok_url
from minichat.dialogSelect import DialogSelect
from minichat.translator import Translator
from minichat.ui import create_chat_window

try:
    import psutil
except ImportError:
    psutil = None

# Set appearance mode and default color theme
ctk.set_appearance_mode("light")  # Modes: "System" (standard), "Dark", "Light"
ctk.set_default_color_theme("blue")  # Themes: "blue" (standard), "green", "dark-blue"

# Windows API setup
user32 = ctypes.windll.user32


class Config:
    def __init__(self):
        self.config = load_config()
        self.xai_api_key = self.config.get("xai_api_key", "")
        self.chatgpt_api_key = self.config.get("chatgpt_api_key", "")
        self.llm_api_key = self.config.get("llm_api_key", "")
        self.firebase_url = self.config.get("firebase_url", "")

        widget_config = self.config.get("widget_config", {})
        self.widget_height = widget_config.get("height", 80)
        self.widget_y_offset = widget_config.get("y_offset", 1)

        language_config = self.config.get("language_config", {})
        self.lang_map = language_config.get(
            "language_names", {"en": "Tiếng Anh", "vi": "Tiếng Việt"}
        )

        # Get Windows API constants from config
        windows_api_config = self.config.get("windows_api", {}).get("constants", {})
        self.HWND_TOPMOST = windows_api_config.get("HWND_TOPMOST", -1)
        self.SWP_NOMOVE = windows_api_config.get("SWP_NOMOVE", 0x0002)
        self.SWP_NOSIZE = windows_api_config.get("SWP_NOSIZE", 0x0001)
        self.SWP_NOACTIVATE = windows_api_config.get("SWP_NOACTIVATE", 0x0010)
        self.EVENT_OBJECT_REORDER = windows_api_config.get(
            "EVENT_OBJECT_REORDER", 0x8004
        )
        self.EVENT_SYSTEM_FOREGROUND = windows_api_config.get(
            "EVENT_SYSTEM_FOREGROUND", 0x0003
        )
        self.WINEVENT_OUTOFCONTEXT = windows_api_config.get(
            "WINEVENT_OUTOFCONTEXT", 0x0000
        )
        self.WINEVENT_SKIPOWNTHREAD = windows_api_config.get(
            "WINEVENT_SKIPOWNTHREAD", 0x0001
        )
        self.WINEVENT_SKIPOWNPROCESS = windows_api_config.get(
            "WINEVENT_SKIPOWNPROCESS", 0x0002
        )


class WindowState:
    def __init__(self):
        self.root: Optional[ThemedTk] = None
        self.sam_mini_chat_win: Optional[ThemedTk] = None
        self.sam_mini_chat_entry: Optional[ctk.CTkTextbox] = None
        self.sam_mini_chat_btn_send: Optional[ctk.CTkButton] = None
        self.last_valid_telegram_hwnd: Optional[int] = None
        self.widget_sam_mini_chat_thread_running: bool = True
        self.z_order_callback: Optional[Any] = None
        self.hwnd_target_lang: Dict[int, str] = {}


# Global instances
config = Config()
window_state = WindowState()
translator = Translator()


def initialize_root_window(r: ThemedTk) -> None:
    window_state.root = r


def initialize_chat_config(
    xai_api_key: str, chatgpt_api_key: str, llm_api_key: str
) -> None:
    if xai_api_key and xai_api_key.startswith("xai-"):
        config.xai_api_key = xai_api_key
        translator.xai_api_key = xai_api_key
    if chatgpt_api_key and chatgpt_api_key.startswith("sk-"):
        config.chatgpt_api_key = chatgpt_api_key
        translator.chatgpt_api_key = chatgpt_api_key
    if llm_api_key and llm_api_key.startswith("llm-"):
        config.llm_api_key = llm_api_key
        translator.llm_api_key = llm_api_key

    # Get language settings from config
    language_config = config.config.get("language_config", {})
    config.target_lang_selection = language_config.get("target_lang", "en")
    config.selected_api = language_config.get("selected_api", "XAI")
    
    # Update translator firebase_url if available
    if config.firebase_url:
        translator.firebase_url = config.firebase_url
    
    # Update translator config if needed
    translator.config = config.config
