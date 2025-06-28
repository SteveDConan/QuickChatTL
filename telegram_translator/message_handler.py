import tkinter as tk
import threading
from telegram_translator.telegram_client import find_telegram_window_handle, send_message_to_telegram

def process_and_send_translated_message(config, window_state, translator):
    """Process user input, translate and send message to Telegram"""
    if window_state.message_input_field is None:
        return

    user_message = window_state.message_input_field.get("1.0", tk.END).strip()
    if not user_message:
        return

    original_message = user_message
    window_state.message_input_field.delete("1.0", tk.END)
    
    telegram_window_handle = find_telegram_window_handle(window_state)
    if telegram_window_handle is None:
        window_state.message_input_field.insert("1.0", original_message)
        return

    target_language = window_state.window_target_language_map.get(telegram_window_handle, config.target_lang_selection)

    # Disable input and send button during processing
    window_state.message_input_field.configure(state=tk.DISABLED)
    window_state.send_button.configure(state=tk.DISABLED)

    # Get animation configuration
    ui_config = config.config.get("ui_config", {})
    loading_animation_frames = ui_config.get(
        "loading_frames", ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    )
    animation_interval = ui_config.get("loading_interval", 100)
    success_animation_duration = ui_config.get("success_delay", 300)
    error_animation_duration = ui_config.get("error_delay", 300)
    animation_styles = ui_config.get("animation", {})

    # Get button style from config
    button_style_config = config.config.get("widget_config", {}).get("button_style", {})

    current_animation_frame = 0
    is_loading_animation_active = True

    def update_loading_animation():
        nonlocal current_animation_frame
        if window_state.send_button.winfo_exists() and is_loading_animation_active:
            sending_style = animation_styles.get("sending", {})
            window_state.send_button.configure(
                text=sending_style.get("text", "Sending {frame}").format(
                    frame=loading_animation_frames[current_animation_frame]
                ),
                fg_color=sending_style.get("bg", "#90EE90"),
            )
            current_animation_frame = (current_animation_frame + 1) % len(loading_animation_frames)
            window_state.root.after(animation_interval, update_loading_animation)

    update_loading_animation()

    def execute_translation_and_send() -> None:
        nonlocal is_loading_animation_active
        try:
            translated_message = None
            translated_message, _ = translator.translate_text(user_message, target_language, config.selected_api, None)

            if translated_message is None or translated_message == user_message:
                raise Exception("Translation failed")

            # Stop loading animation
            is_loading_animation_active = False

            # Send message and wait for completion
            if send_message_to_telegram(telegram_window_handle, translated_message, config, window_state):
                # Success animation
                success_style = animation_styles.get("success", {})
                window_state.root.after(
                    0,
                    lambda: window_state.send_button.configure(
                        text="✓ Sent", fg_color=success_style.get("bg", "#4CAF50")
                    ),
                )
                window_state.root.after(
                    success_animation_duration,
                    lambda: window_state.send_button.configure(
                        text="➤", fg_color=button_style_config.get("bg", "#007AFF")
                    ),
                )
                window_state.message_input_field.focus_force()
            else:
                raise Exception("Failed to send message")

        except Exception as e:
            # Stop loading animation
            is_loading_animation_active = False

            # Error animation
            error_style = animation_styles.get("error", {})
            window_state.root.after(
                0,
                lambda: window_state.send_button.configure(
                    text="✗ Error", fg_color=error_style.get("bg", "#FF3B30")
                ),
            )
            window_state.root.after(
                error_animation_duration,
                lambda: window_state.send_button.configure(
                    text="➤", fg_color=button_style_config.get("bg", "#007AFF")
                ),
            )
            window_state.root.after(
                0, lambda: window_state.message_input_field.delete("1.0", tk.END)
            )
            window_state.root.after(
                0, lambda: window_state.message_input_field.insert("1.0", original_message)
            )
        finally:
            # Re-enable input and send button
            window_state.root.after(
                0, lambda: window_state.message_input_field.configure(state=tk.NORMAL)
            )
            window_state.root.after(
                0,
                lambda: window_state.send_button.configure(state=tk.NORMAL),
            )

    threading.Thread(target=execute_translation_and_send, daemon=True).start()

def cleanup_translation_window(window_state):
    """Clean up and close the translation window"""
    window_state.is_widget_thread_running = False
    if window_state.translation_window is not None:
        try:
            if window_state.translation_window.winfo_exists():
                window_state.translation_window.destroy()
            window_state.translation_window = None
            window_state.message_input_field = None
        except tk.TclError:
            window_state.translation_window = None
            window_state.message_input_field = None

    if window_state.root is not None:
        try:
            window_state.root.quit()
            window_state.root.destroy()
        except tk.TclError:
            pass 