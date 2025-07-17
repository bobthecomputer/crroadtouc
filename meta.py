import requests
import os
from typing import List, Dict, Iterable
from youtube_api import search_videos

ROYALE_API_BASE = "https://api.royaleapi.com"


def get_api_key() -> str:
    return os.getenv("ROYALEAPI_TOKEN", "")


def get_top_decks(limit: int = 1000) -> List[Dict]:
    """Return top decks from RoyaleAPI leaderboard."""
    token = get_api_key()
    if not token:
        raise RuntimeError("ROYALEAPI_TOKEN not set")
    url = f"{ROYALE_API_BASE}/player/top?limit={limit}"
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(url, headers=headers, timeout=10)
    resp.raise_for_status()
    return resp.json().get("items", [])


def meta_pulse(decks: Iterable[Dict], threshold: float = 0.05) -> List[Dict]:
    """Return decks with usage over a threshold."""
    trending = []
    for d in decks:
        if d.get("usage", 0) >= threshold:
            trending.append(d)
    return trending


PRO_CHANNELS = {
    "UCa-Y5sBjOlbwL6GzGkN6IBw",  # example channel IDs (e.g., Clash with Ash)
    "UCnS5iAw-Aw5XVKwIk98cNVQ",  # SirTag
}


def find_matchup_videos(deck_a: str, deck_b: str, max_results: int = 5) -> List[Dict]:
    """Search YouTube for pro matchup videos."""
    query = f"{deck_a} vs {deck_b} Clash Royale"
    videos = search_videos(query, max_results=max_results)
    if not videos:
        return []
    filtered = []
    for v in videos:
        if not PRO_CHANNELS:
            filtered.append(v)
        elif any(cid in v.get("channelId", "") for cid in PRO_CHANNELS):
            filtered.append(v)
    return filtered
