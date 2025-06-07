# mini_chat.py

# Consolog: Đã cập nhật để sử dụng xAI thay vì OpenAI
# Consolog: Loại bỏ mọi tham chiếu đến ChatGPT, đảm bảo chỉ gọi API xAI
# Consolog [THAY ĐỔI 2025-05-11]: Chia cửa sổ Mini Chat thành hai nửa trái/phải, thay nút X-AI thành Translate, thêm nút Swap
# Consolog [THAY ĐỔI 2025-05-12]: Thiết kế lại giao diện Mini Chat với 2 ô bằng nhau (trái: nhập, phải: hiển thị), đảm bảo chức năng dịch
# Consolog [THAY ĐỔI 2025-05-13]: Dịch ăn theo cấu hình MY_LANG và TARGET_LANG, Swap đổi ngôn ngữ, căn giữa các nút
# Consolog [THAY ĐỔI 2025-05-14]: Swap chỉ đổi ngôn ngữ, không đổi vị trí ô nhập liệu và hiển thị
# Consolog [THAY ĐỔI 2025-05-15]: Cập nhật prompt cho Translate để dịch giữ nguyên định dạng, hỗ trợ copy/paste văn bản
# Consolog [THAY ĐỔI 2025-05-16]: Thêm thanh cuộn cho ô hiển thị, tăng max_tokens để không giới hạn kết quả dịch
# Consolog [THAY ĐỔI 2025-05-19]: Tách prompt cho nút Translate và Send, tối ưu cho đoạn văn dài và đoạn thoại ngắn
# Consolog [THAY ĐỔI 2025-05-20]: Thêm biến điều chỉnh kích thước và căn chỉnh giao diện Mini Chat và Mini xAI Widget
# Consolog [THAY ĐỔI 2025-05-21]: Không khóa giao diện khi dịch, nút Translate đổi thành Translating và trở lại Translate khi hoàn tất
# Consolog [THAY ĐỔI 2025-05-22]: Tự động mở Mini Chat cùng Mini xAI Widget, đặt Mini Chat bên phải Telegram
# Consolog [THAY ĐỔI 2025-05-23]: Sửa lỗi bấm Zoom tạo cửa sổ Mini Chat mới, chỉ di chuyển hoặc khôi phục cửa sổ hiện có
# Consolog [THAY ĐỔI 2025-05-24]: Cải thiện quản lý cửa sổ Mini Chat để đảm bảo không tạo cửa sổ dư thừa khi bấm Zoom
# Consolog [THAY ĐỔI 2025-05-25]: Sau khi bấm Send trên Mini Chat, con trỏ chuột quay lại vị trí ban đầu
# Consolog [THAY ĐỔI 2025-05-26]: Khôi phục nút thu nhỏ và phóng to trên cửa sổ Mini Chat
# Consolog [THAY ĐỔI 2025-05-27]: Bổ sung hỗ trợ tiếng Hindi (hi)
# Consolog [THAY ĐỔI 2025-05-11]: Loại bỏ mini_chat_monitor, DPI_ENABLED, translation_logs để tối ưu mã

import os
import sys
import requests
import json
import threading
import time
import tkinter as tk
from tkinter import messagebox
import ctypes
import math

try:
    import psutil
except ImportError:
    psutil = None

# Biến điều chỉnh kích thước cho Mini Chat
MINI_CHAT_WIDTH = 700  # Chiều rộng cửa sổ Mini Chat (pixels)
MINI_CHAT_HEIGHT = 400  # Chiều cao cửa sổ Mini Chat (pixels)
MINI_CHAT_X_OFFSET = 20  # Khoảng cách từ cạnh phải màn hình (pixels)
MINI_CHAT_Y_OFFSET = 20  # Khoảng cách từ cạnh dưới màn hình (pixels)
MINI_CHAT_TEXT_HEIGHT = 15  # Chiều cao của ô nhập và ô hiển thị (số dòng)
MINI_CHAT_TEXT_WIDTH = 35  # Chiều rộng của ô nhập và ô hiển thị (số ký tự)

# Biến điều chỉnh kích thước cho Mini xAI Widget
WIDGET_HEIGHT = 32  # Chiều cao thanh widget (pixels)
WIDGET_Y_OFFSET = 10  # Khoảng cách từ đỉnh cửa sổ Telegram (pixels)

root = None
XAI_API_KEY = None
TRANSLATION_ONLY = True
DEFAULT_TARGET_LANG = "vi"

MY_LANG_SELECTION = "vi"
TARGET_LANG_SELECTION = DEFAULT_TARGET_LANG

