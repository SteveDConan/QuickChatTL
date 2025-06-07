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
from config import load_config
import re

try:
    import psutil
except ImportError:
    psutil = None

# Lấy API keys và Firebase URL từ config.json
config = load_config()
XAI_API_KEY = config.get("xai_api_key", "")
CHATGPT_API_KEY = config.get("chatgpt_api_key", "")
LLM_API_KEY = config.get("llm_api_key", "")
FIREBASE_URL = config.get("firebase_url", "")
print(f"Consolog: Đã tải API keys từ config.json: XAI={XAI_API_KEY[:8] if XAI_API_KEY else None}..., ChatGPT={CHATGPT_API_KEY[:8] if CHATGPT_API_KEY else None}..., LLM={LLM_API_KEY[:8] if LLM_API_KEY else None}...")
print(f"Consolog: Đã tải FIREBASE_URL từ config.json: {FIREBASE_URL if FIREBASE_URL else 'Không có, sẽ yêu cầu người dùng nhập.'}")

# Biến cấu hình kích thước cho Sam Mini Chat
widget_config = config.get("widget_config", {})
WIDGET_HEIGHT = widget_config.get("height", 80)
WIDGET_Y_OFFSET = widget_config.get("y_offset", 1)

root = None
DEFAULT_TARGET_LANG = "en"

# Lấy cấu hình ngôn ngữ từ config
language_config = config.get("language_config", {})
all_lang_options = language_config.get("available_languages", ["en", "vi"])
lang_map = language_config.get("language_names", {"en": "Tiếng Anh", "vi": "Tiếng Việt"})

print(f"Consolog: Đã tải cấu hình ngôn ngữ từ config.json:")
print(f"Consolog: - Danh sách ngôn ngữ: {all_lang_options}")
print(f"Consolog: - Mapping ngôn ngữ: {lang_map}")

MY_LANG_SELECTION = config.get("MY_LANG_SELECTION", "vi")
TARGET_LANG_SELECTION = config.get("TARGET_LANG_SELECTION", DEFAULT_TARGET_LANG)
SELECTED_API = config.get("SELECTED_API", "XAI")  # API mặc định

sam_mini_chat_win = None
sam_mini_chat_entry = None
sam_mini_chat_pause_button = None

last_valid_telegram_hwnd = None
widget_sam_mini_chat_thread_running = True

my_lang_var = None
target_lang_var = None
sam_mini_chat_btn_send = None  # Nút Send cho Sam Mini Chat
firebase_url_var = None

user32 = ctypes.windll.user32

# Thêm các hằng số Windows API cần thiết
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

# Biến toàn cục để lưu trữ callback
z_order_callback = None

def set_root(r):
    global root
    root = r

def prompt_for_firebase_url():
    global FIREBASE_URL
    if FIREBASE_URL:
        return FIREBASE_URL

    dialog = tk.Toplevel(root)
    dialog.title("Nhập Firebase URL")
    dialog.geometry("400x150")
    dialog.attributes("-topmost", True)
    dialog.grab_set()

    tk.Label(dialog, text="Vui lòng nhập Firebase URL:").pack(pady=10)
    url_entry = tk.Entry(dialog, width=50)
    url_entry.pack(pady=5)

    def save_url():
        global FIREBASE_URL
        FIREBASE_URL = url_entry.get().strip()
        if FIREBASE_URL:
            try:
                config = load_config()
                config['firebase_url'] = FIREBASE_URL
                with open("config.json", "w", encoding="utf-8") as f:
                    json.dump(config, f, ensure_ascii=False, indent=4)
                print(f"Consolog: Đã lưu FIREBASE_URL vào config.json: {FIREBASE_URL}")
                dialog.destroy()
            except Exception as e:
                print(f"Consolog [LỖI]: Lỗi lưu FIREBASE_URL vào config.json: {e}")
                messagebox.showerror("Lỗi", f"Không thể lưu URL: {e}")
        else:
            messagebox.showerror("Lỗi", "URL không được để trống!")

    tk.Button(dialog, text="OK", command=save_url).pack(pady=10)
    dialog.wait_window()
    return FIREBASE_URL

