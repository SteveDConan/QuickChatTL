# Import functions from separated modules
from telegram_translator.telegram_message_sender import find_telegram_window_handle, send_message_to_telegram
from telegram_translator.widget_position_manager import synchronize_window_z_order, update_widget_position

# Re-export functions for backward compatibility
__all__ = [
    'find_telegram_window_handle',
    'send_message_to_telegram', 
    'synchronize_window_z_order',
    'update_widget_position'
] 