mini_xai_win = None
mini_xai_entry = None
mini_xai_pause_button = None

last_valid_telegram_hwnd = None
widget_mini_chat_thread_running = True

# Các biến để quản lý trạng thái hoán đổi
left_frame = None
right_frame = None
mini_chat_text = None  # Ô hiển thị văn bản dịch
mini_chat_entry = None  # Ô nhập văn bản
my_lang_var = None  # Biến lưu trữ giá trị menu "Ngôn ngữ của tôi"
target_lang_var = None  # Biến lưu trữ giá trị menu "Ngôn ngữ đối phương"
translate_button = None  # Biến lưu trữ nút Translate

print("Consolog: Khởi tạo widget_mini_chat_thread_running = True.")

def set_root(r):
    global root
    root = r

def set_mini_chat_globals(api_key, translation_only_flag, default_lang):
    global XAI_API_KEY, TRANSLATION_ONLY, DEFAULT_TARGET_LANG
    if not api_key or not api_key.startswith("xai-"):
        error_msg = "Mini Chat [LỖI]: Khóa API xAI không hợp lệ hoặc rỗng."
        print(f"Consolog [LỖI]: {error_msg}")
        append_mini_chat(error_msg)
        raise ValueError(error_msg)
    XAI_API_KEY = api_key
    TRANSLATION_ONLY = translation_only_flag
    DEFAULT_TARGET_LANG = default_lang
    print(f"Consolog: Đã thiết lập XAI_API_KEY: {XAI_API_KEY[:8]}...")

def load_config():
    global MY_LANG_SELECTION, TARGET_LANG_SELECTION
    config_file = os.path.join(os.getcwd(), "config.ini")
    if os.path.exists(config_file):
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or "=" not in line:
                        continue
                    key, value = line.split("=", 1)
                    if key == "MY_LANG_SELECTION":
                        MY_LANG_SELECTION = value
                    elif key == "TARGET_LANG_SELECTION":
                        TARGET_LANG_SELECTION = value
            print("Consolog: Load cấu hình từ config.ini")
        except Exception as e:
            print(f"Consolog [LỖI]: Lỗi load config: {e}")
    else:
        print("Consolog: Không tìm thấy config.ini, dùng mặc định")

load_config()

mini_chat_win = None
mini_chat_text = None
mini_chat_entry = None

hwnd_target_lang = {}

user32 = ctypes.windll.user32

def swap_frames():
    global MY_LANG_SELECTION, TARGET_LANG_SELECTION, my_lang_var, target_lang_var
    # Hoán đổi ngôn ngữ
    temp_lang = MY_LANG_SELECTION
    MY_LANG_SELECTION = TARGET_LANG_SELECTION
    TARGET_LANG_SELECTION = temp_lang
    # Cập nhật giao diện menu
    if my_lang_var and target_lang_var:
        my_lang_var.set(MY_LANG_SELECTION)
        target_lang_var.set(TARGET_LANG_SELECTION)
    print(f"Consolog: Hoán đổi ngôn ngữ, MY_LANG={MY_LANG_SELECTION}, TARGET_LANG={TARGET_LANG_SELECTION}")

