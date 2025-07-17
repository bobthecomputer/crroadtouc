import os
import json
import requests
from typing import Optional, Dict, List
from clash_api import get_battlelog

WATCH_FILE = "watch.json"


def _load() -> Dict:
    try:
        with open(WATCH_FILE) as fh:
            return json.load(fh)
    except Exception:
        return {}


def _save(data: Dict) -> None:
    try:
        with open(WATCH_FILE, "w") as fh:
            json.dump(data, fh)
    except Exception:
        pass


def check_new_video(channel_id: str, base_url: str | None = None) -> Optional[Dict]:
    """Return latest video info if it differs from stored state."""
    base = base_url or os.getenv("INVIDIOUS_BASE", "https://yewtu.be")
    url = f"{base}/api/v1/channels/{channel_id}/latest"
    resp = requests.get(url, timeout=10)
    resp.raise_for_status()
    items = resp.json()
    if not items:
        return None
    latest = items[0]
    data = _load()
    last = data.get("video_last", {}).get(channel_id)
    if latest.get("videoId") != last:
        data.setdefault("video_last", {})[channel_id] = latest.get("videoId")
        _save(data)
        return {
            "title": latest.get("title"),
            "url": f"https://www.youtube.com/watch?v={latest.get('videoId')}"
        }
    return None


def _deck_from_battle(battle: Dict) -> List[str]:
    team = battle.get("team", [{}])[0]
    return [c.get("name") for c in team.get("cards", [])]


def check_deck_change(player_tag: str, similarity: float = 0.75) -> Optional[List[str]]:
    """Return latest deck if changed significantly since last check."""
    battles = get_battlelog(player_tag)
    if not battles:
        return None
    latest = tuple(sorted(_deck_from_battle(battles[0])))
    data = _load()
    prev = tuple(data.get("deck_last", {}).get(player_tag, ()))
    same = len(set(latest).intersection(prev)) / 8 if prev else 0.0
    if same < similarity:
        data.setdefault("deck_last", {})[player_tag] = list(latest)
        _save(data)
        return list(latest)
    return None
