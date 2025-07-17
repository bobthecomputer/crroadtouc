import unittest
from deck_optimizer import smart_swap, upgrade_optimizer

class OptimizerTests(unittest.TestCase):
    def test_smart_swap(self):
        deck = ["A", "B", "C", "D"]
        pool = ["E", "F", "G", "H"]
        def fitness(d):
            return len(set(d))
        result = smart_swap(deck, pool, fitness, generations=1)
        self.assertTrue(result)

    def test_upgrade_optimizer(self):
        levels = {"Knight": 12, "Archers": 11}
        costs = {"Knight": 20000, "Archers": 5000}
        picks = upgrade_optimizer(levels, costs, gold=20000)
        self.assertIn("Archers", picks)

if __name__ == '__main__':
    unittest.main()
