import unittest
from datetime import datetime, timezone
from analysis import (
    compute_win_rate,
    compute_deck_rating,
    detect_tilt,
    analyze_cycle,
    aggro_meter,
    collect_event_stats,
    daily_event_wr,
    record_daily_progress,
    load_progress,
    progress_to_csv,
    reset_progress,
    card_cycle_trainer,
    elixir_diff_timeline,
    classify_playstyle,
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

    def test_collect_event_stats_and_daily_wr(self):
        log = [
            {
                "type": "challenge",
                "battleTime": "20240716T120000.000Z",
                "eventMode": {"id": 1},
                "team": [{"crowns": 1, "cards": [{"name": "Knight"}]}],
                "opponent": [{"crowns": 0}],
            },
            {
                "type": "challenge",
                "battleTime": "20240716T130000.000Z",
                "eventMode": {"id": 1},
                "team": [{"crowns": 0, "cards": [{"name": "Knight"}]}],
                "opponent": [{"crowns": 1}],
            },
        ]
        stats = collect_event_stats(log, path="/tmp/events.json")
        self.assertEqual(stats[0]["wins"], 1)
        wr = daily_event_wr(log, days=1000)
        self.assertTrue(wr)

    def test_record_and_load_progress(self):
        log = [
            {
                "type": "PvP",
                "team": [{"crowns": 1}],
                "opponent": [{"crowns": 0}],
                "battleTime": datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.000Z"),
            }
        ]
        path = "/tmp/progress.json"
        record_daily_progress(log, trophies=6000, league_rank=10, path=path)
        data = load_progress(path=path)
        self.assertTrue(data)

    def test_reset_and_export_progress(self):
        path = "/tmp/progress2.json"
        record_daily_progress([], trophies=5000, league_rank=5, path=path)
        data = load_progress(path=path)
        csv = progress_to_csv(data)
        self.assertIn("date", csv)
        reset_progress(path=path)
        self.assertFalse(load_progress(path=path))

    def test_card_cycle_trainer(self):
        deck = ["A", "B", "C", "D", "E", "F", "G", "H"]
        plays = ["A", "B", "C", "D"]
        hands = card_cycle_trainer(deck, plays)
        self.assertEqual(hands[0], ["A", "B", "C", "D"])
        self.assertEqual(hands[1], ["B", "C", "D", "E"])

    def test_elixir_diff_timeline(self):
        events = [
            {"time": 0, "side": "player", "elixir": 2},
            {"time": 1, "side": "opponent", "elixir": 3},
            {"time": 4, "side": "player", "elixir": 4},
        ]
        timeline = elixir_diff_timeline(events)
        self.assertAlmostEqual(timeline[-1]["diff"], timeline[-1]["player"] - timeline[-1]["opponent"])

    def test_classify_playstyle(self):
        deck = ["Hog Rider", "Ice Spirit", "Cannon", "Log"]
        style = classify_playstyle(deck)
        self.assertIn(style, {"Cycle", "Control", "Beatdown", "Bait", "Siege"})


if __name__ == "__main__":
    unittest.main()