def create_mini_chat():
    global mini_chat_win, mini_chat_text, mini_chat_entry, TARGET_LANG_SELECTION, MY_LANG_SELECTION
    global left_frame, right_frame, my_lang_var, target_lang_var, translate_button
    if root is None:
        print("Consolog [LỖI]: root chưa set. Gọi set_root(root).")
        return

    # Hủy bỏ cửa sổ Mini Chat cũ nếu tồn tại
    if mini_chat_win is not None and mini_chat_win.winfo_exists():
        print("Consolog: Hủy bỏ cửa sổ Mini Chat cũ trước khi tạo mới.")
        mini_chat_win.destroy()
    mini_chat_win = tk.Toplevel(root)
    mini_chat_win.title("Mini Chat")

    # Xử lý khi cửa sổ bị đóng
    def on_closing():
        global mini_chat_win, mini_chat_text, mini_chat_entry
        mini_chat_win.destroy()
        mini_chat_win = None
        mini_chat_text = None
        mini_chat_entry = None
        print("Consolog: Cửa sổ Mini Chat đã bị đóng bởi người dùng.")

    mini_chat_win.protocol("WM_DELETE_WINDOW", on_closing)

    # Lấy thông tin cửa sổ Telegram để định vị Mini Chat
    hwnd = get_correct_telegram_hwnd()
    if hwnd and not user32.IsIconic(hwnd):
        placement = WINDOWPLACEMENT()
        placement.length = ctypes.sizeof(WINDOWPLACEMENT)
        user32.GetWindowPlacement(hwnd, ctypes.byref(placement))
        if placement.showCmd != 1:
            rect = placement.rcNormalPosition
            print("Consolog: Telegram không bình thường, dùng rcNormalPosition.")
        else:
            rect = ctypes.wintypes.RECT()
            user32.GetWindowRect(hwnd, ctypes.byref(rect))
        window_width = rect.right - rect.left
        # Đặt Mini Chat ngay bên phải cửa sổ Telegram
        x = rect.right + 10  # 10px khoảng cách bên phải Telegram
        y = rect.top  # Cùng độ cao với đỉnh Telegram
    else:
        # Nếu không tìm thấy Telegram, đặt mặc định ở góc dưới bên phải
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        x = screen_width - MINI_CHAT_WIDTH - MINI_CHAT_X_OFFSET
        y = screen_height - MINI_CHAT_HEIGHT - MINI_CHAT_Y_OFFSET

    mini_chat_win.geometry(f"{MINI_CHAT_WIDTH}x{MINI_CHAT_HEIGHT}+{x}+{y}")
    mini_chat_win.attributes("-topmost", True)

    # Frame menu
    menu_frame = tk.Frame(mini_chat_win)
    menu_frame.pack(side=tk.TOP, fill=tk.X, pady=5)
    tk.Label(menu_frame, text="Ngôn ngữ của tôi:").pack(side=tk.LEFT, padx=5)
    my_lang_var = tk.StringVar(value=MY_LANG_SELECTION)
    my_lang_options = ["en", "vi", "fr", "es", "de", "zh", "km", "pt", "hi"]  # Thêm tiếng Hindi
    def update_my_lang(val):
        global MY_LANG_SELECTION
        MY_LANG_SELECTION = val
        print(f"Consolog: Cập nhật ngôn ngữ của tôi: {MY_LANG_SELECTION}")
    my_lang_menu = tk.OptionMenu(menu_frame, my_lang_var, *my_lang_options, command=update_my_lang)
    my_lang_menu.pack(side=tk.LEFT, padx=5)
    tk.Label(menu_frame, text="Ngôn ngữ đối phương:").pack(side=tk.LEFT, padx=5)
    target_lang_var = tk.StringVar(value=TARGET_LANG_SELECTION)
    target_lang_options = ["vi", "en", "fr", "es", "de", "zh", "km", "pt", "hi"]  # Thêm tiếng Hindi
    def update_target_lang(val):
        global TARGET_LANG_SELECTION
        TARGET_LANG_SELECTION = val
        print(f"Consolog: Cập nhật ngôn ngữ đối phương: {TARGET_LANG_SELECTION}")
    target_lang_menu = tk.OptionMenu(menu_frame, target_lang_var, *target_lang_options, command=update_target_lang)
    target_lang_menu.pack(side=tk.LEFT, padx=5)
    save_button = tk.Button(menu_frame, text="Save", command=save_config)
    save_button.pack(side=tk.LEFT, padx=5)

    # Frame chính chứa hai ô trái và phải
    main_frame = tk.Frame(mini_chat_win)
    main_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

    # Frame trái (ô nhập văn bản)
    left_frame = tk.Frame(main_frame)
    left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
    mini_chat_entry = tk.Text(left_frame, height=MINI_CHAT_TEXT_HEIGHT, width=MINI_CHAT_TEXT_WIDTH, wrap=tk.WORD)
    mini_chat_entry.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
    mini_chat_entry.bind("<Return>", lambda event: send_mini_chat_message())

    # Frame phải (ô hiển thị văn bản dịch) với thanh cuộn
    right_frame = tk.Frame(main_frame)
    right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
    scrollbar = tk.Scrollbar(right_frame, orient=tk.VERTICAL)
    mini_chat_text = tk.Text(right_frame, height=MINI_CHAT_TEXT_HEIGHT, width=MINI_CHAT_TEXT_WIDTH, wrap=tk.WORD, state=tk.DISABLED, yscrollcommand=scrollbar.set)
    scrollbar.config(command=mini_chat_text.yview)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    mini_chat_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    # Frame chứa các nút, căn giữa
    button_frame = tk.Frame(mini_chat_win)
    button_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=5)
    button_subframe = tk.Frame(button_frame)
    button_subframe.pack(anchor=tk.CENTER)
    btn_send = tk.Button(button_subframe, text="Send", command=send_mini_chat_message)
    btn_send.pack(side=tk.LEFT, padx=5, pady=5)
    translate_button = tk.Button(button_subframe, text="Translate", command=trigger_translation)
    translate_button.pack(side=tk.LEFT, padx=5, pady=5)
    print("Consolog: Thêm nút Translate thay cho X-AI.")
    btn_clear = tk.Button(button_subframe, text="Clear", command=clear_mini_chat)
    btn_clear.pack(side=tk.LEFT, padx=5, pady=5)
    btn_swap = tk.Button(button_subframe, text="Swap", command=swap_frames)
    btn_swap.pack(side=tk.LEFT, padx=5, pady=5)
    print("Consolog: Thêm nút Swap và căn giữa các nút.")

