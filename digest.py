from datetime import datetime, timezone, timedelta
from typing import List, Dict
import json

from clash_api import get_player, get_battlelog
from analysis import compute_win_rate, record_daily_progress, load_progress


def has_lucky_drop(battlelog: List[Dict]) -> bool:
    """Return True if a Lucky Drop chest appears in the log."""
    for b in battlelog:
        data = json.dumps(b).lower()
        if "lucky drop" in data:
            return True
    return False


def daily_digest_info(player_tag: str, progress_path: str = "progress.json") -> Dict:
    """Return today's trophy delta, league step delta and win rate."""
    player = get_player(player_tag)
    battles = get_battlelog(player_tag)
    record_daily_progress(
        battles,
        player.get("trophies", 0),
        player.get("leagueRank", 0),
        path=progress_path,
    )
    progress = load_progress(path=progress_path)
    if not progress:
        return {}
    today = progress[-1]
    delta_trophies = 0
    delta_step = 0
    if len(progress) > 1:
        prev = progress[-2]
        delta_trophies = today["trophies"] - prev.get("trophies", 0)
        delta_step = today.get("league_rank", 0) - prev.get("league_rank", 0)

    cutoff = datetime.now(timezone.utc) - timedelta(days=1)
    recent = [
        b
        for b in battles
        if datetime.strptime(b.get("battleTime"), "%Y%m%dT%H%M%S.000Z").replace(tzinfo=timezone.utc)
        > cutoff
    ]
    wr = compute_win_rate(recent)

    return {
        "date": today["date"],
        "trophies": today["trophies"],
        "delta_trophies": delta_trophies,
        "league_rank": today.get("league_rank", 0),
        "delta_step": delta_step,
        "win_rate": wr,
        "lucky_drop": has_lucky_drop(battles),
    }
