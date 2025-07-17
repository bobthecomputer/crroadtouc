import json
import os
import time
from typing import List, Dict


def _path(run_id: str) -> str:
    os.makedirs("gc_runs", exist_ok=True)
    return os.path.join("gc_runs", f"{run_id}.json")


def start_run(deck: List[str]) -> str:
    """Create a new Grand Challenge run and return its id."""
    run_id = str(int(time.time()))
    data = {"run_id": run_id, "deck": deck, "matches": []}
    with open(_path(run_id), "w") as fh:
        json.dump(data, fh)
    return run_id


def record_match(run_id: str, win: bool, opponent_elo: int) -> None:
    """Append a match result to the run."""
    path = _path(run_id)
    try:
        with open(path) as fh:
            data = json.load(fh)
    except Exception:
        return
    data.setdefault("matches", []).append({"win": win, "elo": opponent_elo})
    with open(path, "w") as fh:
        json.dump(data, fh)


def summarize_run(run_id: str) -> Dict:
    """Return win rate and opponent average elo for the run."""
    path = _path(run_id)
    with open(path) as fh:
        data = json.load(fh)
    matches = data.get("matches", [])
    wins = sum(1 for m in matches if m.get("win"))
    total = len(matches)
    avg_elo = sum(m.get("elo", 0) for m in matches) / total if total else 0
    return {"wins": wins, "total": total, "avg_elo": avg_elo}


def get_gc_decks(limit: int = 20) -> List[Dict]:
    """Fetch recent successful GC decks from RoyaleAPI."""
    token = os.getenv("ROYALEAPI_TOKEN")
    if not token:
        raise RuntimeError("ROYALEAPI_TOKEN not set")
    url = (
        "https://api.royaleapi.com/decks/popular?type=GC&time=7d&limit="
        f"{limit}"
    )
    headers = {"Authorization": f"Bearer {token}"}
    import requests

    resp = requests.get(url, headers=headers, timeout=10)
    resp.raise_for_status()
    return resp.json().get("items", [])
