import tkinter as tk
import threading
from minichat.telegram_integration import get_telegram_window_handle, send_message_to_telegram

def send_translated_message(config, window_state, translator):
    if window_state.sam_mini_chat_entry is None:
        return

    msg = window_state.sam_mini_chat_entry.get("1.0", tk.END).strip()
    if not msg:
        return

    original_msg = msg
    window_state.sam_mini_chat_entry.delete("1.0", tk.END)
    hwnd = get_telegram_window_handle(window_state)
    if hwnd is None:
        window_state.sam_mini_chat_entry.insert("1.0", original_msg)
        return

    target_lang = window_state.hwnd_target_lang.get(hwnd, config.target_lang_selection)

    # Disable input and send button during sending
    window_state.sam_mini_chat_entry.configure(state=tk.DISABLED)
    window_state.sam_mini_chat_btn_send.configure(state=tk.DISABLED)

    # Get animation config
    ui_config = config.config.get("ui_config", {})
    loading_frames = ui_config.get(
        "loading_frames", ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    )
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
                text=sending_config.get("text", "Sending {frame}").format(
                    frame=loading_frames[current_frame]
                ),
                fg_color=sending_config.get("bg", "#90EE90"),
            )
            current_frame = (current_frame + 1) % len(loading_frames)
            window_state.root.after(loading_interval, update_loading)

    update_loading()

    def send_thread() -> None:
        nonlocal loading_active
        try:
            translated = None
            translated, _ = translator.translate_text(msg, target_lang, config.selected_api, None)

            if translated is None or translated == msg:
                raise Exception("Translation failed")

            # Stop loading animation
            loading_active = False

            # Send message and wait for completion
            if send_message_to_telegram(hwnd, translated, config, window_state):
                # Success animation
                success_config = animation.get("success", {})
                window_state.root.after(
                    0,
                    lambda: window_state.sam_mini_chat_btn_send.configure(
                        text="✓ Sent", fg_color=success_config.get("bg", "#4CAF50")
                    ),
                )
                window_state.root.after(
                    success_delay,
                    lambda: window_state.sam_mini_chat_btn_send.configure(
                        text="➤", fg_color=button_style.get("bg", "#007AFF")
                    ),
                )
                window_state.sam_mini_chat_entry.focus_force()
            else:
                raise Exception("Failed to send message")

        except Exception as e:
            # Stop loading animation
            loading_active = False

            # Error animation
            error_config = animation.get("error", {})
            window_state.root.after(
                0,
                lambda: window_state.sam_mini_chat_btn_send.configure(
                    text="✗ Error", fg_color=error_config.get("bg", "#FF3B30")
                ),
            )
            window_state.root.after(
                error_delay,
                lambda: window_state.sam_mini_chat_btn_send.configure(
                    text="➤", fg_color=button_style.get("bg", "#007AFF")
                ),
            )
            window_state.root.after(
                0, lambda: window_state.sam_mini_chat_entry.delete("1.0", tk.END)
            )
            window_state.root.after(
                0, lambda: window_state.sam_mini_chat_entry.insert("1.0", original_msg)
            )
        finally:
            # Re-enable input and send button
            window_state.root.after(
                0, lambda: window_state.sam_mini_chat_entry.configure(state=tk.NORMAL)
            )
            window_state.root.after(
                0,
                lambda: window_state.sam_mini_chat_btn_send.configure(state=tk.NORMAL),
            )

    threading.Thread(target=send_thread, daemon=True).start()

def close_translation_window(window_state):
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