def trigger_translation():
    global mini_chat_entry, mini_chat_text, translate_button
    msg = mini_chat_entry.get("1.0", tk.END).strip()
    if not msg:
        append_mini_chat("Mini Chat [LỖI]: Vui lòng nhập văn bản để dịch.")
        print("Consolog [LỖI]: Không có văn bản để dịch.")
        return
    hwnd = get_correct_telegram_hwnd()
    if hwnd is None:
        append_mini_chat("Mini Chat [LỖI]: Không tìm thấy Telegram active.")
        print("Consolog [LỖI]: Không tìm thấy Telegram active.")
        return

    # Đổi văn bản nút thành "Translating" và vô hiệu hóa nút
    if translate_button:
        translate_button.config(text="Translating", state=tk.DISABLED)
        print("Consolog: Đổi nút thành 'Translating' và vô hiệu hóa.")

    print(f"Consolog: Bắt đầu dịch văn bản từ {MY_LANG_SELECTION} sang {TARGET_LANG_SELECTION}")

    # Hàm chạy trong luồng để dịch
    def translate_in_thread():
        translated, _ = translate_text_for_paragraph(msg, source_lang=MY_LANG_SELECTION, target_lang=TARGET_LANG_SELECTION)
        # Lên lịch cập nhật giao diện trên luồng chính
        root.after(0, lambda: update_ui_after_translation(translated))

    # Hàm cập nhật giao diện sau khi dịch xong
    def update_ui_after_translation(translated):
        # Xóa nội dung cũ trong ô hiển thị
        mini_chat_text.config(state=tk.NORMAL)
        mini_chat_text.delete("1.0", tk.END)
        append_mini_chat(f"Translated:\n{translated}")
        mini_chat_text.config(state=tk.DISABLED)
        # Khôi phục nút Translate
        if translate_button:
            translate_button.config(text="Translate", state=tk.NORMAL)
            print("Consolog: Khôi phục nút thành 'Translate' và kích hoạt.")
        print(f"Consolog: Kết quả dịch: {translated}")

    # Chạy dịch trong luồng riêng
    threading.Thread(target=translate_in_thread, daemon=True).start()

def clear_mini_chat():
    global mini_chat_text, mini_chat_entry
    if mini_chat_text is not None:
        mini_chat_text.config(state=tk.NORMAL)
        mini_chat_text.delete("1.0", tk.END)
        mini_chat_text.config(state=tk.DISABLED)
    if mini_chat_entry is not None:
        mini_chat_entry.delete("1.0", tk.END)
    print("Consolog: Xóa nội dung cả hai ô Mini Chat.")

def append_mini_chat(text):
    global mini_chat_text
    if mini_chat_text is None:
        return
    mini_chat_text.config(state=tk.NORMAL)
    mini_chat_text.insert(tk.END, text + "\n")
    mini_chat_text.see(tk.END)
    mini_chat_text.config(state=tk.DISABLED)

