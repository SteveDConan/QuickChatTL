"""
Telegram Auto Translation Tool
-----------------------------
A powerful tool for translating and sending messages via Telegram
- Multiple translation APIs (XAI, ChatGPT, LLM)
- User-friendly interface
- Telegram integration
"""

import os
import tkinter as tk
from tkinter import messagebox
from telegram_translator.app_initializer import initialize_root_window, initialize_chat_configuration, app_config, app_window_state, translation_service
from telegram_translator.chat_interface import create_chat_window
from settings_manager import load_config
from ttkthemes import ThemedTk
import customtkinter as ctk

class TelegramTranslationApp:
    """Main application class for Telegram translation tool"""
    def __init__(self):
        """Initialize app and load configuration"""
        self.root = None
        self.config = load_config()
        # Load API keys
        self.xai_api_key = self.config.get("xai_api_key", "")
        self.chatgpt_api_key = self.config.get("chatgpt_api_key", "")
        self.llm_api_key = self.config.get("llm_api_key", "")

    def validate_api_keys(self) -> bool:
        """Check if all required API keys are valid"""
        if not all([self.xai_api_key, self.chatgpt_api_key, self.llm_api_key]):
            messagebox.showerror(
                "Error", 
                "Missing API keys. Please update config/api_keys.json"
            )
            return False
        return True

    def handle_window_closing(self) -> None:
        """Handle window close event"""
        print("Log: Closing application...")
        if self.root:
            self.root.destroy()

    def initialize_main_interface(self) -> None:
        """Initialize main user interface"""
        print("Log: Checking API keys")
        if not self.validate_api_keys():
            return

        try:
            # Create main window
            self.root = ThemedTk(theme="arc")
            self.root.title("Telegram Translation Tool")
            self.root.eval('tk::PlaceWindow . center')
            
            # Set window to always be on top
            self.root.attributes('-topmost', True)
            self.root.lift()
            self.root.attributes('-topmost', True)  # Keep it on top
            
            # Initialize components
            initialize_root_window(self.root)
            initialize_chat_configuration(
                self.xai_api_key,
                self.chatgpt_api_key,
                self.llm_api_key
            )
            create_chat_window(app_config, app_window_state, translation_service)
            
            # Setup window close handler
            self.root.protocol("WM_DELETE_WINDOW", self.handle_window_closing)
            print("Log: Telegram Translation Tool started")
            
            # Start main loop
            self.root.mainloop()
                
        except Exception as e:
            print(f"Error: Failed to start Telegram Translation Tool - {e}")
            if self.root:
                self.root.destroy()
            return

def main() -> None:
    """Application entry point"""
    print("Log: Starting Telegram Translation Tool")
    app = TelegramTranslationApp()
    app.initialize_main_interface()

if __name__ == "__main__":
    main()