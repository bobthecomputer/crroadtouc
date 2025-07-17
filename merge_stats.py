"""Helpers for the Merge Tactics mode (2025)."""
import os
import requests
from typing import List, Dict

ROYALE_API_BASE = "https://api.royaleapi.com"


def get_merge_leaderboard(limit: int = 100) -> List[Dict]:
    token = os.getenv("ROYALEAPI_TOKEN")
    if not token:
        raise RuntimeError("ROYALEAPI_TOKEN not set")
    url = f"{ROYALE_API_BASE}/leaderboards/merge?limit={limit}"
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(url, headers=headers, timeout=10)
    resp.raise_for_status()
    return resp.json().get("items", [])


def card_tier_list(stats: List[Dict]) -> List[Dict]:
    """Return cards sorted by win rate per turn."""
    graded = []
    for c in stats:
        turns = c.get("turns", 1)
        wr = c.get("wins", 0) / max(1, c.get("battles", 1))
        efficiency = wr / turns
        graded.append({"card": c.get("name"), "eff": efficiency})
    graded.sort(key=lambda x: x["eff"], reverse=True)
    return graded

