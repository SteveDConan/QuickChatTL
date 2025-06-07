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
from config import load_config  # Giả định bạn có file config.py
import re  # Để lọc <think> tags nếu cần

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

# Biến cấu hình kích thước cho Sam Translate
SAM_TRANSLATE_WIDTH = 700
SAM_TRANSLATE_HEIGHT = 400
SAM_TRANSLATE_X_OFFSET = 20
SAM_TRANSLATE_Y_OFFSET = 20
SAM_TRANSLATE_TEXT_HEIGHT = 15
SAM_TRANSLATE_TEXT_WIDTH = 35

# Biến cấu hình kích thước cho Sam Mini Chat
WIDGET_HEIGHT = 32
WIDGET_Y_OFFSET = 1

root = None
TRANSLATION_ONLY = True
DEFAULT_TARGET_LANG = "vi"

MY_LANG_SELECTION = "vi"
TARGET_LANG_SELECTION = DEFAULT_TARGET_LANG
SELECTED_API = "XAI"  # API mặc định

sam_mini_chat_win = None
sam_mini_chat_entry = None
sam_mini_chat_pause_button = None

last_valid_telegram_hwnd = None
widget_sam_mini_chat_thread_running = True

left_frame = None
right_frame = None
sam_translate_text = None
sam_translate_entry = None
my_lang_var = None
target_lang_var = None
translate_button = None
sam_translate_btn_send = None  # Nút Send cho Sam Translate
sam_mini_chat_btn_send = None  # Nút Send cho Sam Mini Chat
firebase_url_var = None

user32 = ctypes.windll.user32

all_lang_options = ["en", "vi", "fr", "es", "de", "zh", "km", "pt", "hi", "bn", "tl", "am", "ar", "id", "yo"]

lang_map = {
    "en": "tiếng Anh",
    "vi": "tiếng Việt",
    "fr": "tiếng Pháp",
    "es": "tiếng Tây Ban Nha",
    "de": "tiếng Đức",
    "zh": "tiếng Trung",
    "km": "tiếng Khmer",
    "pt": "tiếng Bồ Đào Nha",
    "hi": "tiếng Hindi",
    "bn": "tiếng Bengali",
    "tl": "tiếng Tagalog",
    "am": "tiếng Amharic",
    "ar": "tiếng Ả Rập",
    "id": "tiếng Indonesia",
    "yo": "tiếng Yoruba"
}

original_text = ""

print("Consolog: Đã bổ sung ngôn ngữ Yoruba (yo) vào all_lang_options và lang_map.")

def set_root(r):
    global root
    root = r
    print("Consolog: Đặt root window cho Sam Translate.")

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

def set_sam_translate_globals(xai_api_key, chatgpt_api_key, llm_api_key, translation_only_flag, default_lang):
    global XAI_API_KEY, CHATGPT_API_KEY, LLM_API_KEY, TRANSLATION_ONLY, DEFAULT_TARGET_LANG
    if xai_api_key and xai_api_key.startswith("xai-"):
        XAI_API_KEY = xai_api_key
    if chatgpt_api_key and chatgpt_api_key.startswith("sk-"):
        CHATGPT_API_KEY = chatgpt_api_key
    if llm_api_key and llm_api_key.startswith("llm-"):
        LLM_API_KEY = llm_api_key
    TRANSLATION_ONLY = translation_only_flag
    DEFAULT_TARGET_LANG = default_lang
    print(f"Consolog: Đã thiết lập API keys: XAI={XAI_API_KEY[:8] if XAI_API_KEY else None}..., ChatGPT={CHATGPT_API_KEY[:8] if CHATGPT_API_KEY else None}..., LLM={LLM_API_KEY[:8] if LLM_API_KEY else None}...")

def load_config_local():
    global MY_LANG_SELECTION, TARGET_LANG_SELECTION, SELECTED_API
    config = load_config()
    MY_LANG_SELECTION = config.get('MY_LANG_SELECTION', MY_LANG_SELECTION)
    TARGET_LANG_SELECTION = config.get('TARGET_LANG_SELECTION', TARGET_LANG_SELECTION)
    SELECTED_API = config.get('SELECTED_API', SELECTED_API)
    print(f"Consolog: Load cấu hình từ config.json: MY_LANG={MY_LANG_SELECTION}, TARGET_LANG={TARGET_LANG_SELECTION}, SELECTED_API={SELECTED_API}")

