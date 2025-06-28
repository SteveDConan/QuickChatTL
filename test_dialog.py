#!/usr/bin/env python3
"""
Test script for DialogSelect class
"""

import tkinter as tk
from minichat.dialogSelect import DialogSelect
from minichat.minichat_cpn import config, window_state

def test_dialog_select():
    """Test the DialogSelect class"""
    root = tk.Tk()
    root.title("Test DialogSelect")
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
            self.lang_map = self.config["language_config"]["language_names"]
    
    test_config = TestConfig()
    
    # Create dialog selector
    dialog_selector = DialogSelect(root, test_config, window_state)
    
    # Test variables
    api_var = tk.StringVar(value="XAI")
    target_lang_var = tk.StringVar(value="Tiếng Việt")
    
    def update_api(val):
        print(f"API updated to: {val}")
        api_var.set(val)
    
    def update_target_lang(val):
        print(f"Language updated to: {val}")
        target_lang_var.set(val)
    
    # Create test buttons
    tk.Button(root, text="Test API Dialog", 
              command=lambda: dialog_selector.open_api_dialog(api_var, update_api, {"api_values": ["XAI", "ChatGPT", "LLM"]})).pack(pady=10)
    
    tk.Button(root, text="Test Language Dialog", 
              command=lambda: dialog_selector.open_lang_dialog(target_lang_var, update_target_lang)).pack(pady=10)
    
    tk.Button(root, text="Quit", command=root.quit).pack(pady=10)
    
    print("Test DialogSelect - Click buttons to test dialogs")
    root.mainloop()

if __name__ == "__main__":
    test_dialog_select() 