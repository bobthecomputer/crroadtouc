import os
import requests

API_BASE = "https://api.clashroyale.com/v1"


def get_auth_headers():
    token = os.getenv("CLASH_ROYALE_TOKEN")
    if not token:
        raise RuntimeError("CLASH_ROYALE_TOKEN environment variable not set")
    return {"Authorization": f"Bearer {token}"}


def get_player(player_tag: str) -> dict:
    url = f"{API_BASE}/players/%23{player_tag.upper()}"
    resp = requests.get(url, headers=get_auth_headers(), timeout=10)
    resp.raise_for_status()
    return resp.json()


def get_battlelog(player_tag: str) -> list:
    url = f"{API_BASE}/players/%23{player_tag.upper()}/battlelog"
    resp = requests.get(url, headers=get_auth_headers(), timeout=10)
    resp.raise_for_status()
    return resp.json()


def get_cards() -> list:
    """Return all cards with their stats."""
    url = f"{API_BASE}/cards"
    resp = requests.get(url, headers=get_auth_headers(), timeout=10)
    resp.raise_for_status()
    return resp.json().get("items", [])