load_config_local()

sam_translate_win = None
sam_translate_text = None
sam_translate_entry = None

hwnd_target_lang = {}

def swap_frames():
    global MY_LANG_SELECTION, TARGET_LANG_SELECTION, my_lang_var, target_lang_var
    temp_lang = MY_LANG_SELECTION
    MY_LANG_SELECTION = TARGET_LANG_SELECTION
    TARGET_LANG_SELECTION = temp_lang
    if my_lang_var and target_lang_var:
        my_lang_var.set(MY_LANG_SELECTION)
        target_lang_var.set(TARGET_LANG_SELECTION)
    print(f"Consolog: Hoán đổi ngôn ngữ, MY_LANG={MY_LANG_SELECTION}, TARGET_LANG={TARGET_LANG_SELECTION}")

def create_sam_translate():
    global sam_translate_win, sam_translate_text, sam_translate_entry, TARGET_LANG_SELECTION, MY_LANG_SELECTION, SELECTED_API
    global left_frame, right_frame, my_lang_var, target_lang_var, translate_button, sam_translate_btn_send
    if root is None:
        print("Consolog [LỖI]: root chưa set. Gọi set_root(root).")
        return

    if sam_translate_win is not None and sam_translate_win.winfo_exists():
        print("Consolog: Hủy bỏ cửa sổ Sam Translate cũ trước khi tạo mới.")
        sam_translate_win.destroy()
    sam_translate_win = tk.Toplevel(root)
    sam_translate_win.title("Sam Translate")

    def on_closing():
        global sam_translate_win, sam_translate_text, sam_translate_entry
        sam_translate_win.destroy()
        sam_translate_win = None
        sam_translate_text = None
        sam_translate_entry = None
        print("Consolog: Cửa sổ Sam Translate đã bị đóng bởi người dùng.")

    sam_translate_win.protocol("WM_DELETE_WINDOW", on_closing)

    hwnd = get_correct_telegram_hwnd()
    if hwnd and not user32.IsIconic(hwnd):
        placement = WINDOWPLACEMENT()
        placement.length = ctypes.sizeof(WINDOWPLACEMENT)
        user32.GetWindowPlacement(hwnd, ctypes.byref(placement))
        if placement.showCmd != 1:
            rect = placement.rcNormalPosition
        else:
            rect = ctypes.wintypes.RECT()
            user32.GetWindowRect(hwnd, ctypes.byref(rect))
        window_width = rect.right - rect.left
        x = rect.right + 10
        y = rect.top
    else:
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        x = screen_width - SAM_TRANSLATE_WIDTH - SAM_TRANSLATE_X_OFFSET
        y = screen_height - SAM_TRANSLATE_HEIGHT - SAM_TRANSLATE_Y_OFFSET

    sam_translate_win.geometry(f"{SAM_TRANSLATE_WIDTH}x{SAM_TRANSLATE_HEIGHT}+{x}+{y}")
    sam_translate_win.attributes("-topmost", True)

    menu_frame = tk.Frame(sam_translate_win)
    menu_frame.pack(side=tk.TOP, fill=tk.X, pady=5)
    tk.Label(menu_frame, text="Ngôn ngữ của tôi:").pack(side=tk.LEFT, padx=5)
    my_lang_var = tk.StringVar(value=MY_LANG_SELECTION)
    my_lang_options = all_lang_options
    def update_my_lang(val):
        global MY_LANG_SELECTION
        MY_LANG_SELECTION = val
        print(f"Consolog: Cập nhật ngôn ngữ của tôi: {MY_LANG_SELECTION}")
    my_lang_menu = tk.OptionMenu(menu_frame, my_lang_var, *my_lang_options, command=update_my_lang)
    my_lang_menu.pack(side=tk.LEFT, padx=5)
    tk.Label(menu_frame, text="Ngôn ngữ đối phương:").pack(side=tk.LEFT, padx=5)
    target_lang_var = tk.StringVar(value=TARGET_LANG_SELECTION)
    target_lang_options = all_lang_options
    def update_target_lang(val):
        global TARGET_LANG_SELECTION
        TARGET_LANG_SELECTION = val
        print(f"Consolog: Cập nhật ngôn ngữ đối phương: {TARGET_LANG_SELECTION}")
    target_lang_menu = tk.OptionMenu(menu_frame, target_lang_var, *target_lang_options, command=update_target_lang)
    target_lang_menu.pack(side=tk.LEFT, padx=5)
    tk.Label(menu_frame, text="API:").pack(side=tk.LEFT, padx=5)
    api_var = tk.StringVar(value=SELECTED_API)
    api_options = ["XAI", "ChatGPT", "LLM"]
    def update_api(val):
        global SELECTED_API
        SELECTED_API = val
        print(f"Consolog: Cập nhật API: {SELECTED_API}")
    api_menu = tk.OptionMenu(menu_frame, api_var, *api_options, command=update_api)
    api_menu.pack(side=tk.LEFT, padx=5)

    save_button = tk.Button(menu_frame, text="Save", command=save_config)
    save_button.pack(side=tk.LEFT, padx=5)

    main_frame = tk.Frame(sam_translate_win)
    main_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

    left_frame = tk.Frame(main_frame)
    left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
    sam_translate_entry = tk.Text(left_frame, height=SAM_TRANSLATE_TEXT_HEIGHT, width=SAM_TRANSLATE_TEXT_WIDTH, wrap=tk.WORD)
    sam_translate_entry.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
    sam_translate_entry.bind("<Return>", lambda event: send_sam_translate_message())

    right_frame = tk.Frame(main_frame)
    right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
    scrollbar = tk.Scrollbar(right_frame, orient=tk.VERTICAL)
    sam_translate_text = tk.Text(right_frame, height=SAM_TRANSLATE_TEXT_HEIGHT, width=SAM_TRANSLATE_TEXT_WIDTH, wrap=tk.WORD, state=tk.DISABLED, yscrollcommand=scrollbar.set)
    scrollbar.config(command=sam_translate_text.yview)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    sam_translate_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    button_frame = tk.Frame(sam_translate_win)
    button_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=5)
    button_subframe = tk.Frame(button_frame)
    button_subframe.pack(anchor=tk.CENTER)
    sam_translate_btn_send = tk.Button(button_subframe, text="Send", command=send_sam_translate_message)
    sam_translate_btn_send.pack(side=tk.LEFT, padx=5, pady=5)
    translate_button = tk.Button(button_subframe, text="Translate", command=trigger_translation)
    translate_button.pack(side=tk.LEFT, padx=5, pady=5)
    btn_clear = tk.Button(button_subframe, text="Clear", command=clear_sam_translate)
    btn_clear.pack(side=tk.LEFT, padx=5, pady=5)
    btn_swap = tk.Button(button_subframe, text="Swap", command=swap_frames)
    btn_swap.pack(side=tk.LEFT, padx=5, pady=5)

