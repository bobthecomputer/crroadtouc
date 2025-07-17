import unittest
from analysis import (
    compute_win_rate,
    compute_deck_rating,
    detect_tilt,
    analyze_cycle,
    aggro_meter,
)


class AnalysisTests(unittest.TestCase):
    def test_compute_win_rate(self):
        log = [
            {"type": "PvP", "team": [{"crowns": 1}], "opponent": [{"crowns": 0}]},
            {"type": "PvP", "team": [{"crowns": 0}], "opponent": [{"crowns": 2}]},
        ]
        self.assertAlmostEqual(compute_win_rate(log), 0.5)

    def test_compute_deck_rating(self):
        deck = ["Knight", "Archers", "Fireball", "Hog Rider"]
        card_data = [
            {"name": "Knight", "elixirCost": 3},
            {"name": "Archers", "elixirCost": 3},
            {"name": "Fireball", "elixirCost": 4},
            {"name": "Hog Rider", "elixirCost": 4},
        ]
        rating = compute_deck_rating(deck, card_data)
        self.assertEqual(rating["average_elixir"], 3.5)
        self.assertTrue(0 <= rating["score"] <= 100)

    def test_detect_tilt(self):
        log = [
            {
                "type": "PvP",
                "team": [{"crowns": 0}],
                "opponent": [{"crowns": 1}],
                "battleTime": "20240716T120100.000Z",
            },
            {
                "type": "PvP",
                "team": [{"crowns": 0}],
                "opponent": [{"crowns": 1}],
                "battleTime": "20240716T120000.000Z",
            },
            {
                "type": "PvP",
                "team": [{"crowns": 0}],
                "opponent": [{"crowns": 1}],
                "battleTime": "20240716T115900.000Z",
            },
        ]
        self.assertTrue(detect_tilt(log, limit=3, minutes=5))

    def test_analyze_cycle(self):
        plays = [
            {"time": 0, "side": "player", "card": "fireball"},
            {"time": 1, "side": "player", "card": "archer"},
            {"time": 2, "side": "player", "card": "knight"},
            {"time": 3, "side": "player", "card": "hog rider"},
        ]
        result = analyze_cycle(plays)
        self.assertTrue(result["anti_air"])
        self.assertTrue(result["spell"])
        self.assertTrue(result["wincon"])

    def test_aggro_meter(self):
        events = [
            {"time": 5, "side": "player", "elixir": 3},
            {"time": 10, "side": "opponent", "elixir": 2},
            {"time": 20, "side": "player", "elixir": 4},
            {"time": 25, "side": "opponent", "elixir": 4},
        ]
        ratio = aggro_meter(events, seconds=30)
        self.assertAlmostEqual(ratio, 7 / 6)


if __name__ == "__main__":
    unittest.main()
