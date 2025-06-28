# Telegram Auto Translation Tool

A powerful tool for translating and sending messages via Telegram with automated translation services.

## Features

- **Multi-API Translation**: Support for XAI, ChatGPT, and LLM translation APIs
- **Telegram Integration**: Direct integration with Telegram Desktop
- **Real-time Translation**: Instant translation and message sending
- **Multi-language Support**: Vietnamese, English, and Chinese interfaces
- **Smart Window Management**: Automatic positioning and monitoring of Telegram windows
- **User-friendly Interface**: Modern, intuitive chat interface

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
- Set up your API credentials in `config/credentials.json`
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
│   ├── credentials.json             # API keys and credentials
│   ├── ui_components.json           # UI component settings
│   ├── supported_languages.json     # Language configurations
│   ├── translation_settings.json    # Translation preferences
│   ├── interface_settings.json      # Interface configurations
│   ├── telegram_window_config.json  # Telegram window settings
│   ├── translation_prompts.json     # Translation prompts
│   └── README.md                    # Configuration documentation
│
├── README.md                        # This file
├── requirements.txt                 # Python dependencies
├── LICENSE                          # License information
└── app.spec                         # PyInstaller specification
```

## Configuration

### API Keys Setup
Edit `config/credentials.json`:
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
    "default_target_language": "en",
    "preferred_api": "XAI",
    "translation_timeout": 30
}
```

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