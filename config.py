import json
import os
from typing import Dict, Any

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
        return {}