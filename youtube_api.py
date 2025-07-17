import os
import requests


DEFAULT_INVIDIOUS = "https://yewtu.be"


def search_videos(query: str, max_results: int = 5, base_url: str | None = None) -> list:
    """Return a list of video dicts using the Invidious API."""
    base = base_url or os.getenv("INVIDIOUS_BASE", DEFAULT_INVIDIOUS)
    params = {
        "q": query,
        "type": "video",
    }
    resp = requests.get(f"{base}/api/v1/search", params=params, timeout=10)
    resp.raise_for_status()
    items = resp.json()[:max_results]
    results = []
    for it in items:
        vid = it.get("videoId")
        if not vid:
            continue
        title = it.get("title", "")
        channel_id = it.get("authorId", "")
        results.append(
            {
                "title": title,
                "url": f"https://www.youtube.com/watch?v={vid}",
                "channelId": channel_id,
            }
        )
    return results
