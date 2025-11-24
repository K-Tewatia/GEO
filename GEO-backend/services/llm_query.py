import os
import requests
from dotenv import load_dotenv



load_dotenv()

API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

def query_gpt(prompt: str, model: str = "openrouter/auto") -> str:
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "HTTP-Referer": "https://yourprojectname.com",  # any string is okay
        "X-Title": "AI Prompt Visibility Generator"
    }

    payload = {
        "model": model,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 512,       # ✅ REQUIRED by some models
        "temperature": 0.6        # Optional: adjust creativity
    }

    response = requests.post(OPENROUTER_URL, headers=headers, json=payload)

    if response.status_code != 200:
        raise Exception(f"OpenRouter error {response.status_code}: {response.text}")

    return response.json()["choices"][0]["message"]["content"]
