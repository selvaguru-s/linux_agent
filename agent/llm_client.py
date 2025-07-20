import requests
from agent.config import CONFIG

def get_command_from_llm(prompt: str) -> str:
    payload = {
        "model": CONFIG["OLLAMA_MODEL"],
        "prompt": prompt,
        "stream": False
    }
    response = requests.post(CONFIG["OLLAMA_API_URL"], json=payload)
    response.raise_for_status()
    return response.json()["response"].strip()


def chat_completion(prompt: str) -> str:
    payload = {
        "model": CONFIG["OLLAMA_MODEL"],
        "prompt": prompt,
        "stream": False
    }
    response = requests.post(CONFIG["OLLAMA_API_URL"], json=payload)
    response.raise_for_status()
    return response.json()["response"].strip()

def output_sum(prompt: str) -> str:
    payload = {
        "model": CONFIG["OLLAMA_MODEL"],
        "prompt": prompt,
        "stream": False
    }
    response = requests.post(CONFIG["OLLAMA_API_URL"], json=payload)
    response.raise_for_status()
    return response.json()["response"].strip()