from typing import List, Dict


def compute_win_rate(battlelog: List[Dict]) -> float:
    if not battlelog:
        return 0.0
    wins = 0
    total = 0
    for battle in battlelog:
        if battle.get("type") != "PvP":
            continue
        team = battle.get("team", [{}])[0]
        opponent = battle.get("opponent", [{}])[0]
        if not team or not opponent:
            continue
        if team.get("crowns", 0) > opponent.get("crowns", 0):
            wins += 1
        total += 1
    return wins / total if total > 0 else 0.0


def compute_deck_rating(deck: List[str], card_data: List[Dict]) -> Dict:
    """Compute average elixir and a simple score with tips."""
    cost_lookup = {c["name"].lower(): c.get("elixirCost", 0) for c in card_data}
    total = 0
    count = 0
    for name in deck:
        cost = cost_lookup.get(name.strip().lower())
        if cost is None:
            continue
        total += cost
        count += 1
    avg = total / count if count else 0
    score = max(0.0, min(100.0, 100 - abs(avg - 3.5) * 20))
    tips = []
    if avg > 4.5:
        tips.append("Deck is heavy; consider cheaper cards.")
    elif avg < 3:
        tips.append("Deck may lack win conditions; add a heavier card.")
    return {"average_elixir": avg, "score": score, "tips": tips}

from datetime import datetime, timezone


def detect_tilt(battlelog: List[Dict], limit: int = 3, minutes: int = 15) -> bool:
    """Return True if the last `limit` battles are losses within `minutes`."""
    consecutive = 0
    first_time = None
    for battle in battlelog:
        if battle.get("type") != "PvP":
            continue
        team = battle.get("team", [{}])[0]
        opponent = battle.get("opponent", [{}])[0]
        if not team or not opponent:
            continue
        won = team.get("crowns", 0) > opponent.get("crowns", 0)
        ts_str = battle.get("battleTime")
        try:
            ts = datetime.strptime(ts_str, "%Y%m%dT%H%M%S.000Z").replace(tzinfo=timezone.utc)
        except Exception:
            break
        if not won:
            if consecutive == 0:
                first_time = ts
            consecutive += 1
            if consecutive >= limit:
                if (first_time - ts).total_seconds() <= minutes * 60:
                    return True
        else:
            break
    return False
