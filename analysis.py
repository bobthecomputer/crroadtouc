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