def set_sam_mini_chat_globals(xai_api_key, chatgpt_api_key, llm_api_key, default_lang):
    global XAI_API_KEY, CHATGPT_API_KEY, LLM_API_KEY, DEFAULT_TARGET_LANG, MY_LANG_SELECTION, TARGET_LANG_SELECTION, SELECTED_API
    if xai_api_key and xai_api_key.startswith("xai-"):
        XAI_API_KEY = xai_api_key
    if chatgpt_api_key and chatgpt_api_key.startswith("sk-"):
        CHATGPT_API_KEY = chatgpt_api_key
    if llm_api_key and llm_api_key.startswith("llm-"):
        LLM_API_KEY = llm_api_key
    DEFAULT_TARGET_LANG = default_lang
    
    # Load cấu hình từ config
    config = load_config()
    MY_LANG_SELECTION = config.get('MY_LANG_SELECTION', MY_LANG_SELECTION)
    TARGET_LANG_SELECTION = config.get('TARGET_LANG_SELECTION', TARGET_LANG_SELECTION)
    SELECTED_API = config.get('SELECTED_API', SELECTED_API)
    
    print(f"Consolog: Đã thiết lập API keys: XAI={XAI_API_KEY[:8] if XAI_API_KEY else None}..., ChatGPT={CHATGPT_API_KEY[:8] if CHATGPT_API_KEY else None}..., LLM={LLM_API_KEY[:8] if LLM_API_KEY else None}...")
    print(f"Consolog: Load cấu hình từ config.json: MY_LANG={MY_LANG_SELECTION}, TARGET_LANG={TARGET_LANG_SELECTION}, SELECTED_API={SELECTED_API}")

hwnd_target_lang = {}

