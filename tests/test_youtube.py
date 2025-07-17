import unittest
from unittest.mock import patch
import youtube_api

class YouTubeTests(unittest.TestCase):
    @patch("youtube_api.requests.get")
    def test_search_videos(self, mock_get):
        mock_get.return_value.json.return_value = [
            {"videoId": "abc", "title": "test", "authorId": "ch"}
        ]
        mock_get.return_value.raise_for_status.return_value = None
        vids = youtube_api.search_videos("query", max_results=1, base_url="https://iv.example")
        self.assertEqual(len(vids), 1)
        self.assertEqual(vids[0]["url"], "https://www.youtube.com/watch?v=abc")

if __name__ == '__main__':
    unittest.main()
