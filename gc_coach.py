import json
import os
import time
from typing import List, Dict
from analysis import classify_playstyle
import requests


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


def get_gc_decks(limit: int = 20, playstyle: str | None = None, min_wr: float = 0.45) -> List[Dict]:
    """Fetch recent GC decks filtered by win rate and optional playstyle.

    The threshold is the greater of ``min_wr`` and the 75th percentile of
    win rates among all decks returned by RoyaleAPI.
    """
    token = os.getenv("ROYALEAPI_TOKEN")
    if not token:
        raise RuntimeError("ROYALEAPI_TOKEN not set")
    url = "https://api.royaleapi.com/decks/popular?type=GC&time=7d&limit=100"
    headers = {"Authorization": f"Bearer {token}"}

    resp = requests.get(url, headers=headers, timeout=10)
    resp.raise_for_status()
    items = resp.json().get("items", [])

    win_rates = []
    for it in items:
        wr = it.get("winPercent") or it.get("win_pct") or it.get("wr") or 0
        if wr <= 1:
            wr *= 100
        win_rates.append(wr)

    threshold = min_wr * 100 if min_wr <= 1 else min_wr
    if win_rates:
        sr = sorted(win_rates)
        p75 = sr[int(len(sr) * 0.75)]
        threshold = max(threshold, p75)

    filtered = []
    for it in items:
        wr = it.get("winPercent") or it.get("win_pct") or it.get("wr") or 0
        wr = wr * 100 if wr <= 1 else wr
        if wr < threshold:
            continue
        deck_cards = it.get("cards", [])
        if playstyle and classify_playstyle(deck_cards) != playstyle:
            continue
        filtered.append(it)
        if len(filtered) >= limit:
            break
    return filtered