def create_sam_mini_chat():
    global sam_mini_chat_win, sam_mini_chat_entry, sam_mini_chat_btn_send
    if root is None:
        print("Consolog [LỖI]: root chưa set. Gọi set_root(root).")
        return
    
    # Sử dụng cửa sổ chính thay vì tạo Toplevel mới
    sam_mini_chat_win = root
    sam_mini_chat_win.title("Sam Mini Chat")
    sam_mini_chat_win.overrideredirect(True)  # Loại bỏ title bar
    sam_mini_chat_win.geometry(f"600x{WIDGET_HEIGHT}+0+0")
    
    # Thiết lập monitoring cho Z-order
    setup_z_order_monitoring()
    
    # Tạo frame chính với style hiện đại
    frame = tk.Frame(sam_mini_chat_win, bg="#f0f0f0", padx=10, pady=5)
    frame.pack(fill=tk.BOTH, expand=True)
    
    # Style cho các widget
    style = {
        "bg": "#f0f0f0",
        "fg": "#333333",
        "font": ("Segoe UI", 10),
        "relief": "flat",
        "borderwidth": 0
    }
    
    # Style chung cho tất cả các widget có chiều cao cố định
    common_height = 28  # Chiều cao cố định cho tất cả các widget
    
    button_style = {
        "bg": "#007AFF",
        "fg": "white",
        "font": ("Segoe UI", 10, "bold"),
        "relief": "flat",
        "borderwidth": 0,
        "padx": 15,
        "height": 1,  # Chiều cao cố định cho button
        "cursor": "hand2"
    }
    
    # Style cho OptionMenu
    option_menu_style = {
        "bg": "#ffffff",
        "fg": style["fg"],
        "font": style["font"],
        "relief": "flat",
        "borderwidth": 1,
        "highlightthickness": 1,
        "highlightbackground": "#cccccc",
        "width": 12,
        "height": 1,  # Chiều cao cố định cho dropdown
        "indicatoron": 0  # Ẩn biểu tượng dropdown arrow
    }
    
    # Thêm nút chọn ngôn ngữ đích với style mới
    target_lang_var = tk.StringVar(value=lang_map.get(TARGET_LANG_SELECTION, "Tiếng Anh"))
    def update_target_lang(val):
        global TARGET_LANG_SELECTION
        lang_code = next((code for code, name in lang_map.items() if name == val), TARGET_LANG_SELECTION)
        TARGET_LANG_SELECTION = lang_code
        hwnd = get_correct_telegram_hwnd()
        if hwnd:
            hwnd_target_lang[hwnd] = lang_code
        print(f"Consolog: Cập nhật ngôn ngữ đích cho Sam Mini Chat: {TARGET_LANG_SELECTION}")
    
    # Dropdown menu cho ngôn ngữ
    lang_display_names = [lang_map[lang] for lang in all_lang_options if lang in lang_map]
    target_lang_menu = tk.OptionMenu(frame, target_lang_var, *lang_display_names, command=update_target_lang)
    target_lang_menu.config(**option_menu_style)
    target_lang_menu.grid(row=0, column=1, padx=5, pady=5, sticky="e")
    
    # Thêm nút chọn API với style mới
    api_var = tk.StringVar(value=SELECTED_API)
    def update_api(val):
        global SELECTED_API
        SELECTED_API = val
        print(f"Consolog: Cập nhật API cho Sam Mini Chat: {SELECTED_API}")
    
    # Dropdown menu cho API
    api_menu = tk.OptionMenu(frame, api_var, *["XAI", "ChatGPT", "LLM"], command=update_api)
    api_menu_style = option_menu_style.copy()
    api_menu_style["width"] = 8  # Điều chỉnh width cho API menu
    api_menu.config(**api_menu_style)
    api_menu.grid(row=0, column=2, padx=5, pady=5, sticky="e")
    
    # Text widget thay thế cho Entry
    sam_mini_chat_entry = tk.Text(
        frame,
        font=style["font"],
        relief="flat",
        borderwidth=1,
        highlightthickness=1,
        highlightbackground="#cccccc",
        highlightcolor="#007AFF",
        height=1,  # Chiều cao ban đầu
        wrap=tk.WORD,  # Tự động xuống dòng
        padx=5,
        pady=2
    )
    sam_mini_chat_entry.grid(row=0, column=0, sticky="we", padx=5, pady=5)
    frame.columnconfigure(0, weight=1)
    
    # Hàm xử lý khi nhấn Enter
    def on_enter(event):
        if not event.state & 0x1:  # Không phải Shift+Enter
            send_sam_mini_chat_message()
            return "break"  # Ngăn không cho xuống dòng
    
    # Hàm xử lý khi nhấn Shift+Enter
    def on_shift_enter(event):
        if event.state & 0x1:  # Shift+Enter
            sam_mini_chat_entry.insert(tk.INSERT, "\n")
            return "break"
    
    sam_mini_chat_entry.bind("<Return>", on_enter)
    sam_mini_chat_entry.bind("<Shift-Return>", on_shift_enter)
    
    # Hàm để lấy nội dung từ Text widget
    def get_text_content():
        return sam_mini_chat_entry.get("1.0", tk.END).strip()
    
    # Hàm để xóa nội dung Text widget
    def clear_text_content():
        sam_mini_chat_entry.delete("1.0", tk.END)
    
    # Nút Send với style mới
    sam_mini_chat_btn_send = tk.Button(
        frame,
        text="Send",
        command=send_sam_mini_chat_message,
        **button_style
    )
    sam_mini_chat_btn_send.grid(row=0, column=3, padx=5, pady=5, sticky="e")
    
    # Nút Quit với style mới
    btn_quit = tk.Button(
        frame,
        text="Quit",
        command=destroy_sam_mini_chat,
        bg="#FF3B30",
        **{k: v for k, v in button_style.items() if k != "bg"}
    )
    btn_quit.grid(row=0, column=4, padx=5, pady=5, sticky="e")
    
    # Thêm hover effect cho các nút
    def on_enter(e):
        e.widget['background'] = '#0056b3' if e.widget['text'] == 'Send' else '#cc2f26'
    
    def on_leave(e):
        e.widget['background'] = '#007AFF' if e.widget['text'] == 'Send' else '#FF3B30'
    
    sam_mini_chat_btn_send.bind("<Enter>", on_enter)
    sam_mini_chat_btn_send.bind("<Leave>", on_leave)
    btn_quit.bind("<Enter>", on_enter)
    btn_quit.bind("<Leave>", on_leave)

    # Thêm khả năng di chuyển cửa sổ bằng cách kéo frame
    def start_move(event):
        frame.x = event.x
        frame.y = event.y

    def do_move(event):
        deltax = event.x - frame.x
        deltay = event.y - frame.y
        x = sam_mini_chat_win.winfo_x() + deltax
        y = sam_mini_chat_win.winfo_y() + deltay
        sam_mini_chat_win.geometry(f"+{x}+{y}")

    frame.bind("<Button-1>", start_move)
    frame.bind("<B1-Motion>", do_move)

    threading.Thread(target=update_sam_mini_chat_position, daemon=True).start()
    print("Consolog: Đã tạo widget Sam Mini Chat với giao diện hiện đại.")

