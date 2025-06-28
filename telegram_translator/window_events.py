import ctypes
import threading
import time
from telegram_translator.telegram_client import find_telegram_window_handle, synchronize_window_z_order

# Windows API setup
user32 = ctypes.windll.user32

def setup_window_monitoring(config, window_state):
    """Setup window monitoring to track Telegram window changes"""
    def monitor_window_changes():
        while window_state.is_widget_thread_running:
            try:
                telegram_window_handle = find_telegram_window_handle(window_state)
                if telegram_window_handle:
                    # Update widget position and z-order
                    if window_state.translation_window and window_state.translation_window.winfo_exists():
                        widget_window_handle = window_state.translation_window.winfo_id()
                        synchronize_window_z_order(telegram_window_handle, widget_window_handle, config)
            except Exception as e:
                print(f"Error in window monitoring: {e}")
            
            time.sleep(0.5)  # Check every 500ms

    # Start monitoring thread
    monitoring_thread = threading.Thread(target=monitor_window_changes, daemon=True)
    monitoring_thread.start()

def handle_window_focus_change(window_handle, window_state):
    """Handle window focus change events"""
    if window_handle == find_telegram_window_handle(window_state):
        # Telegram window is now active, ensure widget is visible
        if window_state.translation_window and window_state.translation_window.winfo_exists():
            window_state.translation_window.deiconify()
            window_state.translation_window.lift()

def window_event_handler(
    win_event_hook: int,
    event_type: int,
    window_handle: int,
    object_id: int,
    child_id: int,
    event_thread_id: int,
    event_time: int,
    config,
    window_state
) -> None:
    """Handle Windows window events"""
    try:
        if event_type == config.EVENT_OBJECT_REORDER or event_type == config.EVENT_SYSTEM_FOREGROUND:
            if window_handle == find_telegram_window_handle(window_state):
                if (
                    window_state.translation_window
                    and window_state.translation_window.winfo_exists()
                ):
                    widget_window_handle = window_state.translation_window.winfo_id()
                    synchronize_window_z_order(window_handle, widget_window_handle, config)
    except Exception as e:
        print(f"Error in window event handler: {e}")

def setup_window_event_monitoring(config, window_state) -> None:
    """Setup Windows event monitoring for window changes"""
    try:
        WinEventProcType = ctypes.WINFUNCTYPE(
            None,
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_int,
        )

        window_state.z_order_callback = WinEventProcType(
            lambda win_event_hook, event_type, window_handle, object_id, child_id, event_thread_id, event_time: 
            window_event_handler(win_event_hook, event_type, window_handle, object_id, child_id, event_thread_id, event_time, config, window_state)
        )

        user32.SetWinEventHook(
            config.EVENT_OBJECT_REORDER,
            config.EVENT_SYSTEM_FOREGROUND,
            0,
            window_state.z_order_callback,
            0,
            0,
            config.WINEVENT_OUTOFCONTEXT
            | config.WINEVENT_SKIPOWNTHREAD
            | config.WINEVENT_SKIPOWNPROCESS,
        )
    except Exception as e:
        print(f"Error setting up Z-order monitoring: {e}") 