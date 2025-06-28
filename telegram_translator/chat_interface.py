import tkinter as tk
import customtkinter as ctk
import threading
from telegram_translator.language_selector import LanguageAndApiSelector
from telegram_translator.telegram_client import find_telegram_window_handle, update_widget_position
from telegram_translator.window_events import setup_window_monitoring
from telegram_translator.message_handler import process_and_send_translated_message, cleanup_translation_window

def create_chat_window(config, window_state, translator):
    """Create the main chat interface window"""
    if window_state.root is None:
        return

    window_config = config.config.get("widget_config", {}).get("window", {})
    window_state.translation_window = window_state.root
    window_state.translation_window.title(window_config.get("title", "Telegram Translation Tool"))
    window_state.translation_window.overrideredirect(
        window_config.get("overrideredirect", True)
    )
    window_state.translation_window.geometry(
        f"{window_config.get('width', 600)}x{config.widget_height}+0+0"
    )

    setup_window_monitoring(config, window_state)

    main_frame = ctk.CTkFrame(
        window_state.translation_window,
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

    window_state.message_input_field = ctk.CTkTextbox(
        input_frame,
        font=tuple(text_entry_style.get("font", ["Segoe UI", 16])),
        fg_color=text_entry_style.get("bg", "#ffffff"),
        text_color=text_entry_style.get("fg", "#333333"),
        border_width=text_entry_style.get("border_width", 1),
        corner_radius=text_entry_style.get("corner_radius", 5),
        height=text_entry_style.get("height", 1) * 32,
    )
    window_state.message_input_field.pack(side=tk.LEFT, fill=tk.X, expand=True)

    window_state.send_button = ctk.CTkButton(
        input_frame,
        text="➤",
        command=lambda: process_and_send_translated_message(config, window_state, translator),
        font=("Segoe UI", 16, "bold"),
        fg_color=button_style.get("send_bg", "#007AFF"),
        hover_color=button_style.get("send_hover", "#0056b3"),
        corner_radius=button_style.get("corner_radius", 5),
        width=40,
        height=32,
    )
    window_state.send_button.pack(
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
    target_language_variable = tk.StringVar(
        value=config.language_mapping.get(config.target_lang_selection, "Tiếng Anh")
    )
    api_variable = tk.StringVar(value=config.selected_api)

    def update_target_language(language_name: str) -> None:
        language_code = next(
            (code for code, name in config.language_mapping.items() if name == language_name),
            config.target_lang_selection,
        )
        config.target_lang_selection = language_code
        telegram_window_handle = find_telegram_window_handle(window_state)
        if telegram_window_handle:
            window_state.window_target_language_map[telegram_window_handle] = language_code
        # Update translator language map
        translator.language_mapping = config.language_mapping

    def update_api_selection(api_name: str) -> None:
        config.selected_api = api_name
        # Update translator config if needed
        translator.config = config.config

    # Initialize dialog selector
    global dialog_selector
    dialog_selector = LanguageAndApiSelector(window_state.translation_window, config, window_state)

    # Quick language selection frame
    quick_language_frame = ctk.CTkFrame(
        left_controls, fg_color=window_config.get("quick_lang_frame_bg", "transparent")
    )
    quick_language_frame.pack(side=tk.LEFT, padx=0)

    quick_languages = config.config.get("language_config", {}).get(
        "quick_languages", ["en", "vi", "ja", "zh", "ko"]
    )

    def handle_quick_language_click(language_code: str) -> None:
        language_name = config.language_mapping.get(language_code, language_code)
        target_language_variable.set(language_name)
        update_target_language(language_name)

    for language_code in quick_languages:
        language_name = config.language_mapping.get(language_code, language_code)
        language_button = ctk.CTkButton(
            quick_language_frame,
            text=language_name,
            command=lambda l=language_code: handle_quick_language_click(l),
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
        language_button.pack(side=tk.LEFT, padx=0)

        def update_button_appearance(*args, btn=language_button):
            if btn.cget("text") == target_language_variable.get():
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

        target_language_variable.trace_add("write", update_button_appearance)
        update_button_appearance()

    # --- Main UI: Add labels to display current API/language selection ---
    api_selection_button = ctk.CTkButton(
        left_controls,
        textvariable=api_variable,
        command=lambda: dialog_selector.show_api_selection_dialog(api_variable, update_api_selection, styles),
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
    api_selection_button.pack(side=tk.LEFT, padx=(0, 2))
    
    language_selection_button = ctk.CTkButton(
        left_controls,
        textvariable=target_language_variable,
        command=lambda: dialog_selector.show_language_selection_dialog(target_language_variable, update_target_language),
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
    language_selection_button.pack(side=tk.LEFT, padx=(0, 2))
    
    quit_button = ctk.CTkButton(
        left_controls,
        text="×",
        command=lambda: cleanup_translation_window(window_state),
        font=("Segoe UI", 16, "bold"),
        fg_color=button_style.get("quit_bg", "#FF3B30"),
        hover_color=button_style.get("quit_hover", "#cc2f26"),
        corner_radius=button_style.get("corner_radius", 5),
        width=15,
        height=32,
    )
    quit_button.pack(side=tk.LEFT, padx=(0, 2))

    def on_enter(event: tk.Event) -> str:
        if not event.state & 0x1:
            process_and_send_translated_message(config, window_state, translator)
            return "break"
        return ""

    def on_shift_enter(event: tk.Event) -> str:
        if event.state & 0x1:
            window_state.message_input_field.insert(tk.INSERT, "\n")
            return "break"
        return ""

    window_state.message_input_field.bind("<Return>", on_enter)
    window_state.message_input_field.bind("<Shift-Return>", on_shift_enter)

    def start_move(event: tk.Event) -> None:
        main_frame.x = event.x
        main_frame.y = event.y

    def do_move(event: tk.Event) -> None:
        deltax = event.x - main_frame.x
        deltay = event.y - main_frame.y
        x = window_state.translation_window.winfo_x() + deltax
        y = window_state.translation_window.winfo_y() + deltay
        window_state.translation_window.geometry(f"+{x}+{y}")

    main_frame.bind("<Button-1>", start_move)
    main_frame.bind("<B1-Motion>", do_move)

    threading.Thread(target=lambda: update_widget_position(config, window_state), daemon=True).start() 