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
    ui_components_file = os.path.join(CONFIG_DIR, "ui_components.json")
    if os.path.exists(ui_components_file):
        try:
            with open(ui_components_file, "r", encoding="utf-8") as f:
                config["widget_config"] = json.load(f)
        except Exception as e:
            print(f"Error loading ui_components.json: {e}")
    
    # Load language config
    supported_languages_file = os.path.join(CONFIG_DIR, "supported_languages.json")
    if os.path.exists(supported_languages_file):
        try:
            with open(supported_languages_file, "r", encoding="utf-8") as f:
                config["language_config"] = json.load(f)
        except Exception as e:
            print(f"Error loading supported_languages.json: {e}")
    
    # Load translation config
    translation_settings_file = os.path.join(CONFIG_DIR, "translation_settings.json")
    if os.path.exists(translation_settings_file):
        try:
            with open(translation_settings_file, "r", encoding="utf-8") as f:
                config["translation_config"] = json.load(f)
        except Exception as e:
            print(f"Error loading translation_settings.json: {e}")
    
    # Load UI config
    interface_settings_file = os.path.join(CONFIG_DIR, "interface_settings.json")
    if os.path.exists(interface_settings_file):
        try:
            with open(interface_settings_file, "r", encoding="utf-8") as f:
                config["ui_config"] = json.load(f)
        except Exception as e:
            print(f"Error loading interface_settings.json: {e}")
    
    # Load Windows API config
    telegram_window_config_file = os.path.join(CONFIG_DIR, "telegram_window_config.json")
    if os.path.exists(telegram_window_config_file):
        try:
            with open(telegram_window_config_file, "r", encoding="utf-8") as f:
                config["windows_api"] = json.load(f)
        except Exception as e:
            print(f"Error loading telegram_window_config.json: {e}")
    
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
            with open(os.path.join(CONFIG_DIR, "ui_components.json"), "w", encoding="utf-8") as f:
                json.dump(config["widget_config"], f, indent=4, ensure_ascii=False)
        
        # Save language config
        if "language_config" in config:
            with open(os.path.join(CONFIG_DIR, "supported_languages.json"), "w", encoding="utf-8") as f:
                json.dump(config["language_config"], f, indent=4, ensure_ascii=False)
        
        # Save translation config
        if "translation_config" in config:
            with open(os.path.join(CONFIG_DIR, "translation_settings.json"), "w", encoding="utf-8") as f:
                json.dump(config["translation_config"], f, indent=4, ensure_ascii=False)
        
        # Save UI config
        if "ui_config" in config:
            with open(os.path.join(CONFIG_DIR, "interface_settings.json"), "w", encoding="utf-8") as f:
                json.dump(config["ui_config"], f, indent=4, ensure_ascii=False)
        
        # Save Windows API config
        if "windows_api" in config:
            with open(os.path.join(CONFIG_DIR, "telegram_window_config.json"), "w", encoding="utf-8") as f:
                json.dump(config["windows_api"], f, indent=4, ensure_ascii=False)
        
        return True
    except Exception as e:
        print(f"Error saving config: {e}")
        return False