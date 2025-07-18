import unittest
from unittest.mock import patch
import digest

class DigestTests(unittest.TestCase):
    @patch('digest.get_battlelog')
    @patch('digest.get_player')
    def test_daily_digest_info(self, mock_player, mock_log):
        import json
        with open("/tmp/prog.json", "w") as fh:
            json.dump([{"date": "2024-07-15", "trophies": 5900, "league_rank": 5, "win_rate": 0.5}], fh)
        mock_player.return_value = {'trophies': 6000, 'leagueRank': 6}
        mock_log.return_value = [
            {
                'type': 'PvP',
                'team': [{'crowns': 1}],
                'opponent': [{'crowns': 0}],
                'battleTime': '20240716T120000.000Z',
            }
        ]
        info = digest.daily_digest_info('TAG', progress_path='/tmp/prog.json')
        self.assertEqual(info['delta_trophies'], 100)
        self.assertEqual(info['delta_step'], 1)

    def test_has_lucky_drop(self):
        log = [{"chest": "Lucky Drop"}]
        self.assertTrue(digest.has_lucky_drop(log))

if __name__ == '__main__':
    unittest.main()
