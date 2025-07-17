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

