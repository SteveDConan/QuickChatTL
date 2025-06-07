import os
import sys
import requests
import json
import threading
import time
import tkinter as tk
from tkinter import messagebox
import ctypes
from ctypes import wintypes
import re
from config import load_config
from typing import Optional, Tuple, Dict, Any

try:
    import psutil
except ImportError:
    psutil = None

# Windows API Constants
HWND_TOPMOST = -1
HWND_NOTOPMOST = -2
SWP_NOMOVE = 0x0002
SWP_NOSIZE = 0x0001
SWP_NOACTIVATE = 0x0010
EVENT_OBJECT_REORDER = 0x8004
EVENT_SYSTEM_FOREGROUND = 0x0003
WINEVENT_OUTOFCONTEXT = 0x0000
WINEVENT_SKIPOWNTHREAD = 0x0001
WINEVENT_SKIPOWNPROCESS = 0x0002

# Windows API setup
user32 = ctypes.windll.user32

class Config:
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
        self.all_lang_options = language_config.get("available_languages", ["en", "vi"])
        self.lang_map = language_config.get("language_names", {"en": "Tiếng Anh", "vi": "Tiếng Việt"})
        self.default_target_lang = "en"
        self.my_lang_selection = self.config.get("MY_LANG_SELECTION", "vi")
        self.target_lang_selection = self.config.get("TARGET_LANG_SELECTION", self.default_target_lang)
        self.selected_api = self.config.get("SELECTED_API", "XAI")

class WindowState:
    def __init__(self):
        self.root: Optional[tk.Tk] = None
        self.sam_mini_chat_win: Optional[tk.Tk] = None
        self.sam_mini_chat_entry: Optional[tk.Text] = None
        self.sam_mini_chat_btn_send: Optional[tk.Button] = None
        self.last_valid_telegram_hwnd: Optional[int] = None
        self.widget_sam_mini_chat_thread_running: bool = True
        self.z_order_callback: Optional[Any] = None
        self.hwnd_target_lang: Dict[int, str] = {}

class WINDOWPLACEMENT(ctypes.Structure):
    _fields_ = [
        ("length", ctypes.c_uint),
        ("flags", ctypes.c_uint),
        ("showCmd", ctypes.c_uint),
        ("ptMinPosition", ctypes.wintypes.POINT),
        ("ptMaxPosition", ctypes.wintypes.POINT),
        ("rcNormalPosition", ctypes.wintypes.RECT),
    ]

# Global instances
config = Config()
window_state = WindowState()

def set_root(r: tk.Tk) -> None:
    window_state.root = r

def prompt_for_firebase_url() -> Optional[str]:
    if config.firebase_url:
        return config.firebase_url

    dialog = tk.Toplevel(window_state.root)
    dialog.title("Nhập Firebase URL")
    dialog.geometry("400x150")
    dialog.attributes("-topmost", True)
    dialog.grab_set()

    tk.Label(dialog, text="Vui lòng nhập Firebase URL:").pack(pady=10)
    url_entry = tk.Entry(dialog, width=50)
    url_entry.pack(pady=5)

    def save_url() -> None:
        url = url_entry.get().strip()
        if not url:
            messagebox.showerror("Lỗi", "URL không được để trống!")
            return

        try:
            config.firebase_url = url
            config.config['firebase_url'] = url
            with open("config.json", "w", encoding="utf-8") as f:
                json.dump(config.config, f, ensure_ascii=False, indent=4)
            dialog.destroy()
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể lưu URL: {e}")

    tk.Button(dialog, text="OK", command=save_url).pack(pady=10)
    dialog.wait_window()
    return config.firebase_url

def set_sam_mini_chat_globals(xai_api_key: str, chatgpt_api_key: str, llm_api_key: str, default_lang: str) -> None:
    if xai_api_key and xai_api_key.startswith("xai-"):
        config.xai_api_key = xai_api_key
    if chatgpt_api_key and chatgpt_api_key.startswith("sk-"):
        config.chatgpt_api_key = chatgpt_api_key
    if llm_api_key and llm_api_key.startswith("llm-"):
        config.llm_api_key = llm_api_key
    config.default_target_lang = default_lang
    
    config.my_lang_selection = config.config.get('MY_LANG_SELECTION', config.my_lang_selection)
    config.target_lang_selection = config.config.get('TARGET_LANG_SELECTION', config.target_lang_selection)
    config.selected_api = config.config.get('SELECTED_API', config.selected_api)

