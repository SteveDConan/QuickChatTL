import requests
import json
import os
import time
import re
from typing import Optional, Tuple
from settings_manager import load_config
from telegram_translator.helpers import remove_think_tags, fetch_ngrok_url


class Translator:
    def __init__(self):
        self.config = load_config()
        self.xai_api_key = self.config.get("xai_api_key", "")
        self.chatgpt_api_key = self.config.get("chatgpt_api_key", "")
        self.llm_api_key = self.config.get("llm_api_key", "")
        self.firebase_url = self.config.get("firebase_url", "")
        
        # Get language settings from config
        language_config = self.config.get("language_config", {})
        self.language_mapping = language_config.get(
            "language_names", {"en": "Tiếng Anh", "vi": "Tiếng Việt"}
        )
        
        # Load prompts config
        self.translation_prompts_config = self._load_translation_prompts_config()

    def _load_translation_prompts_config(self):
        """Load translation prompts configuration from translation_prompts.json"""
        try:
            config_path = os.path.join("config", "translation_prompts.json")
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading translation prompts config: {e}")
            return {}

    def _build_translation_prompt(self, source_text: str, target_language: str) -> str:
        """Build translation prompt using configuration"""
        prompts_config = self.translation_prompts_config.get("translation_prompt", {})
        
        target_language_name = self.language_mapping.get(target_language.lower(), target_language)
        system_prompt = prompts_config.get("system_prompt", "")
        task_description = prompts_config.get("task_description", "").format(lang_name=target_language_name)
        requirements = prompts_config.get("requirements", [])
        content_wrapper = prompts_config.get("content_wrapper", {})
        
        # Build requirements string
        requirements_string = "\n".join([f"- {requirement}" for requirement in requirements])
        
        # Build full prompt
        complete_prompt = (
            f"{system_prompt} "
            f"{task_description}\n"
            f"{requirements_string}\n"
            f"Đoạn cần dịch:\n"
            f"{content_wrapper.get('begin', '<<<BEGIN>>>')}\n"
            f"{source_text}\n"
            f"{content_wrapper.get('end', '<<<END>>>')}"
        )
        
        return complete_prompt

    def _get_translation_config(self, api_name: str) -> dict:
        """Get translation configuration for specific API from translation_settings.json"""
        translation_config = self.config.get("translation_config", {})
        return translation_config.get(api_name, {})

    def translate_with_xai_api(
        self, source_text: str, target_language: str = "vi"
    ) -> Tuple[Optional[str], Optional[str]]:
        """Translate text using XAI API"""
        if not self.xai_api_key:
            return source_text, None

        try:
            translation_prompt = self._build_translation_prompt(source_text, target_language)
            xai_config = self._get_translation_config("xai")

            request_headers = {
                "Authorization": f"Bearer {self.xai_api_key}",
                "Content-Type": "application/json",
            }

            request_payload = {
                "model": xai_config.get("model", "grok-3-mini"),
                "messages": [{"role": "user", "content": translation_prompt}],
                "temperature": xai_config.get("temperature", 0.05),
                "top_p": xai_config.get("top_p", 0.9),
                "max_tokens": xai_config.get("max_tokens", 2000),
            }

            api_response = requests.post(
                xai_config.get("api_url", "https://api.xai.com/v1/chat/completions"),
                headers=request_headers,
                json=request_payload,
                timeout=10,
            )

            if api_response.status_code == 200:
                response_data = api_response.json()
                translated_text = response_data["choices"][0]["message"]["content"].strip()
                translated_text = remove_think_tags(translated_text)
                return translated_text, None
            else:
                return source_text, None

        except Exception as e:
            return source_text, None

    def translate_with_chatgpt_api(
        self, source_text: str, target_language: str = "es"
    ) -> Tuple[Optional[str], Optional[str]]:
        """Translate text using ChatGPT API"""
        if not self.chatgpt_api_key:
            return source_text, None

        try:
            translation_prompt = self._build_translation_prompt(source_text, target_language)
            chatgpt_config = self._get_translation_config("chatgpt")

            request_headers = {
                "Authorization": f"Bearer {self.chatgpt_api_key}",
                "Content-Type": "application/json",
            }

            request_payload = {
                "model": chatgpt_config.get("model", "gpt-4o"),
                "messages": [{"role": "user", "content": translation_prompt}],
                "temperature": chatgpt_config.get("temperature", 0.05),
                "top_p": chatgpt_config.get("top_p", 0.9),
                "max_tokens": chatgpt_config.get("max_tokens", 2000),
            }

            api_response = requests.post(
                chatgpt_config.get("api_url", "https://api.openai.com/v1/chat/completions"),
                headers=request_headers,
                json=request_payload,
                timeout=10,
            )

            if api_response.status_code == 200:
                response_data = api_response.json()
                translated_text = response_data["choices"][0]["message"]["content"].strip()
                translated_text = remove_think_tags(translated_text)
                return translated_text, None
            else:
                return source_text, None

        except Exception as e:
            return source_text, None

    def translate_with_llm_api(
        self, source_text: str, target_language: str = "vi", dialog_selector=None
    ) -> Tuple[Optional[str], Optional[str]]:
        """Translate text using LLM API"""
        if not self.llm_api_key:
            return None, "LLM API key not set"

        if not self.firebase_url:
            if dialog_selector:
                self.firebase_url = dialog_selector.prompt_for_firebase_url()
            if not self.firebase_url:
                return None, "Firebase URL not set"

        ngrok_url = fetch_ngrok_url(self.firebase_url)
        if not ngrok_url:
            return None, "Failed to fetch ngrok URL"

        try:
            api_endpoint = f"{ngrok_url}/v1/chat/completions"
            request_headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.llm_api_key}",
            }

            translation_prompt = self._build_translation_prompt(source_text, target_language)
            llm_config = self._get_translation_config("llm")

            request_payload = {
                "model": llm_config.get("model", "qwen3-8b"),
                "messages": [{"role": "user", "content": translation_prompt}],
                "temperature": llm_config.get("temperature", 0.05),
                "top_p": llm_config.get("top_p", 0.9),
                "max_tokens": llm_config.get("max_tokens", 2000),
            }

            api_response = requests.post(api_endpoint, headers=request_headers, json=request_payload, timeout=10)

            if api_response.status_code == 200:
                response_data = api_response.json()
                translated_text = response_data["choices"][0]["message"]["content"].strip()
                translated_text = remove_think_tags(translated_text)
                return translated_text, None
            else:
                return source_text, None

        except Exception as e:
            return source_text, None

    def translate_text(self, source_text: str, target_language: str, selected_api: str, dialog_selector=None) -> Tuple[Optional[str], Optional[str]]:
        """Main translation method that routes to appropriate API based on selection"""
        if selected_api == "XAI":
            return self.translate_with_xai_api(source_text, target_language)
        elif selected_api == "ChatGPT":
            return self.translate_with_chatgpt_api(source_text, target_language)
        elif selected_api == "LLM":
            return self.translate_with_llm_api(source_text, target_language, dialog_selector)
        else:
            return source_text, f"Unknown API: {selected_api}" 