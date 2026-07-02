"""
server/tests/test_moderator_engine.py
======================================
Unit tests for ModeratorEngine orchestration.
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from moderator_engine import get_moderator_engine

class TestModeratorEngine(unittest.TestCase):

    def setUp(self):
        self.engine = get_moderator_engine()

    def test_engine_process(self):
        res = self.engine.process_message(
            room_id="unit_test_room_engine",
            sender="Student_301",
            message_text="Main apni ranking complete kar chuka hun",
            language="ur",
            time_remaining_min=10.0
        )
        self.assertEqual(res["intervention_type"], "ranking_complete")
        self.assertIn("response_text", res)
        self.assertTrue(len(res["response_text"]) > 0)

if __name__ == "__main__":
    unittest.main()
