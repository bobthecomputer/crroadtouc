from typing import List, Callable, Dict
import random


def smart_swap(deck: List[str], card_pool: List[str], fitness: Callable[[List[str]], float], generations: int = 10, population: int = 6) -> List[Dict]:
    """Return best mutated decks using a simple genetic search."""
    best = [{"deck": deck, "score": fitness(deck)}]
    current = [deck]
    for _ in range(generations):
        next_pop = []
        for d in current:
            for _ in range(population):
                new = d.copy()
                idx = random.randrange(len(deck))
                new[idx] = random.choice(card_pool)
                if random.random() < 0.5:
                    idx2 = random.randrange(len(deck))
                    new[idx2] = random.choice(card_pool)
                next_pop.append(new)
        scored = [{"deck": nd, "score": fitness(nd)} for nd in next_pop]
        scored.sort(key=lambda x: x["score"], reverse=True)
        best.append(scored[0])
        current = [s["deck"] for s in scored[:3]]
    best.sort(key=lambda x: x["score"], reverse=True)
    return best[:3]


def upgrade_optimizer(levels: Dict[str, int], costs: Dict[str, int], gold: int) -> List[str]:
    """Return card names to upgrade for best ROI."""
    value = {card: (levels[card] + 1) / costs.get(card, 1) for card in levels}
    picks = []
    remaining = gold
    for card in sorted(value, key=value.get, reverse=True):
        price = costs.get(card, 0)
        if price <= remaining:
            remaining -= price
            picks.append(card)
    return picks
