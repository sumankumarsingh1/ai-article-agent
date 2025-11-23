import os
import json
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

from langchain_community.llms import OpenAI
from langchain_ollama import OllamaLLM


# Load environment variables from .env
load_dotenv()
OPENROUTER_API_KEY = os.getenv("API_KEY")

def load_model(model_name):
    with open("models.json") as f:
        data = json.load(f)
    
    for model in data["models"]:
        if model["name"] == model_name:
            params = model["params"]
            if model["type"] == "ollama":
                return OllamaLLM(model=params["model"], base_url=params["base_url"])
            elif model["type"] == "openrouter":
                return ChatOpenAI(
                    model=params["model"],
                    base_url=params["base_url"],
                    api_key=OPENROUTER_API_KEY
                )

    raise ValueError("Model not found in configuration")
