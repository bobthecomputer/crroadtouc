import unittest
from unittest.mock import patch
import os
import player_watch

class WatchTests(unittest.TestCase):
    @patch('player_watch.requests.get')
    def test_check_new_video(self, mock_get):
        player_watch.WATCH_FILE = '/tmp/watch.json'
        if os.path.exists(player_watch.WATCH_FILE):
            os.remove(player_watch.WATCH_FILE)
        mock_get.return_value.json.return_value = [{'videoId': 'abc', 'title': 't'}]
        mock_get.return_value.raise_for_status.return_value = None
        vid = player_watch.check_new_video('cid', base_url='https://iv')
        self.assertIsNotNone(vid)
        vid2 = player_watch.check_new_video('cid', base_url='https://iv')
        self.assertIsNone(vid2)

    @patch('player_watch.get_battlelog')
    def test_check_deck_change(self, mock_log):
        player_watch.WATCH_FILE = '/tmp/watch2.json'
        if os.path.exists(player_watch.WATCH_FILE):
            os.remove(player_watch.WATCH_FILE)
        mock_log.return_value = [{
            'team': [{'cards': [{'name': c} for c in 'ABCDEFGH']}]
        }]
        deck = player_watch.check_deck_change('TAG')
        self.assertIsNotNone(deck)
        mock_log.return_value = [{
            'team': [{'cards': [{'name': c} for c in 'ABCDWXYZ']}]
        }]
        deck2 = player_watch.check_deck_change('TAG')
        self.assertIsNotNone(deck2)

