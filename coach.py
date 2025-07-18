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

USE_QWEN = os.getenv("USE_QWEN_COACH", "0") == "1"


def heuristic_tips(ctx: Dict) -> str:
    msgs = []
    wr = ctx.get("win_rate", 0)
    if wr < 0.4:
        msgs.append("Low win rate; try a different deck.")
    elif wr > 0.6:
        msgs.append("Great job! Keep pushing.")
    if ctx.get("tilt"):
        msgs.append("Tilt detected. Take a short break.")
    if not msgs:
        msgs.append("Keep practicing and review your replays.")
    return " ".join(msgs)


def get_tips(ctx: Dict) -> str:
    if USE_QWEN:
        if ollama is None:
            raise RuntimeError("USE_QWEN_COACH set but ollama not installed")
        messages = [
            {"role": "system", "content": "Tu es coach Clash Royale."},
            {"role": "user", "content": str(ctx)},
        ]
        return request_coaching(messages)
    return heuristic_tips(ctx)