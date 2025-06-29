# Translation Configuration Guide

File `translation_settings.json` chứa tất cả cấu hình cho các API dịch thuật được sử dụng trong ứng dụng.

## Cấu trúc cấu hình

### XAI API
```json
{
    "xai": {
        "model": "grok-3-mini",
        "temperature": 0.05,
        "top_p": 0.9,
        "max_tokens": 2000,
        "api_url": "https://api.xai.com/v1/chat/completions"
    }
}
```

### ChatGPT API
```json
{
    "chatgpt": {
        "model": "gpt-4o",
        "temperature": 0.05,
        "top_p": 0.9,
        "max_tokens": 2000,
        "api_url": "https://api.openai.com/v1/chat/completions"
    }
}
```

### LLM API
```json
{
    "llm": {
        "model": "qwen3-8b",
        "temperature": 0.05,
        "top_p": 0.9,
        "max_tokens": 2000
    }
}
```

## Các tham số cấu hình

### model
- **Mô tả**: Tên model AI được sử dụng cho dịch thuật
- **XAI**: `grok-3-mini`, `grok-beta`, `grok-1`, `grok-2`
- **ChatGPT**: `gpt-4o`, `gpt-4`, `gpt-3.5-turbo`
- **LLM**: `qwen3-8b`, `qwen2.5-7b`, `llama3-8b`

### temperature
- **Mô tả**: Độ sáng tạo của model (0.0 - 1.0)
- **Giá trị thấp**: Dịch thuật chính xác hơn, ít sáng tạo
- **Giá trị cao**: Dịch thuật linh hoạt hơn, nhiều sáng tạo
- **Khuyến nghị**: 0.05 cho dịch thuật chính xác

### top_p
- **Mô tả**: Nucleus sampling parameter (0.0 - 1.0)
- **Ảnh hưởng**: Chất lượng và đa dạng của output
- **Khuyến nghị**: 0.9 cho cân bằng giữa chất lượng và đa dạng

### max_tokens
- **Mô tả**: Số token tối đa trong response
- **Ảnh hưởng**: Độ dài của bản dịch
- **Khuyến nghị**: 2000 cho hầu hết trường hợp

### api_url
- **Mô tả**: URL endpoint của API
- **XAI**: `https://api.xai.com/v1/chat/completions`
- **ChatGPT**: `https://api.openai.com/v1/chat/completions`
- **LLM**: Không cần (sử dụng ngrok URL)

## Cách sử dụng trong code

### Trong translation_service.py
```python
def _get_translation_config(self, api_name: str) -> dict:
    """Get translation configuration for specific API"""
    translation_config = self.config.get("translation_config", {})
    return translation_config.get(api_name, {})

# Sử dụng
xai_config = self._get_translation_config("xai")
model = xai_config.get("model", "grok-3-mini")
temperature = xai_config.get("temperature", 0.05)
```

### Trong test_api_connection.py
```python
def test_xai_api(api_key, translation_config):
    xai_config = translation_config.get("xai", {})
    model = xai_config.get("model", "grok-3-mini")
    api_url = xai_config.get("api_url", "https://api.xai.com/v1/chat/completions")
```

## Lợi ích của việc tập trung cấu hình

1. **Quản lý tập trung**: Tất cả cấu hình translation ở một nơi
2. **Dễ bảo trì**: Thay đổi cấu hình không cần sửa code
3. **Tính nhất quán**: Đảm bảo tất cả module sử dụng cùng cấu hình
4. **Linh hoạt**: Dễ dàng thay đổi model, tham số mà không cần deploy lại
5. **Kiểm soát phiên bản**: Cấu hình được version control cùng với code

## Cách thay đổi cấu hình

1. **Thay đổi model**: Chỉnh sửa giá trị `model` trong file JSON
2. **Điều chỉnh chất lượng**: Thay đổi `temperature` và `top_p`
3. **Thay đổi độ dài**: Điều chỉnh `max_tokens`
4. **Cập nhật endpoint**: Thay đổi `api_url` nếu cần

## Lưu ý

- Sau khi thay đổi cấu hình, restart ứng dụng để áp dụng
- Kiểm tra API key tương ứng với model được chọn
- Test kết nối API sau khi thay đổi cấu hình
- Backup file cấu hình trước khi thay đổi lớn 