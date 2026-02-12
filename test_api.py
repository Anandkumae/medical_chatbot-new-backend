import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Check if API key is loaded
api_key = os.getenv('OPENROUTER_API_KEY')
print(f"API Key loaded: {bool(api_key)}")
if api_key:
    print(f"API Key starts with: {api_key[:20]}...")
else:
    print("API Key not found!")

# Test OpenRouter API call
import requests

if api_key:
    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": "mistralai/mistral-7b-instruct",
                "messages": [{"role": "user", "content": "Hello"}],
            },
        )
        print(f"API Response Status: {response.status_code}")
        if response.status_code == 200:
            print("API Key is working!")
        else:
            print(f"API Error: {response.text}")
    except Exception as e:
        print(f"API Call Failed: {e}")