def translate_text_for_paragraph(text, source_lang="auto", target_lang="vi", conversation_context=""):
    global XAI_API_KEY
    if not XAI_API_KEY:
        error_msg = "Mini Chat [LỖI]: Khóa API xAI chưa set."
        append_mini_chat(error_msg)
        print(f"Consolog [LỖI]: {error_msg}")
        return text, None
    try:
        print(f"Consolog: Gọi xAI API (dịch đoạn văn) với API key: {XAI_API_KEY[:8]}...")
        lang_map = {
            "vi": "tiếng Việt", "en": "tiếng Anh", "zh": "tiếng Trung",
            "km": "tiếng Khmer", "pt": "tiếng Bồ Đào Nha", "hi": "tiếng Hindi"
        }
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
        print(f"Consolog: Gửi yêu cầu đến https://api.x.ai/v1/chat/completions")
        response = requests.post(
            "https://api.x.ai/v1/chat/completions",
            headers=headers,
            json=payload
        )
        print(f"Consolog: Phản hồi API xAI: {response.status_code}, Nội dung: {response.text}")
        if response.status_code == 200:
            data = response.json()
            full_reply = data["choices"][0]["message"]["content"].strip()
            print(f"Consolog: Kết quả thô từ xAI: {full_reply}")
            detected_lang = None
            translated_text = full_reply.strip()
            print(f"Consolog: Kết quả dịch: {translated_text}")
            if not translated_text:
                print(f"Consolog [CẢNH BÁO]: Kết quả dịch rỗng, trả về full_reply: {full_reply}")
                translated_text = full_reply
                append_mini_chat(f"Mini Chat [CẢNH BÁO]: Kết quả dịch rỗng, đã sử dụng phản hồi gốc: {translated_text}")
            return translated_text, detected_lang
        else:
            error_msg = f"Mini Chat [LỖI]: Lỗi API xAI (HTTP {response.status_code}): {response.text}"
            append_mini_chat(error_msg)
            messagebox.showerror("Lỗi API", error_msg)
            print(f"Consolog [LỖI]: {error_msg}")
            return text, None
    except requests.exceptions.RequestException as e:
        error_msg = f"Mini Chat [LỖI]: Lỗi kết nối API xAI: {str(e)}"
        append_mini_chat(error_msg)
        messagebox.showerror("Lỗi Kết nối", error_msg)
        print(f"Consolog [LỖI]: {error_msg}")
        return text, None
    except Exception as e:
        error_msg = f"Mini Chat [LỖI]: Lỗi không xác định khi gọi API xAI: {str(e)}"
        append_mini_chat(error_msg)
        messagebox.showerror("Lỗi", error_msg)
        print(f"Consolog [LỖI]: {error_msg}")
        return text, None

def translate_text_for_dialogue(text, source_lang="auto", target_lang="vi", conversation_context=""):
    global XAI_API_KEY
    if not XAI_API_KEY:
        error_msg = "Mini Chat [LỖI]: Khóa API xAI chưa set."
        print(f"Consolog [LỖI]: {error_msg}")
        return text, None
    try:
        print(f"Consolog: Gọi xAI API (dịch đoạn thoại ngắn) với API key: {XAI_API_KEY[:8]}...")
        lang_map = {
            "vi": "tiếng Việt", "en": "tiếng Anh", "zh": "tiếng Trung",
            "km": "tiếng Khmer", "pt": "tiếng Bồ Đào Nha", "hi": "tiếng Hindi"
        }
        lang_name = lang_map.get(target_lang.lower(), target_lang)
        prompt = (
            f"Bạn là một công cụ dịch ngôn ngữ chuyên nghiệp, chuyên dịch các đoạn thoại ngắn trong giao tiếp. Nhiệm vụ duy nhất của bạn là dịch đoạn thoại dưới đây từ {source_lang} sang {lang_name} một cách tự nhiên, phù hợp với ngữ cảnh giao tiếp. "
            f"Đoạn thoại có thể chứa từ lóng, viết tắt, tiếng địa phương, hoặc câu không đủ chủ ngữ/vị ngữ. Tuân theo các nguyên tắc sau:\n"
            f"1. Chỉ trả về bản dịch thuần túy, không thêm bất kỳ bình luận, ghi chú (như '[Translated]'), hoặc nội dung không liên quan.\n"
            f"2. Dịch tự nhiên, giữ đúng phong cách giao tiếp, bao gồm từ lóng, viết tắt, hoặc tiếng địa phương nếu chúng có trong đoạn thoại gốc.\n"
            f"3. Dịch chính xác ý nghĩa của đoạn thoại, không cần giữ định dạng phức tạp (xuống dòng, khoảng cách không quan trọng).\n"
            f"4. Nếu câu không đủ chủ ngữ/vị ngữ, dịch sao cho vẫn tự nhiên và phù hợp ngữ cảnh giao tiếp.\n"
            f"5. Nếu đoạn thoại không rõ ràng, dịch theo nghĩa hợp lý nhất dựa trên ngữ cảnh giao tiếp.\n\n"
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
            "max_tokens": 500
        }
        print(f"Consolog: Gửi yêu cầu đến https://api.x.ai/v1/chat/completions")
        response = requests.post(
            "https://api.x.ai/v1/chat/completions",
            headers=headers,
            json=payload
        )
        print(f"Consolog: Phản hồi API xAI: {response.status_code}, Nội dung: {response.text}")
        if response.status_code == 200:
            data = response.json()
            full_reply = data["choices"][0]["message"]["content"].strip()
            print(f"Consolog: Kết quả thô từ xAI: {full_reply}")
            detected_lang = None
            translated_text = full_reply.strip()
            print(f"Consolog: Kết quả dịch: {translated_text}")
            if not translated_text:
                print(f"Consolog [CẢNH BÁO]: Kết quả dịch rỗng, trả về full_reply: {full_reply}")
                translated_text = full_reply
            return translated_text, detected_lang
        else:
            error_msg = f"Mini Chat [LỖI]: Lỗi API xAI (HTTP {response.status_code}): {response.text}"
            print(f"Consolog [LỖI]: {error_msg}")
            return text, None
    except requests.exceptions.RequestException as e:
        error_msg = f"Mini Chat [LỖI]: Lỗi kết nối API xAI: {str(e)}"
        print(f"Consolog [LỖI]: {error_msg}")
        return text, None
    except Exception as e:
        error_msg = f"Mini Chat [LỖI]: Lỗi không xác định khi gọi API xAI: {str(e)}"
        print(f"Consolog [LỖI]: {error_msg}")
        return text, None

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
            print(f"Consolog [INFO]: Active Telegram HWND: {hwnd_fore}")
            return hwnd_fore
        else:
            print("Consolog: Foreground Telegram thu nhỏ hoặc không phải Telegram.")
    except Exception as e:
        print(f"Consolog [LỖI]: Lỗi kiểm tra foreground: {e}")
    if last_valid_telegram_hwnd is not None and not user32.IsIconic(last_valid_telegram_hwnd):
        print(f"Consolog [INFO]: Dùng last_valid_telegram_hwnd: {last_valid_telegram_hwnd}")
        return last_valid_telegram_hwnd
    hwnd_result = None
    EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_int, ctypes.c_int)
    def enum_windows_proc(hwnd, lParam):
        nonlocal hwnd_result
        if user32.IsWindowVisible(hwnd) and not user32.IsIconic(hwnd):
            length = user32.GetWindowTextLengthW(hwnd)
            buff = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buff, length + 1)
            title = buff.value
            pid_local = ctypes.wintypes.DWORD()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid_local))
            try:
                proc = psutil.Process(pid_local.value)
                if proc.name().lower() == "telegram.exe":
                    hwnd_result = hwnd
                    last_valid_telegram_hwnd = hwnd
                    print(f"Consolog [INFO]: Tìm Telegram: {title}, PID={pid_local.value}")
                    return False
            except Exception as e:
                print(f"Consolog [LỖI]: Lỗi lấy tiến trình: {e}")
        return True
    enum_proc_c = EnumWindowsProc(enum_windows_proc)
    user32.EnumWindows(enum_proc_c, 0)
    print(f"Consolog [INFO]: Correct Telegram HWND: {hwnd_result}")
    return hwnd_result

