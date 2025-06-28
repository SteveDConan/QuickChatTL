from typing import Optional
import requests

def remove_think_tags(text: str) -> str:
    return text.replace("[think]", "").replace("[/think]", "")

def fetch_ngrok_url(firebase_url: Optional[str] = None) -> Optional[str]:
    if not firebase_url:
        return None
            
    try:
        response = requests.get(firebase_url, timeout=5)
        if response.status_code == 200:
            url = response.json()
            if url:
                return url
            else:
                raise ValueError("Ngrok URL is empty")
        else:
            raise Exception(f"Failed to fetch ngrok URL: {response.status_code}")
    except Exception:
        return None
