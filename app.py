"""
Mini Chat App
------------
A simple chat interface with translation features
- Multiple translation APIs (XAI, ChatGPT, LLM)
- User-friendly interface
- Telegram integration
"""

import os
import tkinter as tk
from tkinter import messagebox
from minichat.minichat_cpn import initialize_root_window, initialize_chat_config, create_chat_window
from config import load_config
from ttkthemes import ThemedTk
import customtkinter as ctk

class MiniChatApp:
    """Main application class"""
    def __init__(self):
        """Initialize app and load config"""
        self.root = None
        self.config = load_config()
        # Load API keys
        self.xai_api_key = self.config.get("xai_api_key", "")
        self.chatgpt_api_key = self.config.get("chatgpt_api_key", "")
        self.llm_api_key = self.config.get("llm_api_key", "")
        self.default_target_lang = self.config.get("default_target_lang", "vi")

    def validate_api_keys(self) -> bool:
        """Check if all API keys are valid"""
        if not all([self.xai_api_key, self.chatgpt_api_key, self.llm_api_key]):
            messagebox.showerror(
                "Error", 
                "Missing API keys. Please update config.json"
            )
            return False
        return True

    def on_closing(self) -> None:
        """Handle window close event"""
        print("Log: Closing application...")
        if self.root:
            self.root.destroy()

    def init_main_ui(self) -> None:
        """Initialize main UI"""
        print("Log: Checking API keys")
        if not self.validate_api_keys():
            return

        try:
            # Create main window
            self.root = ThemedTk(theme="arc")
            self.root.title("Mini Chat")
            self.root.eval('tk::PlaceWindow . center')
            
            # Initialize components
            initialize_root_window(self.root)
            initialize_chat_config(
                self.xai_api_key,
                self.chatgpt_api_key,
                self.llm_api_key,
                self.default_target_lang
            )
            create_chat_window()
            
            # Setup window close handler
            self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
            print("Log: Mini Chat started")
            
            # Start main loop
            self.root.mainloop()
                
        except Exception as e:
            print(f"Error: Failed to start Mini Chat - {e}")
            if self.root:
                self.root.destroy()
            return

def main() -> None:
    """Application entry point"""
    print("Log: Starting application")
    app = MiniChatApp()
    app.init_main_ui()

if __name__ == "__main__":
    main()