def send_mini_chat_message():
    global mini_chat_text, hwnd_target_lang, TARGET_LANG_SELECTION
    translated_text = mini_chat_text.get("1.0", tk.END).strip()
    if not translated_text.startswith("Translated:"):
        append_mini_chat("Mini Chat [LỖI]: Vui lòng dịch văn bản trước khi gửi.")
        return
    translated_text = translated_text.replace("Translated:\n", "").strip()
    if not translated_text:
        append_mini_chat("Mini Chat [LỖI]: Không có văn bản đã dịch để gửi.")
        return
    hwnd = get_correct_telegram_hwnd()
    if hwnd is None:
        append_mini_chat("Mini Chat [LỖI]: Không tìm thấy Telegram active.")
        return

    # Lưu vị trí con trỏ chuột hiện tại
    cursor_pos = ctypes.wintypes.POINT()
    user32.GetCursorPos(ctypes.byref(cursor_pos))
    original_x, original_y = cursor_pos.x, cursor_pos.y
    print(f"Consolog: Lưu vị trí con trỏ chuột ban đầu: ({original_x}, {original_y})")

    print("Consolog: Gửi tin nhắn dịch vào Telegram.")
    try:
        send_message_to_telegram_input(hwnd, translated_text)
        time.sleep(0.1)
        if mini_chat_win:
            mini_chat_win.lift()
        print("Consolog: Tin nhắn đã gửi tới Telegram.")

        # Khôi phục vị trí con trỏ chuột về vị trí ban đầu
        user32.SetCursorPos(original_x, original_y)
        print(f"Consolog: Khôi phục vị trí con trỏ chuột về: ({original_x}, {original_y})")
    except Exception as e:
        append_mini_chat(f"Mini Chat [LỖI]: Lỗi gửi tin: {e}")
        print(f"Consolog [LỖI]: Lỗi gửi tin: {e}")
        # Nếu có lỗi, vẫn cố gắng khôi phục vị trí con trỏ chuột
        user32.SetCursorPos(original_x, original_y)
        print(f"Consolog: Khôi phục vị trí con trỏ chuột sau lỗi: ({original_x}, {original_y})")

