# Telegram Auto Translation Tool

A powerful tool for translating and sending messages via Telegram with automated translation services.

## Features

- **Multi-API Translation**: Support for XAI, ChatGPT, and LLM translation APIs
- **Telegram Integration**: Direct integration with Telegram Desktop
- **Real-time Translation**: Instant translation and message sending
- **Multi-language Support**: Vietnamese, English, and Chinese interfaces
- **Smart Window Management**: Automatic positioning and monitoring of Telegram windows
- **User-friendly Interface**: Modern, intuitive chat interface
- **Centralized Configuration**: All translation settings managed in one place

## Requirements

- Python 3.8+
- Telegram Desktop
- Windows OS
- API keys for translation services (XAI, ChatGPT, LLM)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/nunerit/TelegramAuto.git
cd TelegramAuto
```

2. Install required packages:
```bash
pip install -r requirements.txt
```

3. Configure your settings:
- Set up your API credentials in `config/api_keys.json`
- Adjust interface settings in `config/interface_settings.json`
- Configure translation settings in `config/translation_settings.json`

## Usage

1. Run the application:
```bash
python main.py
```

2. Main features:
- **Translation**: Enter text and get instant translation
- **Auto-send**: Automatically send translated messages to Telegram
- **Language Selection**: Choose target language for translation
- **API Selection**: Switch between different translation APIs

## Project Structure

```
project_root/
│
├── main.py                           # Main application entry point
├── settings_manager.py               # Configuration management
├── test_telegram_integration.py      # Integration testing
├── test_translation_config.py        # Translation config testing
│
├── telegram_translator/              # Core translation module
│   ├── __init__.py                   # Package initialization
│   ├── app_initializer.py           # Application initialization
│   ├── message_handler.py           # Message processing
│   ├── telegram_client.py           # Telegram integration
│   ├── translation_service.py       # Translation APIs
│   ├── chat_interface.py            # User interface
│   ├── language_selector.py         # Language selection
│   ├── window_events.py             # Window event handling
│   └── helpers.py                   # Utility functions
│
├── config/                          # Configuration files
│   ├── api_keys.json                # API keys and credentials
│   ├── ui_components.json           # UI component settings
│   ├── supported_languages.json     # Language configurations
│   ├── translation_settings.json    # Translation API configurations
│   ├── interface_settings.json      # Interface configurations
│   ├── telegram_window_config.json  # Telegram window settings
│   ├── translation_prompts.json     # Translation prompts
│   ├── TRANSLATION_CONFIG.md        # Translation config guide
│   └── README.md                    # Configuration documentation
│
├── README.md                        # This file
├── requirements.txt                 # Python dependencies
├── LICENSE                          # License information
└── app.spec                         # PyInstaller specification
```

## Configuration

### API Keys Setup
Edit `config/api_keys.json`:
```json
{
    "xai_api_key": "your-xai-api-key",
    "chatgpt_api_key": "your-chatgpt-api-key", 
    "llm_api_key": "your-llm-api-key"
}
```

### Translation Settings
Configure in `config/translation_settings.json`:
```json
{
    "xai": {
        "model": "grok-3-mini",
        "temperature": 0.05,
        "top_p": 0.9,
        "max_tokens": 2000,
        "api_url": "https://api.xai.com/v1/chat/completions"
    },
    "chatgpt": {
        "model": "gpt-4o",
        "temperature": 0.05,
        "top_p": 0.9,
        "max_tokens": 2000,
        "api_url": "https://api.openai.com/v1/chat/completions"
    },
    "llm": {
        "model": "qwen3-8b",
        "temperature": 0.05,
        "top_p": 0.9,
        "max_tokens": 2000
    }
}
```

## Configuration Management

### Centralized Translation Settings
All translation configurations are centralized in `config/translation_settings.json`:

- **Single Source of Truth**: All translation parameters (model, temperature, top_p, max_tokens, api_url) are managed in one file
- **Easy Maintenance**: Change settings without modifying code
- **Consistency**: All modules use the same configuration
- **Version Control**: Configuration changes are tracked with code

### Benefits of Centralized Configuration
1. **Unified Management**: All translation settings in one place
2. **Easy Updates**: Change models or parameters without code changes
3. **Consistency**: All components use identical settings
4. **Flexibility**: Switch between different models easily
5. **Testing**: Verify configuration with `test_translation_config.py`

### Testing Configuration
Run the configuration test to verify everything is working:
```bash
python test_translation_config.py
```

For detailed configuration guide, see `config/TRANSLATION_CONFIG.md`.

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a new Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Thanks to XAI, OpenAI, and LLM providers for translation APIs
- Telegram for the messaging platform
- All contributors and users of this tool

## Support

For support, please open an issue in the GitHub repository or contact the maintainers. 