import unittest
import os
import gc_coach

class GCTests(unittest.TestCase):
    def test_run_lifecycle(self):
        run_id = gc_coach.start_run(["Knight", "Archers"])
        self.assertTrue(os.path.exists(os.path.join("gc_runs", f"{run_id}.json")))
        gc_coach.record_match(run_id, True, 6000)
        gc_coach.record_match(run_id, False, 6100)
        summary = gc_coach.summarize_run(run_id)
        self.assertEqual(summary['total'], 2)
        self.assertEqual(summary['wins'], 1)
        os.remove(os.path.join("gc_runs", f"{run_id}.json"))


    def test_get_gc_decks_filter(self):
        sample = {
            "items": [
                {"cards": ["Knight"], "winPercent": 70},
                {"cards": ["Archer"], "winPercent": 60},
            ]
        }
        from unittest.mock import patch

        with patch.dict(os.environ, {"ROYALEAPI_TOKEN": "t"}):
            with patch("requests.get") as mock_get:
                mock_get.return_value.json.return_value = sample
                mock_get.return_value.raise_for_status.return_value = None
                decks = gc_coach.get_gc_decks(limit=2, min_wr=0.45)
                self.assertEqual(len(decks), 1)
                self.assertEqual(decks[0]["cards"], ["Knight"])