def create_sam_mini_chat() -> None:
    if window_state.root is None:
        return
    
    window_state.sam_mini_chat_win = window_state.root
    window_state.sam_mini_chat_win.title("Sam Mini Chat")
    window_state.sam_mini_chat_win.overrideredirect(True)
    window_state.sam_mini_chat_win.geometry(f"600x{config.widget_height}+0+0")
    
    setup_z_order_monitoring()
    
    frame = tk.Frame(window_state.sam_mini_chat_win, bg="#f0f0f0", padx=10, pady=5)
    frame.pack(fill=tk.BOTH, expand=True)
    
    style = {
        "bg": "#f0f0f0",
        "fg": "#333333",
        "font": ("Segoe UI", 11),
        "relief": "flat",
        "borderwidth": 0
    }
    
    button_style = {
        "bg": "#007AFF",
        "fg": "white",
        "font": ("Segoe UI", 10, "bold"),
        "relief": "flat",
        "borderwidth": 0,
        "padx": 15,
        "height": 1,
        "cursor": "hand2"
    }
    
    option_menu_style = {
        "bg": "#ffffff",
        "fg": style["fg"],
        "font": style["font"],
        "relief": "flat",
        "borderwidth": 1,
        "highlightthickness": 1,
        "highlightbackground": "#cccccc",
        "width": 12,
        "height": 1,
        "indicatoron": 0
    }
    
    target_lang_var = tk.StringVar(value=config.lang_map.get(config.target_lang_selection, "Tiếng Anh"))
    
    def update_target_lang(val: str) -> None:
        lang_code = next((code for code, name in config.lang_map.items() if name == val), config.target_lang_selection)
        config.target_lang_selection = lang_code
        hwnd = get_correct_telegram_hwnd()
        if hwnd:
            window_state.hwnd_target_lang[hwnd] = lang_code
    
    lang_display_names = [config.lang_map[lang] for lang in config.all_lang_options if lang in config.lang_map]
    target_lang_menu = tk.OptionMenu(frame, target_lang_var, *lang_display_names, command=update_target_lang)
    target_lang_menu.config(**option_menu_style)
    target_lang_menu.grid(row=0, column=1, padx=5, pady=5, sticky="e")
    
    api_var = tk.StringVar(value=config.selected_api)
    
    def update_api(val: str) -> None:
        config.selected_api = val
    
    api_menu = tk.OptionMenu(frame, api_var, *["XAI", "ChatGPT", "LLM"], command=update_api)
    api_menu_style = option_menu_style.copy()
    api_menu_style["width"] = 8
    api_menu.config(**api_menu_style)
    api_menu.grid(row=0, column=2, padx=5, pady=5, sticky="e")
    
    window_state.sam_mini_chat_entry = tk.Text(
        frame,
        font=style["font"],
        relief="flat",
        borderwidth=1,
        highlightthickness=1,
        highlightbackground="#cccccc",
        highlightcolor="#007AFF",
        height=1,
        wrap=tk.WORD,
        padx=5,
        pady=3
    )
    window_state.sam_mini_chat_entry.grid(row=0, column=0, sticky="we", padx=5, pady=5)
    frame.columnconfigure(0, weight=1)
    
    # Add quick reply button
    quick_reply_text = "Xin chào! Bạn cần chúng tôi giúp đỡ gì không ?"
    quick_reply_btn = tk.Button(
        frame,
        text=quick_reply_text,
        command=lambda: send_quick_reply(quick_reply_text),
        bg="#E8F5E9",
        fg="#2E7D32",
        font=("Segoe UI", 9),
        relief="flat",
        borderwidth=0,
        padx=10,
        pady=5,
        cursor="hand2"
    )
    quick_reply_btn.grid(row=1, column=0, columnspan=5, sticky="we", padx=5, pady=(0, 5))
    
    # Add second quick reply button
    quick_reply_text2 = "Vui lòng cung cấp cho tôi Email hoặc Số điện thoại đăng ký của bạn, tôi sẽ kiểm tra trên hệ thống !"
    quick_reply_btn2 = tk.Button(
        frame,
        text=quick_reply_text2,
        command=lambda: send_quick_reply(quick_reply_text2),
        bg="#E3F2FD",
        fg="#1565C0",
        font=("Segoe UI", 9),
        relief="flat",
        borderwidth=0,
        padx=10,
        pady=5,
        cursor="hand2"
    )
    quick_reply_btn2.grid(row=2, column=0, columnspan=5, sticky="we", padx=5, pady=(0, 5))
    
    def on_quick_reply_enter(e):
        if e.widget == quick_reply_btn:
            e.widget['background'] = '#C8E6C9'
        else:
            e.widget['background'] = '#BBDEFB'
    
    def on_quick_reply_leave(e):
        if e.widget == quick_reply_btn:
            e.widget['background'] = '#E8F5E9'
        else:
            e.widget['background'] = '#E3F2FD'
    
    quick_reply_btn.bind("<Enter>", on_quick_reply_enter)
    quick_reply_btn.bind("<Leave>", on_quick_reply_leave)
    quick_reply_btn2.bind("<Enter>", on_quick_reply_enter)
    quick_reply_btn2.bind("<Leave>", on_quick_reply_leave)
    
    def send_quick_reply(text):
        window_state.sam_mini_chat_entry.delete("1.0", tk.END)
        window_state.sam_mini_chat_entry.insert("1.0", text)
        send_sam_mini_chat_message()
    
    def on_enter(event: tk.Event) -> str:
        if not event.state & 0x1:
            send_sam_mini_chat_message()
            return "break"
        return ""
    
    def on_shift_enter(event: tk.Event) -> str:
        if event.state & 0x1:
            window_state.sam_mini_chat_entry.insert(tk.INSERT, "\n")
            return "break"
        return ""
    
    window_state.sam_mini_chat_entry.bind("<Return>", on_enter)
    window_state.sam_mini_chat_entry.bind("<Shift-Return>", on_shift_enter)
    
    window_state.sam_mini_chat_btn_send = tk.Button(
        frame,
        text="Send",
        command=send_sam_mini_chat_message,
        **button_style
    )
    window_state.sam_mini_chat_btn_send.grid(row=0, column=3, padx=5, pady=5, sticky="e")
    
    btn_quit = tk.Button(
        frame,
        text="Quit",
        command=destroy_sam_mini_chat,
        bg="#FF3B30",
        **{k: v for k, v in button_style.items() if k != "bg"}
    )
    btn_quit.grid(row=0, column=4, padx=5, pady=5, sticky="e")
    
    def on_enter(e: tk.Event) -> None:
        e.widget['background'] = '#0056b3' if e.widget['text'] == 'Send' else '#cc2f26'
    
    def on_leave(e: tk.Event) -> None:
        e.widget['background'] = '#007AFF' if e.widget['text'] == 'Send' else '#FF3B30'
    
    window_state.sam_mini_chat_btn_send.bind("<Enter>", on_enter)
    window_state.sam_mini_chat_btn_send.bind("<Leave>", on_leave)
    btn_quit.bind("<Enter>", on_enter)
    btn_quit.bind("<Leave>", on_leave)
    
    def start_move(event: tk.Event) -> None:
        frame.x = event.x
        frame.y = event.y
    
    def do_move(event: tk.Event) -> None:
        deltax = event.x - frame.x
        deltay = event.y - frame.y
        x = window_state.sam_mini_chat_win.winfo_x() + deltax
        y = window_state.sam_mini_chat_win.winfo_y() + deltay
        window_state.sam_mini_chat_win.geometry(f"+{x}+{y}")
    
    frame.bind("<Button-1>", start_move)
    frame.bind("<B1-Motion>", do_move)
    
    threading.Thread(target=update_sam_mini_chat_position, daemon=True).start()

