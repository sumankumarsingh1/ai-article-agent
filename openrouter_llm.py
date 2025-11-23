# openrouter_llm.py
import os
import requests

class OpenRouterLLM:
    def __init__(self, model, api_key, base_url="https://openrouter.ai/api/v1"):
        self.model = model
        self.api_key = api_key
        self.base_url = base_url

    def invoke(self, prompt):
        # ✅ handle dict input (LangChain sometimes passes {'input': '...'})
        if isinstance(prompt, dict):
            if "input" in prompt:
                prompt = prompt["input"]
            elif "text" in prompt:
                prompt = prompt["text"]
            else:
                prompt = str(prompt)

        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:7860",  # optional
            "X-Title": "AI Article Agent"
        }

        data = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}]
        }

        response = requests.post(url, headers=headers, json=data)
        if response.status_code != 200:
            raise Exception(f"Error {response.status_code}: {response.text}")

        content = response.json()
        return content["choices"][0]["message"]["content"]
