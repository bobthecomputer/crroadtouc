import os
import requests

YOUTUBE_API_BASE = "https://www.googleapis.com/youtube/v3"


def get_api_key() -> str:
    key = os.getenv("YOUTUBE_API_KEY")
    if not key:
        raise RuntimeError("YOUTUBE_API_KEY environment variable not set")
    return key


def search_videos(query: str, max_results: int = 5) -> list:
    """Return a list of video dicts with title and url."""
    params = {
        "part": "snippet",
        "type": "video",
        "q": query,
        "order": "date",
        "maxResults": max_results,
        "key": get_api_key(),
    }
    resp = requests.get(f"{YOUTUBE_API_BASE}/search", params=params, timeout=10)
    resp.raise_for_status()
    items = resp.json().get("items", [])
    results = []
    for it in items:
        vid = it.get("id", {}).get("videoId")
        if not vid:
            continue
        title = it.get("snippet", {}).get("title", "")
        results.append({"title": title, "url": f"https://www.youtube.com/watch?v={vid}"})
    return results
