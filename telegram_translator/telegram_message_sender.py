import ctypes
import time
import psutil
from typing import Optional
from ctypes import wintypes

# Windows API setup
user32 = ctypes.windll.user32

def find_telegram_window_handle(window_state) -> Optional[int]:
    """Find and return the handle of the active Telegram window"""
    foreground_window_handle = user32.GetForegroundWindow()
    process_id = ctypes.wintypes.DWORD()
    user32.GetWindowThreadProcessId(foreground_window_handle, ctypes.byref(process_id))

    try:
        process = psutil.Process(process_id.value)
        if process.name().lower() == "telegram.exe" and not user32.IsIconic(foreground_window_handle):
            window_state.last_valid_telegram_window_handle = foreground_window_handle
            return foreground_window_handle
    except Exception:
        pass

    if window_state.last_valid_telegram_window_handle is not None and not user32.IsIconic(
        window_state.last_valid_telegram_window_handle
    ):
        return window_state.last_valid_telegram_window_handle

    found_window_handle = None
    EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_int, ctypes.c_int)

    def enumerate_windows_callback(window_handle: int, _: int) -> bool:
        nonlocal found_window_handle
        if user32.IsWindowVisible(window_handle) and not user32.IsIconic(window_handle):
            local_process_id = ctypes.wintypes.DWORD()
            user32.GetWindowThreadProcessId(window_handle, ctypes.byref(local_process_id))
            try:
                process = psutil.Process(local_process_id.value)
                if process.name().lower() == "telegram.exe":
                    found_window_handle = window_handle
                    window_state.last_valid_telegram_window_handle = window_handle
                    return False
            except Exception:
                pass
        return True

    enum_proc_callback = EnumWindowsProc(enumerate_windows_callback)
    user32.EnumWindows(enum_proc_callback, 0)
    return found_window_handle

def send_message_to_telegram(window_handle: int, message_text: str, config, window_state) -> bool:
    """Send translated message to Telegram window using Windows API"""
    window_rectangle = ctypes.wintypes.RECT()
    user32.GetWindowRect(window_handle, ctypes.byref(window_rectangle))
    window_width = window_rectangle.right - window_rectangle.left
    click_x_position = window_rectangle.left + window_width // 2
    click_y_position = window_rectangle.bottom - 3

    # Click to focus the message input area
    user32.SetCursorPos(click_x_position, click_y_position)
    time.sleep(0.1)
    user32.mouse_event(2, 0, 0, 0, 0)  # Mouse down
    time.sleep(0.05)
    user32.mouse_event(4, 0, 0, 0, 0)  # Mouse up
    time.sleep(0.1)

    # Copy message to clipboard
    window_state.root.clipboard_clear()
    window_state.root.clipboard_append(message_text)
    window_state.root.update()
    time.sleep(0.1)

    # Get keyboard configuration
    keyboard_config = config.config.get("windows_api", {}).get("keyboard", {})
    VK_CONTROL = keyboard_config.get("VK_CONTROL", 17)
    VK_V = keyboard_config.get("VK_V", 86)
    VK_RETURN = keyboard_config.get("VK_RETURN", 13)

    # Paste message (Ctrl+V)
    user32.keybd_event(VK_CONTROL, 0, 0, 0)
    time.sleep(0.05)
    user32.keybd_event(VK_V, 0, 0, 0)
    time.sleep(0.05)
    user32.keybd_event(VK_V, 0, 2, 0)
    time.sleep(0.05)
    user32.keybd_event(VK_CONTROL, 0, 2, 0)
    time.sleep(0.1)
    
    # Send message (Enter)
    user32.keybd_event(VK_RETURN, 0, 0, 0)
    time.sleep(0.05)
    user32.keybd_event(VK_RETURN, 0, 2, 0)
    time.sleep(0.1)

    return True 