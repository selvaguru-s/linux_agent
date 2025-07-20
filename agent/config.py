import os
from dotenv import load_dotenv

load_dotenv()

CONFIG = {
    "OLLAMA_API_URL": os.getenv("OLLAMA_API_URL", "http://127.0.0.1:11434/api/generate"),
    "OLLAMA_MODEL": os.getenv("OLLAMA_MODEL", "deepseek-coder:6.7b"),
    "LOG_FILE": os.getenv("LOG_FILE", "agent.log"),
}
