from typing import Dict, List


def check_badges(history: List[int], goals: Dict[str, int]) -> List[str]:
    """Return badges achieved based on trophy history."""
    achieved = []
    current = history[-1] if history else 0
    for name, target in goals.items():
        if current >= target:
            achieved.append(name)
    return achieved


def update_goal_tracker(goals: Dict[str, int], trophies: int) -> None:
    """Simple persistence of trophy goals."""
    for name in list(goals.keys()):
        if trophies >= goals[name]:
            del goals[name]
