import os
import sys
import requests
import json
import threading
import time
import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk
from ttkthemes import ThemedTk
import ctypes
from ctypes import wintypes
import re
from config import load_config
from typing import Optional, Tuple, Dict, Any

try:
    import psutil
except ImportError:
    psutil = None

# Set appearance mode and default color theme
ctk.set_appearance_mode("light")  # Modes: "System" (standard), "Dark", "Light"
ctk.set_default_color_theme("blue")  # Themes: "blue" (standard), "green", "dark-blue"

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
        self.root: Optional[ThemedTk] = None
        self.sam_mini_chat_win: Optional[ThemedTk] = None
        self.sam_mini_chat_entry: Optional[ctk.CTkTextbox] = None
        self.sam_mini_chat_btn_send: Optional[ctk.CTkButton] = None
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

class QuickReply:
    def __init__(self, title, content):
        self.title = title
        self.content = content

# Global instances
config = Config()
window_state = WindowState()

def initialize_root_window(r: ThemedTk) -> None:
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

def initialize_chat_config(xai_api_key: str, chatgpt_api_key: str, llm_api_key: str, default_lang: str) -> None:
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

def create_chat_window() -> None:
    if window_state.root is None:
        return
    
    window_config = config.config.get("widget_config", {}).get("window", {})
    window_state.sam_mini_chat_win = window_state.root
    window_state.sam_mini_chat_win.title(window_config.get("title", "Sam Mini Chat"))
    window_state.sam_mini_chat_win.overrideredirect(window_config.get("overrideredirect", True))
    window_state.sam_mini_chat_win.geometry(f"{window_config.get('width', 600)}x{config.widget_height}+0+0")
    
    setup_z_order_monitoring()
    
    main_frame = ctk.CTkFrame(
        window_state.sam_mini_chat_win,
        fg_color=window_config.get("bg", "#f0f0f0"),
        corner_radius=0
    )
    main_frame.pack(fill=tk.BOTH, expand=True, padx=window_config.get("padx", 10), pady=window_config.get("pady", 5))
    
    # Top row frame
    top_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
    top_frame.pack(fill=tk.X, pady=(0, 5))
    
    style = config.config.get("widget_config", {}).get("style", {})
    button_style = config.config.get("widget_config", {}).get("button_style", {})
    option_menu_style = config.config.get("widget_config", {}).get("option_menu_style", {})
    api_menu_style = config.config.get("widget_config", {}).get("api_menu_style", {})
    text_entry_style = config.config.get("widget_config", {}).get("text_entry_style", {})
    
    # Left controls frame (API, Quit, Language)
    left_controls = ctk.CTkFrame(top_frame, fg_color="transparent")
    left_controls.pack(side=tk.LEFT, padx=5)
    
    api_var = tk.StringVar(value=config.selected_api)
    
    def update_api(val: str) -> None:
        config.selected_api = val
    
    api_menu = ctk.CTkOptionMenu(
        left_controls,
        values=["XAI", "ChatGPT", "LLM"],
        variable=api_var,
        command=update_api,
        font=tuple(api_menu_style.get("font", ["Segoe UI", 10, "bold"])),
        fg_color=api_menu_style.get("bg", "#E8F5E9"),
        text_color=api_menu_style.get("fg", "#2E7D32"),
        button_color=api_menu_style.get("activebackground", "#C8E6C9"),
        button_hover_color=api_menu_style.get("activeforeground", "#1B5E20"),
        corner_radius=5,
        width=api_menu_style.get("width", 80)
    )
    api_menu.pack(side=tk.LEFT, padx=5)
    
    btn_quit = ctk.CTkButton(
        left_controls,
        text="Quit",
        command=close_chat_window,
        fg_color="#FF3B30",
        hover_color="#cc2f26",
        font=tuple(button_style.get("font", ["Segoe UI", 10, "bold"])),
        corner_radius=5,
        width=button_style.get("width", 10)
    )
    btn_quit.pack(side=tk.LEFT, padx=5)
    
    target_lang_var = tk.StringVar(value=config.lang_map.get(config.target_lang_selection, "Tiếng Anh"))
    
    def update_target_lang(val: str) -> None:
        lang_code = next((code for code, name in config.lang_map.items() if name == val), config.target_lang_selection)
        config.target_lang_selection = lang_code
        hwnd = get_correct_telegram_hwnd()
        if hwnd:
            window_state.hwnd_target_lang[hwnd] = lang_code
    
    lang_display_names = [config.lang_map[lang] for lang in config.all_lang_options if lang in config.lang_map]
    target_lang_menu = ctk.CTkOptionMenu(
        left_controls,
        values=lang_display_names,
        variable=target_lang_var,
        command=update_target_lang,
        font=tuple(option_menu_style.get("font", ["Segoe UI", 10])),
        fg_color=option_menu_style.get("bg", "#ffffff"),
        text_color=option_menu_style.get("fg", "#333333"),
        button_color=option_menu_style.get("activebackground", "#f5f5f5"),
        button_hover_color=option_menu_style.get("activeforeground", "#007AFF"),
        corner_radius=5
    )
    target_lang_menu.pack(side=tk.LEFT, padx=5)
    
    # Input frame
    input_frame = ctk.CTkFrame(top_frame, fg_color="transparent")
    input_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
    
    window_state.sam_mini_chat_entry = ctk.CTkTextbox(
        input_frame,
        font=tuple(text_entry_style.get("font", ["Segoe UI", 11])),
        fg_color=text_entry_style.get("bg", "#ffffff"),
        text_color=text_entry_style.get("fg", "#333333"),
        border_width=text_entry_style.get("borderwidth", 1),
        corner_radius=5,
        height=text_entry_style.get("height", 1) * 20
    )
    window_state.sam_mini_chat_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
    
    window_state.sam_mini_chat_btn_send = ctk.CTkButton(
        input_frame,
        text="Send",
        command=send_sam_mini_chat_message,
        font=tuple(button_style.get("font", ["Segoe UI", 10, "bold"])),
        fg_color=button_style.get("bg", "#007AFF"),
        hover_color="#0056b3",
        corner_radius=5,
        width=button_style.get("width", 10)
    )
    window_state.sam_mini_chat_btn_send.pack(side=tk.LEFT, padx=5)
    
    # Quick language selection frame
    quick_lang_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
    quick_lang_frame.pack(fill=tk.X, pady=(0, 5))
    
    quick_lang_style = config.config.get("language_config", {}).get("quick_language_style", {})
    quick_languages = config.config.get("language_config", {}).get("quick_languages", ["en", "vi", "ja", "zh", "ko"])
    
    def on_quick_lang_click(lang_code: str) -> None:
        lang_name = config.lang_map.get(lang_code, lang_code)
        target_lang_var.set(lang_name)
        update_target_lang(lang_name)
    
    # Create a container frame for the buttons that aligns with input_frame
    lang_buttons_frame = ctk.CTkFrame(quick_lang_frame, fg_color="transparent")
    lang_buttons_frame.pack(side=tk.LEFT, padx=(310, 0))  # Set left padding to 200px
    
    for lang_code in quick_languages:
        lang_name = config.lang_map.get(lang_code, lang_code)
        btn = ctk.CTkButton(
            lang_buttons_frame,
            text=lang_name,
            command=lambda l=lang_code: on_quick_lang_click(l),
            font=tuple(quick_lang_style.get("button", {}).get("font", ["Segoe UI", 13])),
            fg_color=quick_lang_style.get("button", {}).get("fg_color", "#E3F2FD"),
            text_color=quick_lang_style.get("button", {}).get("text_color", "#1976D2"),
            hover_color=quick_lang_style.get("button", {}).get("hover_color", "#BBDEFB"),
            corner_radius=quick_lang_style.get("button", {}).get("corner_radius", 3),
            border_width=quick_lang_style.get("button", {}).get("border_width", 1),
            border_color=quick_lang_style.get("button", {}).get("border_color", "#90CAF9"),
            height=quick_lang_style.get("button", {}).get("height", 1) * 20,
            width=quick_lang_style.get("button", {}).get("width", 8),
            cursor=quick_lang_style.get("button", {}).get("cursor", "hand2")
        )
        btn.pack(side=tk.LEFT, padx=2)
        
        def update_btn_appearance(*args, btn=btn):
            if btn.cget("text") == target_lang_var.get():
                btn.configure(
                    fg_color=quick_lang_style.get("button", {}).get("selected_color", "#2196F3"),
                    text_color=quick_lang_style.get("button", {}).get("selected_text_color", "white"),
                    border_color=quick_lang_style.get("button", {}).get("selected_border_color", "#1976D2")
                )
            else:
                btn.configure(
                    fg_color=quick_lang_style.get("button", {}).get("fg_color", "#E3F2FD"),
                    text_color=quick_lang_style.get("button", {}).get("text_color", "#1976D2"),
                    border_color=quick_lang_style.get("button", {}).get("border_color", "#90CAF9")
                )
        
        target_lang_var.trace_add("write", update_btn_appearance)
        update_btn_appearance()
    
    # Quick reply frame
    quick_reply_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
    quick_reply_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 5))
    
    # Get quick replies from config
    quick_replies = config.config.get("widget_config", {}).get("quick_reply_buttons", [])
    
    # Create two columns with equal width
    left_column = ctk.CTkFrame(quick_reply_frame, fg_color="transparent")
    left_column.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
    
    # Add vertical divider
    divider = ctk.CTkFrame(quick_reply_frame, width=2, fg_color="#E0E0E0")
    divider.pack(side=tk.LEFT, fill=tk.Y, padx=0)
    
    right_column = ctk.CTkFrame(quick_reply_frame, fg_color="transparent")
    right_column.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5, 0))
    
    # Get button colors from config
    button_colors = config.config.get("widget_config", {}).get("quick_reply_colors", [
        {"bg": "#4CAF50", "fg": "white", "hover": "#45A049"},  # Green
        {"bg": "#2196F3", "fg": "white", "hover": "#1E88E5"},  # Blue
        {"bg": "#FF9800", "fg": "white", "hover": "#F57C00"},  # Orange
        {"bg": "#9C27B0", "fg": "white", "hover": "#8E24AA"},  # Purple
        {"bg": "#00BCD4", "fg": "white", "hover": "#00ACC1"},  # Cyan
        {"bg": "#F44336", "fg": "white", "hover": "#E53935"},  # Red
        {"bg": "#8BC34A", "fg": "white", "hover": "#7CB342"},  # Light Green
        {"bg": "#3F51B5", "fg": "white", "hover": "#3949AB"},  # Indigo
        {"bg": "#E91E63", "fg": "white", "hover": "#D81B60"},  # Pink
        {"bg": "#795548", "fg": "white", "hover": "#6D4C41"}   # Brown
    ])
    
    # Create buttons in two columns
    for i, reply in enumerate(quick_replies):
        # Get color from config, use default if not found
        color_index = i % len(button_colors)
        style = button_colors[color_index]
        
        # Determine which column to place the button
        column = left_column if i % 2 == 0 else right_column
        
        quick_reply_btn = ctk.CTkButton(
            column,
            text=reply.get("title", ""),
            command=lambda r=reply: send_quick_reply(r.get("content", "")),
            font=tuple(reply.get("font", ["Segoe UI", 9, "bold"])),
            fg_color=style["bg"],
            text_color=style["fg"],
            hover_color=style["hover"],
            corner_radius=8,
            width=180,
            height=35,
            border_width=0,
            anchor="w"  # Left align text
        )
        quick_reply_btn.pack(pady=2, fill="x", expand=True)
    
    # Add resize handle at the bottom
    resize_handle = ctk.CTkFrame(main_frame, height=5, fg_color="#CCCCCC", cursor="sb_v_double_arrow")
    resize_handle.pack(side=tk.BOTTOM, fill=tk.X, padx=0, pady=0)
    
    def start_resize(event):
        resize_handle.y_start = event.y_root
        resize_handle.win_height = window_state.sam_mini_chat_win.winfo_height()
        resize_handle.bind("<B1-Motion>", do_resize)
        resize_handle.bind("<ButtonRelease-1>", stop_resize)
    
    def do_resize(event):
        delta_y = event.y_root - resize_handle.y_start
        new_height = resize_handle.win_height + delta_y
        if new_height >= 100:  # Minimum height
            window_state.sam_mini_chat_win.geometry(f"{window_state.sam_mini_chat_win.winfo_width()}x{new_height}")
            config.widget_height = new_height
    
    def stop_resize(event):
        resize_handle.unbind("<B1-Motion>")
        resize_handle.unbind("<ButtonRelease-1>")
    
    resize_handle.bind("<Button-1>", start_resize)
    
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
    
    def start_move(event: tk.Event) -> None:
        main_frame.x = event.x
        main_frame.y = event.y
    
    def do_move(event: tk.Event) -> None:
        deltax = event.x - main_frame.x
        deltay = event.y - main_frame.y
        x = window_state.sam_mini_chat_win.winfo_x() + deltax
        y = window_state.sam_mini_chat_win.winfo_y() + deltay
        window_state.sam_mini_chat_win.geometry(f"+{x}+{y}")
    
    main_frame.bind("<Button-1>", start_move)
    main_frame.bind("<B1-Motion>", do_move)
    
    threading.Thread(target=update_sam_mini_chat_position, daemon=True).start()

