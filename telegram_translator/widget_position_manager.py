import ctypes
import time
from ctypes import wintypes

# Windows API setup
user32 = ctypes.windll.user32

class WINDOWPLACEMENT(ctypes.Structure):
    _fields_ = [
        ("length", ctypes.c_uint),
        ("flags", ctypes.c_uint),
        ("showCmd", ctypes.c_uint),
        ("ptMinPosition", ctypes.wintypes.POINT),
        ("ptMaxPosition", ctypes.wintypes.POINT),
        ("rcNormalPosition", ctypes.wintypes.RECT),
    ]

def find_telegram_window_handle(window_state):
    """Find and return the handle of the active Telegram window"""
    from telegram_translator.telegram_message_sender import find_telegram_window_handle
    return find_telegram_window_handle(window_state)

def synchronize_window_z_order(telegram_window_handle: int, widget_window_handle: int, config) -> None:
    """Synchronize the Z-order of the widget window with Telegram window"""
    try:
        # Always set the widget to be topmost
        user32.SetWindowPos(
            widget_window_handle,
            config.HWND_TOPMOST,
            0,
            0,
            0,
            0,
            config.SWP_NOMOVE | config.SWP_NOSIZE | config.SWP_NOACTIVATE,
        )
    except Exception as e:
        print(f"Error synchronizing Z-order: {e}")

def update_widget_position(config, window_state):
    """Continuously update widget position to follow Telegram window"""
    while (
        window_state.translation_window is not None
        and window_state.is_widget_thread_running
    ):
        try:
            telegram_window_handle = find_telegram_window_handle(window_state)
            if telegram_window_handle:
                window_placement = WINDOWPLACEMENT()
                window_placement.length = ctypes.sizeof(WINDOWPLACEMENT)
                user32.GetWindowPlacement(telegram_window_handle, ctypes.byref(window_placement))

                is_window_minimized = user32.IsIconic(telegram_window_handle)

                if is_window_minimized:
                    window_state.translation_window.withdraw()
                else:
                    window_state.translation_window.deiconify()

                    if window_placement.showCmd != 1:
                        window_rectangle = window_placement.rcNormalPosition
                    else:
                        window_rectangle = ctypes.wintypes.RECT()
                        user32.GetWindowRect(telegram_window_handle, ctypes.byref(window_rectangle))

                    telegram_window_width = window_rectangle.right - window_rectangle.left
                    widget_x_position = window_rectangle.left
                    widget_y_position = window_rectangle.bottom + config.widget_y_offset

                    new_geometry = f"{telegram_window_width}x{config.widget_height}+{widget_x_position}+{widget_y_position}"
                    window_state.translation_window.geometry(new_geometry)

                    widget_window_handle = window_state.translation_window.winfo_id()
                    synchronize_window_z_order(telegram_window_handle, widget_window_handle, config)
            else:
                window_state.translation_window.withdraw()

        except Exception as e:
            print(f"Error updating widget position: {e}")

        time.sleep(0.1) 