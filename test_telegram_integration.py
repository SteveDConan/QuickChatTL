#!/usr/bin/env python3
"""
Test script for LanguageAndApiSelector class
"""

import tkinter as tk
from tkinter import messagebox
import threading
import time
from telegram_translator.language_selector import LanguageAndApiSelector
from telegram_translator.app_initializer import app_config, app_window_state

def test_language_and_api_selector():
    """Test the LanguageAndApiSelector class"""
    root = tk.Tk()
    root.title("Test LanguageAndApiSelector")
    root.geometry("300x200")
    
    # Create a test config-like object
    class TestConfig:
        def __init__(self):
            self.config = {
                "language_config": {
                    "available_languages": ["en", "vi", "ja", "zh"],
                    "language_names": {
                        "en": "Tiếng Anh",
                        "vi": "Tiếng Việt", 
                        "ja": "Tiếng Nhật",
                        "zh": "Tiếng Trung"
                    }
                }
            }
            self.language_mapping = self.config["language_config"]["language_names"]
    
    test_config = TestConfig()
    
    # Create dialog selector
    dialog_selector = LanguageAndApiSelector(root, test_config, app_window_state)
    
    # Test variables
    api_variable = tk.StringVar(value="XAI")
    target_language_variable = tk.StringVar(value="Tiếng Việt")
    
    def update_api_selection(api_name):
        print(f"API updated to: {api_name}")
        api_variable.set(api_name)
    
    def update_target_language(language_name):
        print(f"Language updated to: {language_name}")
        target_language_variable.set(language_name)
    
    # Create test buttons
    tk.Button(root, text="Test API Dialog", 
              command=lambda: dialog_selector.show_api_selection_dialog(api_variable, update_api_selection, {"api_values": ["XAI", "ChatGPT", "LLM"]})).pack(pady=10)
    
    tk.Button(root, text="Test Language Dialog", 
              command=lambda: dialog_selector.show_language_selection_dialog(target_language_variable, update_target_language)).pack(pady=10)
    
    tk.Button(root, text="Quit", command=root.quit).pack(pady=10)
    
    print("Test LanguageAndApiSelector - Click buttons to test dialogs")
    root.mainloop()

if __name__ == "__main__":
    test_language_and_api_selector() 