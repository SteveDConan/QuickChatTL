#!/usr/bin/env python3
"""
Test script to check API connections for XAI and ChatGPT
"""

import json
import os
import requests
from settings_manager import load_config

def test_xai_api(api_key, translation_config):
    """Test XAI API connection with configuration from translation_settings.json"""
    print("Testing XAI API connection...")
    
    xai_config = translation_config.get("xai", {})
    model = xai_config.get("model", "grok-3-mini")
    api_url = xai_config.get("api_url", "https://api.xai.com/v1/chat/completions")
    temperature = xai_config.get("temperature", 0.05)
    top_p = xai_config.get("top_p", 0.9)
    max_tokens = xai_config.get("max_tokens", 2000)
    
    print(f"  Using model: {model}")
    print(f"  Using endpoint: {api_url}")
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": model,
        "messages": [
            {"role": "user", "content": "Hello, this is a test message."}
        ],
        "temperature": temperature,
        "top_p": top_p,
        "max_tokens": 50  # Use smaller max_tokens for testing
    }
    
    try:
        response = requests.post(api_url, headers=headers, json=data, timeout=15)
        if response.status_code == 200:
            print("✅ XAI API connection successful!")
            # Show a bit of the response
            response_data = response.json()
            if 'choices' in response_data and len(response_data['choices']) > 0:
                content = response_data['choices'][0]['message']['content']
                print(f"  Response preview: {content[:100]}...")
            return True
        else:
            print(f"❌ XAI API connection failed. Status code: {response.status_code}")
            if response.status_code == 401:
                print("  ❌ Unauthorized - API key might be invalid")
            elif response.status_code == 404:
                print("  ❌ Endpoint not found")
            print(f"  Response: {response.text[:200]}...")
            return False
    except requests.exceptions.Timeout:
        print("  ⏰ Timeout")
        return False
    except requests.exceptions.ConnectionError:
        print("  🔌 Connection error")
        return False
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False

def test_chatgpt_api(api_key, translation_config):
    """Test ChatGPT API connection with configuration from translation_settings.json"""
    print("Testing ChatGPT API connection...")
    
    chatgpt_config = translation_config.get("chatgpt", {})
    model = chatgpt_config.get("model", "gpt-4o")
    api_url = chatgpt_config.get("api_url", "https://api.openai.com/v1/chat/completions")
    temperature = chatgpt_config.get("temperature", 0.05)
    top_p = chatgpt_config.get("top_p", 0.9)
    max_tokens = chatgpt_config.get("max_tokens", 2000)
    
    print(f"  Using model: {model}")
    print(f"  Using endpoint: {api_url}")
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": model,
        "messages": [
            {"role": "user", "content": "Hello, this is a test message."}
        ],
        "temperature": temperature,
        "top_p": top_p,
        "max_tokens": 50  # Use smaller max_tokens for testing
    }
    
    try:
        response = requests.post(api_url, headers=headers, json=data, timeout=15)
        if response.status_code == 200:
            print("✅ ChatGPT API connection successful!")
            # Show a bit of the response
            response_data = response.json()
            if 'choices' in response_data and len(response_data['choices']) > 0:
                content = response_data['choices'][0]['message']['content']
                print(f"  Response preview: {content[:100]}...")
            return True
        else:
            print(f"❌ ChatGPT API connection failed. Status code: {response.status_code}")
            if response.status_code == 401:
                print("  ❌ Unauthorized - API key might be invalid")
            print(f"  Response: {response.text[:200]}...")
            return False
    except Exception as e:
        print(f"❌ ChatGPT API connection error: {e}")
        return False

def test_api_key_format():
    """Test API key format validation"""
    print("🔍 Checking API key formats...")
    
    config = load_config()
    xai_api_key = config.get("xai_api_key", "")
    chatgpt_api_key = config.get("chatgpt_api_key", "")
    
    # Check XAI API key format
    if xai_api_key.startswith("xai-"):
        print("✅ XAI API key format looks correct (starts with 'xai-')")
    else:
        print("❌ XAI API key format might be incorrect (should start with 'xai-')")
    
    # Check ChatGPT API key format
    if chatgpt_api_key.startswith("sk-"):
        print("✅ ChatGPT API key format looks correct (starts with 'sk-')")
    else:
        print("❌ ChatGPT API key format might be incorrect (should start with 'sk-')")
    
    print()

def main():
    """Main test function"""
    print("🔍 Testing API Connections...")
    print("=" * 60)
    
    # Check API key formats first
    test_api_key_format()
    
    # Load configuration
    config = load_config()
    translation_config = config.get("translation_config", {})
    
    # Get API keys
    xai_api_key = config.get("xai_api_key", "")
    chatgpt_api_key = config.get("chatgpt_api_key", "")
    
    print(f"XAI API Key: {'✅ Found' if xai_api_key else '❌ Missing'}")
    print(f"ChatGPT API Key: {'✅ Found' if chatgpt_api_key else '❌ Missing'}")
    print()
    
    # Test connections
    xai_success = False
    chatgpt_success = False
    
    if xai_api_key:
        xai_success = test_xai_api(xai_api_key, translation_config)
    else:
        print("❌ XAI API key not found in config")
    
    print()
    
    if chatgpt_api_key:
        chatgpt_success = test_chatgpt_api(chatgpt_api_key, translation_config)
    else:
        print("❌ ChatGPT API key not found in config")
    
    print()
    print("=" * 60)
    print("📊 Test Results Summary:")
    print(f"XAI API: {'✅ Connected' if xai_success else '❌ Failed'}")
    print(f"ChatGPT API: {'✅ Connected' if chatgpt_success else '❌ Failed'}")
    
    if xai_success and chatgpt_success:
        print("🎉 All APIs are working correctly!")
    elif xai_success or chatgpt_success:
        print("⚠️  Some APIs are working, some failed")
    else:
        print("❌ All API connections failed")

if __name__ == "__main__":
    main() 