def destroy_sam_mini_chat():
    global sam_mini_chat_win, widget_sam_mini_chat_thread_running
    widget_sam_mini_chat_thread_running = False
    if sam_mini_chat_win is not None:
        try:
            if sam_mini_chat_win.winfo_exists():
                sam_mini_chat_win.destroy()
            sam_mini_chat_win = None
            sam_mini_chat_entry = None
        except tk.TclError:
            sam_mini_chat_win = None
            sam_mini_chat_entry = None
    
    # Đóng hoàn toàn ứng dụng
    if root is not None:
        try:
            root.quit()
            root.destroy()
        except tk.TclError:
            pass
    print("Consolog: Đã đóng hoàn toàn ứng dụng.")

def sync_z_order_with_telegram(telegram_hwnd, widget_hwnd):
    """Đồng bộ Z-order của widget với cửa sổ Telegram"""
    try:
        # Lấy handle của cửa sổ phía trên Telegram
        hwnd_above = user32.GetWindow(telegram_hwnd, 3)  # GW_HWNDNEXT = 3
        if hwnd_above:
            # Đặt widget ngay sau cửa sổ phía trên Telegram
            user32.SetWindowPos(widget_hwnd, hwnd_above, 0, 0, 0, 0, 
                              SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE)
        else:
            # Nếu không có cửa sổ nào phía trên, đặt widget lên trên cùng
            user32.SetWindowPos(widget_hwnd, HWND_TOPMOST, 0, 0, 0, 0, 
                              SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE)
            # Sau đó đặt lại về trạng thái bình thường
            user32.SetWindowPos(widget_hwnd, HWND_NOTOPMOST, 0, 0, 0, 0, 
                              SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE)
    except Exception as e:
        print(f"Consolog [LỖI]: Lỗi khi đồng bộ Z-order: {e}")

def update_sam_mini_chat_position():
    global sam_mini_chat_win, widget_sam_mini_chat_thread_running
    while sam_mini_chat_win is not None and widget_sam_mini_chat_thread_running:
        try:
            hwnd = get_correct_telegram_hwnd()
            if hwnd:
                # Lấy trạng thái cửa sổ Telegram
                placement = WINDOWPLACEMENT()
                placement.length = ctypes.sizeof(WINDOWPLACEMENT)
                user32.GetWindowPlacement(hwnd, ctypes.byref(placement))
                
                # Kiểm tra xem Telegram có bị minimize không
                is_minimized = user32.IsIconic(hwnd)
                
                if is_minimized:
                    # Nếu Telegram bị minimize, ẩn widget
                    sam_mini_chat_win.withdraw()
                else:
                    # Nếu Telegram đang hiển thị, hiện widget và cập nhật vị trí
                    sam_mini_chat_win.deiconify()
                    
                    # Lấy vị trí và kích thước của cửa sổ Telegram
                    if placement.showCmd != 1:  # Không phải minimize
                        rect = placement.rcNormalPosition
                    else:
                        rect = ctypes.wintypes.RECT()
                        user32.GetWindowRect(hwnd, ctypes.byref(rect))
                    
                    window_width = rect.right - rect.left
                    widget_width = window_width
                    x = rect.left
                    y = rect.bottom + WIDGET_Y_OFFSET
                    
                    # Cập nhật vị trí và kích thước của widget
                    new_geometry = f"{widget_width}x{WIDGET_HEIGHT}+{x}+{y}"
                    sam_mini_chat_win.geometry(new_geometry)
                    
                    # Đồng bộ Z-order với Telegram
                    widget_hwnd = sam_mini_chat_win.winfo_id()
                    sync_z_order_with_telegram(hwnd, widget_hwnd)
            else:
                # Nếu không tìm thấy Telegram, ẩn widget
                sam_mini_chat_win.withdraw()
                
        except tk.TclError:
            break
        except Exception as e:
            print(f"Consolog [LỖI]: Lỗi khi cập nhật vị trí widget: {e}")
            
        time.sleep(0.1)  # Giảm thời gian sleep để cập nhật mượt hơn

