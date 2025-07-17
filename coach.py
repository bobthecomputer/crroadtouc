import os
from typing import List, Dict

try:
    import ollama
except Exception:  # pragma: no cover - optional dependency
    ollama = None


def get_model() -> str:
    """Return the Ollama model name."""
    return os.getenv("OLLAMA_MODEL", "qwen:7b")


def request_coaching(messages: List[Dict[str, str]]) -> str:
    """Send a chat completion request to a local Ollama server."""
    if ollama is None:
        raise RuntimeError("ollama package not installed")
    response = ollama.chat(model=get_model(), messages=messages)
    return response["message"]["content"]