def destroy_sam_mini_chat() -> None:
    window_state.widget_sam_mini_chat_thread_running = False
    if window_state.sam_mini_chat_win is not None:
        try:
            if window_state.sam_mini_chat_win.winfo_exists():
                window_state.sam_mini_chat_win.destroy()
            window_state.sam_mini_chat_win = None
            window_state.sam_mini_chat_entry = None
        except tk.TclError:
            window_state.sam_mini_chat_win = None
            window_state.sam_mini_chat_entry = None
    
    if window_state.root is not None:
        try:
            window_state.root.quit()
            window_state.root.destroy()
        except tk.TclError:
            pass

def sync_z_order_with_telegram(telegram_hwnd: int, widget_hwnd: int) -> None:
    try:
        hwnd_above = user32.GetWindow(telegram_hwnd, 3)
        if hwnd_above:
            user32.SetWindowPos(widget_hwnd, hwnd_above, 0, 0, 0, 0, 
                              SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE)
        else:
            user32.SetWindowPos(widget_hwnd, HWND_TOPMOST, 0, 0, 0, 0, 
                              SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE)
            user32.SetWindowPos(widget_hwnd, HWND_NOTOPMOST, 0, 0, 0, 0, 
                              SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE)
    except Exception as e:
        print(f"Error syncing Z-order: {e}")

