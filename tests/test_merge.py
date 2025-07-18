import unittest
from merge_stats import card_tier_list

class MergeTests(unittest.TestCase):
    def test_card_tier_list(self):
        stats = [
            {'name': 'A', 'wins': 5, 'battles': 10, 'turns': 2},
            {'name': 'B', 'wins': 8, 'battles': 10, 'turns': 4},
        ]
        tier = card_tier_list(stats)
        self.assertEqual(tier[0]['card'], 'A')

if __name__ == '__main__':
    unittest.main()
