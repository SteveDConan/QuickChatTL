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
    try:
        # Validate window handle
        if not user32.IsWindow(window_handle):
            print("Invalid window handle")
            return False
            
        # Ensure window is not minimized
        if user32.IsIconic(window_handle):
            user32.ShowWindow(window_handle, 9)  # SW_RESTORE
            time.sleep(0.2)
            
        # Bring window to front
        user32.SetForegroundWindow(window_handle)
        time.sleep(0.2)
        
        # Get window dimensions
        window_rectangle = ctypes.wintypes.RECT()
        if not user32.GetWindowRect(window_handle, ctypes.byref(window_rectangle)):
            print("Failed to get window rectangle")
            return False
            
        window_width = window_rectangle.right - window_rectangle.left
        window_height = window_rectangle.bottom - window_rectangle.top
        
        # Calculate better click position for message input area
        # Telegram input area is typically at the bottom center of the window
        # Adjust Y position to be higher from bottom to avoid clicking on status bar
        click_x_position = window_rectangle.left + window_width // 2
        click_y_position = window_rectangle.bottom - 50  # 50 pixels from bottom instead of 3
        
        # Validate click position
        if click_x_position < 0 or click_y_position < 0:
            print("Invalid click position calculated")
            return False

        # Click to focus the message input area
        user32.SetCursorPos(click_x_position, click_y_position)
        time.sleep(0.15)  # Increased delay for better reliability
        
        # Perform click with better timing
        user32.mouse_event(2, 0, 0, 0, 0)  # Mouse down
        time.sleep(0.08)
        user32.mouse_event(4, 0, 0, 0, 0)  # Mouse up
        time.sleep(0.15)

        # Copy message to clipboard with validation
        try:
            window_state.root.clipboard_clear()
            window_state.root.clipboard_append(message_text)
            window_state.root.update()
            time.sleep(0.15)
            
            # Verify clipboard content
            clipboard_content = window_state.root.clipboard_get()
            if clipboard_content != message_text:
                print("Clipboard content verification failed")
                return False
        except Exception as e:
            print(f"Clipboard operation failed: {e}")
            return False

        # Get keyboard configuration
        keyboard_config = config.config.get("windows_api", {}).get("keyboard", {})
        VK_CONTROL = keyboard_config.get("VK_CONTROL", 17)
        VK_V = keyboard_config.get("VK_V", 86)
        VK_RETURN = keyboard_config.get("VK_RETURN", 13)

        # Paste message (Ctrl+V) with better timing
        user32.keybd_event(VK_CONTROL, 0, 0, 0)
        time.sleep(0.08)
        user32.keybd_event(VK_V, 0, 0, 0)
        time.sleep(0.08)
        user32.keybd_event(VK_V, 0, 2, 0)
        time.sleep(0.08)
        user32.keybd_event(VK_CONTROL, 0, 2, 0)
        time.sleep(0.15)
        
        # Send message (Enter) with better timing
        user32.keybd_event(VK_RETURN, 0, 0, 0)
        time.sleep(0.08)
        user32.keybd_event(VK_RETURN, 0, 2, 0)
        time.sleep(0.15)

        return True
        
    except Exception as e:
        print(f"Error sending message to Telegram: {e}")
        return False 