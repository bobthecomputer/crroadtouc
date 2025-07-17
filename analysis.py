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

# --- Coaching utilities ---

ANTI_AIR = {
    "archer", "minions", "minion horde", "musketeer", "baby dragon",
    "inferno dragon", "electro dragon", "wizard", "electro wizard",
    "flying machine", "hunter", "archer queen", "mega minion",
    "phoenix", "bats", "firecracker",
}

SPELLS = {
    "fireball", "rocket", "lightning", "zap", "arrows", "log",
    "snowball", "poison", "freeze", "earthquake", "barbarian barrel",
    "giant snowball",
}

WIN_CONDITIONS = {
    "hog rider", "royal giant", "giant", "golem", "graveyard",
    "balloon", "mega knight", "mortar", "x-bow", "lava hound",
    "elixir golem", "goblin barrel", "battle ram", "ram rider",
    "royal hogs", "electro giant", "miner", "skeleton barrel",
}


def classify_card(name: str) -> Dict[str, bool]:
    n = name.lower()
    return {
        "anti_air": n in ANTI_AIR,
        "spell": n in SPELLS,
        "wincon": n in WIN_CONDITIONS,
    }


def analyze_cycle(plays: List[Dict[str, str]], window: int = 4) -> Dict[str, bool]:
    """Check if at any point the player lacks a role in a hand-sized window."""
    hand: List[str] = []
    issues = {"anti_air": False, "spell": False, "wincon": False}
    for play in plays:
        if play.get("side") != "player":
            continue
        card = play.get("card", "").lower()
        hand.append(card)
        if len(hand) > window:
            hand.pop(0)
        if len(hand) < window:
            continue
        roles = {"anti_air": False, "spell": False, "wincon": False}
        for c in hand:
            cls = classify_card(c)
            for k, v in cls.items():
                if v:
                    roles[k] = True
        for k in issues:
            if not roles[k]:
                issues[k] = True
    return {k: not v for k, v in issues.items()}


def aggro_meter(events: List[Dict], seconds: int = 60) -> float:
    """Return ratio of elixir spent by player vs opponent in first `seconds`."""
    player = 0.0
    opp = 0.0
    for e in events:
        t = e.get("time", 0)
        if t > seconds:
            continue
        elixir = float(e.get("elixir", 0))
        if e.get("side") == "player":
            player += elixir
        elif e.get("side") == "opponent":
            opp += elixir
    return player / opp if opp > 0 else float("inf")

# --- Event tracker utilities ---
import json
from datetime import timedelta


def collect_event_stats(battlelog: List[Dict], path: str = "event_stats.json") -> List[Dict]:
    """Collect win/loss counts for non-ranked modes and persist to JSON."""
    stats: Dict[str, Dict] = {}
    for battle in battlelog:
        if battle.get("type") == "PvP" or battle.get("type") == "ranked":
            continue
        event = battle.get("eventMode", {})
        event_id = str(event.get("id", event.get("name", "unknown")))
        team = battle.get("team", [{}])[0]
        opp = battle.get("opponent", [{}])[0]
        won = team.get("crowns", 0) > opp.get("crowns", 0)
        entry = stats.setdefault(
            event_id,
            {
                "event_id": event_id,
                "wins": 0,
                "losses": 0,
                "deck": [c.get("name") for c in team.get("cards", [])],
                "date": battle.get("battleTime"),
            },
        )
        if won:
            entry["wins"] += 1
        else:
            entry["losses"] += 1
        entry["date"] = battle.get("battleTime")
    for entry in stats.values():
        total = entry["wins"] + entry["losses"]
        entry["WR"] = entry["wins"] / total if total else 0
    results = list(stats.values())
    try:
        with open(path, "w") as fh:
            json.dump(results, fh)
    except Exception:
        pass
    return results


def daily_event_wr(battlelog: List[Dict], days: int = 30) -> List[Dict]:
    """Return daily win rate for events in the last `days`."""
    start = datetime.utcnow() - timedelta(days=days)
    by_date: Dict[str, Dict[str, int]] = {}
    for battle in battlelog:
        if battle.get("type") == "PvP" or battle.get("type") == "ranked":
            continue
        ts_str = battle.get("battleTime")
        try:
            ts = datetime.strptime(ts_str, "%Y%m%dT%H%M%S.000Z")
        except Exception:
            continue
        if ts < start:
            continue
        date_key = ts.date().isoformat()
        team = battle.get("team", [{}])[0]
        opp = battle.get("opponent", [{}])[0]
        won = team.get("crowns", 0) > opp.get("crowns", 0)
        rec = by_date.setdefault(date_key, {"wins": 0, "total": 0})
        if won:
            rec["wins"] += 1
        rec["total"] += 1
    chart = []
    for date in sorted(by_date.keys()):
        rec = by_date[date]
        wr = rec["wins"] / rec["total"] if rec["total"] else 0
        chart.append({"date": date, "win_rate": wr})
    return chart
