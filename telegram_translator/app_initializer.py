import threading
import time
import tkinter as tk
import customtkinter as ctk
from ttkthemes import ThemedTk
import ctypes
from ctypes import wintypes
from settings_manager import load_config
from typing import Optional, Tuple, Dict, Any
from telegram_translator.helpers import remove_think_tags, fetch_ngrok_url
from telegram_translator.language_selector import LanguageAndApiSelector
from telegram_translator.translation_service import Translator
from telegram_translator.chat_interface import create_chat_window

try:
    import psutil
except ImportError:
    psutil = None

# Set appearance mode and default color theme
ctk.set_appearance_mode("light")  # Modes: "System" (standard), "Dark", "Light"
ctk.set_default_color_theme("blue")  # Themes: "blue" (standard), "green", "dark-blue"

# Windows API setup
user32 = ctypes.windll.user32


class ApplicationConfiguration:
    """Configuration class for application settings"""
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
        self.language_mapping = language_config.get(
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


class ApplicationWindowState:
    """Class to manage application window state and UI components"""
    def __init__(self):
        self.root: Optional[ThemedTk] = None
        self.translation_window: Optional[ThemedTk] = None
        self.message_input_field: Optional[ctk.CTkTextbox] = None
        self.send_button: Optional[ctk.CTkButton] = None
        self.last_valid_telegram_window_handle: Optional[int] = None
        self.is_widget_thread_running: bool = True
        self.z_order_callback: Optional[Any] = None
        self.window_target_language_map: Dict[int, str] = {}


# Global instances
app_config = ApplicationConfiguration()
app_window_state = ApplicationWindowState()
translation_service = Translator()


def initialize_root_window(root_window: ThemedTk) -> None:
    """Initialize the main root window"""
    app_window_state.root = root_window


def initialize_chat_configuration(
    xai_api_key: str, chatgpt_api_key: str, llm_api_key: str
) -> None:
    """Initialize chat configuration with API keys"""
    if xai_api_key and xai_api_key.startswith("xai-"):
        app_config.xai_api_key = xai_api_key
        translation_service.xai_api_key = xai_api_key
    if chatgpt_api_key and chatgpt_api_key.startswith("sk-"):
        app_config.chatgpt_api_key = chatgpt_api_key
        translation_service.chatgpt_api_key = chatgpt_api_key
    if llm_api_key and llm_api_key.startswith("llm-"):
        app_config.llm_api_key = llm_api_key
        translation_service.llm_api_key = llm_api_key

    # Get language settings from config
    language_config = app_config.config.get("language_config", {})
    app_config.target_lang_selection = language_config.get("target_lang", "en")
    app_config.selected_api = language_config.get("selected_api", "XAI")
    
    # Update translator firebase_url if available
    if app_config.firebase_url:
        translation_service.firebase_url = app_config.firebase_url
    
    # Update translator config if needed
    translation_service.config = app_config.config
