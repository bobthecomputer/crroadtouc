from typing import List, Dict
import io
import csv
from datetime import datetime, timezone, timedelta
import json


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


def classify_playstyle(deck: List[str]) -> str:
    """Return a simple playstyle category."""
    avg_cost = 0
    spells = buildings = wincon = 0
    for card in deck:
        c = card.lower()
        if c in SPELLS:
            spells += 1
        if "building" in c:
            buildings += 1
        if c in WIN_CONDITIONS:
            wincon += 1
        avg_cost += 1
    avg_cost = avg_cost / len(deck) if deck else 0
    if buildings > 0 and wincon <= 1:
        return "Siege"
    if avg_cost <= 3.0:
        return "Cycle"
    if spells >= 3:
        return "Control"
    if avg_cost >= 4.0:
        return "Beatdown"
    return "Bait"

# --- Event tracker utilities ---

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
    start = datetime.now(timezone.utc) - timedelta(days=days)
    by_date: Dict[str, Dict[str, int]] = {}
    for battle in battlelog:
        if battle.get("type") == "PvP" or battle.get("type") == "ranked":
            continue
        ts_str = battle.get("battleTime")
        try:
            ts = datetime.strptime(ts_str, "%Y%m%dT%H%M%S.000Z").replace(tzinfo=timezone.utc)
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


# --- Daily progress utilities ---
def record_daily_progress(
    battlelog: List[Dict],
    trophies: int,
    league_rank: int,
    path: str = "progress.json",
) -> None:
    """Append today's trophy count, league rank and win rate to the progress file."""
    today = datetime.now(timezone.utc).date().isoformat()
    wr = compute_win_rate(
        [b for b in battlelog if b.get("battleTime", "").startswith(today.replace("-", ""))]
    )
    entry = {
        "date": today,
        "trophies": trophies,
        "league_rank": league_rank,
        "win_rate": wr,
    }
    try:
        with open(path) as fh:
            data = json.load(fh)
    except Exception:
        data = []
    # overwrite if today's entry exists
    data = [d for d in data if d.get("date") != today]
    data.append(entry)
    try:
        with open(path, "w") as fh:
            json.dump(sorted(data, key=lambda d: d["date"]), fh)
    except Exception:
        pass


def load_progress(path: str = "progress.json") -> List[Dict]:
    """Return list of recorded progress entries."""
    try:
        with open(path) as fh:
            return json.load(fh)
    except Exception:
        return []


def reset_progress(path: str = "progress.json") -> None:
    """Clear all recorded progress."""
    try:
        with open(path, "w") as fh:
            fh.write("[]")
    except Exception:
        pass


def progress_to_csv(data: List[Dict]) -> str:
    """Return CSV representation of progress entries."""
    if not data:
        return ""
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=["date", "trophies", "league_rank", "win_rate"])
    writer.writeheader()
    writer.writerows(data)
    return output.getvalue()


def card_cycle_trainer(deck: List[str], plays: List[str]) -> List[List[str]]:
    """Return the hand (first four cards) before each play."""
    cycle = deck.copy()
    hands = []
    for card in plays:
        hands.append(cycle[:4])
        if card in cycle:
            cycle.remove(card)
            cycle.append(card)
    return hands


ELIXIR_REGEN = 1 / 2.8

def elixir_diff_timeline(events: List[Dict]) -> List[Dict]:
    """Return timeline of elixir difference (player - opponent)."""
    events = sorted(events, key=lambda e: e.get("time", 0))
    player = opp = 5.0
    t_prev = 0.0
    timeline = []
    for e in events:
        t = float(e.get("time", 0))
        dt = t - t_prev
        player = min(10.0, player + dt * ELIXIR_REGEN)
        opp = min(10.0, opp + dt * ELIXIR_REGEN)
        spent = float(e.get("elixir", 0))
        if e.get("side") == "player":
            player -= spent
        else:
            opp -= spent
        timeline.append({"time": t, "diff": player - opp, "player": player, "opponent": opp})
        t_prev = t
    return timeline