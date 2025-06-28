import ctypes
from minichat.telegram_integration import get_correct_telegram_hwnd, sync_z_order_with_telegram

# Windows API setup
user32 = ctypes.windll.user32

def win_event_callback(
    hWinEventHook: int,
    event: int,
    hwnd: int,
    idObject: int,
    idChild: int,
    dwEventThread: int,
    dwmsEventTime: int,
    config,
    window_state
) -> None:
    try:
        if event == config.EVENT_OBJECT_REORDER or event == config.EVENT_SYSTEM_FOREGROUND:
            if hwnd == get_correct_telegram_hwnd(window_state):
                if (
                    window_state.sam_mini_chat_win
                    and window_state.sam_mini_chat_win.winfo_exists()
                ):
                    widget_hwnd = window_state.sam_mini_chat_win.winfo_id()
                    sync_z_order_with_telegram(hwnd, widget_hwnd, config)
    except Exception as e:
        print(f"Error in win_event_callback: {e}")

def setup_z_order_monitoring(config, window_state) -> None:
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
            lambda hWinEventHook, event, hwnd, idObject, idChild, dwEventThread, dwmsEventTime: 
            win_event_callback(hWinEventHook, event, hwnd, idObject, idChild, dwEventThread, dwmsEventTime, config, window_state)
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