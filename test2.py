from openrouter_llm import OpenRouterLLM
import os
from dotenv import load_dotenv

load_dotenv()
llm = OpenRouterLLM("mistralai/mistral-7b-instruct:free", os.getenv("API_KEY"))
print(llm.invoke({"input": "Explain what an AI agent is"}))