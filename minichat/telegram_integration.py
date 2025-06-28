import ctypes
import time
import psutil
from typing import Optional
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

def get_telegram_window_handle(window_state) -> Optional[int]:
    hwnd_fore = user32.GetForegroundWindow()
    pid = ctypes.wintypes.DWORD()
    user32.GetWindowThreadProcessId(hwnd_fore, ctypes.byref(pid))

    try:
        proc = psutil.Process(pid.value)
        if proc.name().lower() == "telegram.exe" and not user32.IsIconic(hwnd_fore):
            window_state.last_valid_telegram_hwnd = hwnd_fore
            return hwnd_fore
    except Exception:
        pass

    if window_state.last_valid_telegram_hwnd is not None and not user32.IsIconic(
        window_state.last_valid_telegram_hwnd
    ):
        return window_state.last_valid_telegram_hwnd

    hwnd_result = None
    EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_int, ctypes.c_int)

    def enum_windows_proc(hwnd: int, _: int) -> bool:
        nonlocal hwnd_result
        if user32.IsWindowVisible(hwnd) and not user32.IsIconic(hwnd):
            pid_local = ctypes.wintypes.DWORD()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid_local))
            try:
                proc = psutil.Process(pid_local.value)
                if proc.name().lower() == "telegram.exe":
                    hwnd_result = hwnd
                    window_state.last_valid_telegram_hwnd = hwnd
                    return False
            except Exception:
                pass
        return True

    enum_proc_c = EnumWindowsProc(enum_windows_proc)
    user32.EnumWindows(enum_proc_c, 0)
    return hwnd_result

def send_message_to_telegram(hwnd: int, message: str, config, window_state) -> bool:
    rect = ctypes.wintypes.RECT()
    user32.GetWindowRect(hwnd, ctypes.byref(rect))
    width = rect.right - rect.left
    x = rect.left + width // 2
    y = rect.bottom - 3

    user32.SetCursorPos(x, y)
    time.sleep(0.1)
    user32.mouse_event(2, 0, 0, 0, 0)
    time.sleep(0.05)
    user32.mouse_event(4, 0, 0, 0, 0)
    time.sleep(0.1)

    window_state.root.clipboard_clear()
    window_state.root.clipboard_append(message)
    window_state.root.update()
    time.sleep(0.1)

    keyboard_config = config.config.get("windows_api", {}).get("keyboard", {})
    VK_CONTROL = keyboard_config.get("VK_CONTROL", 17)
    VK_V = keyboard_config.get("VK_V", 86)
    VK_RETURN = keyboard_config.get("VK_RETURN", 13)

    user32.keybd_event(VK_CONTROL, 0, 0, 0)
    time.sleep(0.05)
    user32.keybd_event(VK_V, 0, 0, 0)
    time.sleep(0.05)
    user32.keybd_event(VK_V, 0, 2, 0)
    time.sleep(0.05)
    user32.keybd_event(VK_CONTROL, 0, 2, 0)
    time.sleep(0.1)
    user32.keybd_event(VK_RETURN, 0, 0, 0)
    time.sleep(0.05)
    user32.keybd_event(VK_RETURN, 0, 2, 0)
    time.sleep(0.1)

    return True

def sync_window_z_order(telegram_hwnd: int, widget_hwnd: int, config) -> None:
    try:
        # Always set the widget to be topmost
        user32.SetWindowPos(
            widget_hwnd,
            config.HWND_TOPMOST,
            0,
            0,
            0,
            0,
            config.SWP_NOMOVE | config.SWP_NOSIZE | config.SWP_NOACTIVATE,
        )
    except Exception as e:
        print(f"Error syncing Z-order: {e}")

def update_widget_position(config, window_state):
    while (
        window_state.sam_mini_chat_win is not None
        and window_state.widget_sam_mini_chat_thread_running
    ):
        try:
            hwnd = get_telegram_window_handle(window_state)
            if hwnd:
                placement = WINDOWPLACEMENT()
                placement.length = ctypes.sizeof(WINDOWPLACEMENT)
                user32.GetWindowPlacement(hwnd, ctypes.byref(placement))

                is_minimized = user32.IsIconic(hwnd)

                if is_minimized:
                    window_state.sam_mini_chat_win.withdraw()
                else:
                    window_state.sam_mini_chat_win.deiconify()

                    if placement.showCmd != 1:
                        rect = placement.rcNormalPosition
                    else:
                        rect = ctypes.wintypes.RECT()
                        user32.GetWindowRect(hwnd, ctypes.byref(rect))

                    window_width = rect.right - rect.left
                    x = rect.left
                    y = rect.bottom + config.widget_y_offset

                    new_geometry = f"{window_width}x{config.widget_height}+{x}+{y}"
                    window_state.sam_mini_chat_win.geometry(new_geometry)

                    widget_hwnd = window_state.sam_mini_chat_win.winfo_id()
                    sync_window_z_order(hwnd, widget_hwnd, config)
            else:
                window_state.sam_mini_chat_win.withdraw()

        except Exception as e:
            print(f"Error updating widget position: {e}")

        time.sleep(0.1) 