def update_sam_mini_chat_position() -> None:
    while window_state.sam_mini_chat_win is not None and window_state.widget_sam_mini_chat_thread_running:
        try:
            hwnd = get_correct_telegram_hwnd()
            if hwnd:
                placement = WINDOWPLACEMENT()
                placement.length = ctypes.sizeof(WINDOWPLACEMENT)
                user32.GetWindowPlacement(hwnd, ctypes.byref(placement))
                
                is_minimized = user32.IsIconic(hwnd)
                
                if is_minimized:
                    window_state.sam_mini_chat_win.withdraw()
                else:
                    window_state.sam_mini_chat_win.deiconify()
                    
                    if placement.showCmd != 1:
                        rect = placement.rcNormalPosition
                    else:
                        rect = ctypes.wintypes.RECT()
                        user32.GetWindowRect(hwnd, ctypes.byref(rect))
                    
                    window_width = rect.right - rect.left
                    x = rect.left
                    y = rect.bottom + config.widget_y_offset
                    
                    new_geometry = f"{window_width}x{config.widget_height}+{x}+{y}"
                    window_state.sam_mini_chat_win.geometry(new_geometry)
                    
                    widget_hwnd = window_state.sam_mini_chat_win.winfo_id()
                    sync_z_order_with_telegram(hwnd, widget_hwnd)
            else:
                window_state.sam_mini_chat_win.withdraw()
                
        except tk.TclError:
            break
        except Exception as e:
            print(f"Error updating widget position: {e}")
            
        time.sleep(0.1)

def send_sam_mini_chat_message() -> None:
    if window_state.sam_mini_chat_entry is None:
        return
        
    msg = window_state.sam_mini_chat_entry.get("1.0", tk.END).strip()
    if not msg:
        return
        
    original_msg = msg
    window_state.sam_mini_chat_entry.delete("1.0", tk.END)
    hwnd = get_correct_telegram_hwnd()
    if hwnd is None:
        window_state.sam_mini_chat_entry.insert("1.0", original_msg)
        return
        
    target_lang = window_state.hwnd_target_lang.get(hwnd, config.target_lang_selection)

    window_state.sam_mini_chat_btn_send.config(text="Sending", state=tk.DISABLED)
    original_bg = window_state.sam_mini_chat_btn_send.cget("background")
    window_state.sam_mini_chat_btn_send.config(background="#90EE90")
    window_state.root.after(100, lambda: window_state.sam_mini_chat_btn_send.config(background=original_bg))
    window_state.root.after(200, lambda: window_state.sam_mini_chat_btn_send.config(background="#90EE90"))
    window_state.root.after(300, lambda: window_state.sam_mini_chat_btn_send.config(background=original_bg))

    def send_thread() -> None:
        try:
            translated = None
            if config.selected_api == "XAI":
                translated, _ = translate_text_for_dialogue_xai(msg, source_lang="auto", target_lang=target_lang)
            elif config.selected_api == "ChatGPT":
                translated, _ = translate_text_for_dialogue_chatgpt(msg, source_lang="auto", target_lang=target_lang)
            elif config.selected_api == "LLM":
                translated, _ = translate_text_for_dialogue_llm(msg, source_lang="auto", target_lang=target_lang)
            
            if translated is None or translated == msg:
                raise Exception("Translation failed")
                
            send_message_to_telegram_input(hwnd, translated)
            window_state.sam_mini_chat_entry.focus_force()
        except Exception as e:
            window_state.root.after(0, lambda: window_state.sam_mini_chat_entry.delete("1.0", tk.END))
            window_state.root.after(0, lambda: window_state.sam_mini_chat_entry.insert("1.0", original_msg))
        finally:
            window_state.root.after(0, lambda: window_state.sam_mini_chat_btn_send.config(text="Send", state=tk.NORMAL))

    threading.Thread(target=send_thread, daemon=True).start()

