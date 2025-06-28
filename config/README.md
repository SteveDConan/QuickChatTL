# Configuration Files

Thư mục này chứa các file cấu hình được tách riêng cho ứng dụng TelegramAuto.

## Cấu trúc file

### `api_keys.json`
Chứa các API keys cho các dịch vụ dịch thuật:
- `xai_api_key`: API key cho XAI
- `chatgpt_api_key`: API key cho ChatGPT
- `llm_api_key`: URL Firebase cho LLM

### `widget.json`
Cấu hình cho giao diện widget:
- `height`: Chiều cao widget
- `y_offset`: Offset theo trục Y
- `window`: Cấu hình cửa sổ
- `style`: Style cho các thành phần UI
- `button_style`: Style cho nút gửi
- `quit_button_style`: Style cho nút thoát
- `option_menu_style`: Style cho menu lựa chọn
- `api_menu_style`: Style cho menu API
- `text_entry_style`: Style cho ô nhập text

### `language.json`
Cấu hình ngôn ngữ và dịch thuật:
- `my_lang`: Ngôn ngữ của người dùng
- `target_lang`: Ngôn ngữ đích
- `available_languages`: Danh sách ngôn ngữ có sẵn
- `language_names`: Tên hiển thị của các ngôn ngữ
- `quick_languages`: Ngôn ngữ nhanh
- `quick_language_style`: Style cho nút ngôn ngữ nhanh

### `translation.json`
Cấu hình cho các API dịch thuật:
- `xai`: Cấu hình cho XAI API
- `chatgpt`: Cấu hình cho ChatGPT API
- `llm`: Cấu hình cho LLM API

### `ui.json`
Cấu hình cho UI và animation:
- `loading_frames`: Các frame cho animation loading
- `loading_interval`: Khoảng thời gian giữa các frame
- `success_delay`: Delay cho animation thành công
- `error_delay`: Delay cho animation lỗi
- `animation`: Cấu hình animation

### `windows_api.json`
Cấu hình cho Windows API:
- `constants`: Các hằng số Windows API
- `keyboard`: Các phím tắt

## Cách sử dụng

Các file config được load tự động bởi hàm `load_config()` trong `config.py`. 
Để thay đổi cấu hình, chỉ cần chỉnh sửa file tương ứng trong thư mục này.

## Lưu ý

- Không commit các file config chứa API keys vào git
- Backup các file config trước khi thay đổi
- Đảm bảo format JSON hợp lệ khi chỉnh sửa 