import json
import os
from typing import Dict, Any

CONFIG_DIR = "config"

def load_config() -> Dict[str, Any]:
    """Load configuration from multiple config files in config directory
    
    Returns:
        Dict[str, Any]: Combined configuration dictionary
    """
    print("Loading config...")
    
    if not os.path.exists(CONFIG_DIR):
        print("Config directory not found")
        return {}
    
    config = {}
    
    # Load API keys
    api_keys_file = os.path.join(CONFIG_DIR, "api_keys.json")
    if os.path.exists(api_keys_file):
        try:
            with open(api_keys_file, "r", encoding="utf-8") as f:
                config.update(json.load(f))
        except Exception as e:
            print(f"Error loading api_keys.json: {e}")
    
    # Load widget config
    widget_file = os.path.join(CONFIG_DIR, "widget.json")
    if os.path.exists(widget_file):
        try:
            with open(widget_file, "r", encoding="utf-8") as f:
                config["widget_config"] = json.load(f)
        except Exception as e:
            print(f"Error loading widget.json: {e}")
    
    # Load language config
    language_file = os.path.join(CONFIG_DIR, "language.json")
    if os.path.exists(language_file):
        try:
            with open(language_file, "r", encoding="utf-8") as f:
                config["language_config"] = json.load(f)
        except Exception as e:
            print(f"Error loading language.json: {e}")
    
    # Load translation config
    translation_file = os.path.join(CONFIG_DIR, "translation.json")
    if os.path.exists(translation_file):
        try:
            with open(translation_file, "r", encoding="utf-8") as f:
                config["translation_config"] = json.load(f)
        except Exception as e:
            print(f"Error loading translation.json: {e}")
    
    # Load UI config
    ui_file = os.path.join(CONFIG_DIR, "ui.json")
    if os.path.exists(ui_file):
        try:
            with open(ui_file, "r", encoding="utf-8") as f:
                config["ui_config"] = json.load(f)
        except Exception as e:
            print(f"Error loading ui.json: {e}")
    
    # Load Windows API config
    windows_api_file = os.path.join(CONFIG_DIR, "windows_api.json")
    if os.path.exists(windows_api_file):
        try:
            with open(windows_api_file, "r", encoding="utf-8") as f:
                config["windows_api"] = json.load(f)
        except Exception as e:
            print(f"Error loading windows_api.json: {e}")
    
    return config

def save_config(config: Dict[str, Any]) -> bool:
    """Save configuration to multiple config files
    
    Args:
        config: Configuration dictionary to save
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        if not os.path.exists(CONFIG_DIR):
            os.makedirs(CONFIG_DIR)
        
        # Save API keys
        api_keys = {
            "xai_api_key": config.get("xai_api_key", ""),
            "chatgpt_api_key": config.get("chatgpt_api_key", ""),
            "llm_api_key": config.get("llm_api_key", "")
        }
        with open(os.path.join(CONFIG_DIR, "api_keys.json"), "w", encoding="utf-8") as f:
            json.dump(api_keys, f, indent=4, ensure_ascii=False)
        
        # Save widget config
        if "widget_config" in config:
            with open(os.path.join(CONFIG_DIR, "widget.json"), "w", encoding="utf-8") as f:
                json.dump(config["widget_config"], f, indent=4, ensure_ascii=False)
        
        # Save language config
        if "language_config" in config:
            with open(os.path.join(CONFIG_DIR, "language.json"), "w", encoding="utf-8") as f:
                json.dump(config["language_config"], f, indent=4, ensure_ascii=False)
        
        # Save translation config
        if "translation_config" in config:
            with open(os.path.join(CONFIG_DIR, "translation.json"), "w", encoding="utf-8") as f:
                json.dump(config["translation_config"], f, indent=4, ensure_ascii=False)
        
        # Save UI config
        if "ui_config" in config:
            with open(os.path.join(CONFIG_DIR, "ui.json"), "w", encoding="utf-8") as f:
                json.dump(config["ui_config"], f, indent=4, ensure_ascii=False)
        
        # Save Windows API config
        if "windows_api" in config:
            with open(os.path.join(CONFIG_DIR, "windows_api.json"), "w", encoding="utf-8") as f:
                json.dump(config["windows_api"], f, indent=4, ensure_ascii=False)
        
        return True
    except Exception as e:
        print(f"Error saving config: {e}")
        return False