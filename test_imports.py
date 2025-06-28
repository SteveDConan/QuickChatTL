#!/usr/bin/env python3
"""
Test script to verify all imports work correctly after refactoring
"""

def test_all_imports():
    """Test all imports to ensure they work correctly"""
    print("Testing all imports...")
    
    try:
        # Test main imports
        from telegram_translator.app_initializer import app_config, app_window_state, translation_service
        print("✓ app_initializer imports successful")
        
        # Test language selector
        from telegram_translator.language_selector import LanguageAndApiSelector
        print("✓ language_selector imports successful")
        
        # Test message handler
        from telegram_translator.message_handler import process_and_send_translated_message, cleanup_translation_window
        print("✓ message_handler imports successful")
        
        # Test chat interface
        from telegram_translator.chat_interface import create_chat_window
        print("✓ chat_interface imports successful")
        
        # Test telegram client
        from telegram_translator.telegram_client import find_telegram_window_handle, send_message_to_telegram
        print("✓ telegram_client imports successful")
        
        # Test window events
        from telegram_translator.window_events import setup_window_monitoring
        print("✓ window_events imports successful")
        
        # Test translation service
        from telegram_translator.translation_service import Translator
        print("✓ translation_service imports successful")
        
        # Test helpers
        from telegram_translator.helpers import remove_think_tags, fetch_ngrok_url
        print("✓ helpers imports successful")
        
        # Test settings manager
        from settings_manager import load_config, save_config
        print("✓ settings_manager imports successful")
        
        print("\n🎉 All imports successful! Refactoring completed successfully.")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_class_instances():
    """Test that class instances can be created"""
    print("\nTesting class instances...")
    
    try:
        from telegram_translator.app_initializer import app_config, app_window_state, translation_service
        
        # Test that instances exist and have correct attributes
        assert hasattr(app_config, 'language_mapping'), "app_config missing language_mapping"
        assert hasattr(app_window_state, 'translation_window'), "app_window_state missing translation_window"
        assert hasattr(translation_service, 'language_mapping'), "translation_service missing language_mapping"
        
        print("✓ All class instances created successfully")
        return True
        
    except Exception as e:
        print(f"❌ Class instance error: {e}")
        return False

if __name__ == "__main__":
    print("=== Testing TelegramAuto Refactoring ===\n")
    
    imports_ok = test_all_imports()
    instances_ok = test_class_instances()
    
    if imports_ok and instances_ok:
        print("\n✅ All tests passed! The refactoring was successful.")
    else:
        print("\n❌ Some tests failed. Please check the errors above.") 