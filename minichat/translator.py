import requests
from typing import Optional, Tuple
from config import load_config
from minichat.utils import remove_think_tags, fetch_ngrok_url


class Translator:
    def __init__(self):
        self.config = load_config()
        self.xai_api_key = self.config.get("xai_api_key", "")
        self.chatgpt_api_key = self.config.get("chatgpt_api_key", "")
        self.llm_api_key = self.config.get("llm_api_key", "")
        self.firebase_url = self.config.get("firebase_url", "")
        
        # Get language settings from config
        language_config = self.config.get("language_config", {})
        self.lang_map = language_config.get(
            "language_names", {"en": "Tiếng Anh", "vi": "Tiếng Việt"}
        )

    def translate_text_for_dialogue_xai(
        self, text: str, target_lang: str = "vi"
    ) -> Tuple[Optional[str], Optional[str]]:
        """Translate text using XAI API"""
        if not self.xai_api_key:
            return text, None

        try:
            lang_name = self.lang_map.get(target_lang.lower(), target_lang)
            prompt = (
                f"Bạn là một công cụ dịch ngôn ngữ chuyên nghiệp, am hiểu sâu sắc về văn hóa và phong cách giao tiếp tại địa phương của ngôn ngữ đích. "
                f"Bạn luôn cân nhắc ngữ cảnh và đối tượng nhận thông điệp khi chuyển ngữ. "
                f"Bối cảnh: Bạn là một tư vấn viên chuyên nghiệp, đang cung cấp dịch vụ và cần giao tiếp chính xác với khách hàng bằng ngôn ngữ đích. "
                f"Nhiệm vụ: dịch đúng phần nội dung nằm giữa các ký hiệu <<<BEGIN>>> và <<<END>>> sang {lang_name}, đảm bảo:\n"
                f"- Ngữ pháp hoàn chỉnh, từ vựng phù hợp, không thiếu/khuyết ý.\n"
                f"- Giữ nguyên cấu trúc câu, định dạng (xuống dòng, danh sách dấu đầu dòng, ký tự đặc biệt…) nếu có.\n"
                f"- Giọng điệu thân thiện nhưng vẫn lịch sự, tôn trọng, phù hợp với văn hóa bản địa của khách hàng.\n"
                f"- Xử lý thành ngữ, tục ngữ hay cách diễn đạt đặc thù sao cho tự nhiên trong ngôn ngữ đích.\n"
                f"- Nếu có thuật ngữ chuyên ngành hoặc tên sản phẩm/dịch vụ, giữ hoặc chú ý phiên âm/phương án thể hiện phù hợp.\n"
                f'- **Chỉ trả về phần nội dung dịch thuần túy, không thêm bất kỳ dấu ngoặc kép (" "") bao quanh cả đoạn,không kèm ký hiệu <<<BEGIN>>> hoặc <<<END>>> hoặc bất kỳ ký tự/thẻ, ký tự bổ sung nào khác**. '
                f" Nếu nội dung dịch có dấu ngoặc kép nội bộ do cấu trúc ngôn ngữ đích yêu cầu, chỉ giữ đúng vị trí của dấu đó, không thêm dấu bao bên ngoài.\n"
                f"- Không thêm bình luận, giải thích hay chú giải nào khác; chỉ output đúng văn bản dịch.\n"
                f"Đoạn cần dịch:\n"
                f"<<<BEGIN>>>\n"
                f"{text}\n"
                f"<<<END>>>"
            )

            headers = {
                "Authorization": f"Bearer {self.xai_api_key}",
                "Content-Type": "application/json",
            }

            translation_config = self.config.get("translation_config", {}).get("xai", {})
            payload = {
                "model": translation_config.get("model", "grok-beta"),
                "messages": [{"role": "user", "content": prompt}],
                "temperature": translation_config.get("temperature", 0.05),
                "top_p": translation_config.get("top_p", 0.9),
                "max_tokens": translation_config.get("max_tokens", 2000),
            }

            response = requests.post(
                translation_config.get("api_url", "https://api.x.ai/v1/chat/completions"),
                headers=headers,
                json=payload,
                timeout=10,
            )

            if response.status_code == 200:
                data = response.json()
                translated_text = data["choices"][0]["message"]["content"].strip()
                translated_text = remove_think_tags(translated_text)
                return translated_text, None
            else:
                return text, None

        except Exception as e:
            return text, None

    def translate_text_for_dialogue_chatgpt(
        self, text: str, target_lang: str = "es"
    ) -> Tuple[Optional[str], Optional[str]]:
        """Translate text using ChatGPT API"""
        if not self.chatgpt_api_key:
            return text, None

        try:
            lang_name = self.lang_map.get(target_lang.lower(), target_lang)
            prompt = (
                f"Bạn là một công cụ dịch ngôn ngữ chuyên nghiệp, am hiểu sâu sắc về văn hóa và phong cách giao tiếp tại địa phương của ngôn ngữ đích. "
                f"Bạn luôn cân nhắc ngữ cảnh và đối tượng nhận thông điệp khi chuyển ngữ. "
                f"Bối cảnh: Bạn là một tư vấn viên chuyên nghiệp, đang cung cấp dịch vụ và cần giao tiếp chính xác với khách hàng bằng ngôn ngữ đích. "
                f"Nhiệm vụ: dịch đúng phần nội dung nằm giữa các ký hiệu <<<BEGIN>>> và <<<END>>> sang {lang_name}, đảm bảo:\n"
                f"- Ngữ pháp hoàn chỉnh, từ vựng phù hợp, không thiếu/khuyết ý.\n"
                f"- Giữ nguyên cấu trúc câu, định dạng (xuống dòng, danh sách dấu đầu dòng, ký tự đặc biệt…) nếu có.\n"
                f"- Giọng điệu thân thiện nhưng vẫn lịch sự, tôn trọng, phù hợp với văn hóa bản địa của khách hàng.\n"
                f"- Xử lý thành ngữ, tục ngữ hay cách diễn đạt đặc thù sao cho tự nhiên trong ngôn ngữ đích.\n"
                f"- Nếu có thuật ngữ chuyên ngành hoặc tên sản phẩm/dịch vụ, giữ hoặc chú ý phiên âm/phương án thể hiện phù hợp.\n"
                f'- **Chỉ trả về phần nội dung dịch thuần túy, không thêm bất kỳ dấu ngoặc kép (" "") bao quanh cả đoạn,không kèm ký hiệu <<<BEGIN>>> hoặc <<<END>>> hoặc bất kỳ ký tự/thẻ, ký tự bổ sung nào khác**. '
                f" Nếu nội dung dịch có dấu ngoặc kép nội bộ do cấu trúc ngôn ngữ đích yêu cầu, chỉ giữ đúng vị trí của dấu đó, không thêm dấu bao bên ngoài.\n"
                f"- Không thêm bình luận, giải thích hay chú giải nào khác; chỉ output đúng văn bản dịch.\n"
                f"Đoạn cần dịch:\n"
                f"<<<BEGIN>>>\n"
                f"{text}\n"
                f"<<<END>>>"
            )

            headers = {
                "Authorization": f"Bearer {self.chatgpt_api_key}",
                "Content-Type": "application/json",
            }

            translation_config = self.config.get("translation_config", {}).get(
                "chatgpt", {}
            )
            payload = {
                "model": translation_config.get("model", "gpt-4"),
                "messages": [{"role": "user", "content": prompt}],
                "temperature": translation_config.get("temperature", 0.05),
                "top_p": translation_config.get("top_p", 0.9),
                "max_tokens": translation_config.get("max_tokens", 2000),
            }

            response = requests.post(
                translation_config.get(
                    "api_url", "https://api.openai.com/v1/chat/completions"
                ),
                headers=headers,
                json=payload,
                timeout=10,
            )

            if response.status_code == 200:
                data = response.json()
                translated_text = data["choices"][0]["message"]["content"].strip()
                translated_text = remove_think_tags(translated_text)
                return translated_text, None
            else:
                return text, None

        except Exception as e:
            return text, None

    def translate_text_for_dialogue_llm(
        self, text: str, target_lang: str = "vi", dialog_selector=None
    ) -> Tuple[Optional[str], Optional[str]]:
        """Translate text using LLM API"""
        if not self.llm_api_key:
            return None, "LLM API key not set"

        if not self.firebase_url:
            if dialog_selector:
                self.firebase_url = dialog_selector.prompt_for_firebase_url()
            if not self.firebase_url:
                return None, "Firebase URL not set"

        url = fetch_ngrok_url(self.firebase_url)
        if not url:
            return None, "Failed to fetch ngrok URL"

        try:
            api_url = f"{url}/v1/chat/completions"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.llm_api_key}",
            }

            lang_name = self.lang_map.get(target_lang.lower(), target_lang)
            prompt = (
                f"Bạn là một công cụ dịch ngôn ngữ chuyên nghiệp, am hiểu sâu sắc về văn hóa và phong cách giao tiếp tại địa phương của ngôn ngữ đích. "
                f"Bạn luôn cân nhắc ngữ cảnh và đối tượng nhận thông điệp khi chuyển ngữ. "
                f"Bối cảnh: Bạn là một tư vấn viên chuyên nghiệp, đang cung cấp dịch vụ và cần giao tiếp chính xác với khách hàng bằng ngôn ngữ đích. "
                f"Nhiệm vụ: dịch đúng phần nội dung nằm giữa các ký hiệu <<<BEGIN>>> và <<<END>>> sang {lang_name}, đảm bảo:\n"
                f"- Ngữ pháp hoàn chỉnh, từ vựng phù hợp, không thiếu/khuyết ý.\n"
                f"- Giữ nguyên cấu trúc câu, định dạng (xuống dòng, danh sách dấu đầu dòng, ký tự đặc biệt…) nếu có.\n"
                f"- Giọng điệu thân thiện nhưng vẫn lịch sự, tôn trọng, phù hợp với văn hóa bản địa của khách hàng.\n"
                f"- Xử lý thành ngữ, tục ngữ hay cách diễn đạt đặc thù sao cho tự nhiên trong ngôn ngữ đích.\n"
                f"- Nếu có thuật ngữ chuyên ngành hoặc tên sản phẩm/dịch vụ, giữ hoặc chú ý phiên âm/phương án thể hiện phù hợp.\n"
                f'- **Chỉ trả về phần nội dung dịch thuần túy, không thêm bất kỳ dấu ngoặc kép (" "") bao quanh cả đoạn,không kèm ký hiệu <<<BEGIN>>> hoặc <<<END>>> hoặc bất kỳ ký tự/thẻ, ký tự bổ sung nào khác**. '
                f" Nếu nội dung dịch có dấu ngoặc kép nội bộ do cấu trúc ngôn ngữ đích yêu cầu, chỉ giữ đúng vị trí của dấu đó, không thêm dấu bao bên ngoài.\n"
                f"- Không thêm bình luận, giải thích hay chú giải nào khác; chỉ output đúng văn bản dịch.\n"
                f"Đoạn cần dịch:\n"
                f"<<<BEGIN>>>\n"
                f"{text}\n"
                f"<<<END>>>"
            )

            translation_config = self.config.get("translation_config", {}).get("llm", {})
            payload = {
                "model": translation_config.get("model", "qwen3-8b"),
                "messages": [{"role": "user", "content": prompt}],
                "temperature": translation_config.get("temperature", 0.05),
                "top_p": translation_config.get("top_p", 0.9),
                "max_tokens": translation_config.get("max_tokens", 2000),
            }

            response = requests.post(api_url, headers=headers, json=payload, timeout=10)

            if response.status_code == 200:
                data = response.json()
                translated_text = data["choices"][0]["message"]["content"].strip()
                translated_text = remove_think_tags(translated_text)
                return translated_text, None
            else:
                return text, None

        except Exception as e:
            return text, None

    def translate_text(self, text: str, target_lang: str, selected_api: str, dialog_selector=None) -> Tuple[Optional[str], Optional[str]]:
        """Main translation method that routes to appropriate API based on selection"""
        if selected_api == "XAI":
            return self.translate_text_for_dialogue_xai(text, target_lang)
        elif selected_api == "ChatGPT":
            return self.translate_text_for_dialogue_chatgpt(text, target_lang)
        elif selected_api == "LLM":
            return self.translate_text_for_dialogue_llm(text, target_lang, dialog_selector)
        else:
            return text, f"Unknown API: {selected_api}" 