def save_config():
    try:
        config_file = os.path.join(os.getcwd(), "config.ini")
        with open(config_file, "w", encoding="utf-8") as f:
            f.write(f"MY_LANG_SELECTION={MY_LANG_SELECTION}\n")
            f.write(f"TARGET_LANG_SELECTION={TARGET_LANG_SELECTION}\n")
        print("Consolog: Lưu cấu hình vào config.ini")
        for hwnd in list(hwnd_target_lang.keys()):
            hwnd_target_lang[hwnd] = TARGET_LANG_SELECTION
            print(f"Consolog: Cập nhật ngôn ngữ HWND {hwnd}: {TARGET_LANG_SELECTION}")
        append_mini_chat("Cài đặt ngôn ngữ đã lưu.")
    except Exception as e:
        print(f"Consolog [LỖI]: Lỗi lưu config: {e}")
        append_mini_chat("Mini Chat [LỖI]: Lỗi lưu config.")

def destroy_mini_chat():
    global mini_chat_win, mini_chat_text, mini_chat_entry
    if mini_chat_win is not None:
        try:
            if mini_chat_win.winfo_exists():
                mini_chat_win.destroy()
            mini_chat_win = None
            mini_chat_text = None
            mini_chat_entry = None
            print("Consolog: Cửa sổ Mini Chat đã đóng.")
        except tk.TclError:
            print("Consolog: Cửa sổ Mini Chat đã bị hủy trước đó, đặt lại trạng thái.")
            mini_chat_win = None
            mini_chat_text = None
            mini_chat_entry = None

import ctypes.wintypes

class WINDOWPLACEMENT(ctypes.Structure):
    _fields_ = [
        ("length", ctypes.c_uint), ("flags", ctypes.c_uint), ("showCmd", ctypes.c_uint),
        ("ptMinPosition", ctypes.wintypes.POINT), ("ptMaxPosition", ctypes.wintypes.POINT),
        ("rcNormalPosition", ctypes.wintypes.RECT),
    ]

def create_mini_xai():
    global mini_xai_win, mini_xai_entry, mini_xai_pause_button
    if root is None:
        print("Consolog [LỖI]: root chưa set. Gọi set_root(root).")
        return
    mini_xai_win = tk.Toplevel(root)
    mini_xai_win.title("Mini xAI Widget")
    mini_xai_win.overrideredirect(True)
    mini_xai_win.attributes("-topmost", False)
    mini_xai_win.geometry(f"400x{WIDGET_HEIGHT}+0+0")
    mini_xai_win.withdraw()
    print("Consolog: Widget Mini xAI khởi tạo và ẩn.")
    frame = tk.Frame(mini_xai_win)
    frame.pack(fill=tk.BOTH, expand=True)
    mini_xai_entry = tk.Entry(frame)
    mini_xai_entry.grid(row=0, column=0, sticky="we", padx=(5, 2), pady=5)
    frame.columnconfigure(0, weight=1)
    mini_xai_entry.bind("<Return>", lambda event: send_mini_xai_message())
    btn_send = tk.Button(frame, text="Send", command=send_mini_xai_message, width=8)
    btn_send.grid(row=0, column=1, padx=2, sticky="e")
    btn_zoom = tk.Button(frame, text="Zoom", command=toggle_mini_chat_zoom, width=8)
    btn_zoom.grid(row=0, column=2, padx=2, sticky="e")
    mini_xai_pause_button = btn_zoom
    btn_quit = tk.Button(frame, text="Quit", command=destroy_mini_xai, width=8)
    btn_quit.grid(row=0, column=3, padx=2, sticky="e")
    print("Consolog: Tạo widget với nút Send, Zoom, Quit.")
    
    # Tự động mở Mini Chat ngay sau khi tạo Mini xAI Widget
    create_mini_chat()
    print("Consolog: Tự động mở Mini Chat cùng với Mini xAI Widget.")

    threading.Thread(target=update_mini_xai_position, daemon=True).start()

