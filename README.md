# Telegram Auto Tool

A powerful tool for managing multiple Telegram accounts with automated login, live checking, and ChatGPT integration.

## Features

- **Multi-Account Management**: Handle multiple Telegram accounts efficiently
- **Automated Login**: Bulk login with Telethon support
- **Live Status Checking**: Verify account status automatically
- **ChatGPT Integration**: AI-powered chat assistance
- **Window Management**: Arrange and manage Telegram windows
- **Multi-language Support**: Vietnamese, English, and Chinese interfaces

## Requirements

- Python 3.8+
- Telegram Desktop
- Windows OS

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
- Set up your Telegram API credentials in `core/config.py`
- Adjust window sizes and paths in settings
- Configure ChatGPT API key if needed

## Usage

1. Run the application:
```bash
python app.py
```

2. Main features:
- **Login**: Bulk login to multiple Telegram accounts
- **Check Live**: Verify account status
- **Window Management**: Arrange Telegram windows
- **Settings**: Configure paths, window sizes, and API keys

## Project Structure

```
project_root/
│
├── app.py                      # Main application entry point
├── core/
│   ├── config.py              # Configuration variables
│   ├── session_utils.py       # Session management
│   ├── telegram_utils.py      # Telegram window utilities
│   ├── image_utils.py         # Image processing utilities
│   ├── update_utils.py        # Update checking
│   └── language.py            # Language localization
│
├── ui/
│   ├── login_ui.py           # Login interface
│   ├── check_live_ui.py      # Live checking interface
│   ├── main_ui.py            # Main application UI
│   └── settings_ui.py        # Settings interface
│
├── mini_chat/                # ChatGPT integration
│   └── mini_chat.py
│
├── assets/                   # Resources and configs
├── README.md                # This file
└── requirements.txt         # Python dependencies
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

- Thanks to Telethon for the Telegram client functionality
- OpenAI for ChatGPT integration
- All contributors and users of this tool

## Support

For support, please open an issue in the GitHub repository or contact the maintainers. 