# API Keys Setup Guide

## Lỗi "Missing API Key" - Hướng dẫn khắc phục

### Vấn đề
Ứng dụng TelegramAuto yêu cầu các API keys để hoạt động, nhưng file `credentials.json` đang bị thiếu.

### Giải pháp

1. **Tạo file credentials.json:**
   - Copy file `credentials_template.json` 
   - Đổi tên thành `credentials.json`
   - Hoặc tạo file mới `config/credentials.json`

2. **Cấu trúc file credentials.json:**
```json
{
    "xai_api_key": "xai-your-actual-xai-api-key",
    "chatgpt_api_key": "sk-your-actual-chatgpt-api-key",
    "llm_api_key": "llm-your-actual-llm-api-key"
}
```

3. **Lấy API Keys:**

   **XAI API Key:**
   - Truy cập: https://x.ai/
   - Đăng ký tài khoản
   - Lấy API key từ dashboard
   - Format: `xai-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

   **ChatGPT API Key:**
   - Truy cập: https://platform.openai.com/
   - Đăng ký tài khoản
   - Tạo API key mới
   - Format: `sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

   **LLM API Key:**
   - Tùy thuộc vào dịch vụ LLM bạn sử dụng
   - Format: `llm-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

4. **Lưu ý bảo mật:**
   - Không commit file `credentials.json` vào git
   - File này đã được thêm vào `.gitignore`
   - Chỉ lưu trữ API keys trên máy local

5. **Kiểm tra:**
   - Sau khi tạo file, chạy lại ứng dụng
   - Lỗi "Missing API Key" sẽ biến mất

### Ví dụ file credentials.json hoàn chỉnh:
```json
{
    "xai_api_key": "xai-abc123def456ghi789jkl012mno345pqr678stu901vwx234yz",
    "chatgpt_api_key": "sk-abc123def456ghi789jkl012mno345pqr678stu901vwx234yz",
    "llm_api_key": "llm-abc123def456ghi789jkl012mno345pqr678stu901vwx234yz"
}
```

### Troubleshooting
- Đảm bảo file có tên chính xác: `credentials.json`
- Đảm bảo file nằm trong thư mục `config/`
- Kiểm tra format JSON hợp lệ
- Đảm bảo API keys có prefix đúng (xai-, sk-, llm-) 