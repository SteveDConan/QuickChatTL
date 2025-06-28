import tkinter as tk
import customtkinter as ctk
import threading
from minichat.dialogSelect import DialogSelect
from minichat.telegram_integration import get_telegram_window_handle, update_widget_position
from minichat.win_event import setup_window_monitoring
from minichat.chat_handlers import send_translated_message, close_translation_window

def create_chat_window(config, window_state, translator):
    if window_state.root is None:
        return

    window_config = config.config.get("widget_config", {}).get("window", {})
    window_state.sam_mini_chat_win = window_state.root
    window_state.sam_mini_chat_win.title(window_config.get("title", "Sam Mini Chat"))
    window_state.sam_mini_chat_win.overrideredirect(
        window_config.get("overrideredirect", True)
    )
    window_state.sam_mini_chat_win.geometry(
        f"{window_config.get('width', 600)}x{config.widget_height}+0+0"
    )

    setup_window_monitoring(config, window_state)

    main_frame = ctk.CTkFrame(
        window_state.sam_mini_chat_win,
        fg_color=window_config.get("bg", "#f0f0f0"),
        corner_radius=window_config.get("corner_radius", 0),
    )
    main_frame.pack(
        fill=tk.BOTH,
        expand=True,
        padx=window_config.get("padx", 2),
        pady=(window_config.get("pady", 2), 0),
    )

    # Get all styles from config
    styles = config.config.get("widget_config", {}).get("styles", {})
    button_style = styles.get("button", {})
    text_entry_style = styles.get("text_entry", {})
    quick_lang_style = styles.get("quick_language", {})

    # Input frame
    input_frame = ctk.CTkFrame(
        main_frame, fg_color=window_config.get("input_frame_bg", "transparent")
    )
    input_frame.pack(fill=tk.X, pady=window_config.get("input_frame_pady", (0, 5)))

    window_state.sam_mini_chat_entry = ctk.CTkTextbox(
        input_frame,
        font=tuple(text_entry_style.get("font", ["Segoe UI", 16])),
        fg_color=text_entry_style.get("bg", "#ffffff"),
        text_color=text_entry_style.get("fg", "#333333"),
        border_width=text_entry_style.get("border_width", 1),
        corner_radius=text_entry_style.get("corner_radius", 5),
        height=text_entry_style.get("height", 1) * 32,
    )
    window_state.sam_mini_chat_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

    window_state.sam_mini_chat_btn_send = ctk.CTkButton(
        input_frame,
        text="➤",
        command=lambda: send_translated_message(config, window_state, translator),
        font=("Segoe UI", 16, "bold"),
        fg_color=button_style.get("send_bg", "#007AFF"),
        hover_color=button_style.get("send_hover", "#0056b3"),
        corner_radius=button_style.get("corner_radius", 5),
        width=40,
        height=32,
    )
    window_state.sam_mini_chat_btn_send.pack(
        side=tk.LEFT, padx=button_style.get("padx", 5)
    )

    # Controls frame (API, Quit, Language)
    controls_frame = ctk.CTkFrame(
        main_frame, fg_color=window_config.get("controls_bg", "transparent")
    )
    controls_frame.pack(fill=tk.X, pady=(0, 0))

    # Left side controls (Quick Lang, API, Language, Quit)
    left_controls = ctk.CTkFrame(
        controls_frame, fg_color=window_config.get("controls_bg", "transparent")
    )
    left_controls.pack(side=tk.LEFT, padx=0)

    # Initialize variables
    target_lang_var = tk.StringVar(
        value=config.lang_map.get(config.target_lang_selection, "Tiếng Anh")
    )
    api_var = tk.StringVar(value=config.selected_api)

    def update_target_lang(val: str) -> None:
        lang_code = next(
            (code for code, name in config.lang_map.items() if name == val),
            config.target_lang_selection,
        )
        config.target_lang_selection = lang_code
        hwnd = get_telegram_window_handle(window_state)
        if hwnd:
            window_state.hwnd_target_lang[hwnd] = lang_code
        # Update translator language map
        translator.lang_map = config.lang_map

    def update_api(val: str) -> None:
        config.selected_api = val
        # Update translator config if needed
        translator.config = config.config

    # Initialize dialog selector
    global dialog_selector
    dialog_selector = DialogSelect(window_state.sam_mini_chat_win, config, window_state)

    # Quick language selection frame
    quick_lang_frame = ctk.CTkFrame(
        left_controls, fg_color=window_config.get("quick_lang_frame_bg", "transparent")
    )
    quick_lang_frame.pack(side=tk.LEFT, padx=0)

    quick_languages = config.config.get("language_config", {}).get(
        "quick_languages", ["en", "vi", "ja", "zh", "ko"]
    )

    def on_quick_lang_click(lang_code: str) -> None:
        lang_name = config.lang_map.get(lang_code, lang_code)
        target_lang_var.set(lang_name)
        update_target_lang(lang_name)

    for lang_code in quick_languages:
        lang_name = config.lang_map.get(lang_code, lang_code)
        btn = ctk.CTkButton(
            quick_lang_frame,
            text=lang_name,
            command=lambda l=lang_code: on_quick_lang_click(l),
            font=tuple(quick_lang_style.get("font", ["Segoe UI", 13])),
            fg_color=quick_lang_style.get("bg", "#E3F2FD"),
            text_color=quick_lang_style.get("fg", "#1976D2"),
            hover_color=quick_lang_style.get("hover", "#BBDEFB"),
            corner_radius=quick_lang_style.get("corner_radius", 6),
            border_width=quick_lang_style.get("border_width", 1),
            border_color=quick_lang_style.get("border_color", "#90CAF9"),
            height=32,
            width=quick_lang_style.get("width", 12),
            cursor=quick_lang_style.get("cursor", "hand2"),
        )
        btn.pack(side=tk.LEFT, padx=0)

        def update_btn_appearance(*args, btn=btn):
            if btn.cget("text") == target_lang_var.get():
                btn.configure(
                    fg_color=quick_lang_style.get("selected_bg", "#2196F3"),
                    text_color=quick_lang_style.get("selected_fg", "white"),
                    border_color=quick_lang_style.get("selected_border", "#1976D2"),
                )
            else:
                btn.configure(
                    fg_color=quick_lang_style.get("bg", "#E3F2FD"),
                    text_color=quick_lang_style.get("fg", "#1976D2"),
                    border_color=quick_lang_style.get("border_color", "#90CAF9"),
                )

        target_lang_var.trace_add("write", update_btn_appearance)
        update_btn_appearance()

    # --- UI chính: Thêm label hiển thị API/ngôn ngữ đang chọn ---
    api_btn = ctk.CTkButton(
        left_controls,
        textvariable=api_var,
        command=lambda: dialog_selector.show_api_selection_dialog(api_var, update_api, styles),
        font=("Segoe UI", 14, "bold"),
        fg_color="#E8F5E9",
        text_color="#2E7D32",
        hover_color="#C8E6C9",
        border_color="#4CAF50",
        border_width=1,
        corner_radius=8,
        width=45,
        height=32,
    )
    api_btn.pack(side=tk.LEFT, padx=(0, 2))
    lang_btn = ctk.CTkButton(
        left_controls,
        textvariable=target_lang_var,
        command=lambda: dialog_selector.show_language_selection_dialog(target_lang_var, update_target_lang),
        font=("Segoe UI", 14, "bold"),
        fg_color="#E3F2FD",
        text_color="#1976D2",
        hover_color="#BBDEFB",
        border_color="#2196F3",
        border_width=1,
        corner_radius=8,
        width=45,
        height=32,
    )
    lang_btn.pack(side=tk.LEFT, padx=(0, 2))
    btn_quit = ctk.CTkButton(
        left_controls,
        text="×",
        command=lambda: close_translation_window(window_state),
        font=("Segoe UI", 16, "bold"),
        fg_color=button_style.get("quit_bg", "#FF3B30"),
        hover_color=button_style.get("quit_hover", "#cc2f26"),
        corner_radius=button_style.get("corner_radius", 5),
        width=15,
        height=32,
    )
    btn_quit.pack(side=tk.LEFT, padx=(0, 2))

    def on_enter(event: tk.Event) -> str:
        if not event.state & 0x1:
            send_translated_message(config, window_state, translator)
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

    threading.Thread(target=lambda: update_widget_position(config, window_state), daemon=True).start() 