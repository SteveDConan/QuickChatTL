import requests
import json
import os
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
        
        # Load prompts config
        self.prompts_config = self._load_prompts_config()

    def _load_prompts_config(self):
        """Load prompts configuration from prompts.json"""
        try:
            config_path = os.path.join("config", "prompts.json")
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading prompts config: {e}")
            return {}

    def _build_translation_prompt(self, text: str, target_lang: str) -> str:
        """Build translation prompt using config"""
        prompts_config = self.prompts_config.get("translation_prompt", {})
        
        lang_name = self.lang_map.get(target_lang.lower(), target_lang)
        system_prompt = prompts_config.get("system_prompt", "")
        task_description = prompts_config.get("task_description", "").format(lang_name=lang_name)
        requirements = prompts_config.get("requirements", [])
        content_wrapper = prompts_config.get("content_wrapper", {})
        
        # Build requirements string
        requirements_str = "\n".join([f"- {req}" for req in requirements])
        
        # Build full prompt
        prompt = (
            f"{system_prompt} "
            f"{task_description}\n"
            f"{requirements_str}\n"
            f"Đoạn cần dịch:\n"
            f"{content_wrapper.get('begin', '<<<BEGIN>>>')}\n"
            f"{text}\n"
            f"{content_wrapper.get('end', '<<<END>>>')}"
        )
        
        return prompt

    def translate_with_xai_api(
        self, text: str, target_lang: str = "vi"
    ) -> Tuple[Optional[str], Optional[str]]:
        """Translate text using XAI API"""
        if not self.xai_api_key:
            return text, None

        try:
            prompt = self._build_translation_prompt(text, target_lang)

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

    def translate_with_chatgpt_api(
        self, text: str, target_lang: str = "es"
    ) -> Tuple[Optional[str], Optional[str]]:
        """Translate text using ChatGPT API"""
        if not self.chatgpt_api_key:
            return text, None

        try:
            prompt = self._build_translation_prompt(text, target_lang)

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

    def translate_with_llm_api(
        self, text: str, target_lang: str = "vi", dialog_selector=None
    ) -> Tuple[Optional[str], Optional[str]]:
        """Translate text using LLM API"""
        if not self.llm_api_key:
            return None, "LLM API key not set"

        if not self.firebase_url:
            if dialog_selector:
                self.firebase_url = dialog_selector.request_firebase_url()
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

            prompt = self._build_translation_prompt(text, target_lang)

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
            return self.translate_with_xai_api(text, target_lang)
        elif selected_api == "ChatGPT":
            return self.translate_with_chatgpt_api(text, target_lang)
        elif selected_api == "LLM":
            return self.translate_with_llm_api(text, target_lang, dialog_selector)
        else:
            return text, f"Unknown API: {selected_api}" 