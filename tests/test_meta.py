import unittest
import meta
from meta import meta_pulse, find_matchup_videos, quartile_benchmarks

class MetaTests(unittest.TestCase):
    def test_meta_pulse(self):
        decks = [{"name": "Deck1", "usage": 0.06}, {"name": "Deck2", "usage": 0.03}]
        trending = meta_pulse(decks, threshold=0.05)
        self.assertEqual(len(trending), 1)
        self.assertEqual(trending[0]["name"], "Deck1")

    def test_find_matchup_videos(self):
        # this function just wraps search_videos; here we mock trivial result
        from meta import search_videos as real_search
        def fake_search(*args, **kwargs):
            return [{"title": "test", "url": "http://y.t", "channelId": "UCnS5iAw-Aw5XVKwIk98cNVQ"}]
        meta.search_videos = fake_search  # monkeypatch
        vids = find_matchup_videos("hog", "giant", max_results=1)
        self.assertTrue(vids)
        meta.search_videos = real_search

    def test_quartile_benchmarks(self):
        players = [
            {"rank_points": 6000, "win_rate": 0.6},
            {"rank_points": 5500, "win_rate": 0.55},
            {"rank_points": 5000, "win_rate": 0.52},
            {"rank_points": 4500, "win_rate": 0.5},
        ]
        qs = quartile_benchmarks(players)
        self.assertEqual(len(qs), 4)
        self.assertGreater(qs[0]["avg_win_rate"], qs[-1]["avg_win_rate"])

if __name__ == '__main__':
    unittest.main()