def close_chat_window() -> None:
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

def send_message_to_telegram_input(hwnd: int, message: str) -> bool:
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
    
    keyboard_config = config.config.get("windows_api", {}).get("keyboard", {})
    VK_CONTROL = keyboard_config.get("VK_CONTROL", 17)
    VK_V = keyboard_config.get("VK_V", 86)
    VK_RETURN = keyboard_config.get("VK_RETURN", 13)
    
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
    
    return True

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

    # Disable input and send button during sending
    window_state.sam_mini_chat_entry.configure(state=tk.DISABLED)
    window_state.sam_mini_chat_btn_send.configure(state=tk.DISABLED)
    
    # Get animation config
    ui_config = config.config.get("ui_config", {})
    loading_frames = ui_config.get("loading_frames", ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"])
    loading_interval = ui_config.get("loading_interval", 100)
    success_delay = ui_config.get("success_delay", 300)
    error_delay = ui_config.get("error_delay", 300)
    animation = ui_config.get("animation", {})
    
    # Get button style from config
    button_style = config.config.get("widget_config", {}).get("button_style", {})
    
    current_frame = 0
    loading_active = True
    
    def update_loading():
        nonlocal current_frame
        if window_state.sam_mini_chat_btn_send.winfo_exists() and loading_active:
            sending_config = animation.get("sending", {})
            window_state.sam_mini_chat_btn_send.configure(
                text=sending_config.get("text", "Sending {frame}").format(frame=loading_frames[current_frame]),
                fg_color=sending_config.get("bg", "#90EE90")
            )
            current_frame = (current_frame + 1) % len(loading_frames)
            window_state.root.after(loading_interval, update_loading)
    
    update_loading()

    def send_thread() -> None:
        nonlocal loading_active
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
            
            # Stop loading animation
            loading_active = False
            
            # Send message and wait for completion
            if send_message_to_telegram_input(hwnd, translated):
                # Success animation
                success_config = animation.get("success", {})
                window_state.root.after(0, lambda: window_state.sam_mini_chat_btn_send.configure(
                    text=success_config.get("text", "✓ Sent"),
                    fg_color=success_config.get("bg", "#4CAF50")
                ))
                window_state.root.after(success_delay, lambda: window_state.sam_mini_chat_btn_send.configure(
                    text="Send",
                    fg_color=button_style.get("bg", "#007AFF")
                ))
                window_state.sam_mini_chat_entry.focus_force()
            else:
                raise Exception("Failed to send message")
            
        except Exception as e:
            # Stop loading animation
            loading_active = False
            
            # Error animation
            error_config = animation.get("error", {})
            window_state.root.after(0, lambda: window_state.sam_mini_chat_btn_send.configure(
                text=error_config.get("text", "✗ Error"),
                fg_color=error_config.get("bg", "#FF3B30")
            ))
            window_state.root.after(error_delay, lambda: window_state.sam_mini_chat_btn_send.configure(
                text="Send",
                fg_color=button_style.get("bg", "#007AFF")
            ))
            window_state.root.after(0, lambda: window_state.sam_mini_chat_entry.delete("1.0", tk.END))
            window_state.root.after(0, lambda: window_state.sam_mini_chat_entry.insert("1.0", original_msg))
        finally:
            # Re-enable input and send button
            window_state.root.after(0, lambda: window_state.sam_mini_chat_entry.configure(state=tk.NORMAL))
            window_state.root.after(0, lambda: window_state.sam_mini_chat_btn_send.configure(state=tk.NORMAL))

    threading.Thread(target=send_thread, daemon=True).start()

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
        
        translation_config = config.config.get("translation_config", {}).get("xai", {})
        payload = {
            "model": translation_config.get("model", "grok-beta"),
            "messages": [{"role": "user", "content": prompt}],
            "temperature": translation_config.get("temperature", 0.05),
            "top_p": translation_config.get("top_p", 0.9),
            "max_tokens": translation_config.get("max_tokens", 2000)
        }
        
        response = requests.post(
            translation_config.get("api_url", "https://api.x.ai/v1/chat/completions"),
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
        
        translation_config = config.config.get("translation_config", {}).get("chatgpt", {})
        payload = {
            "model": translation_config.get("model", "gpt-4"),
            "messages": [{"role": "user", "content": prompt}],
            "temperature": translation_config.get("temperature", 0.05),
            "top_p": translation_config.get("top_p", 0.9),
            "max_tokens": translation_config.get("max_tokens", 2000)
        }
        
        response = requests.post(
            translation_config.get("api_url", "https://api.openai.com/v1/chat/completions"),
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
        
        translation_config = config.config.get("translation_config", {}).get("llm", {})
        payload = {
            "model": translation_config.get("model", "qwen3-8b"),
            "messages": [{"role": "user", "content": prompt}],
            "temperature": translation_config.get("temperature", 0.05),
            "top_p": translation_config.get("top_p", 0.9),
            "max_tokens": translation_config.get("max_tokens", 2000)
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
        
        windows_api_config = config.config.get("windows_api", {}).get("constants", {})
        user32.SetWinEventHook(
            windows_api_config.get("EVENT_OBJECT_REORDER", 32772),
            windows_api_config.get("EVENT_SYSTEM_FOREGROUND", 3),
            0,
            window_state.z_order_callback,
            0,
            0,
            windows_api_config.get("WINEVENT_OUTOFCONTEXT", 0) | 
            windows_api_config.get("WINEVENT_SKIPOWNTHREAD", 1) | 
            windows_api_config.get("WINEVENT_SKIPOWNPROCESS", 2)
        )
    except Exception as e:
        print(f"Error setting up Z-order monitoring: {e}")