def trigger_translation():
    global original_text, sam_translate_entry, sam_translate_text, translate_button, SELECTED_API
    original_text = sam_translate_entry.get("1.0", tk.END).strip()
    msg = original_text
    if not msg:
        append_sam_translate("Sam Translate [LỖI]: Vui lòng nhập văn bản để dịch.")
        return
    hwnd = get_correct_telegram_hwnd()
    if hwnd is None:
        append_sam_translate("Sam Translate [LỖI]: Không tìm thấy Telegram active.")
        return

    if translate_button:
        translate_button.config(text="Translating", state=tk.DISABLED)

    def translate_in_thread():
        if SELECTED_API == "XAI":
            translated, _ = translate_text_for_paragraph_xai(msg, source_lang=MY_LANG_SELECTION, target_lang=TARGET_LANG_SELECTION)
        elif SELECTED_API == "ChatGPT":
            translated, _ = translate_text_for_paragraph_chatgpt(msg, source_lang=MY_LANG_SELECTION, target_lang=TARGET_LANG_SELECTION)
        elif SELECTED_API == "LLM":
            translated, _ = translate_text_for_paragraph_llm(msg, source_lang=MY_LANG_SELECTION, target_lang=TARGET_LANG_SELECTION)
        root.after(0, lambda: update_ui_after_translation(translated))

    def update_ui_after_translation(translated):
        sam_translate_text.config(state=tk.NORMAL)
        sam_translate_text.delete("1.0", tk.END)
        append_sam_translate(f"Translated:\n{translated}")
        sam_translate_text.config(state=tk.DISABLED)
        if translate_button:
            translate_button.config(text="Translate", state=tk.NORMAL)

    threading.Thread(target=translate_in_thread, daemon=True).start()