def send_sam_mini_chat_message():
    global sam_mini_chat_entry, sam_mini_chat_btn_send
    if sam_mini_chat_entry is None:
        print("Consolog [LỖI]: sam_mini_chat_entry không tồn tại.")
        return
    msg = sam_mini_chat_entry.get("1.0", tk.END).strip()
    if not msg:
        print("Consolog: Không gửi vì tin nhắn rỗng.")
        return
    original_msg = msg
    sam_mini_chat_entry.delete("1.0", tk.END)
    hwnd = get_correct_telegram_hwnd()
    if hwnd is None:
        sam_mini_chat_entry.insert("1.0", original_msg)
        print("Consolog [LỖI]: Không tìm thấy Telegram active, khôi phục văn bản gốc.")
        return
    target_lang = hwnd_target_lang.get(hwnd, TARGET_LANG_SELECTION)

    sam_mini_chat_btn_send.config(text="Sending", state=tk.DISABLED)
    original_bg = sam_mini_chat_btn_send.cget("background")
    sam_mini_chat_btn_send.config(background="#90EE90")
    root.after(100, lambda: sam_mini_chat_btn_send.config(background=original_bg))
    root.after(200, lambda: sam_mini_chat_btn_send.config(background="#90EE90"))
    root.after(300, lambda: sam_mini_chat_btn_send.config(background=original_bg))

    def send_thread():
        try:
            translated = None
            if SELECTED_API == "XAI":
                translated, _ = translate_text_for_dialogue_xai(msg, source_lang="auto", target_lang=target_lang)
            elif SELECTED_API == "ChatGPT":
                translated, _ = translate_text_for_dialogue_chatgpt(msg, source_lang="auto", target_lang=target_lang)
            elif SELECTED_API == "LLM":
                translated, _ = translate_text_for_dialogue_llm(msg, source_lang="auto", target_lang=target_lang)
            
            if translated is None or translated == msg:
                raise Exception("Dịch thất bại, API không trả về bản dịch hợp lệ.")
                
            send_message_to_telegram_input(hwnd, translated)
            sam_mini_chat_entry.focus_force()
            print("Consolog: Gửi tin nhắn thành công qua Sam Mini Chat.")
        except Exception as e:
            root.after(0, lambda: sam_mini_chat_entry.delete("1.0", tk.END))
            root.after(0, lambda: sam_mini_chat_entry.insert("1.0", original_msg))
            print(f"Consolog [LỖI]: Widget lỗi (dịch hoặc gửi tin): {e}")
        finally:
            root.after(0, lambda: sam_mini_chat_btn_send.config(text="Send", state=tk.NORMAL))

    threading.Thread(target=send_thread, daemon=True).start()

def send_message_to_telegram_input(hwnd, message):
    rect = ctypes.wintypes.RECT()
    user32.GetWindowRect(hwnd, ctypes.byref(rect))
    width = rect.right - rect.left
    x = rect.left + width // 2
    y = rect.bottom - 3
    ctypes.windll.user32.SetCursorPos(x, y)
    time.sleep(0.1)
    ctypes.windll.user32.mouse_event(2, 0, 0, 0, 0)
    time.sleep(0.05)
    ctypes.windll.user32.mouse_event(4, 0, 0, 0, 0)
    time.sleep(0.1)
    root.clipboard_clear()
    root.clipboard_append(message)
    root.update()
    time.sleep(0.1)
    VK_CONTROL = 0x11
    VK_V = 0x56
    VK_RETURN = 0x0D
    ctypes.windll.user32.keybd_event(VK_CONTROL, 0, 0, 0)
    time.sleep(0.05)
    ctypes.windll.user32.keybd_event(VK_V, 0, 0, 0)
    time.sleep(0.05)
    ctypes.windll.user32.keybd_event(VK_V, 0, 2, 0)
    time.sleep(0.05)
    ctypes.windll.user32.keybd_event(VK_CONTROL, 0, 2, 0)
    time.sleep(0.1)
    ctypes.windll.user32.keybd_event(VK_RETURN, 0, 0, 0)
    time.sleep(0.05)
    ctypes.windll.user32.keybd_event(VK_RETURN, 0, 2, 0)
    time.sleep(0.1)