def send_message_to_telegram_input(hwnd: int, message: str) -> None:
    rect = ctypes.wintypes.RECT()
    user32.GetWindowRect(hwnd, ctypes.byref(rect))
    width = rect.right - rect.left
    x = rect.left + width // 2
    y = rect.bottom - 3
    
    user32.SetCursorPos(x, y)
    time.sleep(0.1)
    user32.mouse_event(2, 0, 0, 0, 0)
    time.sleep(0.05)
    user32.mouse_event(4, 0, 0, 0, 0)
    time.sleep(0.1)
    
    window_state.root.clipboard_clear()
    window_state.root.clipboard_append(message)
    window_state.root.update()
    time.sleep(0.1)
    
    VK_CONTROL = 0x11
    VK_V = 0x56
    VK_RETURN = 0x0D
    
    user32.keybd_event(VK_CONTROL, 0, 0, 0)
    time.sleep(0.05)
    user32.keybd_event(VK_V, 0, 0, 0)
    time.sleep(0.05)
    user32.keybd_event(VK_V, 0, 2, 0)
    time.sleep(0.05)
    user32.keybd_event(VK_CONTROL, 0, 2, 0)
    time.sleep(0.1)
    user32.keybd_event(VK_RETURN, 0, 0, 0)
    time.sleep(0.05)
    user32.keybd_event(VK_RETURN, 0, 2, 0)
    time.sleep(0.1)

def get_correct_telegram_hwnd() -> Optional[int]:
    hwnd_fore = user32.GetForegroundWindow()
    pid = ctypes.wintypes.DWORD()
    user32.GetWindowThreadProcessId(hwnd_fore, ctypes.byref(pid))
    
    try:
        proc = psutil.Process(pid.value)
        if proc.name().lower() == "telegram.exe" and not user32.IsIconic(hwnd_fore):
            window_state.last_valid_telegram_hwnd = hwnd_fore
            return hwnd_fore
    except Exception:
        pass
        
    if window_state.last_valid_telegram_hwnd is not None and not user32.IsIconic(window_state.last_valid_telegram_hwnd):
        return window_state.last_valid_telegram_hwnd
        
    hwnd_result = None
    EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_int, ctypes.c_int)
    
    def enum_windows_proc(hwnd: int, lParam: int) -> bool:
        nonlocal hwnd_result
        if user32.IsWindowVisible(hwnd) and not user32.IsIconic(hwnd):
            length = user32.GetWindowTextLengthW(hwnd)
            buff = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buff, length + 1)
            pid_local = ctypes.wintypes.DWORD()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid_local))
            try:
                proc = psutil.Process(pid_local.value)
                if proc.name().lower() == "telegram.exe":
                    hwnd_result = hwnd
                    window_state.last_valid_telegram_hwnd = hwnd
                    return False
            except Exception:
                pass
        return True
        
    enum_proc_c = EnumWindowsProc(enum_windows_proc)
    user32.EnumWindows(enum_proc_c, 0)
    return hwnd_result

def remove_think_tags(text: str) -> str:
    return re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL).strip()