def send_mini_xai_message():
    global mini_xai_entry
    if mini_xai_entry is None:
        return
    msg = mini_xai_entry.get().strip()
    if not msg:
        return
    mini_xai_entry.delete(0, tk.END)
    print(f"Consolog: [mini xai] Nhập: {msg}")
    hwnd = get_correct_telegram_hwnd()
    if hwnd is None:
        print("Consolog [LỖI]: Widget không tìm thấy Telegram active.")
        return
    target_lang = hwnd_target_lang.get(hwnd, TARGET_LANG_SELECTION)
    print(f"Consolog: [mini xai] Ngôn ngữ đối phương: {target_lang}")
    translated, _ = translate_text_for_dialogue(msg, source_lang="auto", target_lang=target_lang)
    print(f"Consolog: [mini xai] Tin nhắn dịch: {translated}")
    try:
        send_message_to_telegram_input(hwnd, translated)
        print("Consolog: [mini xai] Gửi tin vào Telegram.")
        mini_xai_entry.focus_force()
        print("Consolog: Focus đặt lại ô widget.")
    except Exception as e:
        print(f"Consolog [LỖI]: Widget lỗi gửi tin: {e}")

def destroy_mini_xai():
    global mini_xai_win, widget_mini_chat_thread_running
    print("Consolog: Thực hiện destroy_mini_xai...")
    destroy_mini_chat()
    widget_mini_chat_thread_running = False
    print("Consolog: Đặt widget_mini_chat_thread_running = False.")
    if mini_xai_win is not None:
        try:
            if mini_xai_win.winfo_exists():
                mini_xai_win.destroy()
            mini_xai_win = None
            mini_xai_entry = None
            mini_xai_pause_button = None
            print("Consolog: Widget Mini xAI đóng.")
        except tk.TclError:
            print("Consolog: Widget Mini xAI đã bị hủy trước đó, đặt lại trạng thái.")
            mini_xai_win = None
            mini_xai_entry = None
            mini_xai_pause_button = None

def update_mini_xai_position():
    global mini_xai_win, widget_mini_chat_thread_running
    while mini_xai_win is not None and widget_mini_chat_thread_running:
        try:
            mini_xai_win.update_idletasks()
            hwnd = get_correct_telegram_hwnd()
            if hwnd and not user32.IsIconic(hwnd):
                mini_xai_win.deiconify()
                placement = WINDOWPLACEMENT()
                placement.length = ctypes.sizeof(WINDOWPLACEMENT)
                user32.GetWindowPlacement(hwnd, ctypes.byref(placement))
                if placement.showCmd != 1:
                    rect = placement.rcNormalPosition
                    print("Consolog: Telegram không bình thường, dùng rcNormalPosition.")
                else:
                    rect = ctypes.wintypes.RECT()
                    user32.GetWindowRect(hwnd, ctypes.byref(rect))
                window_width = rect.right - rect.left
                widget_width = window_width
                x = rect.left
                y = rect.top - WIDGET_HEIGHT - WIDGET_Y_OFFSET
                new_geometry = f"{widget_width}x{WIDGET_HEIGHT}+{x}+{y}"
                mini_xai_win.geometry(new_geometry)
                mini_xai_win.lift()
                print(f"Consolog: Cập nhật widget: {new_geometry} gắn HWND {hwnd}.")
            else:
                mini_xai_win.withdraw()
                print("Consolog: Không tìm Telegram, ẩn widget.")
        except tk.TclError:
            print("Consolog: Widget Mini xAI đã bị hủy, thoát vòng lặp update.")
            break
        time.sleep(0.5)

def toggle_mini_chat_zoom():
    global mini_chat_win
    # Kiểm tra xem cửa sổ Mini Chat có tồn tại và còn "sống" không
    try:
        if mini_chat_win is None or not mini_chat_win.winfo_exists():
            print("Consolog: Mini Chat không tồn tại hoặc đã bị hủy, tạo mới.")
            create_mini_chat()
        else:
            # Nếu cửa sổ tồn tại, kiểm tra trạng thái và khôi phục nếu cần
            state = mini_chat_win.state()
            if state in ("withdrawn", "iconic"):
                mini_chat_win.deiconify()
                print("Consolog: Khôi phục Mini Chat từ trạng thái ẩn hoặc thu nhỏ.")
            else:
                print("Consolog: Mini Chat đã hiển thị, chỉ cập nhật vị trí.")
    except tk.TclError:
        print("Consolog: Mini Chat đã bị hủy trước đó, tạo mới.")
        create_mini_chat()

    # Cập nhật vị trí của Mini Chat
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
        x = rect.right + 10
        y = rect.top
    else:
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        x = screen_width - MINI_CHAT_WIDTH - MINI_CHAT_X_OFFSET
        y = screen_height - MINI_CHAT_HEIGHT - MINI_CHAT_Y_OFFSET
    mini_chat_win.geometry(f"{MINI_CHAT_WIDTH}x{MINI_CHAT_HEIGHT}+{x}+{y}")
    mini_chat_win.lift()
    print("Consolog: Mini Chat được định vị lại.")