def get_correct_telegram_hwnd():
    global last_valid_telegram_hwnd
    hwnd_fore = user32.GetForegroundWindow()
    pid = ctypes.wintypes.DWORD()
    user32.GetWindowThreadProcessId(hwnd_fore, ctypes.byref(pid))
    try:
        proc = psutil.Process(pid.value)
        if proc.name().lower() == "telegram.exe" and not user32.IsIconic(hwnd_fore):
            last_valid_telegram_hwnd = hwnd_fore
            return hwnd_fore
    except Exception:
        pass
    if last_valid_telegram_hwnd is not None and not user32.IsIconic(last_valid_telegram_hwnd):
        return last_valid_telegram_hwnd
    hwnd_result = None
    EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_int, ctypes.c_int)
    def enum_windows_proc(hwnd, lParam):
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
                    last_valid_telegram_hwnd = hwnd
                    return False
            except Exception:
                pass
        return True
    enum_proc_c = EnumWindowsProc(enum_windows_proc)
    user32.EnumWindows(enum_proc_c, 0)
    return hwnd_result

class WINDOWPLACEMENT(ctypes.Structure):
    _fields_ = [
        ("length", ctypes.c_uint), ("flags", ctypes.c_uint), ("showCmd", ctypes.c_uint),
        ("ptMinPosition", ctypes.wintypes.POINT), ("ptMaxPosition", ctypes.wintypes.POINT),
        ("rcNormalPosition", ctypes.wintypes.RECT),
    ]

def remove_think_tags(text):
    return re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL).strip()

def translate_text_for_dialogue_xai(text, source_lang="auto", target_lang="vi"):
    global XAI_API_KEY
    if not XAI_API_KEY:
        print("Consolog [LỖI]: Khóa API XAI chưa set.")
        return text, None
    try:
        lang_name = lang_map.get(target_lang.lower(), target_lang)
        prompt = (
            f"Bạn là một công cụ dịch ngôn ngữ chuyên nghiệp. Nhiệm vụ của bạn là dịch tin nhắn sau từ {source_lang} sang {lang_name}. "
            f"Chỉ trả về bản dịch mà không thêm bất kỳ bình luận hoặc giải thích nào. "
            f"Tin nhắn: \"{text}\""
        )
        headers = {
            "Authorization": f"Bearer {XAI_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "grok-beta",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.05,
            "top_p": 0.9,
            "max_tokens": 2000
        }
        print(f"Consolog: Gửi yêu cầu dịch đến API XAI: {text[:50]}...")
        response = requests.post(
            "https://api.x.ai/v1/chat/completions",
            headers=headers,
            json=payload
        )
        if response.status_code == 200:
            data = response.json()
            translated_text = data["choices"][0]["message"]["content"].strip()
            translated_text = remove_think_tags(translated_text)
            print(f"Consolog: Nhận được bản dịch từ XAI: {translated_text[:50]}...")
            return translated_text, None
        else:
            print(f"Consolog [LỖI]: Lỗi API XAI (HTTP {response.status_code}): {response.text}")
            return text, None
    except Exception as e:
        print(f"Consolog [LỖI]: Lỗi khi gọi API XAI: {str(e)}")
        return text, None

def translate_text_for_dialogue_chatgpt(text, source_lang="auto", target_lang="vi"):
    global CHATGPT_API_KEY
    if not CHATGPT_API_KEY:
        print("Consolog [LỖI]: Khóa API ChatGPT chưa set.")
        return text, None
    try:
        lang_name = lang_map.get(target_lang.lower(), target_lang)
        prompt = (
            f"You are a professional language translator. Your task is to translate the following message from {source_lang} to {lang_name}. "
            f"Provide only the translation without any additional comments or explanations. "
            f"Message: \"{text}\""
        )
        headers = {
            "Authorization": f"Bearer {CHATGPT_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "gpt-4o",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.05,
            "top_p": 0.9,
            "max_tokens": 2000
        }
        print(f"Consolog: Gửi yêu cầu dịch đến API ChatGPT: {text[:50]}...")
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=payload
        )
        if response.status_code == 200:
            data = response.json()
            translated_text = data["choices"][0]["message"]["content"].strip()
            translated_text = remove_think_tags(translated_text)
            print(f"Consolog: Nhận được bản dịch từ ChatGPT: {translated_text[:50]}...")
            return translated_text, None
        else:
            print(f"Consolog [LỖI]: Lỗi API ChatGPT (HTTP {response.status_code}): {response.text}")
            return text, None
    except Exception as e:
        print(f"Consolog [LỖI]: Lỗi khi gọi API ChatGPT: {str(e)}")
        return text, None