def translate_text_for_dialogue_xai(text: str, source_lang: str = "auto", target_lang: str = "vi") -> Tuple[Optional[str], Optional[str]]:
    if not config.xai_api_key:
        return text, None
        
    try:
        lang_name = config.lang_map.get(target_lang.lower(), target_lang)
        prompt = (
            f"Bạn là một công cụ dịch ngôn ngữ chuyên nghiệp. Nhiệm vụ của bạn là dịch tin nhắn sau từ {source_lang} sang {lang_name}. "
            f"Chỉ trả về bản dịch mà không thêm bất kỳ bình luận hoặc giải thích nào. "
            f"Tin nhắn: \"{text}\""
        )
        
        headers = {
            "Authorization": f"Bearer {config.xai_api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "grok-beta",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.05,
            "top_p": 0.9,
            "max_tokens": 2000
        }
        
        response = requests.post(
            "https://api.x.ai/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            translated_text = data["choices"][0]["message"]["content"].strip()
            translated_text = remove_think_tags(translated_text)
            return translated_text, None
        else:
            return text, None
            
    except Exception as e:
        return text, None

def translate_text_for_dialogue_chatgpt(text: str, source_lang: str = "auto", target_lang: str = "vi") -> Tuple[Optional[str], Optional[str]]:
    if not config.chatgpt_api_key:
        return text, None
        
    try:
        lang_name = config.lang_map.get(target_lang.lower(), target_lang)
        prompt = (
            f"You are a professional language translator. Your task is to translate the following message from {source_lang} to {lang_name}. "
            f"Provide only the translation without any additional comments or explanations. "
            f"Message: \"{text}\""
        )
        
        headers = {
            "Authorization": f"Bearer {config.chatgpt_api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "gpt-4",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.05,
            "top_p": 0.9,
            "max_tokens": 2000
        }
        
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            translated_text = data["choices"][0]["message"]["content"].strip()
            translated_text = remove_think_tags(translated_text)
            return translated_text, None
        else:
            return text, None
            
    except Exception as e:
        return text, None

def translate_text_for_dialogue_llm(text: str, source_lang: str = "auto", target_lang: str = "vi") -> Tuple[Optional[str], Optional[str]]:
    if not config.llm_api_key:
        return text, None
        
    ngrok_url = fetch_ngrok_url()
    if not ngrok_url:
        return text, None
        
    try:
        api_url = f"{ngrok_url}/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {config.llm_api_key}"
        }
        
        lang_name = config.lang_map.get(target_lang.lower(), target_lang)
        prompt = (
            f"You are a professional language translator. Your task is to translate the following message from {source_lang} to {lang_name}. "
            f"Provide only the translation without any additional comments or explanations. "
            f"Message: \"{text}\""
        )
        
        payload = {
            "model": "qwen3-8b",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.05,
            "top_p": 0.9,
            "max_tokens": 2000
        }
        
        response = requests.post(api_url, headers=headers, json=payload, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            translated_text = data["choices"][0]["message"]["content"].strip()
            translated_text = remove_think_tags(translated_text)
            return translated_text, None
        else:
            return text, None
            
    except Exception as e:
        return text, None

def fetch_ngrok_url() -> Optional[str]:
    if not config.firebase_url:
        config.firebase_url = prompt_for_firebase_url()
        if not config.firebase_url:
            return None
            
    try:
        response = requests.get(config.firebase_url, timeout=5)
        if response.status_code == 200:
            url = response.json()
            if url:
                return url
            else:
                raise ValueError("Ngrok URL is empty")
        else:
            raise Exception(f"Failed to fetch ngrok URL: {response.status_code}")
    except Exception as e:
        return None

def win_event_callback(hWinEventHook: int, event: int, hwnd: int, idObject: int, idChild: int, dwEventThread: int, dwmsEventTime: int) -> None:
    try:
        if event == EVENT_OBJECT_REORDER or event == EVENT_SYSTEM_FOREGROUND:
            if hwnd == get_correct_telegram_hwnd():
                if window_state.sam_mini_chat_win and window_state.sam_mini_chat_win.winfo_exists():
                    widget_hwnd = window_state.sam_mini_chat_win.winfo_id()
                    sync_z_order_with_telegram(hwnd, widget_hwnd)
    except Exception as e:
        print(f"Error in win_event_callback: {e}")

def setup_z_order_monitoring() -> None:
    try:
        WinEventProcType = ctypes.WINFUNCTYPE(
            None, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int
        )
        
        window_state.z_order_callback = WinEventProcType(win_event_callback)
        
        user32.SetWinEventHook(
            EVENT_OBJECT_REORDER,
            EVENT_SYSTEM_FOREGROUND,
            0,
            window_state.z_order_callback,
            0,
            0,
            WINEVENT_OUTOFCONTEXT | WINEVENT_SKIPOWNTHREAD | WINEVENT_SKIPOWNPROCESS
        )
    except Exception as e:
        print(f"Error setting up Z-order monitoring: {e}")