def clear_sam_translate():
    global sam_translate_text, sam_translate_entry
    if sam_translate_text is not None:
        sam_translate_text.config(state=tk.NORMAL)
        sam_translate_text.delete("1.0", tk.END)
    if sam_translate_entry is not None:
        sam_translate_entry.delete("1.0", tk.END)

def append_sam_translate(text):
    global sam_translate_text
    if sam_translate_text is None:
        return
    sam_translate_text.config(state=tk.NORMAL)
    sam_translate_text.insert(tk.END, text + "\n")
    sam_translate_text.see(tk.END)
    sam_translate_text.config(state=tk.DISABLED)

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

def remove_think_tags(text):
    return re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL).strip()

def translate_text_for_paragraph_xai(text, source_lang="auto", target_lang="vi", conversation_context=""):
    global XAI_API_KEY
    if not XAI_API_KEY:
        error_msg = "Sam Translate [LỖI]: Khóa API XAI chưa set."
        append_sam_translate(error_msg)
        return text, None
    try:
        lang_name = lang_map.get(target_lang.lower(), target_lang)
        prompt = (
            f"Bạn là một công cụ dịch ngôn ngữ chuyên nghiệp. Nhiệm vụ duy nhất của bạn là dịch đoạn văn dưới đây từ {source_lang} sang {lang_name}, giữ nguyên định dạng của văn bản gốc, bao gồm xuống dòng, khoảng cách và cấu trúc đoạn. "
            f"Tuân theo các nguyên tắc sau:\n"
            f"1. Chỉ trả về bản dịch thuần túy, không thêm bất kỳ bình luận, ghi chú (như '[Translated]'), hoặc nội dung không liên quan.\n"
            f"2. Giữ nguyên định dạng của văn bản gốc: nếu văn bản gốc có xuống dòng, bản dịch phải giữ đúng số dòng và vị trí xuống dòng; nếu có khoảng cách hoặc tab, bản dịch cũng phải giữ tương ứng.\n"
            f"3. Dịch từng đoạn, từng dòng một cách chính xác, không thay đổi ý nghĩa, phong cách hoặc cấu trúc của văn bản gốc.\n"
            f"4. Sử dụng từ ngữ chuẩn mực, phù hợp với ngữ cảnh của đoạn văn.\n"
            f"5. Không trả về dòng rỗng hoặc nội dung không có ý nghĩa ngoài bản dịch.\n"
            f"6. Nếu văn bản gốc không rõ ràng, dịch theo nghĩa sát nhất có thể mà không thay đổi định dạng.\n\n"
            f"Nội dung cần dịch:\n{text}\n"
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
            error_msg = f"Sam Translate [LỖI]: Lỗi API XAI (HTTP {response.status_code}): {response.text}"
            append_sam_translate(error_msg)
            return text, None
    except Exception as e:
        error_msg = f"Sam Translate [LỖI]: Lỗi khi gọi API XAI: {str(e)}"
        append_sam_translate(error_msg)
        return text, None

def translate_text_for_paragraph_chatgpt(text, source_lang="auto", target_lang="vi", conversation_context=""):
    global CHATGPT_API_KEY
    if not CHATGPT_API_KEY:
        error_msg = "Sam Translate [LỖI]: Khóa API ChatGPT chưa set."
        append_sam_translate(error_msg)
        return text, None
    try:
        lang_name = lang_map.get(target_lang.lower(), target_lang)
        prompt = (
            f"Translate the following paragraph from {source_lang} to {lang_name}, maintaining the original format, including line breaks, spacing, and paragraph structure. "
            f"Follow these guidelines:\n"
            f"1. Only return the pure translation, without any comments, notes (like '[Translated]'), or unrelated content.\n"
            f"2. Preserve the original format: if the original text has line breaks, the translation must maintain the same number of lines and break positions; if there are spaces or tabs, the translation must also keep them accordingly.\n"
            f"3. Translate each paragraph and line accurately, without changing the meaning, style, or structure of the original text.\n"
            f"4. Use standard vocabulary appropriate for the context of the paragraph.\n"
            f"5. Do not return empty lines or meaningless content beyond the translation.\n"
            f"6. If the original text is unclear, translate as closely as possible without altering the format.\n\n"
            f"Text to translate:\n{text}\n"
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
            error_msg = f"Sam Translate [LỖI]: Lỗi API ChatGPT (HTTP {response.status_code}): {response.text}"
            append_sam_translate(error_msg)
            return text, None
    except Exception as e:
        error_msg = f"Sam Translate [LỖI]: Lỗi khi gọi API ChatGPT: {str(e)}"
        append_sam_translate(error_msg)
        return text, None

def translate_text_for_paragraph_llm(text, source_lang="auto", target_lang="vi", conversation_context=""):
    global LLM_API_KEY
    if not LLM_API_KEY:
        error_msg = "Sam Translate [LỖI]: Khóa API LLM chưa set."
        append_sam_translate(error_msg)
        return text, None
    ngrok_url = fetch_ngrok_url()
    if not ngrok_url:
        error_msg = "Sam Translate [LỖI]: Không thể lấy URL ngrok từ Firebase."
        append_sam_translate(error_msg)
        return text, None
    try:
        api_url = f"{ngrok_url}/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {LLM_API_KEY}"
        }
        lang_name = lang_map.get(target_lang.lower(), target_lang)
        prompt = (
            f"Translate the following paragraph from {source_lang} to {lang_name}, maintaining the original format, including line breaks, spacing, and paragraph structure. "
            f"Follow these guidelines:\n"
            f"1. Only return the pure translation, without any comments, notes (like '[Translated]'), or unrelated content.\n"
            f"2. Preserve the original format: if the original text has line breaks, the translation must maintain the same number of lines and break positions; if there are spaces or tabs, the translation must also keep them accordingly.\n"
            f"3. Translate each paragraph and line accurately, without changing the meaning, style, or structure of the original text.\n"
            f"4. Use standard vocabulary appropriate for the context of the paragraph.\n"
            f"5. Do not return empty lines or meaningless content beyond the translation.\n"
            f"6. If the original text is unclear, translate as closely as possible without altering the format.\n\n"
            f"Text to translate:\n{text}\n"
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
            error_msg = f"Sam Translate [LỖI]: Lỗi API LLM (HTTP {response.status_code}): {response.text}"
            append_sam_translate(error_msg)
            return text, None
    except Exception as e:
        error_msg = f"Sam Translate [LỖI]: Lỗi khi gọi API LLM: {str(e)}"
        append_sam_translate(error_msg)
        return text, None

def translate_text_for_dialogue_xai(text, source_lang="auto", target_lang="vi", conversation_context=""):
    global XAI_API_KEY
    if not XAI_API_KEY:
        error_msg = "Sam Translate [LỖI]: Khóa API XAI chưa set."
        append_sam_translate(error_msg)
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
            error_msg = f"Sam Translate [LỖI]: Lỗi API XAI (HTTP {response.status_code}): {response.text}"
            append_sam_translate(error_msg)
            return text, None
    except Exception as e:
        error_msg = f"Sam Translate [LỖI]: Lỗi khi gọi API XAI: {str(e)}"
        append_sam_translate(error_msg)
        return text, None

def translate_text_for_dialogue_chatgpt(text, source_lang="auto", target_lang="vi", conversation_context=""):
    global CHATGPT_API_KEY
    if not CHATGPT_API_KEY:
        error_msg = "Sam Translate [LỖI]: Khóa API ChatGPT chưa set."
        append_sam_translate(error_msg)
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
            error_msg = f"Sam Translate [LỖI]: Lỗi API ChatGPT (HTTP {response.status_code}): {response.text}"
            append_sam_translate(error_msg)
            return text, None
    except Exception as e:
        error_msg = f"Sam Translate [LỖI]: Lỗi khi gọi API ChatGPT: {str(e)}"
        append_sam_translate(error_msg)
        return text, None

def translate_text_for_dialogue_llm(text, source_lang="auto", target_lang="vi", conversation_context=""):
    global LLM_API_KEY
    if not LLM_API_KEY:
        error_msg = "Sam Translate [LỖI]: Khóa API LLM chưa set."
        append_sam_translate(error_msg)
        return text, None
    ngrok_url = fetch_ngrok_url()
    if not ngrok_url:
        error_msg = "Sam Translate [LỖI]: Không thể lấy URL ngrok từ Firebase."
        append_sam_translate(error_msg)
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
            error_msg = f"Sam Translate [LỖI]: Lỗi API LLM (HTTP {response.status_code}): {response.text}"
            append_sam_translate(error_msg)
            return text, None
    except Exception as e:
        error_msg = f"Sam Translate [LỖI]: Lỗi khi gọi API LLM: {str(e)}"
        append_sam_translate(error_msg)
        return text, None

def send_sam_translate_message():
    global sam_translate_text, hwnd_target_lang, TARGET_LANG_SELECTION, sam_translate_btn_send
    translated_text = sam_translate_text.get("1.0", tk.END).strip()
    if not translated_text.startswith("Translated:"):
        append_sam_translate("Sam Translate [LỖI]: Vui lòng dịch văn bản trước khi gửi.")
        return
    translated_text = translated_text.replace("Translated:\n", "").strip()
    if not translated_text:
        append_sam_translate("Sam Translate [LỖI]: Không có văn bản đã dịch để gửi.")
        return
    hwnd = get_correct_telegram_hwnd()
    if hwnd is None:
        append_sam_translate("Sam Translate [LỖI]: Không tìm thấy Telegram active.")
        return

    sam_translate_btn_send.config(text="Sending...", state=tk.DISABLED)

    def send_thread():
        try:
            send_message_to_telegram_input(hwnd, translated_text)
            time.sleep(0.1)
            if sam_translate_win:
                sam_translate_win.lift()
        except Exception as e:
            root.after(0, lambda: sam_translate_entry.delete("1.0", tk.END))
            root.after(0, lambda: sam_translate_entry.insert(tk.END, original_text))
            append_sam_translate(f"Sam Translate [LỖI]: Lỗi gửi tin: {e}")
        finally:
            root.after(0, lambda: sam_translate_btn_send.config(text="Send", state=tk.NORMAL))

    threading.Thread(target=send_thread, daemon=True).start()

def save_config():
    global MY_LANG_SELECTION, TARGET_LANG_SELECTION, SELECTED_API
    try:
        config = load_config()
        config['MY_LANG_SELECTION'] = MY_LANG_SELECTION
        config['TARGET_LANG_SELECTION'] = TARGET_LANG_SELECTION
        config['SELECTED_API'] = SELECTED_API
        with open("config.json", "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=4)
        for hwnd in list(hwnd_target_lang.keys()):
            hwnd_target_lang[hwnd] = TARGET_LANG_SELECTION
        append_sam_translate("Cài đặt ngôn ngữ và API đã lưu.")
        print("Consolog: Đã lưu cấu hình ngôn ngữ và API vào config.json")
    except Exception as e:
        append_sam_translate(f"Sam Translate [LỖI]: Lỗi lưu config: {e}")
        print(f"Consolog [ERROR]: Lỗi lưu cấu hình: {e}")

def destroy_sam_translate():
    global sam_translate_win, sam_translate_text, sam_translate_entry
    if sam_translate_win is not None:
        try:
            if sam_translate_win.winfo_exists():
                sam_translate_win.destroy()
            sam_translate_win = None
            sam_translate_text = None
            sam_translate_entry = None
        except tk.TclError:
            sam_translate_win = None
            sam_translate_text = None
            sam_translate_entry = None

class WINDOWPLACEMENT(ctypes.Structure):
    _fields_ = [
        ("length", ctypes.c_uint), ("flags", ctypes.c_uint), ("showCmd", ctypes.c_uint),
        ("ptMinPosition", ctypes.wintypes.POINT), ("ptMaxPosition", ctypes.wintypes.POINT),
        ("rcNormalPosition", ctypes.wintypes.RECT),
    ]

def create_sam_mini_chat():
    global sam_mini_chat_win, sam_mini_chat_entry, sam_mini_chat_btn_send
    if root is None:
        print("Consolog [LỖI]: root chưa set. Gọi set_root(root).")
        return
    sam_mini_chat_win = tk.Toplevel(root)
    sam_mini_chat_win.title("Sam Mini Chat")
    sam_mini_chat_win.overrideredirect(True)
    sam_mini_chat_win.attributes("-topmost", False)
    sam_mini_chat_win.geometry(f"400x{WIDGET_HEIGHT}+0+0")
    sam_mini_chat_win.withdraw()
    frame = tk.Frame(sam_mini_chat_win)
    frame.pack(fill=tk.BOTH, expand=True)
    sam_mini_chat_entry = tk.Entry(frame)
    sam_mini_chat_entry.grid(row=0, column=0, sticky="we", padx=(5, 2), pady=5)
    frame.columnconfigure(0, weight=1)
    sam_mini_chat_entry.bind("<Return>", lambda event: send_sam_mini_chat_message())
    sam_mini_chat_btn_send = tk.Button(frame, text="Send", command=send_sam_mini_chat_message, width=8)
    sam_mini_chat_btn_send.grid(row=0, column=1, padx=2, sticky="e")
    btn_quit = tk.Button(frame, text="Quit", command=destroy_sam_mini_chat, width=8)
    btn_quit.grid(row=0, column=2, padx=2, sticky="e")

    create_sam_translate()
    threading.Thread(target=update_sam_mini_chat_position, daemon=True).start()
    print("Consolog: Đã tạo widget Sam Mini Chat với nút Send riêng biệt.")

def send_sam_mini_chat_message():
    global sam_mini_chat_entry, sam_mini_chat_btn_send
    if sam_mini_chat_entry is None:
        print("Consolog [LỖI]: sam_mini_chat_entry không tồn tại.")
        return
    msg = sam_mini_chat_entry.get().strip()
    if not msg:
        print("Consolog: Không gửi vì tin nhắn rỗng.")
        return
    original_msg = msg
    sam_mini_chat_entry.delete(0, tk.END)
    hwnd = get_correct_telegram_hwnd()
    if hwnd is None:
        sam_mini_chat_entry.insert(0, original_msg)
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
            root.after(0, lambda: sam_mini_chat_entry.delete(0, tk.END))
            root.after(0, lambda: sam_mini_chat_entry.insert(0, original_msg))
            print(f"Consolog [LỖI]: Widget lỗi (dịch hoặc gửi tin): {e}")
        finally:
            root.after(0, lambda: sam_mini_chat_btn_send.config(text="Send", state=tk.NORMAL))

    threading.Thread(target=send_thread, daemon=True).start()

def destroy_sam_mini_chat():
    global sam_mini_chat_win, widget_sam_mini_chat_thread_running
    destroy_sam_translate()
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

def update_sam_mini_chat_position():
    global sam_mini_chat_win, widget_sam_mini_chat_thread_running
    while sam_mini_chat_win is not None and widget_sam_mini_chat_thread_running:
        try:
            sam_mini_chat_win.update_idletasks()
            hwnd = get_correct_telegram_hwnd()
            if hwnd and not user32.IsIconic(hwnd):
                sam_mini_chat_win.deiconify()
                placement = WINDOWPLACEMENT()
                placement.length = ctypes.sizeof(WINDOWPLACEMENT)
                user32.GetWindowPlacement(hwnd, ctypes.byref(placement))
                if placement.showCmd != 1:
                    rect = placement.rcNormalPosition
                else:
                    rect = ctypes.wintypes.RECT()
                    user32.GetWindowRect(hwnd, ctypes.byref(rect))
                window_width = rect.right - rect.left
                widget_width = window_width
                x = rect.left
                y = rect.bottom + WIDGET_Y_OFFSET
                new_geometry = f"{widget_width}x{WIDGET_HEIGHT}+{x}+{y}"
                sam_mini_chat_win.geometry(new_geometry)
                sam_mini_chat_win.lift()
            else:
                sam_mini_chat_win.withdraw()
        except tk.TclError:
            break
        time.sleep(0.5)

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