def translate_text_for_dialogue_llm(text, source_lang="auto", target_lang="vi"):
    global LLM_API_KEY
    if not LLM_API_KEY:
        print("Consolog [LỖI]: Khóa API LLM chưa set.")
        return text, None
    ngrok_url = fetch_ngrok_url()
    if not ngrok_url:
        print("Consolog [LỖI]: Không thể lấy URL ngrok từ Firebase.")
        return text, None
    try:
        api_url = f"{ngrok_url}/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {LLM_API_KEY}"
        }
        lang_name = lang_map.get(target_lang.lower(), target_lang)
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
        print(f"Consolog: Gửi yêu cầu dịch đến API LLM: {text[:50]}...")
        response = requests.post(api_url, headers=headers, json=payload)
        if response.status_code == 200:
            data = response.json()
            translated_text = data["choices"][0]["message"]["content"].strip()
            translated_text = remove_think_tags(translated_text)
            print(f"Consolog: Nhận được bản dịch từ LLM: {translated_text[:50]}...")
            return translated_text, None
        else:
            print(f"Consolog [LỖI]: Lỗi API LLM (HTTP {response.status_code}): {response.text}")
            return text, None
    except Exception as e:
        print(f"Consolog [LỖI]: Lỗi khi gọi API LLM: {str(e)}")
        return text, None

def fetch_ngrok_url():
    global FIREBASE_URL
    if not FIREBASE_URL:
        FIREBASE_URL = prompt_for_firebase_url()
        if not FIREBASE_URL:
            print("Consolog [LỖI]: Người dùng không nhập FIREBASE_URL, không thể lấy ngrok URL.")
            return None
    try:
        print(f"Consolog: Gửi yêu cầu lấy ngrok URL từ: {FIREBASE_URL}")
        response = requests.get(FIREBASE_URL)
        if response.status_code == 200:
            url = response.json()
            if url:
                print(f"Consolog: Nhận được ngrok URL: {url}")
                return url
            else:
                raise ValueError("Ngrok URL is empty")
        else:
            raise Exception(f"Failed to fetch ngrok URL: {response.status_code}")
    except Exception as e:
        print(f"Consolog [LỖI]: Lỗi lấy ngrok URL: {e}")
        return None

def win_event_callback(hWinEventHook, event, hwnd, idObject, idChild, dwEventThread, dwmsEventTime):
    """Callback function để xử lý sự kiện thay đổi Z-order"""
    global sam_mini_chat_win
    try:
        if event == EVENT_OBJECT_REORDER or event == EVENT_SYSTEM_FOREGROUND:
            # Kiểm tra xem cửa sổ được kích hoạt có phải là Telegram không
            if hwnd == get_correct_telegram_hwnd():
                if sam_mini_chat_win and sam_mini_chat_win.winfo_exists():
                    # Đồng bộ lại Z-order của widget
                    widget_hwnd = sam_mini_chat_win.winfo_id()
                    sync_z_order_with_telegram(hwnd, widget_hwnd)
    except Exception as e:
        print(f"Consolog [LỖI]: Lỗi trong win_event_callback: {e}")

def setup_z_order_monitoring():
    """Thiết lập monitoring cho sự kiện thay đổi Z-order"""
    global z_order_callback
    try:
        # Định nghĩa kiểu callback
        WinEventProcType = ctypes.WINFUNCTYPE(
            None, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int
        )
        
        # Tạo callback
        z_order_callback = WinEventProcType(win_event_callback)
        
        # Đăng ký hook cho sự kiện
        user32.SetWinEventHook(
            EVENT_OBJECT_REORDER,
            EVENT_SYSTEM_FOREGROUND,
            0,
            z_order_callback,
            0,
            0,
            WINEVENT_OUTOFCONTEXT | WINEVENT_SKIPOWNTHREAD | WINEVENT_SKIPOWNPROCESS
        )
        
        print("Consolog: Đã thiết lập monitoring cho sự kiện Z-order")
    except Exception as e:
        print(f"Consolog [LỖI]: Lỗi khi thiết lập Z-order monitoring: {e}")