import json
import os
from typing import Dict, Any
import tkinter as tk
from tkinter import messagebox

CONFIG_FILE = "config.json"

def load_config() -> Dict[str, Any]:
    """Load configuration from config.json file
    
    Returns:
        Dict[str, Any]: Configuration dictionary
    """
    print("Loading config...")
    if not os.path.exists(CONFIG_FILE):
        print("Config file not found")
        return {}
        
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading config: {e}")
        messagebox.showerror("Error", f"Failed to load config: {e}")
        return {}

def save_config(config: Dict[str, Any]) -> None:
    """Save configuration to config.json file
    
    Args:
        config (Dict[str, Any]): Configuration to save
    """
    print("Saving config...")
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"Error saving config: {e}")
        messagebox.showerror("Error", f"Failed to save config: {e}")